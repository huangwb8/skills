"""Compatibility wrapper for Pack-local atomic verifier scripts.

Verifier rules now live beside their contracts in
``verifiers/<name>/scripts/verify.py``.  ``run_atomic`` remains for older callers
that imported the central helper directly.
"""

from __future__ import annotations

from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from typing import Any, Mapping

from .verifiers import FilesystemVerifierRegistry, builtin_verifier_root


@lru_cache(maxsize=1)
def _registry() -> FilesystemVerifierRegistry:
    return FilesystemVerifierRegistry(builtin_verifier_root())


@lru_cache(maxsize=None)
def _script_module(name: str):
    definitions = [definition for definition in _registry().definitions() if definition.path.name == name]
    if len(definitions) != 1 or definitions[0].classification != "atomic":
        raise ValueError(f"unknown atomic verifier: {name}")
    definition = definitions[0]
    pack = definition.contract_pack()
    scripts = [component.entrypoint for component in pack.components if component.type == "script" and component.entrypoint]
    if len(scripts) != 1:
        raise ValueError(f"atomic verifier must declare one script component: {name}")
    script = definition.path / scripts[0]
    spec = spec_from_file_location(
        f"bensz_skill_kernel._builtin_verifier_{name.replace('-', '_')}",
        script,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load verifier script: {script}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "verify"):
        raise ImportError(f"verifier script has no verify() function: {script}")
    return module


def run_atomic(name: str, request: Any, evidence: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    return _script_module(name).verify(request, evidence)
