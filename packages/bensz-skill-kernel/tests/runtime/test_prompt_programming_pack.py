import json
from pathlib import Path

from bensz_skill_kernel.states import FilesystemStateRegistry, SkillStateDeclaration, check_state_invariants
from bensz_skill_kernel.verifiers import FilesystemVerifierRegistry


ROOT = Path(__file__).parents[3] / ".." / "skills" / "beta" / "prompt-programming"


def test_prompt_programming_state_pack_matches_s_prompt() -> None:
    registry = FilesystemStateRegistry(ROOT / "references" / "states")
    assert {item.id for item in registry.definitions()} == {
        "bensz.prompt-programming.draft",
        "bensz.prompt-programming.schema-valid",
        "bensz.prompt-programming.reviewed",
        "bensz.prompt-programming.published",
    }
    assert registry.resolve("prompt-programming.reviewed").id == "bensz.prompt-programming.reviewed"


def test_prompt_contract_verifier_canonical_alias_and_fail_closed() -> None:
    registry = FilesystemVerifierRegistry(ROOT / "references" / "verifiers")
    request = {"subject": {"program": "目标：x\n输入：x\n输出：x\n流程：若满足则执行\n校验：核对\n返回：上述输出"}}
    assert registry.run("bensz.prompt.contract-conformance", request, version="1.0.0")["verdict"] == "pass"
    assert registry.resolve("prompt-programming.contract-conformance", "1.0.0").verifier_id == "bensz.prompt.contract-conformance"
    result = registry.run("bensz.prompt.contract-conformance", {"subject": {"program": "目标：x"}}, version="1.0.0")
    assert result["verdict"] == "fail"
    assert any(item["code"] == "missing-block" for item in result["findings"])


def test_prompt_semantic_verifier_is_declared_as_ai_judge() -> None:
    registry = FilesystemVerifierRegistry(ROOT / "references" / "verifiers")
    definition = registry.resolve("bensz.prompt.semantic-equivalence", "1.0.0")
    assert definition.spec.mode == "prompt"
    assert definition.spec.assurance_tier == "llm_judge"
    assert definition.spec.prompt_pack_ref == "PROMPT.md"
    assert registry.resolve("prompt-programming.semantic-equivalence", "1.0.0").verifier_id == "bensz.prompt.semantic-equivalence"
    result = registry.run(
        "bensz.prompt.semantic-equivalence",
        {"subject": {"source_prompt": "原始任务", "program": "目标：保留任务"}, "context": {"rubric_version": "1.0"}},
        version="1.0.0",
    )
    assert result["verdict"] == "unchecked"
    assert result["execution_status"] == "unchecked"


def test_prompt_skill_runtime_declares_local_verifiers() -> None:
    declaration = SkillStateDeclaration.from_skill_root(ROOT)
    requirements = {item["id"] for item in declaration.verifier_requirements()}
    assert requirements == {
        "bensz.prompt.contract-conformance",
        "bensz.prompt.semantic-equivalence",
    }


def test_required_verifier_invariant_rejects_missing_ai_result() -> None:
    definition = FilesystemStateRegistry(ROOT / "references" / "states").resolve("bensz.prompt-programming.schema-valid")
    context = {
        "run_id": "run-1",
        "attempt_id": "attempt-1",
        "required_verifiers": [
            {"id": "bensz.prompt.contract-conformance", "version": "1.0.0"},
            {"id": "bensz.prompt.semantic-equivalence", "version": "1.0.0"},
        ],
    }
    structural_result = {
        "type": "verification.result", "run_id": "run-1", "attempt_id": "attempt-1",
        "payload": {"verifier_id": "bensz.prompt.contract-conformance", "verifier_version": "1.0.0", "execution_status": "completed", "verdict": "pass"},
    }
    gate = {
        "type": "verification.gate", "run_id": "run-1", "attempt_id": "attempt-1",
        "payload": {"decision": "allow", "result_refs": ["bensz.prompt.contract-conformance@1.0.0"]},
    }
    failures = check_state_invariants(definition, (structural_result, gate), context=context)
    assert any("bensz.prompt.semantic-equivalence@1.0.0" in item for item in failures)


def test_prompt_pack_indexes_are_declared_and_json_valid() -> None:
    for path in (ROOT / "references" / "states" / "index.json", ROOT / "references" / "verifiers" / "index.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["protocol"] == "bensz-pack-index-v1"
        assert payload["entries"]
