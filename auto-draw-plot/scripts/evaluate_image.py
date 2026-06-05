#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, Optional

from common import expand_path, extract_json_from_text, load_config, read_text, sha256_file, write_json
from modes import DrawMode, mode_evaluation_lines, mode_prompt_lines
from nano_banana_client import generate_text, load_gemini_config, part_from_image_path


def evaluate_image(
    *,
    image_path: Path,
    request_text: str,
    image_prompt: str,
    remote_env: Optional[Path],
    output_json: Optional[Path],
    debug_dir: Optional[Path],
    mode: Optional[DrawMode] = None,
) -> Dict[str, Any]:
    cfg = load_config()
    eval_cfg = cfg.get("evaluation", {}) or {}
    gemini_cfg = load_gemini_config(remote_env_path=remote_env)

    review_prompt = "\n".join(
        [
            "你是一位严格但建设性的视觉评审。",
            "请根据用户需求、当前图片 prompt 与提供的图片本身，判断这张图是否足够满足要求。",
            "输出必须是原始 JSON，不要加 Markdown 代码块，不要解释。",
            "JSON schema:",
            "{",
            '  "score": 0.0,',
            '  "passed": false,',
            '  "summary": "一句话总结",',
            '  "strengths": ["..."],',
            '  "issues": ["..."],',
            '  "must_fix": ["..."],',
            '  "prompt_patch": ["下一轮 prompt 应补充的指令"],',
            '  "confidence": 0.0',
            "}",
            "",
            "评分标准：",
            "- 需求覆盖度",
            "- 主体是否清晰",
            "- 画面结构是否稳定",
            "- 若含文字，文字是否尽量清晰可读",
            "- 是否有明显伪影、水印、乱码或离题",
            *(["", "模式检查：", *mode_prompt_lines(mode)] if mode is not None else []),
            *(mode_evaluation_lines(mode) if mode is not None else []),
            "",
            "用户需求：",
            request_text.strip(),
            "",
            "当前图片 prompt：",
            image_prompt.strip(),
        ]
    )

    text, _resp = generate_text(
        cfg=gemini_cfg,
        parts=[{"text": review_prompt}, part_from_image_path(image_path)],
        debug_dir=debug_dir,
        timeout_s=int((cfg.get("api", {}) or {}).get("request_timeout_s", 180)),
        temperature=float(eval_cfg.get("evaluation_temperature", 0.1)),
        max_output_tokens=int(eval_cfg.get("evaluation_max_tokens", 1200)),
    )
    payload = extract_json_from_text(text) or salvage_evaluation_payload(text)
    normalized = normalize_evaluation(
        payload=payload,
        raw_text=text,
        image_path=image_path,
        cfg=eval_cfg,
    )
    if output_json is not None:
        write_json(output_json, normalized)
    return normalized


