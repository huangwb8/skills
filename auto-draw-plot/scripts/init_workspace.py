#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Optional

from common import ensure_dir, expand_path, fatal, load_config, now_tag, write_json, write_text


def init_workspace(
    *,
    project_root: Path,
    workspace_base: Optional[str],
    output_png: Optional[str],
    run_id: Optional[str],
    allow_outside_project: bool = False,
) -> Dict[str, Any]:
    cfg = load_config()
    workspace_cfg = cfg.get("workspace", {}) or {}
    reports_cfg = cfg.get("reports", {}) or {}
    generation_cfg = cfg.get("generation", {}) or {}

    if workspace_base:
        hidden_root = expand_path(workspace_base, base=project_root)
    else:
        hidden_root = expand_path(str(workspace_cfg.get("hidden_dir", ".draw-plot")), base=project_root)

    prefix = str(workspace_cfg.get("run_prefix", "run-"))
    timestamp_fmt = str(workspace_cfg.get("timestamp_format", "%Y%m%d%H%M%S%f"))
    if run_id:
        normalized_run_id = run_id if run_id.startswith(prefix) else f"{prefix}{run_id}"
    else:
        normalized_run_id = f"{prefix}{now_tag(timestamp_fmt)}"

    run_dir = ensure_dir(hidden_root / normalized_run_id)
    subdirs = {name: ensure_dir(run_dir / str(name)) for name in (workspace_cfg.get("subdirs") or [])}
    latest_run_pointer = hidden_root / str(workspace_cfg.get("latest_run_pointer", "latest-run.txt"))
    write_text(latest_run_pointer, normalized_run_id + "\n")

    if output_png:
        public_output_png = expand_path(output_png, base=project_root)
    else:
        public_output_png = project_root / str(generation_cfg.get("default_output_name", "draw-plot.png"))
    allow_external = bool(allow_outside_project or workspace_cfg.get("allow_outside_project", False))
    if not allow_external:
        if not _is_within(hidden_root, project_root):
            fatal("workspace_base 必须位于 project_root 内；如确需写到外部路径，请显式允许 outside project。")
        if not _is_within(public_output_png.resolve().parent, project_root):
            fatal("output_png 必须位于 project_root 内；如确需写到外部路径，请显式允许 outside project。")

    manifest = {
        "project_root": str(project_root.resolve()),
        "workspace_root": str(hidden_root.resolve()),
        "run_id": normalized_run_id,
        "run_dir": str(run_dir.resolve()),
        "workspace_inside_project_root": _is_within(hidden_root, project_root),
        "public_output_png": str(public_output_png.resolve()),
        "public_output_dir": str(public_output_png.resolve().parent),
        "requests_dir": str(subdirs.get("requests", run_dir / "requests")),
        "rounds_dir": str(subdirs.get("rounds", run_dir / "rounds")),
        "meta_dir": str(subdirs.get("meta", run_dir / "meta")),
        "exports_dir": str(subdirs.get("exports", run_dir / "exports")),
        "parallel_vibe_dir": str(subdirs.get("parallel-vibe", run_dir / "parallel-vibe")),
        "request_file": str((subdirs.get("requests", run_dir / "requests") / "user-need.md").resolve()),
        "analysis_json": str((run_dir / str(reports_cfg.get("analysis_json", "meta/analysis.json"))).resolve()),
        "result_json": str((run_dir / str(reports_cfg.get("result_json", "meta/result.json"))).resolve()),
    }
    write_json(run_dir / str(reports_cfg.get("run_manifest", "run-manifest.json")), manifest)
    return manifest


def _is_within(target: Path, base: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化 auto-draw-plot 隐藏工作区。")
    parser.add_argument("--project-root", default=".", help="项目根目录，默认当前目录")
    parser.add_argument("--workspace-base", default="", help="自定义隐藏工作区根目录")
    parser.add_argument("--output-png", default="", help="最终公开输出 PNG 路径")
    parser.add_argument("--run-id", default="", help="指定 run id（可选）")
    parser.add_argument("--allow-outside-project", action="store_true", help="允许 workspace/output 写到 project_root 外部")
    args = parser.parse_args()

    manifest = init_workspace(
        project_root=expand_path(args.project_root, base=Path.cwd()),
        workspace_base=args.workspace_base or None,
        output_png=args.output_png or None,
        run_id=args.run_id or None,
        allow_outside_project=bool(args.allow_outside_project),
    )
    write_json(Path(manifest["run_dir"]) / "init-output.json", manifest)
    print(manifest["run_dir"])


if __name__ == "__main__":
    main()
