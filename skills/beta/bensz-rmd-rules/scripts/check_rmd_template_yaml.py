#!/usr/bin/env python3
"""
Validate that templates/Rmd_template.Rmd YAML header matches config.yaml:rmd_template.yaml_header.

Why:
- config.yaml is the single source of truth for the YAML header structure.
- The template keeps a convenience copy for "copy-and-start", which can drift over time.

This script is for maintainers (CI/local checks), not for end-users.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    print(f"[FAIL] PyYAML is required for this check. Error: {e}", file=sys.stderr)
    raise SystemExit(2)


def _skill_root() -> Path:
    # scripts/check_rmd_template_yaml.py -> {skill_root}/scripts/...
    return Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _extract_frontmatter(text: str) -> str | None:
    # Extract the first YAML frontmatter block between --- and ---.
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]) + "\n"
    return None


def main() -> int:
    root = _skill_root()
    config_path = root / "config.yaml"
    tmpl_path = root / "templates" / "Rmd_template.Rmd"

    if not config_path.exists():
        print(f"[FAIL] missing: {config_path}", file=sys.stderr)
        return 2
    if not tmpl_path.exists():
        print(f"[FAIL] missing: {tmpl_path}", file=sys.stderr)
        return 2

    cfg = _load_yaml(config_path) or {}
    if not isinstance(cfg, dict):
        print("[FAIL] config.yaml is not a mapping.", file=sys.stderr)
        return 2

    sec = cfg.get("rmd_template")
    if not isinstance(sec, dict):
        print("[FAIL] missing config.yaml:rmd_template section.", file=sys.stderr)
        return 2
    cfg_header = sec.get("yaml_header")
    if not isinstance(cfg_header, dict):
        print("[FAIL] missing config.yaml:rmd_template.yaml_header mapping.", file=sys.stderr)
        return 2

    fm = _extract_frontmatter(tmpl_path.read_text(encoding="utf-8", errors="replace"))
    if fm is None:
        print("[FAIL] templates/Rmd_template.Rmd does not start with YAML frontmatter.", file=sys.stderr)
        return 1

    try:
        tmpl_header = yaml.safe_load(fm) or {}
    except Exception as e:
        print(f"[FAIL] failed to parse template frontmatter as YAML: {e}", file=sys.stderr)
        return 1

    if tmpl_header != cfg_header:
        # Human-friendly diff-ish output (YAML dumps).
        dumped_cfg = yaml.safe_dump(cfg_header, sort_keys=True, allow_unicode=False)
        dumped_tmpl = yaml.safe_dump(tmpl_header, sort_keys=True, allow_unicode=False)
        print("[FAIL] YAML header mismatch between config.yaml and templates/Rmd_template.Rmd.", file=sys.stderr)
        print("--- config.yaml:rmd_template.yaml_header", file=sys.stderr)
        print(dumped_cfg, file=sys.stderr)
        print("--- templates/Rmd_template.Rmd frontmatter", file=sys.stderr)
        print(dumped_tmpl, file=sys.stderr)
        return 1

    print("[PASS] YAML header matches config.yaml:rmd_template.yaml_header")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
