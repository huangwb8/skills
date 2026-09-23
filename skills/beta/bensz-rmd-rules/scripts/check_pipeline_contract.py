#!/usr/bin/env python3
"""Read-only checks for the targets-first R analysis pipeline contract."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def finding(code: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--workflow-mode",
        choices=("auto", "simple", "complex"),
        default="auto",
    )
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": "project root is not a directory"}, ensure_ascii=False))
        return 2

    targets_entry = root / "_targets.R"
    mode = args.workflow_mode
    if mode == "auto":
        mode = "complex" if targets_entry.is_file() else "simple"
    if mode == "simple":
        result = {"status": "pass", "workflow_mode": mode, "findings": [], "skipped": "no targets pipeline (simple mode)"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    findings: list[dict[str, str]] = []
    if not targets_entry.is_file():
        findings.append(finding("missing-targets-entry", "complex/pipeline requires _targets.R"))
    r_dir = root / "R"
    if not r_dir.is_dir():
        findings.append(finding("missing-r-directory", "targets-first pipeline requires project R/ for target functions"))

    targets_text = targets_entry.read_text(encoding="utf-8", errors="replace") if targets_entry.is_file() else ""
    if targets_text and not re.search(r"tar_source\s*\(\s*[\"']R[\"']", targets_text):
        findings.append(finding("r-source-not-declared", "_targets.R should discover R/ through tar_source(\"R\")"))

    rmd_files = sorted(
        path for path in root.rglob("*.Rmd")
        if "templates" not in path.parts and ".bensz-api" not in path.parts
    )
    for rmd in rmd_files:
        text = rmd.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"(?:tar_read|tar_load|tar_render)\s*\(", text):
            findings.append(finding("rmd-bypasses-targets", f"{rmd.relative_to(root)} must consume target results with tar_read/tar_load/tar_render"))
        if re.search(r"(?:read\.(?:csv|delim)|readRDS)\s*\(\s*[\"']raw[/\\]", text):
            findings.append(finding("rmd-reads-raw-directly", f"{rmd.relative_to(root)} reads raw/ directly instead of consuming targets"))

    errors = [item for item in findings if item["severity"] == "error"]
    result = {
        "status": "pass" if not errors else "fail",
        "workflow_mode": mode,
        "targets_entry": str(targets_entry.relative_to(root)) if targets_entry.exists() else None,
        "r_directory": str(r_dir.relative_to(root)) if r_dir.exists() else None,
        "reports_checked": [str(path.relative_to(root)) for path in rmd_files],
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
