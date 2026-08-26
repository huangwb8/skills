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


def test_legacy_flags_remain_supported(tmp_path: Path):
    events = tmp_path / "events.ndjson"
    assert main(["--append-event", str(events), "--type", "task.created", "--payload", '{"state":"planned"}']) == 0
    assert main(["--status", str(events)]) == 0


def test_builtin_verifier_catalog(tmp_path: Path, capsys):
    markdown = tmp_path / "readme.md"
    markdown.write_text("# Title\n\n[ok](#title)\n", encoding="utf-8")

    assert main(["verifier", "list", "--tag", "citation"]) == 0
    catalog = json.loads(capsys.readouterr().out)
    assert catalog["verifiers"][0]["verifier_id"] == "citation.truth-and-fit"
    assert catalog["verifiers"][0]["version"] == "1.0.0"
    assert "common" in catalog["verifiers"][0]["tags"]


def test_directory_verifier_runs_markdown_link_integrity(tmp_path: Path, capsys):
    markdown = tmp_path / "readme.md"
    markdown.write_text("# Title\n\n[ok](#title)\n", encoding="utf-8")
    assert main(["verifier", "run", "markdown.link-integrity", "--input", str(markdown)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["results"][0]["verdict"] == "pass"
    assert output["gate"]["decision"] == "allow"
    assert output["summary"]["valid"] == 1
