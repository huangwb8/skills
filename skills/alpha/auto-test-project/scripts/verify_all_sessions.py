#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from workspace_paths import resolve_legacy_workspace, resolve_workspace


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
    skill_source_root: Path,
    project_root: Path,
    task_root: Path | None,
    legacy_root: Path | None,
    session_dir: Path,
    require_plan: bool,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(skill_source_root / "scripts" / "verify_test_session.py"),
        "--project-root",
        str(project_root),
    ]
    if task_root is not None:
        cmd.extend(["--task-root", str(task_root)])
    if legacy_root is not None:
        cmd.extend(["--legacy-root", str(legacy_root)])
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
        description="Verify all sessions under one explicit active task root or legacy read-only root."
    )
    parser.add_argument("--project-root", default=".", help="Project root that owns .bensz-api (default: .).")
    workspace_group = parser.add_mutually_exclusive_group(required=True)
    workspace_group.add_argument(
        "--task-root",
        default="",
        help="Active task root to verify; the command never creates or renames it.",
    )
    workspace_group.add_argument(
        "--legacy-root",
        default="",
        help="Explicit read-only .bensz-api/skills/auto-test-project compatibility root.",
    )
    parser.add_argument(
        "--require-plan",
        action="store_true",
        help="Run verify in strict mode (requires configured plans dir/<session_name>.md with P0-1 ids).",
    )
    parser.add_argument(
        "--skip-missing-plan",
        action="store_true",
        help="When --require-plan is enabled, skip sessions that lack the matching plan file instead of failing.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    dirs = _load_directories_from_skill_config()
    try:
        if args.task_root:
            workspace = resolve_workspace(
                project_root=project_root,
                task_root_arg=args.task_root,
                task_description="",
                directories=dirs,
                create=False,
            )
        else:
            workspace = resolve_legacy_workspace(
                project_root=project_root,
                legacy_root_arg=args.legacy_root,
                directories=dirs,
            )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    tests_dir = workspace.tests_dir
    plans_dir = workspace.plans_dir

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
            skill_source_root=Path(__file__).resolve().parent.parent,
            project_root=project_root,
            task_root=None if workspace.legacy else workspace.task_root,
            legacy_root=workspace.skill_root if workspace.legacy else None,
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
        print(f"note: skipped {skipped} sessions missing configured plans dir", file=sys.stderr)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
