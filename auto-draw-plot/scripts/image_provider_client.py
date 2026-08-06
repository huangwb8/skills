from __future__ import annotations

import base64
import hashlib
import io
import json
import mimetypes
import os
import re
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common import ensure_dir, load_config, warn, write_json
from env_utils import find_remote_env, mask_secret, merged_env
from nano_banana_client import (
    generate_png as generate_nano_banana_png,
    load_gemini_config,
    nano_banana_health_check,
)


@dataclass(frozen=True)
class ImageProviderConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    env_path: Optional[Path]
    source: str
    preflight_status: str = "not_checked"
    preflight_scope: str = "configuration_only"
    generation_eligibility: str = "unknown_until_image_submit"

    def with_preflight(self, *, status: str, scope: str) -> "ImageProviderConfig":
        return replace(
            self,
            preflight_status=str(status),
            preflight_scope=str(scope),
            generation_eligibility="unknown_until_image_submit",
        )


class ProviderUnavailable(RuntimeError):
    pass


class ProviderHTTPError(RuntimeError):
    def __init__(self, code: int, reason: str, detail: str, *, headers: Optional[Dict[str, str]] = None):
        self.code = int(code)
        self.reason = str(reason)
        self.detail = str(detail)
        self.headers = dict(headers or {})
        error = _parse_provider_error_detail(self.detail)
        self.error_type = error["type"]
        self.error_code = error["code"]
        self.retryable = error["retryable"]
        self.safe_message = error["message"]
        self.category = _classify_provider_error(http_status=self.code, error_code=self.error_code)
        machine_code = f" code={self.error_code}" if self.error_code else ""
        super().__init__(f"HTTP {self.code} {self.reason}{machine_code}: {self.safe_message}")


class ProviderProtocolError(RuntimeError):
    def __init__(
        self,
        *,
        error_code: str,
        http_status: int,
        http_reason: str,
        request_url: str,
        final_url: str,
        headers: Dict[str, str],
        body: bytes,
        request_client_request_id: str = "",
    ) -> None:
        self.error_type = "provider_protocol_error"
        self.error_code = str(error_code or "PROVIDER_NON_JSON_RESPONSE")
        self.http_status = int(http_status or 0)
        self.http_reason = re.sub(r"[\r\n]+", " ", str(http_reason or "").strip())[:200]
        self.request_location = _safe_url_origin_path(request_url)
        self.response_location = _safe_url_origin_path(final_url)
        self.was_redirected = str(request_url) != str(final_url)
        self.final_origin_changed = _safe_url_origin(request_url) != _safe_url_origin(final_url)
        self.content_type = _safe_response_header(headers, "Content-Type")
        self.content_length = _safe_response_header(headers, "Content-Length")
        self.request_id = _safe_correlation_id(_safe_response_header(headers, "X-Request-ID"))
        self.client_request_id = _safe_correlation_id(
            _safe_response_header(headers, "X-Client-Request-ID")
        ) or _safe_correlation_id(request_client_request_id)
        self.body_bytes = len(body)
        self.body_sha256 = hashlib.sha256(body).hexdigest()
        self.body_prefix_kind = _body_prefix_kind(body)
        self.retryable = False
        self.category = "provider_protocol_error"
        self.safe_message = (
            "image provider returned an empty success response"
            if self.error_code == "PROVIDER_EMPTY_RESPONSE"
            else "image provider returned a non-JSON success response"
        )
        super().__init__(
            f"{self.error_code}: HTTP {self.http_status} {self.http_reason}; "
            f"location={self.response_location}; body_bytes={self.body_bytes}"
        )


class ProviderJobError(RuntimeError):
    def __init__(
        self,
        *,
        job_id: str,
        status: str,
        error_type: str,
        error_code: str,
        message: str,
    ) -> None:
        self.job_id = str(job_id or "unknown")
        self.status = str(status or "failed")
        self.error_type = str(error_type or "provider_error")
        self.error_code = str(error_code or "IMAGE_GENERATION_FAILED")
        self.safe_message = _redact_sensitive_error_text(message or "image generation job failed")
        self.category = _classify_provider_error(http_status=None, error_code=self.error_code)
        super().__init__(
            "gpt-image-2 异步图片任务失败："
            f"job_id={self.job_id}; status={self.status}; code={self.error_code}; message={self.safe_message}"
        )


def health_check_image_provider(
    *,
    remote_env_path: Optional[Path] = None,
    provider_name: Optional[str] = None,
    timeout_s: int = 30,
) -> ImageProviderConfig:
    return resolve_image_provider(
        remote_env_path=remote_env_path,
        provider_name=provider_name,
        timeout_s=timeout_s,
        run_healthcheck=True,
    )


def resolve_image_provider(
    *,
    remote_env_path: Optional[Path] = None,
    provider_name: Optional[str] = None,
    timeout_s: int = 30,
    run_healthcheck: bool = False,
) -> ImageProviderConfig:
    cfg = load_config()
    api_cfg = cfg.get("api", {}) if isinstance(cfg.get("api"), dict) else {}
    requested_provider = _normalize_provider(provider_name or "")
    priority = (
        [requested_provider]
        if requested_provider and requested_provider != "auto"
        else [str(item).strip() for item in (api_cfg.get("provider_priority") or ["gpt-image-2", "nano_banana"])]
    )
    errors: List[str] = []
    for provider in priority:
        normalized = _normalize_provider(provider)
        try:
            if normalized == "gpt-image-2":
                image_cfg = load_gpt_image_2_config(remote_env_path=remote_env_path)
                if run_healthcheck:
                    preflight_status = _openai_health_check(image_cfg, timeout_s=timeout_s)
                    image_cfg = image_cfg.with_preflight(
                        status=preflight_status,
                        scope=(
                            "connectivity_and_authentication_only"
                            if preflight_status == "connectivity/authentication_ok"
                            else "connectivity_only"
                        ),
                    )
                return image_cfg
            if normalized == "nano_banana":
                gemini_cfg = load_gemini_config(remote_env_path=remote_env_path)
                if run_healthcheck:
                    nano_banana_health_check(remote_env_path=remote_env_path, timeout_s=timeout_s)
                image_cfg = ImageProviderConfig(
                    provider="nano_banana",
                    base_url=gemini_cfg.base_url,
                    api_key=gemini_cfg.api_key,
                    model=gemini_cfg.model,
                    env_path=gemini_cfg.env_path,
                    source="remote_env",
                )
                if run_healthcheck:
                    image_cfg = image_cfg.with_preflight(
                        status="provider_probe_ok",
                        scope="provider_specific_probe_only",
                    )
                return image_cfg
        except Exception as exc:
            errors.append(f"{normalized}: {exc}")
            if requested_provider and requested_provider != "auto":
                raise ProviderUnavailable(
                    f"用户指定的图片 provider `{normalized}` 不可用，未切换到其他模型。原因：{exc}"
                ) from exc
            warn(f"图片 provider `{normalized}` 不可用，尝试下一个 provider。原因：{exc}")
    raise ProviderUnavailable("未找到可用图片生成 provider：" + " | ".join(errors))


def load_gpt_image_2_config(*, remote_env_path: Optional[Path] = None) -> ImageProviderConfig:
    cfg = load_config()
    api_cfg = cfg.get("api", {}) if isinstance(cfg.get("api"), dict) else {}
    gpt_cfg = api_cfg.get("gpt_image_2", {}) if isinstance(api_cfg.get("gpt_image_2"), dict) else {}
    env_path = find_remote_env(remote_env_path)
    env = merged_env(env_path)

    codex_config_path, codex_auth_path = _codex_config_paths(api_cfg=api_cfg)
    codex = _load_codex_provider_config(
        config_path=codex_config_path,
        auth_path=codex_auth_path,
        provider_names=_codex_provider_names(api_cfg=api_cfg, data=None),
        auth_key_names=gpt_cfg.get("codex_auth_key_names") or gpt_cfg.get("env_api_key_keys") or ["OPENAI_API_KEY", "OPENAI_API"],
    )
    base_url, api_key, model, source = _resolve_gpt_image_2_inputs(codex=codex, env=env, gpt_cfg=gpt_cfg)
    if not model:
        model = str(gpt_cfg.get("model") or "gpt-image-2")
    if str(model).strip() != str(gpt_cfg.get("model") or "gpt-image-2"):
        raise ProviderUnavailable(f"OpenAI 图片模型必须是 {gpt_cfg.get('model', 'gpt-image-2')}，当前为 {model!r}")
    if not base_url:
        raise ProviderUnavailable("缺少 OPENAI_BASE_URL / OPENAI_API_BASE，且未从 Codex 配置找到 BenszAPI base_url")
    if not api_key:
        raise ProviderUnavailable("缺少 OPENAI_API_KEY / OPENAI_API，且未从 Codex auth.json 找到可复用密钥")

    base_url = str(base_url).strip().rstrip("/")
    allowed_domains = [str(item).strip().lower() for item in (gpt_cfg.get("allowed_base_domains") or ["benszresearch.com"])]
    _validate_benszresearch_base_url(base_url, allowed_domains=allowed_domains)
    return ImageProviderConfig(
        provider="gpt-image-2",
        base_url=base_url,
        api_key=str(api_key).strip(),
        model=str(model).strip(),
        env_path=env_path,
        source=source,
    )


