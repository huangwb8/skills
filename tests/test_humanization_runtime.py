"""Revision public entry integration. Synthetic reviews test protocol, not prose."""

import argparse
from dataclasses import fields
import importlib.util
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/alpha/humanization/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("revision_control", SCRIPTS / "control.py")
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)
from revision_evidence import ControlError, canonical, config, digest, load_request, parameters, validate_review
from bensz_skill_kernel import ComponentHandoff, EventLog, TaskWorkspace


@pytest.fixture
def uninitialized_case(tmp_path, monkeypatch):
    # Production readiness is confirmed by the task's actual installer call.
    # Do not contact the package index for every synthetic failure case.
    monkeypatch.setattr(control, "managed_runtime", lambda **kw: importlib.metadata.version("bensz-skill-kernel"))
    task = tmp_path / ".bensz-api/task-fixture"
    (task / "humanization/input").mkdir(parents=True)
    (task / "humanization/output").mkdir()
    (task / "humanization/input/original.txt").write_text("目前，我们计划周五提供报告。", encoding="utf-8")
    (task / "humanization/output/revised.txt").write_text("我们计划周五提供报告。", encoding="utf-8")
    request = {"original": "humanization/input/original.txt", "outcome": "revise",
               "delivery": {"text": "humanization/output/revised.txt"}}
    control.write_json(task, "humanization/input/request.json", request)
    args = argparse.Namespace(action="init", project_root=str(tmp_path), task_root=str(task),
                              request_file="humanization/input/request.json", run_id="test-run", attempt_id="edit-1", submission_file=None)
    return task, args, request


@pytest.fixture
def case(uninitialized_case):
    task, args, request = uninitialized_case
    control.execute(args)
    args.action = "release"
    return task, args, request


def synthetic_submission(task, pending):
    """Intentionally synthetic; no claim that a model executed this judgement."""
    bundle = control.read_json(task, pending["handoff_ref"])
    h = bundle["handoffs"][0]
    index = h["context"]["index"]
    fields_allowed = {f.name for f in fields(ComponentHandoff)}
    handoff = ComponentHandoff(**{k: v for k, v in h.items() if k in fields_allowed})
    texts = {"original": (task / index["original"]["ref"]).read_text(encoding="utf-8")}
    texts.update({k: (task / v["ref"]).read_text(encoding="utf-8") for k, v in index["delivery"].items()})
    audit = {key.removeprefix("require_"): {"applicability": "applicable", "reason": "synthetic protocol fixture",
             "items": [{"disposition": "reviewed", "reason": "synthetic anchor coverage",
                        "anchors": [{"artifact": k, "start": 0, "end": len(t)} for k, t in texts.items()]}]}
             for key, value in config()["quality_checks"].items() if key.startswith("require_") and value}
    facts = {"evidence_hash": bundle["evidence_hash"], "summary": "synthetic protocol result", "confidence": 0.9,
             "uncertainties": [], "audit": audit,
             "comparison": {"outcome": index["outcome"], "net_improvement": True, "reason": "synthetic comparison"},
             "rounds": [{"focus": ["expression", "safety"], "summary": "synthetic review"} for _ in range(index["parameters"]["self_eval_rounds"])],
             "lexical_explanation": "synthetic lexical review"}
    anchors = [{"artifact": k, "start": 0, "end": len(t)} for k, t in texts.items()]
    reviewer_records = []
    for i in range(3):
        reviewer_id = f"synthetic-{i}"
        ref = f"parallel-vibe/synthetic-{h['attempt_id']}/{reviewer_id}/workspace/RESULT.md"
        record = {"protocol": "humanization-review-v1", "reviewer_id": reviewer_id,
                  **{key: h[key] for key in ("run_id", "state_visit_id", "attempt_id")},
                  "evidence_hash": bundle["evidence_hash"],
                  "reviews": {row["pack_id"]: {"verdict": "pass", "summary": "synthetic protocol fixture",
                              "material_findings": []} for row in bundle["handoffs"]}}
        path = task / ref
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("```json\n" + json.dumps(record) + "\n```\n", encoding="utf-8")
        reviewer_records.append({"reviewer_id": reviewer_id, "result_ref": ref,
                                 "result_hash": digest(path.read_bytes()), "artifact_hash": bundle["evidence_hash"],
                                 "verdict": "pass"})
    facts.update(reviewers=reviewer_records, resolutions=[])
    results = []
    for row in bundle["handoffs"]:
        bound = ComponentHandoff(**{k: v for k, v in row.items() if k in fields_allowed})
        if row["pack_id"] == "bensz.prose.revision-readiness":
            component_facts = facts
        else:
            component_facts = {"evidence_hash": bundle["evidence_hash"], "summary": "synthetic defensive fixture",
                               "confidence": 0.9, "uncertainties": [], "reviewers": reviewer_records, "resolutions": [],
                               "defensive_audit": {"scope": "diagnosis" if index["outcome"] == "diagnosis" else "text",
                               "coverage": {"reason": "synthetic coverage", "anchors": anchors}, "items": [],
                               "unresolved_material_findings": []}}
        results.append(bound.bind_result(verdict="pass", facts=component_facts, evidence_refs=[row["subject"]["ref"]],
                                 executor={"type": "agent", "id": "synthetic-test", "model": "synthetic-no-model"}))
    control.write_json(task, "humanization/input/submissions.json", {"results": results})
    return results[0]



