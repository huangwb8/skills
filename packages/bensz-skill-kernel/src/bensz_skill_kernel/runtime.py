"""Append-only events, deterministic projection and lifecycle guards.

The module intentionally has no third-party runtime dependencies.  Event logs are
newline-delimited JSON and are the source of truth; ``state.json`` is disposable.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

VALID_STATES = frozenset(
    {"planned", "active", "waiting", "checking", "delivering", "completed", "failed", "cancelled"}
)
TERMINAL_STATES = frozenset({"completed", "failed", "cancelled"})
ALLOWED_TRANSITIONS = {
    "planned": frozenset({"active", "waiting", "cancelled"}),
    "active": frozenset({"active", "waiting", "checking", "cancelled", "failed"}),
    "waiting": frozenset({"active", "cancelled", "failed"}),
    "checking": frozenset({"active", "waiting", "delivering", "failed", "cancelled"}),
    "delivering": frozenset({"active", "waiting", "checking", "completed", "failed", "cancelled"}),
    "completed": frozenset(),
    "failed": frozenset(),
    "cancelled": frozenset(),
}
WAIT_REASONS = frozenset(
    {"input", "authorization", "approval", "choice", "dependency", "quota", "children", "schedule", "operator_pause"}
)


class KernelError(Exception):
    """Base error for deterministic kernel failures."""


class IntegrityError(KernelError):
    """The event stream is malformed, out of order, or hash-chain broken."""


class InvalidTransition(KernelError):
    """A requested state transition is not in the lifecycle contract."""


class CompletionError(InvalidTransition):
    """Completion was requested without the required evidence."""


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class EventEnvelope:
    seq: int
    event_id: str
    scope: str = "task"
    actor: str = "runtime"
    attempt_id: str = "default"
    event_type: str = ""
    summary: str = ""
    path: str | None = None
    evidence_refs: tuple[str, ...] = ()
    idempotency_key: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    prev_hash: str = ""
    event_hash: str = ""
    occurred_at: str = ""

    @property
    def type(self) -> str:
        return self.event_type

    def unsigned(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "event_id": self.event_id,
            "scope": self.scope,
            "actor": self.actor,
            "attempt_id": self.attempt_id,
            "type": self.event_type,
            "summary": self.summary,
            "path": self.path,
            "evidence_refs": list(self.evidence_refs),
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "occurred_at": self.occurred_at,
        }

    def with_hash(self) -> "EventEnvelope":
        digest = hashlib.sha256(_canonical(self.unsigned())).hexdigest()
        return EventEnvelope(**{**self.__dict__, "event_hash": digest})

    def to_dict(self) -> dict[str, Any]:
        result = self.unsigned()
        result["event_hash"] = self.event_hash
        return result

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "EventEnvelope":
        try:
            return cls(
                seq=int(raw["seq"]),
                event_id=str(raw["event_id"]),
                scope=str(raw.get("scope", "task")),
                actor=str(raw.get("actor", "runtime")),
                attempt_id=str(raw.get("attempt_id", "default")),
                event_type=str(raw.get("type", raw.get("event_type", ""))),
                summary=str(raw.get("summary", "")),
                path=raw.get("path"),
                evidence_refs=tuple(raw.get("evidence_refs", ())),
                idempotency_key=raw.get("idempotency_key"),
                payload=dict(raw.get("payload", {})),
                prev_hash=str(raw.get("prev_hash", "")),
                event_hash=str(raw.get("event_hash", "")),
                occurred_at=str(raw.get("occurred_at", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IntegrityError(f"invalid event envelope: {exc}") from exc


def _event_state(event: EventEnvelope) -> tuple[str | None, dict[str, Any]]:
    """Return an optional target state and normalized payload for an event."""
    payload = dict(event.payload)
    if event.event_type in {"state.transition", "transition", "status.changed"}:
        return payload.get("to", payload.get("state")), payload
    aliases = {
        "task.created": "planned", "task.accepted": "planned", "task.started": "active",
        "task.waiting": "waiting", "validation.started": "checking", "delivery.started": "delivering",
        "task.completed": "completed", "task.failed": "failed", "task.cancelled": "cancelled",
    }
    return aliases.get(event.event_type), payload


def reduce_events(events: Iterable[EventEnvelope], *, initial: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Deterministically replay events into a JSON-serializable projection."""
    projection: dict[str, Any] = {
        "current_state": None,
        "phase": None,
        "outcome": None,
        "wait_reason": None,
        "artifacts": {},
        "validations": [],
        "verifications": [],
        "gate_decisions": [],
        "delivery_report": None,
        "evidence_refs": [],
        "last_seq": 0,
        "last_event_id": None,
        "event_count": 0,
    }
    if initial:
        projection.update(dict(initial))
    for event in events:
        target, payload = _event_state(event)
        current = projection["current_state"]
        if target is not None:
            if target not in VALID_STATES:
                raise InvalidTransition(f"unknown state: {target}")
            if current is not None and target not in ALLOWED_TRANSITIONS[current]:
                raise InvalidTransition(f"illegal transition {current!r} -> {target!r}")
            projection["current_state"] = target
            if target != "waiting":
                projection["wait_reason"] = None
            if target in TERMINAL_STATES:
                projection["outcome"] = payload.get(
                    "outcome",
                    {"completed": "success", "failed": "failed", "cancelled": "cancelled"}.get(target, projection.get("outcome")),
                )
        if "phase" in payload:
            projection["phase"] = payload["phase"]
        if target == "waiting":
            reason = payload.get("wait_reason")
            if reason is not None and reason not in WAIT_REASONS:
                raise InvalidTransition(f"unknown wait_reason: {reason}")
            projection["wait_reason"] = reason
        if event.event_type == "artifact.registered":
            artifact_id = payload.get("artifact_id") or event.path
            if artifact_id:
                projection["artifacts"][artifact_id] = {**payload, "artifact_id": artifact_id}
        elif event.event_type in {"validation.completed", "validation.recorded"}:
            projection["validations"].append(payload)
        elif event.event_type == "verification.result":
            projection["verifications"].append(payload)
        elif event.event_type == "verification.gate":
            projection["gate_decisions"].append(payload)
        elif event.event_type in {"delivery.reported", "delivery.completed"}:
            projection["delivery_report"] = payload.get("report") or payload.get("path") or event.path or payload
        projection["evidence_refs"] = list(dict.fromkeys([*projection["evidence_refs"], *event.evidence_refs, *payload.get("evidence_refs", [])]))
        projection["last_seq"] = event.seq
        projection["last_event_id"] = event.event_id
        projection["event_count"] += 1
    return projection


