#!/usr/bin/env python3
"""Inspect project state and validate simple/complex R workflow prerequisites."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_TEST_ENTRY = "scripts/tests/smoke_test.R"
DEFAULT_TEST_STORE = "tmp/tests/<run-id>/_targets"


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


def observed_mechanisms(root: Path) -> dict[str, object]:
    root_scripts = sorted(path.name for path in root.glob("*.R"))
    return {
        "renv": (root / "renv.lock").is_file() or (root / "renv" / "activate.R").is_file(),
        "targets": (root / "_targets.R").is_file(),
        "legacy_runner": (root / "analysis-plan.yaml").is_file()
        or any("runner" in name.lower() for name in root_scripts),
        "product_roots": [name for name in ("products", "tmp", "reports") if (root / name).is_dir()],
    }


def project_path(root: Path, value: str, label: str) -> tuple[Path | None, str | None]:
    candidate = Path(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        return None, f"{label} must be a normalized relative path inside the project"
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, f"{label} must stay inside the project"
    return resolved, None


def validate_test_contract(
    root: Path,
    workflow_mode: str,
    test_entry: str,
    test_store: str,
) -> tuple[list[str], list[dict[str, str]]]:
    missing: list[str] = []
    issues: list[dict[str, str]] = []
    entry_path, entry_error = project_path(root, test_entry, "test entry")
    store_path, store_error = project_path(root, test_store, "test store")
    if entry_error:
        issues.append({"code": "unsafe-test-entry", "message": entry_error})
    elif entry_path is not None and not entry_path.is_file():
        missing.append(test_entry)
    if store_error:
        issues.append({"code": "unsafe-test-store", "message": store_error})
    elif store_path is not None:
        forbidden = [root / name for name in ("_targets", "raw", "products", "reports")]
        if any(store_path == path.resolve() or path.resolve() in store_path.parents for path in forbidden):
            issues.append(
                {
                    "code": "unsafe-test-store",
                    "message": "test store must stay under an isolated tmp/ test directory",
                }
            )
        expected_parent = (root / "tmp" / "tests").resolve()
        if store_path != expected_parent and expected_parent not in store_path.parents:
            issues.append(
                {
                    "code": "test-store-not-isolated",
                    "message": "test store must be tmp/tests or one of its descendants",
                }
            )

    if entry_path is None or not entry_path.is_file():
        return missing, issues
    text = entry_path.read_text(encoding="utf-8", errors="replace")
    has_tar_make = bool(re.search(r"\btar_make\s*\(", text))
    delegates_run_root = "test_harness.R" in text
    if "BENSZ_TEST_RUN_ID" not in text and "run_id" not in text and not delegates_run_root:
        issues.append(
            {
                "code": "test-run-root-not-unique",
                "message": "smoke tests must create a unique tmp/tests/<run-id>/ run root",
            }
        )
    if workflow_mode == "simple" and has_tar_make:
        issues.append(
            {
                "code": "simple-test-uses-targets",
                "message": "simple smoke tests must execute the R/Rmd entry directly, without targets",
            }
        )
    if workflow_mode == "complex":
        if not has_tar_make:
            issues.append(
                {
                    "code": "complex-test-missing-tar-make",
                    "message": "complex smoke tests must execute the real target graph with tar_make()",
                }
            )
        harness_bound = "test_harness.R" in text and "targets_store" in text
        literal_bound = "store" in text and all(part in text for part in ("tmp", "tests", "_targets"))
        if not (harness_bound or literal_bound):
            issues.append(
                {
                    "code": "complex-test-store-unbound",
                    "message": "complex smoke tests must bind tar_make() to an isolated tmp/tests/<run-id>/_targets store",
                }
            )
        if re.search(r"store\s*=\s*['\"]_targets/?['\"]", text):
            issues.append(
                {
                    "code": "complex-test-uses-formal-store",
                    "message": "complex smoke tests cannot use the formal _targets/ store",
                }
            )
    return missing, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--mode",
        choices=("auto", "new", "existing"),
        default=None,
        help="Deprecated compatibility alias for --project-state.",
    )
    parser.add_argument("--project-state", choices=("auto", "new", "existing"), default=None)
    parser.add_argument(
        "--workflow-mode",
        choices=("auto", "simple", "complex", "preserved-existing"),
        default="auto",
    )
    parser.add_argument("--test-entry", default=DEFAULT_TEST_ENTRY)
    parser.add_argument("--test-store", default=DEFAULT_TEST_STORE)
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": "project root is not a directory"}, ensure_ascii=False))
        return 2

    project_state = args.project_state or args.mode or "auto"
    if args.project_state and args.mode and args.project_state != args.mode:
        print(
            json.dumps(
                {"status": "error", "message": "--mode and --project-state disagree"},
                ensure_ascii=False,
            )
        )
        return 2

    signals = existing_signals(root)
    if project_state == "auto":
        project_state = "existing" if signals else "new"

    workflow_mode = args.workflow_mode
    if workflow_mode == "auto":
        if project_state == "existing":
            workflow_mode = "preserved-existing"
        else:
            workflow_mode = "complex" if (root / "_targets.R").is_file() else "simple"

    missing: list[str] = []
    issues: list[dict[str, str]] = []
    warnings: list[str] = []
    if project_state == "new":
        if workflow_mode == "preserved-existing":
            issues.append(
                {
                    "code": "invalid-new-workflow-mode",
                    "message": "preserved-existing is only valid for existing projects",
                }
            )
        for rel in ("renv.lock", "renv/activate.R"):
            if not (root / rel).is_file():
                missing.append(rel)
        test_missing, test_issues = validate_test_contract(
            root,
            workflow_mode,
            args.test_entry,
            args.test_store,
        )
        missing.extend(test_missing)
        issues.extend(test_issues)
        if workflow_mode == "complex" and not (root / "_targets.R").is_file():
            missing.append("_targets.R")
        if workflow_mode == "simple" and (root / "_targets.R").exists():
            issues.append(
                {
                    "code": "simple-has-targets-entry",
                    "message": "simple mode must not create _targets.R; choose complex or remove the unintended entry",
                }
            )
    else:
        if workflow_mode != "preserved-existing":
            issues.append(
                {
                    "code": "existing-workflow-mode-not-preserved",
                    "message": "existing projects must use workflow_mode=preserved-existing",
                }
            )
            workflow_mode = "preserved-existing"
        if not (root / "renv.lock").is_file():
            warnings.append("existing project has no renv.lock; preserved without implicit initialization")
        if not (root / "_targets.R").is_file():
            warnings.append("existing project has no _targets.R; preserved without implicit migration")

    missing = sorted(set(missing))
    status = "pass" if not missing and not issues else "fail"
    result = {
        "status": status,
        "project_state": project_state,
        "workflow_mode": workflow_mode,
        "mode": project_state,
        "signals": signals,
        "missing": missing,
        "issues": issues,
        "warnings": warnings,
        "observed_mechanisms": observed_mechanisms(root) if project_state == "existing" else None,
        "test_entry": args.test_entry,
        "test_store": args.test_store if workflow_mode == "complex" else None,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