def test_complete_gate_state_replay_and_readback(case):
    task, args, _ = case
    pending = control.execute(args)
    assert pending["status"] == "pending_review"
    synthetic_submission(task, pending)
    args.submission_file = "humanization/input/submissions.json"
    ready = control.execute(args)
    assert ready["status"] == "ready"
    assert ready["gate"]["computed_by"] == "kernel"
    assert ready["transition"]["gate_binding"]["status"] == "bound"
    log = EventLog(TaskWorkspace.open_existing(task).events)
    assert log.query_transition_bindings(run_id=args.run_id, skill="humanization")[-1]["status"] == "bound"
    rebuilt = log.rebuild()
    assert rebuilt
    args.attempt_id = ready["attempt_id"]
    assert control.execute(args)["status"] == "already_ready"


def test_pending_is_idempotent_and_does_not_advance(case):
    task, args, _ = case
    first = control.execute(args)
    log = EventLog(TaskWorkspace.open_existing(task).events)
    before = len(log.read())
    second = control.execute(args)
    assert len(log.read()) == before
    assert first["gate"]["event_id"] == second["gate"]["event_id"]
    assert control.read_state(task, args.run_id)["current_state"] == "bensz.revision.working"


@pytest.mark.parametrize("verdict", ["fail", "uncertain", "unchecked", "error", "timed_out", "skipped"])
def test_nonpass_never_releases(case, verdict):
    task, args, _ = case
    pending = control.execute(args)
    result = synthetic_submission(task, pending)
    result.update(verdict=verdict, uncertainty_reason="synthetic failure")
    if verdict == "timed_out":
        result["execution_status"] = "timed_out"
    control.write_json(task, "humanization/input/submissions.json", {"results": [result]})
    args.submission_file = "humanization/input/submissions.json"
    assert control.execute(args)["status"] != "ready"
    assert control.read_state(task, args.run_id)["current_state"] == "bensz.revision.working"


@pytest.mark.parametrize("field", ["attempt_id", "state_visit_id", "handoff_hash", "contract_hash", "pack_version"])
def test_stale_binding_rejected(case, field):
    task, args, _ = case
    result = synthetic_submission(task, control.execute(args))
    result[field] = "wrong"
    control.write_json(task, "humanization/input/submissions.json", {"results": [result]})
    args.submission_file = "humanization/input/submissions.json"
    with pytest.raises(Exception):
        control.execute(args)
    assert control.read_state(task, args.run_id)["current_state"] == "bensz.revision.working"


def test_changed_candidate_and_retry_old_submission(case):
    task, args, _ = case
    result = synthetic_submission(task, control.execute(args))
    (task / "humanization/output/revised.txt").write_text("我们保证周五提供报告。", encoding="utf-8")
    with pytest.raises(ControlError, match="evidence_changed"):
        control.execute(args)
    args.action, args.attempt_id = "retry", "edit-2"
    assert control.execute(args)["status"] == "retry_started"
    args.action = "release"
    args.submission_file = "humanization/input/submissions.json"
    with pytest.raises(Exception):
        control.execute(args)


@pytest.mark.parametrize("section", ["term_table", "invariant_audit", "protected_token_diff", "boundary_disposition_table", "source_comparison"])
def test_required_audit_sections_cannot_be_omitted(case, section):
    task, args, _ = case
    result = synthetic_submission(task, control.execute(args))
    del result["facts"]["audit"][section]
    control.write_json(task, "humanization/input/submissions.json", {"results": [result]})
    args.submission_file = "humanization/input/submissions.json"
    with pytest.raises(ControlError, match="review_section_missing"):
        control.execute(args)


