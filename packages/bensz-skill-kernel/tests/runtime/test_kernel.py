import json
from pathlib import Path

import pytest

from bensz_skill_kernel import (
    EventLog,
    InvalidTransition,
    IntegrityError,
    CompletionError,
    reduce_events,
)


def test_append_events_have_sequence_and_hash_chain(tmp_path: Path):
    log = EventLog(tmp_path / "log" / "events.ndjson")
    first = log.append("task.created", payload={"state": "planned"}, summary="created")
    second = log.append("state.transition", payload={"to": "active"})

    assert first.seq == 1
    assert second.seq == 2
    assert second.prev_hash == first.event_hash
    assert len(second.event_hash) == 64
    assert len(log.read()) == 2


def test_reducer_is_deterministic_and_rebuildable(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    log.append("task.created", payload={"state": "planned"})
    log.append("state.transition", payload={"to": "active"})
    log.append("state.transition", payload={"to": "waiting", "wait_reason": "dependency"})
    events = log.read()

    projection = reduce_events(events)
    assert projection["current_state"] == "waiting"
    assert projection["wait_reason"] == "dependency"
    assert projection["last_seq"] == 3
    assert projection == reduce_events(events)


def test_invalid_transition_is_rejected(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    log.append("task.created", payload={"state": "planned"})
    with pytest.raises(InvalidTransition):
        log.append("state.transition", payload={"to": "completed"})


def test_hash_chain_corruption_is_detected(tmp_path: Path):
    path = tmp_path / "events.ndjson"
    log = EventLog(path)
    log.append("task.created", payload={"state": "planned"})
    raw = json.loads(path.read_text().splitlines()[0])
    raw["summary"] = "tampered"
    path.write_text(json.dumps(raw) + "\n")
    with pytest.raises(IntegrityError):
        log.read()


def test_completion_guard_requires_artifacts_validation_and_report(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    log.append("task.created", payload={"state": "planned"})
    log.append("state.transition", payload={"to": "active"})
    log.append("artifact.registered", payload={"artifact_id": "report", "required": True})
    log.append("validation.completed", payload={"verdict": "pass", "evidence_refs": ["report"]})
    with pytest.raises(CompletionError):
        log.append("state.transition", payload={"to": "completed"})
    log.append("delivery.reported", payload={"report": "report.md"})
    done = log.append("state.transition", payload={"to": "checking"})
    assert done.payload["to"] == "checking"
    log.append("state.transition", payload={"to": "delivering"})
    log.append("state.transition", payload={"to": "completed", "outcome": "success"})
    assert log.projection()["current_state"] == "completed"


def test_verifier_events_are_replayable(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    result, gate = log.record_verification(
        {"verdict": "fail", "execution_status": "completed", "evidence_refs": ["snapshot:1"]},
        {"decision": "reject", "reason": "required verifier failure"},
    )
    projection = log.projection()
    assert result.event_type == "verification.result"
    assert gate and gate.event_type == "verification.gate"
    assert projection["verifications"][0]["verdict"] == "fail"
    assert projection["gate_decisions"][0]["decision"] == "reject"
