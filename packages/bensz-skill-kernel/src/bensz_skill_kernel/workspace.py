"""Safe task workspace creation and Skill-scoped path resolution."""

from __future__ import annotations

import json
import hashlib
import os
import re
import platform
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from .identity import STATE_IDENTITY_PROTOCOL, normalize_state_identity

WORKSPACE_KINDS = frozenset({"input", "output", "log"})
WORKSPACE_PROTOCOL_VERSION = "bensz-api-task-v1"
META_STATE_SNAPSHOT_VERSION = "bensz-meta-state-v2"
_SNAPSHOT_VOLATILE_FIELDS = frozenset({"snapshot_hash", "state_event_id", "path"})
_RUN_SNAPSHOT_DERIVED_FIELDS = frozenset({"snapshot_hash", "snapshot_id", "contract_hash"})


def state_snapshot_hash(snapshot: Mapping[str, Any]) -> str:
    """Hash the stable state snapshot fields using the public audit contract."""
    stable = {str(key): value for key, value in snapshot.items() if key not in _SNAPSHOT_VOLATILE_FIELDS}
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _validate_meta_state_snapshot(snapshot: Mapping[str, Any]) -> None:
    protocol = snapshot.get("protocol", "bensz-meta-state-v1")
    if protocol not in {"bensz-meta-state-v1", META_STATE_SNAPSHOT_VERSION}:
        raise WorkspaceError("meta-state snapshot protocol is unsupported")
    if protocol == META_STATE_SNAPSHOT_VERSION:
        if snapshot.get("identity_protocol") != STATE_IDENTITY_PROTOCOL:
            raise WorkspaceError("v2 meta-state snapshot requires the State identity protocol")
        try:
            normalize_state_identity(
                {
                    "run_id": snapshot.get("run_id"),
                    "state_visit_id": snapshot.get("state_visit_id"),
                    "attempt_id": snapshot.get("active_attempt_id"),
                },
                label="meta-state snapshot identity",
            )
        except ValueError as exc:
            raise WorkspaceError(str(exc)) from exc


