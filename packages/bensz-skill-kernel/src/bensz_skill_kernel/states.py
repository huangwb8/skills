"""Declarative meta-state definitions used by Agent Skills.

The lifecycle reducer in :mod:`runtime` remains deliberately small and stable.
This module provides the extensible, human-readable catalogue around it: each
state is a directory containing ``STATE.md`` and optional helper scripts.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


META_STATE_PROTOCOL_VERSION = "bensz-meta-state-v1"
SKILL_STATE_DECLARATION_VERSION = "bensz-skill-state-v1"
_SCRIPT_VERDICTS = frozenset({"pass", "fail", "uncertain", "unchecked", "error", "timed_out", "skipped"})


class StateDefinitionError(ValueError):
    """A state definition is missing or malformed."""


class StateTransitionError(StateDefinitionError):
    """A declarative state transition is not allowed."""


class StateExecutionError(StateDefinitionError):
    """A state helper could not be run or returned an invalid response."""


def _frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text.strip()
    lines = text.splitlines()
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise StateDefinitionError("state frontmatter is not closed") from exc
    values: dict[str, Any] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise StateDefinitionError(f"invalid state metadata line: {line}")
        key, raw = line.split(":", 1)
        key, raw = key.strip(), raw.strip()
        if not key:
            raise StateDefinitionError("state metadata key cannot be empty")
        if raw.startswith("[") and raw.endswith("]"):
            value: Any = [item.strip().strip("'\"") for item in raw[1:-1].split(",") if item.strip()]
        elif raw.lower() in {"true", "false"}:
            value = raw.lower() == "true"
        else:
            value = raw.strip("'\"")
        values[key] = value
    return values, "\n".join(lines[end + 1 :]).strip()


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    raise StateDefinitionError("state list metadata must be a string or list")


@dataclass(frozen=True)
class StateDefinition:
    id: str
    version: str = "1.0.0"
    description: str = ""
    kind: str = "skill"
    entry_conditions: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    transitions: tuple[str, ...] = ()
    entrypoint: str | None = None
    instructions: str = ""
    source: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", self.id):
            raise StateDefinitionError(f"invalid state id: {self.id!r}")
        if not self.version:
            raise StateDefinitionError("state version cannot be empty")

    @classmethod
    def from_markdown(cls, path: str | Path) -> "StateDefinition":
        target = Path(path)
        if target.name != "STATE.md" or not target.is_file():
            raise StateDefinitionError(f"state definition does not exist: {target}")
        metadata, instructions = _frontmatter(target.read_text(encoding="utf-8"))
        state_id = metadata.get("id")
        if not state_id:
            raise StateDefinitionError(f"state definition missing id: {target}")
        known = {"id", "version", "description", "kind", "entry", "entry_conditions", "invariants", "transitions", "next_states", "entrypoint"}
        extra = {key: value for key, value in metadata.items() if key not in known}
        return cls(
            id=str(state_id),
            version=str(metadata.get("version", "1.0.0")),
            description=str(metadata.get("description", "")),
            kind=str(metadata.get("kind", "skill")),
            entry_conditions=_as_tuple(metadata.get("entry_conditions", metadata.get("entry"))),
            invariants=_as_tuple(metadata.get("invariants")),
            transitions=_as_tuple(metadata.get("transitions", metadata.get("next_states"))),
            entrypoint=str(metadata["entrypoint"]) if metadata.get("entrypoint") else None,
            instructions=instructions,
            source=str(target),
            metadata=extra,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "description": self.description,
            "kind": self.kind,
            "entry_conditions": list(self.entry_conditions),
            "invariants": list(self.invariants),
            "transitions": list(self.transitions),
            "entrypoint": self.entrypoint,
            "instructions": self.instructions,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


class FilesystemStateRegistry:
    """Discover ``STATE.md`` definitions below a filesystem root."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self._states: dict[str, StateDefinition] = {}
        self.refresh()

    def refresh(self) -> None:
        self._states.clear()
        if not self.root.is_dir():
            return
        for path in sorted(self.root.rglob("STATE.md")):
            definition = StateDefinition.from_markdown(path)
            if definition.id in self._states:
                raise StateDefinitionError(f"duplicate state id: {definition.id}")
            self._states[definition.id] = definition

    def definitions(self, *, kind: str | None = None) -> tuple[StateDefinition, ...]:
        values = self._states.values()
        if kind:
            values = (item for item in values if item.kind == kind)
        return tuple(sorted(values, key=lambda item: item.id))

    def resolve(self, state_id: str) -> StateDefinition:
        try:
            return self._states[state_id]
        except KeyError as exc:
            raise StateDefinitionError(f"unknown state: {state_id}") from exc


