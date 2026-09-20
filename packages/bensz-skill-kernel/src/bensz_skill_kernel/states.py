"""Declarative meta-state definitions used by Agent Skills.

The lifecycle reducer in :mod:`runtime` remains deliberately small and stable.
This module provides the extensible, human-readable catalogue around it: each
state is a directory containing ``STATE.md`` and optional helper scripts.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .contract_packs import ContractExecutionReport, ContractPack, ContractPackExecutor, STATE_MODES
from .identity import STATE_IDENTITY_PROTOCOL, normalize_state_identity, validate_kernel_runtime_declaration
from .packs import load_pack_entries, resolve_entrypoint, run_stdio
from .state_ids import parse_state_aliases, validate_state_id


META_STATE_PROTOCOL_VERSION = "bensz-meta-state-v2"
SKILL_STATE_DECLARATION_VERSION = "bensz-skill-state-v1"
_SCRIPT_VERDICTS = frozenset({"pass", "fail", "uncertain", "unchecked", "error", "timed_out", "skipped"})

# Invariants are intentionally opt-in and conservative.  Free-form invariant
# text remains documentation; only entries with a defined kernel meaning are
# enforced here.  This keeps domain rules out of the kernel while allowing a
# Skill to request a small set of generic evidence guards.
_INVARIANT_EVENT_REQUIREMENTS = {
    "verifier-result-recorded": frozenset({"verification.result", "verification.gate"}),
}
_GATE_BINDING_INVARIANTS = frozenset({
    "verifier-result-recorded",
    "verifier-gate-allow",
    "required-verifiers-pass",
})


class StateDefinitionError(ValueError):
    """A state definition is missing or malformed."""


class StateTransitionError(StateDefinitionError):
    """A declarative state transition is not allowed."""


class StateExecutionError(StateDefinitionError):
    """A state helper could not be run or returned an invalid response."""


def state_requires_gate_binding(definition: "StateDefinition") -> bool:
    """Return whether a State contract protects its exit with a verifier Gate.

    The decision is derived only from Kernel-defined invariants declared by the
    State Pack.  It deliberately does not inspect domain State IDs or edge
    names, so system/initialization edges remain governed by their contracts.
    """
    return bool(_GATE_BINDING_INVARIANTS.intersection(definition.invariants))


def check_state_invariants(definition: "StateDefinition", events: Iterable[Any] = (), *, context: Mapping[str, Any] | None = None) -> tuple[str, ...]:
    """Return failed, kernel-defined invariants for a state.

    State contracts may contain prose invariants that require a domain adapter
    or human review.  Those are deliberately not guessed by the kernel.  The
    supported ``verifier-result-recorded`` invariant is an evidence guard: a
    task event stream must contain both a verifier result and its Gate before
    leaving the checking state.  When ``context.skill`` identifies the owning
    Skill, only evidence recorded after its latest entry into the current State
    is eligible.
    """
    event_list = list(events)
    context = context or {}
    run_id = context.get("run_id")
    state_visit_id = context.get("state_visit_id")
    attempt_id = context.get("attempt_id")
    skill = context.get("skill")
    def _value(event: Any, key: str, default: Any = None) -> Any:
        if isinstance(event, Mapping):
            return event.get(key, default)
        return getattr(event, key, default)

    def _payload(event: Any) -> Mapping[str, Any]:
        payload = _value(event, "payload", {})
        return payload if isinstance(payload, Mapping) else {}

    def _event_type(event: Any) -> str:
        return str(_value(event, "type", _value(event, "event_type", "")))

    # A Gate proves that the current State may be left only when its evidence
    # was produced during the current visit to that State.  Without this
    # temporal window, an earlier State's passing result can be reused later
    # when a caller keeps the same run/attempt identity.
    state_entry_position: int | None = None
    attempt_window_position: int | None = None
    state_entry_event: Any | None = None
    active_identity: dict[str, Any] | None = None
    v2_identity = False
    if isinstance(skill, str) and skill:
        for position, event in enumerate(event_list):
            payload = _payload(event)
            if (
                _event_type(event) == "state.transition"
                and payload.get("state_domain") == "skill"
                and payload.get("skill") == skill
                and payload.get("to_state") == definition.id
            ):
                state_entry_position = position
                attempt_window_position = position
                state_entry_event = event
                if payload.get("identity_protocol") == STATE_IDENTITY_PROTOCOL:
                    try:
                        active_identity = normalize_state_identity(payload.get("target_identity", {}), label="target identity")
                    except ValueError:
                        return ("State entry has an invalid target identity",)
                    v2_identity = True
                else:
                    active_identity = {
                        "run_id": _value(event, "run_id"),
                        "state_visit_id": _value(event, "state_visit_id"),
                        "attempt_id": _value(event, "attempt_id", "default"),
                    }
                    v2_identity = False
            elif (
                state_entry_position is not None
                and _event_type(event) == "state.attempt.started"
                and payload.get("skill") == skill
                and payload.get("state") == definition.id
            ):
                if not v2_identity or active_identity is None:
                    return ("attempt start exists without an active v2 State visit",)
                if (
                    _value(event, "run_id") != active_identity["run_id"]
                    or _value(event, "state_visit_id") != active_identity["state_visit_id"]
                    or payload.get("supersedes_attempt_id") != active_identity["attempt_id"]
                ):
                    return ("attempt start identity does not match the active State visit",)
                active_identity = {
                    "run_id": active_identity["run_id"],
                    "state_visit_id": active_identity["state_visit_id"],
                    "attempt_id": _value(event, "attempt_id", "default"),
                }
                attempt_window_position = position

    # Once an event stream carries run identity, silently evaluating the
    # invariant against all historical attempts would allow stale evidence to
    # satisfy a new run.  Callers must provide the *pair* explicitly; a
    # half-bound context is ambiguous and is rejected as well.
    has_identity = any(_value(event, "run_id") is not None or _value(event, "attempt_id", "default") != "default" for event in event_list)
    identity_bound_invariants = {
        "verifier-result-recorded", "verifier-gate-allow", "required-verifiers-pass",
    }
    active_identity_invariants = identity_bound_invariants.intersection(definition.invariants)
    if active_identity_invariants and has_identity and (run_id is None or attempt_id is None):
        return (
            f"{sorted(active_identity_invariants)[0]} (run_id/attempt_id required; both must be provided)",
        )
    if active_identity_invariants and v2_identity and state_visit_id is None:
        return (
            f"{sorted(active_identity_invariants)[0]} (state_visit_id required for a v2 State visit)",
        )
    if (
        state_entry_event is not None
        and (run_id is not None or attempt_id is not None)
        and active_identity_invariants
        and active_identity is not None
        and active_identity != {
            "run_id": run_id,
            "state_visit_id": state_visit_id,
            "attempt_id": attempt_id,
        }
    ):
        return (
            "context identity does not match the active state visit/attempt"
            if v2_identity
            else "state entry identity does not match current run_id/attempt_id",
        )
    positioned_events = list(enumerate(event_list))
    if run_id is not None or attempt_id is not None:
        def _matches(event: Any) -> bool:
            get = event.get if isinstance(event, Mapping) else lambda key, default=None: getattr(event, key, default)
            return (
                (run_id is None or get("run_id") == run_id)
                and (state_visit_id is None or get("state_visit_id") == state_visit_id)
                and (attempt_id is None or get("attempt_id", "default") == attempt_id)
            )
        positioned_events = [(position, event) for position, event in positioned_events if _matches(event)]
    window_position = attempt_window_position if attempt_window_position is not None else state_entry_position
    if window_position is not None:
        positioned_events = [
            (position, event)
            for position, event in positioned_events
            if position > window_position
        ]
    event_list = [event for _, event in positioned_events]
    event_types = {
        _event_type(event)
        for event in event_list
    }
    failures: list[str] = []
    for invariant in definition.invariants:
        required = _INVARIANT_EVENT_REQUIREMENTS.get(invariant)
        if required:
            missing = sorted(required - event_types)
            if missing:
                timing = (
                    " after current attempt start"
                    if attempt_window_position is not None and attempt_window_position != state_entry_position
                    else (" after current state entry" if state_entry_position is not None else "")
                )
                failures.append(f"{invariant} (missing events{timing}: {', '.join(missing)})")
            elif run_id is not None or attempt_id is not None:
                result_events = [e for e in event_list if _value(e, "type", _value(e, "event_type", "")) == "verification.result"]
                gate_events = [e for e in event_list if _value(e, "type", _value(e, "event_type", "")) == "verification.gate"]
                result_refs = {f"{_payload(e).get('verifier_id')}@{_payload(e).get('verifier_version')}" for e in result_events}
                if any(ref.startswith("None@") or ref.endswith("@None") for ref in result_refs):
                    failures.append(f"{invariant} (verification result missing verifier identity)")
                gate_refs = set()
                for gate in gate_events:
                    payload = _payload(gate)
                    gate_refs.update(str(item) for item in payload.get("result_refs", ()))
                if result_refs and not result_refs.issubset(gate_refs):
                    failures.append(f"{invariant} (gate result_refs do not cover current run results)")
                result_event_ids = {str(_value(item, "event_id")) for item in result_events}
                bound_ids = {str(_payload(item).get("result_event_id")) for item in gate_events if _payload(item).get("result_event_id")}
                if gate_events and not bound_ids:
                    failures.append(f"{invariant} (gate is not bound to a current result event)")
                elif bound_ids and not bound_ids.issubset(result_event_ids):
                    failures.append(f"{invariant} (gate result_event_id is not from the current run)")
        elif invariant == "verifier-gate-allow":
            allowed = False
            for event in event_list:
                kind = event.get("type", event.get("event_type", "")) if isinstance(event, Mapping) else getattr(event, "event_type", "")
                if kind != "verification.gate":
                    continue
                payload = event.get("payload", event) if isinstance(event, Mapping) else getattr(event, "payload", {})
                if payload.get("decision") in {"allow", "allow_with_warnings"}:
                    allowed = True
            if not allowed:
                timing = (
                    " after current attempt start"
                    if attempt_window_position is not None and attempt_window_position != state_entry_position
                    else (" after current state entry" if state_entry_position is not None else "")
                )
                failures.append(f"verifier-gate-allow (no allowing Gate decision{timing})")
        elif invariant == "required-verifiers-pass":
            required = context.get("required_verifiers")
            if not isinstance(required, Iterable) or isinstance(required, (str, bytes, Mapping)):
                failures.append("required-verifiers-pass (required_verifiers missing)")
                continue
            required_refs = set()
            for item in required:
                if isinstance(item, Mapping):
                    identifier = item.get("id", item.get("verifier_id"))
                    version = item.get("version")
                    if identifier and version:
                        required_refs.add(f"{identifier}@{version}")
            if not required_refs:
                failures.append("required-verifiers-pass (required_verifiers empty)")
                continue
            passed_refs = set()
            gate_refs = set()
            allowing_gate = False
            for event in event_list:
                kind = event.get("type", event.get("event_type", "")) if isinstance(event, Mapping) else getattr(event, "event_type", "")
                payload = event.get("payload", {}) if isinstance(event, Mapping) else getattr(event, "payload", {})
                if not isinstance(payload, Mapping):
                    payload = {}
                if kind == "verification.result":
                    ref = f"{payload.get('verifier_id')}@{payload.get('verifier_version')}"
                    if payload.get("execution_status") == "completed" and payload.get("verdict") == "pass":
                        passed_refs.add(ref)
                elif kind == "verification.gate":
                    if payload.get("decision") in {"allow", "allow_with_warnings"}:
                        allowing_gate = True
                    gate_refs.update(str(item) for item in payload.get("result_refs", ()))
            missing = sorted(required_refs - passed_refs)
            if missing:
                failures.append("required-verifiers-pass (missing passing results: " + ", ".join(missing) + ")")
            elif not allowing_gate or not required_refs.issubset(gate_refs):
                failures.append("required-verifiers-pass (allowing Gate does not cover all required verifiers)")
    return tuple(failures)


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
    aliases: tuple[str, ...] = ()
    classification: str = "domain"
    tags: tuple[str, ...] = ()
    mode: str = "human"

    def __post_init__(self) -> None:
        try:
            validate_state_id(self.id)
        except ValueError as exc:
            raise StateDefinitionError(f"canonical state ID required: {self.id!r}") from exc
        if not self.version:
            raise StateDefinitionError("state version cannot be empty")
        if self.mode not in STATE_MODES:
            raise StateDefinitionError(f"unsupported state mode: {self.mode}")
        if self.id in self.aliases or len(set(self.aliases)) != len(self.aliases):
            raise StateDefinitionError("state aliases must be unique and differ from the canonical ID")
        for reference in (*self.entry_conditions, *self.transitions):
            if reference == "*":
                continue
            try:
                validate_state_id(reference)
            except ValueError as exc:
                raise StateDefinitionError(
                    f"canonical state graph reference required: {reference!r}"
                ) from exc

    @classmethod
    def from_markdown(cls, path: str | Path) -> "StateDefinition":
        target = Path(path)
        if target.name != "STATE.md" or not target.is_file():
            raise StateDefinitionError(f"state definition does not exist: {target}")
        metadata, instructions = _frontmatter(target.read_text(encoding="utf-8"))
        state_id = metadata.get("id")
        if not state_id:
            raise StateDefinitionError(f"state definition missing id: {target}")
        known = {"id", "version", "description", "kind", "entry", "entry_conditions", "invariants", "transitions", "next_states", "entrypoint", "aliases", "mode"}
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
            aliases=parse_state_aliases(metadata.get("aliases")),
            mode=str(metadata.get("mode", "rule" if metadata.get("entrypoint") else "human")),
        )

    @classmethod
    def from_indexed_markdown(cls, path: str | Path, entry: Mapping[str, Any]) -> "StateDefinition":
        target = Path(path)
        if target.name != "STATE.md" or not target.is_file():
            raise StateDefinitionError(f"state definition does not exist: {target}")
        metadata, instructions = _frontmatter(target.read_text(encoding="utf-8"))
        known = {"description", "entry", "entry_conditions", "invariants", "transitions", "next_states", "entrypoint", "mode"}
        extra = {key: value for key, value in metadata.items() if key not in known}
        entrypoint = resolve_entrypoint(
            target.parent,
            entry.get("entrypoint") or metadata.get("entrypoint"),
            error_type=StateDefinitionError,
            label="state",
        )
        return cls(
            id=str(entry.get("id", "")),
            version=str(entry.get("version", "")),
            description=str(metadata.get("description", entry.get("description", ""))),
            kind=str(entry.get("kind", "system")),
            entry_conditions=_as_tuple(metadata.get("entry_conditions", metadata.get("entry"))),
            invariants=_as_tuple(metadata.get("invariants")),
            transitions=_as_tuple(metadata.get("transitions", metadata.get("next_states"))),
            entrypoint=entrypoint,
            instructions=instructions,
            source=str(target),
            metadata={**extra, "index": dict(entry)},
            aliases=parse_state_aliases(entry.get("aliases")),
            classification=str(entry.get("classification", "domain")),
            tags=_as_tuple(entry.get("tags")),
            mode=str(entry.get("mode", metadata.get("mode", "rule" if entrypoint else "human"))),
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
            "aliases": list(self.aliases),
            "classification": self.classification,
            "tags": list(self.tags),
            "mode": self.mode,
        }

    def contract_pack(self) -> ContractPack:
        """Return the common execution descriptor without changing State semantics."""
        if not self.source:
            raise StateDefinitionError(f"state {self.id} has no source path")
        index = self.metadata.get("index")
        entry = dict(index) if isinstance(index, Mapping) else {
            "id": self.id,
            "version": self.version,
            "contract": "STATE.md",
            "entrypoint": self.entrypoint,
            "mode": self.mode,
            "assurance_tier": "deterministic" if self.entrypoint else "human",
            "aliases": list(self.aliases),
        }
        return ContractPack.from_directory(
            Path(self.source).parent,
            package_kind="state",
            contract_name="STATE.md",
            entry=entry,
        )


class FilesystemStateRegistry:
    """Discover ``STATE.md`` definitions below a filesystem root."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self._states: dict[str, StateDefinition] = {}
        self._aliases: dict[str, str] = {}
        self.refresh()

    def refresh(self) -> None:
        self._states.clear()
        self._aliases.clear()
        if not self.root.is_dir():
            return
        indexed = load_pack_entries(
            self.root,
            package_kind="state",
            contract_name="STATE.md",
            error_type=StateDefinitionError,
            recursive_without_index=True,
        )
        for path, entry in indexed:
            definition = StateDefinition.from_indexed_markdown(path, entry) if entry else StateDefinition.from_markdown(path)
            if definition.id in self._states:
                raise StateDefinitionError(f"duplicate state id: {definition.id}")
            self._states[definition.id] = definition
            for alias in definition.aliases:
                if alias in self._states or alias in self._aliases:
                    raise StateDefinitionError(f"duplicate state alias: {alias}")
                self._aliases[alias] = definition.id
        collisions = set(self._aliases) & set(self._states)
        if collisions:
            raise StateDefinitionError(f"state aliases collide with canonical IDs: {', '.join(sorted(collisions))}")

    def definitions(self, *, kind: str | None = None) -> tuple[StateDefinition, ...]:
        values = self._states.values()
        if kind:
            values = (item for item in values if item.kind == kind)
        return tuple(sorted(values, key=lambda item: item.id))

    def resolve(self, state_id: str) -> StateDefinition:
        state_id = self._aliases.get(state_id, state_id)
        try:
            return self._states[state_id]
        except KeyError as exc:
            raise StateDefinitionError(f"unknown state: {state_id}") from exc