def test_parameter_change_requires_retry(case):
    task, args, request = case
    request["parameters"] = {"strength": "aggressive"}
    control.write_json(task, args.request_file, request)
    with pytest.raises(ControlError, match="input_changed"):
        control.execute(args)


@pytest.mark.parametrize("mode,outcome,delivery", [
    ("diagnosis_only", "diagnosis", {"diagnosis": "humanization/output/revised.txt"}),
    ("text_only", "keep_original", {"text": "humanization/output/revised.txt"}),
])
def test_diagnosis_and_keep_original_are_valid(case, mode, outcome, delivery):
    task, args, request = case
    request.update(parameters={"output_mode": mode}, outcome=outcome, delivery=delivery)
    text = (task / request["original"]).read_text(encoding="utf-8") if outcome == "keep_original" else "建议删去重复铺垫，保留计划性质。"
    (task / "humanization/output/revised.txt").write_text(text, encoding="utf-8")
    control.write_json(task, args.request_file, request)
    args.action, args.attempt_id = "retry", "edit-2"
    control.execute(args)
    args.action = "release"
    synthetic_submission(task, control.execute(args))
    args.submission_file = "humanization/input/submissions.json"
    assert control.execute(args)["status"] == "ready"


@pytest.mark.parametrize("path", ["../escape.txt", "/tmp/escape.txt", "humanization/output/../input/original.txt"])
def test_path_escape_rejected(case, path):
    task, _, request = case
    request["delivery"]["text"] = path
    control.write_json(task, "humanization/input/request.json", request)
    with pytest.raises(ControlError):
        load_request(task, "humanization/input/request.json", complete=True)


def test_symlink_and_oversized_input_rejected(case):
    task, _, request = case
    revised = task / request["delivery"]["text"]
    revised.unlink()
    revised.symlink_to(task / request["original"])
    with pytest.raises(ControlError, match="symlink"):
        load_request(task, "humanization/input/request.json", complete=True)
    revised.unlink()
    revised.write_bytes(b"x" * (config()["control_policy"]["max_text_bytes"] + 1))
    with pytest.raises(ControlError, match="oversized"):
        load_request(task, "humanization/input/request.json", complete=True)


def test_math_only_reflow_falls_back_and_rejects_structure_change(case):
    task, args, request = case
    original = "阈值为 $0.8$。\n其余条件不变。"
    (task / request["original"]).write_text(original, encoding="utf-8")
    (task / request["delivery"]["text"]).write_text(original.replace("\n", ""), encoding="utf-8")
    request["parameters"] = {"structure_mode": "reflow_plain"}
    control.write_json(task, args.request_file, request)
    with pytest.raises(ControlError, match="structure_changed"):
        load_request(task, args.request_file, complete=True)


def test_normal_english_lexical_difference_remains_reviewable(case):
    task, args, request = case
    (task / request["original"]).write_text("In order to export, click `Export`.", encoding="utf-8")
    (task / request["delivery"]["text"]).write_text("To export, click `Export`.", encoding="utf-8")
    index = load_request(task, args.request_file, complete=True)
    assert index["lexical"]["status"] == "fail"


def test_unknown_action_and_unconfirmed_runtime_fail_closed(case, monkeypatch):
    _, args, _ = case
    args.action = "unknown"
    with pytest.raises(ControlError, match="unknown_action"):
        control.execute(args)
    args.action = "release"
    monkeypatch.setattr(control, "managed_runtime", lambda **kw: "wrong-version")
    with pytest.raises(ControlError, match="runtime_update_unconfirmed"):
        control.execute(args)


@pytest.mark.parametrize("mutation", ["status", "target_state", "state_version", "snapshot_hash", "gate_binding"])
def test_transition_receipt_mismatch_is_not_accepted(case, monkeypatch, mutation):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    args.submission_file = "humanization/input/submissions.json"
    real = control.state_command
    def wrong(*a, **kw):
        response = real(*a, **kw)
        if mutation == "state_version":
            response["state"]["version"] = "0.0.0"
        elif mutation == "snapshot_hash":
            response["snapshot"]["snapshot_hash"] = "wrong"
        elif mutation == "gate_binding":
            response["gate_binding"]["status"] = "unbound"
        else:
            response[mutation] = "rejected"
        return response
    monkeypatch.setattr(control, "state_command", wrong)
    with pytest.raises(ControlError):
        control.execute(args)
    assert not (task / "humanization/log/release.json").exists()