def _redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): ("[REDACTED]" if any(token in str(k).lower() for token in ("token", "secret", "password", "cookie", "api_key", "credential")) else _redact(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


class WorkspaceError(ValueError):
    """A task workspace is invalid or outside the project boundary."""


def _run_snapshot_digest(snapshot: Mapping[str, Any]) -> str:
    payload = {
        str(key): value
        for key, value in snapshot.items()
        if key not in _RUN_SNAPSHOT_DERIVED_FIELDS
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_run_snapshot(snapshot: Mapping[str, Any]) -> None:
    digest = _run_snapshot_digest(snapshot)
    legacy_hash = snapshot.get("contract_hash")
    if snapshot.get("snapshot_hash") is None and snapshot.get("snapshot_id") is None:
        if legacy_hash == digest.removeprefix("sha256:"):
            return
        raise WorkspaceError("run snapshot integrity mismatch")
    snapshot_id = "run-snapshot-" + digest.removeprefix("sha256:")[:24]
    if (
        snapshot.get("snapshot_hash") != digest
        or snapshot.get("contract_hash") != digest
        or snapshot.get("snapshot_id") != snapshot_id
    ):
        raise WorkspaceError("run snapshot integrity mismatch")


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

    @classmethod
    def create_exclusive(
        cls,
        project_root: str | Path = ".",
        *,
        task_root: str | Path | None = None,
        description: str = "task",
        now: datetime | None = None,
    ) -> tuple["TaskWorkspace", str]:
        """Atomically reserve a new task root and return its ownership token."""
        project = Path(project_root).expanduser().resolve()
        if not project.is_dir():
            raise WorkspaceError(f"project root does not exist: {project}")
        bensz_root = project / ".bensz-api"
        if bensz_root.exists() and not bensz_root.is_dir():
            raise WorkspaceError(f".bensz-api must be a directory: {bensz_root}")
        bensz_root.mkdir(exist_ok=True)
        owner = str(uuid.uuid4())
        instant = now or datetime.now()

        if task_root is not None:
            candidate = Path(task_root).expanduser()
            if not candidate.is_absolute():
                candidate = project / candidate
            candidate = candidate.resolve()
            try:
                candidate.relative_to(bensz_root.resolve())
            except ValueError as exc:
                raise WorkspaceError("task root must be inside project .bensz-api") from exc
            try:
                candidate.mkdir()
            except FileExistsError as exc:
                raise WorkspaceError("workspace_already_exists: atomic initialization requires a new task root") from exc
        else:
            stamp = instant.strftime("%Y%m%d-%H%M")
            slug = _safe_segment(description, label="description")
            suffix = 0
            while True:
                ending = "" if suffix == 0 else f"-{chr(96 + suffix) if suffix <= 26 else suffix}"
                candidate = bensz_root / f"task-{stamp}-{slug}{ending}"
                try:
                    candidate.mkdir()
                    break
                except FileExistsError:
                    suffix += 1

        workspace = cls(candidate)
        manifest = {
            "protocol": WORKSPACE_PROTOCOL_VERSION,
            "state": "bensz.workspace.ready",
            "created_at": instant.isoformat(timespec="seconds"),
            "initialization_owner": owner,
        }
        try:
            with workspace.manifest_path.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            (candidate / "log").mkdir()
            for kind in WORKSPACE_KINDS:
                (candidate / "shared" / kind).mkdir(parents=True)
        except Exception:
            if candidate.is_dir():
                shutil.rmtree(candidate)
            raise
        return workspace, owner

    def paths(self, skill: str, *, create: bool = True) -> WorkspacePaths:
        paths = WorkspacePaths(self.task_root, _safe_segment(skill, label="skill"))
        if create:
            for kind in WORKSPACE_KINDS:
                paths.path(kind).mkdir(parents=True, exist_ok=True)
        return paths

    def manifest(self) -> dict[str, Any]:
        if not self.manifest_path.is_file():
            raise WorkspaceError(f"workspace manifest does not exist: {self.manifest_path}")
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkspaceError(f"invalid workspace manifest: {self.manifest_path}") from exc
        if not isinstance(manifest, dict) or manifest.get("protocol") != WORKSPACE_PROTOCOL_VERSION:
            raise WorkspaceError("workspace protocol version mismatch")
        run_snapshot = manifest.get("run_snapshot")
        if run_snapshot is not None:
            if not isinstance(run_snapshot, Mapping):
                raise WorkspaceError("run snapshot integrity mismatch")
            _validate_run_snapshot(run_snapshot)
        return manifest

    def _replace_manifest(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        value = dict(manifest)
        temporary = self.manifest_path.with_name(self.manifest_path.name + ".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, self.manifest_path)
        return value

    def update_manifest(self, **fields: Any) -> dict[str, Any]:
        """Atomically extend the workspace manifest with a run contract snapshot."""
        current = self.manifest()
        if "run_snapshot" in fields and "run_snapshot" in current and fields["run_snapshot"] != current["run_snapshot"]:
            raise WorkspaceError("run snapshot is immutable; create a new workspace/task root for another run")
        current.update(fields)
        return self._replace_manifest(current)

    def complete_initialization(self, owner: str) -> dict[str, Any]:
        manifest = self.manifest()
        if manifest.get("initialization_owner") != owner:
            raise WorkspaceError("workspace initialization ownership mismatch")
        manifest.pop("initialization_owner", None)
        return self._replace_manifest(manifest)

    def rollback_initialization(self, owner: str) -> None:
        """Remove only a task root still owned by this initialization call."""
        manifest = self.manifest()
        if manifest.get("initialization_owner") != owner:
            raise WorkspaceError("workspace initialization ownership mismatch; refusing rollback")
        shutil.rmtree(self.task_root)

    def record_run_snapshot(self, *, skill_id: str, run_id: str | None = None, skill_version: str | None = None, identity_policy: str | None = None, runtime_config: Mapping[str, Any] | None = None, state_versions: Mapping[str, str] | None = None, state_contract_hashes: Mapping[str, str] | None = None, verifier_versions: Mapping[str, str] | None = None, verifier_contract_hashes: Mapping[str, Any] | None = None, model: str | None = None, prompt: str | None = None, tools: Iterable[str] = (), evidence: Mapping[str, str] | None = None, authorization: Mapping[str, Any] | None = None) -> dict[str, Any]:
        from . import __version__ as kernel_version

        snapshot = {
            "skill_id": skill_id,
            "run_id": run_id,
            "skill_version": skill_version,
            "identity_policy": identity_policy,
            "kernel_version": kernel_version,
            "runtime_config": _redact(dict(runtime_config or {})),
            "state_versions": dict(state_versions or {}),
            "state_contract_hashes": dict(state_contract_hashes or {}),
            "verifier_versions": dict(verifier_versions or {}),
            "verifier_contract_hashes": dict(verifier_contract_hashes or {}),
            "python": {
                "implementation": platform.python_implementation(),
                "version": platform.python_version(),
                "version_info": list(sys.version_info[:3]),
            },
            "model": model,
            "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest() if prompt is not None else None,
            "tools": sorted(set(str(item) for item in tools)),
            "evidence": _redact(dict(evidence or {})),
            "authorization": _redact(dict(authorization or {})),
        }
        snapshot_hash = _run_snapshot_digest(snapshot)
        snapshot["snapshot_hash"] = snapshot_hash
        snapshot["snapshot_id"] = "run-snapshot-" + snapshot_hash.removeprefix("sha256:")[:24]
        snapshot["contract_hash"] = snapshot_hash
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
        if paths.meta_state.with_name(paths.meta_state.name + ".tmp").exists():
            raise WorkspaceError(f"meta-state snapshot has an incomplete commit: {paths.meta_state}")
        if not paths.meta_state.is_file():
            return {
                "protocol": "bensz-meta-state-v1",
                "skill": paths.skill,
                "current_state": "bensz.workspace.ready",
                "state_version": "1.0.0",
                "workspace_state": self.manifest().get("state"),
                "legacy_identity": True,
            }
        try:
            snapshot = json.loads(paths.meta_state.read_text(encoding="utf-8"))
            if not isinstance(snapshot, dict):
                raise ValueError("snapshot must be an object")
            _validate_meta_state_snapshot(snapshot)
            expected = snapshot.get("snapshot_hash")
            if expected and str(expected).removeprefix("sha256:") != state_snapshot_hash(snapshot):
                raise WorkspaceError(f"meta-state snapshot integrity mismatch: {paths.meta_state}")
            if snapshot.get("state_event_id") == "pending":
                raise WorkspaceError(f"meta-state snapshot has an incomplete commit: {paths.meta_state}")
            return snapshot
        except WorkspaceError:
            raise
        except (json.JSONDecodeError, ValueError) as exc:
            raise WorkspaceError(f"invalid meta-state snapshot: {paths.meta_state}") from exc

    def write_meta_state(self, skill: str, snapshot: dict[str, Any]) -> Path:
        temporary, target = self.prepare_meta_state(skill, snapshot)
        os.replace(temporary, target)
        return target

    def prepare_meta_state(self, skill: str, snapshot: dict[str, Any]) -> tuple[Path, Path]:
        """Write and fsync a snapshot staging file without publishing it."""
        _validate_meta_state_snapshot(snapshot)
        if snapshot.get("snapshot_hash") and str(snapshot["snapshot_hash"]).removeprefix("sha256:") != state_snapshot_hash(snapshot):
            raise WorkspaceError("meta-state snapshot hash does not match its contents")
        paths = self.paths(skill)
        target = paths.meta_state
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        return temporary, target

    def commit_meta_state(self, temporary: Path, target: Path) -> Path:
        """Atomically publish a previously prepared snapshot."""
        os.replace(temporary, target)
        try:
            directory = os.open(str(target.parent), os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass
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
