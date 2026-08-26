"""Safe task workspace creation and Skill-scoped path resolution."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE_KINDS = frozenset({"input", "output", "log"})
WORKSPACE_PROTOCOL_VERSION = "bensz-api-task-v1"


class WorkspaceError(ValueError):
    """A task workspace is invalid or outside the project boundary."""


def _safe_segment(value: str, *, label: str) -> str:
    if "/" in value or "\\" in value or value.strip() in {".", ".."}:
        raise WorkspaceError(f"{label} cannot contain path separators")
    candidate = re.sub(r"[^\w.-]+", "-", value.strip(), flags=re.UNICODE).strip(".-")
    if not candidate or candidate in {".", ".."}:
        raise WorkspaceError(f"{label} must contain at least one safe character")
    return candidate


@dataclass(frozen=True)
class WorkspacePaths:
    task_root: Path
    skill: str

    @property
    def skill_root(self) -> Path:
        return self.task_root / _safe_segment(self.skill, label="skill")

    def path(self, kind: str) -> Path:
        if kind not in WORKSPACE_KINDS:
            raise WorkspaceError(f"unknown workspace kind: {kind}; expected one of {sorted(WORKSPACE_KINDS)}")
        return self.skill_root / kind

    @property
    def events(self) -> Path:
        return self.task_root / "log" / "events.ndjson"

    @property
    def state(self) -> Path:
        return self.task_root / "log" / "state.json"


class TaskWorkspace:
    """A locked task root shared by all Skills in one logical task."""

    def __init__(self, task_root: str | Path):
        self.task_root = Path(task_root).expanduser().resolve()
        self.manifest_path = self.task_root / ".workspace.json"

    @classmethod
    def open_existing(cls, task_root: str | Path) -> "TaskWorkspace":
        """Open only a previously initialized task root under ``.bensz-api``."""
        workspace = cls(task_root)
        if workspace.task_root.parent.name != ".bensz-api":
            raise WorkspaceError("task root must be a direct child of .bensz-api")
        workspace.manifest()
        return workspace

    @classmethod
    def open(
        cls,
        project_root: str | Path = ".",
        *,
        task_root: str | Path | None = None,
        description: str = "task",
        now: datetime | None = None,
    ) -> "TaskWorkspace":
        project = Path(project_root).expanduser().resolve()
        if not project.is_dir():
            raise WorkspaceError(f"project root does not exist: {project}")
        bensz_root = project / ".bensz-api"
        if bensz_root.exists() and not bensz_root.is_dir():
            raise WorkspaceError(f".bensz-api must be a directory: {bensz_root}")
        bensz_root.mkdir(exist_ok=True)
        if task_root is None:
            stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M")
            slug = _safe_segment(description, label="description")
            candidate = bensz_root / f"task-{stamp}-{slug}"
            suffix = 0
            while candidate.exists():
                suffix += 1
                candidate = bensz_root / f"task-{stamp}-{slug}-{chr(96 + suffix) if suffix <= 26 else suffix}"
        else:
            candidate = Path(task_root).expanduser()
            if not candidate.is_absolute():
                candidate = project / candidate
            candidate = candidate.resolve()
            try:
                candidate.relative_to(bensz_root.resolve())
            except ValueError as exc:
                raise WorkspaceError("task root must be inside project .bensz-api") from exc
        candidate.mkdir(parents=True, exist_ok=True)
        workspace = cls(candidate)
        if workspace.manifest_path.exists():
            try:
                manifest = json.loads(workspace.manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise WorkspaceError(f"invalid workspace manifest: {workspace.manifest_path}") from exc
            if manifest.get("protocol") != WORKSPACE_PROTOCOL_VERSION:
                raise WorkspaceError("workspace protocol version mismatch")
        else:
            manifest = {
                "protocol": WORKSPACE_PROTOCOL_VERSION,
                "state": "workspace.ready",
                "created_at": (now or datetime.now()).isoformat(timespec="seconds"),
            }
            try:
                with workspace.manifest_path.open("x", encoding="utf-8") as handle:
                    handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            except FileExistsError:
                existing = workspace.manifest()
                if existing.get("protocol") != WORKSPACE_PROTOCOL_VERSION:
                    raise WorkspaceError("workspace protocol version mismatch")
        (candidate / "log").mkdir(exist_ok=True)
        return workspace

    def paths(self, skill: str, *, create: bool = True) -> WorkspacePaths:
        paths = WorkspacePaths(self.task_root, _safe_segment(skill, label="skill"))
        if create:
            for kind in WORKSPACE_KINDS:
                paths.path(kind).mkdir(parents=True, exist_ok=True)
        return paths

    def manifest(self) -> dict[str, Any]:
        if not self.manifest_path.is_file():
            raise WorkspaceError(f"workspace manifest does not exist: {self.manifest_path}")
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    @property
    def events(self) -> Path:
        return self.task_root / "log" / "events.ndjson"

    @property
    def state(self) -> Path:
        return self.task_root / "log" / "state.json"

    def status(self) -> dict[str, Any]:
        manifest = self.manifest()
        skills = sorted(path.name for path in self.task_root.iterdir() if path.is_dir() and path.name != "log" and not path.name.startswith("."))
        return {"task_root": str(self.task_root), "manifest": manifest, "skills": skills, "events": str(self.events), "state": str(self.state)}


def workspace_path(
    project_root: str | Path = ".",
    *,
    skill: str,
    kind: str,
    task_root: str | Path | None = None,
    description: str = "task",
) -> Path:
    """Resolve one Skill-scoped directory through the canonical workspace API."""
    workspace = TaskWorkspace.open(project_root, task_root=task_root, description=description)
    return workspace.paths(skill).path(kind)
