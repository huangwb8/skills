#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.runtime import ALLOWED_TRANSITIONS
from bensz_skill_kernel.verifier_script_helpers import request_parts, result, run_main


def verify(request, evidence=None):
    subject, _context = request_parts(request)
    current, target = subject.get("current_state"), subject.get("target_state")
    allowed = target in ALLOWED_TRANSITIONS.get(current, ())
    return result(
        allowed,
        {"current_state": current, "target_state": target},
        "illegal-transition",
        [target] if not allowed else [],
    )


if __name__ == "__main__":
    raise SystemExit(run_main(verify))
