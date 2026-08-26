from bensz_skill_kernel import (
    Evidence,
    PackRegistry,
    VerifierPack,
    VerifierRunner,
    VerifierSpec,
    VerificationRequest,
    apply_gate,
)


def test_hybrid_pack_preserves_rule_failure_and_prompt_gap():
    spec = VerifierSpec("demo.v1", "1.0.0", "hybrid", evidence_requirements=("subject",))
    pack = VerifierPack(
        spec,
        rules=(("schema", lambda request, evidence: {"verdict": "fail", "findings": [{"id": "bad"}]}),),
        prompts=(("rubric", lambda request, evidence: {"verdict": "pass", "confidence": 0.8}),),
    )
    registry = PackRegistry()
    registry.register(pack)
    results, gate = VerifierRunner(registry).run(
        VerificationRequest(subject={"id": "x"}, evidence=(Evidence("subject", "snapshot", {"id": "x"}),)),
        "demo.v1",
    )
    assert [result.verdict for result in results] == ["fail", "pass"]
    assert gate.decision == "reject"


def test_missing_evidence_cannot_pass():
    spec = VerifierSpec("needs.v1", "1.0.0", "rule", evidence_requirements=("required",))
    registry = PackRegistry()
    registry.register(VerifierPack(spec, rules=(("rule", lambda *_: {"verdict": "pass"}),)))
    results, gate = VerifierRunner(registry).run(VerificationRequest(subject={}), "needs.v1")
    assert results[0].verdict == "unchecked"
    assert gate.decision == "manual_review"


def test_gate_empty_results_waits():
    assert apply_gate(()).decision == "wait"
