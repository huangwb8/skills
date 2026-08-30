import json
from pathlib import Path

from bensz_skill_kernel.states import FilesystemStateRegistry
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


def test_prompt_pack_indexes_are_declared_and_json_valid() -> None:
    for path in (ROOT / "references" / "states" / "index.json", ROOT / "references" / "verifiers" / "index.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["protocol"] == "bensz-pack-index-v1"
        assert payload["entries"]
