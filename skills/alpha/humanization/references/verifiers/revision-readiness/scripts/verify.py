#!/usr/bin/env python3
"""JSON-stdio mechanical revision facts; no prose or semantic verdicts."""

from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from revision_evidence import ControlError, canonical, digest, load_request


def main():
    try:
        request = json.load(sys.stdin)
        context = request["context"]
        root = Path(context["task_root"])
        index = load_request(root, context["request_ref"], complete=True)
        expected = request["subject"]["content_hash"]
        if index != context["index"] or digest(canonical(index)) != expected:
            raise ControlError("evidence_mismatch")
        ref = request["subject"]["ref"]
        result = {"verdict": "pass", "facts": {"evidence_hash": expected, "lexical": index["lexical"],
                  "outcome": index["outcome"], "effective_structure_mode": index["effective_structure_mode"]},
                  "evidence_refs": [ref]}
    except Exception as error:
        result = {"verdict": "fail", "findings": [{"id": "revision-input", "reason_code": str(error) if isinstance(error, ControlError) else "invalid_revision_input"}]}
    json.dump(result, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
