#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Any, Dict

from common import expand_path, load_config, skill_root, slugify, write_json


def build_parallel_plan(
    *,
    run_dir: Path,
    request_file: Path,
    round_index: int,
    output_plan: Path,
) -> Dict[str, Any]:
    cfg = load_config()
    pv_cfg = cfg.get("parallel_vibe", {}) or {}
    runner_script = skill_root() / str(pv_cfg.get("worker_script", "scripts/parallel_round_worker.py"))
    round_name = f"{cfg.get('generation', {}).get('round_dir_prefix', 'round-')}{round_index:02d}"
    thread_id = f"{round_index:03d}"
    plan = {
        "threads": [
            {
                "thread_id": thread_id,
                "title": f"auto-draw-plot {round_name}",
                "runner": {
                    "type": str(pv_cfg.get("default_runner", "shell")),
                    "profile": str(pv_cfg.get("default_profile", "deep")),
                    "cmd_template": (
                        f"python3 {shlex.quote(str(runner_script))} "
                        f"--run-dir {shlex.quote(str(run_dir))} "
                        f"--request-file {shlex.quote(str(request_file))} "
                        f"--round {round_index} "
                        f"--result-file {shlex.quote(str(pv_cfg.get('result_filename', 'RESULT.md')))}"
                    ),
                },
                "prompt": (
                    "在当前 workspace 内完成本轮 prompt 优化草案：读取用户需求与已有 round 记录，"
                    "输出 `prompt.txt`、`evaluation-request.md` 与 `RESULT.md`。"
                ),
            }
        ],
        "synthesize": False,
        "project_hint": slugify(request_file.stem, max_len=32),
    }
    write_json(output_plan, plan)
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="为 auto-draw-plot 生成 parallel-vibe plan.json。")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--request-file", required=True)
    parser.add_argument("--round", required=True, type=int)
    parser.add_argument("--output-plan", default="")
    args = parser.parse_args()

    run_dir = expand_path(args.run_dir, base=Path.cwd())
    request_file = expand_path(args.request_file, base=Path.cwd())
    cfg = load_config()
    default_plan_name = str((cfg.get("parallel_vibe", {}) or {}).get("plan_filename", "parallel-plan.json"))
    output_plan = expand_path(args.output_plan, base=Path.cwd()) if args.output_plan else run_dir / "parallel-vibe" / default_plan_name
    build_parallel_plan(run_dir=run_dir, request_file=request_file, round_index=int(args.round), output_plan=output_plan)
    print(output_plan)


if __name__ == "__main__":
    main()
