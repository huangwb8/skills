#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.verifier_script_helpers import request_parts, result, run_main


def verify(request, evidence=None):
    subject, context = request_parts(request)
    raw_paths = subject.get("paths") or ([subject["path"]] if subject.get("path") else [])
    allowed = [Path(item).expanduser().resolve() for item in context.get("allowed_paths", ())]
    violations = []
    for raw in raw_paths:
        target = Path(raw).expanduser().resolve()
        # Scope is lexical after resolve() and must not depend on an allowed
        # directory already existing.
        if not any(target == root or root in target.parents for root in allowed):
            violations.append(str(target))
    return result(
        not violations,
        {"paths": list(raw_paths), "violations": violations},
        "path-out-of-scope",
        violations,
    )


if __name__ == "__main__":
    raise SystemExit(run_main(verify))