@pytest.mark.parametrize("field", ["delivery", "attempt_id", "source_attempt_id", "gate", "transition"])
def test_ready_readback_rebuilds_untrusted_receipt(case, field):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    args.submission_file = "humanization/input/submissions.json"
    ready = control.execute(args)
    poisoned = dict(ready)
    poisoned[field] = {"forged": True} if field in {"delivery", "gate", "transition"} else "forged"
    control.write_json(task, "humanization/log/release.json", poisoned)
    args.attempt_id = ready["attempt_id"]
    recovered = control.execute(args)
    assert recovered["status"] == "already_ready"
    assert recovered["delivery"] == ready["delivery"]
    assert recovered["attempt_id"] == ready["attempt_id"]
    assert recovered["source_attempt_id"] == ready["source_attempt_id"]
    assert recovered["gate"] == ready["gate"]
    assert recovered["transition"]["gate_binding"]["status"] == "bound"


def test_transition_commit_recovers_after_receipt_write_failure(case, monkeypatch):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    args.submission_file = "humanization/input/submissions.json"
    real_write = control.write_json
    def fail_receipt(root, ref, value):
        if ref == "humanization/log/release.json":
            raise OSError("synthetic disk failure")
        real_write(root, ref, value)
    monkeypatch.setattr(control, "write_json", fail_receipt)
    with pytest.raises(OSError):
        control.execute(args)
    snapshot = control.read_state(task, args.run_id)
    assert snapshot["current_state"] == "bensz.revision.ready"
    assert not (task / "humanization/log/release.json").exists()
    monkeypatch.setattr(control, "write_json", real_write)
    args.attempt_id = snapshot["active_attempt_id"]
    assert control.execute(args)["status"] == "already_ready"


@pytest.mark.parametrize("change", ["text", "index"])
def test_ready_recovery_rejects_changed_evidence(case, change):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    args.submission_file = "humanization/input/submissions.json"
    ready = control.execute(args)
    if change == "text":
        (task / "humanization/output/revised.txt").write_text("我们保证周五提供报告。", encoding="utf-8")
    else:
        ref = "humanization/log/attempt-edit-1-evidence.json"
        index = control.read_json(task, ref)
        index["delivery"]["text"]["hash"] = "sha256:forged"
        control.write_json(task, ref, index)
    args.attempt_id = ready["attempt_id"]
    with pytest.raises(ControlError, match="evidence_changed"):
        control.execute(args)


@pytest.mark.parametrize("original", ["标题\n===\n正文。", "标题\n---\n正文。", "    code\n正文。", "\tcode\n正文。", "换行\\\\\n继续。"])
def test_reflow_fallback_preserves_newline_formats(case, original):
    task, args, request = case
    (task / request["original"]).write_text(original, encoding="utf-8")
    (task / request["delivery"]["text"]).write_text(original, encoding="utf-8")
    request["parameters"] = {"structure_mode": "reflow_plain"}
    control.write_json(task, args.request_file, request)
    index = load_request(task, args.request_file, complete=True)
    assert index["effective_structure_mode"] == "preserve"
    assert index["structure_fallback"] == "protected_markup"
    (task / request["delivery"]["text"]).write_text(original.replace("\n", ""), encoding="utf-8")
    with pytest.raises(ControlError, match="structure_changed"):
        load_request(task, args.request_file, complete=True)


def test_review_round_cap_clips_default_but_rejects_explicit_conflict():
    assert parameters({"max_self_eval_rounds": 1})["self_eval_rounds"] == 1
    with pytest.raises(ControlError, match="invalid_review_budget"):
        parameters({"max_self_eval_rounds": 1, "self_eval_rounds": 2})


def test_review_requires_all_artifacts_in_invariant_audit(case):
    task, args, _ = case
    result = synthetic_submission(task, control.execute(args))
    result["facts"]["audit"]["invariant_audit"]["items"][0]["anchors"] = [
        {"artifact": "original", "start": 0, "end": 1}]
    index = load_request(task, args.request_file, complete=True)
    with pytest.raises(ControlError, match="review_artifact_coverage_missing"):
        validate_review(result["facts"], index, task)


