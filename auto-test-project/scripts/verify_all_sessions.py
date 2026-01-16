#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _strip_inline_comment(value: str) -> str:
    if "#" not in value:
        return value
    return value.split("#", 1)[0].rstrip()


def _parse_simple_yaml_sections(text: str, *, wanted_sections: set[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        if not line.startswith(" ") and line.endswith(":"):
            section = line[:-1].strip()
            current = section if section in wanted_sections else None
            continue

        if current is None:
            continue

        if line.startswith("  ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = _strip_inline_comment(value.strip())
            if not value:
                continue
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            result.setdefault(current, {})[key] = value

    return result


def _safe_rel_path(value: str, *, default: str) -> str:
    if not value:
        return default
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        return default
    return value


def _load_directories_from_skill_config() -> dict[str, str]:
    skill_root = Path(__file__).resolve().parent.parent
    config_path = skill_root / "config.yaml"
    if not config_path.exists():
        return {}

    text = config_path.read_text(encoding="utf-8", errors="replace")
    try:
        import yaml  # type: ignore
    except Exception:
        data = _parse_simple_yaml_sections(text, wanted_sections={"directories"})
        return data.get("directories") or {}

    try:
        obj = yaml.safe_load(text) or {}
    except Exception:
        data = _parse_simple_yaml_sections(text, wanted_sections={"directories"})
        return data.get("directories") or {}

    v = obj.get("directories")
    if isinstance(v, dict):
        return {str(k): str(vv) for k, vv in v.items() if isinstance(vv, (str, int, float))}
    return {}


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
    parser = argparse.ArgumentParser(
        description="Verify all test sessions under <project_root>/<tests_dir> (tests_dir defaults to config.yaml:directories.tests)."
    )
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
    dirs = _load_directories_from_skill_config()
    tests_dir = project_root / _safe_rel_path(dirs.get("tests", ""), default="tests")
    plans_dir = project_root / _safe_rel_path(dirs.get("plans", ""), default="plans")
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
