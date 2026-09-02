"""Implementations for the small, domain-neutral atomic verifier packs.

This module lives beside the directory contracts so reviewers can inspect the
rules independently from the registry and runner plumbing.  Each directory's
``scripts/verify.py`` is a thin JSON-stdio adapter around ``run_atomic``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from bensz_skill_kernel.runtime import ALLOWED_TRANSITIONS, EventLog


def _parts(request: Any) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if hasattr(request, "subject"):
        return request.subject, request.context
    return request.get("subject") or {}, request.get("context") or {}


def _evidence_map(request: Any, evidence: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if evidence:
        return evidence
    if hasattr(request, "evidence"):
        return {item.ref: item for item in request.evidence}
    raw = request.get("evidence") or []
    return {str(item.get("ref", index)): item for index, item in enumerate(raw) if isinstance(item, Mapping)}


def run_atomic(name: str, request: Any, evidence: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    subject, context = _parts(request)
    evidence = _evidence_map(request, evidence)
    if name == "contract-conformance":
        required = tuple(context.get("required_fields", ()))
        missing = [field for field in required if field not in subject]
        return _result(not missing, {"required_fields": list(required), "missing": missing}, "missing-field", missing)
    if name == "path-scope":
        raw_paths = subject.get("paths") or ([subject["path"]] if subject.get("path") else [])
        allowed = [Path(item).expanduser().resolve() for item in context.get("allowed_paths", ())]
        violations = []
        for raw in raw_paths:
            target = Path(raw).expanduser().resolve()
            # Scope is lexical after ``resolve()`` and must not depend on an
            # allowed directory already existing.  Requiring ``is_dir()``
            # made valid output paths fail before their parent was created.
            if not any(target == root or root in target.parents for root in allowed):
                violations.append(str(target))
        return _result(not violations, {"paths": list(raw_paths), "violations": violations}, "path-out-of-scope", violations)
    if name == "schema-conformance":
        data = subject.get("data", subject)
        schema = context.get("schema", {})
        required = schema.get("required", ()) if isinstance(schema, Mapping) else ()
        missing = [key for key in required if not isinstance(data, Mapping) or key not in data]
        return _result(not missing, {"missing": missing}, "schema-required-field", missing)
    if name == "diff-scope":
        changed = set(subject.get("changed_paths", ()))
        violations = sorted(changed - set(context.get("allowed_paths", ())))
        return _result(not violations, {"changed": sorted(changed), "violations": violations}, "unexpected-change", violations)
    if name == "secret-redaction":
        raw = json.dumps(subject, ensure_ascii=False, default=str)
        patterns = (r"[\"']?(?:api[_-]?key|token|password|cookie)[\"']?\s*[:=]\s*[\"']?[^,\s}\"']+", r"sk-[A-Za-z0-9_-]{8,}")
        matches = [pattern for pattern in patterns if re.search(pattern, raw, re.IGNORECASE)]
        return {"verdict": "fail" if matches else "pass", "facts": {"matched_patterns": len(matches)}, "findings": [{"id": "secret-detected", "verdict": "fail"}] if matches else []}
    if name == "evidence-provenance":
        def value(item: Any, key: str) -> Any:
            return item.get(key) if isinstance(item, Mapping) else getattr(item, key, None)
        invalid = [ref for ref, item in evidence.items() if not value(item, "source_type") or not value(item, "content_hash") or not value(item, "collected_at")]
        return _result(not invalid, {"evidence_count": len(evidence)}, "missing-provenance", invalid)
    if name == "event-integrity":
        path = subject.get("path")
        if not path:
            return _result(False, {}, "missing-events-path", ["events"])
        try:
            count = len(EventLog(path).read())
        except Exception as exc:
            return {"verdict": "fail", "uncertainty_reason": str(exc), "findings": [{"id": "event-integrity", "verdict": "fail"}]}
        return {"verdict": "pass", "facts": {"event_count": count}, "findings": []}
    if name == "state-transition":
        current, target = subject.get("current_state"), subject.get("target_state")
        allowed = target in ALLOWED_TRANSITIONS.get(current, ())
        return _result(allowed, {"current_state": current, "target_state": target}, "illegal-transition", [target] if not allowed else [])
    if name == "task-completeness":
        required = tuple(context.get("required_fields", ("artifacts", "verifications", "delivery_report")))
        missing = [key for key in required if not subject.get(key)]
        return _result(not missing, {"missing": missing}, "task-incomplete", missing)
    raise ValueError(f"unknown atomic verifier: {name}")


def _result(ok: bool, facts: Mapping[str, Any], finding_id: str, values: list[Any]) -> Mapping[str, Any]:
    return {"verdict": "pass" if ok else "fail", "facts": dict(facts), "findings": [{"id": finding_id, "value": value, "verdict": "fail"} for value in values]}
