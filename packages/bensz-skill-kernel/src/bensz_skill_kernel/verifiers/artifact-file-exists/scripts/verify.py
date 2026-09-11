#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.verifier_script_helpers import request_parts, run_main


def verify(request, evidence=None):
    subject, _context = request_parts(request)
    path = subject.get("path")
    exists = bool(path and Path(path).is_file())
    return {
        "execution_status": "completed",
        "verdict": "pass" if exists else "fail",
        "facts": {"path": path, "exists": exists},
        "findings": []
        if exists
        else [
            {
                "id": "missing-file",
                "verdict": "fail",
                "message": f"file does not exist: {path}",
            }
        ],
    }


def main() -> int:
    return run_main(verify)


if __name__ == "__main__":
    raise SystemExit(main())