class CombinedStateRegistry:
    """A read-only union of system and Skill-owned state directories."""

    def __init__(self, *registries: FilesystemStateRegistry):
        self.registries = registries
        self._states: dict[str, StateDefinition] = {}
        self._aliases: dict[str, str] = {}
        for registry in registries:
            for definition in registry.definitions():
                if definition.id in self._states:
                    raise StateDefinitionError(f"duplicate state id: {definition.id}")
                self._states[definition.id] = definition
                for alias in definition.aliases:
                    if alias in self._states or alias in self._aliases:
                        raise StateDefinitionError(f"duplicate state alias: {alias}")
                    self._aliases[alias] = definition.id
        collisions = set(self._aliases) & set(self._states)
        if collisions:
            raise StateDefinitionError(f"state aliases collide with canonical IDs: {', '.join(sorted(collisions))}")

    def definitions(self, *, kind: str | None = None) -> tuple[StateDefinition, ...]:
        values = self._states.values()
        if kind:
            values = (item for item in values if item.kind == kind)
        return tuple(sorted(values, key=lambda item: item.id))

    def resolve(self, state_id: str) -> StateDefinition:
        state_id = self._aliases.get(state_id, state_id)
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
    verifiers: tuple[Mapping[str, Any], ...] = ()
    identity_policy: str | None = None
    skill_id: str | None = None
    skill_version: str | None = None

    @classmethod
    def from_skill_root(cls, skill_root: str | Path) -> "SkillStateDeclaration":
        root = Path(skill_root).expanduser().resolve()
        # New Skills keep runtime declarations beside their other configuration.
        # The JSON file remains a read-only compatibility format for older Skills.
        source = root / "config.yaml"
        raw: Mapping[str, Any] | None = None
        loaded_config: Mapping[str, Any] = {}
        if source.is_file():
            try:
                loaded = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
            except (OSError, yaml.YAMLError) as exc:
                raise StateDefinitionError(f"invalid Skill config: {exc}") from exc
            if isinstance(loaded, Mapping) and isinstance(loaded.get("runtime"), Mapping):
                raw = loaded["runtime"]
                loaded_config = loaded
        if raw is None:
            source = root / "state-machine.json"
            try:
                raw = json.loads(source.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise StateDefinitionError(f"Skill state declaration does not exist: {source}") from exc
            except json.JSONDecodeError as exc:
                raise StateDefinitionError(f"invalid Skill state declaration: {exc.msg}") from exc
            if not isinstance(raw, Mapping) or raw.get("protocol") != SKILL_STATE_DECLARATION_VERSION:
                raise StateDefinitionError(f"Skill state declaration must use {SKILL_STATE_DECLARATION_VERSION}")
        identity_policy = raw.get("identity_policy")
        if identity_policy is not None:
            from .identity import STRICT_IDENTITY_POLICY

            if identity_policy != STRICT_IDENTITY_POLICY:
                raise StateDefinitionError(
                    f"runtime.identity_policy must be {STRICT_IDENTITY_POLICY!r} when present"
                )
        initial = raw.get("initial_state", "bensz.workspace.ready")
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
        registry = build_state_registry(*resolved_roots)
        try:
            canonical_initial = registry.resolve(str(initial)).id
            canonical_names = tuple(registry.resolve(item).id for item in names)
        except StateDefinitionError as exc:
            raise StateDefinitionError(
                f"Skill state declaration references an unknown state: {exc}"
            ) from exc
        raw_verifiers = raw.get("verifiers", ())
        if raw_verifiers is None:
            raw_verifiers = ()
        if not isinstance(raw_verifiers, Iterable) or isinstance(raw_verifiers, (str, bytes, Mapping)):
            raise StateDefinitionError("Skill verifier declaration must be a list")
        verifier_items = []
        if raw_verifiers:
            try:
                from .verifiers import SkillVerifierDeclaration

                verifier_items = list(SkillVerifierDeclaration.from_skill_root(root).verifier_requirements())
            except (ImportError, KeyError, ValueError) as exc:
                raise StateDefinitionError(f"invalid verifier requirements: {exc}") from exc
        runtime_kernel = raw.get("kernel")
        if isinstance(runtime_kernel, Mapping):
            from . import __version__ as kernel_version
            try:
                validate_kernel_runtime_declaration(runtime_kernel, running_version=kernel_version)
            except ValueError as exc:
                raise StateDefinitionError(str(exc)) from exc
        skill_info = loaded_config.get("skill_info", {})
        if not isinstance(skill_info, Mapping):
            raise StateDefinitionError("skill_info must be a mapping when present")
        skill_id = str(skill_info.get("name") or root.name)
        raw_skill_version = skill_info.get("version")
        skill_version = str(raw_skill_version) if raw_skill_version is not None else None
        return cls(
            root,
            canonical_initial,
            tuple(resolved_roots),
            canonical_names,
            source,
            tuple(verifier_items),
            str(identity_policy) if identity_policy is not None else None,
            skill_id,
            skill_version,
        )

    def registry(self) -> "CombinedStateRegistry":
        registry = build_state_registry(*self.state_roots)
        declared = set(self.states) | {self.initial_state}
        unknown = set()
        for state_id in declared:
            try:
                registry.resolve(state_id)
            except StateDefinitionError:
                unknown.add(state_id)
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
            "verifiers": [dict(item) for item in self.verifiers],
            "identity_policy": self.identity_policy,
            "skill_id": self.skill_id,
            "skill_version": self.skill_version,
        }

    def verifier_requirements(self) -> tuple[Mapping[str, Any], ...]:
        """Return the immutable runtime verifier selection for adapters."""
        return tuple(dict(item) for item in self.verifiers)


