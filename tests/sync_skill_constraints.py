#!/usr/bin/env python3
"""Synchronize the canonical public constraint block into every Skill."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


BEGIN = "<!-- BEGIN COMMON CONSTRAINTS -->"
END = "<!-- END COMMON CONSTRAINTS -->"
SECTION_RE = re.compile(r"(?ms)^## 约束\s*$.*?(?=^##\s+|\Z)")
LEGACY_PUBLIC_RE = re.compile(
    r"(?ms)^## (?:BenszAPI 任务工作区|与 bensz-collect-bugs 的协作约定)\s*$.*?(?=^##\s+|\Z)"
)


def _template(project_root: Path) -> str:
    path = project_root / "docs/templates/skill-common-constraints.md"
    text = path.read_text(encoding="utf-8").strip()
    return text + "\n"


def _canonical(template: str) -> str:
    digest = hashlib.sha256(template.encode("utf-8")).hexdigest()
    return f"{BEGIN}\n<!-- Source-Hash: sha256:{digest} -->\n{template}{END}\n"


def _preserve_specific(old: str) -> str:
    lines = old.splitlines()
    kept: list[str] = []
    skip_bug = False
    skip_common = False
    for line in lines:
        if line.strip() == "### Skill 专属约束":
            continue
        if line.strip() == BEGIN:
            skip_common = True
            continue
        if skip_common:
            if line.strip() == END:
                skip_common = False
            continue
        if line.startswith("#### "):
            skip_bug = "bensz-collect-bugs" in line
            if not skip_bug:
                kept.append(line)
            continue
        if skip_bug:
            continue
        if any(token in line for token in (
            "本 Skill 的新任务中间文件统一写入",
            "遵守 `.bensz-api` 任务工作区协议",
            "不记录 API Key",
            "不记录密钥、令牌",
            "文件操作限于授权范围",
            "只有用户明确要求",
            "因本 skill 设计缺陷",
            "如果用户环境里出现因本 skill 设计缺陷",
        )):
            continue
        kept.append(line)
    while kept and not kept[0].strip():
        kept.pop(0)
    while kept and not kept[-1].strip():
        kept.pop()
    if not kept:
        return ""
    return "\n### Skill 专属约束\n\n" + "\n".join(kept).strip() + "\n"


def sync_skill(path: Path, template: str, *, write: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    text = LEGACY_PUBLIC_RE.sub("", text)
    match = SECTION_RE.search(text)
    if not match:
        replacement = "\n\n## 约束\n\n" + _canonical(template)
        if write:
            path.write_text(text.rstrip() + replacement + "\n", encoding="utf-8")
        return True
    old = match.group(0)
    specific = _preserve_specific(old[len("## 约束"):])
    replacement = "## 约束\n\n" + _canonical(template) + specific + "\n"
    candidate = text[: match.start()] + replacement.rstrip() + "\n" + text[match.end():].lstrip("\n")
    changed = candidate != path.read_text(encoding="utf-8")
    if changed and write:
        path.write_text(candidate, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    template = _template(root)
    paths = sorted(
        path
        for source in ("alpha", "beta")
        for path in (root / "skills" / source).rglob("SKILL.md")
    )
    changed = [path for path in paths if sync_skill(path, template, write=args.write)]
    for path in changed:
        print(path.relative_to(root))
    print(f"skills={len(paths)} changed={len(changed)} mode={'write' if args.write else 'check'}")
    return 1 if changed and not args.write else 0


if __name__ == "__main__":
    raise SystemExit(main())