def generate_image_png(
    *,
    provider_cfg: ImageProviderConfig,
    prompt: str,
    output_png: Path,
    canvas_w: int,
    canvas_h: int,
    reference_images: Optional[List[Path]] = None,
    debug_dir: Optional[Path] = None,
    timeout_s: int = 180,
    retries: int = 5,
    postprocess_resize: bool = False,
    postprocess_w: Optional[int] = None,
    postprocess_h: Optional[int] = None,
    quality: Optional[str] = None,
    provider_size: Optional[str] = None,
    output_format: Optional[str] = None,
    output_compression: Optional[int] = None,
) -> Dict[str, Any]:
    _validate_postprocess_args(
        postprocess_resize=postprocess_resize,
        postprocess_w=postprocess_w,
        postprocess_h=postprocess_h,
    )
    if provider_cfg.provider == "gpt-image-2":
        result = _generate_openai_png(
            cfg=provider_cfg,
            prompt=prompt,
            output_png=output_png,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            reference_images=reference_images,
            debug_dir=debug_dir,
            timeout_s=timeout_s,
            retries=retries,
            postprocess_resize=postprocess_resize,
            postprocess_w=postprocess_w,
            postprocess_h=postprocess_h,
            quality=quality,
            provider_size=provider_size,
            output_format=output_format,
            output_compression=output_compression,
        )
    else:
        gemini_cfg = load_gemini_config(remote_env_path=provider_cfg.env_path)
        result = generate_nano_banana_png(
            cfg=gemini_cfg,
            prompt=prompt,
            output_png=output_png,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            reference_images=reference_images,
            debug_dir=debug_dir,
            timeout_s=timeout_s,
            retries=retries,
            postprocess_resize=postprocess_resize,
            postprocess_w=postprocess_w,
            postprocess_h=postprocess_h,
        )
    result.update(
        {
            "provider": provider_cfg.provider,
            "model": provider_cfg.model,
            "base_url": provider_cfg.base_url,
            "env_path": str(provider_cfg.env_path) if provider_cfg.env_path else None,
            "provider_source": provider_cfg.source,
        }
    )
    if debug_dir is not None:
        write_json(debug_dir / "image-provider.json", _debug_provider(provider_cfg))
    return result


def _generate_openai_png(
    *,
    cfg: ImageProviderConfig,
    prompt: str,
    output_png: Path,
    canvas_w: int,
    canvas_h: int,
    reference_images: Optional[List[Path]],
    debug_dir: Optional[Path],
    timeout_s: int,
    retries: int,
    postprocess_resize: bool,
    postprocess_w: Optional[int],
    postprocess_h: Optional[int],
    quality: Optional[str] = None,
    provider_size: Optional[str] = None,
    output_format: Optional[str] = None,
    output_compression: Optional[int] = None,
) -> Dict[str, Any]:
    refs = [Path(p) for p in (reference_images or [])]
    if refs:
        return _generate_openai_edit_png(
            cfg=cfg,
            prompt=prompt,
            output_png=output_png,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            reference_images=refs,
            debug_dir=debug_dir,
            timeout_s=timeout_s,
            retries=retries,
            postprocess_resize=postprocess_resize,
            postprocess_w=postprocess_w,
            postprocess_h=postprocess_h,
            quality=quality,
            provider_size=provider_size,
            output_format=output_format,
            output_compression=output_compression,
        )
    requested_size = _openai_requested_size(canvas_w, canvas_h, provider_size)
    quality, output_format, output_compression = _openai_generation_options(
        quality, output_format, output_compression
    )
    submit_retries = min(max(1, retries), _openai_submit_retry_attempts())
    payload: Dict[str, Any] = {
        "model": cfg.model,
        "prompt": prompt,
        "size": requested_size,
        "n": 1,
        "quality": quality,
        "output_format": output_format,
    }
    if output_compression is not None:
        payload["output_compression"] = output_compression
    endpoint_path = "/images/jobs/generations" if _use_openai_async_job_endpoint() else "/images/generations"
    submit_mode = _openai_submit_mode(endpoint_path)
    if debug_dir is not None:
        ensure_dir(debug_dir)
        write_json(
            debug_dir / "request.json",
            _openai_request_debug_payload(
                cfg=cfg,
                endpoint=endpoint_path,
                submit_mode=submit_mode,
                payload=payload,
            ),
        )

    try:
        response = _post_json_with_retries(
            url=f"{cfg.base_url}{endpoint_path}",
            payload=payload,
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            timeout_s=timeout_s,
            retries=submit_retries,
            retry_message="gpt-image-2 暂时不可用",
        )
    except ProviderHTTPError as exc:
        if not _can_fallback_openai_async_job_to_sync(exc):
            raise
        if debug_dir is not None:
            write_json(
                debug_dir / "async-job-unsupported.json",
                {
                    "endpoint": endpoint_path,
                    "submit_mode": submit_mode,
                    "error": provider_error_debug_payload(exc),
                    "fallback_endpoint": "/images/generations",
                },
            )
            write_json(
                debug_dir / "request-sync-fallback.json",
                _openai_request_debug_payload(
                    cfg=cfg,
                    endpoint="/images/generations",
                    submit_mode="sync_unsupported_fallback",
                    payload=payload,
                ),
            )
        endpoint_path = "/images/generations"
        submit_mode = "sync_unsupported_fallback"
        response = _post_json_with_retries(
            url=f"{cfg.base_url}{endpoint_path}",
            payload=payload,
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            timeout_s=timeout_s,
            retries=submit_retries,
            retry_message="gpt-image-2 兼容同步接口暂时不可用",
        )
    response = _resolve_openai_image_response(
        initial_response=response,
        cfg=cfg,
        endpoint=endpoint_path,
        debug_dir=debug_dir,
        timeout_s=timeout_s,
    )
    if debug_dir is not None:
        write_json(debug_dir / "response.json", _sanitize_image_response(response))

    best = _best_image(_extract_openai_images(response))
    if best is None:
        excerpt = json.dumps(response, ensure_ascii=False)[:800]
        raise RuntimeError(f"未从 gpt-image-2 响应中提取到图片。response_excerpt={excerpt}")
    mime, raw = best
    mime = _write_provider_image(output_png, mime, raw)
    size_meta = _build_output_size_meta(
        output_png,
        postprocess_resize=postprocess_resize,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        postprocess_w=postprocess_w,
        postprocess_h=postprocess_h,
    )
    return {
        "mime_type": mime,
        "output_file": str(output_png),
        "output_png": str(output_png),
        "requested_provider_size": _openai_size_meta(requested_size),
        **size_meta,
        "response_path": str(debug_dir / "response.json") if debug_dir is not None else None,
        "submit_mode": submit_mode,
        "endpoint": endpoint_path,
    }


