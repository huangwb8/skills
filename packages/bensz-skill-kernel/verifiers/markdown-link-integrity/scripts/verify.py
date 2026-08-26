#!/usr/bin/env python3
import json
import sys
from pathlib import Path

try:
    from bensz_skill_kernel.builtins import collect_markdown
except ModuleNotFoundError:
    src = Path(__file__).resolve().parents[4] / "src"
    sys.path.insert(0, str(src))
    from bensz_skill_kernel.builtins import collect_markdown


def main() -> int:
    request = json.load(sys.stdin)
    subject = request.get("subject") or {}
    path = subject.get("path")
    if not path:
        json.dump({"execution_status": "completed", "verdict": "fail", "findings": [{"id": "missing-path", "message": "subject.path is required"}]}, sys.stdout)
        return 0
    context = request.get("context") or {}
    try:
        report = collect_markdown(
            path,
            timeout=int(context.get("timeout", 10)),
            blacklist=tuple(context.get("blacklist", ())),
            whitelist=tuple(context.get("whitelist", ())),
        )
    except Exception as exc:
        json.dump({"execution_status": "error", "verdict": "error", "uncertainty_reason": str(exc)}, sys.stdout)
        return 0
    invalid = report["summary"]["invalid"]
    findings = [
        {"id": "invalid-reference", "verdict": "fail", "reference": item.get("index"), "message": item.get("validation", {}).get("error")}
        for item in report["references"]
        if not item.get("validation", {}).get("valid") and not item.get("validation", {}).get("skipped")
    ]
    json.dump({"execution_status": "completed", "verdict": "fail" if invalid else "pass", "facts": report, "findings": findings}, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
