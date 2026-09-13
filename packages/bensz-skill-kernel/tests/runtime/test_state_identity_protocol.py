import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from bensz_skill_kernel import (
    ContractPack,
    ContractPackExecutor,
    CompletionError,
    EventEnvelope,
    EventLog,
    IntegrityError,
    InvalidTransition,
    KERNEL_CAPABILITIES_PROTOCOL,
    STATE_IDENTITY_PROTOCOL,
    StateDefinition,
    TaskWorkspace,
    WorkspaceError,
    check_state_invariants,
    kernel_capabilities,
)
from bensz_skill_kernel.cli import main


def _identity(run_id: str, state_visit_id: str, attempt_id: str) -> dict[str, str]:
    return {
        "run_id": run_id,
        "state_visit_id": state_visit_id,
        "attempt_id": attempt_id,
    }


def _enter_v2_state(
    log: EventLog,
    *,
    state: str = "test.demo.checking",
    visit: str = "visit-checking-1",
    attempt: str = "attempt-checking-1",
    bind_snapshot: bool = True,
):
    payload = {
        "state_domain": "skill",
        "skill": "demo-skill",
        "from_state": "bensz.workspace.ready",
        "to_state": state,
        "state_version": "1.0.0",
        "identity_protocol": STATE_IDENTITY_PROTOCOL,
        "source_identity": None,
        "target_identity": _identity("run-1", visit, attempt),
    }
    if bind_snapshot:
        payload["snapshot_hash"] = "a" * 64
    return log.append(
        "state.transition",
        payload=payload,
        scope="skill",
        run_id="run-1",
        state_visit_id=visit,
        attempt_id=attempt,
    )


def _make_transition_skill(root: Path) -> Path:
    skill = root / "demo-skill"
    state = skill / "states" / "checking" / "STATE.md"
    state.parent.mkdir(parents=True)
    (skill / "config.yaml").write_text(
        "runtime:\n"
        "  state_roots: [states]\n"
        "  initial_state: bensz.workspace.ready\n"
        "  states: [test.demo.checking]\n",
        encoding="utf-8",
    )
    state.write_text(
        "---\n"
        "id: test.demo.checking\n"
        "version: 1.0.0\n"
        "entry_conditions: bensz.workspace.ready\n"
        "---\n\n# Checking\n",
        encoding="utf-8",
    )
    return skill


