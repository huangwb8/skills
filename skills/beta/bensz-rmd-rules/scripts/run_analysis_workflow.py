#!/usr/bin/env python3
"""Run numbered R compute units in analysis-plan order."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover
    print(f"[FAIL] PyYAML is required: {exc}", file=sys.stderr)
    raise SystemExit(2)

import check_analysis_workflow as checker


def load_units(plan_path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("units"), list):
        raise ValueError("analysis plan must contain a units list")
    units = [item for item in data["units"] if isinstance(item, dict)]
    return sorted(units, key=lambda item: checker.unit_key(str(item.get("id", ""))))


def compute_script(unit: dict[str, Any]) -> str | None:
    code = unit.get("code", [])
    if not isinstance(code, list):
        return None
    unit_stem = f"{unit.get('id')}. {unit.get('name')}"
    r_files = [str(item) for item in code if str(item).endswith(".R") and not str(item).endswith("_functions.R")]
    mismatched = [item for item in r_files if Path(item).name != f"{unit_stem}.R"]
    if mismatched:
        raise ValueError(f"unit {unit.get('id')} executable does not match its stem: {mismatched[0]}")
    candidates = r_files
    if len(candidates) > 1:
        raise ValueError(f"unit {unit.get('id')} has multiple executable .R files")
    return candidates[0] if candidates else None


def execution_environment(force_step: str, resume_from: str) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("BENSZ_FORCE_STEP", None)
    env.pop("BENSZ_RESUME_FROM", None)
    if force_step:
        env["BENSZ_FORCE_STEP"] = force_step
    if resume_from:
        env["BENSZ_RESUME_FROM"] = resume_from
    return env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--plan", default="analysis-plan.yaml")
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--force-step", default="")
    parser.add_argument("--resume-from", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.project_root).expanduser().resolve()
    plan_path = (root / args.plan).resolve()
    try:
        plan_path.relative_to(root)
    except ValueError:
        print("[FAIL] --plan must stay inside project root", file=sys.stderr)
        return 2

    validation_args = [
        str(root),
        "--plan",
        relative_plan(plan_path, root),
        "--strict",
        "--allow-stale-checkpoints",
    ]
    if checker.main(validation_args) != 0:
        print("[FAIL] workflow validation failed; no R units were run", file=sys.stderr)
        return 1

    try:
        units = load_units(plan_path)
        scripts = [(str(unit["id"]), compute_script(unit)) for unit in units]
    except (KeyError, TypeError, ValueError) as exc:
        print(f"[FAIL] cannot build execution plan: {exc}", file=sys.stderr)
        return 2

    scripts = [(unit_id, script) for unit_id, script in scripts if script]
    unit_ids = {unit_id for unit_id, _script in scripts}
    for option, value in (("--force-step", args.force_step), ("--resume-from", args.resume_from)):
        if value and value not in unit_ids:
            print(f"[FAIL] {option} does not match a planned .R compute unit: {value}", file=sys.stderr)
            return 2

    for unit_id, script in scripts:
        print(f"[PLAN] {unit_id}: {script}")
    if args.dry_run:
        return 0

    rscript = shutil.which(args.rscript)
    if rscript is None:
        print(f"[FAIL] Rscript executable not found: {args.rscript}", file=sys.stderr)
        return 2

    env = execution_environment(args.force_step, args.resume_from)
    for unit_id, script in scripts:
        print(f"[EXEC] {unit_id}: {script}", flush=True)
        result = subprocess.run([rscript, script], cwd=root, env=env, check=False)
        if result.returncode != 0:
            print(f"[FAIL] unit {unit_id} exited with {result.returncode}", file=sys.stderr)
            return result.returncode or 1
    print(f"[PASS] completed {len(scripts)} compute units")
    return 0


def relative_plan(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
