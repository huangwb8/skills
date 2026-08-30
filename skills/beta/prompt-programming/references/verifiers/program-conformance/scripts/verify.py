"""Deterministic Prompt Program structure verifier (JSON in / JSON out)."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


MAX_PROGRAM_CHARS = 200_000
VERIFIER_ID = "bensz.prompt.contract-conformance"
VERIFIER_VERSION = "1.0.0"
DEFAULT_BLOCKS = ("目标", "输入", "输出", "流程", "校验", "返回")
BLOCK_ORDER = ("程序", "目标", "输入", "输出", "定义", "约束", "流程", "校验", "缺口处理", "返回")
BLOCK_RE = re.compile(r"^\s*(程序|目标|输入|输出|定义|约束|流程|校验|缺口处理|返回)\s*[:：]\s*(.*)$")
CONTROL_RE = re.compile(r"(若|如果|否则|对每个|重复|直到|条件|if\b|for\b|while\b|fallback)", re.I)


def _result(verdict: str, findings: list[dict[str, Any]], facts: dict[str, Any], *, execution_status: str = "completed") -> dict[str, Any]:
    # Include stable identity so the Kernel can recompute and bind the Gate.
    return {
        "verifier_id": VERIFIER_ID,
        "verifier_version": VERIFIER_VERSION,
        "execution_status": execution_status,
        "verdict": verdict,
        "findings": findings,
        "facts": facts,
        "assurance_tier": "deterministic",
    }


def main(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        return _result("error", [{"code": "invalid-request", "message": "request must be a JSON object"}], {})
    subject = request.get("subject")
    if not isinstance(subject, dict):
        return _result("error", [{"code": "missing-subject", "message": "subject must be an object"}], {})
    program = subject.get("program")
    if not isinstance(program, str) or not program.strip():
        return _result("error", [{"code": "missing-program", "message": "subject.program must be a non-empty string"}], {})
    if len(program) > MAX_PROGRAM_CHARS:
        return _result("error", [{"code": "program-too-large", "message": "subject.program exceeds size limit"}], {})

    context = request.get("context")
    if context is None:
        context = {}
    if not isinstance(context, dict):
        return _result("error", [{"code": "invalid-context", "message": "context must be an object"}], {})
    required = context.get("required_blocks", list(DEFAULT_BLOCKS))
    if not isinstance(required, list) or not required or any(not isinstance(item, str) or item not in BLOCK_ORDER for item in required):
        return _result("error", [{"code": "invalid-required-blocks", "message": "context.required_blocks must contain known block labels"}], {})
    required = list(dict.fromkeys(required))

    blocks: list[tuple[str, int, str]] = []
    for line_no, line in enumerate(program.splitlines(), 1):
        match = BLOCK_RE.match(line)
        if match:
            blocks.append((match.group(1), line_no, match.group(2).strip()))
    positions = {name: [index for index, block in enumerate(blocks) if block[0] == name] for name in required}
    findings: list[dict[str, Any]] = []
    for name in required:
        if not positions[name]:
            findings.append({"code": "missing-block", "block": name})
        elif len(positions[name]) > 1:
            findings.append({"code": "duplicate-block", "block": name, "count": len(positions[name])})
        else:
            index = positions[name][0]
            if not blocks[index][2]:
                findings.append({"code": "empty-block", "block": name, "line": blocks[index][1]})
    present = [(index, block[0]) for index, block in enumerate(blocks) if block[0] in required]
    expected = [name for name in BLOCK_ORDER if name in required and positions[name]]
    actual = [name for _, name in present]
    if actual != expected:
        findings.append({"code": "block-order", "expected": expected, "actual": actual})
    if context.get("control_required"):
        flow = next((block[2] for block in blocks if block[0] == "流程"), "")
        if not CONTROL_RE.search(flow):
            findings.append({"code": "missing-control", "message": "流程 lacks a conditional or iteration marker"})
    facts = {"blocks": [block[0] for block in blocks], "required_blocks": required, "block_count": len(blocks)}
    return _result("pass" if not findings else "fail", findings, facts)


def run() -> None:
    try:
        payload = json.load(sys.stdin)
        output = main(payload)
    except json.JSONDecodeError:
        output = _result("error", [{"code": "invalid-json", "message": "stdin must contain one JSON object"}], {}, execution_status="error")
    except Exception as exc:  # fail closed without exposing input
        output = _result("error", [{"code": "internal-error", "message": type(exc).__name__}], {}, execution_status="error")
    json.dump(output, sys.stdout, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    run()
