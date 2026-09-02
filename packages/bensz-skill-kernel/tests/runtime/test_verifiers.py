import importlib.util
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

import pytest

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
    normalize_result,
    normalize_requirements,
)
from bensz_skill_kernel.atomic_verifiers import run_atomic
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


class _UnreachableOpener:
    def open(self, request, timeout: int):
        raise URLError("name resolution failed")


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


def test_network_resolution_failure_is_unresolved(monkeypatch):
    monkeypatch.setattr(_COLLECTOR, '_blocked', lambda _url, _blacklist: False)
    result = _probe('https://public.invalid/start', 1, (), (), opener=_UnreachableOpener())
    assert result['valid'] is False
    assert result['validation_status'] == 'unresolved'


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


def test_instruction_only_verifier_preserves_evidence_refs(tmp_path):
    verifier_dir = tmp_path / "manual"
    verifier_dir.mkdir()
    (verifier_dir / "VERIFIER.md").write_text("---\nid: test.manual.evidence\nversion: 1.0.0\n---\n", encoding="utf-8")
    result = FilesystemVerifierRegistry(tmp_path).run(
        "test.manual.evidence",
        {"subject": {}, "evidence": [{"ref": "claim"}, {"ref": "source"}]},
    )
    assert result["evidence_refs"] == ("claim", "source")


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


def test_normalize_requirements_rejects_unknown_duplicate_and_bad_versions(tmp_path: Path):
    registry = FilesystemVerifierRegistry(builtin_verifier_root())
    normalized = normalize_requirements(
        [{"id": "markdown.link-integrity", "version": "1.0.0", "required": True}], registry
    )
    assert normalized[0] == {"id": "bensz.document.markdown-link-integrity", "version": "1.0.0", "required": True}
    with pytest.raises(ValueError, match="unknown verifier"):
        normalize_requirements([{"id": "bensz.document.missing", "version": "1.0.0"}], registry)
    with pytest.raises(ValueError, match="invalid verifier version"):
        normalize_requirements([{"id": "bensz.document.markdown-link-integrity", "version": "latest"}], registry)
    with pytest.raises(ValueError, match="duplicate verifier"):
        normalize_requirements([
            {"id": "bensz.document.markdown-link-integrity", "version": "1.0.0"},
            {"id": "markdown.link-integrity", "version": "1.0.0"},
        ], registry)


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


@pytest.mark.parametrize(
    ("name", "subject", "context"),
    [
        ("contract-conformance", {"id": "x"}, {"required_fields": ["id"]}),
        ("path-scope", {"path": "docs/readme.md"}, {"allowed_paths": ["docs"]}),
        ("schema-conformance", {"data": {"id": 1}}, {"schema": {"required": ["id"]}}),
        ("diff-scope", {"changed_paths": ["src/app.py"]}, {"allowed_paths": ["src/app.py"]}),
        ("state-transition", {"current_state": "active", "target_state": "checking"}, {}),
        ("task-completeness", {"artifacts": ["report"], "verifications": ["v1"], "delivery_report": "report.md"}, {}),
    ],
)
def test_atomic_verifiers_pass_for_satisfied_contracts(name, subject, context):
    result = run_atomic(name, {"subject": subject, "context": context})
    assert result["verdict"] == "pass"
    assert result["findings"] == []


@pytest.mark.parametrize(
    ("name", "subject", "context"),
    [
        ("contract-conformance", {}, {"required_fields": ["id"]}),
        ("schema-conformance", {"data": {}}, {"schema": {"required": ["id"]}}),
        ("diff-scope", {"changed_paths": ["secret.txt"]}, {"allowed_paths": ["src/app.py"]}),
        ("state-transition", {"current_state": "active", "target_state": "completed"}, {}),
        ("task-completeness", {"artifacts": [], "verifications": [], "delivery_report": None}, {}),
    ],
)
def test_atomic_verifiers_fail_for_unsatisfied_contracts(name, subject, context):
    result = run_atomic(name, {"subject": subject, "context": context})
    assert result["verdict"] == "fail"
    assert result["findings"]


def test_atomic_path_scope_rejects_outside_path_and_provenance_requires_all_fields(tmp_path: Path):
    allowed_root = tmp_path / "allowed"
    inside = run_atomic(
        "path-scope",
        {"subject": {"paths": [str(allowed_root / "future.txt")]}, "context": {"allowed_paths": [str(allowed_root)]}},
    )
    assert inside["verdict"] == "pass"
    assert not allowed_root.exists()

    result = run_atomic(
        "path-scope",
        {"subject": {"paths": [str(tmp_path / "outside.txt")]}, "context": {"allowed_paths": [str(allowed_root)]}},
    )
    assert result["verdict"] == "fail"
    result = run_atomic(
        "evidence-provenance",
        {"evidence": [{"ref": "source", "source_type": "web", "content_hash": ""}]},
    )
    assert result["verdict"] == "fail"


