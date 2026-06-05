from __future__ import annotations

import base64
import json
import math
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common import ensure_dir, warn
from env_utils import find_remote_env, mask_secret, merged_env


@dataclass(frozen=True)
class GeminiConfig:
    base_url: str
    api_key: str
    model: str
    env_path: Optional[Path]


class GeminiHTTPError(RuntimeError):
    def __init__(self, code: int, reason: str, detail: str):
        super().__init__(f"HTTP {code} {reason}: {detail}")
        self.code = int(code)
        self.reason = str(reason)
        self.detail = str(detail)


def load_gemini_config(*, remote_env_path: Optional[Path] = None) -> GeminiConfig:
    env_path = find_remote_env(remote_env_path)
    env = merged_env(env_path)

    base_url = str(env.get("GEMINI_BASE_URL", "") or "").strip().rstrip("/")
    api_key = str(
        env.get("GEMINI_API", "")
        or env.get("GEMINI_API_KEY", "")
        or env.get("GOOGLE_API_KEY", "")
        or ""
    ).strip()
    model = str(env.get("GEMINI_MODEL", "") or "").strip()

    missing: List[str] = []
    if not env_path:
        missing.append("remote.env")
    if not base_url:
        missing.append("GEMINI_BASE_URL")
    if not api_key:
        missing.append("GEMINI_API")
    if not model:
        missing.append("GEMINI_MODEL")
    if missing:
        raise RuntimeError(
            "未检测到可用的 Nano Banana / Gemini 配置。缺少：{}。请先检查 `~/.bensz-skills/config/remote.env`。".format(
                "、".join(missing)
            )
        )

    return GeminiConfig(base_url=base_url, api_key=api_key, model=model, env_path=env_path)


