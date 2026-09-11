#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from bensz_skill_kernel.verifier_script_helpers import evidence_map, result, run_main


def _value(item: Any, key: str) -> Any:
    return item.get(key) if isinstance(item, Mapping) else getattr(item, key, None)


def verify(request, evidence=None):
    evidence_items = evidence_map(request, evidence)
    invalid = [
        ref
        for ref, item in evidence_items.items()
        if not _value(item, "source_type")
        or not _value(item, "content_hash")
        or not _value(item, "collected_at")
    ]
    return result(
        not invalid,
        {"evidence_count": len(evidence_items)},
        "missing-provenance",
        invalid,
    )


if __name__ == "__main__":
    raise SystemExit(run_main(verify))
