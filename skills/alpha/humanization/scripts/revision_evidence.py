"""Local revision evidence: mechanical checks only; no semantic verdicts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from check_revision import PLAIN_MARKUP, UnsupportedInput, compare, structure_signature

SKILL_ROOT = Path(__file__).resolve().parents[1]


class ControlError(ValueError):
    """Stable reason code; never include source text or private paths."""


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def config() -> dict:
    import yaml

    return yaml.safe_load((SKILL_ROOT / "config.yaml").read_text(encoding="utf-8"))


def safe_path(root: Path, ref: str) -> Path:
    if not isinstance(ref, str) or not ref or "\\" in ref:
        raise ControlError("invalid_path")
    relative = PurePosixPath(ref)
    if relative.is_absolute() or any(x in {"..", ".", ""} for x in ref.split("/")):
        raise ControlError("invalid_path")
    path = root
    for segment in relative.parts:
        path = path / segment
        if path.is_symlink():
            raise ControlError("symlink_forbidden")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ControlError("path_outside_task")
    return path


def read_bytes(root: Path, ref: str, limit: int) -> bytes:
    path = safe_path(root, ref)
    if not path.is_file() or path.stat().st_size > limit:
        raise ControlError("missing_or_oversized_file")
    data = path.read_bytes()
    if len(data) > limit:
        raise ControlError("oversized_file")
    return data


def read_json(root: Path, ref: str) -> dict:
    value = json.loads(read_bytes(root, ref, config()["control_policy"]["max_json_bytes"]))
    if not isinstance(value, dict):
        raise ControlError("json_object_required")
    return value


def write_json(root: Path, ref: str, value: dict) -> None:
    path = safe_path(root, ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = safe_path(root, ref + ".pending")
    temporary.write_bytes(canonical(value))
    temporary.replace(path)


def parameters(raw: dict) -> dict:
    cfg = config()
    if not isinstance(raw, dict) or set(raw) - set(cfg["defaults"]):
        raise ControlError("unknown_parameter")
    result = {**cfg["defaults"], **raw}
    for name, values in cfg["parameters"].items():
        if type(result[name]) is not type(values[0]) or result[name] not in values:
            raise ControlError("invalid_parameter")
    if result["style_profile"] not in cfg["style_profiles"]:
        raise ControlError("invalid_style_profile")
    if not isinstance(result["section_type"], str) or not result["section_type"].strip():
        raise ControlError("invalid_section_type")
    maximum = result["max_self_eval_rounds"]
    if type(maximum) is not int or not 1 <= maximum <= cfg["defaults"]["max_self_eval_rounds"]:
        raise ControlError("invalid_review_budget")
    if "self_eval_rounds" not in raw:
        result["self_eval_rounds"] = min(result["self_eval_rounds"], maximum)
    if result["self_eval_rounds"] > maximum:
        raise ControlError("invalid_review_budget")
    return result


def load_request(root: Path, ref: str, *, complete: bool) -> dict:
    request = read_json(root, ref)
    if set(request) - {"original", "delivery", "parameters", "outcome"}:
        raise ControlError("unknown_request_field")
    params = parameters(request.get("parameters", {}))
    limit = config()["control_policy"]["max_text_bytes"]
    original_ref = request.get("original")
    if not isinstance(original_ref, str) or not original_ref.startswith("humanization/input/"):
        raise ControlError("original_must_be_input")
    original = read_bytes(root, original_ref, limit)
    if not original.strip():
        raise ControlError("empty_original")
    original_text = original.decode("utf-8")
    mode = params["structure_mode"]
    effective = "preserve" if mode == "reflow_plain" and PLAIN_MARKUP.search(original_text) else mode
    identity = {"original": {"ref": original_ref, "hash": digest(original)}, "parameters": params}
    if not complete:
        return identity
    outcome = request.get("outcome")
    if outcome not in {"revise", "keep_original", "diagnosis"}:
        raise ControlError("invalid_outcome")
    diagnosis = params["output_mode"] == "diagnosis_only"
    if diagnosis != (outcome == "diagnosis"):
        raise ControlError("outcome_mode_mismatch")
    expected = {"diagnosis"} if diagnosis else {"text"}
    if params["output_mode"] in {"text_with_change_summary", "text_with_change_summary_and_style_card"}:
        expected.add("summary")
    if params["output_mode"] == "text_with_change_summary_and_style_card":
        expected.add("style_card")
    delivery = request.get("delivery")
    if not isinstance(delivery, dict) or set(delivery) != expected:
        raise ControlError("delivery_mode_mismatch")
    artifacts = {}
    for key, path in delivery.items():
        if not isinstance(path, str) or not path.startswith("humanization/output/") or path == original_ref:
            raise ControlError("delivery_must_be_output")
        data = read_bytes(root, path, limit)
        if not data.strip():
            raise ControlError("empty_delivery")
        data.decode("utf-8")
        artifacts[key] = {"ref": path, "hash": digest(data)}
    identities = {(safe_path(root, path).stat().st_dev, safe_path(root, path).stat().st_ino) for path in delivery.values()}
    if len(identities) != len(delivery):
        raise ControlError("duplicate_delivery_path")
    lexical = {"status": "not_applicable", "reason": "diagnosis_only"}
    if not diagnosis:
        candidate = read_bytes(root, delivery["text"], limit)
        revised = candidate.decode("utf-8")
        if outcome == "keep_original" and candidate != original:
            raise ControlError("keep_original_changed")
        if effective == "preserve" and structure_signature(original_text) != structure_signature(revised):
            raise ControlError("structure_changed")
        if effective == "reflow_plain" and PLAIN_MARKUP.search(revised):
            raise ControlError("reflow_added_markup")
        try:
            lexical = compare(original_text, revised, effective)
        except UnsupportedInput as error:
            lexical = {"status": "unchecked", "reason": str(error), "semantic_review": "required"}
    return {**identity, "delivery": artifacts, "outcome": outcome,
            "requested_structure_mode": mode, "effective_structure_mode": effective,
            "structure_fallback": "protected_markup" if mode != effective else None,
            "lexical": lexical}


def validate_review(facts: dict, index: dict, root: Path) -> None:
    """Validate coverage records and anchors, never their semantic truth."""
    if not isinstance(facts, dict) or facts.get("evidence_hash") != digest(canonical(index)):
        raise ControlError("review_evidence_mismatch")
    if not isinstance(facts.get("summary"), str) or not facts["summary"].strip():
        raise ControlError("review_summary_missing")
    confidence = facts.get("confidence")
    if type(confidence) not in {int, float} or not 0 <= confidence <= 1:
        raise ControlError("review_confidence_invalid")
    if facts.get("uncertainties") != []:
        raise ControlError("review_uncertain")
    audit = facts.get("audit")
    if not isinstance(audit, dict):
        raise ControlError("review_audit_missing")
    source = read_bytes(root, index["original"]["ref"], config()["control_policy"]["max_text_bytes"]).decode("utf-8")
    texts = {"original": source}
    texts.update({key: read_bytes(root, val["ref"], config()["control_policy"]["max_text_bytes"]).decode("utf-8")
                  for key, val in index["delivery"].items()})
    for setting, required in config()["quality_checks"].items():
        if not setting.startswith("require_") or required is not True:
            continue
        key = setting.removeprefix("require_")
        section = audit.get(key)
        if not isinstance(section, dict) or section.get("applicability") not in {"applicable", "not_applicable"}:
            raise ControlError("review_section_missing")
        if not isinstance(section.get("reason"), str) or not section["reason"].strip():
            raise ControlError("review_reason_missing")
        items = section.get("items")
        if not isinstance(items, list) or (section["applicability"] == "applicable" and not items):
            raise ControlError("review_items_missing")
        if key == "invariant_audit" and section["applicability"] != "applicable":
            raise ControlError("invariant_review_required")
        if section["applicability"] == "not_applicable" and items:
            raise ControlError("review_applicability_mismatch")
        for item in items:
            if not isinstance(item, dict) or item.get("disposition") not in {"preserved", "rewritten", "merged", "reviewed"}:
                raise ControlError("review_disposition_invalid")
            if not isinstance(item.get("reason"), str) or not item["reason"].strip():
                raise ControlError("review_reason_missing")
            anchors = item.get("anchors")
            if not isinstance(anchors, list) or not anchors:
                raise ControlError("review_anchor_missing")
            for anchor in anchors:
                if not isinstance(anchor, dict):
                    raise ControlError("review_anchor_invalid")
                start, end = anchor.get("start"), anchor.get("end")
                artifact = anchor.get("artifact")
                if artifact not in texts or type(start) is not int or type(end) is not int or not 0 <= start < end <= len(texts[artifact]):
                    raise ControlError("review_anchor_invalid")
    covered = {a["artifact"] for item in audit["invariant_audit"]["items"] for a in item["anchors"]}
    if not set(texts).issubset(covered):
        raise ControlError("review_artifact_coverage_missing")
    comparison = facts.get("comparison")
    if not isinstance(comparison, dict) or comparison.get("outcome") != index["outcome"] or not comparison.get("reason"):
        raise ControlError("comparison_missing")
    if index["outcome"] == "revise" and comparison.get("net_improvement") is not True:
        raise ControlError("no_net_improvement")
    rounds = facts.get("rounds")
    if not isinstance(rounds, list) or len(rounds) != index["parameters"]["self_eval_rounds"]:
        raise ControlError("review_rounds_missing")
    if any(not isinstance(x, dict) or not x.get("summary") or not isinstance(x.get("focus"), list) for x in rounds):
        raise ControlError("review_round_invalid")
    if not {"expression", "safety"}.issubset({x for row in rounds for x in row["focus"]}):
        raise ControlError("review_focus_missing")
    if index["lexical"]["status"] in {"fail", "unchecked"} and not facts.get("lexical_explanation"):
        raise ControlError("lexical_review_missing")