def _guard_completion(projection: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> None:
    contract = contract or {}
    artifacts = projection.get("artifacts", {})
    required = contract.get("required_artifacts")
    if required is None:
        required = [k for k, value in artifacts.items() if value.get("required")]
    missing = [item for item in required if item not in artifacts]
    if missing:
        raise CompletionError(f"required artifacts missing: {', '.join(map(str, missing))}")
    validations = projection.get("validations", [])
    if not validations or any(v.get("verdict") not in {"pass", "passed", "success"} for v in validations[-1:]):
        raise CompletionError("a passing validation evidence is required")
    if not projection.get("delivery_report"):
        raise CompletionError("a delivery report is required")


class EventLog:
    """Append-only NDJSON event log with projection and rebuild helpers."""

    def __init__(self, path: str | os.PathLike[str], *, contract: Mapping[str, Any] | None = None):
        self.path = Path(path)
        self.contract = dict(contract or {})

    def read(self) -> list[EventEnvelope]:
        if not self.path.exists():
            return []
        events: list[EventEnvelope] = []
        previous = ""
        expected_seq = 1
        for line_no, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                event = EventEnvelope.from_dict(json.loads(line))
            except json.JSONDecodeError as exc:
                raise IntegrityError(f"invalid JSON at line {line_no}: {exc}") from exc
            if event.seq != expected_seq or event.prev_hash != previous or not event.event_hash:
                raise IntegrityError(f"sequence/hash link broken at line {line_no}")
            if event.with_hash().event_hash != event.event_hash:
                raise IntegrityError(f"event hash mismatch at line {line_no}")
            events.append(event)
            expected_seq += 1
            previous = event.event_hash
        return events

    def append(self, event_type: str, *, payload: Mapping[str, Any] | None = None, summary: str = "", scope: str = "task", actor: str = "runtime", attempt_id: str = "default", path: str | None = None, evidence_refs: Iterable[str] = (), idempotency_key: str | None = None) -> EventEnvelope:
        events = self.read()
        if idempotency_key:
            for event in events:
                if event.idempotency_key == idempotency_key:
                    return event
        data = dict(payload or {})
        event = EventEnvelope(seq=len(events) + 1, event_id=str(uuid.uuid4()), scope=scope, actor=actor, attempt_id=attempt_id, event_type=event_type, summary=summary, path=path, evidence_refs=tuple(evidence_refs), idempotency_key=idempotency_key, payload=data, prev_hash=events[-1].event_hash if events else "", occurred_at=_utc_now()).with_hash()
        target, _ = _event_state(event)
        current = reduce_events(events)["current_state"]
        if target == "completed":
            # Report missing evidence explicitly even when the caller attempted
            # to skip the delivering phase; this is safer and easier to act on.
            _guard_completion(reduce_events(events), self.contract)
            if current != "delivering":
                raise InvalidTransition(f"illegal transition {current!r} -> 'completed'")
        elif target is not None and current is not None and target not in ALLOWED_TRANSITIONS[current]:
            raise InvalidTransition(f"illegal transition {current!r} -> {target!r}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def append_event(self, event: EventEnvelope | Mapping[str, Any] | str, **kwargs: Any) -> EventEnvelope:
        """Compatibility façade accepting an envelope, mapping, or event type."""
        if isinstance(event, EventEnvelope):
            kwargs = {
                "payload": event.payload,
                "summary": event.summary,
                "scope": event.scope,
                "actor": event.actor,
                "attempt_id": event.attempt_id,
                "path": event.path,
                "evidence_refs": event.evidence_refs,
                "idempotency_key": event.idempotency_key,
                **kwargs,
            }
            return self.append(event.event_type, **kwargs)
        if isinstance(event, Mapping):
            # A mapping may be a complete persisted envelope or a convenient
            # append request containing only ``type`` and ``payload``.
            if "seq" in event:
                parsed = EventEnvelope.from_dict(event)
                return self.append_event(parsed, **kwargs)
            data = dict(event)
            event_type = data.pop("type", data.pop("event_type", None))
            if not event_type:
                raise ValueError("append event mapping requires type")
            payload = data.pop("payload", {})
            return self.append(str(event_type), payload=payload, **data, **kwargs)
        return self.append(event, **kwargs)

    def projection(self) -> dict[str, Any]:
        return reduce_events(self.read())

    def transition(
        self,
        to: str,
        *,
        scope: str = "task",
        actor: str = "runtime",
        attempt_id: str = "default",
        idempotency_key: str | None = None,
        **payload: Any,
    ) -> EventEnvelope:
        """Append a state transition using the canonical event type."""
        payload["to"] = to
        return self.append(
            "state.transition",
            payload=payload,
            scope=scope,
            actor=actor,
            attempt_id=attempt_id,
            idempotency_key=idempotency_key,
        )

    def record_artifact(self, artifact_id: str, *, required: bool = False, **metadata: Any) -> EventEnvelope:
        return self.append("artifact.registered", payload={"artifact_id": artifact_id, "required": required, **metadata})

    def record_validation(self, verdict: str, *, evidence_refs: Iterable[str] = (), **metadata: Any) -> EventEnvelope:
        return self.append("validation.completed", payload={"verdict": verdict, "evidence_refs": list(evidence_refs), **metadata}, evidence_refs=evidence_refs)

    def record_verification(
        self,
        result: Mapping[str, Any],
        gate: Mapping[str, Any] | None = None,
        *,
        scope: str = "task",
        actor: str = "runtime",
        attempt_id: str = "default",
        idempotency_key: str | None = None,
    ) -> tuple[EventEnvelope, EventEnvelope | None]:
        """Append a replayable verifier result and optional gate decision."""
        refs = tuple(result.get("evidence_refs", ()))
        verification = self.append(
            "verification.result",
            payload=dict(result),
            evidence_refs=refs,
            scope=scope,
            actor=actor,
            attempt_id=attempt_id,
            idempotency_key=idempotency_key,
        )
        gate_event = None
        if gate is not None:
            gate_event = self.append(
                "verification.gate",
                payload=dict(gate),
                evidence_refs=refs,
                scope=scope,
                actor=actor,
                attempt_id=attempt_id,
                idempotency_key=f"{idempotency_key}:gate" if idempotency_key else None,
            )
        return verification, gate_event

    def record_delivery(self, report: str, **metadata: Any) -> EventEnvelope:
        return self.append("delivery.reported", payload={"report": report, **metadata}, path=report)

    def rebuild(self, state_path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
        projection = self.projection()
        target = Path(state_path) if state_path else self.path.parent / "state.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, target)
        return projection


def main() -> int:
    from .cli import main as cli_main

    return cli_main()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
