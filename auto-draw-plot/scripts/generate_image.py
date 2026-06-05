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
) -> Dict[str, Any]:
    cfg = load_config()
    api_cfg = cfg.get("api", {}) or {}
    provider_cfg = provider_cfg or resolve_image_provider(remote_env_path=remote_env, run_healthcheck=False)
    if provider_cfg.provider == "gpt-image-2" and reference_images:
        try:
            gemini_cfg = load_gemini_config(remote_env_path=remote_env)
            provider_cfg = ImageProviderConfig(
                provider="nano_banana",
                base_url=gemini_cfg.base_url,
                api_key=gemini_cfg.api_key,
                model=gemini_cfg.model,
                env_path=gemini_cfg.env_path,
                source="reference-image-fallback",
            )
            warn("检测到 reference_images；当前 gpt-image-2 生成路径不消费参考图，已优先使用 Nano Banana。")
        except Exception:
            warn("检测到 reference_images，但 Nano Banana 配置不可用；将继续尝试 gpt-image-2 文本生成。")
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
        )
    except Exception as exc:
        if provider_cfg.provider != "gpt-image-2":
            raise
        warn(f"gpt-image-2 生成失败，回退到 Nano Banana/Gemini：{exc}")
        gpt_error = exc
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
        )
    if debug_dir is not None:
        write_json(debug_dir / "image-generation.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="调用图片 provider 生成 PNG，默认 gpt-image-2 优先，失败回退 Nano Banana/Gemini。")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt-file", help="prompt 文件路径")
    group.add_argument("--prompt-text", help="直接传入 prompt 文本")
    parser.add_argument("--output-png", required=True, help="输出 PNG 路径")
    parser.add_argument("--api-env", default="", help="remote.env 路径，默认 ~/.bensz-skills/config/remote.env")
    parser.add_argument("--canvas-width", type=int, default=1600)
    parser.add_argument("--canvas-height", type=int, default=900)
    parser.add_argument("--debug-dir", default="", help="调试目录")
    parser.add_argument("--reference-image", action="append", default=[], help="可重复传入参考图路径")
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
    )
    print(result["output_png"])


if __name__ == "__main__":
    main()
