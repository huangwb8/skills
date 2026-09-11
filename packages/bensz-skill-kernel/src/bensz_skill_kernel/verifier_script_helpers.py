"""Shared helpers for built-in verifier entrypoint scripts.

This module owns request/result plumbing only. Verifier-specific rules stay in
their Pack-local ``scripts/verify.py`` files.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Mapping


def request_parts(request: Any) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if hasattr(request, "subject"):
        return request.subject, request.context
    return request.get("subject") or {}, request.get("context") or {}


def evidence_map(
    request: Any,
    evidence: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    if evidence:
        return evidence
    if hasattr(request, "evidence"):
        return {item.ref: item for item in request.evidence}
    raw = request.get("evidence") or []
    return {
        str(item.get("ref", index)): item
        for index, item in enumerate(raw)
        if isinstance(item, Mapping)
    }


def result(
    ok: bool,
    facts: Mapping[str, Any],
    finding_id: str,
    values: list[Any],
) -> Mapping[str, Any]:
    return {
        "verdict": "pass" if ok else "fail",
        "facts": dict(facts),
        "findings": [
            {"id": finding_id, "value": value, "verdict": "fail"}
            for value in values
        ],
    }


def run_main(
    verify: Callable[[Any], Mapping[str, Any]],
    *,
    stdin: Any = sys.stdin,
    stdout: Any = sys.stdout,
) -> int:
    json.dump(verify(json.load(stdin)), stdout, ensure_ascii=False)
    return 0