@pytest.mark.parametrize("stage", ["before_intent", "after_intent", "after_state", "before_commit", "after_commit"])
def test_init_interruptions_resume_one_initial_transition(uninitialized_case, monkeypatch, stage):
    task, args, _ = uninitialized_case
    real_write, real_state = control.write_json, control.state_command
    calls = 0
    def interrupted_write(root, ref, value):
        nonlocal calls
        if ref == control.SESSION:
            calls += 1
            if (stage == "before_intent" and calls == 1) or (stage == "before_commit" and calls == 2):
                raise OSError("synthetic write failure")
        real_write(root, ref, value)
        if ref == control.SESSION and ((stage == "after_intent" and calls == 1) or (stage == "after_commit" and calls == 2)):
            raise OSError("synthetic post-write failure")
    def interrupted_state(*a, **kw):
        result = real_state(*a, **kw)
        if stage == "after_state":
            raise OSError("synthetic post-transition failure")
        return result
    monkeypatch.setattr(control, "write_json", interrupted_write)
    monkeypatch.setattr(control, "state_command", interrupted_state)
    with pytest.raises(OSError):
        control.execute(args)
    monkeypatch.setattr(control, "write_json", real_write)
    monkeypatch.setattr(control, "state_command", real_state)
    assert control.execute(args)["status"] == "initialized"
    log = EventLog(TaskWorkspace.open_existing(task).events)
    assert len(log.query_transitions(run_id=args.run_id, skill="humanization")) == 1
    assert "pending_operation" not in control.read_json(task, control.SESSION)


@pytest.mark.parametrize("action", ["init", "retry"])
def test_real_process_exit_recovers_same_identity(uninitialized_case, action):
    task, args, _ = uninitialized_case
    if action == "retry":
        control.execute(args)
        args.action, args.attempt_id = "retry", "edit-2"
        (task / "humanization/input/original.txt").write_text("我们计划周五提供报告。", encoding="utf-8")
    code = '''
import argparse, importlib.metadata, json, os, sys
sys.path.insert(0, sys.argv[1])
import control
control.managed_runtime = lambda **kw: importlib.metadata.version("bensz-skill-kernel")
args = argparse.Namespace(**json.loads(sys.argv[2]))
if args.action == "init":
    real = control.state_command
    def interrupted(*a, **kw):
        real(*a, **kw)
        os._exit(73)
    control.state_command = interrupted
else:
    real = control.run_json
    def interrupted(argv, **kw):
        result = real(argv, **kw)
        if argv[1:3] == ["attempt", "start"]:
            os._exit(73)
        return result
    control.run_json = interrupted
control.execute(args)
'''
    result = subprocess.run([sys.executable, "-c", code, str(SCRIPTS), json.dumps(vars(args))], cwd=task, capture_output=True, text=True)
    assert result.returncode == 73, result.stderr
    assert control.read_json(task, control.SESSION)["pending_operation"]["action"] == action
    assert control.execute(args)["status"] in {"initialized", "retry_started"}
    log = EventLog(TaskWorkspace.open_existing(task).events)
    expected_type = "state.transition" if action == "init" else "state.attempt.started"
    assert len([e for e in log.read() if e.event_type == expected_type]) == 1
    assert control.read_state(task, args.run_id, args.attempt_id)


def test_invalid_retry_input_does_not_change_attempt(case):
    task, args, _ = case
    args.action, args.attempt_id = "retry", "edit-2"
    (task / "humanization/input/original.txt").write_text("", encoding="utf-8")
    before = control.read_json(task, control.SESSION)
    with pytest.raises(ControlError, match="empty_original"):
        control.execute(args)
    assert control.read_state(task, args.run_id)["active_attempt_id"] == "edit-1"
    assert control.read_json(task, control.SESSION) == before


@pytest.mark.parametrize("stage", ["intent", "commit"])
def test_retry_write_failure_resumes_same_attempt(case, monkeypatch, stage):
    task, args, _ = case
    args.action, args.attempt_id = "retry", "edit-2"
    (task / "humanization/input/original.txt").write_text("我们计划周五提供报告。", encoding="utf-8")
    real_write = control.write_json
    calls = 0
    def fail(root, ref, value):
        nonlocal calls
        if ref == control.SESSION:
            calls += 1
            if calls == (1 if stage == "intent" else 2):
                raise OSError("synthetic write failure")
        real_write(root, ref, value)
    monkeypatch.setattr(control, "write_json", fail)
    with pytest.raises(OSError):
        control.execute(args)
    monkeypatch.setattr(control, "write_json", real_write)
    assert control.execute(args)["status"] == "retry_started"
    assert control.execute(args)["status"] == "retry_started"
    log = EventLog(TaskWorkspace.open_existing(task).events)
    assert len([e for e in log.read() if e.event_type == "state.attempt.started"]) == 1


