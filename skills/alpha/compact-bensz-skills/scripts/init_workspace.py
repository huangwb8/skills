#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import (
    build_totals,
    compute_file_record,
    ensure_workspace,
    iter_markdown_files,
    load_config,
    path_within,
    resolve_skill_root,
    resolve_workspace_root,
    snapshot_files,
    write_latest_run_id,
    write_json,
    write_text,
)


def build_plan(records: list[dict[str, object]]) -> str:
    top_records = sorted(records, key=lambda item: item["words"], reverse=True)[:5]
    lines = [
        "# 压缩计划",
        "",
        "## 当前判断",
        "",
        "- 先阅读 `SKILL.md`、`config.yaml` 与关键脚本，再决定哪些文档可以缩短。",
        "- `tests/`、`plans/`、`README.md`、`CHANGELOG.md` 已被排除，不作为默认待压缩源文件。",
        "- 优先压缩字数最高、重复解释最多的 Markdown 文件。",
        "",
        "## 优先处理文件",
        "",
    ]
    if not top_records:
        lines.append("- 暂无待处理 Markdown 文件")
    else:
        for record in top_records:
            lines.append(f"- `{record['path']}`：约 {record['words']} 词，{record['chars']} 字符")
    lines.extend(
        [
            "",
            "## 必保留信息",
            "",
            "- frontmatter 中的 `name`、`description`、`metadata.author`",
            "- 关键命令、关键路径、默认输出",
            "- 安全限制与不适用范围",
            "",
            "## 完成后必做",
            "",
            "- 重新运行 `measure_markdown.py --phase after`",
            "- 运行 `validate_compaction.py`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化 compact-bensz-skills 隐藏工作区")
    parser.add_argument("--skill-root", required=True, help="目标 skill 根目录")
    parser.add_argument("--workspace-dir", help="自定义隐藏工作区")
    parser.add_argument("--run-id", help="显式指定 run 目录名，例如 run-20260328194500")
    args = parser.parse_args()

    config = load_config()
    target_skill_root = resolve_skill_root(args.skill_root)
    workspace_root = resolve_workspace_root(
        target_skill_root,
        config,
        args.workspace_dir,
        run_id=args.run_id,
        create=True,
    )
    paths = ensure_workspace(config, workspace_root)
    write_latest_run_id(paths["workspace_base"], config, workspace_root.name)

    markdown_files = iter_markdown_files(target_skill_root, config, workspace_root)
    snapshot_files(target_skill_root, markdown_files, paths["before_snapshot_dir"])
    records = [compute_file_record(target_skill_root, path) for path in markdown_files]
    inventory = {
        "skill_root": str(target_skill_root),
        "workspace_base": str(paths["workspace_base"]),
        "workspace_root": str(workspace_root),
        "run_id": workspace_root.name,
        "workspace_inside_skill_root": path_within(target_skill_root, workspace_root),
        "file_count": len(records),
        "files": records,
    }
    totals = build_totals(records, phase="before")

    write_json(paths["inventory_json"], inventory)
    write_json(paths["size_before_json"], totals)
    write_text(paths["plan_markdown"], build_plan(records))

    print(f"workspace_base={paths['workspace_base']}")
    print(f"workspace_root={workspace_root}")
    print(f"run_id={workspace_root.name}")
    print(f"inventory={paths['inventory_json']}")
    print(f"snapshot_dir={paths['before_snapshot_dir']}")
    print(f"size_before={paths['size_before_json']}")
    if not inventory["workspace_inside_skill_root"]:
        print("warning=workspace_dir 位于目标 skill 根目录之外；这只应在用户明确指定时使用")


if __name__ == "__main__":
    main()