def _generate_openai_edit_png(
    *,
    cfg: ImageProviderConfig,
    prompt: str,
    output_png: Path,
    canvas_w: int,
    canvas_h: int,
    reference_images: List[Path],
    debug_dir: Optional[Path],
    timeout_s: int,
    retries: int,
    postprocess_resize: bool,
    postprocess_w: Optional[int],
    postprocess_h: Optional[int],
    quality: Optional[str] = None,
    provider_size: Optional[str] = None,
    output_format: Optional[str] = None,
    output_compression: Optional[int] = None,
) -> Dict[str, Any]:
    refs = _existing_reference_images(reference_images)
    requested_size = _openai_requested_size(canvas_w, canvas_h, provider_size)
    quality, output_format, output_compression = _openai_generation_options(
        quality, output_format, output_compression
    )
    submit_retries = min(max(1, retries), _openai_submit_retry_attempts())
    fields: Dict[str, str] = {
        "model": cfg.model,
        "prompt": prompt,
        "size": requested_size,
        "n": "1",
        "quality": quality,
        "output_format": output_format,
    }
    if output_compression is not None:
        fields["output_compression"] = str(output_compression)
    files = _openai_edit_file_parts(refs)
    endpoint_path = "/images/jobs/edits" if _use_openai_async_job_endpoint() else "/images/edits"
    submit_mode = _openai_submit_mode(endpoint_path)
    if debug_dir is not None:
        ensure_dir(debug_dir)
        write_json(
            debug_dir / "request.json",
            {
                "provider": cfg.provider,
                "base_url": cfg.base_url,
                "model": cfg.model,
                "endpoint": endpoint_path,
                "submit_mode": submit_mode,
                "headers": _redacted_openai_headers(cfg),
                "payload": fields,
                "files": [
                    {
                        "field": field,
                        "filename": filename,
                        "mime_type": mime_type,
                        "size_bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
                    for field, filename, mime_type, raw in files
                ],
            },
        )

    try:
        response = _post_multipart_with_retries(
            url=f"{cfg.base_url}{endpoint_path}",
            fields=fields,
            files=files,
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            timeout_s=timeout_s,
            retries=submit_retries,
            retry_message="gpt-image-2 编辑暂时不可用",
        )
    except ProviderHTTPError as exc:
        if not _can_fallback_openai_async_job_to_sync(exc):
            raise
        if debug_dir is not None:
            write_json(
                debug_dir / "async-job-unsupported.json",
                {
                    "endpoint": endpoint_path,
                    "submit_mode": submit_mode,
                    "error": provider_error_debug_payload(exc),
                    "fallback_endpoint": "/images/edits",
                },
            )
            write_json(
                debug_dir / "request-sync-fallback.json",
                {
                    "provider": cfg.provider,
                    "base_url": cfg.base_url,
                    "model": cfg.model,
                    "endpoint": "/images/edits",
                    "submit_mode": "sync_unsupported_fallback",
                    "headers": _redacted_openai_headers(cfg),
                    "payload": fields,
                    "files": [
                        {
                            "field": field,
                            "filename": filename,
                            "mime_type": mime_type,
                            "size_bytes": len(raw),
                            "sha256": hashlib.sha256(raw).hexdigest(),
                        }
                        for field, filename, mime_type, raw in files
                    ],
                },
            )
        endpoint_path = "/images/edits"
        submit_mode = "sync_unsupported_fallback"
        response = _post_multipart_with_retries(
            url=f"{cfg.base_url}{endpoint_path}",
            fields=fields,
            files=files,
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            timeout_s=timeout_s,
            retries=submit_retries,
            retry_message="gpt-image-2 兼容编辑接口暂时不可用",
        )
    response = _resolve_openai_image_response(
        initial_response=response,
        cfg=cfg,
        endpoint=endpoint_path,
        debug_dir=debug_dir,
        timeout_s=timeout_s,
    )
    if debug_dir is not None:
        write_json(debug_dir / "response.json", _sanitize_image_response(response))

    best = _best_image(_extract_openai_images(response))
    if best is None:
        excerpt = json.dumps(response, ensure_ascii=False)[:800]
        raise RuntimeError(f"未从 gpt-image-2 编辑响应中提取到图片。response_excerpt={excerpt}")
    mime, raw = best
    mime = _write_provider_image(output_png, mime, raw)
    size_meta = _build_output_size_meta(
        output_png,
        postprocess_resize=postprocess_resize,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        postprocess_w=postprocess_w,
        postprocess_h=postprocess_h,
    )
    return {
        "mime_type": mime,
        "output_file": str(output_png),
        "output_png": str(output_png),
        "requested_provider_size": _openai_size_meta(requested_size),
        **size_meta,
        "response_path": str(debug_dir / "response.json") if debug_dir is not None else None,
        "reference_image_count": len(refs),
        "reference_images": [
            {
                "path": str(ref),
                "sha256": hashlib.sha256(ref.read_bytes()).hexdigest(),
                "source": "reference_image",
            }
            for ref in refs
        ],
        "operation": "image-edit",
        "submit_mode": submit_mode,
        "endpoint": endpoint_path,
    }


def _openai_health_check(cfg: ImageProviderConfig, *, timeout_s: int) -> str:
    parsed = urllib.parse.urlparse(cfg.base_url)
    probe_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/v1/models", "", "", ""))
    if cfg.base_url.endswith("/v1"):
        probe_url = f"{cfg.base_url}/models"
    try:
        _post_json(probe_url, None, method="GET", headers={"Authorization": f"Bearer {cfg.api_key}"}, timeout_s=timeout_s)
    except ProviderHTTPError as exc:
        if exc.code in {404, 405}:
            return "connectivity_ok_models_probe_unsupported"
        raise
    return "connectivity/authentication_ok"


_OPENAI_TRANSIENT_HTTP_CODES = {429, 500, 502, 503, 504}
_OPENAI_ASYNC_UNSUPPORTED_HTTP_CODES = {404, 405, 501}
_CLIENT_POLICY_ERROR_CODES = {
    "BILLING_PRICING_NOT_CONFIGURED",
    "SUBSCRIPTION_REQUIRED",
    "OVERAGE_LIMIT_EXCEEDED",
    "INSUFFICIENT_BALANCE",
    "INSUFFICIENT_QUOTA",
    "PERMISSION_DENIED",
    "ACCESS_DENIED",
    "BILLING_NOT_ALLOWED",
}
_PROVIDER_FALLBACK_BLOCKED_ERROR_CODES = _CLIENT_POLICY_ERROR_CODES | {
    "BILLING_SERVICE_ERROR",
    "PROVIDER_EMPTY_RESPONSE",
    "PROVIDER_NON_JSON_RESPONSE",
}


def _parse_provider_error_detail(detail: str) -> Dict[str, Any]:
    raw = str(detail or "").strip()
    payload: Any = None
    if raw:
        try:
            payload = json.loads(raw)
        except Exception:
            payload = None
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        error = payload if isinstance(payload, dict) else {}
    error_type = _safe_scalar(error.get("type"))
    error_code = _safe_scalar(error.get("code"))
    message = _safe_scalar(error.get("message") or error.get("detail"))
    if not message:
        message = raw if payload is None else "image provider request failed"
    return {
        "type": error_type,
        "code": error_code,
        "message": _redact_sensitive_error_text(message),
        "retryable": error.get("retryable") if isinstance(error.get("retryable"), bool) else None,
    }


def _safe_scalar(value: Any) -> str:
    if isinstance(value, (str, int, float)):
        return str(value).strip()[:800]
    return ""


def _redact_sensitive_error_text(value: str) -> str:
    text = str(value or "").strip()[:800]
    text = re.sub(r"(?i)Bearer\s+[^\s,;]+", "Bearer [redacted]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "[redacted:api_key]", text)
    return text


def _classify_provider_error(*, http_status: Optional[int], error_code: str) -> str:
    normalized_code = str(error_code or "").strip().upper()
    if normalized_code in _CLIENT_POLICY_ERROR_CODES:
        return "client_policy_error"
    if normalized_code == "BILLING_SERVICE_ERROR":
        return "transient_platform_error"
    if http_status in _OPENAI_TRANSIENT_HTTP_CODES:
        return "transient_platform_error"
    if http_status is not None and 400 <= int(http_status) < 500:
        return "client_policy_error"
    return "provider_error"


def _should_retry_provider_http_error(exc: ProviderHTTPError) -> bool:
    if exc.retryable is False:
        return False
    if exc.retryable is True:
        return exc.code in _OPENAI_TRANSIENT_HTTP_CODES
    return exc.code in _OPENAI_TRANSIENT_HTTP_CODES and exc.category == "transient_platform_error"


def is_provider_fallback_allowed(exc: BaseException) -> bool:
    if isinstance(exc, ProviderProtocolError):
        return False
    error_code = str(getattr(exc, "error_code", "") or "").strip().upper()
    category = str(getattr(exc, "category", "") or "").strip()
    cfg = load_config()
    api_cfg = cfg.get("api", {}) if isinstance(cfg.get("api"), dict) else {}
    configured = api_cfg.get("provider_fallback_blocked_error_codes")
    blocked_codes = (
        {str(item).strip().upper() for item in configured if str(item).strip()}
        if isinstance(configured, list)
        else _PROVIDER_FALLBACK_BLOCKED_ERROR_CODES
    )
    if error_code in blocked_codes:
        return False
    if category == "client_policy_error":
        return False
    return True


def provider_error_debug_payload(exc: BaseException) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "category": str(getattr(exc, "category", "provider_error") or "provider_error"),
        "exception_type": type(exc).__name__,
    }
    if isinstance(exc, ProviderHTTPError):
        payload.update(
            {
                "http_status": exc.code,
                "http_reason": exc.reason,
                "error": {
                    "type": exc.error_type,
                    "code": exc.error_code,
                    "message": exc.safe_message,
                },
            }
        )
        return payload
    if isinstance(exc, ProviderProtocolError):
        payload.update(
            {
                "error": {
                    "type": exc.error_type,
                    "code": exc.error_code,
                    "message": exc.safe_message,
                },
                "response": {
                    "http_status": exc.http_status,
                    "http_reason": exc.http_reason,
                    "request_location": exc.request_location,
                    "response_location": exc.response_location,
                    "content_type": exc.content_type,
                    "content_length": exc.content_length,
                    "body_bytes": exc.body_bytes,
                    "body_sha256": exc.body_sha256,
                    "body_prefix_kind": exc.body_prefix_kind,
                    "was_redirected": exc.was_redirected,
                    "final_origin_changed": exc.final_origin_changed,
                    "request_id": exc.request_id,
                    "client_request_id": exc.client_request_id,
                },
            }
        )
        return payload
    if isinstance(exc, ProviderJobError):
        payload.update(
            {
                "job_id": exc.job_id,
                "status": exc.status,
                "error": {
                    "type": exc.error_type,
                    "code": exc.error_code,
                    "message": exc.safe_message,
                },
            }
        )
        return payload
    payload["message"] = _redact_sensitive_error_text(str(exc))
    return payload


def _post_json_with_retries(
    *,
    url: str,
    payload: Optional[Dict[str, Any]],
    headers: Dict[str, str],
    timeout_s: int,
    retries: int,
    retry_message: str,
) -> Dict[str, Any]:
    last_error: Optional[ProviderHTTPError] = None
    for attempt in range(1, max(1, retries) + 1):
        try:
            return _post_json(
                url,
                payload,
                headers=headers,
                timeout_s=timeout_s,
            )
        except ProviderHTTPError as exc:
            last_error = exc
            if not _should_retry_provider_http_error(exc) or attempt >= retries:
                break
            wait_s = _retry_after(exc.headers) or min(30.0, 2.0**attempt)
            warn(f"{retry_message}（HTTP {exc.code}），{wait_s:.1f}s 后重试（{attempt}/{retries}）。")
            time.sleep(max(0.5, wait_s))
    if last_error is not None:
        raise last_error
    raise RuntimeError("图片 provider 请求失败，但没有捕获到明确错误。")


def _post_multipart_with_retries(
    *,
    url: str,
    fields: Dict[str, str],
    files: List[Tuple[str, str, str, bytes]],
    headers: Dict[str, str],
    timeout_s: int,
    retries: int,
    retry_message: str,
) -> Dict[str, Any]:
    last_error: Optional[ProviderHTTPError] = None
    for attempt in range(1, max(1, retries) + 1):
        try:
            return _post_multipart(
                url,
                fields=fields,
                files=files,
                headers=headers,
                timeout_s=timeout_s,
            )
        except ProviderHTTPError as exc:
            last_error = exc
            if not _should_retry_provider_http_error(exc) or attempt >= retries:
                break
            wait_s = _retry_after(exc.headers) or min(30.0, 2.0**attempt)
            warn(f"{retry_message}（HTTP {exc.code}），{wait_s:.1f}s 后重试（{attempt}/{retries}）。")
            time.sleep(max(0.5, wait_s))
    if last_error is not None:
        raise last_error
    raise RuntimeError("图片 provider multipart 请求失败，但没有捕获到明确错误。")


def _use_openai_async_job_endpoint() -> bool:
    async_cfg = _async_image_job_config()
    if not bool(async_cfg.get("enabled", True)):
        return False
    submit_mode = str(async_cfg.get("submit_mode") or "sub2api_job_endpoint").strip().lower()
    return submit_mode in {"sub2api_job_endpoint", "job_endpoint", "jobs"}


def _openai_submit_mode(endpoint_path: str) -> str:
    if str(endpoint_path).startswith("/images/jobs/"):
        return str(_async_image_job_config().get("submit_mode") or "sub2api_job_endpoint")
    return "sync"


def _can_fallback_openai_async_job_to_sync(exc: ProviderHTTPError) -> bool:
    if not _use_openai_async_job_endpoint():
        return False
    async_cfg = _async_image_job_config()
    if not bool(async_cfg.get("fallback_to_sync_on_unsupported", True)):
        return False
    return int(exc.code) in _OPENAI_ASYNC_UNSUPPORTED_HTTP_CODES


def _openai_request_debug_payload(
    *,
    cfg: ImageProviderConfig,
    endpoint: str,
    submit_mode: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "provider": cfg.provider,
        "base_url": cfg.base_url,
        "model": cfg.model,
        "endpoint": endpoint,
        "submit_mode": submit_mode,
        "headers": _redacted_openai_headers(cfg),
        "payload": payload,
    }


def _redacted_openai_headers(cfg: ImageProviderConfig) -> Dict[str, str]:
    return {"Authorization": f"Bearer {mask_secret(cfg.api_key)}"}


def _resolve_openai_image_response(
    *,
    initial_response: Dict[str, Any],
    cfg: ImageProviderConfig,
    endpoint: str,
    debug_dir: Optional[Path],
    timeout_s: int,
) -> Dict[str, Any]:
    if _best_image(_extract_openai_images(initial_response)) is not None:
        return initial_response

    job = _extract_openai_async_job(initial_response)
    if not job:
        return initial_response

    async_cfg = _async_image_job_config()
    if not bool(async_cfg.get("enabled", True)):
        return initial_response

    if debug_dir is not None:
        ensure_dir(debug_dir)
        write_json(debug_dir / "async-job-initial.json", _sanitize_image_response(initial_response))

    status_urls = _openai_async_status_urls(
        cfg=cfg,
        job_id=str(job.get("job_id") or ""),
        status_url=str(job.get("status_url") or ""),
        templates=async_cfg.get("status_endpoint_templates"),
    )
    if not status_urls:
        raise RuntimeError(
            "gpt-image-2 返回了异步图片任务，但响应中没有可轮询的 status_url 或 job_id。"
            f"endpoint={endpoint}; status={job.get('status') or 'unknown'}"
        )

    max_wait_s = max(1.0, float(async_cfg.get("max_wait_s", timeout_s) or timeout_s))
    poll_interval_s = max(0.5, float(async_cfg.get("poll_interval_s", 5) or 5))
    poll_timeout_s = max(1, int(async_cfg.get("poll_timeout_s", min(timeout_s, 60)) or min(timeout_s, 60)))
    started = time.monotonic()
    current = initial_response
    poll_log: List[Dict[str, Any]] = []
    attempt = 0
    while time.monotonic() - started <= max_wait_s:
        images = _extract_openai_images(current)
        if _best_image(images) is not None:
            if debug_dir is not None:
                write_json(debug_dir / "async-job-polls.json", poll_log)
            return current

        job = _extract_openai_async_job(current) or job
        status = str(job.get("status") or "").strip().lower()
        if status in _OPENAI_ASYNC_FAILURE_STATUSES:
            raise ProviderJobError(
                job_id=str(job.get("job_id") or "unknown"),
                status=status,
                error_type=str(job.get("error_type") or "provider_error"),
                error_code=str(job.get("error_code") or "IMAGE_GENERATION_FAILED"),
                message=str(job.get("error_message") or job.get("detail") or "image generation job failed"),
            )
        if status in _OPENAI_ASYNC_SUCCESS_STATUSES:
            result = _resolve_openai_async_job_result(
                current=current,
                cfg=cfg,
                job=job,
                debug_dir=debug_dir,
                timeout_s=poll_timeout_s,
                result_templates=async_cfg.get("result_endpoint_templates"),
            )
            if _best_image(_extract_openai_images(result)) is not None:
                if debug_dir is not None:
                    write_json(debug_dir / "async-job-polls.json", poll_log)
                return result
            if attempt > 0:
                raise RuntimeError(
                    "gpt-image-2 异步图片任务已完成，但响应中没有可提取图片："
                    f"job_id={job.get('job_id') or 'unknown'}"
                )

        if attempt > 0:
            time.sleep(poll_interval_s)
        attempt += 1
        current = _poll_openai_async_job(
            status_urls=status_urls,
            api_key=cfg.api_key,
            timeout_s=poll_timeout_s,
        )
        polled_job = _extract_openai_async_job(current) or {}
        poll_log.append(
            {
                "attempt": attempt,
                "elapsed_s": round(time.monotonic() - started, 3),
                "status": polled_job.get("status") or status or "unknown",
                "job_id": polled_job.get("job_id") or job.get("job_id"),
                "response": _sanitize_image_response(current),
            }
        )
        if debug_dir is not None:
            write_json(debug_dir / "async-job-polls.json", poll_log)

    raise TimeoutError(
        "gpt-image-2 异步图片任务轮询超时："
        f"job_id={job.get('job_id') or 'unknown'}; max_wait_s={max_wait_s:g}; endpoint={endpoint}"
    )


def _resolve_openai_async_job_result(
    *,
    current: Dict[str, Any],
    cfg: ImageProviderConfig,
    job: Dict[str, Any],
    debug_dir: Optional[Path],
    timeout_s: int,
    result_templates: Any,
) -> Dict[str, Any]:
    response_obj = _first_dict_value(current, ("response", "result", "output"))
    if response_obj and _best_image(_extract_openai_images(response_obj)) is not None:
        if debug_dir is not None:
            write_json(debug_dir / "async-job-result.json", _sanitize_image_response(response_obj))
        return response_obj

    result_urls = _openai_async_result_urls(
        cfg=cfg,
        job_id=str(job.get("job_id") or ""),
        result_url=str(job.get("result_url") or ""),
        templates=result_templates,
    )
    for result_url in result_urls:
        result = _post_json(
            result_url,
            None,
            method="GET",
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            timeout_s=timeout_s,
        )
        if debug_dir is not None:
            write_json(
                debug_dir / "async-job-result.json",
                {
                    "result_url": result_url,
                    "response": _sanitize_image_response(result),
                },
            )
        return result

    return current


_OPENAI_ASYNC_PENDING_STATUSES = {
    "created",
    "queued",
    "pending",
    "submitted",
    "starting",
    "running",
    "processing",
    "in_progress",
    "in-progress",
}
_OPENAI_ASYNC_SUCCESS_STATUSES = {"completed", "complete", "succeeded", "success", "done", "finished"}
_OPENAI_ASYNC_FAILURE_STATUSES = {"failed", "failure", "error", "cancelled", "canceled", "expired", "rejected"}


def _async_image_job_config() -> Dict[str, Any]:
    cfg = load_config()
    api_cfg = cfg.get("api", {}) if isinstance(cfg.get("api"), dict) else {}
    async_cfg = api_cfg.get("async_image_job", {}) if isinstance(api_cfg.get("async_image_job"), dict) else {}
    return dict(async_cfg)


def _extract_openai_async_job(resp: Dict[str, Any]) -> Dict[str, Any]:
    for item in _iter_response_dicts(resp):
        status = _first_string(item, ("status", "state", "phase"))
        status_normalized = status.strip().lower()
        job_id = _first_string(
            item,
            (
                "job_id",
                "jobId",
                "task_id",
                "taskId",
                "generation_id",
                "generationId",
                "request_id",
                "requestId",
                "id",
            ),
        )
        status_url = _first_string(
            item,
            ("status_url", "statusUrl", "poll_url", "pollUrl", "polling_url", "pollingUrl"),
        )
        result_url = _first_string(
            item,
            ("result_url", "resultUrl", "response_url", "responseUrl", "output_url", "outputUrl"),
        )
        object_type = _first_string(item, ("object", "type", "kind")).strip().lower()
        explicit_job_id = _first_string(
            item,
            ("job_id", "jobId", "task_id", "taskId", "generation_id", "generationId"),
        )
        looks_async = bool(status_url) or bool(result_url) or bool(explicit_job_id) or object_type in {
            "image.job",
            "image_job",
            "job",
            "task",
            "generation.job",
        } or status_normalized in (
            _OPENAI_ASYNC_PENDING_STATUSES | _OPENAI_ASYNC_SUCCESS_STATUSES | _OPENAI_ASYNC_FAILURE_STATUSES
        )
        if not looks_async:
            continue
        error_fields = _structured_error_fields(item)
        return {
            "job_id": job_id,
            "status": status_normalized or status,
            "status_url": status_url,
            "result_url": result_url,
            "detail": _detail_string(item),
            "error_type": error_fields["type"],
            "error_code": error_fields["code"],
            "error_message": error_fields["message"],
        }
    return {}


def _iter_response_dicts(value: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    def visit(node: Any, depth: int) -> None:
        if depth > 5:
            return
        if isinstance(node, dict):
            out.append(node)
            for child in node.values():
                if isinstance(child, (dict, list)):
                    visit(child, depth + 1)
        elif isinstance(node, list):
            for child in node:
                if isinstance(child, (dict, list)):
                    visit(child, depth + 1)

    visit(value, 0)
    return out


def _first_string(data: Dict[str, Any], keys: Tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)) and str(value).strip():
            return str(value).strip()
    return ""


def _first_dict_value(data: Dict[str, Any], keys: Tuple[str, ...]) -> Dict[str, Any]:
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _detail_string(data: Dict[str, Any]) -> str:
    value = _first_string(data, ("message", "detail", "failure_reason", "failureReason"))
    if value:
        return value
    error = data.get("error")
    if isinstance(error, str):
        return error.strip()
    if isinstance(error, dict):
        return _first_string(error, ("message", "detail", "code", "type")) or json.dumps(error, ensure_ascii=False)[:800]
    return ""


def _structured_error_fields(data: Dict[str, Any]) -> Dict[str, str]:
    error = data.get("error")
    source = error if isinstance(error, dict) else data
    message = _safe_scalar(source.get("message") or source.get("detail"))
    if not message and isinstance(error, str):
        message = error.strip()
    return {
        "type": _safe_scalar(source.get("type")),
        "code": _safe_scalar(source.get("code")),
        "message": _redact_sensitive_error_text(message),
    }


def _openai_async_status_urls(
    *,
    cfg: ImageProviderConfig,
    job_id: str,
    status_url: str,
    templates: Any,
) -> List[str]:
    urls: List[str] = []
    normalized_status_url = _normalize_openai_status_url(cfg.base_url, status_url)
    if normalized_status_url:
        urls.append(normalized_status_url)
    if job_id:
        if not isinstance(templates, list) or not templates:
            templates = ["{base_url}/images/jobs/{job_id}", "{base_url}/images/generations/{job_id}"]
        quoted_job_id = urllib.parse.quote(job_id, safe="")
        for template in templates:
            try:
                rendered = str(template).format(base_url=cfg.base_url.rstrip("/"), job_id=quoted_job_id)
            except Exception:
                continue
            normalized = _normalize_openai_status_url(cfg.base_url, rendered)
            if normalized:
                urls.append(normalized)
    return list(dict.fromkeys(urls))


def _openai_async_result_urls(
    *,
    cfg: ImageProviderConfig,
    job_id: str,
    result_url: str,
    templates: Any,
) -> List[str]:
    urls: List[str] = []
    normalized_result_url = _normalize_openai_status_url(cfg.base_url, result_url)
    if normalized_result_url:
        urls.append(normalized_result_url)
    if job_id:
        if not isinstance(templates, list) or not templates:
            templates = ["{base_url}/images/jobs/{job_id}/result"]
        quoted_job_id = urllib.parse.quote(job_id, safe="")
        for template in templates:
            try:
                rendered = str(template).format(base_url=cfg.base_url.rstrip("/"), job_id=quoted_job_id)
            except Exception:
                continue
            normalized = _normalize_openai_status_url(cfg.base_url, rendered)
            if normalized:
                urls.append(normalized)
    return list(dict.fromkeys(urls))


def _normalize_openai_status_url(base_url: str, status_url: str) -> str:
    raw = str(status_url or "").strip()
    if not raw:
        return ""
    parsed_base = urllib.parse.urlparse(base_url)
    parsed = urllib.parse.urlparse(raw)
    if not parsed.scheme:
        if not raw.startswith("/"):
            raw = "/" + raw
        raw = urllib.parse.urlunparse((parsed_base.scheme, parsed_base.netloc, raw, "", "", ""))
        parsed = urllib.parse.urlparse(raw)
    if parsed.scheme != "https" or parsed.netloc.lower() != parsed_base.netloc.lower():
        return ""
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", parsed.query, ""))


def _poll_openai_async_job(*, status_urls: List[str], api_key: str, timeout_s: int) -> Dict[str, Any]:
    errors: List[str] = []
    for url in status_urls:
        try:
            return _post_json(
                url,
                None,
                method="GET",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout_s=timeout_s,
            )
        except ProviderHTTPError as exc:
            errors.append(f"{url}: HTTP {exc.code} {exc.reason}")
            if exc.code not in {404, 405}:
                raise
    raise RuntimeError("异步图片任务状态接口不可用：" + " | ".join(errors))


def _post_json(
    url: str,
    payload: Optional[Dict[str, Any]],
    *,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    timeout_s: int = 60,
) -> Dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method.upper())
    if body is not None:
        req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "OpenAI/Python 1.0.0")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    client_request_id = _ensure_client_request_id(req)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
            response_status = _response_status(resp)
            response_reason = str(getattr(resp, "reason", "") or "")
            response_url = str(resp.geturl() or url)
            response_headers = {str(k): str(v) for k, v in getattr(resp, "headers", {}).items()}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        hdrs = {str(k): str(v) for k, v in getattr(exc, "headers", {}).items()}
        raise ProviderHTTPError(int(exc.code), str(exc.reason), detail[:1600], headers=hdrs) from exc
    except Exception as exc:
        raise RuntimeError(f"请求图片 provider 失败：{exc}") from exc
    data = _decode_provider_json_response(
        raw,
        http_status=response_status,
        http_reason=response_reason,
        request_url=url,
        final_url=response_url,
        headers=response_headers,
        request_client_request_id=client_request_id,
    )
    if not isinstance(data, dict):
        raise RuntimeError("图片 provider 响应不是 JSON object。")
    return data


