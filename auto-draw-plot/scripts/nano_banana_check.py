#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import expand_path
from image_provider_client import health_check_image_provider


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 auto-draw-plot 图片 provider 配置（兼容旧 Nano Banana 检查入口）。")
    parser.add_argument("--api-env", default="", help="remote.env 路径，默认 ~/.bensz-skills/config/remote.env")
    args = parser.parse_args()

    cfg = health_check_image_provider(
        remote_env_path=expand_path(args.api_env) if args.api_env else None,
    )
    print(f"OK provider={cfg.provider} model={cfg.model} base_url={cfg.base_url}")


if __name__ == "__main__":
    main()
