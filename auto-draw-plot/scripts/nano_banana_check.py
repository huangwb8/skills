#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import expand_path
from image_provider_client import health_check_image_provider


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 auto-draw-plot 图片 provider 配置（兼容旧 Nano Banana 检查入口）。")
    parser.add_argument("--api-env", default="", help="remote.env 路径，默认 ~/.bensz-skills/config/remote.env")
    parser.add_argument("--provider", default="auto", help="图片 provider：auto（默认）/ gpt-image-2 / nano_banana")
    args = parser.parse_args()

    cfg = health_check_image_provider(
        remote_env_path=expand_path(args.api_env) if args.api_env else None,
        provider_name=str(args.provider or "auto"),
    )
    print(
        f"OK {cfg.preflight_status} provider={cfg.provider} model={cfg.model} base_url={cfg.base_url} "
        f"scope={cfg.preflight_scope} generation_eligible={cfg.generation_eligibility}"
    )


if __name__ == "__main__":
    main()
