#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.verifier_script_helpers import request_parts, result, run_main


def verify(request, evidence=None):
    subject, context = request_parts(request)
    required = tuple(
        context.get(
            "required_fields",
            ("artifacts", "verifications", "delivery_report"),
        )
    )
    missing = [key for key in required if not subject.get(key)]
    return result(not missing, {"missing": missing}, "task-incomplete", missing)


if __name__ == "__main__":
    raise SystemExit(run_main(verify))
