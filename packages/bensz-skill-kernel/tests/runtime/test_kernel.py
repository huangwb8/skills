import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from bensz_skill_kernel import (
    EventLog,
    InvalidTransition,
    IntegrityError,
    CompletionError,
    AuthorizationError,
    IdempotencyConflict,
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


def test_rebuild_detects_skill_snapshot_drift(tmp_path: Path):
    from bensz_skill_kernel import state_snapshot_hash

    task = tmp_path / "task"
    skill_log = task / "demo" / "log"
    skill_log.mkdir(parents=True)
    snapshot = {"protocol": "bensz-meta-state-v1", "skill": "demo", "current_state": "bensz.demo.ready", "state_version": "1.0.0"}
    snapshot["snapshot_hash"] = state_snapshot_hash(snapshot)
    snapshot_path = skill_log / "meta-state.json"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
    log = EventLog(task / "log" / "events.ndjson")
    log.append("state.transition", payload={"state_domain": "skill", "skill": "demo", "to_state": "bensz.demo.ready", "snapshot_hash": snapshot["snapshot_hash"], "snapshot_path": str(snapshot_path)})
    snapshot["current_state"] = "bensz.demo.tampered"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
    with pytest.raises(IntegrityError, match="state snapshot hash mismatch"):
        log.rebuild()


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


def test_kernel_recomputes_forged_allow_gate_and_binds_result(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    result, gate = log.record_verification(
        {
            "verifier_id": "bensz.demo.check",
            "verifier_version": "1.0.0",
            "verdict": "fail",
            "execution_status": "completed",
        },
        {"decision": "allow", "reason": "forged"},
        run_id="run-1",
        attempt_id="attempt-1",
    )
    assert gate is not None
    assert gate.payload["decision"] == "reject"
    assert gate.payload["computed_by"] == "kernel"
    assert gate.payload["result_event_id"] == result.event_id
    assert gate.run_id == result.run_id == "run-1"
    assert gate.attempt_id == result.attempt_id == "attempt-1"


def test_direct_gate_append_is_forbidden(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    with pytest.raises(IntegrityError, match="record_verification"):
        log.append("verification.gate", payload={"decision": "allow", "computed_by": "kernel"})
    with pytest.raises(IntegrityError, match="record_verification"):
        log.append("verification.gate", payload={"decision": "allow"}, _kernel_gate=True)


def test_verification_batches_are_contiguous_under_concurrency(tmp_path: Path):
    events_path = tmp_path / "events.ndjson"
    batches = [
        [
            {"verifier_id": "bensz.document.markdown-link-integrity", "verifier_version": "1.0.0", "verdict": "pass", "execution_status": "completed"},
            {"verifier_id": "bensz.evidence.citation-truth-fit", "verifier_version": "1.0.0", "verdict": "unchecked", "execution_status": "unchecked"},
        ],
        [
            {"verifier_id": "bensz.document.markdown-link-integrity", "verifier_version": "1.0.0", "verdict": "pass", "execution_status": "completed"},
            {"verifier_id": "bensz.evidence.citation-truth-fit", "verifier_version": "1.0.0", "verdict": "unchecked", "execution_status": "unchecked"},
        ],
    ]

    def write(index: int):
        EventLog(events_path).record_verification_batch(
            batches[index], {"decision": "manual_review"}, run_id=f"run-{index}", idempotency_key=f"batch-{index}"
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(write, range(2)))
    events = EventLog(events_path).read()
    assert len(events) == 6
    for offset in (0, 3):
        assert [event.event_type for event in events[offset:offset + 3]] == [
            "verification.result", "verification.result", "verification.gate"
        ]


def test_event_boundary_redacts_paths_raw_text_and_secrets(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    event = log.append(
        "audit",
        summary="/private/user/input.md",
        path="DOCUMENT CONTENT",
        evidence_refs=("/private/user/evidence.json",),
        payload={"facts": {"path": "/private/user/input.md", "password": "secret"}, "stdout": "raw output"},
    )
    raw = json.dumps(event.to_dict())
    assert "/private/user" not in raw
    assert "DOCUMENT CONTENT" not in raw
    assert "raw output" not in raw
    assert "[REDACTED]" in raw


def test_snapshot_hash_event_missing_file_is_integrity_error(tmp_path: Path):
    log = EventLog(tmp_path / "log" / "events.ndjson")
    log.append(
        "state.transition",
        payload={
            "state_domain": "skill",
            "skill": "demo",
            "to_state": "bensz.demo.ready",
            "snapshot_hash": "0" * 64,
            "snapshot_path": "demo/log/meta-state.json",
        },
    )
    with pytest.raises(IntegrityError, match="state snapshot missing"):
        log.rebuild()


def test_idempotency_replays_same_intent_and_rejects_conflict(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")

    first = log.append("task.created", payload={"state": "planned"}, idempotency_key="create-1")
    replay = log.append("task.created", payload={"state": "planned"}, idempotency_key="create-1")

    assert replay == first
    assert len(log.read()) == 1
    with pytest.raises(IdempotencyConflict):
        log.append("task.created", payload={"state": "active"}, idempotency_key="create-1")


def test_side_effect_events_require_authorization(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")

    with pytest.raises(AuthorizationError):
        log.append("effect.applied", payload={"effect_id": "publish"})

    event = log.append(
        "effect.applied",
        payload={"effect_id": "publish"},
        authorization={"scope": ["publish"]},
    )
    assert event.authorization == {"scope": ["publish"]}


def test_audit_payloads_are_hashed_and_sensitive_fields_redacted(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    log.record_tool_call(run_id="run-1", tool="publish", input={"token": "secret"}, output={"ok": True})

    event = log.read()[0]
    assert "input" not in event.payload
    assert "output" not in event.payload
    assert len(event.payload["input_hash"]) == 64
    assert len(event.payload["output_hash"]) == 64


def test_partial_tail_is_recovered_but_complete_tail_is_not_discarded(tmp_path: Path):
    path = tmp_path / "events.ndjson"
    log = EventLog(path)
    log.append("task.created", payload={"state": "planned"})
    path.write_bytes(path.read_bytes() + b'{"seq":2')

    assert len(log.read()) == 1
    assert path.read_bytes().endswith(b"\n")


def test_invalid_event_json_and_protocol_are_integrity_errors(tmp_path: Path):
    path = tmp_path / "events.ndjson"
    path.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(IntegrityError):
        EventLog(path).read()

    path.write_text('{"protocol":"other","seq":1,"event_id":"x"}\n', encoding="utf-8")
    with pytest.raises(IntegrityError):
        EventLog(path).read()


def test_completion_guard_rejects_artifact_path_and_hash_violations(tmp_path: Path):
    report = tmp_path / "report.md"
    report.write_text("ok\n", encoding="utf-8")
    log = EventLog(tmp_path / "events.ndjson", contract={"artifact_root": str(tmp_path), "required_artifacts": ["report"]})
    log.append("task.created", payload={"state": "planned"})
    log.transition("active")
    log.record_artifact("report", required=True, path=str(report), content_hash="sha256:" + "0" * 64)
    log.record_validation("pass")
    log.record_delivery(str(report))
    log.transition("checking")
    log.transition("delivering")

    with pytest.raises(CompletionError, match="hash mismatch"):
        log.transition("completed", outcome="success")

    outside = tmp_path.parent / "outside-report.md"
    outside.write_text("outside\n", encoding="utf-8")
    outside_log = EventLog(
        tmp_path / "outside-events.ndjson",
        contract={"artifact_root": str(tmp_path), "required_artifacts": ["report"]},
    )
    outside_log.append("task.created", payload={"state": "planned"})
    outside_log.transition("active")
    outside_log.record_artifact("report", required=True, path=str(outside))
    outside_log.record_validation("pass")
    outside_log.record_delivery(str(outside))
    outside_log.transition("checking")
    outside_log.transition("delivering")
    with pytest.raises(CompletionError, match="not a file|outside allowed root"):
        outside_log.transition("completed", outcome="success")
