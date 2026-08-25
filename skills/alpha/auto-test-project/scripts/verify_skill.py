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
    "scripts/verify_all_sessions.py",
    "scripts/workspace_paths.py",
    "scripts/test_workspace_paths.py",
    "scripts/test_workspace_cli.py",
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


def _fill_valid_session(*, plan_path: Path, session_dir: Path) -> None:
    issue_ids = [f"P0-{index}" for index in range(1, 11)]
    plan_path.write_text(
        "# Self-check plan\n\n"
        + "\n".join(f"#### {issue_id}: deterministic check" for issue_id in issue_ids)
        + "\n",
        encoding="utf-8",
    )
    evidence = "\n".join(
        f"- {issue_id}: verified by scripts/verify_skill.py:1 with reproducible output."
        for issue_id in issue_ids
    )
    (session_dir / "TEST_PLAN.md").write_text(
        "# TEST_PLAN\n\n" + "\n".join(issue_ids) + "\n",
        encoding="utf-8",
    )
    (session_dir / "TEST_REPORT.md").write_text(
        "# TEST_REPORT\n\n## Evidence\n\n"
        + evidence
        + "\n\n## Verification\n\n"
        + ("The task-local workspace contract was verified. " * 20)
        + "\n",
        encoding="utf-8",
    )


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
        [
            sys.executable,
            "-m",
            "py_compile",
            "scripts/create_test_session.py",
            "scripts/verify_test_session.py",
            "scripts/verify_all_sessions.py",
            "scripts/workspace_paths.py",
            "scripts/test_workspace_paths.py",
            "scripts/test_workspace_cli.py",
        ],
        cwd=skill_root,
    )
    if py_compile.returncode != 0:
        failures.append("py_compile failed:\n" + py_compile.stderr.strip())

    for test_script in [
        "scripts/test_workspace_paths.py",
        "scripts/test_workspace_cli.py",
    ]:
        proc = _run([sys.executable, test_script], cwd=skill_root)
        if proc.returncode != 0:
            failures.append(
                f"{test_script} failed:\n"
                + (proc.stderr or proc.stdout).strip()
            )

    # CLI sanity.
    for script in [
        "scripts/create_test_session.py",
        "scripts/verify_test_session.py",
        "scripts/verify_all_sessions.py",
    ]:
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
        task_root = dummy_root / ".bensz-api" / "task-20000101-0000-selfcheck"

        a_create = _run(
            [
                sys.executable,
                str(skill_root / "scripts/create_test_session.py"),
                "--project-root",
                str(dummy_root),
                "--task-root",
                str(task_root),
                "--kind",
                "a",
                "--id",
                a_id,
                "--create-plan",
                "--overwrite",
            ],
            cwd=skill_root,
        )
        if a_create.returncode != 0:
            failures.append("dummy A session creation failed:\n" + (a_create.stderr or a_create.stdout).strip())
        else:
            a_plan = task_root / "auto-test-project" / "output" / "plans" / f"{a_id}.md"
            a_session = task_root / "auto-test-project" / "output" / "tests" / a_id
            failures.extend(
                _assert_placeholders_replaced(
                    a_plan,
                    keys=["PLAN_ID", "PROJECT_ROOT", "PLAN_TIME", "SESSION_NAME"],
                )
            )
            failures.extend(
                _assert_placeholders_replaced(
                    a_session / "TEST_PLAN.md",
                    keys=["TEST_ID", "PROJECT_ROOT", "PROJECT_TYPE", "TEST_TIME", "PLAN_DOC_PATH", "ROUND_KIND", "SESSION_NAME", "TASK_ROOT", "SKILL_WORKSPACE"],
                )
            )
            failures.extend(
                _assert_placeholders_replaced(
                    a_session / "TEST_REPORT.md",
                    keys=["ROUND_KIND", "SESSION_NAME", "PROJECT_ROOT", "TEST_TIME", "PLAN_DOC_PATH", "TASK_ROOT", "SKILL_WORKSPACE"],
                )
            )

        b_create = _run(
            [
                sys.executable,
                str(skill_root / "scripts/create_test_session.py"),
                "--project-root",
                str(dummy_root),
                "--task-root",
                str(task_root),
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
            b_plan = task_root / "auto-test-project" / "output" / "plans" / f"B轮-{b_id}.md"
            b_session = task_root / "auto-test-project" / "output" / "tests" / f"B轮-{b_id}"
            failures.extend(
                _assert_placeholders_replaced(
                    b_plan,
                    keys=["SESSION_NAME", "PLAN_TIME", "PROJECT_NAME", "PROJECT_ROOT", "PROJECT_TYPE", "A_TEST_ID"],
                )
            )

        if a_create.returncode == 0 and b_create.returncode == 0:
            _fill_valid_session(plan_path=a_plan, session_dir=a_session)
            _fill_valid_session(plan_path=b_plan, session_dir=b_session)
            for session_dir in (a_session, b_session):
                verify = _run(
                    [
                        sys.executable,
                        str(skill_root / "scripts/verify_test_session.py"),
                        "--project-root",
                        str(dummy_root),
                        "--task-root",
                        str(task_root),
                        "--require-plan",
                        str(session_dir),
                    ],
                    cwd=skill_root,
                )
                if verify.returncode != 0:
                    failures.append(
                        "task-local session verification failed:\n"
                        + (verify.stderr or verify.stdout).strip()
                    )

            verify_all = _run(
                [
                    sys.executable,
                    str(skill_root / "scripts/verify_all_sessions.py"),
                    "--project-root",
                    str(dummy_root),
                    "--task-root",
                    str(task_root),
                    "--require-plan",
                ],
                cwd=skill_root,
            )
            if verify_all.returncode != 0:
                failures.append(
                    "task-local batch verification failed:\n"
                    + (verify_all.stderr or verify_all.stdout).strip()
                )

        if (dummy_root / ".bensz-api" / "skills").exists():
            failures.append("default self-check created the disabled .bensz-api/skills directory")

        missing_root = dummy_root / ".bensz-api" / "task-20000101-0000-missing"
        missing_verify = _run(
            [
                sys.executable,
                str(skill_root / "scripts/verify_all_sessions.py"),
                "--project-root",
                str(dummy_root),
                "--task-root",
                str(missing_root),
            ],
            cwd=skill_root,
        )
        if missing_verify.returncode != 2 or "Traceback" in (missing_verify.stderr + missing_verify.stdout):
            failures.append("missing task root did not produce a structured verification error")

    if failures:
        print("❌ verify_skill failed", file=sys.stderr)
        for item in failures:
            print("\n" + item, file=sys.stderr)
        return 1

    print("✅ verify_skill passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