@pytest.mark.parametrize("mismatch", ["run_id", "attempt_id", "request_file", "input", "assets", "runtime"])
def test_pending_init_rejects_binding_mismatch(uninitialized_case, monkeypatch, mismatch):
    task, args, _ = uninitialized_case
    real = control.state_command
    monkeypatch.setattr(control, "state_command", lambda *a, **kw: (_ for _ in ()).throw(OSError("synthetic failure")))
    with pytest.raises(OSError):
        control.execute(args)
    monkeypatch.setattr(control, "state_command", real)
    if mismatch in {"run_id", "attempt_id", "request_file"}:
        setattr(args, mismatch, "wrong")
    elif mismatch == "input":
        (task / "humanization/input/original.txt").write_text("不同原文。", encoding="utf-8")
    else:
        data = control.read_json(task, control.SESSION)
        data["asset_hashes" if mismatch == "assets" else "runtime_version"] = "wrong"
        control.write_json(task, control.SESSION, data)
    with pytest.raises(Exception):
        control.execute(args)
    assert not EventLog(TaskWorkspace.open_existing(task).events).query_transitions(run_id="test-run", skill="humanization")


@pytest.mark.parametrize("alias", ["same", "slashes", "hardlink"])
def test_delivery_artifacts_must_be_distinct_files(case, alias):
    task, args, request = case
    request["parameters"] = {"output_mode": "text_with_change_summary"}
    text = request["delivery"]["text"]
    if alias == "hardlink":
        request["delivery"]["summary"] = "humanization/output/summary.txt"
        (task / request["delivery"]["summary"]).hardlink_to(task / text)
    else:
        request["delivery"]["summary"] = text if alias == "same" else text.replace("output/", "output//")
    control.write_json(task, args.request_file, request)
    with pytest.raises(ControlError):
        load_request(task, args.request_file, complete=True)


@pytest.mark.parametrize("action", ["init", "retry"])
@pytest.mark.parametrize("replace_number", [1, 2])
def test_session_atomic_replace_failure_is_resumable(uninitialized_case, monkeypatch, action, replace_number):
    task, args, _ = uninitialized_case
    if action == "retry":
        control.execute(args)
        args.action, args.attempt_id = "retry", "edit-2"
    real_replace = Path.replace
    count = 0
    def fail_replace(path, target):
        nonlocal count
        if path.name == "control-session.json.pending":
            count += 1
            if count == replace_number:
                raise OSError("synthetic replace failure")
        return real_replace(path, target)
    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError):
        control.execute(args)
    monkeypatch.setattr(Path, "replace", real_replace)
    assert control.execute(args)["status"] in {"initialized", "retry_started"}
    assert control.read_state(task, args.run_id, args.attempt_id)


@pytest.mark.parametrize("mismatch", ["source", "target", "input"])
def test_pending_retry_refuses_other_identity_or_input(case, monkeypatch, mismatch):
    task, args, _ = case
    args.action, args.attempt_id = "retry", "edit-2"
    real = control.run_json
    def fail_start(argv, **kw):
        if argv[1:3] == ["attempt", "start"]:
            raise OSError("synthetic pre-attempt failure")
        return real(argv, **kw)
    monkeypatch.setattr(control, "run_json", fail_start)
    with pytest.raises(OSError):
        control.execute(args)
    monkeypatch.setattr(control, "run_json", real)
    if mismatch == "source":
        data = control.read_json(task, control.SESSION)
        data["pending_operation"]["source"]["state_visit_id"] = "wrong"
        control.write_json(task, control.SESSION, data)
    elif mismatch == "target":
        args.attempt_id = "edit-3"
    else:
        (task / "humanization/input/original.txt").write_text("另一原文。", encoding="utf-8")
    with pytest.raises(ControlError):
        control.execute(args)
    assert control.read_state(task, args.run_id)["active_attempt_id"] == "edit-1"


