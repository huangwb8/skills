#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from i18n import get_translator


def load_legacy_skill_names(config_path: Path) -> list[str]:
    """从配置文件读取 legacy skill 名单。"""
    if not config_path.exists():
        return []

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("缺少 PyYAML 依赖，请先运行 `python3 -m pip install pyyaml`") from exc

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise RuntimeError(f"配置文件解析失败: {exc}") from exc

    raw_names = config.get("legacy_skill_names", [])
    if raw_names is None:
        return []
    if not isinstance(raw_names, list):
        raise RuntimeError("配置项 legacy_skill_names 必须是列表")

    legacy_skill_names: list[str] = []
    seen: set[str] = set()
    for item in raw_names:
        name = str(item).strip()
        if not name or name in seen:
            continue
        legacy_skill_names.append(name)
        seen.add(name)
    return legacy_skill_names


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


def remove_legacy_skills(
    *,
    target_root: Path,
    legacy_skill_names: list[str],
    dry_run: bool,
    active_skill_names: set[str] | None = None,
) -> list[str]:
    """删除目标平台目录中已弃用的 skill 目录。"""
    t = get_translator()
    messages: list[str] = []
    active_names = {name for name in (active_skill_names or set()) if name}

    for skill_name in legacy_skill_names:
        if skill_name in active_names:
            continue

        legacy_path = target_root / skill_name
        if not legacy_path.exists() and not legacy_path.is_symlink():
            continue

        if dry_run:
            messages.append(f"{t.get('dry_run_prefix')}remove legacy skill: {legacy_path}")
            continue

        _remove_path(legacy_path)
        messages.append(t.removed_legacy_skill(path=legacy_path))

    return messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="删除 Codex/Claude Code 中已弃用的 legacy skills。")
    parser.add_argument("--config", type=Path, default=Path(__file__).parents[1] / "config.yaml", help="legacy skill 配置文件路径")
    parser.add_argument("--codex", action="store_true", help="仅清理 Codex")
    parser.add_argument("--claude", action="store_true", help="仅清理 Claude Code")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际删除")
    args = parser.parse_args(argv)

    try:
        legacy_skill_names = load_legacy_skill_names(args.config)
    except RuntimeError as exc:
        print(f"错误: {exc}")
        return 1

    if not legacy_skill_names:
        print("未配置 legacy_skill_names，无需清理。")
        return 0

    install_codex = args.codex or (not args.codex and not args.claude)
    install_claude = args.claude or (not args.codex and not args.claude)

    targets: list[tuple[str, Path]] = []
    home = Path.home()
    if install_codex:
        targets.append(("CODEX", home / ".codex" / "skills"))
    if install_claude:
        targets.append(("CLAUDE", home / ".claude" / "skills"))

    removed_any = False
    for label, target_root in targets:
        print(f"\n[{label}] {target_root}")
        messages = remove_legacy_skills(
            target_root=target_root,
            legacy_skill_names=legacy_skill_names,
            dry_run=args.dry_run,
        )
        if not messages:
            print("未发现需要清理的 legacy skills。")
            continue
        removed_any = True
        for message in messages:
            print(message)

    if not removed_any:
        print("\n所有目标平台都没有发现 legacy skills。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
