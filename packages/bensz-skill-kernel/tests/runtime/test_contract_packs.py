import json
from pathlib import Path

import pytest

from bensz_skill_kernel import (
    ContractBindingError,
    ContractExecutionError,
    ContractPack,
    ContractPackExecutor,
    EventLog,
    FilesystemStateRegistry,
    StateContractAdapter,
    VerifierContractAdapter,
    VerifierSpec,
    execute_state,
    summarize_metrics,
)


def _pack(tmp_path: Path, *, script_verdict: str = "pass", include_human: bool = True) -> ContractPack:
    root = tmp_path / "mixed"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (root / "VERIFIER.md").write_text("# Mixed contract\n\nJudge the evidence conservatively.\n", encoding="utf-8")
    (scripts / "check.py").write_text(
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        f"json.dump({{'verdict': '{script_verdict}', 'facts': {{'schema_valid': {script_verdict == 'pass'}}}, "
        "'evidence_refs': ['subject']}, sys.stdout)\n",
        encoding="utf-8",
    )
    components = [
        {
            "id": "schema",
            "type": "script",
            "entrypoint": "scripts/check.py",
            "required": True,
            "assurance": "deterministic",
            "side_effects": "none",
        },
        {
            "id": "semantics",
            "type": "agent",
            "depends_on": ["schema"],
            "required": True,
            "assurance": "llm_judge",
            "side_effects": "none",
        },
    ]
    if include_human:
        components.append(
            {
                "id": "approval",
                "type": "human",
                "depends_on": ["semantics"],
                "required": True,
                "assurance": "human",
                "side_effects": "none",
            }
        )
    return ContractPack.from_directory(
        root,
        package_kind="verifier",
        contract_name="VERIFIER.md",
        entry={
            "id": "test.demo.mixed",
            "version": "1.0.0",
            "mode": "hybrid",
            "assurance_tier": "mixed",
            "components": components,
        },
    )


def _result(handoff, verdict: str = "pass", **extra):
    executor = {
        "type": handoff.component_type,
        "id": "reviewer-1",
    }
    if handoff.component_type == "agent":
        executor["model"] = "external-model"
    if handoff.component_type == "human":
        executor["confirmed_at"] = "2026-09-02T06:00:00Z"
    return handoff.bind_result(
        verdict=verdict,
        execution_status="completed",
        evidence_refs=("subject",),
        executor=executor,
        **extra,
    )


