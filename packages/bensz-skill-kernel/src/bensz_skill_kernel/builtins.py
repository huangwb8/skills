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


def _file_exists(request: Any, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]:
    path = request.subject.get('path')
    exists = bool(path and Path(path).is_file())
    return {'verdict': 'pass' if exists else 'fail', 'facts': {'path': path, 'exists': exists}, 'findings': [] if exists else [{'id': 'missing-file', 'severity': 'required', 'verdict': 'fail', 'message': f'file does not exist: {path}'}]}


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
    registry.register(VerifierPack(FILE_SPEC, rules=(('file-exists', _file_exists),)))
    registry.register(VerifierPack(CITATION_TRUTH_FIT_SPEC, prompts=(('citation-semantics', _citation_engine_gap),)))
    return registry
