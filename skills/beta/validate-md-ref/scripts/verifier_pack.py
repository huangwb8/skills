"""Domain Pack for validate-md-ref.

The URL checker remains a deterministic adapter.  This module only translates
its facts into the generic kernel contract; it never decides how a document is
rewritten and never performs writes.
"""

from __future__ import annotations

from typing import Any, Mapping

from bensz_skill_kernel import Evidence, PackRegistry, VerifierPack, VerifierSpec


SPEC = VerifierSpec(
    verifier_id="markdown.references.v1",
    version="1.0.0",
    mode="hybrid",
    capabilities=("markdown.reference_extraction", "url.reachability", "anchor.local"),
    evidence_requirements=("markdown.snapshot", "reference.results"),
    uncertainty_policy={"missing_evidence": "unchecked", "probe_failure": "uncertain"},
    metadata={"side_effects": "none", "network": "declared read-only probe"},
)


def rule_results(request: Any, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]:
    payload = evidence["reference.results"].content
    summary = dict(payload.get("summary", {}))
    invalid = int(summary.get("invalid", 0))
    findings = []
    for item in payload.get("references", []):
        validation = item.get("validation", {})
        if validation.get("valid") is False and not validation.get("skipped"):
            findings.append({"id": "unreachable-reference", "severity": "required", "verdict": "fail", "message": validation.get("error"), "evidence_refs": [f"reference:{item.get('index')}"]})
    return {"verdict": "fail" if invalid else "pass", "facts": {"summary": summary}, "findings": findings, "evidence_refs": ["reference.results"]}


def prompt_fallback(request: Any, evidence: Mapping[str, Evidence]) -> Mapping[str, Any]:
    """A deterministic semantic placeholder: no content entailment is claimed."""
    return {"execution_status": "unchecked", "verdict": "unchecked", "uncertainty_reason": "URL reachability does not establish citation content support", "evidence_refs": ["markdown.snapshot", "reference.results"], "model_or_engine": "none"}


def build_registry() -> PackRegistry:
    registry = PackRegistry()
    registry.register(VerifierPack(spec=SPEC, rules=(("url-reachability", rule_results),), prompts=(("content-entailment", prompt_fallback),)))
    return registry