def test_transition_projects_explicit_target_identity_and_rebuilds(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    event = _enter_v2_state(log, bind_snapshot=False)

    projection = log.projection()
    current = projection["skill_states"]["demo-skill"]
    assert event.protocol == "bensz-event-v2"
    assert current["identity_protocol"] == STATE_IDENTITY_PROTOCOL
    assert current["run_id"] == "run-1"
    assert current["state_visit_id"] == "visit-checking-1"
    assert current["active_attempt_id"] == "attempt-checking-1"
    assert current["legacy_identity"] is False
    assert log.rebuild(tmp_path / "state.json") == projection


def test_attempt_supersede_invalidates_old_evidence_handoff_and_authorization(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    _enter_v2_state(log)
    definition = StateDefinition(
        id="test.demo.checking",
        version="1.0.0",
        invariants=("verifier-result-recorded", "verifier-gate-allow"),
    )
    old_identity = _identity("run-1", "visit-checking-1", "attempt-checking-1")
    new_identity = _identity("run-1", "visit-checking-1", "attempt-checking-2")
    log.record_verification(
        {
            "verifier_id": "test.demo.links",
            "verifier_version": "1.0.0",
            "verdict": "pass",
            "execution_status": "completed",
        },
        {"decision": "allow", "result_refs": ["test.demo.links@1.0.0"]},
        **old_identity,
    )
    log.append(
        "action.handoff",
        payload={"handoff_id": "handoff-old", "skill": "demo-skill", "state": definition.id},
        scope="skill",
        evidence_refs=("evidence:old",),
        **old_identity,
    )
    grant = log.preflight_action(
        skill="demo-skill",
        action="publish-report",
        state=definition.id,
        state_version="1.0.0",
        handoff_id="handoff-old",
        evidence_refs=("evidence:old",),
        **old_identity,
    )
    assert grant.event_type == "action.authorization.granted"

    started = log.start_attempt(
        skill="demo-skill",
        state=definition.id,
        state_version="1.0.0",
        run_id="run-1",
        state_visit_id="visit-checking-1",
        attempt_id="attempt-checking-2",
        reason="retry after failed evidence collection",
        idempotency_key="retry-checking-2",
    )
    assert started.event_type == "state.attempt.started"
    assert started.payload["supersedes_attempt_id"] == "attempt-checking-1"
    assert log.projection()["skill_states"]["demo-skill"]["active_attempt_id"] == "attempt-checking-2"
    assert log.projection()["action_authorizations"][grant.payload["authorization_id"]]["status"] == "expired"

    old_failures = check_state_invariants(
        definition,
        log.read(),
        context={"skill": "demo-skill", **old_identity},
    )
    assert any("active state visit/attempt" in item for item in old_failures)
    new_failures = check_state_invariants(
        definition,
        log.read(),
        context={"skill": "demo-skill", **new_identity},
    )
    assert any("missing events after current attempt start" in item for item in new_failures)

    stale_handoff = log.preflight_action(
        skill="demo-skill",
        action="publish-report",
        state=definition.id,
        state_version="1.0.0",
        handoff_id="handoff-old",
        **new_identity,
    )
    assert stale_handoff.payload["reason_code"] == "handoff_outside_attempt_window"
    expired = log.consume_action_authorization(
        grant.payload["authorization_id"],
        skill="demo-skill",
        action="publish-report",
        **new_identity,
    )
    assert expired.payload["reason_code"] == "authorization_expired"

    log.record_verification(
        {
            "verifier_id": "test.demo.links",
            "verifier_version": "1.0.0",
            "verdict": "pass",
            "execution_status": "completed",
        },
        {"decision": "allow", "result_refs": ["test.demo.links@1.0.0"]},
        **new_identity,
    )
    assert check_state_invariants(
        definition,
        log.read(),
        context={"skill": "demo-skill", **new_identity},
    ) == ()


def test_contract_handoff_and_submission_bind_state_visit(tmp_path: Path):
    root = tmp_path / "verifier"
    root.mkdir()
    (root / "VERIFIER.md").write_text("# Review\n\nReview evidence.\n", encoding="utf-8")
    pack = ContractPack.from_directory(
        root,
        package_kind="verifier",
        contract_name="VERIFIER.md",
        entry={
            "id": "test.demo.review",
            "version": "1.0.0",
            "components": [{"id": "review", "type": "agent"}],
        },
    )
    executor = ContractPackExecutor()
    pending = executor.execute(
        pack,
        request={"evidence": [{"ref": "subject"}]},
        run_id="run-1",
        state_visit_id="visit-1",
        attempt_id="attempt-1",
    )
    handoff = pending.handoffs[0]
    assert handoff.state_visit_id == "visit-1"
    submission = handoff.bind_result(
        verdict="pass",
        evidence_refs=("subject",),
        executor={"type": "agent", "id": "reviewer", "model": "model"},
    )
    submission["state_visit_id"] = "visit-other"
    try:
        executor.execute(
            pack,
            request={"evidence": [{"ref": "subject"}]},
            submissions=(submission,),
            run_id="run-1",
            state_visit_id="visit-1",
            attempt_id="attempt-1",
        )
    except Exception as exc:
        assert "state visit identity mismatch" in str(exc)
    else:
        raise AssertionError("cross-visit component result must be rejected")


def test_legacy_state_event_remains_readable_but_is_marked_legacy(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    log.append(
        "state.transition",
        payload={
            "state_domain": "skill",
            "skill": "demo-skill",
            "to_state": "test.demo.legacy",
            "state_version": "1.0.0",
        },
        scope="skill",
        run_id="legacy-run",
        attempt_id="legacy-attempt",
    )
    state = log.projection()["skill_states"]["demo-skill"]
    assert state["legacy_identity"] is True
    assert state["state_visit_id"] is None
    assert state["active_attempt_id"] == "legacy-attempt"


def test_reducer_rejects_wrong_source_reused_visit_and_reused_attempt(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    _enter_v2_state(log, bind_snapshot=False)
    with pytest.raises(IntegrityError, match="source identity is not active"):
        log.append(
            "state.transition",
            payload={
                "state_domain": "skill",
                "skill": "demo-skill",
                "from_state": "test.demo.checking",
                "to_state": "test.demo.reported",
                "state_version": "1.0.0",
                "identity_protocol": STATE_IDENTITY_PROTOCOL,
                "source_identity": _identity("run-1", "visit-checking-1", "wrong-attempt"),
                "target_identity": _identity("run-1", "visit-reported-1", "attempt-reported-1"),
            },
            scope="skill",
            run_id="run-1",
            state_visit_id="visit-reported-1",
            attempt_id="attempt-reported-1",
        )

    log.start_attempt(
        skill="demo-skill",
        state="test.demo.checking",
        state_version="1.0.0",
        run_id="run-1",
        state_visit_id="visit-checking-1",
        attempt_id="attempt-checking-2",
        reason="retry",
        idempotency_key="attempt-2",
    )
    log.start_attempt(
        skill="demo-skill",
        state="test.demo.checking",
        state_version="1.0.0",
        run_id="run-1",
        state_visit_id="visit-checking-1",
        attempt_id="attempt-checking-3",
        reason="retry again",
        idempotency_key="attempt-3",
    )
    with pytest.raises(InvalidTransition, match="attempt_identity_reused"):
        log.start_attempt(
            skill="demo-skill",
            state="test.demo.checking",
            state_version="1.0.0",
            run_id="run-1",
            state_visit_id="visit-checking-1",
            attempt_id="attempt-checking-2",
            reason="must not reuse",
            idempotency_key="attempt-2-reused",
        )

    log.append(
        "state.transition",
        payload={
            "state_domain": "skill",
            "skill": "demo-skill",
            "from_state": "test.demo.checking",
            "to_state": "test.demo.reported",
            "state_version": "1.0.0",
            "identity_protocol": STATE_IDENTITY_PROTOCOL,
            "source_identity": _identity("run-1", "visit-checking-1", "attempt-checking-3"),
            "target_identity": _identity("run-1", "visit-reported-1", "attempt-reported-1"),
        },
        scope="skill",
        run_id="run-1",
        state_visit_id="visit-reported-1",
        attempt_id="attempt-reported-1",
    )
    with pytest.raises(IntegrityError, match="State visit identity was already used"):
        log.append(
            "state.transition",
            payload={
                "state_domain": "skill",
                "skill": "demo-skill",
                "from_state": "test.demo.reported",
                "to_state": "test.demo.checking",
                "state_version": "1.0.0",
                "identity_protocol": STATE_IDENTITY_PROTOCOL,
                "source_identity": _identity("run-1", "visit-reported-1", "attempt-reported-1"),
                "target_identity": _identity("run-1", "visit-checking-1", "attempt-checking-4"),
            },
            scope="skill",
            run_id="run-1",
            state_visit_id="visit-checking-1",
            attempt_id="attempt-checking-4",
        )


def test_stale_attempt_idempotency_replay_does_not_reactivate_old_attempt(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    _enter_v2_state(log, bind_snapshot=False)
    common = {
        "skill": "demo-skill",
        "state": "test.demo.checking",
        "state_version": "1.0.0",
        "run_id": "run-1",
        "state_visit_id": "visit-checking-1",
    }
    log.start_attempt(
        **common,
        attempt_id="attempt-checking-2",
        reason="first retry",
        idempotency_key="attempt-2",
    )
    log.start_attempt(
        **common,
        attempt_id="attempt-checking-3",
        reason="second retry",
        idempotency_key="attempt-3",
    )

    with pytest.raises(InvalidTransition, match="idempotent_attempt_not_active"):
        log.start_attempt(
            **common,
            attempt_id="attempt-checking-2",
            reason="first retry",
            idempotency_key="attempt-2",
        )


def test_v2_snapshot_requires_complete_identity(tmp_path: Path):
    workspace = TaskWorkspace.open(tmp_path, description="invalid-v2")
    with pytest.raises(WorkspaceError, match="state_visit_id"):
        workspace.write_meta_state(
            "demo-skill",
            {
                "protocol": "bensz-meta-state-v2",
                "identity_protocol": STATE_IDENTITY_PROTOCOL,
                "skill": "demo-skill",
                "current_state": "test.demo.checking",
                "state_version": "1.0.0",
                "run_id": "run-1",
                "active_attempt_id": "attempt-1",
            },
        )


def test_v2_event_requires_complete_string_identity(tmp_path: Path):
    log = EventLog(tmp_path / "events.ndjson")
    with pytest.raises(ValueError, match="event identity.attempt_id"):
        log.append(
            "verification.result",
            run_id="run-1",
            state_visit_id="visit-1",
            attempt_id=1,
        )


def test_completion_rejects_gate_from_another_state_visit(tmp_path: Path):
    log = EventLog(
        tmp_path / "events.ndjson",
        contract={"requirements": [{"verifier_id": "test.demo.links", "required": True}]},
    )
    log.append("task.created", payload={"state": "planned"})
    log.append("state.transition", payload={"to": "active"})
    log.record_verification(
        {
            "verifier_id": "test.demo.links",
            "verifier_version": "1.0.0",
            "verdict": "pass",
            "execution_status": "completed",
        },
        {"decision": "allow"},
        run_id="run-1",
        state_visit_id="visit-old",
        attempt_id="attempt-1",
    )
    log.append("validation.completed", payload={"verdict": "pass"})
    log.append("delivery.reported", payload={"report": "report.md"})
    log.append("state.transition", payload={"to": "checking"})
    log.append("state.transition", payload={"to": "delivering"})

    with pytest.raises(CompletionError, match="required verifiers"):
        log.append(
            "state.transition",
            payload={"to": "completed"},
            run_id="run-1",
            state_visit_id="visit-current",
            attempt_id="attempt-1",
        )
    with pytest.raises(IntegrityError, match="event identity.run_id"):
        EventEnvelope.from_dict(
            {
                "protocol": "bensz-event-v2",
                "seq": 1,
                "event_id": "event-1",
                "state_visit_id": "visit-1",
                "attempt_id": "attempt-1",
                "type": "verification.result",
            },
        )


def test_transition_snapshot_transaction_holds_event_lock(tmp_path: Path, monkeypatch, capsys):
    workspace = TaskWorkspace.open(tmp_path, description="transaction-lock")
    skill = _make_transition_skill(tmp_path)
    lock_depth = 0
    original_locked = EventLog._locked
    original_prepare = TaskWorkspace.prepare_meta_state
    original_commit = TaskWorkspace.commit_meta_state

    @contextmanager
    def traced_locked(self):
        nonlocal lock_depth
        with original_locked(self):
            lock_depth += 1
            try:
                yield
            finally:
                lock_depth -= 1

    def traced_prepare(self, target_skill, snapshot):
        assert lock_depth == 1
        return original_prepare(self, target_skill, snapshot)

    def traced_commit(self, temporary, target):
        assert lock_depth == 1
        return original_commit(self, temporary, target)

    monkeypatch.setattr(EventLog, "_locked", traced_locked)
    monkeypatch.setattr(TaskWorkspace, "prepare_meta_state", traced_prepare)
    monkeypatch.setattr(TaskWorkspace, "commit_meta_state", traced_commit)

    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.checking",
        "--skill-root", str(skill), "--run-id", "run-1",
        "--target-attempt-id", "checking-1", "--idempotency-key", "enter-checking",
    ]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "transitioned"
    assert first["target_identity"]["state_visit_id"].startswith("state-visit-")
    event_count = len(EventLog(workspace.events).read())

    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.checking",
        "--skill-root", str(skill), "--run-id", "run-1",
        "--target-attempt-id", "checking-1", "--idempotency-key", "enter-checking",
    ]) == 0
    assert json.loads(capsys.readouterr().out)["target_identity"] == first["target_identity"]
    assert len(EventLog(workspace.events).read()) == event_count

    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.checking",
        "--skill-root", str(skill), "--run-id", "run-1", "--state-visit-id", "different-source",
        "--target-attempt-id", "checking-1", "--idempotency-key", "enter-checking",
    ]) == 2
    assert "idempotency key conflict" in capsys.readouterr().err