def _post_json(
    url: str,
    payload: Dict[str, Any],
    *,
    headers: Optional[Dict[str, str]] = None,
    timeout_s: int = 60,
) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail_raw = exc.read()
        detail = detail_raw.decode("utf-8", errors="replace")
        raise GeminiHTTPError(int(exc.code), str(exc.reason), detail[:1600]) from exc
    except Exception as exc:
        raise RuntimeError(f"请求 Gemini 失败：{exc}") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Gemini 响应 JSON 解析失败：{exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Gemini 响应不是 JSON object。")
    return data


def generate_content(cfg: GeminiConfig, payload: Dict[str, Any], *, timeout_s: int = 120) -> Dict[str, Any]:
    endpoint = f"{cfg.base_url}/models/{cfg.model}:generateContent"
    try:
        return _post_json(endpoint, payload, headers={"x-goog-api-key": cfg.api_key}, timeout_s=timeout_s)
    except GeminiHTTPError as exc:
        if exc.code not in {401, 403}:
            raise
        warn(f"Gemini header 认证失败（HTTP {exc.code}），回退到 query key。")
        return _post_json(f"{endpoint}?key={cfg.api_key}", payload, headers=None, timeout_s=timeout_s)


def nano_banana_health_check(*, remote_env_path: Optional[Path] = None, timeout_s: int = 30) -> GeminiConfig:
    cfg = load_gemini_config(remote_env_path=remote_env_path)
    text_payload = {
        "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 16},
    }
    try:
        resp = generate_content(cfg, text_payload, timeout_s=timeout_s)
        if not isinstance(resp.get("candidates"), list) or not resp.get("candidates"):
            raise RuntimeError("Gemini 文本连通性检查失败：响应中缺少 candidates。")
        return cfg
    except GeminiHTTPError as exc:
        if exc.code != 400 or "not supported by this model" not in exc.detail.lower():
            raise
        # Some Nano Banana style models only support IMAGE outputs. In that case
        # we fall back to a tiny image-generation probe.
        image_payload = {
            "contents": [{"role": "user", "parts": [{"text": "A tiny blue square on white background"}]}],
            "generationConfig": {
                "temperature": 0.0,
                "imageConfig": {"aspectRatio": "1:1", "imageSize": "1K"},
            },
        }
        resp = generate_content(cfg, image_payload, timeout_s=timeout_s)
        if _best_image(_extract_inline_images(resp)) is None:
            raise RuntimeError("Gemini 图片连通性检查失败：未返回 inline image。")
        return cfg


def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    cloned = json.loads(json.dumps(payload, ensure_ascii=False))
    contents = cloned.get("contents")
    if not isinstance(contents, list):
        return cloned
    for content in contents:
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline = part.get("inlineData") or part.get("inline_data")
            if isinstance(inline, dict) and isinstance(inline.get("data"), str):
                inline["data"] = "<omitted>"
    return cloned


def _write_debug_request(debug_dir: Optional[Path], cfg: GeminiConfig, payload: Dict[str, Any]) -> None:
    if debug_dir is None:
        return
    ensure_dir(debug_dir)
    body = {
        "base_url": cfg.base_url,
        "model": cfg.model,
        "api_key": mask_secret(cfg.api_key),
        "payload": _sanitize_payload(payload),
    }
    (debug_dir / "request.json").write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_debug_response(debug_dir: Optional[Path], payload: Dict[str, Any]) -> None:
    if debug_dir is None:
        return
    ensure_dir(debug_dir)
    (debug_dir / "response.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _extract_text(resp: Dict[str, Any]) -> str:
    out: List[str] = []
    candidates = resp.get("candidates")
    if not isinstance(candidates, list):
        return ""
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        content = cand.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            if part.get("thought") is True:
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                out.append(text)
    return "\n".join(out).strip()


def _extract_inline_images(resp: Dict[str, Any]) -> List[Tuple[str, bytes]]:
    out: List[Tuple[str, bytes]] = []
    candidates = resp.get("candidates")
    if not isinstance(candidates, list):
        return out
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        content = cand.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline = part.get("inlineData") or part.get("inline_data")
            if not isinstance(inline, dict):
                continue
            data_b64 = inline.get("data")
            if not isinstance(data_b64, str) or not data_b64.strip():
                continue
            try:
                raw = base64.b64decode(data_b64)
            except Exception:
                continue
            mime = str(inline.get("mimeType") or inline.get("mime_type") or "application/octet-stream").lower()
            out.append((mime, raw))
    return out


def _best_image(images: List[Tuple[str, bytes]]) -> Optional[Tuple[str, bytes]]:
    if not images:
        return None
    scored: List[Tuple[int, int, Tuple[str, bytes]]] = []
    for mime, raw in images:
        scored.append((1 if "png" in mime else 0, len(raw), (mime, raw)))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return scored[0][2]


def _infer_image_mime(path: Path, raw: bytes) -> str:
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(raw) >= 12 and raw[0:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    raise RuntimeError(f"不支持的图片格式：{path}")


def part_from_image_path(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    mime = _infer_image_mime(path, raw)
    return {
        "inlineData": {
            "mimeType": mime,
            "data": base64.b64encode(raw).decode("ascii"),
        }
    }


def generate_text(
    *,
    cfg: GeminiConfig,
    parts: List[Dict[str, Any]],
    debug_dir: Optional[Path] = None,
    timeout_s: int = 120,
    temperature: float = 0.1,
    max_output_tokens: int = 1200,
) -> Tuple[str, Dict[str, Any]]:
    payload: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": float(temperature),
            "maxOutputTokens": int(max_output_tokens),
        },
    }
    _write_debug_request(debug_dir, cfg, payload)
    resp = generate_content(cfg, payload, timeout_s=timeout_s)
    _write_debug_response(debug_dir, resp)
    return _extract_text(resp), resp


def _choose_aspect_ratio(w: int, h: int) -> str:
    ratios = {
        "16:9": 16 / 9,
        "9:16": 9 / 16,
        "4:3": 4 / 3,
        "3:4": 3 / 4,
        "3:2": 3 / 2,
        "2:3": 2 / 3,
        "1:1": 1.0,
        "5:4": 5 / 4,
        "4:5": 4 / 5,
        "21:9": 21 / 9,
        "1:4": 1 / 4,
        "4:1": 4 / 1,
    }
    target = (w / max(1, h)) if h else 1.0
    return min(ratios.items(), key=lambda item: abs(item[1] - target))[0]


def _target_4k_dims(canvas_w: int, canvas_h: int) -> Tuple[int, int]:
    long_edge = 3840
    w = max(1, int(canvas_w))
    h = max(1, int(canvas_h))
    if w >= h:
        return long_edge, max(1, int(round(long_edge * (h / w))))
    return max(1, int(round(long_edge * (w / h)))), long_edge


def _maybe_resize_to_canvas(path: Path, *, target_w: int, target_h: int) -> None:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        warn("缺少 Pillow，跳过 PNG 尺寸对齐。")
        return
    try:
        with Image.open(path) as img:
            w, h = img.size
            if w == target_w and h == target_h:
                return
            scale = min(target_w / max(1, w), target_h / max(1, h))
            new_w = max(1, int(math.floor(w * scale)))
            new_h = max(1, int(math.floor(h * scale)))
            resized = img.convert("RGBA").resize((new_w, new_h), resample=Image.LANCZOS)
            canvas = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 255))
            ox = (target_w - new_w) // 2
            oy = (target_h - new_h) // 2
            canvas.paste(resized, (ox, oy), resized)
            canvas.convert("RGB").save(path, format="PNG", optimize=True)
    except Exception as exc:
        warn(f"PNG 尺寸对齐失败（已忽略）：{exc}")


