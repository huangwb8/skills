#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.runtime import EventLog
from bensz_skill_kernel.verifier_script_helpers import request_parts, result, run_main


def verify(request, evidence=None):
    subject, _context = request_parts(request)
    path = subject.get("path")
    if not path:
        return result(False, {}, "missing-events-path", ["events"])
    try:
        count = len(EventLog(path).read())
    except Exception as exc:
        return {
            "verdict": "fail",
            "uncertainty_reason": str(exc),
            "findings": [{"id": "event-integrity", "verdict": "fail"}],
        }
    return {"verdict": "pass", "facts": {"event_count": count}, "findings": []}


if __name__ == "__main__":
    raise SystemExit(run_main(verify))