@dataclass(frozen=True)
class StateExecutionResult:
    """Normalized result returned by an optional state helper script."""

    state_id: str
    execution_status: str
    verdict: str
    summary: str = ""
    facts: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()
    contract_hash: str | None = None
    plan_hash: str | None = None
    execution_plan: Mapping[str, Any] = field(default_factory=dict)
    component_results: tuple[Mapping[str, Any], ...] = ()
    handoffs: tuple[Mapping[str, Any], ...] = ()
    run_id: str | None = None
    attempt_id: str | None = None
    state_visit_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": META_STATE_PROTOCOL_VERSION,
            "state_id": self.state_id,
            "execution_status": self.execution_status,
            "verdict": self.verdict,
            "summary": self.summary,
            "facts": dict(self.facts),
            "evidence_refs": list(self.evidence_refs),
            "contract_hash": self.contract_hash,
            "plan_hash": self.plan_hash,
            "execution_plan": dict(self.execution_plan),
            "component_results": [dict(item) for item in self.component_results],
            "handoffs": [dict(item) for item in self.handoffs],
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "state_visit_id": self.state_visit_id,
        }


class StateContractAdapter:
    """Interpret a common execution report as State entry/exit evidence."""

    def adapt(self, state_id: str, report: ContractExecutionReport) -> StateExecutionResult:
        if report.package_kind != "state":
            # A shared test/example may deliberately reuse one execution report
            # across both adapters.  The adapter owns the semantic target ID and
            # does not mutate the common report.
            package_kind = report.package_kind
        else:
            package_kind = "state"
        if report.decision in {"completed", "completed_with_warnings"}:
            status, verdict = "completed", "pass"
        elif report.decision == "reject":
            status, verdict = "completed", "fail"
        elif report.decision == "manual_review":
            status, verdict = "unchecked", "uncertain"
        else:
            status, verdict = "pending", "unchecked"
        refs = tuple(dict.fromkeys(ref for item in report.results for ref in item.evidence_refs))
        return StateExecutionResult(
            state_id=state_id,
            execution_status=status,
            verdict=verdict,
            summary=f"Contract execution {report.decision} ({package_kind} adapter).",
            facts={"decision": report.decision, "unresolved": list(report.unresolved)},
            evidence_refs=refs,
            contract_hash=report.contract_hash,
            plan_hash=report.plan_hash,
            execution_plan=dict(report.execution_plan),
            component_results=tuple(item.to_dict() for item in report.results),
            handoffs=tuple(item.to_dict() for item in report.handoffs),
            run_id=report.run_id,
            attempt_id=report.attempt_id,
            state_visit_id=report.state_visit_id,
        )


