#!/usr/bin/env python3
"""JSON stdio: bind frozen artifacts and locate hints, never judge their wording."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from revision_evidence import ControlError, canonical, digest, load_request, review_texts
from evidence import collect_clues


def main():
    try:
        request = json.load(sys.stdin)
        context = request["context"]
        root = Path(context["task_root"])
        index = load_request(root, context["request_ref"], complete=True)
        expected = request["subject"]["content_hash"]
        if index != context["index"] or digest(canonical(index)) != expected:
            raise ControlError("evidence_mismatch")
        clues = collect_clues(review_texts(index, root))
        result = {"verdict": "pass", "facts": {"evidence_hash": expected, **clues,
                  "semantic_status": "unchecked", "clues_are_exhaustive": False},
                  "evidence_refs": [request["subject"]["ref"]]}
    except Exception as error:
        result = {"verdict": "fail", "findings": [{"id": "defensive-input",
                  "reason_code": str(error) if isinstance(error, ControlError) else "invalid_defensive_input"}]}
    json.dump(result, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
