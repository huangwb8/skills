"""Defensive framing evidence schema; semantic decisions remain with reviewers."""

import re

from revision_evidence import (
    ControlError, canonical, config, digest, require_text, review_texts, validate_anchors,
)

# Hints locate candidate spans only. A match is never a defect or a verdict.
HINTS = re.compile(r"并不意味着|不代表|需要强调|谨慎看待|不能排除|可能|免责声明|"
                   r"does not (?:mean|imply)|not (?:claim|suggest)|disclaimer|may|caution", re.I)


def collect_clues(texts: dict) -> dict:
    clues, count = [], 0
    limit = config()["control_policy"]["max_defensive_clues"]
    for artifact, text in texts.items():
        for match in HINTS.finditer(text):
            count += 1
            if len(clues) < limit:
                clues.append({"artifact": artifact, "start": match.start(), "end": match.end()})
    return {"clues": clues, "clue_count": count, "clues_truncated": count > len(clues)}


def validate_defensive_review(facts: dict, index: dict, root) -> None:
    if not isinstance(facts, dict) or facts.get("evidence_hash") != digest(canonical(index)):
        raise ControlError("review_evidence_mismatch")
    require_text(facts.get("summary"), "review_summary_missing")
    confidence = facts.get("confidence")
    if type(confidence) not in {int, float} or not 0 <= confidence <= 1:
        raise ControlError("review_confidence_invalid")
    if facts.get("uncertainties") != []:
        raise ControlError("review_uncertain")
    audit = facts.get("defensive_audit")
    target = "diagnosis" if index["outcome"] == "diagnosis" else "text"
    if not isinstance(audit, dict) or audit.get("scope") != target:
        raise ControlError("defensive_audit_missing")
    if audit.get("unresolved_material_findings") != []:
        raise ControlError("unresolved_material_finding")
    texts = review_texts(index, root)
    # A clean document still needs a positive, anchored full-reading record.
    coverage = audit.get("coverage")
    if not isinstance(coverage, dict):
        raise ControlError("defensive_coverage_missing")
    require_text(coverage.get("reason"), "defensive_coverage_missing")
    validate_anchors(coverage.get("anchors"), texts, required=set(texts))
    items = audit.get("items")
    if not isinstance(items, list):
        raise ControlError("defensive_items_missing")
    allowed = {"necessary": {"keep", "compress", "rewrite"},
               "redundant": {"keep", "compress", "rewrite", "delete"},
               "anticipatory": {"keep", "compress", "rewrite", "delete"},
               "performative": {"keep", "compress", "rewrite", "delete"},
               "mixed": {"keep", "compress", "rewrite"}, "unresolved": {"human_review"}}
    for item in items:
        if not isinstance(item, dict):
            raise ControlError("defensive_item_invalid")
        category, action = item.get("necessity"), item.get("disposition")
        if not isinstance(category, str) or category not in allowed or action not in allowed[category]:
            raise ControlError("defensive_disposition_invalid")
        for field in ("pattern", "materiality_reason", "preserved_function"):
            require_text(item.get(field), "defensive_reason_missing")
        if category == "unresolved" or item.get("material") is not False:
            raise ControlError("unresolved_material_finding")
        source, candidate = item.get("source_anchors"), item.get("candidate_anchors")
        if not isinstance(source, list) or not isinstance(candidate, list) or not (source or candidate):
            raise ControlError("review_anchor_missing")
        if source:
            validate_anchors(source, {"original": texts["original"]})
        if candidate:
            validate_anchors(candidate, {k: v for k, v in texts.items() if k != "original"})
        # Every removal/merge must show where its information survives.
        validate_anchors(item.get("preserved_anchors"), texts, required={target})
