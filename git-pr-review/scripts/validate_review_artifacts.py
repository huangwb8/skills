#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from common_config import get_skill_root, load_config


SCRIPT_PATH = Path(__file__)
SKILL_ROOT = get_skill_root(SCRIPT_PATH)
CONFIG = load_config(SKILL_ROOT)
OUTPUT = CONFIG["output"]

REQUIRED_PATH_KEYS = [
    "workspace_root",
    "run_dir",
    "raw_dir",
    "notes_dir",
    "evidence_dir",
    "logs_dir",
    "report_dir",
    "report_path",
]
REQUIRED_FILE_KEYS = [
    "manifest_path",
    "raw_readme",
    "user_context_note",
    "community_note",
    "license_review_note",
    "key_findings_note",
    "missing_items_note",
]


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def build_report_regex() -> re.Pattern[str]:
    prefix = re.escape(str(OUTPUT["report_prefix"]))
    ext = re.escape(str(OUTPUT["report_extension"]))
    timestamp_digits = len(datetime.now().strftime(str(OUTPUT["timestamp_format"])))
    return re.compile(rf"^{prefix}_[A-Za-z0-9._-]+_pr-\d+_\d{{{timestamp_digits}}}{ext}$")


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    return payload


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"manifest missing object: {key}")
    return value


def _resolve_manifest_paths(paths: dict[str, Any]) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for key in REQUIRED_PATH_KEYS:
        value = paths.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"manifest missing paths.{key}")
        resolved[key] = Path(value).expanduser().resolve()
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate git-pr-review workspace and report artifacts.")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--report", required=True, help="Path to final Markdown report")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not manifest_path.exists():
        return fail(f"manifest not found: {manifest_path}")
    if not report_path.exists():
        return fail(f"report not found: {report_path}")

    try:
        manifest = _load_manifest(manifest_path)
        paths = _require_mapping(manifest, "paths")
        files = _require_mapping(manifest, "files")
        policy = manifest.get("policy", {})
        if not isinstance(policy, dict):
            return fail("manifest.policy must be a JSON object")
        resolved = _resolve_manifest_paths(paths)
    except ValueError as exc:
        return fail(str(exc))
    for key in REQUIRED_FILE_KEYS:
        if key not in files:
            return fail(f"manifest missing files.{key}")

    run_dir = resolved["run_dir"]
    workspace_root = resolved["workspace_root"]
    for key in ("raw_dir", "notes_dir", "evidence_dir", "logs_dir"):
        path = resolved[key]
        if not path.exists() or not path.is_dir():
            return fail(f"required directory missing: {path}")
        try:
            path.relative_to(run_dir)
        except ValueError:
            return fail(f"{key} must be inside run_dir: {path}")

    try:
        run_dir.relative_to(workspace_root)
    except ValueError:
        return fail("run_dir must be inside workspace_root")

    if OUTPUT.get("enforce_hidden_workspace_when_default") and policy.get("default_hidden_workspace"):
        if not workspace_root.name.startswith("."):
            return fail("default workspace must be a hidden directory")

    for key in REQUIRED_FILE_KEYS:
        value = files[key]
        path = Path(value).expanduser().resolve()
        if not path.exists() or not path.is_file():
            return fail(f"required scaffold file missing: {key} -> {path}")
        try:
            path.relative_to(run_dir)
        except ValueError:
            return fail(f"scaffold file must stay inside run_dir: {key} -> {path}")

    if report_path != resolved["report_path"]:
        return fail("report path does not match manifest suggestion")
    if not build_report_regex().fullmatch(report_path.name):
        return fail(f"report filename is invalid: {report_path.name}")
    if report_path.suffix.lower() != str(OUTPUT["report_extension"]):
        return fail(f"report must use {OUTPUT['report_extension']} extension")

    required_sections = policy.get("required_report_sections") or OUTPUT.get("required_sections") or []
    report_text = report_path.read_text(encoding="utf-8")
    for section in required_sections:
        if section not in report_text:
            return fail(f"report missing required section: {section}")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
