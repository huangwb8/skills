#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.verifier_script_helpers import request_parts, result, run_main


def verify(request, evidence=None):
    subject, context = request_parts(request)
    changed = set(subject.get("changed_paths", ()))
    violations = sorted(changed - set(context.get("allowed_paths", ())))
    return result(
        not violations,
        {"changed": sorted(changed), "violations": violations},
        "unexpected-change",
        violations,
    )


if __name__ == "__main__":
    raise SystemExit(run_main(verify))
