"""Append-only events, deterministic projection and lifecycle guards.

The module intentionally has no third-party runtime dependencies.  Event logs are
newline-delimited JSON and are the source of truth; ``state.json`` is disposable.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .verifiers import GateDecision, VerificationResult, apply_gate

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
EFFECT_STATUSES = frozenset(
    {"none", "prepared", "authorized", "applied", "reconciled", "unknown", "conflicted", "compensated"}
)


class KernelError(Exception):
    """Base error for deterministic kernel failures."""


class IntegrityError(KernelError):
    """The event stream is malformed, out of order, or hash-chain broken."""


class InvalidTransition(KernelError):
    """A requested state transition is not in the lifecycle contract."""


class CompletionError(InvalidTransition):
    """Completion was requested without the required evidence."""


class IdempotencyConflict(KernelError):
    """An idempotency key was reused for a different request intent."""


class AuthorizationError(KernelError):
    """A side-effect event lacks an explicit authorization record."""


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _request_hash(event_type: str, payload: Mapping[str, Any], summary: str, scope: str, actor: str, attempt_id: str, path: str | None, evidence_refs: Iterable[str], run_id: str | None = None, authorization: Mapping[str, Any] | None = None, snapshot: Mapping[str, Any] | None = None) -> str:
    intent = {"type": event_type, "payload": dict(payload), "summary": summary, "scope": scope, "actor": actor, "attempt_id": attempt_id, "path": path, "evidence_refs": list(evidence_refs), "run_id": run_id, "authorization": dict(authorization or {}), "snapshot": dict(snapshot or {})}
    return hashlib.sha256(_canonical(intent)).hexdigest()


def _redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if any(token in str(key).lower() for token in ("token", "secret", "password", "cookie", "api_key", "credential")):
            result[str(key)] = "[REDACTED]"
        elif isinstance(item, Mapping):
            result[str(key)] = _redact_mapping(item)
        elif isinstance(item, (list, tuple)):
            result[str(key)] = [_redact_mapping(part) if isinstance(part, Mapping) else part for part in item]
        else:
            result[str(key)] = item
    return result


_SENSITIVE_KEYS = ("token", "secret", "password", "cookie", "api_key", "credential")
_RAW_KEYS = {"input", "output", "prompt", "content", "response", "stdout", "stderr"}
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_KERNEL_GATE_TOKEN = object()
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _component_bound_gate(
    result: Mapping[str, Any],
    *,
    run_id: str | None,
    attempt_id: str,
) -> GateDecision | None:
    """Recompute a v2 Gate from bound component evidence.

    Legacy v1 results return ``None`` and continue through the original
    verifier-level gate path.  A malformed v2 result is always rejected; the
    caller's advisory Gate can never turn it into an allow decision.
    """
    if result.get("protocol") != "bensz-verification-v2":
        return None
    verifier_id = str(result.get("verifier_id", ""))
    verifier_version = str(result.get("verifier_version", ""))
    result_ref = (f"{verifier_id}@{verifier_version}",) if verifier_id and verifier_version else ()
    contract_hash = result.get("contract_hash")
    plan_hash = result.get("plan_hash")
    execution_plan = result.get("execution_plan")
    components = result.get("component_results")

    def reject(reason: str, unresolved: Iterable[str] = ("component_binding",)) -> GateDecision:
        return GateDecision("reject", reason, result_ref, tuple(str(item) for item in unresolved))

    if not _SHA256_RE.fullmatch(str(contract_hash)) or not _SHA256_RE.fullmatch(str(plan_hash)):
        return reject("invalid Contract Pack hash binding")
    if result.get("run_id") != run_id or result.get("attempt_id") != attempt_id:
        return reject("verification result run identity mismatch")
    if not isinstance(execution_plan, Mapping):
        return reject("v2 verification requires an execution plan")
    plan_components = execution_plan.get("components")
    if (
        execution_plan.get("protocol") != "bensz-contract-execution-v1"
        or execution_plan.get("package_kind") != "verifier"
        or execution_plan.get("pack_id") != verifier_id
        or execution_plan.get("version") != verifier_version
        or execution_plan.get("contract_hash") != contract_hash
        or execution_plan.get("plan_hash") != plan_hash
        or not isinstance(plan_components, list)
        or not plan_components
    ):
        return reject("execution plan binding mismatch")
    plan_core = {
        "protocol": execution_plan.get("protocol"),
        "package_kind": execution_plan.get("package_kind"),
        "pack_id": execution_plan.get("pack_id"),
        "version": execution_plan.get("version"),
        "contract_hash": execution_plan.get("contract_hash"),
        "mode": execution_plan.get("mode"),
        "assurance_tier": execution_plan.get("assurance_tier"),
        "components": plan_components,
    }
    if "sha256:" + hashlib.sha256(_canonical(plan_core)).hexdigest() != plan_hash:
        return reject("execution plan hash mismatch")
    if not isinstance(components, list) or not components:
        return reject("v2 verification requires component results")
    plan_by_id: dict[str, Mapping[str, Any]] = {}
    for raw_plan in plan_components:
        if not isinstance(raw_plan, Mapping):
            return reject("execution plan component must be an object")
        component_id = str(raw_plan.get("id", ""))
        if not component_id or component_id in plan_by_id or not _SHA256_RE.fullmatch(str(raw_plan.get("component_hash", ""))):
            return reject("execution plan component identity is invalid")
        plan_by_id[component_id] = raw_plan
    seen: set[str] = set()
    aggregate_evidence_refs = result.get("evidence_refs", ())
    if not isinstance(aggregate_evidence_refs, (list, tuple)) or not all(isinstance(item, str) for item in aggregate_evidence_refs):
        return reject("aggregate evidence refs are invalid")
    known_evidence_refs = set(aggregate_evidence_refs)
    required_failures: list[str] = []
    required_uncertain: list[str] = []
    required_waiting: list[str] = []
    optional_failures: list[str] = []
    for raw in components:
        if not isinstance(raw, Mapping):
            return reject("component result must be an object")
        component_id = str(raw.get("component_id", ""))
        if not component_id or component_id in seen:
            return reject("component result identity is missing or duplicated")
        seen.add(component_id)
        declared = plan_by_id.get(component_id)
        if declared is None:
            return reject("component result is not declared by execution plan", (component_id,))
        if (
            raw.get("protocol") != "bensz-contract-component-result-v1"
            or raw.get("pack_id") != verifier_id
            or raw.get("pack_version") != verifier_version
            or raw.get("package_kind") != "verifier"
            or raw.get("contract_hash") != contract_hash
            or raw.get("plan_hash") != plan_hash
            or raw.get("run_id") != run_id
            or raw.get("attempt_id") != attempt_id
            or not _SHA256_RE.fullmatch(str(raw.get("component_hash", "")))
            or raw.get("component_hash") != declared.get("component_hash")
            or raw.get("component_type") != declared.get("type")
            or raw.get("required", True) != declared.get("required", True)
            or raw.get("assurance") != declared.get("assurance")
        ):
            return reject("component result binding mismatch", (component_id,))
        component_type = raw.get("component_type")
        if component_type not in {"script", "agent", "human"}:
            return reject("component executor type is invalid", (component_id,))
        status = raw.get("execution_status")
        verdict = raw.get("verdict")
        if status not in {"completed", "pending", "unchecked", "error", "timed_out", "skipped"} or verdict not in {"pass", "fail", "uncertain", "unchecked", "error", "timed_out", "skipped"}:
            return reject("component result status is invalid", (component_id,))
        if status != "completed" and verdict == "pass":
            return reject("non-completed component cannot pass", (component_id,))
        executor = raw.get("executor", {})
        if status == "completed":
            if not isinstance(executor, Mapping) or executor.get("type") != component_type or not executor.get("id"):
                return reject("completed component lacks bound executor identity", (component_id,))
            if component_type == "agent" and not executor.get("model"):
                return reject("agent component lacks model identity", (component_id,))
            if component_type == "human" and not executor.get("confirmed_at"):
                return reject("human component lacks confirmation timestamp", (component_id,))
            if component_type in {"agent", "human"} and not _SHA256_RE.fullmatch(str(raw.get("handoff_hash", ""))):
                return reject("external component lacks handoff binding", (component_id,))
        component_evidence_refs = raw.get("evidence_refs", ())
        if not isinstance(component_evidence_refs, (list, tuple)) or not all(isinstance(item, str) for item in component_evidence_refs):
            return reject("component evidence refs are invalid", (component_id,))
        if set(component_evidence_refs) - known_evidence_refs:
            return reject("component evidence is not bound to aggregate evidence", (component_id,))
        required = raw.get("required", True)
        if not isinstance(required, bool):
            return reject("component required flag must be boolean", (component_id,))
        if required and verdict == "fail":
            required_failures.append(component_id)
        elif required and verdict in {"uncertain", "error", "timed_out"}:
            required_uncertain.append(component_id)
        elif required and verdict in {"unchecked", "skipped"}:
            required_waiting.append(component_id)
        elif not required and verdict != "pass":
            optional_failures.append(component_id)
    missing_components = tuple(sorted(set(plan_by_id) - seen))
    if missing_components:
        return reject("execution plan components are missing", missing_components)
    if required_failures:
        decision = GateDecision("reject", "required component failure", result_ref, tuple(required_failures))
        expected_verdict = "fail"
    elif required_uncertain:
        unresolved = tuple(dict.fromkeys((*required_uncertain, *required_waiting)))
        decision = GateDecision("manual_review", "component incomplete or uncertain", result_ref, unresolved)
        expected_verdict = None
    elif required_waiting:
        decision = GateDecision("wait", "component result pending", result_ref, tuple(required_waiting))
        expected_verdict = "unchecked"
    elif optional_failures:
        decision = GateDecision("allow_with_warnings", "optional component did not pass", result_ref, tuple(optional_failures))
        expected_verdict = "pass"
    else:
        decision = GateDecision("allow", "all required components passed", result_ref)
        expected_verdict = "pass"
    if expected_verdict is not None and result.get("verdict") != expected_verdict:
        return reject("aggregate verdict conflicts with component results", tuple(seen))
    if decision.decision == "manual_review" and result.get("verdict") not in {"uncertain", "unchecked", "timed_out", "error"}:
        return reject("aggregate uncertainty conflicts with component results", tuple(required_uncertain))
    return decision


def _event_safe_value(value: Any, *, key: str | None = None, base_dir: Path | None = None) -> Any:
    """Return an audit-safe representation without leaking private evidence."""
    lowered = (key or "").lower()
    if any(token in lowered for token in _SENSITIVE_KEYS):
        return "[REDACTED]"
    if lowered in _RAW_KEYS:
        return None
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            child_key = str(raw_key)
            if child_key.lower() in _RAW_KEYS:
                result[f"{child_key}_hash"] = hashlib.sha256(_canonical({"value": raw_value})).hexdigest()
            else:
                result[child_key] = _event_safe_value(raw_value, key=child_key, base_dir=base_dir)
        return result
    if isinstance(value, (list, tuple)):
        return [_event_safe_value(item, key=key, base_dir=base_dir) for item in value]
    if isinstance(value, str):
        # Absolute paths are replaced by a stable locator, retaining audit
        # correlation without exposing a user's directory structure.
        if value.startswith(("/", "\\")) or (len(value) > 2 and value[1] == ":" and value[2] in "\\/"):
            if base_dir is not None:
                try:
                    resolved = Path(value).resolve()
                except OSError:
                    resolved = None
                if resolved is None:
                    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
                    return f"path#sha256:{digest}"
                for candidate_root in (base_dir, base_dir.parent):
                    try:
                        return str(resolved.relative_to(candidate_root.resolve()))
                    except (ValueError, OSError):
                        continue
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
            return f"path#sha256:{digest}"
        if lowered in {"error", "message", "uncertainty_reason"} and len(value) > 256:
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
            return f"text#sha256:{digest}"
    return value


def _sanitize_event_payload(value: Mapping[str, Any], *, base_dir: Path | None = None) -> dict[str, Any]:
    return dict(_event_safe_value(value, base_dir=base_dir))


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
    request_hash: str | None = None
    protocol: str = "bensz-event-v1"
    run_id: str | None = None
    authorization: dict[str, Any] = field(default_factory=dict)
    snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def type(self) -> str:
        return self.event_type

    def unsigned(self) -> dict[str, Any]:
        result = {
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
        if self.protocol:
            result["protocol"] = self.protocol
            if self.request_hash is not None:
                result["request_hash"] = self.request_hash
            if self.run_id is not None:
                result["run_id"] = self.run_id
            if self.authorization:
                result["authorization"] = self.authorization
            if self.snapshot:
                result["snapshot"] = self.snapshot
        return result

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
            if not isinstance(raw, Mapping):
                raise TypeError("event envelope must be an object")
            if raw.get("protocol", "bensz-event-v1") != "bensz-event-v1":
                raise ValueError("unsupported event protocol")
            refs = raw.get("evidence_refs", ())
            if not isinstance(refs, (list, tuple)) or not all(isinstance(item, str) for item in refs):
                raise TypeError("evidence_refs must be a string list")
            payload = raw.get("payload", {})
            if not isinstance(payload, Mapping):
                raise TypeError("payload must be an object")
            return cls(
                seq=int(raw["seq"]),
                event_id=str(raw["event_id"]),
                scope=str(raw.get("scope", "task")),
                actor=str(raw.get("actor", "runtime")),
                attempt_id=str(raw.get("attempt_id", "default")),
                event_type=str(raw.get("type", raw.get("event_type", ""))),
                summary=str(raw.get("summary", "")),
                path=raw.get("path"),
                evidence_refs=tuple(refs),
                idempotency_key=raw.get("idempotency_key"),
                payload=dict(payload),
                prev_hash=str(raw.get("prev_hash", "")),
                event_hash=str(raw.get("event_hash", "")),
                occurred_at=str(raw.get("occurred_at", "")),
                request_hash=(str(raw["request_hash"]) if raw.get("request_hash") is not None else None),
                protocol=(str(raw["protocol"]) if "protocol" in raw else ""),
                run_id=(str(raw["run_id"]) if raw.get("run_id") is not None else None),
                authorization=dict(raw.get("authorization", {})),
                snapshot=dict(raw.get("snapshot", {})),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IntegrityError(f"invalid event envelope: {exc}") from exc


def _event_state(event: EventEnvelope) -> tuple[str | None, dict[str, Any]]:
    """Return an optional target state and normalized payload for an event."""
    payload = dict(event.payload)
    if event.event_type in {"state.transition", "transition", "status.changed"}:
        # Skill-owned state transitions share the append-only log but must not
        # be interpreted as lifecycle states by the domain-neutral reducer.
        if payload.get("state_domain") == "skill" or payload.get("to_state") is not None:
            return None, payload
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
        "phases": [],
        "outcome": None,
        "wait_reason": None,
        "effect_status": "none",
        "artifacts": {},
        "validations": [],
        "verifications": [],
        "gate_decisions": [],
        "verification_records": [],
        "gate_records": [],
        "delivery_report": None,
        "evidence_refs": [],
        "last_seq": 0,
        "last_event_id": None,
        "event_count": 0,
        "audit_trail": [],
        "run_snapshot": {},
        "skill_states": {},
        "skill_state_transitions": [],
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
            if payload["phase"] is not None and payload["phase"] not in projection["phases"]:
                projection["phases"].append(payload["phase"])
        if target == "waiting":
            reason = payload.get("wait_reason")
            if reason is not None and reason not in WAIT_REASONS:
                raise InvalidTransition(f"unknown wait_reason: {reason}")
            projection["wait_reason"] = reason
        if "effect_status" in payload:
            effect_status = payload["effect_status"]
            if effect_status not in EFFECT_STATUSES:
                raise InvalidTransition(f"unknown effect_status: {effect_status}")
            projection["effect_status"] = effect_status
        if event.event_type == "artifact.registered":
            artifact_id = payload.get("artifact_id") or event.path
            if artifact_id:
                projection["artifacts"][artifact_id] = {**payload, "artifact_id": artifact_id}
        elif event.event_type in {"validation.completed", "validation.recorded"}:
            projection["validations"].append(payload)
        elif event.event_type == "verification.result":
            projection["verifications"].append(payload)
            projection["verification_records"].append({**payload, "_event_id": event.event_id, "_run_id": event.run_id, "_attempt_id": event.attempt_id})
        elif event.event_type == "verification.gate":
            projection["gate_decisions"].append(payload)
            projection["gate_records"].append({**payload, "_event_id": event.event_id, "_run_id": event.run_id, "_attempt_id": event.attempt_id})
        elif event.event_type == "state.transition" and payload.get("state_domain") == "skill":
            skill = str(payload.get("skill", ""))
            target = payload.get("to_state")
            if skill and target:
                projection["skill_states"][skill] = {
                    "state": str(target),
                    "version": str(payload.get("state_version", "")),
                    "event_id": event.event_id,
                    "snapshot_hash": payload.get("snapshot_hash"),
                }
                projection["skill_state_transitions"].append({
                    "skill": skill,
                    "from_state": payload.get("from_state"),
                    "to_state": target,
                    "state_version": payload.get("state_version"),
                    "run_id": event.run_id,
                    "attempt_id": event.attempt_id,
                    "event_id": event.event_id,
                    "snapshot_hash": payload.get("snapshot_hash"),
                })
        elif event.event_type in {"delivery.reported", "delivery.completed"}:
            projection["delivery_report"] = payload.get("report") or payload.get("path") or event.path or payload
        if event.snapshot:
            projection["run_snapshot"] = dict(event.snapshot)
        if event.event_type in {
            "run.started", "model.called", "tool.called", "verification.result", "verification.gate",
            "approval.granted", "effect.prepared", "effect.applied", "effect.reconciled",
            "delivery.reported", "recovery.recorded",
        }:
            projection["audit_trail"].append({
                "seq": event.seq,
                "event_id": event.event_id,
                "type": event.event_type,
                "actor": event.actor,
                "run_id": event.run_id,
                "request_hash": event.request_hash,
                "authorization": dict(event.authorization),
                "payload": payload,
                "evidence_refs": list(event.evidence_refs),
                "occurred_at": event.occurred_at,
            })
        projection["evidence_refs"] = list(dict.fromkeys([*projection["evidence_refs"], *event.evidence_refs, *payload.get("evidence_refs", [])]))
        projection["last_seq"] = event.seq
        projection["last_event_id"] = event.event_id
        projection["event_count"] += 1
    return projection


def _verify_skill_snapshots(events: Iterable[EventEnvelope], *, events_path: Path) -> None:
    """Validate current on-disk Skill snapshots referenced by new state events.

    Older events may not carry a snapshot hash/path and remain read-only
    compatible. Missing cache files are also tolerated because the event log is
    authoritative; a present file with a drifted hash is an integrity failure.
    """
    from .workspace import state_snapshot_hash
    latest: dict[str, EventEnvelope] = {}
    for event in events:
        if event.event_type != "state.transition" or event.payload.get("state_domain") != "skill":
            continue
        if event.payload.get("snapshot_hash"):
            latest[str(event.payload.get("skill", ""))] = event
    for event in latest.values():
        expected = event.payload.get("snapshot_hash")
        if not expected:
            continue
        raw_path = event.payload.get("snapshot_path")
        target = Path(raw_path) if raw_path else events_path.parent.parent / str(event.payload.get("skill", "")) / "log" / "meta-state.json"
        if not target.is_absolute():
            target = events_path.parent.parent / target
        try:
            target = target.resolve()
            target.relative_to(events_path.parent.parent.resolve())
        except (ValueError, OSError) as exc:
            raise IntegrityError("state snapshot path outside task workspace") from exc
        if not target.is_file():
            raise IntegrityError("state snapshot missing")
        try:
            snapshot = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IntegrityError("state snapshot unreadable") from exc
        if not isinstance(snapshot, Mapping) or state_snapshot_hash(snapshot) != str(expected).removeprefix("sha256:"):
            raise IntegrityError("state snapshot hash mismatch")
        if event.payload.get("state_event_id") and snapshot.get("state_event_id") != event.payload.get("state_event_id"):
            raise IntegrityError("state snapshot event binding mismatch")


def _guard_completion(
    projection: Mapping[str, Any],
    contract: Mapping[str, Any] | None = None,
    *,
    run_id: str | None = None,
    attempt_id: str | None = None,
) -> None:
    contract = contract or {}
    artifacts = projection.get("artifacts", {})
    required = contract.get("required_artifacts")
    if required is None:
        required = [k for k, value in artifacts.items() if value.get("required")]
    missing = [item for item in required if item not in artifacts]
    if missing:
        raise CompletionError(f"required artifacts missing: {', '.join(map(str, missing))}")
    required_phases = tuple(contract.get("required_phases", ()))
    phases = {str(item.get("phase")) for item in artifacts.values() if item.get("phase") is not None}
    phases.update(str(item.get("phase")) for item in projection.get("validations", []) if item.get("phase") is not None)
    phases.update(str(item) for item in projection.get("phases", ()))
    if required_phases and not set(required_phases).issubset(phases):
        raise CompletionError("required phases missing: " + ", ".join(sorted(set(required_phases) - phases)))
    for artifact_id in required:
        item = artifacts.get(artifact_id, {})
        path = item.get("path")
        if contract and not path:
            raise CompletionError(f"required artifact path is missing: {artifact_id}")
        if path:
            target = Path(path).expanduser()
            root = contract.get("artifact_root") or contract.get("project_root")
            if not target.is_absolute() and root:
                target = Path(root).expanduser() / target
            if not target.is_file():
                raise CompletionError(f"required artifact is not a file: {artifact_id}")
            if root:
                try:
                    target.resolve().relative_to(Path(root).expanduser().resolve())
                except ValueError as exc:
                    raise CompletionError(f"artifact path outside allowed root: {artifact_id}") from exc
            expected = item.get("content_hash") or item.get("hash")
            if expected and str(expected).removeprefix("sha256:") != hashlib.sha256(target.read_bytes()).hexdigest():
                raise CompletionError(f"artifact hash mismatch: {artifact_id}")
    validations = projection.get("validations", [])
    if not validations or any(v.get("verdict") not in {"pass", "passed", "success"} for v in validations[-1:]):
        raise CompletionError("a passing validation evidence is required")
    if not projection.get("delivery_report"):
        raise CompletionError("a delivery report is required")
    requirements = tuple(contract.get("requirements", ()))
    required_requirements = [item for item in requirements if isinstance(item, Mapping) and item.get("required", True)]
    verifications = list(projection.get("verification_records") or projection.get("verifications", []))
    gates = list(projection.get("gate_records") or projection.get("gate_decisions", []))
    # Completion evidence is scoped to the current execution identity.  A
    # caller that supplies only one half of the identity is ambiguous and is
    # rejected rather than silently falling back to historical evidence.
    if run_id is not None or attempt_id is not None:
        if run_id is None or attempt_id is None:
            raise CompletionError("run_id and attempt_id must be provided together")
        verifications = [item for item in verifications if item.get("_run_id") == run_id and item.get("_attempt_id", "default") == attempt_id]
        gates = [item for item in gates if item.get("_run_id") == run_id and item.get("_attempt_id", "default") == attempt_id]
    for item in verifications:
        component_gate = _component_bound_gate(
            item,
            run_id=item.get("_run_id"),
            attempt_id=str(item.get("_attempt_id", "default")),
        )
        if component_gate is not None and component_gate.decision not in {"allow", "allow_with_warnings"}:
            raise CompletionError("Contract Pack components do not allow completion")
    passed_ids = {
        str(item.get("requirement_id") or item.get("id") or item.get("verifier_id"))
        for item in verifications
        if item.get("verdict") == "pass" and item.get("execution_status", "completed") == "completed"
    }
    if required_requirements and not all(
        any(str(item.get(key)) in passed_ids for key in ("verifier_id", "id") if item.get(key))
        for item in required_requirements
    ):
        raise CompletionError("required verifiers missing or not passing")
    if required_requirements or gates:
        if not gates:
            raise CompletionError("a verifier gate decision is required")
        if not verifications:
            raise CompletionError("a verifier result is required before a gate decision")
        gate = gates[-1]
        if gate.get("decision") not in {"allow", "allow_with_warnings"}:
            raise CompletionError("verifier gate did not allow completion")
        refs = {f"{item.get('verifier_id')}@{item.get('verifier_version')}" for item in verifications if item.get("verifier_id") and item.get("verifier_version")}
        declared_refs = tuple(str(item) for item in gate.get("result_refs", ()))
        if not declared_refs:
            raise CompletionError("verifier gate must bind result_refs")
        if gates[-1].get("computed_by") != "kernel":
            raise CompletionError("verifier gate must be kernel-computed")
        try:
            recomputed = apply_gate(
                tuple(
                    VerificationResult(
                        verifier_id=str(item["verifier_id"]),
                        verifier_version=str(item["verifier_version"]),
                        execution_status=str(item.get("execution_status", "completed")),
                        verdict=str(item["verdict"]),
                        evidence_refs=tuple(item.get("evidence_refs", ())),
                    )
                    for item in verifications
                ),
                requirements=requirements or None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CompletionError("verifier result cannot be recomputed") from exc
        if gate.get("decision") != recomputed.decision or tuple(gate.get("unresolved", ())) != recomputed.unresolved:
            raise CompletionError("verifier gate does not match Kernel recomputation")
        if set(declared_refs) != refs or len(declared_refs) != len(verifications):
            raise CompletionError("verifier gate is not bound to recorded results")
        result_event_id = gate.get("result_event_id")
        if not result_event_id or result_event_id != verifications[-1].get("_event_id"):
            raise CompletionError("verifier gate is bound to a different result event")
        if any(item.get("verdict") in {"unchecked", "uncertain", "timed_out", "manual_review"} or item.get("execution_status", "completed") != "completed" for item in verifications):
            raise CompletionError("uncertain or unchecked verifier result cannot complete")


class EventLog:
    """Append-only NDJSON event log with projection and rebuild helpers."""

    def __init__(self, path: str | os.PathLike[str], *, contract: Mapping[str, Any] | None = None):
        self.path = Path(path)
        self.contract = dict(contract.to_dict() if hasattr(contract, "to_dict") else (contract or {}))

    @contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.with_name(self.path.name + ".lock").open("a+", encoding="utf-8")
        if os.name == "nt" and handle.tell() == 0:
            handle.write("0")
            handle.flush()
        try:
            try:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except ImportError:
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            yield
        finally:
            try:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except ImportError:
                pass
            handle.close()

    def _recover_partial_tail(self) -> None:
        """Drop only an unterminated final JSON fragment left by a crash."""
        if not self.path.is_file():
            return
        raw = self.path.read_bytes()
        if not raw or raw.endswith(b"\n"):
            return
        last_newline = raw.rfind(b"\n")
        fragment = raw[last_newline + 1 :]
        try:
            json.loads(fragment.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.path.write_bytes(raw[: last_newline + 1])

    def read(self) -> list[EventEnvelope]:
        if not self.path.exists():
            return []
        self._recover_partial_tail()
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

    def append(self, event_type: str, *, payload: Mapping[str, Any] | None = None, summary: str = "", scope: str = "task", actor: str = "runtime", attempt_id: str = "default", path: str | None = None, evidence_refs: Iterable[str] = (), idempotency_key: str | None = None, run_id: str | None = None, authorization: Mapping[str, Any] | None = None, snapshot: Mapping[str, Any] | None = None, event_id: str | None = None, _kernel_gate: object | None = None, _lock_held: bool = False) -> EventEnvelope:
        # Use the declared artifact/project root for artifact locators; this
        # keeps legitimate completion paths resolvable while still redacting
        # anything outside the allowed boundary.
        base_dir = self.path.parent
        declared_root = self.contract.get("artifact_root") or self.contract.get("project_root")
        if declared_root:
            try:
                base_dir = Path(declared_root).expanduser().resolve()
            except OSError:
                pass
        data = _sanitize_event_payload(dict(payload or {}), base_dir=base_dir)
        refs = tuple(str(_event_safe_value(ref, key="evidence_ref", base_dir=base_dir)) for ref in evidence_refs)
        auth = _sanitize_event_payload(dict(authorization or {}), base_dir=base_dir)
        snap = _sanitize_event_payload(dict(snapshot or {}), base_dir=base_dir)
        safe_path = _event_safe_value(path, key="path", base_dir=base_dir) if path is not None else None
        if path is not None and not Path(str(path)).is_file() and not (isinstance(safe_path, str) and (safe_path.startswith("path#") or safe_path.startswith("text#"))):
            safe_path = f"text#sha256:{hashlib.sha256(str(path).encode('utf-8')).hexdigest()}"
        safe_summary = str(_event_safe_value(summary, key="summary", base_dir=base_dir))
        request_hash = _request_hash(event_type, data, safe_summary, scope, actor, attempt_id, safe_path, refs, run_id, auth, snap)
        with (nullcontext() if _lock_held else self._locked()):
            self._recover_partial_tail()
            events = self.read()
            if event_type == "verification.gate" and _kernel_gate is not _KERNEL_GATE_TOKEN:
                raise IntegrityError("verification.gate must be emitted by record_verification")
            if event_type in {"effect.applied", "effect.reconciled"} and not (auth.get("scope") or auth.get("approval_ref") or auth.get("policy_version")):
                raise AuthorizationError(f"{event_type} requires explicit authorization")
            if idempotency_key:
                for existing in events:
                    if existing.idempotency_key == idempotency_key:
                        existing_hash = existing.request_hash or _request_hash(existing.event_type, existing.payload, existing.summary, existing.scope, existing.actor, existing.attempt_id, existing.path, existing.evidence_refs, existing.run_id, existing.authorization, existing.snapshot)
                        if existing_hash != request_hash:
                            raise IdempotencyConflict(f"idempotency key conflict: {idempotency_key}")
                        return existing
            event = EventEnvelope(seq=len(events) + 1, event_id=event_id or str(uuid.uuid4()), scope=scope, actor=actor, attempt_id=attempt_id, event_type=event_type, summary=safe_summary, path=safe_path, evidence_refs=refs, idempotency_key=idempotency_key, payload=data, prev_hash=events[-1].event_hash if events else "", occurred_at=_utc_now(), request_hash=request_hash, run_id=run_id, authorization=auth, snapshot=snap).with_hash()
            target, _ = _event_state(event)
            current = reduce_events(events)["current_state"]
            if target == "completed":
                identity_events = [item for item in events if item.run_id is not None or item.attempt_id != "default"]
                if identity_events and run_id is None:
                    raise CompletionError("run_id and attempt_id are required when run-bound evidence exists")
                _guard_completion(reduce_events(events), self.contract, run_id=run_id, attempt_id=attempt_id if run_id is not None else None)
                if current != "delivering":
                    raise InvalidTransition(f"illegal transition {current!r} -> 'completed'")
            elif target is not None and current is not None and target not in ALLOWED_TRANSITIONS[current]:
                raise InvalidTransition(f"illegal transition {current!r} -> {target!r}")
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
                "run_id": event.run_id,
                "authorization": event.authorization,
                "snapshot": event.snapshot,
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
        run_id: str | None = None,
        authorization: Mapping[str, Any] | None = None,
        snapshot: Mapping[str, Any] | None = None,
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
            run_id=run_id,
            authorization=authorization,
            snapshot=snapshot,
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
        run_id: str | None = None,
        authorization: Mapping[str, Any] | None = None,
        snapshot: Mapping[str, Any] | None = None,
        requirements: Mapping[str, bool] | Iterable[Mapping[str, Any]] | None = None,
        _lock_held: bool = False,
    ) -> tuple[EventEnvelope, EventEnvelope | None]:
        """Append a verifier result and a Kernel-recomputed gate decision.

        The caller-provided ``gate`` is treated as an advisory candidate only;
        its decision/reason/unresolved values are never trusted for completion.
        """
        if not isinstance(result, Mapping):
            return self.record_verification_batch(tuple(result), gate, scope=scope, actor=actor, attempt_id=attempt_id, idempotency_key=idempotency_key, run_id=run_id, authorization=authorization, snapshot=snapshot, requirements=requirements)
        refs = tuple(result.get("evidence_refs", ()))
        result_data = dict(result)
        verifier_id = result_data.get("verifier_id")
        verifier_version = result_data.get("verifier_version")
        computed: Any = None
        if verifier_id and verifier_version:
            try:
                computed_result = VerificationResult(
                    verifier_id=str(verifier_id), verifier_version=str(verifier_version),
                    execution_status=str(result_data.get("execution_status", "completed")),
                    verdict=str(result_data.get("verdict")),
                    findings=tuple(result_data.get("findings", ())), facts=dict(result_data.get("facts", {})),
                    evidence_refs=refs, confidence=result_data.get("confidence"),
                    uncertainty_reason=result_data.get("uncertainty_reason"), model_or_engine=result_data.get("model_or_engine"),
                    duration_ms=result_data.get("duration_ms"), assurance_tier=str(result_data.get("assurance_tier", "deterministic")),
                )
                computed = apply_gate((computed_result,), requirements=requirements)
                component_gate = _component_bound_gate(result_data, run_id=run_id, attempt_id=attempt_id)
                if component_gate is not None:
                    computed = component_gate
            except (TypeError, ValueError):
                computed = None
        if computed is None:
            # Malformed identity/status is persisted as a non-passing result,
            # but can never produce an allowing gate.
            computed = {"decision": "reject", "reason": "invalid verifier result identity or status", "result_refs": (), "unresolved": (str(verifier_id or "unknown"),)}
        verification = self.append(
            "verification.result",
            payload=result_data,
            evidence_refs=refs,
            scope=scope,
            actor=actor,
            attempt_id=attempt_id,
            idempotency_key=idempotency_key,
            run_id=run_id,
            authorization=authorization,
            snapshot=snapshot,
            _lock_held=_lock_held,
        )
        gate_event = None
        if gate is not None:
            try:
                from .verifier_ids import validate_verifier_id
                identity_valid = bool(verifier_id and verifier_version and _VERSION_RE.match(str(verifier_version)) and validate_verifier_id(str(verifier_id)))
            except ValueError:
                identity_valid = False
            if identity_valid:
                gate_payload = computed.to_dict() if hasattr(computed, "to_dict") else dict(computed)
                gate_payload.update({"computed_by": "kernel", "result_event_id": verification.event_id})
            else:
                # Legacy callers may persist non-canonical IDs; retain their
                # historical gate shape, which is never eligible for
                # completion because it lacks Kernel binding metadata.
                gate_payload = dict(gate)
            if gate.get("request_id") is not None:
                gate_payload["request_id"] = gate.get("request_id")
            gate_event = self.append(
                "verification.gate",
                payload=gate_payload,
                evidence_refs=refs,
                scope=scope,
                actor=actor,
                attempt_id=attempt_id,
                idempotency_key=f"{idempotency_key}:gate" if idempotency_key else None,
                run_id=run_id,
                authorization=authorization,
                snapshot=snapshot,
                _kernel_gate=_KERNEL_GATE_TOKEN,
                _lock_held=_lock_held,
            )
        return verification, gate_event

    def record_verification_batch(
        self,
        results: Iterable[Mapping[str, Any]],
        gate: Mapping[str, Any] | None = None,
        *,
        scope: str = "task",
        actor: str = "runtime",
        attempt_id: str = "default",
        idempotency_key: str | None = None,
        run_id: str | None = None,
        authorization: Mapping[str, Any] | None = None,
        snapshot: Mapping[str, Any] | None = None,
        requirements: Mapping[str, bool] | Iterable[Mapping[str, Any]] | None = None,
    ) -> tuple[EventEnvelope, EventEnvelope | None]:
        items = tuple(results)
        if not items:
            raise ValueError("verification result list cannot be empty")
        with self._locked():
            result_events: list[EventEnvelope] = []
            for index, item in enumerate(items):
                event, _ = self.record_verification(item, None, scope=scope, actor=actor, attempt_id=attempt_id, idempotency_key=f"{idempotency_key}:{index}" if idempotency_key else None, run_id=run_id, authorization=authorization, snapshot=snapshot, requirements=requirements, _lock_held=True)
                result_events.append(event)
            computed_results: list[VerificationResult] = []
            component_gates: list[GateDecision] = []
            for item in items:
                try:
                    from .verifier_ids import validate_verifier_id
                    validate_verifier_id(str(item["verifier_id"]))
                    computed_results.append(VerificationResult(verifier_id=str(item["verifier_id"]), verifier_version=str(item["verifier_version"]), execution_status=str(item.get("execution_status", "completed")), verdict=str(item["verdict"]), evidence_refs=tuple(item.get("evidence_refs", ()))))
                    component_gate = _component_bound_gate(item, run_id=run_id, attempt_id=attempt_id)
                    if component_gate is not None:
                        component_gates.append(component_gate)
                except (KeyError, TypeError, ValueError):
                    continue
            computed = apply_gate(computed_results, requirements=requirements) if len(computed_results) == len(items) else None
            blocking_component_gates = [item for item in component_gates if item.decision not in {"allow", "allow_with_warnings"}]
            if blocking_component_gates:
                decision = "reject" if any(item.decision == "reject" for item in blocking_component_gates) else "manual_review"
                computed = GateDecision(
                    decision,
                    "one or more Contract Pack component sets did not pass",
                    tuple(ref for item in blocking_component_gates for ref in item.result_refs),
                    tuple(dict.fromkeys(value for item in blocking_component_gates for value in item.unresolved)),
                )
            if gate is None:
                return result_events[-1], None
            gate_payload = computed.to_dict() if computed is not None else dict(gate or {"decision": "reject", "reason": "invalid verifier result identity or status"})
            if computed is not None:
                gate_payload.update({"computed_by": "kernel", "result_event_id": result_events[-1].event_id})
            return result_events[-1], self.append("verification.gate", payload=gate_payload, evidence_refs=tuple(dict.fromkeys(ref for item in items for ref in item.get("evidence_refs", ()))), scope=scope, actor=actor, attempt_id=attempt_id, idempotency_key=f"{idempotency_key}:gate" if idempotency_key else None, run_id=run_id, authorization=authorization, snapshot=snapshot, _kernel_gate=_KERNEL_GATE_TOKEN, _lock_held=True)

    def record_audit(self, event_type: str, *, payload: Mapping[str, Any] | None = None, run_id: str | None = None, actor: str = "runtime", authorization: Mapping[str, Any] | None = None, evidence_refs: Iterable[str] = (), idempotency_key: str | None = None, snapshot: Mapping[str, Any] | None = None) -> EventEnvelope:
        """Record a redacted execution-audit event without changing lifecycle state."""
        safe: dict[str, Any] = {}
        for key, value in dict(payload or {}).items():
            if key.lower() in {"input", "output", "prompt", "content", "response", "stderr", "stdout"}:
                safe[f"{key}_hash"] = hashlib.sha256(_canonical({"value": value})).hexdigest()
            else:
                safe[key] = value
        return self.append(event_type, payload=safe, run_id=run_id, actor=actor, authorization=authorization, evidence_refs=evidence_refs, idempotency_key=idempotency_key, snapshot=snapshot)

    def record_run_started(self, *, run_id: str, snapshot: Mapping[str, Any] | None = None, actor: str = "runtime", authorization: Mapping[str, Any] | None = None) -> EventEnvelope:
        return self.record_audit("run.started", run_id=run_id, snapshot=snapshot, actor=actor, authorization=authorization)

    def record_model_call(self, *, run_id: str, model: str, prompt: Any = None, output: Any = None, actor: str = "runtime") -> EventEnvelope:
        return self.record_audit("model.called", run_id=run_id, actor=actor, payload={"model": model, "prompt": prompt, "output": output})

    def record_tool_call(self, *, run_id: str, tool: str, input: Any = None, output: Any = None, actor: str = "runtime") -> EventEnvelope:
        return self.record_audit("tool.called", run_id=run_id, actor=actor, payload={"tool": tool, "input": input, "output": output})

    def record_delivery(self, report: str, **metadata: Any) -> EventEnvelope:
        value = str(report)
        if Path(value).is_file():
            safe_report: Any = value
            path_value: str = value
        else:
            safe_report = f"text#sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"
            path_value = safe_report
        return self.append("delivery.reported", payload={"report": safe_report, **metadata}, path=path_value)

    def rebuild(self, state_path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
        events = self.read()
        _verify_skill_snapshots(events, events_path=self.path)
        projection = reduce_events(events)
        target = Path(state_path) if state_path else self.path.parent / "state.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, target)
        try:
            directory = os.open(str(target.parent), os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass
        return projection


def main() -> int:
    from .cli import main as cli_main

    return cli_main()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
