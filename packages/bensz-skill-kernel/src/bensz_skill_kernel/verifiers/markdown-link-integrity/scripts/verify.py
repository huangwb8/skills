#!/usr/bin/env python3
import json
import sys

try:
    from .collector import collect_markdown
except ImportError:
    # The entrypoint is executed as a file by the filesystem registry, so the
    # scripts directory is on sys.path but is not a Python package.
    from collector import collect_markdown


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
    unresolved = report["summary"].get("unresolved", 0)
    findings = [
        {"id": "invalid-reference", "verdict": "fail", "reference": item.get("index"), "message": item.get("validation", {}).get("error")}
        for item in report["references"]
        if item.get("validation", {}).get("validation_status") == "invalid"
    ]
    timed_out = report["summary"].get("timed_out", 0)
    verdict = "fail" if invalid else ("timed_out" if unresolved and timed_out == unresolved else ("unchecked" if unresolved else "pass"))
    execution_status = "timed_out" if verdict == "timed_out" else ("unchecked" if unresolved and not invalid else "completed")
    json.dump({"execution_status": execution_status, "verdict": verdict, "facts": report, "findings": findings,
               "uncertainty_reason": "one or more URLs could not be observed" if unresolved else None}, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
