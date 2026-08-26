"""Declarative meta-state definitions used by Agent Skills.

The lifecycle reducer in :mod:`runtime` remains deliberately small and stable.
This module provides the extensible, human-readable catalogue around it: each
state is a directory containing ``STATE.md`` and optional helper scripts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


class StateDefinitionError(ValueError):
    """A state definition is missing or malformed."""


class StateTransitionError(StateDefinitionError):
    """A declarative state transition is not allowed."""


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
        known = {"id", "version", "description", "kind", "entry", "entry_conditions", "invariants", "transitions", "next_states"}
        extra = {key: value for key, value in metadata.items() if key not in known}
        return cls(
            id=str(state_id),
            version=str(metadata.get("version", "1.0.0")),
            description=str(metadata.get("description", "")),
            kind=str(metadata.get("kind", "skill")),
            entry_conditions=_as_tuple(metadata.get("entry_conditions", metadata.get("entry"))),
            invariants=_as_tuple(metadata.get("invariants")),
            transitions=_as_tuple(metadata.get("transitions", metadata.get("next_states"))),
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


class StateMachine:
    """Small in-memory evaluator for a registry-defined meta-state graph.

    Persistence remains the responsibility of a Skill's event log.  This class
    only validates a requested transition against the ``STATE.md`` contract.
    """

    def __init__(self, registry: FilesystemStateRegistry, initial: str = "workspace.ready"):
        self.registry = registry
        self.current = registry.resolve(initial).id

    def can_transition(self, target: str) -> bool:
        return target in self.registry.resolve(self.current).transitions

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
