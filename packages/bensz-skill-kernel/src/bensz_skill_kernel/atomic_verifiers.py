"""Compatibility wrapper for Pack-local atomic verifier scripts.

Verifier rules now live beside their contracts in
``verifiers/<name>/scripts/verify.py``.  ``run_atomic`` remains for older callers
that imported the central helper directly.
"""

from __future__ import annotations

from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Mapping


_SCRIPT_BY_NAME = {
    "artifact-file-exists": "artifact-file-exists",
    "contract-conformance": "contract-conformance",
    "path-scope": "path-scope",
    "schema-conformance": "schema-conformance",
    "diff-scope": "diff-scope",
    "secret-redaction": "secret-redaction",
    "evidence-provenance": "evidence-provenance",
    "event-integrity": "event-integrity",
    "state-transition": "state-transition",
    "task-completeness": "task-completeness",
}


@lru_cache(maxsize=None)
def _script_module(name: str):
    directory = _SCRIPT_BY_NAME.get(name)
    if directory is None:
        raise ValueError(f"unknown atomic verifier: {name}")
    script = Path(__file__).resolve().parent / "verifiers" / directory / "scripts" / "verify.py"
    spec = spec_from_file_location(
        f"bensz_skill_kernel._builtin_verifier_{directory.replace('-', '_')}",
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