def test_builtin_atomic_script_verifiers_cover_file_and_event_integrity(tmp_path: Path):
    existing = tmp_path / "report.md"
    existing.write_text("report\n", encoding="utf-8")
    registry = FilesystemVerifierRegistry(builtin_verifier_root())

    present = registry.run("bensz.artifact.file-existence", {"subject": {"path": str(existing)}})
    missing = registry.run("bensz.artifact.file-existence", {"subject": {"path": str(tmp_path / "missing")}})
    assert present["verdict"] == "pass"
    assert missing["verdict"] == "fail"

    empty = registry.run("bensz.runtime.event-integrity", {"subject": {"path": str(tmp_path / "missing.ndjson")}})
    assert empty["verdict"] == "pass"
    assert empty["facts"]["event_count"] == 0


def test_normalize_result_rejects_malformed_provider_output():
    spec = VerifierSpec("test.demo.normalize", "1.0.0", "rule")
    result = normalize_result({"verdict": "pass", "execution_status": "timed_out"}, spec, evidence_refs=("snapshot:1",))
    assert result.verdict == "unchecked"
    assert result.execution_status == "unchecked"
    assert result.evidence_refs == ("snapshot:1",)


def test_optional_failure_gate_allows_with_warnings():
    spec = VerifierSpec("test.demo.optional", "1.0.0", "rule")
    result = normalize_result({"verdict": "fail"}, spec)
    assert apply_gate((result,), required=False).decision == "allow_with_warnings"


def test_gate_requirements_classify_optional_and_required_failures():
    required = normalize_result({"verdict": "fail"}, VerifierSpec("test.demo.required", "1.0.0", "rule"))
    optional = normalize_result({"verdict": "fail"}, VerifierSpec("test.demo.optional2", "1.0.0", "rule"))
    assert apply_gate((required, optional), requirements=[{"verifier_id": required.verifier_id, "required": True}, {"verifier_id": optional.verifier_id, "required": False}]).decision == "reject"
    assert apply_gate((optional,), requirements=[{"verifier_id": optional.verifier_id, "required": False}]).decision == "allow_with_warnings"


def test_gate_missing_required_verifier_fails_closed():
    present = normalize_result({"verdict": "pass"}, VerifierSpec("test.demo.present", "1.0.0", "rule"))
    gate = apply_gate(
        (present,),
        requirements=[
            {"verifier_id": present.verifier_id, "required": True},
            {"verifier_id": "test.demo.missing", "required": True},
        ],
    )
    assert gate.decision == "manual_review"
    assert gate.unresolved == ("test.demo.missing",)
    assert gate.result_refs == ("test.demo.present@1.0.0",)


def test_filesystem_registry_rejects_non_object_request_as_structured_error():
    result = FilesystemVerifierRegistry(builtin_verifier_root()).run(
        "bensz.artifact.file-existence", [], version="1.0.0"
    )
    assert result["execution_status"] == "error"
    assert result["verdict"] == "error"
    assert "JSON object" in result["uncertainty_reason"]


def test_gate_required_version_mismatch_fails_closed():
    result = normalize_result(
        {"verdict": "pass"},
        VerifierSpec("test.demo.versioned", "9.9.9", "rule"),
    )
    gate = apply_gate(
        (result,),
        requirements=[{"verifier_id": result.verifier_id, "version": "1.0.0", "required": True}],
    )
    assert gate.decision == "manual_review"
    assert gate.unresolved == ("test.demo.versioned@1.0.0",)


def test_gate_malformed_required_requirement_fails_closed():
    result = normalize_result({"verdict": "pass"}, VerifierSpec("test.demo.malformed", "1.0.0", "rule"))
    gate = apply_gate((result,), requirements=[{"required": True}])
    assert gate.decision == "manual_review"
    assert gate.unresolved == ("invalid_requirement",)


def test_gate_non_boolean_mapping_requirement_fails_closed():
    result = normalize_result({"verdict": "pass"}, VerifierSpec("test.demo.mapping", "1.0.0", "rule"))
    gate = apply_gate((result,), requirements={result.verifier_id: "yes"})
    assert gate.decision == "manual_review"
    assert gate.unresolved == ("invalid_requirement",)


def test_gate_invalid_optional_requirement_version_fails_closed():
    result = normalize_result({"verdict": "pass"}, VerifierSpec("test.demo.optional-version", "1.0.0", "rule"))
    gate = apply_gate(
        (result,),
        requirements=[{"verifier_id": result.verifier_id, "version": "not-semver", "required": False}],
    )
    assert gate.decision == "manual_review"
    assert gate.unresolved == ("invalid_requirement",)