def execute_state(definition: StateDefinition, request: Mapping[str, Any], *, timeout: int = 10) -> StateExecutionResult:
    """Run an optional state helper using the same JSON-stdio boundary as verifiers."""
    index = definition.metadata.get("index")
    if isinstance(index, Mapping) and "components" in index:
        if not definition.source:
            raise StateExecutionError(f"state {definition.id} has no source path")
        try:
            pack = definition.contract_pack()
            raw_submissions = request.get("component_results", request.get("submissions", ()))
            if not isinstance(raw_submissions, (list, tuple)):
                raise StateExecutionError("state component results must be a list")
            submissions = raw_submissions
            context = request.get("context", {})
            run_id = str(context.get("run_id", request.get("run_id", "run"))) if isinstance(context, Mapping) else "run"
            attempt_id = str(context.get("attempt_id", request.get("attempt_id", "default"))) if isinstance(context, Mapping) else "default"
            state_visit_id = context.get("state_visit_id", request.get("state_visit_id")) if isinstance(context, Mapping) else None
            report = ContractPackExecutor().execute(
                pack,
                request=request,
                submissions=submissions,
                run_id=run_id,
                attempt_id=attempt_id,
                state_visit_id=str(state_visit_id) if state_visit_id is not None else None,
                timeout=timeout,
            )
            return StateContractAdapter().adapt(definition.id, report)
        except ValueError as exc:
            raise StateExecutionError(str(exc)) from exc
    if not definition.entrypoint:
        return StateExecutionResult(definition.id, "not_applicable", "unchecked", "This state has no helper script.")
    if not definition.source:
        raise StateExecutionError(f"state {definition.id} has no source path")
    state_root = Path(definition.source).parent.resolve()
    entrypoint = resolve_entrypoint(
        state_root,
        definition.entrypoint,
        error_type=StateExecutionError,
        label="state",
    )
    if entrypoint is None:  # guarded above, keeps the executor contract explicit
        return StateExecutionResult(definition.id, "not_applicable", "unchecked", "This state has no helper script.")
    payload = {"protocol": META_STATE_PROTOCOL_VERSION, "state": definition.to_dict(), "request": dict(request)}
    execution = run_stdio(state_root, entrypoint, payload, timeout=timeout)
    if execution.status == "timed_out":
        return StateExecutionResult(definition.id, "timed_out", "timed_out", execution.detail)
    if execution.status in {"error", "denied", "input_too_large", "output_too_large", "invalid_input"}:
        return StateExecutionResult(definition.id, "error", "error", execution.detail)
    if execution.status == "invalid_json":
        raise StateExecutionError(execution.detail)
    raw = execution.value
    if not isinstance(raw, Mapping) or raw.get("verdict") not in _SCRIPT_VERDICTS:
        raise StateExecutionError("state helper result requires a supported verdict")
    execution_status = str(raw.get("execution_status", "completed"))
    if execution_status != "completed":
        raise StateExecutionError("state helper execution_status must be completed")
    facts = raw.get("facts", {})
    refs = raw.get("evidence_refs", [])
    if not isinstance(facts, Mapping) or not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
        raise StateExecutionError("state helper facts must be an object and evidence_refs a string list")
    return StateExecutionResult(definition.id, execution_status, str(raw["verdict"]), str(raw.get("summary", "")), dict(facts), tuple(refs))