class CombinedStateRegistry:
    """A read-only union of system and Skill-owned state directories."""

    def __init__(self, *registries: FilesystemStateRegistry):
        self.registries = registries
        self._states: dict[str, StateDefinition] = {}
        for registry in registries:
            for definition in registry.definitions():
                if definition.id in self._states:
                    raise StateDefinitionError(f"duplicate state id: {definition.id}")
                self._states[definition.id] = definition

    def definitions(self, *, kind: str | None = None) -> tuple[StateDefinition, ...]:
        values = self._states.values()
        if kind:
            values = (item for item in values if item.kind == kind)
        return tuple(sorted(values, key=lambda item: item.id))

    def resolve(self, state_id: str) -> StateDefinition:
        try:
            return self._states[state_id]
        except KeyError as exc:
            raise StateDefinitionError(f"unknown state: {state_id}") from exc


@dataclass(frozen=True)
class SkillStateDeclaration:
    """A Skill-owned selection of state packs, kept outside kernel code."""

    skill_root: Path
    initial_state: str
    state_roots: tuple[Path, ...]
    states: tuple[str, ...]
    source: Path

    @classmethod
    def from_skill_root(cls, skill_root: str | Path) -> "SkillStateDeclaration":
        root = Path(skill_root).expanduser().resolve()
        source = root / "state-machine.json"
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise StateDefinitionError(f"Skill state declaration does not exist: {source}") from exc
        except json.JSONDecodeError as exc:
            raise StateDefinitionError(f"invalid Skill state declaration: {exc.msg}") from exc
        if not isinstance(raw, Mapping) or raw.get("protocol") != SKILL_STATE_DECLARATION_VERSION:
            raise StateDefinitionError(f"Skill state declaration must use {SKILL_STATE_DECLARATION_VERSION}")
        initial = raw.get("initial_state", "workspace.ready")
        names = _as_tuple(raw.get("states"))
        roots = _as_tuple(raw.get("state_roots", ("states",)))
        if not names:
            raise StateDefinitionError("Skill state declaration must list at least one state")
        resolved_roots = []
        for item in roots:
            candidate = (root / item).resolve()
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise StateDefinitionError("state_roots must stay inside the Skill directory") from exc
            resolved_roots.append(candidate)
        return cls(root, str(initial), tuple(resolved_roots), names, source)

    def registry(self) -> "CombinedStateRegistry":
        registry = build_state_registry(*self.state_roots)
        declared = set(self.states) | {self.initial_state}
        available = {definition.id for definition in registry.definitions()}
        unknown = declared - available
        if unknown:
            raise StateDefinitionError(f"Skill state declaration references unknown states: {', '.join(sorted(unknown))}")
        return registry

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": SKILL_STATE_DECLARATION_VERSION,
            "initial_state": self.initial_state,
            "state_roots": [str(item) for item in self.state_roots],
            "states": list(self.states),
            "source": str(self.source),
        }


@dataclass(frozen=True)
class StateExecutionResult:
    """Normalized result returned by an optional state helper script."""

    state_id: str
    execution_status: str
    verdict: str
    summary: str = ""
    facts: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": META_STATE_PROTOCOL_VERSION,
            "state_id": self.state_id,
            "execution_status": self.execution_status,
            "verdict": self.verdict,
            "summary": self.summary,
            "facts": dict(self.facts),
            "evidence_refs": list(self.evidence_refs),
        }