def test_pack_execution_script_is_bound_to_session_contract(case, monkeypatch):
    task, args, _ = case
    ref = "references/verifiers/revision-readiness/scripts/verify.py"
    hashes = control.asset_hashes()
    assert ref in hashes
    monkeypatch.setattr(control, "asset_hashes", lambda: {**hashes, ref: "sha256:changed"})
    with pytest.raises(ControlError, match="runtime_contract_drift"):
        control.execute(args)


@pytest.mark.parametrize("pack_index", [0, 1])
@pytest.mark.parametrize("verdict", [None, "fail", "uncertain", "unchecked"])
def test_both_required_reviews_must_pass(case, pack_index, verdict):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    bundle = control.read_json(task, "humanization/input/submissions.json")
    if verdict is None:
        bundle["results"].pop(pack_index)
    else:
        bundle["results"][pack_index].update(verdict=verdict, uncertainty_reason="synthetic nonpass")
    control.write_json(task, "humanization/input/submissions.json", bundle)
    args.submission_file = "humanization/input/submissions.json"
    assert control.execute(args)["status"] != "ready"
    assert control.read_state(task, args.run_id)["current_state"] == "bensz.revision.working"


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "hash", "old_attempt", "fake_vote", "empty_coverage", "fake_anchor", "wrong_schema"])
def test_defensive_evidence_cannot_fake_pass(case, mutation):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    bundle = control.read_json(task, "humanization/input/submissions.json")
    facts = bundle["results"][1]["facts"]
    if mutation == "missing":
        facts["reviewers"].pop()
    elif mutation == "duplicate":
        facts["reviewers"][2] = facts["reviewers"][0]
    elif mutation == "hash":
        facts["reviewers"][0]["result_hash"] = "sha256:wrong"
    elif mutation == "fake_vote":
        facts["reviewers"][0]["verdict"] = "fail"
    elif mutation == "old_attempt":
        reviewer = facts["reviewers"][0]
        path = task / reviewer["result_ref"]
        path.write_text(path.read_text().replace('"attempt_id": "edit-1"', '"attempt_id": "edit-old"'))
        for result in bundle["results"]:
            result["facts"]["reviewers"][0]["result_hash"] = digest(path.read_bytes())
    elif mutation == "empty_coverage":
        facts["defensive_audit"]["coverage"] = {}
    elif mutation == "fake_anchor":
        facts["defensive_audit"]["coverage"]["anchors"][0]["end"] = 999999
    else:
        bundle["results"][1]["facts"] = bundle["results"][0]["facts"]
    control.write_json(task, "humanization/input/submissions.json", bundle)
    args.submission_file = "humanization/input/submissions.json"
    with pytest.raises(ControlError):
        control.execute(args)
    assert control.read_state(task, args.run_id)["current_state"] == "bensz.revision.working"


def dissent(task, bundle, *, material=True):
    reviewer = bundle["results"][0]["facts"]["reviewers"][2]
    path = task / reviewer["result_ref"]
    record = json.loads(path.read_text().split("```json\n")[1].split("\n```")[0])
    anchors = [{"artifact": "original", "start": 0, "end": 2}, {"artifact": "text", "start": 0, "end": 2}]
    for opinion in record["reviews"].values():
        opinion.update(verdict="fail", summary="synthetic dissent", material_findings=[
            {"id": "lost-condition", "reason": "synthetic allegation", "anchors": anchors}] if material else [])
    path.write_text("```json\n" + json.dumps(record) + "\n```\n")
    for result in bundle["results"]:
        result["facts"]["reviewers"][2].update(result_hash=digest(path.read_bytes()), verdict="fail")
    return anchors


def test_majority_cannot_silence_material_dissent(case):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    bundle = control.read_json(task, "humanization/input/submissions.json")
    anchors = dissent(task, bundle)
    control.write_json(task, "humanization/input/submissions.json", bundle)
    args.submission_file = "humanization/input/submissions.json"
    with pytest.raises(ControlError, match="unresolved_material_finding"):
        control.execute(args)
    assert control.read_state(task, args.run_id)["current_state"] == "bensz.revision.working"
    for result in bundle["results"]:
        result["facts"]["resolutions"] = [{"reviewer_id": "synthetic-2", "finding_id": "lost-condition",
            "disposition": "dismissed", "reason": "Synthetic anchored dismissal, not proof of semantic truth", "anchors": anchors}]
    control.write_json(task, "humanization/input/submissions.json", bundle)
    assert control.execute(args)["status"] == "ready"


