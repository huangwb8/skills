#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.verifier_script_helpers import request_parts, result, run_main


def verify(request, evidence=None):
    subject, context = request_parts(request)
    data = subject.get("data", subject)
    schema = context.get("schema", {})
    required = schema.get("required", ()) if isinstance(schema, Mapping) else ()
    missing = [
        key
        for key in required
        if not isinstance(data, Mapping) or key not in data
    ]
    return result(not missing, {"missing": missing}, "schema-required-field", missing)


if __name__ == "__main__":
    raise SystemExit(run_main(verify))
