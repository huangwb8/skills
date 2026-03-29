#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    build_totals,
    compute_file_record,
    ensure_workspace,
    find_local_link_issues,
    iter_markdown_files,
    load_config,
    nested_get,
    path_within,
    parse_frontmatter,
    read_text,
    resolve_skill_root,
    resolve_workspace_root,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="校验压缩后的 skill Markdown")
    parser.add_argument("--skill-root", required=True, help="目标 skill 根目录")
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

    errors: list[str] = []
    warnings: list[str] = []
    skill_md = target_skill_root / "SKILL.md"
    frontmatter, skill_body = parse_frontmatter(read_text(skill_md))

    for dotted_key in config["preservation"]["required_skill_frontmatter_fields"]:
        if nested_get(frontmatter, dotted_key) in (None, "", []):
            errors.append(f"SKILL.md frontmatter 缺少必需字段: {dotted_key}")

    if nested_get(frontmatter, "name") != target_skill_root.name:
        warnings.append(
            "SKILL.md frontmatter.name 与目录名不一致；若这是历史兼容设计可忽略，否则建议修正"
        )

    keywords = nested_get(frontmatter, "metadata.keywords") or []
    if config["preservation"]["required_skill_keywords_include_name"] and nested_get(
        frontmatter, "name"
    ) not in keywords:
        errors.append("metadata.keywords 未包含 skill 名")

    if not path_within(target_skill_root, workspace_root):
        warnings.append("workspace_dir 位于目标 skill 根目录之外；只有用户明确指定时才应这样做")

    for path in markdown_files:
        issues = find_local_link_issues(path, read_text(path), target_skill_root)
        errors.extend(
            [f"{path.relative_to(target_skill_root)}: {issue}" for issue in issues]
        )

    if not skill_body.strip():
        errors.append("SKILL.md 正文为空")

    before_stats_path = paths["size_before_json"]
    after_stats_path = paths["size_after_json"]
    if before_stats_path.exists():
        before = json.loads(before_stats_path.read_text(encoding="utf-8"))
        if not after_stats_path.exists():
            current_records = [compute_file_record(target_skill_root, path) for path in markdown_files]
            write_json(after_stats_path, build_totals(current_records, phase="after"))
        after = json.loads(after_stats_path.read_text(encoding="utf-8"))
        if after["total_words"] >= before["total_words"]:
            warnings.append(
                "压缩后总词数未下降；如果这是有意保留，请在报告中说明原因"
            )

    snapshot_skill_md = paths["before_snapshot_dir"] / "SKILL.md"
    if snapshot_skill_md.exists():
        snapshot_frontmatter, _ = parse_frontmatter(read_text(snapshot_skill_md))
        if nested_get(snapshot_frontmatter, "name") != nested_get(frontmatter, "name"):
            errors.append("SKILL.md frontmatter.name 与压缩前快照不一致")
        if nested_get(snapshot_frontmatter, "description") != nested_get(frontmatter, "description"):
            warnings.append("SKILL.md frontmatter.description 与压缩前快照不同；请确认只是等价压缩")

    result = {
        "skill_root": str(target_skill_root),
        "workspace_base": str(paths["workspace_base"]),
        "workspace_root": str(workspace_root),
        "run_id": workspace_root.name,
        "workspace_inside_skill_root": path_within(target_skill_root, workspace_root),
        "checked_files": [str(path.relative_to(target_skill_root)) for path in markdown_files],
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
    write_json(paths["validation_json"], result)

    print(f"workspace_root={workspace_root}")
    print(f"run_id={workspace_root.name}")
    print(f"validation={paths['validation_json']}")
    if warnings:
        print(f"warnings={len(warnings)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
