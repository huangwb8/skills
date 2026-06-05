from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common import ensure_dir, load_config, warn, write_json
from env_utils import find_remote_env, mask_secret, merged_env
from nano_banana_client import (
    GeminiHTTPError,
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


class ProviderUnavailable(RuntimeError):
    pass


class ProviderHTTPError(RuntimeError):
    def __init__(self, code: int, reason: str, detail: str, *, headers: Optional[Dict[str, str]] = None):
        super().__init__(f"HTTP {code} {reason}: {detail}")
        self.code = int(code)
        self.reason = str(reason)
        self.detail = str(detail)
        self.headers = dict(headers or {})


def health_check_image_provider(*, remote_env_path: Optional[Path] = None, timeout_s: int = 30) -> ImageProviderConfig:
    return resolve_image_provider(remote_env_path=remote_env_path, timeout_s=timeout_s, run_healthcheck=True)


def resolve_image_provider(
    *,
    remote_env_path: Optional[Path] = None,
    timeout_s: int = 30,
    run_healthcheck: bool = False,
) -> ImageProviderConfig:
    cfg = load_config()
    api_cfg = cfg.get("api", {}) if isinstance(cfg.get("api"), dict) else {}
    priority = [str(item).strip() for item in (api_cfg.get("provider_priority") or ["gpt-image-2", "nano_banana"])]
    errors: List[str] = []
    for provider in priority:
        normalized = _normalize_provider(provider)
        try:
            if normalized == "gpt-image-2":
                image_cfg = load_gpt_image_2_config(remote_env_path=remote_env_path)
                if run_healthcheck:
                    _openai_health_check(image_cfg, timeout_s=timeout_s)
                return image_cfg
            if normalized == "nano_banana":
                gemini_cfg = load_gemini_config(remote_env_path=remote_env_path)
                if run_healthcheck:
                    nano_banana_health_check(remote_env_path=remote_env_path, timeout_s=timeout_s)
                return ImageProviderConfig(
                    provider="nano_banana",
                    base_url=gemini_cfg.base_url,
                    api_key=gemini_cfg.api_key,
                    model=gemini_cfg.model,
                    env_path=gemini_cfg.env_path,
                    source="remote_env",
                )
        except Exception as exc:
            errors.append(f"{normalized}: {exc}")
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
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
    refs = [Path(p) for p in (reference_images or [])]
    if refs:
        warn("gpt-image-2 当前仅使用文本生成；参考图将随回退到 Nano Banana 时生效。")
    payload: Dict[str, Any] = {
        "model": cfg.model,
        "prompt": prompt,
        "size": _choose_openai_size(canvas_w, canvas_h),
        "n": 1,
    }
    if debug_dir is not None:
        ensure_dir(debug_dir)
        write_json(debug_dir / "request.json", {"provider": cfg.provider, "base_url": cfg.base_url, "model": cfg.model, "payload": payload})

    last_error: Optional[Exception] = None
    response: Dict[str, Any] = {}
    for attempt in range(1, max(1, retries) + 1):
        try:
            response = _post_json(
                f"{cfg.base_url}/images/generations",
                payload,
                headers={"Authorization": f"Bearer {cfg.api_key}"},
                timeout_s=timeout_s,
            )
            last_error = None
            break
        except ProviderHTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt >= retries:
                break
            wait_s = _retry_after(exc.headers) or min(30.0, 2.0**attempt)
            warn(f"gpt-image-2 暂时不可用（HTTP {exc.code}），{wait_s:.1f}s 后重试（{attempt}/{retries}）。")
            time.sleep(max(0.5, wait_s))
    if last_error is not None:
        raise last_error
    if debug_dir is not None:
        write_json(debug_dir / "response.json", _sanitize_image_response(response))

    best = _best_image(_extract_openai_images(response))
    if best is None:
        excerpt = json.dumps(response, ensure_ascii=False)[:800]
        raise RuntimeError(f"未从 gpt-image-2 响应中提取到图片。response_excerpt={excerpt}")
    mime, raw = best
    output_png.parent.mkdir(parents=True, exist_ok=True)
    output_png.write_bytes(raw)
    _resize_like_nano_banana(output_png, canvas_w=canvas_w, canvas_h=canvas_h)
    return {
        "mime_type": mime,
        "output_png": str(output_png),
        "target_size": _target_4k_size(canvas_w, canvas_h),
        "response_path": str(debug_dir / "response.json") if debug_dir is not None else None,
    }


def _openai_health_check(cfg: ImageProviderConfig, *, timeout_s: int) -> None:
    parsed = urllib.parse.urlparse(cfg.base_url)
    probe_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/v1/models", "", "", ""))
    if cfg.base_url.endswith("/v1"):
        probe_url = f"{cfg.base_url}/models"
    try:
        _post_json(probe_url, None, method="GET", headers={"Authorization": f"Bearer {cfg.api_key}"}, timeout_s=timeout_s)
    except ProviderHTTPError as exc:
        if exc.code in {404, 405}:
            return
        raise


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
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        hdrs = {str(k): str(v) for k, v in getattr(exc, "headers", {}).items()}
        raise ProviderHTTPError(int(exc.code), str(exc.reason), detail[:1600], headers=hdrs) from exc
    except Exception as exc:
        raise RuntimeError(f"请求图片 provider 失败：{exc}") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"图片 provider 响应 JSON 解析失败：{exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("图片 provider 响应不是 JSON object。")
    return data


def _extract_openai_images(resp: Dict[str, Any]) -> List[Tuple[str, bytes]]:
    out: List[Tuple[str, bytes]] = []
    data = resp.get("data")
    if not isinstance(data, list):
        return out
    for item in data:
        if not isinstance(item, dict):
            continue
        b64 = item.get("b64_json") or item.get("b64Json")
        if not isinstance(b64, str) or not b64.strip():
            continue
        try:
            out.append(("image/png", base64.b64decode(b64)))
        except Exception:
            continue
    return out


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


def _target_4k_size(canvas_w: int, canvas_h: int) -> Dict[str, int]:
    long_edge = 3840
    w = max(1, int(canvas_w))
    h = max(1, int(canvas_h))
    if w >= h:
        return {"width": long_edge, "height": max(1, int(round(long_edge * (h / w))))}
    return {"width": max(1, int(round(long_edge * (w / h)))), "height": long_edge}


def _resize_like_nano_banana(path: Path, *, canvas_w: int, canvas_h: int) -> None:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        warn("缺少 Pillow，跳过 PNG 尺寸对齐。")
        return
    target = _target_4k_size(canvas_w, canvas_h)
    try:
        with Image.open(path) as img:
            w, h = img.size
            if w == target["width"] and h == target["height"]:
                return
            scale = min(target["width"] / max(1, w), target["height"] / max(1, h))
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            resized = img.convert("RGBA").resize((new_w, new_h), resample=Image.LANCZOS)
            canvas = Image.new("RGBA", (target["width"], target["height"]), (255, 255, 255, 255))
            canvas.paste(resized, ((target["width"] - new_w) // 2, (target["height"] - new_h) // 2), resized)
            canvas.convert("RGB").save(path, format="PNG", optimize=True)
    except Exception as exc:
        warn(f"PNG 尺寸对齐失败（已忽略）：{exc}")


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
        try:
            import tomllib
            data = tomllib.loads(codex_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
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
    }


def _sanitize_image_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    cloned = json.loads(json.dumps(resp, ensure_ascii=False))
    data = cloned.get("data")
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            b64 = item.get("b64_json") or item.get("b64Json")
            if isinstance(b64, str):
                try:
                    raw = base64.b64decode(b64)
                    item["b64_json"] = f"<omitted {len(raw)} bytes>"
                except Exception:
                    item["b64_json"] = "<omitted invalid base64>"
                item.pop("b64Json", None)
    return cloned
