#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from common import expand_path, load_config, warn, write_json
from image_provider_client import (
    ImageProviderConfig,
    generate_image_png,
    resolve_image_provider,
)
from nano_banana_client import load_gemini_config


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
    try:
        result = generate_image_png(
            provider_cfg=provider_cfg,
            prompt=prompt,
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
                    "error": str(gpt_error),
                    "reference_image_count": len(reference_images or []),
                },
            )
        if not allow_provider_fallback:
            raise RuntimeError(
                "gpt-image-2 生成失败，未切换到其他图片模型。"
                "只有用户明确要求允许模型回退时，才会改用 Nano Banana/Gemini。"
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
            prompt=prompt,
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
        )
    if debug_dir is not None:
        write_json(debug_dir / "image-generation.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="调用图片 provider 生成 PNG；默认不在生成失败后自动切换模型。")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt-file", help="prompt 文件路径")
    group.add_argument("--prompt-text", help="直接传入 prompt 文本")
    parser.add_argument("--output-png", required=True, help="输出 PNG 路径")
    parser.add_argument("--api-env", default="", help="remote.env 路径，默认 ~/.bensz-skills/config/remote.env")
    parser.add_argument("--canvas-width", type=int, default=1600, help="期望布局宽度/宽高比参考，不承诺最终 PNG 像素")
    parser.add_argument("--canvas-height", type=int, default=900, help="期望布局高度/宽高比参考，不承诺最终 PNG 像素")
    parser.add_argument("--postprocess-resize", action="store_true", default=None, help="显式启用后处理尺寸对齐；默认保留 provider 原生输出")
    parser.add_argument("--postprocess-width", type=int, default=0, help="后处理目标宽度；需配合 --postprocess-resize")
    parser.add_argument("--postprocess-height", type=int, default=0, help="后处理目标高度；需配合 --postprocess-resize")
    parser.add_argument("--debug-dir", default="", help="调试目录")
    parser.add_argument("--reference-image", action="append", default=[], help="可重复传入参考图路径")
    parser.add_argument("--provider", default="auto", help="图片 provider：auto（默认）/ gpt-image-2 / nano_banana")
    parser.add_argument("--allow-provider-fallback", action="store_true", help="生成失败后允许从 gpt-image-2 切到 Nano Banana/Gemini")
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
        output_png=expand_path(args.output_png, base=Path.cwd()),
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
    )
    print(result["output_png"])


if __name__ == "__main__":
    main()
