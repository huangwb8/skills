"""Minimal state helper: verify that the selected Markdown input is readable."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    payload = json.load(sys.stdin)
    context = payload.get("request", {}).get("context", {})
    document = context.get("document")
    if not isinstance(document, str) or not document:
        result = {"verdict": "fail", "summary": "context.document is required.", "facts": {}, "evidence_refs": []}
    else:
        path = Path(document).expanduser()
        if not path.is_file() or path.suffix.lower() != ".md":
            result = {"verdict": "fail", "summary": "context.document must name an existing Markdown file.", "facts": {"document": str(path)}, "evidence_refs": []}
        else:
            result = {"verdict": "pass", "summary": "Markdown input is readable.", "facts": {"document": str(path.resolve())}, "evidence_refs": [str(path.resolve())]}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