def test_style_dissent_does_not_have_unlimited_veto(case):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    bundle = control.read_json(task, "humanization/input/submissions.json")
    dissent(task, bundle, material=False)
    control.write_json(task, "humanization/input/submissions.json", bundle)
    args.submission_file = "humanization/input/submissions.json"
    assert control.execute(args)["status"] == "ready"


def test_readback_rechecks_reviewer_file_hash(case):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    bundle = control.read_json(task, "humanization/input/submissions.json")
    args.submission_file = "humanization/input/submissions.json"
    ready = control.execute(args)
    reviewer = bundle["results"][0]["facts"]["reviewers"][0]
    (task / reviewer["result_ref"]).write_text("changed reviewer record")
    args.attempt_id = ready["attempt_id"]
    with pytest.raises(ControlError, match="reviewer_hash_mismatch"):
        control.execute(args)


def test_defensive_hints_do_not_reject_necessary_limits(case):
    task, args, request = case
    text = "可能存在关联，但并不意味着因果。The estimate may be biased."
    (task / request["original"]).write_text(text)
    (task / request["delivery"]["text"]).write_text(text)
    request["outcome"] = "keep_original"
    control.write_json(task, args.request_file, request)
    args.action, args.attempt_id = "retry", "edit-2"
    control.execute(args)
    args.action = "release"
    pending = control.execute(args)
    assert pending["status"] == "pending_review"
    log = EventLog(TaskWorkspace.open_existing(task).events)
    result = [e for e in log.read() if e.event_type == "verification.result" and e.payload.get("verifier_id") == "bensz.prose.defensive-framing"][-1]
    component = next(c for c in result.payload["component_results"] if c["component_id"] == "defensive-facts")
    assert component["verdict"] == "pass"
    assert component["facts"]["clues"]
    assert component["facts"]["semantic_status"] == "unchecked"
    synthetic_submission(task, pending)
    args.submission_file = "humanization/input/submissions.json"
    assert control.execute(args)["status"] == "ready"


@pytest.mark.parametrize("category,action", [("necessary", "delete"), ("mixed", "delete"), ("unresolved", "human_review")])
def test_defensive_pass_cannot_erase_or_ignore_uncertain_function(case, category, action):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    bundle = control.read_json(task, "humanization/input/submissions.json")
    bundle["results"][1]["facts"]["defensive_audit"]["items"] = [{
        "pattern": "synthetic", "necessity": category, "disposition": action,
        "materiality_reason": "synthetic", "preserved_function": "synthetic", "material": False,
        "source_anchors": [{"artifact": "original", "start": 0, "end": 2}],
        "candidate_anchors": [{"artifact": "text", "start": 0, "end": 2}],
        "preserved_anchors": [{"artifact": "text", "start": 0, "end": 2}]}]
    control.write_json(task, "humanization/input/submissions.json", bundle)
    args.submission_file = "humanization/input/submissions.json"
    with pytest.raises(ControlError):
        control.execute(args)


def test_clue_output_is_bounded_without_semantic_verdict():
    path = SCRIPTS.parent / "references/verifiers/defensive-framing/scripts/evidence.py"
    spec = importlib.util.spec_from_file_location("defensive_evidence_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.collect_clues({"original": "may " * 40000, "text": "may " * 40000})
    assert result["clue_count"] == 80000
    assert len(result["clues"]) == config()["control_policy"]["max_defensive_clues"]
    assert result["clues_truncated"] is True
    assert len(canonical(result)) < 65536


def test_reviewers_cannot_use_hardlinks_as_independent_votes(case):
    task, args, _ = case
    synthetic_submission(task, control.execute(args))
    bundle = control.read_json(task, "humanization/input/submissions.json")
    refs = bundle["results"][0]["facts"]["reviewers"]
    first, second = task / refs[0]["result_ref"], task / refs[1]["result_ref"]
    second.unlink()
    second.hardlink_to(first)
    for result in bundle["results"]:
        result["facts"]["reviewers"][1]["result_hash"] = digest(first.read_bytes())
    control.write_json(task, "humanization/input/submissions.json", bundle)
    args.submission_file = "humanization/input/submissions.json"
    with pytest.raises(ControlError, match="duplicate_reviewer"):
        control.execute(args)
