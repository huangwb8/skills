#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def main() -> int:
    request = json.load(sys.stdin)
    path = (request.get("subject") or {}).get("path")
    exists = bool(path and Path(path).is_file())
    json.dump(
        {
            "execution_status": "completed",
            "verdict": "pass" if exists else "fail",
            "facts": {"path": path, "exists": exists},
            "findings": [] if exists else [{"id": "missing-file", "verdict": "fail", "message": f"file does not exist: {path}"}],
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