@pytest.mark.parametrize("failure_stage", ["append", "commit"])
def test_transition_failure_leaves_detectable_pending_snapshot(
    tmp_path: Path,
    monkeypatch,
    capsys,
    failure_stage: str,
):
    workspace = TaskWorkspace.open(tmp_path, description=f"failure-{failure_stage}")
    skill = _make_transition_skill(tmp_path)
    original_append = EventLog.append

    if failure_stage == "append":
        def fail_append(self, event_type, **kwargs):
            if event_type == "state.transition":
                raise OSError("simulated append failure")
            return original_append(self, event_type, **kwargs)

        monkeypatch.setattr(EventLog, "append", fail_append)
    else:
        def fail_commit(self, temporary, target):
            raise OSError("simulated commit failure")

        monkeypatch.setattr(TaskWorkspace, "commit_meta_state", fail_commit)

    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.checking",
        "--skill-root", str(skill), "--run-id", "run-1",
        "--target-state-visit-id", "visit-checking-1", "--target-attempt-id", "checking-1",
    ]) == 2
    assert "simulated" in capsys.readouterr().err
    meta_state = workspace.paths("demo-skill").meta_state
    assert meta_state.with_name(meta_state.name + ".tmp").is_file()
    with pytest.raises(WorkspaceError, match="incomplete commit"):
        workspace.read_meta_state("demo-skill")

    projection = EventLog(workspace.events).projection()
    if failure_stage == "append":
        assert "demo-skill" not in projection["skill_states"]
    else:
        assert projection["skill_states"]["demo-skill"]["state_visit_id"] == "visit-checking-1"
        assert projection["skill_states"]["demo-skill"]["active_attempt_id"] == "checking-1"


