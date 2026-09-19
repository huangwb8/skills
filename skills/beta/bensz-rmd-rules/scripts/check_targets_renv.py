#!/usr/bin/env python3
"""Check the targets/renv project strategy without creating or migrating files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def existing_signals(root: Path) -> list[str]:
    signals = []
    for rel in ("_targets.R", "renv.lock", "renv/activate.R", "analysis-plan.yaml"):
        if (root / rel).exists():
            signals.append(rel)
    for directory in ("raw", "products", "reports", "renv"):
        if (root / directory).is_dir():
            signals.append(directory + "/")
    if list(root.glob("*.R")) or list(root.glob("*.Rmd")):
        signals.append("root-R-files")
    return sorted(set(signals))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--mode", choices=("auto", "new", "existing"), default="auto")
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": "project root is not a directory"}, ensure_ascii=False))
        return 2

    signals = existing_signals(root)
    mode = args.mode
    if mode == "auto":
        mode = "existing" if signals else "new"
    missing = []
    if mode == "new":
        for rel in ("_targets.R", "renv.lock", "renv/activate.R"):
            if not (root / rel).is_file():
                missing.append(rel)
    result = {"status": "pass" if not missing else "fail", "mode": mode, "signals": signals, "missing": missing}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