def _post_multipart(
    url: str,
    *,
    fields: Dict[str, str],
    files: List[Tuple[str, str, str, bytes]],
    headers: Optional[Dict[str, str]] = None,
    timeout_s: int = 60,
) -> Dict[str, Any]:
    boundary = "----auto-draw-plot-" + base64.urlsafe_b64encode(os.urandom(18)).decode("ascii").rstrip("=")
    body = _encode_multipart(fields=fields, files=files, boundary=boundary)
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "OpenAI/Python 1.0.0")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    client_request_id = _ensure_client_request_id(req)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
            response_status = _response_status(resp)
            response_reason = str(getattr(resp, "reason", "") or "")
            response_url = str(resp.geturl() or url)
            response_headers = {str(k): str(v) for k, v in getattr(resp, "headers", {}).items()}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        hdrs = {str(k): str(v) for k, v in getattr(exc, "headers", {}).items()}
        raise ProviderHTTPError(int(exc.code), str(exc.reason), detail[:1600], headers=hdrs) from exc
    except Exception as exc:
        raise RuntimeError(f"请求图片 provider 失败：{exc}") from exc
    data = _decode_provider_json_response(
        raw,
        http_status=response_status,
        http_reason=response_reason,
        request_url=url,
        final_url=response_url,
        headers=response_headers,
        request_client_request_id=client_request_id,
    )
    if not isinstance(data, dict):
        raise RuntimeError("图片 provider 响应不是 JSON object。")
    return data


