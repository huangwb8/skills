"""Safe task workspace creation and Skill-scoped path resolution."""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


WORKSPACE_KINDS = frozenset({"input", "output", "log"})
WORKSPACE_PROTOCOL_VERSION = "bensz-api-task-v1"
META_STATE_SNAPSHOT_VERSION = "bensz-meta-state-v1"


def _redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): ("[REDACTED]" if any(token in str(k).lower() for token in ("token", "secret", "password", "cookie", "api_key", "credential")) else _redact(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


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

    @property
    def meta_state(self) -> Path:
        return self.skill_root / "log" / "meta-state.json"


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
                "state": "bensz.workspace.ready",
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
        for kind in WORKSPACE_KINDS:
            (candidate / "shared" / kind).mkdir(parents=True, exist_ok=True)
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

    def update_manifest(self, **fields: Any) -> dict[str, Any]:
        """Atomically extend the workspace manifest with a run contract snapshot."""
        current = self.manifest()
        current.update(fields)
        temporary = self.manifest_path.with_name(self.manifest_path.name + ".tmp")
        temporary.write_text(json.dumps(current, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.manifest_path)
        return current

    def record_run_snapshot(self, *, skill_id: str, skill_version: str | None = None, runtime_config: Mapping[str, Any] | None = None, state_versions: Mapping[str, str] | None = None, verifier_versions: Mapping[str, str] | None = None, model: str | None = None, prompt: str | None = None, tools: Iterable[str] = (), evidence: Mapping[str, str] | None = None, authorization: Mapping[str, Any] | None = None) -> dict[str, Any]:
        snapshot = {
            "skill_id": skill_id,
            "skill_version": skill_version,
            "runtime_config": _redact(dict(runtime_config or {})),
            "state_versions": dict(state_versions or {}),
            "verifier_versions": dict(verifier_versions or {}),
            "model": model,
            "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest() if prompt is not None else None,
            "tools": sorted(set(str(item) for item in tools)),
            "evidence": _redact(dict(evidence or {})),
            "authorization": _redact(dict(authorization or {})),
        }
        snapshot["contract_hash"] = hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return self.update_manifest(run_snapshot=snapshot)

    @property
    def events(self) -> Path:
        return self.task_root / "log" / "events.ndjson"

    @property
    def state(self) -> Path:
        return self.task_root / "log" / "state.json"

    def status(self) -> dict[str, Any]:
        manifest = self.manifest()
        skills = sorted(path.name for path in self.task_root.iterdir() if path.is_dir() and path.name not in {"log", "shared"} and not path.name.startswith("."))
        return {"task_root": str(self.task_root), "manifest": manifest, "skills": skills, "events": str(self.events), "state": str(self.state)}

    def read_meta_state(self, skill: str) -> dict[str, Any]:
        paths = self.paths(skill)
        if not paths.meta_state.is_file():
            return {
                "protocol": META_STATE_SNAPSHOT_VERSION,
                "skill": paths.skill,
                "current_state": "bensz.workspace.ready",
                "state_version": "1.0.0",
                "workspace_state": self.manifest().get("state"),
            }
        try:
            return json.loads(paths.meta_state.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise WorkspaceError(f"invalid meta-state snapshot: {paths.meta_state}") from exc

    def write_meta_state(self, skill: str, snapshot: dict[str, Any]) -> Path:
        paths = self.paths(skill)
        target = paths.meta_state
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        temporary.replace(target)
        return target


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
