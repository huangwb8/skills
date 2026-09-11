"""Small, dependency-free verifier packs shipped with the kernel.

Skills select these by stable id and tags.  Domain-specific packs can still be
registered by a Skill, but common packs live here so Skills do not duplicate
command, result, or Gate plumbing.
"""

from __future__ import annotations

from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Mapping

from .verifiers import Evidence, PackRegistry, VerifierPack, VerifierSpec


@lru_cache(maxsize=1)
def _markdown_collector_module():
    """Load the legacy Markdown API without keeping its implementation here."""
    collector_path = (
        Path(__file__).resolve().parent
        / 'verifiers'
        / 'markdown-link-integrity'
        / 'scripts'
        / 'collector.py'
    )
    spec = spec_from_file_location('bensz_skill_kernel._markdown_link_integrity_collector', collector_path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load Markdown collector: {collector_path}')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_markdown(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Backward-compatible proxy to the Markdown Verifier collector.

    New code should invoke ``markdown-link-integrity`` through the filesystem
    Verifier entrypoint instead of importing this compatibility API.
    """
    return _markdown_collector_module().collect_markdown(*args, **kwargs)


@lru_cache(maxsize=None)
def _verifier_script_module(directory: str):
    script_path = Path(__file__).resolve().parent / 'verifiers' / directory / 'scripts' / 'verify.py'
    spec = spec_from_file_location(
        f"bensz_skill_kernel._builtin_verifier_{directory.replace('-', '_')}",
        script_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load verifier script: {script_path}')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'verify'):
        raise ImportError(f'verifier script has no verify() function: {script_path}')
    return module


def _script_rule(directory: str):
    return lambda request, evidence: _verifier_script_module(directory).verify(request, evidence)


CITATION_TRUTH_FIT_SPEC = VerifierSpec(
    verifier_id='bensz.evidence.citation-truth-fit',
    version='1.0.0',
    mode='hybrid',
    capabilities=('evidence.identity', 'semantic.entailment', 'semantic.appropriateness'),
    evidence_requirements=('subject_context', 'source_metadata', 'source_excerpt'),
    uncertainty_policy={'missing_evidence': 'manual_review', 'engine_unavailable': 'unchecked'},
    tags=('common', 'citation', 'semantic', 'evidence'),
    aliases=('citation.truth-and-fit',),
    metadata={'side_effects': 'none', 'requires_external_engine': True},
)


def _citation_engine_gap(request: Any, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]:
    return {
        'execution_status': 'unchecked',
        'verdict': 'unchecked',
        'uncertainty_reason': 'semantic citation engine is not bundled with the kernel',
        'evidence_refs': ['subject_context', 'source_metadata', 'source_excerpt'],
        'model_or_engine': 'none',
    }


FILE_SPEC = VerifierSpec(
    verifier_id='bensz.artifact.file-existence',
    version='1.0.0',
    mode='rule',
    capabilities=('filesystem.read',),
    tags=('common', 'filesystem', 'deterministic'),
    aliases=('artifact.file-exists',),
    metadata={'side_effects': 'none'},
)


def build_builtin_registry() -> PackRegistry:
    registry = PackRegistry()
    registry.register(VerifierPack(FILE_SPEC, rules=(('file-exists', _script_rule('artifact-file-exists')),)))
    registry.register(VerifierPack(CITATION_TRUTH_FIT_SPEC, prompts=(('citation-semantics', _citation_engine_gap),)))
    atomic = (
        ("bensz.contract.conformance", "contract-conformance", "contract-conformance", "contract"),
        ("bensz.artifact.path-scope", "path-scope", "path-scope", "artifact"),
        ("bensz.artifact.schema-conformance", "schema-conformance", "schema-conformance", "artifact"),
        ("bensz.source.diff-scope", "diff-scope", "diff-scope", "source"),
        ("bensz.security.secret-redaction", "secret-redaction", "secret-redaction", "security"),
        ("bensz.evidence.provenance", "evidence-provenance", "evidence-provenance", "evidence"),
        ("bensz.runtime.event-integrity", "event-integrity", "event-integrity", "runtime"),
        ("bensz.runtime.state-transition", "state-transition", "state-transition", "runtime"),
        ("bensz.runtime.task-completeness", "task-completeness", "task-completeness", "runtime"),
    )
    for verifier_id, rule_name, directory, tag in atomic:
        rule = _script_rule(directory)
        registry.register(VerifierPack(VerifierSpec(verifier_id, "1.0.0", "rule", tags=("common", tag, "deterministic")), rules=((rule_name, rule),)))
    return registry
