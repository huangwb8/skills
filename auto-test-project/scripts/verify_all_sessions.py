#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run_verify(
    *,
    project_root: Path,
    session_dir: Path,
    require_plan: bool,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(project_root / "scripts" / "verify_test_session.py")]
    if require_plan:
        cmd.append("--require-plan")
    cmd.append(str(session_dir))
    return subprocess.run(
        cmd,
        cwd=str(project_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify all test sessions under <project_root>/tests.")
    parser.add_argument("--project-root", default=".", help="Project root containing tests/ and scripts/ (default: .).")
    parser.add_argument(
        "--require-plan",
        action="store_true",
        help="Run verify in strict mode (requires plans/<session_name>.md with P0-1 ids).",
    )
    parser.add_argument(
        "--skip-missing-plan",
        action="store_true",
        help="When --require-plan is enabled, skip sessions that lack the matching plan file instead of failing.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    tests_dir = project_root / "tests"
    plans_dir = project_root / "plans"
    if not tests_dir.exists():
        print(f"error: missing tests dir: {tests_dir}", file=sys.stderr)
        return 2

    sessions = sorted([p for p in tests_dir.iterdir() if p.is_dir()])
    if not sessions:
        print(f"warning: no sessions under {tests_dir}", file=sys.stderr)
        return 0

    failed = 0
    skipped = 0
    for session_dir in sessions:
        plan_path = plans_dir / f"{session_dir.name}.md"
        if args.require_plan and args.skip_missing_plan and not plan_path.exists():
            skipped += 1
            print(f"⏭️  SKIP (missing plan): {session_dir}")
            continue

        proc = _run_verify(
            project_root=project_root,
            session_dir=session_dir,
            require_plan=args.require_plan,
        )
        if proc.returncode == 0:
            print(f"✅ PASS: {session_dir}")
        else:
            failed += 1
            print(f"❌ FAIL: {session_dir}")
            if proc.stdout.strip():
                print(proc.stdout.rstrip())
            if proc.stderr.strip():
                print(proc.stderr.rstrip(), file=sys.stderr)

    if args.require_plan and args.skip_missing_plan and skipped:
        print(f"note: skipped {skipped} sessions missing plans/", file=sys.stderr)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

