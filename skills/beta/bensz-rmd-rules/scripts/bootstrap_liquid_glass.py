#!/usr/bin/env python3
"""
Bootstrap Liquid Glass assets into a new project.

Why:
- The default Rmd template assumes the project root contains:
  - templates/liquid_glass_theme.css
  - templates/liquid_glass_lightbox.html (lightbox + view state persistence)
- Optionally, it also benefits from:
  - 00.Environment.R (project root)
  - templates/datatables_helper.R, templates/nature_theme.R, etc.

This script copies those files from the installed skill directory into the
current working directory (or --project-root).

Design:
- Deterministic, no network.
- Path-aware: locate skill root via __file__ so it works after installation.
- Safe-by-default: never overwrite unless --force.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def _skill_root() -> Path:
    # scripts/bootstrap_liquid_glass.py -> skill_root
    return Path(__file__).resolve().parents[1]


def _copy(src: Path, dst: Path, *, force: bool) -> tuple[bool, str]:
    if not src.exists():
        return False, f"missing source: {src}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        return False, f"skip exists: {dst}"
    shutil.copy2(src, dst)
    return True, f"copied: {dst}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Copy Liquid Glass theme assets into a project root.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Target project root directory (default: current directory).",
    )
    parser.add_argument(
        "--with-env",
        action="store_true",
        help='Also copy "00.Environment.R" into project root (if missing).',
    )
    parser.add_argument(
        "--with-extras",
        action="store_true",
        help="Also copy common helper templates (DT/theme/etc.).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files.",
    )
    args = parser.parse_args(argv)

    skill_root = _skill_root()
    src_templates = skill_root / "templates"
    project_root = Path(args.project_root).expanduser().resolve()

    tasks: list[tuple[Path, Path]] = [
        (src_templates / "liquid_glass_theme.css", project_root / "templates" / "liquid_glass_theme.css"),
        (src_templates / "liquid_glass_lightbox.html", project_root / "templates" / "liquid_glass_lightbox.html"),
    ]

    if args.with_env:
        tasks.append((src_templates / "00.Environment.R", project_root / "00.Environment.R"))

    if args.with_extras:
        for name in [
            "datatables_helper.R",
            "nature_colors.R",
            "nature_theme.R",
            "complexheatmap_template.R",
            "plotly_template.R",
        ]:
            tasks.append((src_templates / name, project_root / "templates" / name))

    ok = 0
    for src, dst in tasks:
        success, msg = _copy(src, dst, force=args.force)
        print(msg)
        ok += int(success)

    print(f"done: {ok}/{len(tasks)} copied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
