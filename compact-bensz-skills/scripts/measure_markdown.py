#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import (
    build_totals,
    compute_file_record,
    ensure_workspace,
    iter_markdown_files,
    load_config,
    resolve_skill_root,
    resolve_workspace_root,
    write_json,
    write_text,
)


def format_delta(before: dict[str, int], after: dict[str, int]) -> str:
    delta_words = after["total_words"] - before["total_words"]
    delta_chars = after["total_chars"] - before["total_chars"]
    lines = [
        "# 压缩统计对比",
        "",
        f"- 压缩前总词数：{before['total_words']}",
        f"- 压缩后总词数：{after['total_words']}",
        f"- 词数变化：{delta_words}",
        f"- 压缩前总字符数：{before['total_chars']}",
        f"- 压缩后总字符数：{after['total_chars']}",
        f"- 字符变化：{delta_chars}",
        "",
        "## 当前最大文件",
        "",
    ]
    for record in sorted(after["files"], key=lambda item: item["words"], reverse=True)[:5]:
        lines.append(f"- `{record['path']}`：{record['words']} 词，{record['chars']} 字符")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="统计目标 skill Markdown 体积")
    parser.add_argument("--skill-root", required=True, help="目标 skill 根目录")
    parser.add_argument(
        "--phase",
        default="after",
        choices=["before", "after"],
        help="写入前/后统计文件",
    )
    parser.add_argument("--workspace-dir", help="自定义隐藏工作区")
    parser.add_argument("--run-id", help="复用 init_workspace.py 创建的 run 目录名")
    args = parser.parse_args()

    config = load_config()
    target_skill_root = resolve_skill_root(args.skill_root)
    workspace_root = resolve_workspace_root(
        target_skill_root,
        config,
        args.workspace_dir,
        run_id=args.run_id,
    )
    paths = ensure_workspace(config, workspace_root)
    markdown_files = iter_markdown_files(target_skill_root, config, workspace_root)
    records = [compute_file_record(target_skill_root, path) for path in markdown_files]
    totals = build_totals(records, phase=args.phase)

    output_key = "size_before_json" if args.phase == "before" else "size_after_json"
    write_json(paths[output_key], totals)

    before_path = paths["size_before_json"]
    after_path = paths["size_after_json"]
    if before_path.exists() and after_path.exists():
        import json

        before = json.loads(before_path.read_text(encoding="utf-8"))
        after = json.loads(after_path.read_text(encoding="utf-8"))
        write_text(paths["size_delta_markdown"], format_delta(before, after))

    print(f"workspace_root={workspace_root}")
    print(f"run_id={workspace_root.name}")
    print(f"{args.phase}_stats={paths[output_key]}")
    if paths["size_delta_markdown"].exists():
        print(f"delta_report={paths['size_delta_markdown']}")


if __name__ == "__main__":
    main()
