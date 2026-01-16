#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "config.yaml",
    "CHANGELOG.md",
    "scripts/create_test_session.py",
    "scripts/verify_test_session.py",
    "templates/OPTIMIZATION_PLAN_TEMPLATE.md",
    "templates/B_ROUND_CHECK_TEMPLATE.md",
    "templates/TEST_PLAN_TEMPLATE.md",
    "templates/TEST_REPORT_TEMPLATE.md",
    "references/A_ROUND_PLAN_TEMPLATE.md",
    "references/FAQ.md",
    "references/PROJECT_TESTING_BEST_PRACTICES.md",
    "references/PROJECT_ISSUE_DISCOVERY_TECHNIQUES.md",
    "references/CRITICAL_THINKING_GUIDE.md",
    "references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md",
    "references/ANTI_PATTERNS_LIBRARY.md",
    "references/EXAMPLE_STRICT_MINIMAL.md",
    "references/EXAMPLE_TEST_REPORT.md",
]


def _check_required_files(skill_root: Path) -> list[str]:
    missing: list[str] = []
    for rel in REQUIRED_FILES:
        if not (skill_root / rel).exists():
            missing.append(rel)
    return missing


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _assert_placeholders_replaced(path: Path, *, keys: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    for key in keys:
        token = f"{{{{{key}}}}}"
        if token in text:
            issues.append(f"{path}: placeholder not replaced: {token}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify auto-test-project skill integrity (deterministic checks).")
    parser.add_argument(
        "--skill-root",
        default=".",
        help="Path to auto-test-project skill root (default: current directory).",
    )
    args = parser.parse_args()

    skill_root = Path(args.skill_root).expanduser().resolve()
    if not (skill_root / "SKILL.md").exists():
        print(f"error: --skill-root does not look like a skill dir (missing SKILL.md): {skill_root}", file=sys.stderr)
        return 2

    failures: list[str] = []

    missing = _check_required_files(skill_root)
    if missing:
        failures.append("missing required files:\n  - " + "\n  - ".join(missing))

    # Basic syntax check for deterministic scripts.
    py_compile = _run(
        [sys.executable, "-m", "py_compile", "scripts/create_test_session.py", "scripts/verify_test_session.py"],
        cwd=skill_root,
    )
    if py_compile.returncode != 0:
        failures.append("py_compile failed:\n" + py_compile.stderr.strip())

    # CLI sanity.
    for script in ["scripts/create_test_session.py", "scripts/verify_test_session.py"]:
        proc = _run([sys.executable, script, "--help"], cwd=skill_root)
        if proc.returncode != 0:
            failures.append(f"{script} --help failed:\n{proc.stderr.strip()}")

    # Regression guards: keep "strict mode" entrypoints and key references discoverable.
    strict_templates = [
        skill_root / "templates/TEST_PLAN_TEMPLATE.md",
        skill_root / "templates/TEST_REPORT_TEMPLATE.md",
    ]
    for path in strict_templates:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "--require-plan" not in text:
            failures.append(f"{path}: missing strict mode example (--require-plan)")

    skill_md = (skill_root / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    readme_md = (skill_root / "README.md").read_text(encoding="utf-8", errors="replace")
    for needle in ["references/FAQ.md", "references/EXAMPLE_STRICT_MINIMAL.md", "references/CRITICAL_THINKING_GUIDE.md"]:
        if needle not in skill_md and needle not in readme_md:
            failures.append(f"docs missing reference to {needle} (expected in SKILL.md or README.md)")

    config_text = (skill_root / "config.yaml").read_text(encoding="utf-8", errors="replace")
    for key in ["skill_info:", "test_rounds:", "a_round_check:", "b_round_check:", "verification:"]:
        if key not in config_text:
            failures.append(f"config.yaml missing key block: {key}")

    # Template auto-fill sanity: generate A/B sessions under a temp project root (no repo pollution).
    with tempfile.TemporaryDirectory(prefix="auto-test-project-selfcheck-") as tmp:
        dummy_root = Path(tmp) / "dummy_project"
        dummy_root.mkdir(parents=True, exist_ok=True)
        (dummy_root / "README.md").write_text("# Dummy Project\n", encoding="utf-8")

        a_id = "v200001010000"
        b_id = "v200001010001"

        a_create = _run(
            [sys.executable, str(skill_root / "scripts/create_test_session.py"), "--project-root", str(dummy_root), "--kind", "a", "--id", a_id, "--create-plan", "--overwrite"],
            cwd=skill_root,
        )
        if a_create.returncode != 0:
            failures.append("dummy A session creation failed:\n" + (a_create.stderr or a_create.stdout).strip())
        else:
            failures.extend(
                _assert_placeholders_replaced(
                    dummy_root / "plans" / f"{a_id}.md",
                    keys=["PLAN_ID", "PROJECT_ROOT", "PLAN_TIME", "SESSION_NAME"],
                )
            )
            failures.extend(
                _assert_placeholders_replaced(
                    dummy_root / "tests" / a_id / "TEST_PLAN.md",
                    keys=["TEST_ID", "PROJECT_ROOT", "PROJECT_TYPE", "TEST_TIME", "PLAN_DOC_PATH", "ROUND_KIND", "SESSION_NAME"],
                )
            )
            failures.extend(
                _assert_placeholders_replaced(
                    dummy_root / "tests" / a_id / "TEST_REPORT.md",
                    keys=["ROUND_KIND", "SESSION_NAME", "PROJECT_ROOT", "TEST_TIME", "PLAN_DOC_PATH"],
                )
            )

        b_create = _run(
            [
                sys.executable,
                str(skill_root / "scripts/create_test_session.py"),
                "--project-root",
                str(dummy_root),
                "--kind",
                "b",
                "--id",
                b_id,
                "--a-test-id",
                a_id,
                "--create-plan",
                "--overwrite",
            ],
            cwd=skill_root,
        )
        if b_create.returncode != 0:
            failures.append("dummy B session creation failed:\n" + (b_create.stderr or b_create.stdout).strip())
        else:
            failures.extend(
                _assert_placeholders_replaced(
                    dummy_root / "plans" / f"B轮-{b_id}.md",
                    keys=["SESSION_NAME", "PLAN_TIME", "PROJECT_NAME", "PROJECT_ROOT", "PROJECT_TYPE", "A_TEST_ID"],
                )
            )

    if failures:
        print("❌ verify_skill failed", file=sys.stderr)
        for item in failures:
            print("\n" + item, file=sys.stderr)
        return 1

    print("✅ verify_skill passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
