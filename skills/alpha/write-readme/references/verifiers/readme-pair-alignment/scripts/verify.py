#!/usr/bin/env python3
"""JSON-stdio adapter for the write-readme pair checker."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


def _load_checker():
    skill_root = Path(__file__).resolve().parents[4]
    checker_path = skill_root / "scripts" / "check_readme_pair.py"
    spec = importlib.util.spec_from_file_location("write_readme_pair_checker", checker_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("checker module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _result(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        return {"execution_status": "error", "verdict": "error", "summary": "request must be a JSON object"}
    subject = request.get("subject")
    if not isinstance(subject, dict):
        return {"execution_status": "error", "verdict": "error", "summary": "subject must be a JSON object"}
    zh_raw, en_raw = subject.get("zh_path"), subject.get("en_path")
    if not isinstance(zh_raw, str) or not isinstance(en_raw, str) or not zh_raw or not en_raw:
        return {"execution_status": "error", "verdict": "error", "summary": "subject requires zh_path and en_path"}
    try:
        context = request.get("context", {})
        project_root = context.get("project_root") if isinstance(context, dict) else None
        base = Path(project_root).expanduser().resolve() if isinstance(project_root, str) and project_root else None
        def resolve(raw: str) -> Path:
            path = Path(raw).expanduser()
            return (base / path).resolve() if base is not None and not path.is_absolute() else path
        checker = _load_checker()
        result = checker.check_pair(resolve(zh_raw), resolve(en_raw))
    except (OSError, UnicodeError, RuntimeError, ValueError) as exc:
        return {"execution_status": "error", "verdict": "error", "summary": f"checker error: {type(exc).__name__}"}
    errors = list(result["errors"])
    warnings = list(result["warnings"])
    facts = dict(result["facts"])
    refs = [item.get("ref") for item in request.get("evidence", ()) if isinstance(item, dict) and item.get("ref")]
    if errors:
        return {
            "execution_status": "completed",
            "verdict": "fail",
            "summary": "README pair has structural or reference errors",
            "findings": [{"kind": "error", "message": item} for item in errors],
            "facts": facts,
            "evidence_refs": refs,
        }
    if warnings:
        return {
            "execution_status": "completed",
            "verdict": "uncertain",
            "summary": "README structure passes, but machine-token drift needs semantic review",
            "findings": [{"kind": "warning", "message": item} for item in warnings],
            "facts": facts,
            "evidence_refs": refs,
            "uncertainty_reason": "token drift requires AI or human equivalence review",
        }
    return {
        "execution_status": "completed",
        "verdict": "pass",
        "summary": "README pair is structurally aligned",
        "facts": facts,
        "evidence_refs": refs,
    }


def main() -> int:
    try:
        request = json.load(sys.stdin)
        payload = _result(request)
    except (json.JSONDecodeError, OSError):
        payload = {"execution_status": "error", "verdict": "error", "summary": "invalid JSON request"}
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
