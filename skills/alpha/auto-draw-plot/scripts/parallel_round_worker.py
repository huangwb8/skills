#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_dir, read_text, write_text


def main() -> None:
    parser = argparse.ArgumentParser(description="parallel-vibe round worker for auto-draw-plot")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--request-file", required=True)
    parser.add_argument("--round", required=True, type=int)
    parser.add_argument("--result-file", default="RESULT.md")
    parser.add_argument("--wrapped-prompt", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        run_dir.mkdir(parents=True, exist_ok=True)
    if not run_dir.is_dir():
        raise ValueError(f"--run-dir 不是目录: {run_dir}")

    request_text = read_text(Path(args.request_file))
    round_dir = ensure_dir(run_dir / f"round-{int(args.round):02d}")
    prompt_path = round_dir / "prompt.txt"
    eval_req = round_dir / "evaluation-request.md"
    prompt_body = "\n".join(
        [
            "请基于以下用户需求，为当前图片生成 provider 生成一段更具体的图片 prompt：",
            "",
            request_text.strip(),
            "",
            "请确保主体清晰、结构稳定、文字短且可读，不要引入无关元素。",
        ]
    )
    write_text(prompt_path, prompt_body + "\n")
    write_text(
        eval_req,
        "本文件由 parallel-vibe worker 生成，用于提示下一阶段做视觉评估。\n",
    )
    result_path = (run_dir / args.result_file).resolve()
    try:
        result_path.relative_to(run_dir)
    except ValueError as exc:
        raise ValueError("--result-file 必须位于 --run-dir 内") from exc
    write_text(
        result_path,
        "\n".join(
            [
                "# auto-draw-plot parallel round",
                "",
                f"- round: `{int(args.round):02d}`",
                f"- prompt_file: `{prompt_path.name}`",
                f"- evaluation_request: `{eval_req.name}`",
                "",
                "本 worker 只负责在隔离 workspace 内生成本轮 prompt 草案，真正的图片生成与评估由主流程脚本执行。",
            ]
        )
        + "\n",
    )


if __name__ == "__main__":
    main()