def execute_state(definition: StateDefinition, request: Mapping[str, Any], *, timeout: int = 10) -> StateExecutionResult:
    """Run an optional state helper using the same JSON-stdio boundary as verifiers."""
    if not definition.entrypoint:
        return StateExecutionResult(definition.id, "not_applicable", "unchecked", "This state has no helper script.")
    if not definition.source:
        raise StateExecutionError(f"state {definition.id} has no source path")
    state_root = Path(definition.source).parent.resolve()
    entrypoint = (state_root / definition.entrypoint).resolve()
    try:
        entrypoint.relative_to(state_root)
    except ValueError as exc:
        raise StateExecutionError("state entrypoint must stay inside its state directory") from exc
    if not entrypoint.is_file():
        raise StateExecutionError(f"state entrypoint does not exist: {entrypoint}")
    command = [sys.executable, str(entrypoint)] if entrypoint.suffix == ".py" else [str(entrypoint)]
    payload = {"protocol": META_STATE_PROTOCOL_VERSION, "state": definition.to_dict(), "request": dict(request)}
    try:
        completed = subprocess.run(command, input=json.dumps(payload, ensure_ascii=False), text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return StateExecutionResult(definition.id, "timed_out", "timed_out", f"State helper exceeded {timeout} seconds.")
    if completed.returncode:
        return StateExecutionResult(definition.id, "error", "error", completed.stderr.strip() or f"State helper exited with {completed.returncode}.")
    try:
        raw = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise StateExecutionError(f"state helper must emit one JSON object: {exc.msg}") from exc
    if not isinstance(raw, Mapping) or raw.get("verdict") not in _SCRIPT_VERDICTS:
        raise StateExecutionError("state helper result requires a supported verdict")
    execution_status = str(raw.get("execution_status", "completed"))
    if execution_status != "completed":
        raise StateExecutionError("state helper execution_status must be completed")
    facts = raw.get("facts", {})
    refs = raw.get("evidence_refs", ())
    if not isinstance(facts, Mapping) or not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
        raise StateExecutionError("state helper facts must be an object and evidence_refs a string list")
    return StateExecutionResult(definition.id, execution_status, str(raw["verdict"]), str(raw.get("summary", "")), dict(facts), tuple(refs))


class StateMachine:
    """Small in-memory evaluator for a registry-defined meta-state graph.

    Persistence remains the responsibility of a Skill's event log.  This class
    only validates a requested transition against the ``STATE.md`` contract.
    """

    def __init__(self, registry: FilesystemStateRegistry | CombinedStateRegistry, initial: str = "workspace.ready"):
        self.registry = registry
        self.current = registry.resolve(initial).id

    def can_transition(self, target: str) -> bool:
        source = self.registry.resolve(self.current)
        destination = self.registry.resolve(target)
        return target in source.transitions or ("*" in source.transitions and self.current in destination.entry_conditions)

    def transition(self, target: str) -> StateDefinition:
        if not self.can_transition(target):
            raise StateTransitionError(f"illegal meta-state transition {self.current!r} -> {target!r}")
        self.current = self.registry.resolve(target).id
        return self.registry.resolve(self.current)

    def snapshot(self) -> dict[str, Any]:
        definition = self.registry.resolve(self.current)
        return {"state": self.current, "version": definition.version, "kind": definition.kind, "next_states": list(definition.transitions)}


def build_builtin_state_registry() -> FilesystemStateRegistry:
    return FilesystemStateRegistry(Path(__file__).with_name("states"))


def build_state_registry(*roots: str | Path) -> CombinedStateRegistry:
    """Combine builtin system states with zero or more Skill-owned state roots."""
    registries = [build_builtin_state_registry(), *(FilesystemStateRegistry(root) for root in roots)]
    return CombinedStateRegistry(*registries)