class StateMachine:
    """Small in-memory evaluator for a registry-defined meta-state graph.

    Persistence remains the responsibility of a Skill's event log.  This class
    only validates a requested transition against the ``STATE.md`` contract.
    """

    def __init__(self, registry: FilesystemStateRegistry | CombinedStateRegistry, initial: str = "bensz.workspace.ready"):
        self.registry = registry
        self.current = registry.resolve(initial).id

    def can_transition(self, target: str) -> bool:
        source = self.registry.resolve(self.current)
        destination = self.registry.resolve(target)
        explicit = {
            self.registry.resolve(item).id
            for item in source.transitions
            if item != "*"
        }
        entry_conditions = {
            self.registry.resolve(item).id
            for item in destination.entry_conditions
            if item != "*"
        }
        return destination.id in explicit or ("*" in source.transitions and self.current in entry_conditions)

    def transition(self, target: str, *, events: Iterable[Any] = (), context: Mapping[str, Any] | None = None) -> StateDefinition:
        if not self.can_transition(target):
            raise StateTransitionError(f"illegal meta-state transition {self.current!r} -> {target!r}")
        invariant_failures = check_state_invariants(self.registry.resolve(self.current), events, context=context)
        if invariant_failures:
            raise StateTransitionError("state invariant failed: " + "; ".join(invariant_failures))
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
