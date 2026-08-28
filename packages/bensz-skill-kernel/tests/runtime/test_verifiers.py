import importlib.util
import json
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
    validate_verifier_id,
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
    spec = VerifierSpec("test.demo.hybrid", "1.0.0", "hybrid", evidence_requirements=("subject",))
    pack = VerifierPack(
        spec,
        rules=(("schema", lambda request, evidence: {"verdict": "fail", "findings": [{"id": "bad"}]}),),
        prompts=(("rubric", lambda request, evidence: {"verdict": "pass", "confidence": 0.8}),),
    )
    registry = PackRegistry()
    registry.register(pack)
    results, gate = VerifierRunner(registry).run(
        VerificationRequest(subject={"id": "x"}, evidence=(Evidence("subject", "snapshot", {"id": "x"}),)),
        "test.demo.hybrid",
    )
    assert [result.verdict for result in results] == ["fail", "pass"]
    assert gate.decision == "reject"


def test_missing_evidence_cannot_pass():
    spec = VerifierSpec("test.needs.evidence", "1.0.0", "rule", evidence_requirements=("required",))
    registry = PackRegistry()
    registry.register(VerifierPack(spec, rules=(("rule", lambda *_: {"verdict": "pass"}),)))
    results, gate = VerifierRunner(registry).run(VerificationRequest(subject={}), "test.needs.evidence")
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
    results, gate = VerifierRunner(registry).run(request, "bensz.evidence.citation-truth-fit", version="1.0.0")
    assert results[0].verdict == "unchecked"
    assert gate.decision == "manual_review"


def test_builtin_pack_alias_resolves_to_canonical_result() -> None:
    request = VerificationRequest(
        subject={"type": "citation"},
        evidence=(
            Evidence("subject_context", "context", {"claim": "x"}),
            Evidence("source_metadata", "metadata", {"title": "source"}),
            Evidence("source_excerpt", "excerpt", {"text": "evidence"}),
        ),
    )
    results, _ = VerifierRunner(build_builtin_registry()).run(request, "citation.truth-and-fit")
    assert results[0].verifier_id == "bensz.evidence.citation-truth-fit"


def test_gate_empty_results_waits():
    assert apply_gate(()).decision == "wait"


def test_filesystem_registry_discovers_markdown_contract(tmp_path):
    verifier_dir = tmp_path / "demo"
    verifier_dir.mkdir()
    (verifier_dir / "VERIFIER.md").write_text(
        "---\n"
        "id: test.demo.check\n"
        "version: 1.2.0\n"
        "description: Demo verifier\n"
        "tags: demo, deterministic\n"
        "---\n\n# Instructions\n\nRun the check.\n",
        encoding="utf-8",
    )
    registry = FilesystemVerifierRegistry(tmp_path)
    definition = registry.resolve("test.demo.check")
    assert isinstance(definition, VerifierDefinition)
    assert definition.version == "1.2.0"
    assert definition.instructions.startswith("# Instructions")
    assert "demo" in definition.tags


def test_builtin_verifiers_are_package_assets():
    root = builtin_verifier_root()
    assert root.parent.name == "bensz_skill_kernel"
    assert (root / "markdown-link-integrity" / "VERIFIER.md").is_file()
    registry = FilesystemVerifierRegistry(root)
    assert registry.resolve("bensz.evidence.citation-truth-fit").version == "1.0.0"
    assert {spec.verifier_id for spec in registry.specs()} == {
        "bensz.artifact.file-existence",
        "bensz.document.markdown-link-integrity",
        "bensz.evidence.citation-truth-fit",
        "bensz.contract.conformance",
        "bensz.artifact.path-scope",
        "bensz.artifact.schema-conformance",
        "bensz.source.diff-scope",
        "bensz.security.secret-redaction",
        "bensz.evidence.provenance",
        "bensz.runtime.event-integrity",
        "bensz.runtime.state-transition",
        "bensz.runtime.task-completeness",
    }


