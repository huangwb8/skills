import json
import io
from pathlib import Path

from bensz_skill_kernel import EventLog
from bensz_skill_kernel.cli import main


def _write_demo_verifier(root: Path) -> None:
    pack = root / "demo"
    script = pack / "scripts" / "verify.py"
    script.parent.mkdir(parents=True)
    (pack / "VERIFIER.md").write_text("# Demo verifier\n", encoding="utf-8")
    script.write_text(
        "import json, sys\n"
        "request = json.load(sys.stdin)\n"
        "value = request.get('subject', {}).get('value')\n"
        "json.dump({'verdict': 'pass' if value == 7 else 'fail', 'facts': {'value': value}}, sys.stdout)\n",
        encoding="utf-8",
    )
    (root / "index.json").write_text(
        json.dumps({
            "protocol": "bensz-pack-index-v1", "package_kind": "verifier",
            "entries": [{
                "directory": "demo", "id": "test.demo.check", "version": "1.0.0",
                "classification": "domain", "tags": ["demo"], "contract": "VERIFIER.md",
                "mode": "rule", "assurance_tier": "deterministic",
                "components": [{"id": "check", "type": "script", "entrypoint": "scripts/verify.py", "required": True}],
            }],
        }),
        encoding="utf-8",
    )


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


def test_verifier_cli_loads_explicit_root_and_accepts_json_request(tmp_path: Path, capsys):
    root = tmp_path / "verifiers"
    _write_demo_verifier(root)
    assert main([
        "verifier", "run", "test.demo.check", "--root", str(root),
        "--request-json", json.dumps({"subject": {"value": 7}}),
    ]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["results"][0]["verdict"] == "pass"
    assert output["metrics"]["component_count"] == 1
    assert output["metrics"]["bound_component_ratio"] == 1.0


def test_verifier_cli_accepts_request_file_from_stdin_and_preserves_attempt_id(tmp_path: Path, capsys, monkeypatch):
    root = tmp_path / "verifiers"
    _write_demo_verifier(root)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"subject": {"value": 7}, "attempt_id": "attempt-json"})))

    assert main([
        "verifier", "run", "test.demo.check", "--root", str(root),
        "--request-file", "-",
    ]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["results"][0]["attempt_id"] == "attempt-json"


def test_action_cli_preflight_and_consume(tmp_path: Path, capsys):
    events = tmp_path / "events.ndjson"
    log = EventLog(events)
    log.append(
        "state.transition",
        payload={
            "state_domain": "skill",
            "skill": "demo-skill",
            "from_state": "test.demo.preparing",
            "to_state": "test.demo.ready",
            "state_version": "1.2.0",
            "snapshot_hash": "a" * 64,
        },
        scope="skill",
        run_id="run-1",
        attempt_id="attempt-1",
    )

    assert main([
        "action", "preflight", str(events), "demo-skill", "publish-report",
        "--state", "test.demo.ready", "--state-version", "1.2.0",
        "--run-id", "run-1", "--attempt-id", "attempt-1",
        "--idempotency-key", "authorize-publish",
    ]) == 0
    granted = json.loads(capsys.readouterr().out)
    assert granted["payload"]["decision"] == "allow"

    assert main([
        "action", "consume", str(events), granted["payload"]["authorization_id"],
        "demo-skill", "publish-report", "--run-id", "run-1",
        "--attempt-id", "attempt-1", "--idempotency-key", "consume-publish",
    ]) == 0
    consumed = json.loads(capsys.readouterr().out)
    assert consumed["type"] == "action.authorization.consumed"


def test_verifier_cli_rejects_combined_root_and_skill_root(tmp_path: Path, capsys):
    root = tmp_path / "verifiers"
    _write_demo_verifier(root)
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "config.yaml").write_text("runtime:\n  verifiers: []\n", encoding="utf-8")

    assert main(["verifier", "list", "--root", str(root), "--skill-root", str(skill)]) == 2
    assert "cannot be combined" in capsys.readouterr().err


def test_verifier_cli_skill_root_enforces_declaration_and_advisory_gate(tmp_path: Path, capsys):
    skill = tmp_path / "skill"
    root = skill / "references" / "verifiers"
    _write_demo_verifier(root)
    (skill / "config.yaml").write_text(
        "runtime:\n"
        "  verifier_roots: [references/verifiers]\n"
        "  verifiers:\n"
        "    - id: test.demo.check\n"
        "      version: 1.0.0\n"
        "      required: false\n",
        encoding="utf-8",
    )
    events = tmp_path / "events.ndjson"
    assert main([
        "verifier", "run", "test.demo.check", "--skill-root", str(skill),
        "--request-json", json.dumps({"subject": {"value": 8}}),
        "--events", str(events),
    ]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["results"][0]["verdict"] == "fail"
    assert output["gate"]["decision"] == "allow_with_warnings"
    assert output["metrics"]["verifier_count"] == 0
    assert output["metrics"]["required_coverage"] == 0.0
    gate = [event for event in EventLog(events).read() if event.event_type == "verification.gate"][-1]
    assert gate.payload["decision"] == "allow_with_warnings"


def test_verifier_cli_skill_root_rejects_undeclared_verifier(tmp_path: Path, capsys):
    skill = tmp_path / "skill"
    root = skill / "references" / "verifiers"
    _write_demo_verifier(root)
    (skill / "config.yaml").write_text(
        "runtime:\n  verifier_roots: [references/verifiers]\n  verifiers: []\n",
        encoding="utf-8",
    )
    assert main([
        "verifier", "run", "test.demo.check", "--skill-root", str(skill),
        "--request-json", json.dumps({"subject": {"value": 7}}),
    ]) == 2
    assert "not declared" in capsys.readouterr().err


def test_directory_verifier_persists_the_gate_returned_by_cli(tmp_path: Path, capsys):
    subject = tmp_path / "artifact.txt"
    subject.write_text("ready\n", encoding="utf-8")
    events = tmp_path / "events.ndjson"

    assert main([
        "verifier", "run", "bensz.artifact.file-existence",
        "--input", str(subject),
        "--events", str(events),
        "--run-id", "run-1",
        "--attempt-id", "attempt-1",
    ]) == 0

    output = json.loads(capsys.readouterr().out)
    persisted_gate = [
        event.payload
        for event in EventLog(events).read()
        if event.event_type == "verification.gate"
    ][-1]
    assert persisted_gate["decision"] == output["gate"]["decision"] == "allow"
    assert persisted_gate["reason"] == output["gate"]["reason"]
    assert persisted_gate["result_refs"] == output["gate"]["result_refs"]


def test_semantic_verifier_cli_returns_bound_agent_handoff(tmp_path: Path, capsys):
    markdown = tmp_path / "claim.md"
    events = tmp_path / "events.ndjson"
    markdown.write_text("A claim with a citation.\n", encoding="utf-8")
    assert main([
        "verifier", "run", "bensz.evidence.citation-truth-fit",
        "--input", str(markdown),
        "--events", str(events),
        "--run-id", "run-1",
    ]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["gate"]["decision"] == "wait"
    persisted_gate = [
        event.payload
        for event in EventLog(events).read()
        if event.event_type == "verification.gate"
    ][-1]
    assert persisted_gate["decision"] == output["gate"]["decision"]
    assert persisted_gate["reason"] == output["gate"]["reason"]
    assert output["handoffs"][0]["component_id"] == "citation-semantics"
    assert output["handoffs"][0]["run_id"] == "run-1"
    assert "instructions" in output["handoffs"][0]
    assert "instructions" not in output["results"][0]