def _decode_provider_json_response(
    raw: bytes,
    *,
    http_status: int,
    http_reason: str,
    request_url: str,
    final_url: str,
    headers: Dict[str, str],
    request_client_request_id: str = "",
) -> Any:
    if not raw.strip():
        raise ProviderProtocolError(
            error_code="PROVIDER_EMPTY_RESPONSE",
            http_status=http_status,
            http_reason=http_reason,
            request_url=request_url,
            final_url=final_url,
            headers=headers,
            body=raw,
            request_client_request_id=request_client_request_id,
        )
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderProtocolError(
            error_code="PROVIDER_NON_JSON_RESPONSE",
            http_status=http_status,
            http_reason=http_reason,
            request_url=request_url,
            final_url=final_url,
            headers=headers,
            body=raw,
            request_client_request_id=request_client_request_id,
        ) from exc


def _response_status(response: Any) -> int:
    status = getattr(response, "status", None)
    if status is None and hasattr(response, "getcode"):
        status = response.getcode()
    try:
        return int(status or 0)
    except (TypeError, ValueError):
        return 0


def _safe_response_header(headers: Dict[str, str], name: str) -> str:
    expected = name.lower()
    for key, value in headers.items():
        if str(key).lower() == expected:
            raw = re.sub(r"[\r\n]+", " ", str(value or "").strip())[:200]
            if expected == "content-length" and not raw.isdigit():
                return ""
            return raw
    return ""


