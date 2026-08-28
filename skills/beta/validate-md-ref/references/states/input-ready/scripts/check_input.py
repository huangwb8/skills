"""Minimal state helper: verify that the selected Markdown input is readable."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    payload = json.load(sys.stdin)
    document = (payload.get("request", {}).get("context", {}) or {}).get("document")
    if not isinstance(document, str) or not document:
        result = {"verdict": "fail", "summary": "context.document is required.", "facts": {}, "evidence_refs": []}
    else:
        path = Path(document).expanduser()
        valid = path.is_file() and path.suffix.lower() == ".md"
        result = {"verdict": "pass" if valid else "fail", "summary": "Markdown input is readable." if valid else "context.document must name an existing Markdown file.", "facts": {"document": str(path.resolve())}, "evidence_refs": [str(path.resolve())] if valid else []}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