def test_capability_api_and_cli_advertise_identity_protocol(capsys):
    capabilities = kernel_capabilities()
    assert capabilities["protocol"] == KERNEL_CAPABILITIES_PROTOCOL
    assert capabilities["state_identity_protocol"] == STATE_IDENTITY_PROTOCOL
    assert set(capabilities["capabilities"]) >= {
        "state_visit_identity",
        "atomic_target_identity_handoff",
        "attempt_supersede",
        "state_bound_verifier_gate",
        "state_bound_action_authorization",
        "legacy_event_read",
    }

    assert main(["capabilities"]) == 0
    assert json.loads(capsys.readouterr().out) == capabilities


def test_cli_transition_hands_off_target_identity_and_attempt_start_updates_snapshot(tmp_path: Path, capsys):
    workspace = TaskWorkspace.open(tmp_path, description="identity")
    skill = tmp_path / "demo-skill"
    for name in ("checking", "reported"):
        (skill / "states" / name).mkdir(parents=True)
    (skill / "config.yaml").write_text(
        "runtime:\n"
        "  state_roots: [states]\n"
        "  initial_state: bensz.workspace.ready\n"
        "  states: [test.demo.checking, test.demo.reported]\n",
        encoding="utf-8",
    )
    (skill / "states" / "checking" / "STATE.md").write_text(
        "---\n"
        "id: test.demo.checking\n"
        "version: 1.0.0\n"
        "entry_conditions: bensz.workspace.ready\n"
        "invariants: verifier-result-recorded\n"
        "transitions: test.demo.reported\n"
        "---\n\n# Checking\n",
        encoding="utf-8",
    )
    (skill / "states" / "reported" / "STATE.md").write_text(
        "---\n"
        "id: test.demo.reported\n"
        "version: 1.0.0\n"
        "entry_conditions: test.demo.checking\n"
        "---\n\n# Reported\n",
        encoding="utf-8",
    )

    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.checking",
        "--skill-root", str(skill), "--run-id", "run-1", "--attempt-id", "bootstrap-1",
        "--target-state-visit-id", "visit-checking-1", "--target-attempt-id", "checking-1",
        "--idempotency-key", "enter-checking-1",
    ]) == 0
    entered = json.loads(capsys.readouterr().out)
    assert entered["status"] == "transitioned"
    assert entered["target_identity"] == _identity("run-1", "visit-checking-1", "checking-1")
    assert workspace.read_meta_state("demo-skill")["active_attempt_id"] == "checking-1"
    event_count = len(EventLog(workspace.events).read())
    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.checking",
        "--skill-root", str(skill), "--run-id", "run-1", "--attempt-id", "bootstrap-1",
        "--target-state-visit-id", "visit-checking-1", "--target-attempt-id", "checking-1",
        "--idempotency-key", "enter-checking-1",
    ]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "transitioned"
    assert len(EventLog(workspace.events).read()) == event_count

    assert main([
        "attempt", "start", str(workspace.task_root), "demo-skill",
        "--run-id", "run-1", "--state-visit-id", "visit-checking-1",
        "--attempt-id", "checking-2", "--reason", "retry",
        "--idempotency-key", "start-checking-2",
    ]) == 0
    retried = json.loads(capsys.readouterr().out)
    assert retried["status"] == "started"
    assert retried["active_identity"] == _identity("run-1", "visit-checking-1", "checking-2")
    snapshot = workspace.read_meta_state("demo-skill")
    assert snapshot["active_attempt_id"] == "checking-2"
    rebuilt = EventLog(workspace.events).rebuild()
    assert rebuilt["skill_states"]["demo-skill"]["active_attempt_id"] == snapshot["active_attempt_id"]

    EventLog(workspace.events).record_verification(
        {
            "verifier_id": "test.demo.links",
            "verifier_version": "1.0.0",
            "verdict": "pass",
            "execution_status": "completed",
        },
        {"decision": "allow", "result_refs": ["test.demo.links@1.0.0"]},
        run_id="run-1",
        state_visit_id="visit-checking-1",
        attempt_id="checking-2",
    )
    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.reported",
        "--skill-root", str(skill), "--run-id", "run-1",
        "--state-visit-id", "visit-checking-1", "--attempt-id", "checking-2",
        "--target-state-visit-id", "visit-reported-1", "--target-attempt-id", "reported-1",
    ]) == 0
    reported = json.loads(capsys.readouterr().out)
    assert reported["status"] == "transitioned"
    assert reported["source_identity"] == _identity("run-1", "visit-checking-1", "checking-2")
    assert reported["target_identity"] == _identity("run-1", "visit-reported-1", "reported-1")
    projection = EventLog(workspace.events).projection()
    assert projection["skill_states"]["demo-skill"]["state_visit_id"] == "visit-reported-1"
    assert projection["skill_states"]["demo-skill"]["active_attempt_id"] == "reported-1"