def _safe_correlation_id(value: str) -> str:
    value = str(value or "")
    if not value or len(value) > 128 or not re.fullmatch(r"[A-Za-z0-9._:-]+", value):
        return ""
    return value


def _ensure_client_request_id(req: urllib.request.Request) -> str:
    existing = _safe_correlation_id(req.get_header("X-client-request-id") or "")
    client_request_id = existing or f"auto-draw-plot:{uuid.uuid4()}"
    req.add_header("X-Client-Request-ID", client_request_id)
    return client_request_id


def _safe_url_origin_path(value: str) -> str:
    try:
        parsed = urllib.parse.urlparse(str(value or ""))
        hostname = str(parsed.hostname or "").lower()
        if not parsed.scheme or not hostname:
            return str(parsed.path or "/")
        port = parsed.port
        netloc = hostname if port is None else f"{hostname}:{port}"
        return urllib.parse.urlunparse((parsed.scheme.lower(), netloc, parsed.path or "/", "", "", ""))
    except (TypeError, ValueError):
        return ""


def _safe_url_origin(value: str) -> str:
    safe_location = _safe_url_origin_path(value)
    parsed = urllib.parse.urlparse(safe_location)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return ""


def _body_prefix_kind(body: bytes) -> str:
    stripped = body.lstrip()
    if not stripped:
        return "empty"
    first = stripped[:1]
    if first == b"<":
        return "markup"
    if first in {b"{", b"["}:
        return "json_like"
    if all(byte in {9, 10, 13} or 32 <= byte <= 126 for byte in stripped[:32]):
        return "text"
    return "binary"


