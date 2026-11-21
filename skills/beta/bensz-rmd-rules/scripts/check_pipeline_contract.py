#!/usr/bin/env python3
"""Read-only checks for the targets-first R analysis pipeline contract."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Iterator

from check_targets_renv import (
    TAR_SOURCE,
    WORKFLOW_MODES,
    has_r_call,
    project_path,
    resolve_workflow_mode,
    without_r_comments,
)


REPORT_EXCLUDED = {"templates", "tmp", "raw", "products", "renv", "_targets", "scripts"}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
R_CHUNK = re.compile(r"^\s*\{r(?:[\s,}]|$)")
INLINE_R = re.compile(r"(?<!`)`r\s+([^`]+)`(?!`)")
TARGET_READ = re.compile(r"\b(?:tar_read|tar_load)(?:_raw)?\s*\(")
RAW_READ = re.compile(
    r'''\b(?:read\.(?:csv2?|delim2?|table)|readRDS|read_(?:csv|tsv|delim|rds)|fread)\s*\(\s*'''
    r'''(?:file\s*=\s*)?(?:["'](?:\./)?raw[/\\]|file\.path\s*\(\s*["']raw["']\s*,)'''
)


def report_paths(root: Path) -> Iterator[Path]:
    def local_directory(path: Path) -> bool:
        # Resolve junctions as well as conventional symlinks before descending.
        try:
            return not path.is_symlink() and path.resolve() == path
        except (OSError, RuntimeError):
            return False

    for directory, dirs, files in os.walk(root):
        base = Path(directory)
        dirs[:] = [
            name for name in dirs
            if not name.startswith(".")
            and (base != root or name.lower() not in REPORT_EXCLUDED)
            and local_directory(base / name)
        ]
        for name in files:
            path = base / name
            if path.suffix.lower() == ".rmd" and not path.is_symlink() and path.is_file():
                yield path


def report_r_code(text: str) -> str:
    code: list[str] = []
    opener = ""
    in_r = False
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() in {"---", "..."}), None)
        if end is not None:
            lines = lines[end + 1:]
    for line in lines:
        fence = FENCE.match(line)
        if opener:
            if fence and fence[1][0] == opener[0] and len(fence[1]) >= len(opener) and not fence[2].strip():
                opener, in_r = "", False
            elif in_r:
                code.append(line)
        elif fence:
            opener, in_r = fence[1], bool(R_CHUNK.match(fence[2]))
        else:
            code.extend(INLINE_R.findall(line))
    return without_r_comments("\n".join(code))


def finding(code: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--workflow-mode",
        choices=WORKFLOW_MODES,
        default="auto",
    )
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": "project root is not a directory"}, ensure_ascii=False))
        return 2

    mode = resolve_workflow_mode(root, args.workflow_mode)
    targets_entry, target_error = project_path(root, "_targets.R", "targets entry")
    if mode == "simple":
        if target_error or (root / "_targets.R").exists() or (root / "_targets.R").is_symlink():
            result = {"status": "fail", "workflow_mode": mode, "findings": [
                finding("simple-has-targets-entry", "simple mode requires no _targets.R entry")
            ]}
        else:
            result = {"status": "pass", "workflow_mode": mode, "findings": [], "skipped": "no targets pipeline (simple mode)"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(result["status"] != "pass")

    findings: list[dict[str, str]] = []
    has_targets = targets_entry is not None and targets_entry.is_file()
    if not has_targets:
        findings.append(finding("missing-targets-entry", "complex/pipeline requires _targets.R"))
    r_dir, _ = project_path(root, "R", "R directory")
    has_r = r_dir is not None and r_dir.is_dir()
    if not has_r:
        findings.append(finding("missing-r-directory", "targets-first pipeline requires project R/ for target functions"))

    if has_targets and not has_r_call(TAR_SOURCE, without_r_comments(targets_entry.read_text(encoding="utf-8", errors="replace"))):
        findings.append(finding("r-source-not-declared", "_targets.R must discover R/ through tar_source(\"R\")"))

    rmd_files = sorted(report_paths(root))
    for rmd in rmd_files:
        code = report_r_code(rmd.read_text(encoding="utf-8-sig", errors="replace"))
        if not has_r_call(TARGET_READ, code):
            findings.append(finding("rmd-bypasses-targets", f"{rmd.relative_to(root)} must consume target results with tar_read/tar_load"))
        if has_r_call(RAW_READ, code):
            findings.append(finding("rmd-reads-raw-directly", f"{rmd.relative_to(root)} reads raw/ directly instead of consuming targets"))

    errors = [item for item in findings if item["severity"] == "error"]
    result = {
        "status": "pass" if not errors else "fail",
        "workflow_mode": mode,
        "targets_entry": "_targets.R" if has_targets else None,
        "r_directory": "R" if has_r else None,
        "reports_checked": [str(path.relative_to(root)) for path in rmd_files],
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
