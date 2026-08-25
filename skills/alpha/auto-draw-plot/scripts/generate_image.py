#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from common import expand_path, load_config, warn, write_json
from image_provider_client import (
    ImageProviderConfig,
    generate_image_png,
    is_provider_fallback_allowed,
    provider_error_debug_payload,
    resolve_image_provider,
)
from nano_banana_client import load_gemini_config


def _reference_preservation_prompt(prompt: str, reference_images: Optional[List[Path]]) -> str:
    if not reference_images:
        return prompt
    return "\n".join(
        [
            prompt.rstrip(),
            "",
            "Reference edit contract:",
            "- preserve_subject=true except for the explicitly requested edit",
            "- preserve_composition=true except for the explicitly requested edit",
            "- preserve_background=true except for the explicitly requested edit",
            "- change only what the request explicitly asks to change",
        ]
    )


def generate_image(
    *,
    prompt: str,
    output_png: Path,
    remote_env: Optional[Path],
    canvas_w: int,
    canvas_h: int,
    debug_dir: Optional[Path],
    reference_images: Optional[List[Path]],
    provider_cfg: Optional[ImageProviderConfig] = None,
    provider_name: Optional[str] = None,
    allow_provider_fallback: Optional[bool] = None,
    require_reference_images: bool = False,
    postprocess_resize: Optional[bool] = None,
    postprocess_w: Optional[int] = None,
    postprocess_h: Optional[int] = None,
    quality: Optional[str] = None,
    provider_size: Optional[str] = None,
    output_format: Optional[str] = None,
    output_compression: Optional[int] = None,
) -> Dict[str, Any]:
    cfg = load_config()
    api_cfg = cfg.get("api", {}) or {}
    gen_cfg = cfg.get("generation", {}) or {}
    if allow_provider_fallback is None:
        allow_provider_fallback = bool(api_cfg.get("allow_provider_fallback", False))
    if postprocess_resize is None:
        postprocess_resize = bool(gen_cfg.get("postprocess_resize_default", False))
    if require_reference_images and not reference_images:
        raise ValueError("当前生成轮次要求参考图，但 reference_images 为空。")
    provider_cfg = provider_cfg or resolve_image_provider(
        remote_env_path=remote_env,
        provider_name=provider_name,
        run_healthcheck=False,
    )
    effective_prompt = _reference_preservation_prompt(prompt, reference_images)
    try:
        result = generate_image_png(
            provider_cfg=provider_cfg,
            prompt=effective_prompt,
            output_png=output_png,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            reference_images=reference_images,
            debug_dir=debug_dir,
            timeout_s=int(api_cfg.get("request_timeout_s", 180)),
            retries=int(api_cfg.get("retry_attempts", 5)),
            postprocess_resize=bool(postprocess_resize),
            postprocess_w=postprocess_w,
            postprocess_h=postprocess_h,
            quality=quality,
            provider_size=provider_size,
            output_format=output_format,
            output_compression=output_compression,
        )
    except Exception as exc:
        if provider_cfg.provider != "gpt-image-2":
            raise
        gpt_error = exc
        if debug_dir is not None:
            write_json(
                debug_dir / "gpt-image-2-error.json",
                {
                    "provider": provider_cfg.provider,
                    "model": provider_cfg.model,
                    "base_url": provider_cfg.base_url,
                    "error": provider_error_debug_payload(gpt_error),
                    "reference_image_count": len(reference_images or []),
                },
            )
        if not allow_provider_fallback:
            raise RuntimeError(
                "gpt-image-2 生成失败，未切换到其他图片模型。"
                "只有用户明确要求允许模型回退时，才会改用 Nano Banana/Gemini。"
                f"错误：{gpt_error}"
            ) from gpt_error
        if not is_provider_fallback_allowed(gpt_error):
            raise RuntimeError(
                "gpt-image-2 请求已被服务端计费、权限或客户端策略拒绝，未跨 provider 回退。"
                "请根据结构化错误码修复订阅、余额、权限或计费服务状态后重试。"
                f"错误：{gpt_error}"
            ) from gpt_error
        warn(f"gpt-image-2 生成失败，用户已允许回退，改用 Nano Banana/Gemini：{exc}")
        try:
            gemini_cfg = load_gemini_config(remote_env_path=remote_env)
        except Exception as gemini_exc:
            raise RuntimeError(f"gpt-image-2 生成失败，且 Nano Banana/Gemini 回退不可用：gpt={gpt_error}; gemini={gemini_exc}") from gemini_exc
        result = generate_image_png(
            provider_cfg=ImageProviderConfig(
                provider="nano_banana",
                base_url=gemini_cfg.base_url,
                api_key=gemini_cfg.api_key,
                model=gemini_cfg.model,
                env_path=gemini_cfg.env_path,
                source="fallback",
            ),
            prompt=effective_prompt,
            output_png=output_png,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            reference_images=reference_images,
            debug_dir=debug_dir,
            timeout_s=int(api_cfg.get("request_timeout_s", 180)),
            retries=int(api_cfg.get("retry_attempts", 5)),
            postprocess_resize=bool(postprocess_resize),
            postprocess_w=postprocess_w,
            postprocess_h=postprocess_h,
            quality=quality,
            provider_size=provider_size,
            output_format=output_format,
            output_compression=output_compression,
        )
    if debug_dir is not None:
        write_json(debug_dir / "image-generation.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="调用图片 provider 生成图片；gpt-image-2 默认请求低画质 JPEG。")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt-file", help="prompt 文件路径")
    group.add_argument("--prompt-text", help="直接传入 prompt 文本")
    parser.add_argument("--output-image", "--output-png", dest="output_image", required=True, help="输出图片路径；--output-png 为兼容别名")
    parser.add_argument("--api-env", default="", help="remote.env 路径，默认 ~/.bensz-skills/config/remote.env")
    parser.add_argument("--canvas-width", type=int, default=1600, help="期望布局宽度/宽高比参考，不承诺最终图片像素")
    parser.add_argument("--canvas-height", type=int, default=900, help="期望布局高度/宽高比参考，不承诺最终图片像素")
    parser.add_argument("--postprocess-resize", action="store_true", default=None, help="显式启用后处理尺寸对齐；默认保留 provider 原生输出")
    parser.add_argument("--postprocess-width", type=int, default=0, help="后处理目标宽度；需配合 --postprocess-resize")
    parser.add_argument("--postprocess-height", type=int, default=0, help="后处理目标高度；需配合 --postprocess-resize")
    parser.add_argument("--quality", default="", help="gpt-image-2 quality：low/medium/high/auto")
    parser.add_argument("--provider-size", default="", help="gpt-image-2 原生尺寸枚举，默认 1024x1024")
    parser.add_argument("--output-format", default="", help="gpt-image-2 输出格式：jpeg/png/webp")
    parser.add_argument("--output-compression", type=int, default=-1, help="输出压缩 0-100；默认使用配置值")
    parser.add_argument("--debug-dir", default="", help="调试目录")
    parser.add_argument("--reference-image", action="append", default=[], help="可重复传入参考图路径")
    parser.add_argument("--provider", default="auto", help="图片 provider：auto（默认）/ gpt-image-2 / nano_banana")
    parser.add_argument(
        "--allow-provider-fallback",
        action="store_true",
        help="provider 故障时允许从 gpt-image-2 切到 Nano Banana/Gemini；计费、权限与客户端策略错误仍不回退",
    )
    parser.add_argument("--require-reference-images", action="store_true", help="传入参考图时必须使用可消费参考图的 provider")
    args = parser.parse_args()

    prompt = (
        Path(args.prompt_file).read_text(encoding="utf-8")
        if args.prompt_file
        else str(args.prompt_text or "").strip()
    )
    if not prompt.strip():
        raise SystemExit("prompt 不能为空。")

    result = generate_image(
        prompt=prompt,
        output_png=expand_path(args.output_image, base=Path.cwd()),
        remote_env=expand_path(args.api_env, base=Path.cwd()) if args.api_env else None,
        canvas_w=int(args.canvas_width),
        canvas_h=int(args.canvas_height),
        debug_dir=expand_path(args.debug_dir, base=Path.cwd()) if args.debug_dir else None,
        reference_images=[expand_path(item, base=Path.cwd()) for item in (args.reference_image or [])],
        provider_name=str(args.provider or "auto"),
        allow_provider_fallback=bool(args.allow_provider_fallback),
        require_reference_images=bool(args.require_reference_images),
        postprocess_resize=args.postprocess_resize,
        postprocess_w=int(args.postprocess_width) or None,
        postprocess_h=int(args.postprocess_height) or None,
        quality=args.quality or None,
        provider_size=args.provider_size or None,
        output_format=args.output_format or None,
        output_compression=args.output_compression if args.output_compression >= 0 else None,
    )
    print(result.get("output_file") or result["output_png"])


if __name__ == "__main__":
    main()