def test_filesystem_atomic_verifier_executes_from_its_own_directory() -> None:
    result = FilesystemVerifierRegistry(builtin_verifier_root()).run(
        "bensz.security.secret-redaction",
        {"subject": {"token": "secret-value"}},
        version="1.0.0",
    )
    assert result["verdict"] == "fail"


def test_filesystem_provenance_verifier_rejects_incomplete_evidence() -> None:
    result = FilesystemVerifierRegistry(builtin_verifier_root()).run(
        "bensz.evidence.provenance",
        {
            "subject": {},
            "evidence": [{"ref": "source", "source_type": "web", "content_hash": "", "collected_at": ""}],
        },
        version="1.0.0",
    )
    assert result["verdict"] == "fail"


def test_builtin_verifier_index_drives_tags_and_classification() -> None:
    root = builtin_verifier_root()
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    assert index["protocol"] == "bensz-pack-index-v1"
    assert index["package_kind"] == "verifier"
    assert all("/" not in item["directory"] for item in index["entries"])
    registry = FilesystemVerifierRegistry(root)
    secret = registry.resolve("bensz.security.secret-redaction")
    citation = registry.resolve("bensz.evidence.citation-truth-fit")
    assert secret.classification == "atomic"
    assert citation.classification == "semantic"
    assert {item.verifier_id for item in registry.definitions(tag="security")} == {
        "bensz.artifact.path-scope",
        "bensz.security.secret-redaction",
    }
    assert not (secret.path / "VERIFIER.md").read_text(encoding="utf-8").startswith("---")


def test_markdown_verifier_resolves_relative_files_and_fragments(tmp_path: Path):
    target = tmp_path / "README.md"
    linked = tmp_path / "docs" / "guide.md"
    linked.parent.mkdir()
    linked.write_text("# Install\n", encoding="utf-8")
    target.write_text("[guide](docs/guide.md#install)\n", encoding="utf-8")
    result = FilesystemVerifierRegistry(builtin_verifier_root()).run(
        "bensz.document.markdown-link-integrity",
        {"subject": {"path": str(target)}, "context": {}},
        version="1.0.0",
    )
    assert result["verdict"] == "pass"
    assert result["facts"]["summary"]["valid"] == 1


def test_instruction_only_verifier_returns_standard_unchecked_result(tmp_path):
    verifier_dir = tmp_path / "manual"
    verifier_dir.mkdir()
    (verifier_dir / "VERIFIER.md").write_text(
        "---\nid: test.manual.review\nversion: 1.0.0\n---\n\n# Review\n",
        encoding="utf-8",
    )
    registry = FilesystemVerifierRegistry(tmp_path)
    result = registry.run("test.manual.review", {"subject": {"value": 1}})
    assert result["execution_status"] == "unchecked"
    assert result["verdict"] == "unchecked"
    assert result["verifier_id"] == "test.manual.review"


def test_script_verifier_uses_json_stdio_protocol(tmp_path):
    verifier_dir = tmp_path / "scripted"
    scripts = verifier_dir / "scripts"
    scripts.mkdir(parents=True)
    (verifier_dir / "VERIFIER.md").write_text(
        "---\nid: test.scripted.check\nversion: 1.0.0\nentrypoint: scripts/check.py\n---\n\n# Check\n",
        encoding="utf-8",
    )
    (scripts / "check.py").write_text(
        "import json, sys\n"
        "request = json.load(sys.stdin)\n"
        "json.dump({'verdict': 'pass', 'facts': {'echo': request['subject']}}, sys.stdout)\n",
        encoding="utf-8",
    )
    result = FilesystemVerifierRegistry(tmp_path).run(
        "test.scripted.check", {"subject": {"value": 2}, "request_id": "r1"}
    )
    assert result["execution_status"] == "completed"
    assert result["verdict"] == "pass"
    assert result["facts"]["echo"] == {"value": 2}


