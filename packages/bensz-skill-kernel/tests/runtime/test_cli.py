import json
from pathlib import Path

from bensz_skill_kernel import EventLog
from bensz_skill_kernel.cli import main


def test_skill_facing_commands_append_and_project(tmp_path: Path):
    events = tmp_path / "events.ndjson"

    assert main(["append", str(events), "task.created", "--payload", '{"state":"planned"}']) == 0
    assert main(["transition", str(events), "active"]) == 0
    assert main(["transition", str(events), "checking"]) == 0
    assert main(["artifact", str(events), "report", "--required"]) == 0
    assert main(["validation", str(events), "pass", "--evidence-ref", "snapshot:1"]) == 0
    assert main(["delivery", str(events), "report.md"]) == 0
    assert main(["status", str(events)]) == 0

    projection = EventLog(events).projection()
    assert projection["current_state"] == "checking"
    assert projection["artifacts"]["report"]["required"] is True


def test_verification_command_records_each_result_and_gate(tmp_path: Path):
    events = tmp_path / "events.ndjson"
    result = [
        {"verifier_id": "demo", "verifier_version": "1", "verdict": "pass", "execution_status": "completed", "evidence_refs": ["reference.results"]},
        {"verifier_id": "semantic", "verifier_version": "1", "verdict": "unchecked", "execution_status": "unchecked", "evidence_refs": ["markdown.snapshot"]},
    ]
    gate = {"decision": "manual_review", "reason": "semantic gap"}

    assert main([
        "verification", str(events), "--result-json", json.dumps(result), "--gate-json", json.dumps(gate),
        "--scope", "skill", "--actor", "validate-md-ref", "--attempt-id", "attempt-1",
    ]) == 0
    projection = EventLog(events).projection()
    assert [item["verdict"] for item in projection["verifications"]] == ["pass", "unchecked"]
    assert projection["gate_decisions"] == [gate]
    assert all(event.scope == "skill" and event.actor == "validate-md-ref" for event in EventLog(events).read())


def test_verification_command_binds_gate_to_all_results(tmp_path: Path):
    events = tmp_path / "events.ndjson"
    result = [
        {"verifier_id": "bensz.document.markdown-link-integrity", "verifier_version": "1.0.0", "verdict": "pass", "execution_status": "completed", "evidence_refs": ["links"]},
        {"verifier_id": "bensz.evidence.citation-truth-fit", "verifier_version": "1.0.0", "verdict": "unchecked", "execution_status": "unchecked", "evidence_refs": ["citations"]},
    ]
    gate = {"decision": "manual_review", "reason": "semantic gap"}

    assert main([
        "verification", str(events), "--result-json", json.dumps(result), "--gate-json", json.dumps(gate),
        "--scope", "skill", "--actor", "validate-md-ref", "--attempt-id", "attempt-1", "--run-id", "run-1",
    ]) == 0
    persisted = EventLog(events).read()
    gate_payload = [event.payload for event in persisted if event.event_type == "verification.gate"][-1]
    assert set(gate_payload["result_refs"]) == {
        "bensz.document.markdown-link-integrity@1.0.0",
        "bensz.evidence.citation-truth-fit@1.0.0",
    }
    assert gate_payload["result_event_id"] == persisted[-2].event_id


def test_verification_command_idempotent_retry_keeps_batch_response(tmp_path: Path, capsys):
    events = tmp_path / "events.ndjson"
    result = [{"verifier_id": "bensz.document.markdown-link-integrity", "verifier_version": "1.0.0", "verdict": "pass", "execution_status": "completed"}]
    args = ["verification", str(events), "--result-json", json.dumps(result), "--idempotency-key", "batch-1"]
    assert main(args) == 0
    capsys.readouterr()
    assert main(args) == 0
    response = json.loads(capsys.readouterr().out)
    assert len(response["events"]) == 1
    assert response["events"][0]["result_event"]["idempotency_key"] == "batch-1:0"


def test_verification_command_without_gate_does_not_append_gate(tmp_path: Path, capsys):
    events = tmp_path / "events.ndjson"
    result = [{"verifier_id": "bensz.document.markdown-link-integrity", "verifier_version": "1.0.0", "verdict": "pass", "execution_status": "completed"}]
    assert main(["verification", str(events), "--result-json", json.dumps(result)]) == 0
    capsys.readouterr()
    assert all(event.event_type != "verification.gate" for event in EventLog(events).read())


def test_legacy_flags_remain_supported(tmp_path: Path):
    events = tmp_path / "events.ndjson"
    assert main(["--append-event", str(events), "--type", "task.created", "--payload", '{"state":"planned"}']) == 0
    assert main(["--status", str(events)]) == 0


def test_builtin_verifier_catalog(tmp_path: Path, capsys):
    markdown = tmp_path / "readme.md"
    markdown.write_text("# Title\n\n[ok](#title)\n", encoding="utf-8")

    assert main(["verifier", "list", "--tag", "citation"]) == 0
    catalog = json.loads(capsys.readouterr().out)
    assert catalog["verifiers"][0]["verifier_id"] == "bensz.evidence.citation-truth-fit"
    assert catalog["verifiers"][0]["version"] == "1.0.0"
    assert "common" in catalog["verifiers"][0]["tags"]


def test_directory_verifier_runs_markdown_link_integrity(tmp_path: Path, capsys):
    markdown = tmp_path / "readme.md"
    markdown.write_text("# Title\n\n[ok](#title)\n", encoding="utf-8")
    assert main(["verifier", "run", "bensz.document.markdown-link-integrity", "--input", str(markdown)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["results"][0]["verdict"] == "pass"
    assert output["gate"]["decision"] == "allow"
    assert output["summary"]["valid"] == 1
