#!/usr/bin/env python3
"""Resolve auto-test-project task workspaces without guessing continuation state."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


SKILL_NAME = "auto-test-project"
_TASK_NAME_RE = re.compile(r"^task-\d{8}-\d{4}-[^\s/]+$")


@dataclass(frozen=True)
class WorkspaceLayout:
    project_root: Path
    task_root: Path
    skill_root: Path
    plans_dir: Path
    tests_dir: Path
    created_task_root: bool = False
    legacy: bool = False


def _safe_relative(value: str, *, default: str, label: str) -> Path:
    raw = value.strip() or default
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a task-local relative path: {raw}")
    return path


def _directory_paths(directories: Mapping[str, str]) -> tuple[Path, Path]:
    plans_rel = _safe_relative(
        directories.get("plans", ""), default="output/plans", label="directories.plans"
    )
    tests_rel = _safe_relative(
        directories.get("tests", ""), default="output/tests", label="directories.tests"
    )
    return plans_rel, tests_rel


def _require_directory(path: Path, *, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"{label} must be a real directory, not a file or symlink: {path}")


def _require_direct_child(path: Path, *, parent: Path, label: str) -> None:
    if path.parent != parent:
        raise ValueError(f"{label} must be a direct child of {parent}: {path}")


def _reject_existing_symlinks(base: Path, path: Path, *, label: str) -> None:
    try:
        relative = path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside project root: {path}") from exc

    current = base
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError(f"{label} must not traverse a symlink: {current}")


def _resolve_task_input(project_root: Path, raw: str) -> Path:
    source = Path(raw).expanduser()
    if ".." in source.parts:
        raise ValueError("--task-root must not contain '..'")
    candidate = source if source.is_absolute() else project_root / source
    if candidate.exists() and candidate.is_symlink():
        raise ValueError(f"task root must not be a symlink: {candidate}")
    candidate = candidate.resolve()
    _reject_existing_symlinks(project_root, candidate, label="task root")
    return candidate


def _slugify_description(value: str) -> str:
    slug = re.sub(r"[^\w-]+", "-", value.strip(), flags=re.UNICODE).strip("-_")
    return slug or SKILL_NAME


def _task_readme(task_root: Path) -> str:
    return (
        "# auto-test-project Task Workspace\n\n"
        "This task root was allocated by `create_test_session.py`. "
        "Pass it back with `--task-root` for A/B rounds and continuations.\n"
    )


def _allocate_task_root(project_root: Path, *, description: str, now: dt.datetime | None) -> Path:
    bensz_root = project_root / ".bensz-api"
    if bensz_root.exists() and (bensz_root.is_symlink() or not bensz_root.is_dir()):
        raise ValueError(f".bensz-api must be a real directory: {bensz_root}")
    bensz_root.mkdir(parents=True, exist_ok=True)

    current = now or dt.datetime.now()
    base_name = f"task-{current:%Y%m%d-%H%M}-{_slugify_description(description)}"
    suffixes = [""] + [f"-{chr(code)}" for code in range(ord("a"), ord("z") + 1)]
    for suffix in suffixes:
        candidate = bensz_root / f"{base_name}{suffix}"
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate.resolve()
    raise FileExistsError(f"Unable to allocate a unique task root for {base_name}")


def _explicit_task_root(project_root: Path, *, raw: str, create: bool) -> tuple[Path, bool]:
    bensz_root = project_root / ".bensz-api"
    if bensz_root.exists() and (bensz_root.is_symlink() or not bensz_root.is_dir()):
        raise ValueError(f".bensz-api must be a real directory: {bensz_root}")

    candidate = _resolve_task_input(project_root, raw)
    expected_parent = bensz_root.resolve()
    _require_direct_child(candidate, parent=expected_parent, label="task root")
    if not _TASK_NAME_RE.fullmatch(candidate.name):
        raise ValueError(
            "--task-root directory name must match task-YYYYMMDD-HHMM-<description>"
        )

    created = False
    if candidate.exists():
        _require_directory(candidate, label="task root")
    elif create:
        bensz_root.mkdir(parents=True, exist_ok=True)
        candidate.mkdir()
        created = True
    else:
        raise FileNotFoundError(f"task root does not exist: {candidate}")
    return candidate, created


def _layout_from_skill_root(
    *,
    project_root: Path,
    task_root: Path,
    skill_root: Path,
    directories: Mapping[str, str],
    create: bool,
    created_task_root: bool = False,
    legacy: bool = False,
) -> WorkspaceLayout:
    plans_rel, tests_rel = _directory_paths(directories)
    plans_dir = skill_root / plans_rel
    tests_dir = skill_root / tests_rel

    if create:
        for path in (skill_root / "input", skill_root / "output", skill_root / "log", plans_dir, tests_dir):
            _reject_existing_symlinks(task_root, path, label="skill workspace path")
            if path.exists() and (path.is_symlink() or not path.is_dir()):
                raise ValueError(f"skill workspace path must be a real directory: {path}")
            path.mkdir(parents=True, exist_ok=True)
    else:
        _require_directory(skill_root, label="skill workspace")
        _require_directory(plans_dir, label="plans directory")
        _require_directory(tests_dir, label="tests directory")

    return WorkspaceLayout(
        project_root=project_root,
        task_root=task_root,
        skill_root=skill_root,
        plans_dir=plans_dir,
        tests_dir=tests_dir,
        created_task_root=created_task_root,
        legacy=legacy,
    )


def resolve_workspace(
    *,
    project_root: Path,
    task_root_arg: str,
    task_description: str,
    directories: Mapping[str, str],
    create: bool,
    now: dt.datetime | None = None,
) -> WorkspaceLayout:
    """Resolve or allocate an active task workspace."""
    project_root = project_root.expanduser().resolve()
    _require_directory(project_root, label="project root")
    _directory_paths(directories)

    if task_root_arg.strip():
        task_root, created = _explicit_task_root(
            project_root, raw=task_root_arg.strip(), create=create
        )
    elif create:
        task_root = _allocate_task_root(
            project_root, description=task_description, now=now
        )
        created = True
    else:
        raise ValueError("--task-root is required when verifying an active task workspace")

    if created:
        readme = task_root / "README.md"
        readme.write_text(_task_readme(task_root), encoding="utf-8")

    return _layout_from_skill_root(
        project_root=project_root,
        task_root=task_root,
        skill_root=task_root / SKILL_NAME,
        directories=directories,
        create=create,
        created_task_root=created,
    )


def resolve_legacy_workspace(
    *, project_root: Path, legacy_root_arg: str, directories: Mapping[str, str]
) -> WorkspaceLayout:
    """Resolve the one supported legacy root for read-only verification."""
    project_root = project_root.expanduser().resolve()
    _require_directory(project_root, label="project root")
    source = Path(legacy_root_arg).expanduser()
    if ".." in source.parts:
        raise ValueError("--legacy-root must not contain '..'")
    candidate = source if source.is_absolute() else project_root / source
    if candidate.exists() and candidate.is_symlink():
        raise ValueError(f"legacy root must not be a symlink: {candidate}")
    candidate = candidate.resolve()
    _reject_existing_symlinks(project_root, candidate, label="legacy root")
    expected = (project_root / ".bensz-api" / "skills" / SKILL_NAME).resolve()
    if candidate != expected:
        raise ValueError(f"--legacy-root must resolve to {expected}")
    _require_directory(candidate, label="legacy root")
    return _layout_from_skill_root(
        project_root=project_root,
        task_root=candidate.parent.parent,
        skill_root=candidate,
        directories=directories,
        create=False,
        legacy=True,
    )


def infer_active_workspace_from_session(
    *, project_root: Path, session_dir: Path, directories: Mapping[str, str]
) -> WorkspaceLayout:
    """Infer only a task-* workspace from an explicit session path."""
    project_root = project_root.expanduser().resolve()
    session_dir = session_dir.expanduser().resolve()
    tests_rel = _safe_relative(
        directories.get("tests", ""), default="output/tests", label="directories.tests"
    )
    try:
        skill_root = session_dir.parents[len(tests_rel.parts)]
    except IndexError as exc:
        raise ValueError(f"session path is too shallow: {session_dir}") from exc
    task_root = skill_root.parent
    expected_parent = (project_root / ".bensz-api").resolve()
    _require_direct_child(task_root, parent=expected_parent, label="task root")
    if not _TASK_NAME_RE.fullmatch(task_root.name) or skill_root.name != SKILL_NAME:
        raise ValueError("session is not inside an active auto-test-project task workspace")
    layout = _layout_from_skill_root(
        project_root=project_root,
        task_root=task_root,
        skill_root=skill_root,
        directories=directories,
        create=False,
    )
    try:
        session_dir.relative_to(layout.tests_dir)
    except ValueError as exc:
        raise ValueError(f"session is outside configured tests directory: {session_dir}") from exc
    return layout