def test_verifier_id_requires_owner_domain_and_capability() -> None:
    assert validate_verifier_id("bensz.document.link-integrity") == "bensz.document.link-integrity"
    assert validate_verifier_id("org.example.evidence.citation-fit") == "org.example.evidence.citation-fit"

    for invalid in ("markdown.link-integrity", "bensz.document", "bensz.Document.link-integrity", "bensz.document.link_integrity", "bensz.document.link-integrity.v1"):
        try:
            validate_verifier_id(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected invalid verifier ID: {invalid}")


def test_filesystem_registry_resolves_legacy_alias_to_canonical_id(tmp_path: Path):
    verifier_dir = tmp_path / "link-integrity"
    verifier_dir.mkdir()
    (verifier_dir / "VERIFIER.md").write_text(
        "---\n"
        "id: bensz.document.link-integrity\n"
        "version: 1.0.0\n"
        "aliases: markdown.link-integrity, markdown.references\n"
        "---\n\n# Link integrity\n",
        encoding="utf-8",
    )
    registry = FilesystemVerifierRegistry(tmp_path)
    assert registry.resolve("markdown.link-integrity").verifier_id == "bensz.document.link-integrity"
    assert registry.resolve("markdown.references").verifier_id == "bensz.document.link-integrity"
    result = registry.run("markdown.link-integrity", {"subject": {}})
    assert result["verifier_id"] == "bensz.document.link-integrity"


def test_noncanonical_filesystem_verifier_id_is_rejected(tmp_path: Path):
    verifier_dir = tmp_path / "legacy"
    verifier_dir.mkdir()
    (verifier_dir / "VERIFIER.md").write_text("---\nid: legacy.check\nversion: 1.0.0\n---\n", encoding="utf-8")
    try:
        FilesystemVerifierRegistry(tmp_path)
    except ValueError as exc:
        assert "canonical verifier ID" in str(exc)
    else:
        raise AssertionError("non-canonical verifier ID must be rejected")


def test_pack_registry_resolves_highest_semantic_version() -> None:
    registry = PackRegistry()
    for version in ("1.9.0", "1.10.0"):
        registry.register(VerifierPack(VerifierSpec("test.demo.versioned", version, "rule")))

    assert registry.resolve("test.demo.versioned").spec.version == "1.10.0"


def test_verifier_spec_exposes_pack_refs_and_subject_kinds() -> None:
    spec = VerifierSpec(
        "test.demo.contract",
        "1.0.0",
        "hybrid",
        subject_kinds=("json",),
        prompt_pack_ref="prompts/demo@1.0.0",
        rule_pack_ref="rules/demo@1.0.0",
        calibration_set_ref="calibration/demo@1.0.0",
    )
    assert spec.subject_kinds == ("json",)
    assert spec.prompt_pack_ref == "prompts/demo@1.0.0"
    assert spec.rule_pack_ref == "rules/demo@1.0.0"
    assert spec.calibration_set_ref == "calibration/demo@1.0.0"


def test_builtin_registry_contains_kernel_atomic_whitelist() -> None:
    ids = {spec.verifier_id for spec in build_builtin_registry().specs()}
    assert {
        "bensz.contract.conformance",
        "bensz.artifact.path-scope",
        "bensz.artifact.schema-conformance",
        "bensz.source.diff-scope",
        "bensz.security.secret-redaction",
        "bensz.evidence.provenance",
        "bensz.runtime.event-integrity",
        "bensz.runtime.state-transition",
        "bensz.runtime.task-completeness",
    } <= ids


def test_secret_redaction_verifier_rejects_token_like_values() -> None:
    result, gate = VerifierRunner(build_builtin_registry()).run(
        VerificationRequest(subject={"token": "secret-value"}),
        "bensz.security.secret-redaction",
    )
    assert result[0].verdict == "fail"
    assert gate.decision == "reject"
