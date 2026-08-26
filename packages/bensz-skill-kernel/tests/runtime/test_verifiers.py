from email.message import Message
from urllib.error import HTTPError
from urllib.parse import urlparse

from bensz_skill_kernel import (
    Evidence,
    PackRegistry,
    VerifierPack,
    VerifierRunner,
    VerifierSpec,
    VerificationRequest,
    apply_gate,
)
from bensz_skill_kernel.builtins import _probe


class _RedirectingOpener:
    def __init__(self) -> None:
        self.requested_urls: list[str] = []

    def open(self, request, timeout: int):
        self.requested_urls.append(request.full_url)
        headers = Message()
        headers['Location'] = 'http://127.0.0.1/admin'
        raise HTTPError(request.full_url, 302, 'Found', headers, None)


def test_redirect_to_private_address_is_skipped_before_request(monkeypatch) -> None:
    opener = _RedirectingOpener()
    monkeypatch.setattr(
        'bensz_skill_kernel.builtins._blocked',
        lambda value, _blacklist: urlparse(value).hostname == '127.0.0.1',
    )

    result = _probe('https://public.invalid/start', 10, (), (), opener=opener)

    assert result['skipped'] is True
    assert result['reason'] == '重定向目标不在允许范围内'
    assert opener.requested_urls == ['https://public.invalid/start']


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
