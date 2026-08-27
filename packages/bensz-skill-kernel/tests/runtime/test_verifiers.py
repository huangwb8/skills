import importlib.util
from email.message import Message
from pathlib import Path
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
    builtin_verifier_root,
    FilesystemVerifierRegistry,
    VerifierDefinition,
    collect_markdown,
)
from bensz_skill_kernel.builtins import build_builtin_registry


_COLLECTOR_PATH = (
    Path(__file__).parents[2]
    / "src"
    / "bensz_skill_kernel"
    / "verifiers"
    / "markdown-link-integrity"
    / "scripts"
    / "collector.py"
)
_COLLECTOR_SPEC = importlib.util.spec_from_file_location("markdown_link_integrity_collector", _COLLECTOR_PATH)
assert _COLLECTOR_SPEC and _COLLECTOR_SPEC.loader
_COLLECTOR = importlib.util.module_from_spec(_COLLECTOR_SPEC)
_COLLECTOR_SPEC.loader.exec_module(_COLLECTOR)
_probe = _COLLECTOR._probe


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
        _COLLECTOR,
        '_blocked',
        lambda value, _blacklist: urlparse(value).hostname == '127.0.0.1',
    )

    result = _probe('https://public.invalid/start', 10, (), (), opener=opener)

    assert result['skipped'] is True
    assert result['reason'] == '重定向目标不在允许范围内'
    assert opener.requested_urls == ['https://public.invalid/start']


def test_legacy_collect_markdown_export_delegates_to_verifier_collector(tmp_path: Path) -> None:
    markdown = tmp_path / 'readme.md'
    markdown.write_text('# Title\n\n[ok](#title)\n', encoding='utf-8')

    report = collect_markdown(markdown)

    assert report['summary']['valid'] == 1
    assert report['references'][0]['validation']['local_anchor'] is True


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


def test_generic_citation_pack_is_format_agnostic_and_conservative():
    registry = build_builtin_registry()
    request = VerificationRequest(
        subject={"type": "citation"},
        evidence=(
            Evidence("subject_context", "context", {"claim": "x"}),
            Evidence("source_metadata", "metadata", {"title": "source"}),
            Evidence("source_excerpt", "excerpt", {"text": "evidence"}),
        ),
    )
    results, gate = VerifierRunner(registry).run(request, "citation.truth-and-fit", version="1.0.0")
    assert results[0].verdict == "unchecked"
    assert gate.decision == "manual_review"


def test_gate_empty_results_waits():
    assert apply_gate(()).decision == "wait"


def test_filesystem_registry_discovers_markdown_contract(tmp_path):
    verifier_dir = tmp_path / "demo"
    verifier_dir.mkdir()
    (verifier_dir / "VERIFIER.md").write_text(
        "---\n"
        "id: demo.check\n"
        "version: 1.2.0\n"
        "description: Demo verifier\n"
        "tags: demo, deterministic\n"
        "---\n\n# Instructions\n\nRun the check.\n",
        encoding="utf-8",
    )
    registry = FilesystemVerifierRegistry(tmp_path)
    definition = registry.resolve("demo.check")
    assert isinstance(definition, VerifierDefinition)
    assert definition.version == "1.2.0"
    assert definition.instructions.startswith("# Instructions")
    assert "demo" in definition.tags


def test_builtin_verifiers_are_package_assets():
    root = builtin_verifier_root()
    assert root.parent.name == "bensz_skill_kernel"
    assert (root / "markdown-link-integrity" / "VERIFIER.md").is_file()
    assert FilesystemVerifierRegistry(root).resolve("citation.truth-and-fit").version == "1.0.0"


def test_instruction_only_verifier_returns_standard_unchecked_result(tmp_path):
    verifier_dir = tmp_path / "manual"
    verifier_dir.mkdir()
    (verifier_dir / "VERIFIER.md").write_text(
        "---\nid: manual.review\nversion: 1.0.0\n---\n\n# Review\n",
        encoding="utf-8",
    )
    registry = FilesystemVerifierRegistry(tmp_path)
    result = registry.run("manual.review", {"subject": {"value": 1}})
    assert result["execution_status"] == "unchecked"
    assert result["verdict"] == "unchecked"
    assert result["verifier_id"] == "manual.review"


def test_script_verifier_uses_json_stdio_protocol(tmp_path):
    verifier_dir = tmp_path / "scripted"
    scripts = verifier_dir / "scripts"
    scripts.mkdir(parents=True)
    (verifier_dir / "VERIFIER.md").write_text(
        "---\nid: scripted.check\nversion: 1.0.0\nentrypoint: scripts/check.py\n---\n\n# Check\n",
        encoding="utf-8",
    )
    (scripts / "check.py").write_text(
        "import json, sys\n"
        "request = json.load(sys.stdin)\n"
        "json.dump({'verdict': 'pass', 'facts': {'echo': request['subject']}}, sys.stdout)\n",
        encoding="utf-8",
    )
    result = FilesystemVerifierRegistry(tmp_path).run(
        "scripted.check", {"subject": {"value": 2}, "request_id": "r1"}
    )
    assert result["execution_status"] == "completed"
    assert result["verdict"] == "pass"
    assert result["facts"]["echo"] == {"value": 2}