def normalize_evaluation(
    *,
    payload: Dict[str, Any],
    raw_text: str,
    image_path: Path,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    score = _coerce_float(payload.get("score"), default=0.0)
    passed = bool(payload.get("passed", False))
    strengths = _normalize_text_list(payload.get("strengths"))
    issues = _normalize_text_list(payload.get("issues"))
    must_fix = _normalize_text_list(payload.get("must_fix"))
    prompt_patch = _normalize_text_list(payload.get("prompt_patch"))
    confidence = _coerce_float(payload.get("confidence"), default=0.0)
    if confidence > 1.0 and confidence <= 10.0:
        confidence = confidence / 10.0
    summary = str(payload.get("summary") or "").strip()

    if not summary:
        summary = "模型未返回结构化总结，需人工复核。"
    if score >= float(cfg.get("accept_score", 8.5)):
        passed = True
    return {
        "score": round(score, 2),
        "passed": passed,
        "summary": summary,
        "strengths": strengths,
        "issues": issues,
        "must_fix": must_fix,
        "prompt_patch": prompt_patch,
        "confidence": round(confidence, 2),
        "image_sha256": sha256_file(image_path),
        "raw_text": raw_text,
    }


def heuristic_evaluation(image_path: Path) -> Dict[str, Any]:
    cfg = load_config()
    eval_cfg = cfg.get("evaluation", {}) or {}
    long_edge = 0
    try:
        from PIL import Image  # type: ignore

        with Image.open(image_path) as img:
            long_edge = max(img.size)
    except Exception:
        long_edge = 0

    size_bytes = image_path.stat().st_size if image_path.exists() else 0
    # Heuristic fallback is intentionally capped below accept_score; it proves
    # the file is non-empty/resolution-sane but cannot certify semantic quality.
    score = 4.5
    strengths = []
    issues = []
    if size_bytes >= int(eval_cfg.get("heuristic_min_file_size_bytes", 8192)):
        score += 1.0
        strengths.append("PNG 文件体积正常，说明图像并非空白占位。")
    else:
        issues.append("PNG 文件过小，可能生成失败或接近空白。")
    if long_edge >= int(eval_cfg.get("heuristic_min_long_edge_px", 1800)):
        score += 1.0
        strengths.append("PNG 分辨率达到基本可用级别。")
    else:
        issues.append("PNG 分辨率偏低，建议重新生成。")
    return {
        "score": round(score, 2),
        "passed": False,
        "summary": "已退化为启发式评估，请人工确认视觉质量。",
        "strengths": strengths,
        "issues": issues or ["缺少 AI 视觉评估结果。"],
        "must_fix": issues,
        "prompt_patch": ["重新强调主体清晰、结构稳定、文字可读。"],
        "confidence": 0.2,
        "image_sha256": sha256_file(image_path) if image_path.exists() else "",
        "raw_text": "",
        "fallback_mode": "heuristic",
    }


def salvage_evaluation_payload(text: str) -> Dict[str, Any]:
    raw = text or ""
    payload: Dict[str, Any] = {}

    score = _search_number(raw, r'"score"\s*:\s*([0-9]+(?:\.[0-9]+)?)')
    if score is not None:
        payload["score"] = score

    passed = re.search(r'"passed"\s*:\s*(true|false)', raw, flags=re.IGNORECASE)
    if passed:
        payload["passed"] = passed.group(1).lower() == "true"

    summary = _search_string_block(raw, "summary")
    if summary:
        payload["summary"] = summary

    for key in ("strengths", "issues", "must_fix", "prompt_patch"):
        arr = _search_string_array(raw, key)
        if arr:
            payload[key] = arr

    confidence = _search_number(raw, r'confidence"?\s*:\s*([0-9]+(?:\.[0-9]+)?)')
    if confidence is not None:
        payload["confidence"] = confidence
    return payload


def _coerce_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _search_number(text: str, pattern: str) -> Optional[float]:
    m = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _search_string_block(text: str, key: str) -> str:
    m = re.search(
        rf'"{re.escape(key)}"\s*:\s*"(?P<body>.*?)"\s*,\s*"',
        text,
        flags=re.DOTALL,
    )
    if not m:
        m = re.search(
            rf'"{re.escape(key)}"\s*:\s*"(?P<body>.*?)"\s*[,\n]\s*[A-Za-z"]',
            text,
            flags=re.DOTALL,
        )
    if not m:
        return ""
    return _clean_multiline_fragment(m.group("body"))


def _search_string_array(text: str, key: str) -> list[str]:
    m = re.search(
        rf'"{re.escape(key)}"\s*:\s*\[(?P<body>.*?)\]',
        text,
        flags=re.DOTALL,
    )
    if not m:
        return []
    items = re.findall(r'"(.*?)"', m.group("body"), flags=re.DOTALL)
    return [_clean_multiline_fragment(item) for item in items if _clean_multiline_fragment(item)]


def _clean_multiline_fragment(text: str) -> str:
    cleaned = text.replace("\\n", "\n")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" ,\n\t")


def main() -> None:
    parser = argparse.ArgumentParser(description="对 auto-draw-plot 生成结果做 AI 视觉评估。")
    parser.add_argument("--image", required=True, help="待评估 PNG 路径")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--request-file", help="用户需求文件")
    group.add_argument("--request-text", help="用户需求文本")
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt-file", help="生成该图片的 prompt 文件")
    prompt_group.add_argument("--prompt-text", help="生成该图片的 prompt 文本")
    parser.add_argument("--output-json", default="", help="输出 JSON 路径")
    parser.add_argument("--api-env", default="", help="remote.env 路径")
    parser.add_argument("--debug-dir", default="", help="调试目录")
    args = parser.parse_args()

    request_text = read_text(Path(args.request_file)) if args.request_file else str(args.request_text or "")
    image_prompt = read_text(Path(args.prompt_file)) if args.prompt_file else str(args.prompt_text or "")

    image_path = expand_path(args.image, base=Path.cwd())
    output_json = expand_path(args.output_json, base=Path.cwd()) if args.output_json else None
    debug_dir = expand_path(args.debug_dir, base=Path.cwd()) if args.debug_dir else None
    remote_env = expand_path(args.api_env, base=Path.cwd()) if args.api_env else None

    try:
        evaluation = evaluate_image(
            image_path=image_path,
            request_text=request_text,
            image_prompt=image_prompt,
            remote_env=remote_env,
            output_json=output_json,
            debug_dir=debug_dir,
        )
    except Exception:
        evaluation = heuristic_evaluation(image_path)
        if output_json is not None:
            write_json(output_json, evaluation)
    print(evaluation["summary"])


if __name__ == "__main__":
    main()
