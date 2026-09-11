"""Small, dependency-free verifier packs shipped with the kernel.

Skills select these by stable id and tags.  Domain-specific packs can still be
registered by a Skill, but common packs live here so Skills do not duplicate
command, result, or Gate plumbing.
"""

from __future__ import annotations

from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from .verifiers import FilesystemVerifierRegistry, PackRegistry, VerifierPack, builtin_verifier_root


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


@lru_cache(maxsize=1)
def _filesystem_registry() -> FilesystemVerifierRegistry:
    return FilesystemVerifierRegistry(builtin_verifier_root())


def _compatibility_component(verifier_id: str, version: str):
    """Adapt an indexed filesystem Pack to the legacy callable interface."""

    def execute(request: Any, _evidence: Any):
        payload = request.to_dict() if hasattr(request, "to_dict") else request
        return _filesystem_registry().run(verifier_id, payload, version=version)

    return execute


FILE_SPEC = _filesystem_registry().resolve("bensz.artifact.file-existence", "1.0.0").spec
CITATION_TRUTH_FIT_SPEC = _filesystem_registry().resolve("bensz.evidence.citation-truth-fit", "1.0.0").spec


def build_builtin_registry() -> PackRegistry:
    """Return the legacy in-memory view, derived entirely from the Pack index."""
    registry = PackRegistry()
    for definition in _filesystem_registry().definitions():
        pack = definition.contract_pack()
        component_id = pack.components[0].id if pack.components else "contract-review"
        component = _compatibility_component(definition.verifier_id, definition.version)
        if pack.mode in {"prompt", "human"}:
            registry.register(VerifierPack(definition.spec, prompts=((component_id, component),)))
        else:
            registry.register(VerifierPack(definition.spec, rules=((component_id, component),)))
    return registry
