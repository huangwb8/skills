#!/usr/bin/env python3
"""Inspect project state and validate simple/complex R workflow prerequisites."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PureWindowsPath


DEFAULT_TEST_ENTRY = "scripts/tests/smoke_test.R"
DEFAULT_TEST_STORE = "tmp/tests/<run-id>/_targets"
WORKFLOW_MODES = ("auto", "simple", "complex", "pipeline")
TAR_MAKE = re.compile(r"\btar_make\s*\(")
TAR_SOURCE = re.compile(r"\btar_source\s*\(\s*([\"'])R\1\s*[,)]")
R_COMMENT_OR_QUOTE = re.compile(r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|#[^\r\n]*''')


def without_r_comments(text: str) -> str:
    return R_COMMENT_OR_QUOTE.sub(lambda match: "" if match[0].startswith("#") else match[0], text)


def has_r_call(pattern: re.Pattern[str], code: str) -> bool:
    """Ignore matches that start inside an R string (arguments may contain strings)."""
    unquoted = R_COMMENT_OR_QUOTE.sub(lambda match: " " * len(match[0]), code)
    return any(unquoted[match.start()] != " " for match in pattern.finditer(code))


def resolve_workflow_mode(root: Path, requested: str) -> str:
    if requested == "auto":
        return "complex" if (root / "_targets.R").is_file() else "simple"
    return "complex" if requested == "pipeline" else requested


def existing_signals(root: Path) -> list[str]:
    signals = []
    for rel in ("_targets.R", "renv.lock", "renv/activate.R", "analysis-plan.yaml"):
        if (root / rel).exists():
            signals.append(rel)
    for directory in ("raw", "products", "reports", "renv", "R"):
        if (root / directory).is_dir():
            signals.append(directory + "/")
    if any(path.is_file() and path.suffix.lower() in {".r", ".rmd"} for path in root.iterdir()):
        signals.append("root-R-files")
    return sorted(set(signals))


def observed_mechanisms(root: Path) -> dict[str, object]:
    return {
        "renv": (root / "renv.lock").is_file() or (root / "renv" / "activate.R").is_file(),
        "targets": (root / "_targets.R").is_file(),
        "product_roots": [name for name in ("products", "tmp", "reports") if (root / name).is_dir()],
    }


def project_path(root: Path, value: str, label: str) -> tuple[Path | None, str | None]:
    parts = value.replace("\\", "/").split("/")
    if PureWindowsPath(value).drive or any(part in {"", ".", ".."} for part in parts):
        return None, f"{label} must be a normalized relative path inside the project"
    try:
        resolved = root.joinpath(*parts).resolve()
        resolved.relative_to(root)
    except (ValueError, OSError, RuntimeError):
        return None, f"{label} must stay inside the project"
    return resolved, None


def test_store_issue(root: Path, value: str) -> dict[str, str] | None:
    parts = value.replace("\\", "/").split("/")
    # The symbolic default describes the layout; never resolve an on-disk '<run-id>'.
    if len(parts) != 4 or parts[:2] != ["tmp", "tests"] or parts[-1] != "_targets" or not (
        parts[2] == "<run-id>" or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", parts[2])
    ):
        return {"code": "test-store-not-isolated", "message": "test store must be tmp/tests/<run-id>/_targets"}
    if parts[2] == "<run-id>":
        parts = parts[:2]
    path = root.joinpath(*parts)
    resolved, error = project_path(root, "/".join(parts), "test store")
    if error or resolved != path or any(p.is_symlink() or (p.exists() and not p.is_dir()) for p in (
        root.joinpath(*parts[:i]) for i in range(1, len(parts) + 1)
    )):
        return {"code": "unsafe-test-store", "message": "test store must use real directories under tmp/tests"}
    return None


def validate_test_contract(
    root: Path,
    workflow_mode: str,
    test_entry: str,
    test_store: str,
) -> tuple[list[str], list[dict[str, str]]]:
    missing: list[str] = []
    issues: list[dict[str, str]] = []
    entry_path, entry_error = project_path(root, test_entry, "test entry")
    if entry_error:
        issues.append({"code": "unsafe-test-entry", "message": entry_error})
    elif entry_path.is_dir():
        issues.append({"code": "invalid-test-entry-type", "message": "test entry must be a file"})
    elif not entry_path.is_file():
        missing.append(test_entry)
    if workflow_mode == "complex" and (store_issue := test_store_issue(root, test_store)):
        issues.append(store_issue)

    if entry_path is None or not entry_path.is_file():
        return missing, issues
    text = without_r_comments(entry_path.read_text(encoding="utf-8", errors="replace"))
    if not text.strip():
        issues.append({"code": "empty-test-entry", "message": "test entry must contain runnable R code"})
    has_tar_make = has_r_call(TAR_MAKE, text)
    delegates_run_root = has_r_call(re.compile(r"\bbensz_test_begin\s*\("), text)
    delegated_run = has_r_call(re.compile(r"\bbensz_test_run_entry\s*\("), text)
    if delegates_run_root or delegated_run:
        harness, error = project_path(root, str(entry_path.parent.relative_to(root) / "test_harness.R"), "test harness")
        if error or harness is None or not harness.is_file() or not without_r_comments(
            harness.read_text(encoding="utf-8", errors="replace")
        ).strip():
            issues.append({"code": "missing-test-harness", "message": "copy test_harness.R next to the test entry"})
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
        if not (has_tar_make or delegated_run):
            issues.append(
                {
                    "code": "complex-test-missing-tar-make",
                    "message": "complex smoke tests must execute the real target graph with tar_make()",
                }
            )
        # Also accept projects that allocate the run with the harness and call
        # tar_make() directly using its context, rather than the child helper.
        harness_bound = delegates_run_root and (
            delegated_run or has_r_call(re.compile(r"\btar_make\s*\(\s*store\s*=\s*\w+\$targets_store\b"), text)
        )
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
        choices=WORKFLOW_MODES,
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

    workflow_mode = resolve_workflow_mode(root, args.workflow_mode)

    missing: list[str] = []
    issues: list[dict[str, str]] = []
    warnings: list[str] = []

    def require_path(rel: str, display: str, *, directory: bool = False, required: bool = False) -> Path | None:
        path, error = project_path(root, rel, display)
        if error:
            issues.append({"code": "unsafe-project-path", "message": error})
        elif (path.is_dir() if directory else path.is_file()):
            return path
        elif path.exists():
            issues.append({"code": "invalid-project-path-type", "message": f"{display} must be a {'directory' if directory else 'file'}"})
        elif project_state == "new" or required:
            missing.append(display)
        else:
            warnings.append(f"existing project has no {display}; not implicitly created")
        return None

    lockfile = require_path("renv.lock", "renv.lock")
    if lockfile is not None:
        try:
            lock = json.loads(lockfile.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError):
            lock = None
        if not isinstance(lock, dict) or not isinstance(lock.get("R"), dict) or not isinstance(lock.get("Packages"), dict):
            issues.append({"code": "invalid-renv-lockfile", "message": "renv.lock must contain JSON R and Packages objects"})
    activation = require_path("renv/activate.R", "renv/activate.R")
    if activation is not None and not without_r_comments(activation.read_text(encoding="utf-8", errors="replace")).strip():
        issues.append({"code": "empty-renv-activation", "message": "renv/activate.R must contain runnable R code"})

    test_missing, test_issues = validate_test_contract(
        root,
        workflow_mode,
        args.test_entry,
        args.test_store,
    )
    if test_missing:
        if project_state == "new":
            missing.extend(test_missing)
        else:
            warnings.append(f"existing project has no {args.test_entry}; not implicitly created")
    issues.extend(test_issues)

    if workflow_mode == "complex":
        targets_entry = require_path("_targets.R", "_targets.R", required=True)
        require_path("R", "R/", directory=True, required=True)
        if targets_entry is not None:
            targets_text = without_r_comments(targets_entry.read_text(encoding="utf-8", errors="replace"))
            if not has_r_call(TAR_SOURCE, targets_text):
                issues.append(
                    {
                        "code": "targets-not-r-first",
                        "message": "complex pipeline _targets.R must discover computation functions from R/ via tar_source(\"R\")",
                    }
                )
    if workflow_mode == "simple" and ((root / "_targets.R").exists() or (root / "_targets.R").is_symlink()):
        issues.append(
            {
                "code": "simple-has-targets-entry",
                "message": "simple mode must not create _targets.R; choose complex or remove the unintended entry",
            }
        )

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