def _encode_multipart(*, fields: Dict[str, str], files: List[Tuple[str, str, str, bytes]], boundary: str) -> bytes:
    chunks: List[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{_escape_multipart_name(name)}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    for field, filename, mime_type, raw in files:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    'Content-Disposition: form-data; '
                    f'name="{_escape_multipart_name(field)}"; filename="{_escape_multipart_name(filename)}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
                raw,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


def _escape_multipart_name(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\r", "").replace("\n", "")


def _existing_reference_images(reference_images: List[Path]) -> List[Path]:
    max_bytes = _max_reference_image_bytes()
    refs: List[Path] = []
    for path in reference_images:
        ref = Path(path)
        if not ref.exists():
            raise FileNotFoundError(f"参考图不存在：{ref}")
        if not ref.is_file():
            raise FileNotFoundError(f"参考图不是文件：{ref}")
        size_bytes = ref.stat().st_size
        if size_bytes > max_bytes:
            raise ValueError(f"参考图过大：{ref} ({size_bytes} bytes > {max_bytes} bytes)")
        refs.append(ref)
    if not refs:
        raise ValueError("gpt-image-2 编辑模式需要至少 1 张参考图。")
    return refs


def _openai_edit_file_parts(reference_images: List[Path]) -> List[Tuple[str, str, str, bytes]]:
    parts: List[Tuple[str, str, str, bytes]] = []
    multi = len(reference_images) > 1
    for ref in reference_images:
        raw = ref.read_bytes()
        mime_type = _infer_reference_image_mime(ref, raw)
        field_name = "image[]" if multi else "image"
        parts.append((field_name, ref.name, mime_type, raw))
    return parts


def _infer_reference_image_mime(path: Path, raw: bytes) -> str:
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(raw) >= 12 and raw[0:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    guessed = mimetypes.guess_type(str(path))[0] or "unknown"
    raise RuntimeError(f"参考图内容不是受支持的图片格式：{path} (guessed={guessed})")


def _extract_openai_images(resp: Dict[str, Any]) -> List[Tuple[str, bytes]]:
    out: List[Tuple[str, bytes]] = []
    for item in _iter_response_dicts(resp):
        mime = str(item.get("mime_type") or item.get("mimeType") or "image/png").lower()
        for key in ("b64_json", "b64Json", "image_b64", "imageB64", "base64_image", "base64Image"):
            raw = _decode_b64_image(item.get(key))
            if raw:
                out.append((mime, raw))
        image_url = item.get("url") or item.get("image_url") or item.get("imageUrl")
        if isinstance(image_url, str) and image_url.startswith("data:image/"):
            raw = _decode_data_url_image(image_url)
            if raw:
                out.append(("image/png", raw))
    return out


def _decode_b64_image(value: Any) -> Optional[bytes]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        raw = base64.b64decode(value.strip(), validate=True)
    except Exception:
        return None
    if not raw:
        return None
    return raw


def _decode_data_url_image(value: str) -> Optional[bytes]:
    try:
        header, encoded = value.split(",", 1)
    except ValueError:
        return None
    if ";base64" not in header.lower():
        return None
    return _decode_b64_image(encoded)


def _best_image(images: List[Tuple[str, bytes]]) -> Optional[Tuple[str, bytes]]:
    if not images:
        return None
    return sorted(images, key=lambda item: (1 if "png" in item[0] else 0, len(item[1])), reverse=True)[0]


def _choose_openai_size(w: int, h: int) -> str:
    if h <= 0:
        return "1024x1024"
    ratio = float(w) / float(h)
    if ratio >= 1.15:
        return "1536x1024"
    if ratio <= (1.0 / 1.15):
        return "1024x1536"
    return "1024x1024"


def _openai_requested_size(w: int, h: int, requested: Optional[str] = None) -> str:
    cfg = load_config()
    gen_cfg = cfg.get("generation", {}) if isinstance(cfg.get("generation"), dict) else {}
    configured = str(requested or gen_cfg.get("provider_size") or "").strip().lower()
    if configured:
        if configured not in {"1024x1024", "1536x1024", "1024x1536", "auto"}:
            raise ValueError(f"不支持的 gpt-image-2 provider_size：{configured}")
        return configured
    return _choose_openai_size(w, h)


def _openai_generation_options(
    requested_quality: Optional[str] = None,
    requested_format: Optional[str] = None,
    requested_compression: Optional[int] = None,
) -> Tuple[str, str, Optional[int]]:
    """Return provider-supported low-cost delivery options from the skill config."""
    cfg = load_config()
    gen_cfg = cfg.get("generation", {}) if isinstance(cfg.get("generation"), dict) else {}
    quality = str(requested_quality or gen_cfg.get("quality") or "low").strip().lower()
    output_format = str(requested_format or gen_cfg.get("output_format") or "jpeg").strip().lower()
    compression_raw = requested_compression if requested_compression is not None else gen_cfg.get("output_compression")
    compression = int(compression_raw) if compression_raw is not None else None
    if quality not in {"low", "medium", "high", "auto"}:
        raise ValueError(f"不支持的图片 quality：{quality}")
    if output_format not in {"png", "jpeg", "webp"}:
        raise ValueError(f"不支持的图片 output_format：{output_format}")
    if compression is not None and not 0 <= compression <= 100:
        raise ValueError("output_compression 必须在 0 到 100 之间。")
    return quality, output_format, compression


def _openai_submit_retry_attempts() -> int:
    # Image-job submit has no durable Idempotency-Key contract yet. Poll and
    # result requests are safe to retry independently after a job id exists.
    return 1


def write_image_with_format_contract(path: Path, raw: bytes) -> str:
    detected = _detect_image_mime(raw)
    if not detected:
        raise RuntimeError("图片 provider 返回的内容不是受支持的 PNG/JPEG/WebP 图片。")
    suffix = path.suffix.lower()
    expected_suffixes = {
        "image/png": {".png"},
        "image/jpeg": {".jpg", ".jpeg"},
        "image/webp": {".webp"},
    }[detected]
    if suffix in {".jpg", ".jpeg"} and detected != "image/jpeg":
        _write_jpeg(path, raw)
        return "image/jpeg"
    if suffix == ".png" and detected != "image/png":
        _write_png(path, raw)
        return "image/png"
    if suffix and suffix not in expected_suffixes:
        raise ValueError(f"输出扩展名 {suffix} 与 provider 图片内容 {detected} 不一致。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return detected


def _write_provider_image(path: Path, _declared_mime: str, raw: bytes) -> str:
    return write_image_with_format_contract(path, raw)


def _write_jpeg(path: Path, raw: bytes) -> None:
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError("将 provider 图片导出为 JPEG 需要 Pillow。") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(raw)) as source:
        if source.mode in {"RGBA", "LA"} or "transparency" in source.info:
            rgba = source.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.getchannel("A"))
            image = background
        else:
            image = source.convert("RGB")
        image.save(path, format="JPEG", quality=85, optimize=True)


def _write_png(path: Path, raw: bytes) -> None:
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError("将 provider 图片导出为 PNG 需要 Pillow。") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(raw)) as source:
        source.save(path, format="PNG", optimize=True)


def _detect_image_mime(raw: bytes) -> str:
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(raw) >= 12 and raw[0:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return ""


def _openai_size_meta(size: str) -> Dict[str, Any]:
    try:
        width_s, height_s = str(size).lower().split("x", 1)
        return {"provider_value": str(size), "width": int(width_s), "height": int(height_s)}
    except Exception:
        return {"provider_value": str(size)}


def _target_4k_size(canvas_w: int, canvas_h: int) -> Dict[str, int]:
    long_edge = 3840
    w = max(1, int(canvas_w))
    h = max(1, int(canvas_h))
    if w >= h:
        return {"width": long_edge, "height": max(1, int(round(long_edge * (h / w))))}
    return {"width": max(1, int(round(long_edge * (w / h)))), "height": long_edge}


def _build_output_size_meta(
    path: Path,
    *,
    postprocess_resize: bool,
    canvas_w: int,
    canvas_h: int,
    postprocess_w: Optional[int],
    postprocess_h: Optional[int],
) -> Dict[str, Any]:
    native_size = _image_size(path)
    target_size = _postprocess_target_size(
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        postprocess_w=postprocess_w,
        postprocess_h=postprocess_h,
    )
    applied = False
    if postprocess_resize:
        applied = _resize_to_canvas(path, target=target_size)
    return {
        "native_size": native_size,
        "output_size": _image_size(path),
        "postprocess_resize_applied": applied,
        "postprocess_target_size": target_size if postprocess_resize else None,
    }


def _postprocess_target_size(
    *,
    canvas_w: int,
    canvas_h: int,
    postprocess_w: Optional[int],
    postprocess_h: Optional[int],
) -> Dict[str, int]:
    if postprocess_w and postprocess_h:
        return {"width": max(1, int(postprocess_w)), "height": max(1, int(postprocess_h))}
    return _target_4k_size(canvas_w, canvas_h)


def _validate_postprocess_args(
    *,
    postprocess_resize: bool,
    postprocess_w: Optional[int],
    postprocess_h: Optional[int],
) -> None:
    has_w = postprocess_w is not None
    has_h = postprocess_h is not None
    if has_w != has_h:
        raise ValueError("--postprocess-width 与 --postprocess-height 必须同时提供。")
    if (has_w or has_h) and not postprocess_resize:
        raise ValueError("只有启用 --postprocess-resize 时才能指定后处理目标尺寸。")
    if postprocess_resize and not (has_w and has_h):
        raise ValueError("--postprocess-resize 需要同时指定 --postprocess-width 与 --postprocess-height。")
    if has_w and int(postprocess_w or 0) <= 0:
        raise ValueError("--postprocess-width 必须为正整数。")
    if has_h and int(postprocess_h or 0) <= 0:
        raise ValueError("--postprocess-height 必须为正整数。")


def _max_reference_image_bytes() -> int:
    cfg = load_config()
    gen_cfg = cfg.get("generation", {}) if isinstance(cfg.get("generation"), dict) else {}
    return max(1, int(gen_cfg.get("max_reference_image_bytes", 20 * 1024 * 1024)))


def _image_size(path: Path) -> Optional[Dict[str, int]]:
    try:
        raw = path.read_bytes()[:32]
        if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 24:
            width, height = struct.unpack(">II", raw[16:24])
            return {"width": int(width), "height": int(height)}
    except Exception:
        pass
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as img:
            return {"width": int(img.size[0]), "height": int(img.size[1])}
    except Exception:
        return None


def _resize_to_canvas(path: Path, *, target: Dict[str, int]) -> bool:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        warn("缺少 Pillow，跳过 PNG 尺寸对齐。")
        return False
    try:
        with Image.open(path) as img:
            w, h = img.size
            if w == target["width"] and h == target["height"]:
                return False
            scale = min(target["width"] / max(1, w), target["height"] / max(1, h))
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            resized = img.convert("RGBA").resize((new_w, new_h), resample=Image.LANCZOS)
            canvas = Image.new("RGBA", (target["width"], target["height"]), (255, 255, 255, 255))
            canvas.paste(resized, ((target["width"] - new_w) // 2, (target["height"] - new_h) // 2), resized)
            canvas.convert("RGB").save(path, format="PNG", optimize=True)
            return True
    except Exception as exc:
        warn(f"PNG 尺寸对齐失败（已忽略）：{exc}")
        return False


def _validate_benszresearch_base_url(base_url: str, *, allowed_domains: List[str]) -> None:
    parsed = urllib.parse.urlparse(base_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        raise ProviderUnavailable("gpt-image-2 base_url 必须是 https URL")
    if parsed.username or parsed.password:
        raise ProviderUnavailable("gpt-image-2 base_url 不允许包含 userinfo")
    if parsed.query or parsed.fragment:
        raise ProviderUnavailable("gpt-image-2 base_url 不允许包含 query 或 fragment")
    if parsed.path.rstrip("/") not in {"", "/v1"}:
        raise ProviderUnavailable("gpt-image-2 base_url 只允许空路径或 /v1")
    allowed = False
    for domain in allowed_domains:
        domain = domain.lstrip(".").lower()
        if host.endswith("." + domain):
            allowed = True
            break
    if not allowed:
        raise ProviderUnavailable("gpt-image-2 base_url 必须是 benszresearch.com 的子域名")


def _resolve_gpt_image_2_inputs(*, codex: Dict[str, Any], env: Dict[str, str], gpt_cfg: Dict[str, Any]) -> Tuple[str, str, str, str]:
    env_base_url = _first_env(env, gpt_cfg.get("env_base_url_keys") or ["OPENAI_BASE_URL", "OPENAI_API_BASE"])
    env_api_key = _first_env(env, gpt_cfg.get("env_api_key_keys") or ["OPENAI_API_KEY", "OPENAI_API"])
    env_model = _first_env(env, gpt_cfg.get("env_model_keys") or ["OPENAI_IMAGE_MODEL", "OPENAI_MODEL"])

    source_parts: List[str] = []
    base_url = ""
    api_key = ""
    model = env_model

    if codex.get("base_url"):
        base_url = str(codex["base_url"])
        source_parts.append("codex_config")
    elif env_base_url:
        base_url = env_base_url
        source_parts.append("env")

    if codex.get("api_key"):
        api_key = str(codex["api_key"])
        source_parts.append("codex_auth")
    elif env_api_key:
        api_key = env_api_key
        if "env" not in source_parts:
            source_parts.append("env")

    if env_model and "env" not in source_parts:
        source_parts.append("env")

    return base_url, api_key, model, "+".join(dict.fromkeys(source_parts)) or "remote_env"


def _codex_config_paths(*, api_cfg: Dict[str, Any]) -> Tuple[Path, Path]:
    config_path = Path(str(api_cfg.get("codex_config_path") or "~/.codex/config.toml")).expanduser()
    auth_path = Path(str(api_cfg.get("codex_auth_path") or "~/.codex/auth.json")).expanduser()
    return config_path, auth_path


def _codex_provider_names(*, api_cfg: Dict[str, Any], data: Optional[Dict[str, Any]]) -> List[str]:
    provider_names: List[str] = []
    gpt_cfg = api_cfg.get("gpt_image_2", {}) if isinstance(api_cfg.get("gpt_image_2"), dict) else {}
    if isinstance(gpt_cfg.get("codex_provider_names"), list):
        provider_names.extend(str(item) for item in gpt_cfg.get("codex_provider_names"))
    if isinstance(data, dict):
        active = str(data.get("model_provider") or "")
        if active:
            provider_names.append(active)
    return list(dict.fromkeys([name for name in provider_names if name]))


def _load_codex_provider_config(
    *,
    config_path: Path,
    auth_path: Path,
    provider_names: List[str],
    auth_key_names: Any,
) -> Dict[str, Any]:
    codex_path = Path(config_path).expanduser()
    out: Dict[str, Any] = {}
    data: Dict[str, Any] = {}
    if codex_path.exists():
        data = _load_codex_toml(codex_path)
    provider_names = list(dict.fromkeys([*provider_names, *_codex_provider_names(api_cfg={}, data=data)]))
    providers = data.get("model_providers") if isinstance(data.get("model_providers"), dict) else {}
    for name in provider_names:
        provider = providers.get(name)
        if isinstance(provider, dict) and provider.get("base_url"):
            out.update({"name": name, "base_url": str(provider.get("base_url"))})
            break

    auth_path = Path(auth_path).expanduser()
    if auth_path.exists():
        try:
            auth_data = json.loads(auth_path.read_text(encoding="utf-8"))
        except Exception:
            auth_data = {}
        api_key = _first_json_secret(auth_data, auth_key_names)
        if api_key:
            out["api_key"] = api_key
            out["auth_path"] = str(auth_path)
    return out


def _load_codex_toml(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        import tomllib
        data = tomllib.loads(raw)
        return data if isinstance(data, dict) else {}
    except ModuleNotFoundError:
        pass
    except Exception:
        return {}
    try:
        import tomli  # type: ignore
        data = tomli.loads(raw)
        return data if isinstance(data, dict) else {}
    except ModuleNotFoundError:
        return _parse_minimal_codex_toml(raw)
    except Exception:
        return {}


def _parse_minimal_codex_toml(raw: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    current: Optional[Dict[str, Any]] = data
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
            parts = section.split(".")
            current = data
            for part in parts:
                if not part:
                    current = None
                    break
                current = current.setdefault(part, {}) if isinstance(current, dict) else None
            continue
        if current is None or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        current[key] = value
    return data


def _first_json_secret(data: Any, keys: Any) -> str:
    if isinstance(keys, str):
        keys = [keys]
    if not isinstance(data, dict):
        return ""
    for key in keys or []:
        value = data.get(str(key))
        if isinstance(value, str) and value.strip():
            return value.strip()
    for container_key in ("env", "secrets", "tokens"):
        nested = data.get(container_key)
        if isinstance(nested, dict):
            value = _first_json_secret(nested, keys)
            if value:
                return value
    return ""


def _first_env(env: Dict[str, str], keys: Any) -> str:
    if isinstance(keys, str):
        keys = [keys]
    for key in keys or []:
        value = str(env.get(str(key), "") or "").strip()
        if value:
            return value
    return ""


def _normalize_provider(value: str) -> str:
    v = str(value or "").strip().lower().replace("_", "-")
    if v in {"", "auto"}:
        return "auto" if v == "auto" else ""
    if v in {"gpt-image-2", "openai", "gptimage2"}:
        return "gpt-image-2"
    if v in {"nano-banana", "nano_banana", "gemini", "google"}:
        return "nano_banana"
    return v


def _retry_after(headers: Dict[str, str]) -> Optional[float]:
    try:
        raw = str(headers.get("Retry-After", "") or "").strip()
        return float(raw) if raw else None
    except Exception:
        return None


def _debug_provider(cfg: ImageProviderConfig) -> Dict[str, Any]:
    return {
        "provider": cfg.provider,
        "base_url": cfg.base_url,
        "model": cfg.model,
        "api_key": mask_secret(cfg.api_key),
        "env_path": str(cfg.env_path) if cfg.env_path else None,
        "source": cfg.source,
        "preflight_status": cfg.preflight_status,
        "preflight_scope": cfg.preflight_scope,
        "generation_eligibility": cfg.generation_eligibility,
    }


def _sanitize_image_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    cloned = json.loads(json.dumps(resp, ensure_ascii=False))
    for item in _iter_response_dicts(cloned):
        for key in list(item):
            if str(key).lower() in {
                "authorization",
                "api_key",
                "apikey",
                "access_token",
                "token",
                "subscription",
                "subscription_id",
                "subscriptionid",
                "billing_details",
                "billingdetails",
                "internal",
                "account_id",
                "accountid",
                "upstream_account_id",
            }:
                item[key] = "[redacted]"
        if "error" in item:
            error = _structured_error_fields(item)
            item["error"] = {key: value for key, value in error.items() if value}
        for key in ("b64_json", "b64Json", "image_b64", "imageB64", "base64_image", "base64Image"):
            b64 = item.get(key)
            if not isinstance(b64, str):
                continue
            try:
                raw = base64.b64decode(b64)
                item[key] = f"<omitted {len(raw)} bytes>"
            except Exception:
                item[key] = "<omitted invalid base64>"
        image_url = item.get("url") or item.get("image_url") or item.get("imageUrl")
        if isinstance(image_url, str) and image_url.startswith("data:image/"):
            if "url" in item:
                item["url"] = "<omitted data image url>"
            if "image_url" in item:
                item["image_url"] = "<omitted data image url>"
            if "imageUrl" in item:
                item["imageUrl"] = "<omitted data image url>"
    return cloned