def _parse_retry_after(detail: str) -> Optional[float]:
    m = re.search(r"retry\\s+in\\s+([0-9]+(?:\\.[0-9]+)?)s", detail, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def generate_png(
    *,
    cfg: GeminiConfig,
    prompt: str,
    output_png: Path,
    canvas_w: int,
    canvas_h: int,
    reference_images: Optional[List[Path]] = None,
    debug_dir: Optional[Path] = None,
    timeout_s: int = 180,
    retries: int = 5,
) -> Dict[str, Any]:
    refs = [Path(p) for p in (reference_images or [])]
    parts = [part_from_image_path(ref) for ref in refs]
    parts.append({"text": prompt})
    payload: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0.2,
            "imageConfig": {
                "aspectRatio": _choose_aspect_ratio(canvas_w, canvas_h),
                "imageSize": "4K",
            },
        },
    }
    _write_debug_request(debug_dir, cfg, payload)

    last_error: Optional[Exception] = None
    response: Dict[str, Any] = {}
    for attempt in range(1, max(1, retries) + 1):
        try:
            response = generate_content(cfg, payload, timeout_s=timeout_s)
            last_error = None
            break
        except GeminiHTTPError as exc:
            last_error = exc
            if exc.code not in {429, 503} or attempt >= retries:
                break
            wait_s = _parse_retry_after(exc.detail) or min(30.0, 2.0**attempt)
            warn(f"Gemini 限流/资源忙，{wait_s:.1f}s 后重试（{attempt}/{retries}）。")
            time.sleep(max(0.5, wait_s))
        except Exception as exc:
            last_error = exc
            break

    if last_error is not None:
        raise last_error

    _write_debug_response(debug_dir, response)
    best = _best_image(_extract_inline_images(response))
    if best is None:
        excerpt = json.dumps(response, ensure_ascii=False)[:800]
        raise RuntimeError(f"未从 Gemini 响应中提取到图片。response_excerpt={excerpt}")
    mime, raw = best
    output_png.parent.mkdir(parents=True, exist_ok=True)
    output_png.write_bytes(raw)
    target_w, target_h = _target_4k_dims(canvas_w, canvas_h)
    _maybe_resize_to_canvas(output_png, target_w=target_w, target_h=target_h)
    return {
        "mime_type": mime,
        "output_png": str(output_png),
        "target_size": {"width": target_w, "height": target_h},
        "response_path": str(debug_dir / "response.json") if debug_dir is not None else None,
    }
