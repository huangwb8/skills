#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from common_config import get_skill_root, load_config


SCRIPT_PATH = Path(__file__)
SKILL_ROOT = get_skill_root(SCRIPT_PATH)
CONFIG = load_config(SKILL_ROOT)
PARALLEL_CFG = CONFIG["parallel_review"]
REVIEW_POLICY = CONFIG.get("review_policy") or {}
RESULT_FILENAME = str(PARALLEL_CFG["result_filename"])
REQUIRED_RESULT_SECTIONS = [str(item) for item in (PARALLEL_CFG.get("required_result_sections") or [])]
ALLOWED_RECOMMENDATIONS = {str(item) for item in (REVIEW_POLICY.get("final_recommendations") or [])}
ALLOWED_RISK_LEVELS = {str(item) for item in (REVIEW_POLICY.get("risk_levels") or [])}
ALLOWED_CONFIDENCE_LEVELS = {str(item) for item in (PARALLEL_CFG.get("confidence_levels") or ["High", "Medium", "Low"])}

REC_RE = re.compile(r"^- Recommendation:\s*(.+?)\s*$", re.MULTILINE)
RISK_RE = re.compile(r"^- Risk Level:\s*(.+?)\s*$", re.MULTILINE)
CONF_RE = re.compile(r"^- Confidence:\s*(.+?)\s*$", re.MULTILINE)


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def _load_job(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"job file is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("job file must be a JSON object")
    return payload


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract(pattern: re.Pattern[str], text: str) -> str:
    m = pattern.search(text)
    return m.group(1).strip() if m else "Unknown"


def _expected_thread_ids(review_count: int) -> list[str]:
    width = int(PARALLEL_CFG["thread_id_width"])
    return [str(index).zfill(width) for index in range(1, review_count + 1)]


def _validate_result_text(text: str) -> list[str]:
    issues: list[str] = []
    for section in REQUIRED_RESULT_SECTIONS:
        if section not in text:
            issues.append(f"missing required section {section!r}")

    recommendation = _extract(REC_RE, text)
    risk_level = _extract(RISK_RE, text)
    confidence = _extract(CONF_RE, text)
    if recommendation == "Unknown":
        issues.append("missing Recommendation field")
    elif ALLOWED_RECOMMENDATIONS and recommendation not in ALLOWED_RECOMMENDATIONS:
        issues.append(f"invalid Recommendation: {recommendation}")
    if risk_level == "Unknown":
        issues.append("missing Risk Level field")
    elif ALLOWED_RISK_LEVELS and risk_level not in ALLOWED_RISK_LEVELS:
        issues.append(f"invalid Risk Level: {risk_level}")
    if confidence == "Unknown":
        issues.append("missing Confidence field")
    elif ALLOWED_CONFIDENCE_LEVELS and confidence not in ALLOWED_CONFIDENCE_LEVELS:
        issues.append(f"invalid Confidence: {confidence}")
    return issues


def _thread_entries(project_root: Path, expected_thread_ids: list[str]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    entries: list[dict[str, Any]] = []
    missing_threads: list[str] = []
    invalid_threads: list[str] = []
    for thread_id in expected_thread_ids:
        child = project_root / thread_id
        if not child.is_dir():
            missing_threads.append(f"{thread_id} (missing thread directory)")
            continue
        result_path = child / RESULT_FILENAME
        if not result_path.exists():
            missing_threads.append(f"{thread_id} (missing {RESULT_FILENAME})")
            continue
        text = _read_text(result_path)
        thread_json = child / "thread.json"
        title = child.name
        if thread_json.exists():
            try:
                title = json.loads(thread_json.read_text(encoding="utf-8")).get("title") or title
            except Exception:
                pass
        issues = _validate_result_text(text)
        if issues:
            invalid_threads.append(f"{thread_id} ({'; '.join(issues)})")
            continue
        entries.append(
            {
                "thread_id": child.name,
                "title": title,
                "result_path": str(result_path),
                "recommendation": _extract(REC_RE, text),
                "risk_level": _extract(RISK_RE, text),
                "confidence": _extract(CONF_RE, text),
                "excerpt": "\n".join(line for line in text.splitlines()[:20]).strip(),
            }
        )
    return entries, missing_threads, invalid_threads


def _mode_or_mixed(values: list[str]) -> str:
    filtered = [v for v in values if v and v != "Unknown"]
    if not filtered:
        return "Unknown"
    counts = Counter(filtered).most_common()
    if len(counts) > 1 and counts[0][1] == counts[1][1]:
        return "Mixed"
    return counts[0][0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate parallel-vibe independent PR review results.")
    parser.add_argument("--job-file", required=True, help="Path to parallel_review_job.json")
    args = parser.parse_args()

    job_path = Path(args.job_file).expanduser().resolve()
    if not job_path.exists():
        return fail(f"job file not found: {job_path}")
    try:
        job = _load_job(job_path)
    except ValueError as exc:
        return fail(str(exc))
    for key in ("project_root", "aggregate_markdown", "aggregate_json", "review_count"):
        if key not in job:
            return fail(f"job file missing required field: {key}")
    project_root = Path(job["project_root"]).resolve()
    aggregate_md = Path(job["aggregate_markdown"]).resolve()
    aggregate_json = Path(job["aggregate_json"]).resolve()
    review_count = int(job["review_count"])
    if review_count < 1:
        return fail(f"review_count must be >= 1: {review_count}")
    if not project_root.exists() or not project_root.is_dir():
        recommended = job.get("recommended_command")
        hint = f"; run `{recommended}` first" if recommended else ""
        return fail(f"parallel review project root not found: {project_root}{hint}")

    entries, missing_threads, invalid_threads = _thread_entries(project_root, _expected_thread_ids(review_count))
    if missing_threads:
        return fail("parallel review outputs are incomplete: " + ", ".join(missing_threads))
    if invalid_threads:
        return fail("parallel review outputs are invalid: " + ", ".join(invalid_threads))
    if not entries:
        return fail(f"no {RESULT_FILENAME} files found under {project_root}")
    rec_counts = Counter(entry["recommendation"] for entry in entries)
    risk_counts = Counter(entry["risk_level"] for entry in entries)
    consensus = {
        "recommendation": _mode_or_mixed([entry["recommendation"] for entry in entries]),
        "risk_level": _mode_or_mixed([entry["risk_level"] for entry in entries]),
    }
    payload = {
        "expected_review_count": review_count,
        "review_count": len(entries),
        "project_root": str(project_root),
        "consensus": consensus,
        "recommendation_counts": dict(rec_counts),
        "risk_counts": dict(risk_counts),
        "threads": entries,
    }
    aggregate_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Independent Review Summary",
        "",
        f"- Expected Review Count: {review_count}",
        f"- Review Count: {len(entries)}",
        f"- Project Root: `{project_root}`",
        f"- Consensus Recommendation: {consensus['recommendation']}",
        f"- Consensus Risk Level: {consensus['risk_level']}",
        "",
        "## Recommendation Distribution",
    ]
    for key, value in sorted(rec_counts.items()):
        md_lines.append(f"- {key}: {value}")
    md_lines.extend(["", "## Risk Distribution"])
    for key, value in sorted(risk_counts.items()):
        md_lines.append(f"- {key}: {value}")
    md_lines.extend(["", "## Review Matrix", "| Thread | Title | Recommendation | Risk | Confidence |", "|------|------|------|------|------|"])
    for entry in entries:
        md_lines.append(
            f"| {entry['thread_id']} | {entry['title']} | {entry['recommendation']} | {entry['risk_level']} | {entry['confidence']} |"
        )
    md_lines.extend(["", "## Per-Thread Excerpts"])
    for entry in entries:
        md_lines.extend([
            f"### Thread {entry['thread_id']} - {entry['title']}",
            f"- Result Path: `{entry['result_path']}`",
            "",
            "```markdown",
            entry["excerpt"],
            "```",
            "",
        ])
    md_lines.extend([
        "## Guidance For Final Report",
        "- 在最终 `Git-PR-Review_*.md` 中新增 `## 独立评审综合结果` 章节。",
        "- 先报告 recommendation / risk 的分布，再写共识与分歧。",
        "- 若共识为 `Mixed`，必须明确说明主要分歧点。",
    ])
    aggregate_md.write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"aggregate_markdown": str(aggregate_md), "aggregate_json": str(aggregate_json)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