def test_contract_pack_hashes_plan_and_rejects_same_version_drift(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    assert pack.contract_hash.startswith("sha256:")
    assert pack.plan_hash.startswith("sha256:")
    assert [item.type for item in pack.components] == ["script", "agent", "human"]
    assert len({item.component_hash for item in pack.components}) == 3

    pending = ContractPackExecutor().execute(
        pack,
        request={"subject": {"id": "x"}, "evidence": [{"ref": "subject", "summary": "snapshot"}]},
        run_id="run-1",
        attempt_id="attempt-1",
    )
    stale = _result(next(item for item in pending.handoffs if item.component_id == "semantics"))
    (pack.root / "VERIFIER.md").write_text("# Drifted contract\n", encoding="utf-8")
    drifted = ContractPack.from_directory(
        pack.root,
        package_kind="verifier",
        contract_name="VERIFIER.md",
        entry=pack.index_entry,
    )
    with pytest.raises(ContractBindingError, match="contract hash mismatch"):
        ContractPackExecutor().execute(
            drifted,
            request={"subject": {"id": "x"}, "evidence": [{"ref": "subject", "summary": "snapshot"}]},
            submissions=(stale,),
            run_id="run-1",
            attempt_id="attempt-1",
        )


def test_legacy_entrypoint_infers_rule_mode_and_list_fields_are_strict(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (root / "VERIFIER.md").write_text("# Legacy contract\n", encoding="utf-8")
    (scripts / "verify.py").write_text(
        "import json, sys\njson.load(sys.stdin)\njson.dump({'verdict': 'pass'}, sys.stdout)\n",
        encoding="utf-8",
    )
    pack = ContractPack.from_directory(
        root,
        package_kind="verifier",
        contract_name="VERIFIER.md",
        entry={"id": "test.demo.legacy", "version": "1.0.0", "entrypoint": "scripts/verify.py"},
    )
    assert pack.mode == "rule"
    assert pack.components[0].type == "script"

    with pytest.raises(ContractExecutionError, match="aliases must be a string list"):
        ContractPack.from_directory(
            root,
            package_kind="verifier",
            contract_name="VERIFIER.md",
            entry={
                "id": "test.demo.legacy",
                "version": "1.0.0",
                "entrypoint": "scripts/verify.py",
                "aliases": "test.demo.old",
            },
        )


def test_mixed_executor_runs_script_and_prepares_bound_handoffs(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    executor = ContractPackExecutor()
    first = executor.execute(
        pack,
        request={"subject": {"id": "x"}, "context": {"scope": "local"}, "evidence": [{"ref": "subject", "summary": "snapshot"}]},
        run_id="run-1",
        attempt_id="attempt-1",
    )
    assert first.decision == "wait"
    assert [item.verdict for item in first.results] == ["pass", "unchecked", "skipped"]
    semantic = next(item for item in first.handoffs if item.component_id == "semantics")
    assert semantic.upstream_facts["schema"]["schema_valid"] is True
    assert semantic.contract_ref == "VERIFIER.md"
    assert "Judge the evidence" in semantic.instructions
    assert "instructions" not in semantic.to_audit_dict()

    second = executor.execute(
        pack,
        request={"subject": {"id": "x"}, "context": {"scope": "local"}, "evidence": [{"ref": "subject", "summary": "snapshot"}]},
        submissions=(_result(semantic),),
        run_id="run-1",
        attempt_id="attempt-1",
    )
    assert second.decision == "wait"
    human = next(item for item in second.handoffs if item.component_id == "approval")

    completed = executor.execute(
        pack,
        request={"subject": {"id": "x"}, "context": {"scope": "local"}, "evidence": [{"ref": "subject", "summary": "snapshot"}]},
        submissions=(_result(semantic), _result(human)),
        run_id="run-1",
        attempt_id="attempt-1",
    )
    assert completed.decision == "completed"
    assert all(item.verdict == "pass" for item in completed.results)
    assert completed.run_id == "run-1"
    assert completed.attempt_id == "attempt-1"


def test_required_rule_failure_cannot_be_overridden_by_agent(tmp_path: Path) -> None:
    pack = _pack(tmp_path, script_verdict="fail", include_human=False)
    executor = ContractPackExecutor()
    first = executor.execute(pack, request={"evidence": [{"ref": "subject"}]}, run_id="r", attempt_id="a")
    semantic = next(item for item in first.handoffs if item.component_id == "semantics")
    report = executor.execute(
        pack,
        request={"evidence": [{"ref": "subject"}]},
        submissions=(_result(semantic),),
        run_id="r",
        attempt_id="a",
    )
    assert [item.verdict for item in report.results] == ["fail", "pass"]
    assert report.decision == "reject"
    assert report.unresolved == ("schema",)


def test_semantic_uncertainty_and_human_wait_fail_closed(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    executor = ContractPackExecutor()
    first = executor.execute(pack, request={"evidence": [{"ref": "subject"}]}, run_id="r", attempt_id="a")
    semantic = next(item for item in first.handoffs if item.component_id == "semantics")
    report = executor.execute(
        pack,
        request={"evidence": [{"ref": "subject"}]},
        submissions=(_result(semantic, "uncertain", uncertainty_reason="insufficient context"),),
        run_id="r",
        attempt_id="a",
    )
    assert report.decision == "manual_review"
    assert report.unresolved == ("semantics", "approval")


def test_timeout_duplicate_and_cross_run_submissions_fail_closed(tmp_path: Path) -> None:
    pack = _pack(tmp_path, include_human=False)
    slow = pack.root / "scripts" / "check.py"
    slow.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
    pack = ContractPack.from_directory(
        pack.root,
        package_kind="verifier",
        contract_name="VERIFIER.md",
        entry=pack.index_entry,
    )
    timed = ContractPackExecutor().execute(pack, request={}, run_id="r", attempt_id="a", timeout=1)
    assert timed.results[0].verdict == "timed_out"
    assert timed.decision == "manual_review"

    fresh = _pack(tmp_path / "fresh", include_human=False)
    request = {"evidence": [{"ref": "subject"}]}
    pending = ContractPackExecutor().execute(fresh, request=request, run_id="r", attempt_id="a")
    handoff = next(item for item in pending.handoffs if item.component_id == "semantics")
    submission = _result(handoff)
    with pytest.raises(ContractBindingError, match="duplicate component submission"):
        ContractPackExecutor().execute(fresh, request=request, submissions=(submission, submission), run_id="r", attempt_id="a")
    with pytest.raises(ContractBindingError, match="run identity mismatch"):
        ContractPackExecutor().execute(fresh, request=request, submissions=(submission,), run_id="other", attempt_id="a")
    with pytest.raises(ContractBindingError, match="handoff binding mismatch"):
        ContractPackExecutor().execute(
            fresh,
            request={"subject": {"revision": 2}, "evidence": [{"ref": "subject"}]},
            submissions=(submission,),
            run_id="r",
            attempt_id="a",
        )
    forged_script = dict(submission)
    forged_script["component_id"] = "schema"
    with pytest.raises(ContractBindingError, match="script component"):
        ContractPackExecutor().execute(
            fresh,
            request=request,
            submissions=(forged_script,),
            run_id="r",
            attempt_id="a",
        )

    inconsistent = _result(handoff)
    inconsistent["verdict"] = "timed_out"
    with pytest.raises(ContractExecutionError, match="timed_out verdict"):
        ContractPackExecutor().execute(
            fresh,
            request=request,
            submissions=(inconsistent,),
            run_id="r",
            attempt_id="a",
        )


def test_out_of_order_submission_and_unauthorized_side_effect_fail_closed(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    executor = ContractPackExecutor()
    first = executor.execute(pack, request={"evidence": [{"ref": "subject"}]}, run_id="r", attempt_id="a")
    semantic = next(item for item in first.handoffs if item.component_id == "semantics")
    second = executor.execute(
        pack,
        request={"evidence": [{"ref": "subject"}]},
        submissions=(_result(semantic),),
        run_id="r",
        attempt_id="a",
    )
    human = next(item for item in second.handoffs if item.component_id == "approval")
    with pytest.raises(ContractBindingError, match="submission order violation"):
        executor.execute(
            pack,
            request={"evidence": [{"ref": "subject"}]},
            submissions=(_result(human),),
            run_id="r",
            attempt_id="a",
        )

    entry = dict(pack.index_entry)
    components = [dict(item) for item in entry["components"]]
    components[0]["side_effects"] = "local_write"
    entry["components"] = components
    side_effect_pack = ContractPack.from_directory(
        pack.root,
        package_kind="verifier",
        contract_name="VERIFIER.md",
        entry=entry,
    )
    denied = executor.execute(
        side_effect_pack,
        request={"evidence": [{"ref": "subject"}]},
        run_id="r",
        attempt_id="a",
    )
    assert denied.results[0].execution_status == "error"
    assert "authorization" in (denied.results[0].uncertainty_reason or "")


def test_state_and_verifier_adapters_keep_domain_semantics_separate(tmp_path: Path) -> None:
    pack = _pack(tmp_path, include_human=False)
    executor = ContractPackExecutor()
    pending = executor.execute(pack, request={"evidence": [{"ref": "subject"}]}, run_id="r", attempt_id="a")
    handoff = next(item for item in pending.handoffs if item.component_id == "semantics")
    report = executor.execute(
        pack,
        request={"evidence": [{"ref": "subject"}]},
        submissions=(_result(handoff),),
        run_id="r",
        attempt_id="a",
    )

    state = StateContractAdapter().adapt("test.demo.reviewing", report)
    assert state.state_id == "test.demo.reviewing"
    assert state.verdict == "pass"
    assert state.contract_hash == pack.contract_hash
    assert len(state.component_results) == 2

    verifier = VerifierContractAdapter().adapt(VerifierSpec("test.demo.mixed", "1.0.0", "hybrid"), report)
    assert verifier.aggregate.verdict == "pass"
    assert verifier.gate.decision == "allow"
    assert len(verifier.components) == 2
    assert verifier.aggregate.contract_hash == pack.contract_hash
    metrics = summarize_metrics(verifier.components, (verifier.gate,))
    assert metrics["component_count"] == 2
    assert metrics["bound_component_ratio"] == 1.0
    assert metrics["executor_identity_ratio"] == 1.0


def test_bound_verifier_execution_is_audit_safe_and_replayable(tmp_path: Path) -> None:
    pack = _pack(tmp_path, include_human=False)
    executor = ContractPackExecutor()
    pending = executor.execute(pack, request={"evidence": [{"ref": "subject"}]}, run_id="r", attempt_id="a")
    handoff = next(item for item in pending.handoffs if item.component_id == "semantics")
    report = executor.execute(
        pack,
        request={"evidence": [{"ref": "subject"}]},
        submissions=(_result(handoff),),
        run_id="r",
        attempt_id="a",
    )
    adapted = VerifierContractAdapter().adapt(VerifierSpec("test.demo.mixed", "1.0.0", "hybrid"), report)
    log = EventLog(tmp_path / "events.ndjson")
    result_event, gate_event = log.record_verification(
        adapted.to_event_payload(),
        adapted.gate.to_dict(),
        run_id="r",
        attempt_id="a",
        requirements=[{"verifier_id": "test.demo.mixed", "version": "1.0.0", "required": True}],
    )
    assert result_event.payload["contract_hash"] == pack.contract_hash
    assert result_event.payload["plan_hash"] == pack.plan_hash
    assert result_event.payload["execution_plan"]["plan_hash"] == pack.plan_hash
    assert len(result_event.payload["component_results"]) == 2
    assert "instructions" not in json.dumps(result_event.payload)
    assert gate_event is not None
    assert gate_event.payload["computed_by"] == "kernel"
    assert len(EventLog(tmp_path / "events.ndjson").read()) == 2


def test_kernel_rejects_forged_or_cross_run_v2_component_evidence(tmp_path: Path) -> None:
    forged = {
        "protocol": "bensz-verification-v2",
        "verifier_id": "test.demo.mixed",
        "verifier_version": "1.0.0",
        "execution_status": "completed",
        "verdict": "pass",
        "contract_hash": "sha256:" + "a" * 64,
        "plan_hash": "sha256:" + "b" * 64,
        "run_id": "r",
        "attempt_id": "a",
        "component_results": [],
    }
    _, gate = EventLog(tmp_path / "forged.ndjson").record_verification(
        forged,
        {"decision": "allow"},
        run_id="r",
        attempt_id="a",
    )
    assert gate is not None
    assert gate.payload["decision"] == "reject"
    assert gate.payload["computed_by"] == "kernel"

    pack = _pack(tmp_path / "bound", include_human=False)
    executor = ContractPackExecutor()
    pending = executor.execute(pack, request={"evidence": [{"ref": "subject"}]}, run_id="r", attempt_id="a")
    handoff = next(item for item in pending.handoffs if item.component_id == "semantics")
    report = executor.execute(
        pack,
        request={"evidence": [{"ref": "subject"}]},
        submissions=(_result(handoff),),
        run_id="r",
        attempt_id="a",
    )
    payload = VerifierContractAdapter().adapt(VerifierSpec("test.demo.mixed", "1.0.0", "hybrid"), report).to_event_payload()
    payload["component_results"][1]["run_id"] = "stale-run"
    _, gate = EventLog(tmp_path / "cross-run.ndjson").record_verification(
        payload,
        {"decision": "allow"},
        run_id="r",
        attempt_id="a",
    )
    assert gate is not None
    assert gate.payload["decision"] == "reject"

    omitted = VerifierContractAdapter().adapt(VerifierSpec("test.demo.mixed", "1.0.0", "hybrid"), report).to_event_payload()
    omitted["component_results"] = omitted["component_results"][:1]
    _, gate = EventLog(tmp_path / "omitted.ndjson").record_verification(
        omitted,
        {"decision": "allow"},
        run_id="r",
        attempt_id="a",
    )
    assert gate is not None
    assert gate.payload["decision"] == "reject"


def test_indexed_state_prepares_agent_handoff_through_common_executor(tmp_path: Path) -> None:
    root = tmp_path / "states"
    state = root / "reviewing"
    state.mkdir(parents=True)
    (state / "STATE.md").write_text(
        "# Reviewing\n\nJudge whether the phase exit conditions are satisfied.\n",
        encoding="utf-8",
    )
    (root / "index.json").write_text(
        json.dumps(
            {
                "protocol": "bensz-pack-index-v1",
                "package_kind": "state",
                "entries": [
                    {
                        "directory": "reviewing",
                        "id": "test.demo.reviewing",
                        "version": "1.0.0",
                        "contract": "STATE.md",
                        "kind": "skill",
                        "mode": "human",
                        "assurance_tier": "llm_judge",
                        "components": [
                            {
                                "id": "exit-review",
                                "type": "agent",
                                "required": True,
                                "assurance": "llm_judge",
                                "evidence_refs": ["draft"],
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    definition = FilesystemStateRegistry(root).resolve("test.demo.reviewing")
    assert definition.contract_pack().components[0].type == "agent"
    result = execute_state(
        definition,
        {
            "subject": {"phase": "reviewing"},
            "evidence": [{"ref": "draft", "summary": "draft snapshot"}],
            "context": {"run_id": "r", "attempt_id": "a"},
        },
    )
    assert result.verdict == "unchecked"
    assert result.execution_status == "pending"
    assert result.handoffs[0]["component_id"] == "exit-review"
    assert result.component_results[0]["contract_hash"] == result.contract_hash


def test_builtin_indexes_declare_execution_components() -> None:
    package = Path(__file__).parents[2] / "src" / "bensz_skill_kernel"
    for name in ("states", "verifiers"):
        index = json.loads((package / name / "index.json").read_text(encoding="utf-8"))
        for entry in index["entries"]:
            assert entry["mode"] in {"rule", "prompt", "hybrid", "human", "none"}
            assert entry["assurance_tier"] in {"deterministic", "mixed", "llm_judge", "human", "none"}
            assert isinstance(entry["components"], list)
