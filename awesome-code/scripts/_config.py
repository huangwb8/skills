#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict


def load_skill_config(skill_root: Path) -> Dict[str, Any]:
    """
    Load `config.yaml` from a skill root.

    We keep this dependency lightweight:
    - If PyYAML isn't available, we return an empty config and let callers fall back to defaults.
    """
    config_path = skill_root / "config.yaml"
    if not config_path.exists():
        return {}

    try:
        import yaml  # type: ignore
    except Exception as exc:
        print(f"[awesome-code] warning: PyYAML unavailable; ignoring {config_path}: {exc}", file=sys.stderr)
        return {}

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[awesome-code] warning: failed to parse {config_path}: {exc}", file=sys.stderr)
        return {}

    if isinstance(data, dict):
        return data
    return {}


def get_nested(config: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = config
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur
