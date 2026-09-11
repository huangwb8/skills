#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.verifier_script_helpers import request_parts, run_main


def verify(request, evidence=None):
    subject, _context = request_parts(request)
    raw = json.dumps(subject, ensure_ascii=False, default=str)
    patterns = (
        r"[\"']?(?:api[_-]?key|token|password|cookie)[\"']?\s*[:=]\s*[\"']?[^,\s}\"']+",
        r"sk-[A-Za-z0-9_-]{8,}",
    )
    matches = [pattern for pattern in patterns if re.search(pattern, raw, re.IGNORECASE)]
    return {
        "verdict": "fail" if matches else "pass",
        "facts": {"matched_patterns": len(matches)},
        "findings": [{"id": "secret-detected", "verdict": "fail"}] if matches else [],
    }


if __name__ == "__main__":
    raise SystemExit(run_main(verify))
