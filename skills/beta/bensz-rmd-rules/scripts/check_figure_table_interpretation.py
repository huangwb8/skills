#!/usr/bin/env python3
"""
Hard-coded coverage check: ensure every *visible* figure/table output chunk in a .Rmd
has a nearby, evidence-anchored interpretation in Markdown prose.

Why this exists:
- Existing checks focus on interpretation *quality* for already-written prose.
- This script focuses on interpretation *coverage*: "there is output, there is interpretation".

Design goals (KISS):
- No knitr execution, purely static.
- Heuristic detection (best-effort), configurable via config.yaml.
- Fail fast in --strict mode to block delivery when coverage is incomplete.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


FENCE_START_RE = re.compile(r"^\s*```{r\b(?P<header>[^}]*)}\s*$")
FENCE_END_RE = re.compile(r"^\s*```\s*$")

NEXT_FENCE_ANY_RE = re.compile(r"^\s*```")
HEADING_RE = re.compile(r"^\s*#{1,6}\s+")

FIG_REF_RE = re.compile(r"(?:Figure|Fig|图)\s*(\d+[a-zA-Z]?)", re.IGNORECASE)
TAB_REF_RE = re.compile(r"(?:Table|表)\s*(\d+[a-zA-Z]?)", re.IGNORECASE)

HAS_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[A-Za-z]+")

_CONFIG_WARNED = False


def _skill_root() -> Path:
    # scripts/xxx.py -> {skill_root}/scripts/xxx.py
    return Path(__file__).resolve().parents[1]


def _warn_once(msg: str) -> None:
    global _CONFIG_WARNED
    if _CONFIG_WARNED:
        return
    _CONFIG_WARNED = True
    print(msg, file=sys.stderr)


def _load_yaml_config() -> dict[str, Any]:
    config_path = _skill_root() / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except Exception:
        _warn_once(
            "[WARN] PyYAML not available; config.yaml will be ignored and defaults will be used. "
            "Install PyYAML to enable configurable checks."
        )
        return {}
    try:
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(cfg, dict):
            _warn_once("[WARN] config.yaml parsed but is not a mapping; ignoring config.")
            return {}
        return cfg
    except Exception as e:
        _warn_once(f"[WARN] Failed to parse config.yaml; ignoring config and using defaults. Error: {e}")
        return {}


def _as_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


@dataclass(frozen=True)
class Chunk:
    start_line: int
    end_line: int
    header: str
    label: str | None
    options_raw: str
    code: str


@dataclass(frozen=True)
class OutputItem:
    kind: str  # "figure" | "table" | "mixed"
    start_line: int
    end_line: int
    chunk_label: str | None
    reason: str


@dataclass(frozen=True)
class MatchResult:
    output: OutputItem
    ok: bool
    details: str
    interpretation_preview: str | None


def _split_header_parts(header: str) -> list[str]:
    # Best-effort split by comma, respecting simple quotes.
    parts: list[str] = []
    buf: list[str] = []
    in_squote = False
    in_dquote = False
    for ch in header:
        if ch == "'" and not in_dquote:
            in_squote = not in_squote
        elif ch == '"' and not in_squote:
            in_dquote = not in_dquote
        if ch == "," and not in_squote and not in_dquote:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_chunk_header(header: str) -> tuple[str | None, dict[str, str]]:
    parts = _split_header_parts(header.strip())
    label: str | None = None
    options: dict[str, str] = {}

    for idx, p in enumerate(parts):
        if "=" in p:
            k, v = p.split("=", 1)
            options[k.strip()] = v.strip()
            continue
        # First non k=v token is commonly the chunk label.
        if idx == 0 and p and p.lower() != "r":
            label = p.strip()
    return label, options


def _is_hidden_chunk(options: dict[str, str]) -> bool:
    # Coverage check is for *visible* outputs in the rendered report.
    def _truthy(v: str) -> bool:
        return v.strip().lower() in {"true", "t", "1", "yes"}

    def _norm(v: str) -> str:
        return v.strip().strip("'\"").lower()

    # Escape hatch: for rare cases where a chunk matches output patterns
    # but is intentionally non-output (e.g. constructing a ggplot object only).
    if "interp_check" in options and not _truthy(options["interp_check"]):
        return True

    if "eval" in options and not _truthy(options["eval"]):
        return True
    if "include" in options and not _truthy(options["include"]):
        return True
    # Plots can be explicitly hidden without disabling execution.
    if "fig.show" in options and "hide" in _norm(options["fig.show"]):
        return True
    if "fig.keep" in options and "none" in _norm(options["fig.keep"]):
        return True
    return False


def parse_rmd_chunks(text: str) -> list[Chunk]:
    lines = text.splitlines()
    chunks: list[Chunk] = []
    in_chunk = False
    header = ""
    start_line = 0
    code_lines: list[str] = []

    for i, line in enumerate(lines, start=1):
        if not in_chunk:
            m = FENCE_START_RE.match(line)
            if m:
                in_chunk = True
                header = m.group("header") or ""
                start_line = i
                code_lines = []
            continue

        # in_chunk
        if FENCE_END_RE.match(line):
            in_chunk = False
            label, options = _parse_chunk_header(header)
            chunks.append(
                Chunk(
                    start_line=start_line,
                    end_line=i,
                    header=header,
                    label=label,
                    options_raw=header,
                    code="\n".join(code_lines).strip("\n"),
                )
            )
            header = ""
            start_line = 0
            code_lines = []
            continue

        code_lines.append(line)

    return chunks


def _compile_any(patterns: Iterable[str]) -> list[re.Pattern[str]]:
    out: list[re.Pattern[str]] = []
    for p in patterns:
        try:
            out.append(re.compile(p, re.IGNORECASE))
        except re.error:
            # Ignore broken patterns in config rather than crash.
            continue
    return out


def detect_outputs(chunks: list[Chunk], cfg: dict[str, Any]) -> list[OutputItem]:
    section = (cfg.get("figure_interpretation_check") or {}) if isinstance(cfg, dict) else {}

    fig_pats = _as_list(((section.get("check_patterns") or {}).get("figure_generation")))
    tab_pats = _as_list(((section.get("check_patterns") or {}).get("table_generation")))

    # Conservative defaults to reduce false negatives while staying readable.
    if not fig_pats:
        fig_pats = [
            r"\bggplot\s*\(",
            r"\bgeom_[a-zA-Z0-9_]+\s*\(",
            r"\bplot\s*\(",
            r"\bheatmap\b",
            r"\bComplexHeatmap\b",
            r"\bHeatmap\s*\(",
            r"\bpheatmap\s*\(",
            r"\bggsave\s*\(",
            r"\bpdf\s*\(",
            r"\bpng\s*\(",
            r"\btiff\s*\(",
            r"\bjpeg\s*\(",
        ]
    if not tab_pats:
        tab_pats = [
            r"\bknitr::kable\s*\(",
            r"\bkable\s*\(",
            r"\bDT::datatable\s*\(",
            r"\bgt::gt\s*\(",
            r"\bflextable::flextable\s*\(",
            r"\breactable::reactable\s*\(",
        ]

    fig_re = _compile_any(fig_pats)
    tab_re = _compile_any(tab_pats)

    outputs: list[OutputItem] = []
    for c in chunks:
        _label, options = _parse_chunk_header(c.header)
        if _is_hidden_chunk(options):
            continue

        code = c.code
        fig_hit = next((r.pattern for r in fig_re if r.search(code)), None)
        tab_hit = next((r.pattern for r in tab_re if r.search(code)), None)

        # Also treat chunks with fig.cap/fig.caption as figure outputs.
        if not fig_hit:
            for k in ("fig.cap", "fig.caption"):
                if k in options:
                    fig_hit = f"chunk_option:{k}"
                    break

        if not fig_hit and not tab_hit:
            continue

        kind = "mixed" if (fig_hit and tab_hit) else ("figure" if fig_hit else "table")
        reason = fig_hit or tab_hit or "pattern"
        outputs.append(
            OutputItem(
                kind=kind,
                start_line=c.start_line,
                end_line=c.end_line,
                chunk_label=c.label,
                reason=reason,
            )
        )

    return outputs


def _extract_prose_window(lines: list[str], start_line: int, max_lines: int) -> tuple[str, int]:
    """
    Return (prose_text, end_line) starting *after* start_line, stopping at next fence
    or max_lines, whichever comes first.
    """
    start_idx = min(len(lines), start_line)  # 1-based line -> 0-based idx after it
    end_idx = min(len(lines), start_idx + max_lines)
    buf: list[str] = []
    last_line_num = start_line

    for idx in range(start_idx, end_idx):
        line = lines[idx]
        line_num = idx + 1
        if NEXT_FENCE_ANY_RE.match(line):
            break
        buf.append(line)
        last_line_num = line_num

    return "\n".join(buf).strip(), last_line_num


def _is_interpretation_valid(
    prose: str,
    *,
    required_markers: list[re.Pattern[str]],
    require_ref: bool,
    min_cjk_chars: int,
    min_en_words: int,
    min_content_elements: int,
) -> tuple[bool, str]:
    # Remove headings-only / whitespace-only.
    raw_lines = [ln.rstrip() for ln in prose.splitlines()]
    lines = [ln for ln in raw_lines if ln.strip()]
    if not lines:
        return False, "no prose after output chunk"

    non_heading = [ln for ln in lines if not HEADING_RE.match(ln)]
    text = "\n".join(non_heading).strip()
    if not text:
        return False, "only headings found after output chunk"

    # Length check (language-aware-ish).
    has_cjk = bool(HAS_CJK_RE.search(text))
    cjk_chars = sum(1 for ch in text if HAS_CJK_RE.match(ch))
    en_words = len(WORD_RE.findall(text))

    if has_cjk and cjk_chars < min_cjk_chars:
        return False, f"interpretation too short (CJK chars {cjk_chars} < {min_cjk_chars})"
    if (not has_cjk) and en_words < min_en_words:
        return False, f"interpretation too short (EN words {en_words} < {min_en_words})"

    # Reference check (optional, but recommended).
    if require_ref:
        if not (FIG_REF_RE.search(text) or TAB_REF_RE.search(text)):
            return False, "missing explicit figure/table reference (e.g., 'Figure 1'/'图 1')"

    # Marker check (e.g. '解读/结论/观察' markers).
    if required_markers:
        if not any(r.search(text) for r in required_markers):
            return False, "missing interpretation markers (e.g., '解读/结论/小结/观察')"

    # Content elements: require at least N evidence-anchoring elements.
    elements = 0
    if re.search(r"展示|显示|show|display", text, re.IGNORECASE):
        elements += 1
    if re.search(r"高于|低于|差异|difference|higher|lower|increase|decrease", text, re.IGNORECASE):
        elements += 1
    if re.search(r"p\\s*[<>=]\\s*0\\.\\d+|显著|significant|FDR|q\\s*[<>=]", text, re.IGNORECASE):
        elements += 1
    if re.search(r"提示|表明|suggest|indicat", text, re.IGNORECASE):
        elements += 1
    if elements < min_content_elements:
        return False, f"content elements insufficient ({elements} < {min_content_elements})"

    return True, "ok"


def check_coverage(
    rmd_path: Path,
    *,
    max_distance_lines: int,
    strict_reference: bool,
    interpretation_marker_patterns: list[str],
    min_cjk_chars: int,
    min_en_words: int,
    min_content_elements: int,
) -> dict[str, Any]:
    text = rmd_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    chunks = parse_rmd_chunks(text)
    cfg = _load_yaml_config()
    outputs = detect_outputs(chunks, cfg)

    marker_res = _compile_any(interpretation_marker_patterns)

    results: list[MatchResult] = []
    for out in outputs:
        prose, _ = _extract_prose_window(lines, out.end_line, max_distance_lines)

        ok, details = _is_interpretation_valid(
            prose,
            required_markers=marker_res,
            require_ref=strict_reference,
            min_cjk_chars=min_cjk_chars,
            min_en_words=min_en_words,
            min_content_elements=min_content_elements,
        )
        preview = None
        if prose:
            preview = "\n".join([ln for ln in prose.splitlines() if ln.strip()][:8]).strip()
        results.append(
            MatchResult(
                output=out,
                ok=ok,
                details=details,
                interpretation_preview=preview,
            )
        )

    unmatched = [r for r in results if not r.ok]

    return {
        "file": str(rmd_path),
        "total_outputs": len(outputs),
        "unmatched_outputs": len(unmatched),
        "pass": len(unmatched) == 0,
        "unmatched_details": [
            {
                "kind": r.output.kind,
                "start_line": r.output.start_line,
                "end_line": r.output.end_line,
                "chunk_label": r.output.chunk_label,
                "reason": r.output.reason,
                "details": r.details,
                "interpretation_preview": r.interpretation_preview,
            }
            for r in unmatched
        ],
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Coverage check for figure/table interpretations in .Rmd files."
    )
    p.add_argument("rmd_file", type=Path, help="Path to a .Rmd file")
    p.add_argument("--strict", action="store_true", help="Exit non-zero if check fails")
    p.add_argument("--json", action="store_true", help="Print JSON report")
    p.add_argument(
        "--max-distance-lines",
        type=int,
        default=None,
        help="Max allowed line distance from output chunk end to interpretation prose (default: from config.yaml or 50)",
    )
    p.add_argument(
        "--require-reference",
        action="store_true",
        help="Require explicit 'Figure/Table/图/表 N' reference in interpretation prose (stricter, fewer false passes).",
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument(
        "--require-markers",
        action="store_true",
        default=None,
        help="Require interpretation markers (default: follow config.yaml).",
    )
    g.add_argument(
        "--no-require-markers",
        action="store_true",
        default=None,
        help="Disable interpretation marker requirement (default: follow config.yaml).",
    )
    p.add_argument(
        "--min-cjk-chars",
        type=int,
        default=None,
        help="Minimum CJK char count for interpretation prose when CJK is detected (default: from config.yaml or 100)",
    )
    p.add_argument(
        "--min-en-words",
        type=int,
        default=None,
        help="Minimum English word count for interpretation prose when no CJK is detected (default: from config.yaml or 50)",
    )
    p.add_argument(
        "--min-content-elements",
        type=int,
        default=None,
        help="Require at least N evidence-anchoring elements in interpretation prose (default: from config.yaml or 2)",
    )

    args = p.parse_args(argv)
    if not args.rmd_file.exists():
        print(f"[FAIL] file not found: {args.rmd_file}", file=sys.stderr)
        return 1

    # Allow config.yaml to set defaults while keeping CLI explicit override.
    cfg = _load_yaml_config()
    sec = cfg.get("figure_interpretation_check") if isinstance(cfg, dict) else None
    sec = sec if isinstance(sec, dict) else {}

    enabled = bool(sec.get("enabled", True))
    if not enabled:
        # Explicitly disabled -> always pass (no-op).
        report = {
            "file": str(args.rmd_file),
            "total_outputs": 0,
            "unmatched_outputs": 0,
            "pass": True,
            "note": "figure_interpretation_check.disabled",
        }
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print("[PASS] figure/table interpretation coverage check is disabled by config.yaml")
        return 0

    check_patterns = sec.get("check_patterns") if isinstance(sec.get("check_patterns"), dict) else {}
    has_marker_key = "interpretation_markers" in check_patterns
    marker_patterns = _as_list(check_patterns.get("interpretation_markers"))
    if (not marker_patterns) and (not has_marker_key):
        # Neutral fallback markers (avoid forcing tier labels).
        marker_patterns = [
            r"解读",
            r"结论",
            r"小结",
            r"观察",
            r"核心结论",
            r"结果(?:显示|表明|提示|可见)",
            r"\binterpretation\b",
            r"\btakeaway\b",
            r"(?:图|表|Figure|Table)\s*\d+.*?(?:解读|分析|结果|interpretation|analysis)",
        ]

    # Config defaults (CLI still overrides via flags).
    max_distance = int(sec.get("max_distance_lines", 50)) if args.max_distance_lines is None else int(args.max_distance_lines)
    min_layers = int(sec.get("required_layers", 4))  # informational; not enforced directly
    _ = min_layers
    strict_mode = bool(sec.get("strict_mode", False))
    require_ref_default = bool(sec.get("require_reference", False))

    if args.require_markers is True:
        require_markers = True
    elif args.no_require_markers is True:
        require_markers = False
    else:
        require_markers = bool(sec.get("require_markers", True))

    # If require_markers=false OR marker list empty -> skip marker check entirely.
    if (not require_markers) or (not marker_patterns):
        marker_patterns = []

    min_cjk_chars = (
        int(sec.get("min_cjk_chars", 100)) if args.min_cjk_chars is None else int(args.min_cjk_chars)
    )
    min_en_words = int(sec.get("min_en_words", 50)) if args.min_en_words is None else int(args.min_en_words)
    min_content_elements = (
        int(sec.get("min_content_elements", 2))
        if args.min_content_elements is None
        else int(args.min_content_elements)
    )

    report = check_coverage(
        args.rmd_file,
        max_distance_lines=max_distance,
        strict_reference=bool(args.require_reference or require_ref_default),
        interpretation_marker_patterns=marker_patterns,
        min_cjk_chars=min_cjk_chars,
        min_en_words=min_en_words,
        min_content_elements=min_content_elements,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("图表/表格-解读覆盖检验报告")
        print(f"文件: {report['file']}")
        print("-" * 60)
        print(f"检测到的输出块数: {report['total_outputs']}")
        print(f"未通过块数: {report['unmatched_outputs']}")

        if report["unmatched_outputs"]:
            print("\n未通过明细（需要补充/加强解读）：")
            for d in report["unmatched_details"]:
                lab = f" chunk={d['chunk_label']}" if d.get("chunk_label") else ""
                print(
                    f"- {d['kind']} L{d['start_line']}-L{d['end_line']}{lab}: {d['details']}"
                )
                if d.get("interpretation_preview"):
                    prev = str(d["interpretation_preview"]).strip().replace("\t", "  ")
                    if prev:
                        print("  现有解读片段（预览）:")
                        for ln in prev.splitlines()[:6]:
                            print(f"    {ln}")

        print("\n" + ("[PASS] 通过" if report["pass"] else "[FAIL] 未通过"))

    should_fail = (args.strict or strict_mode) and (not report["pass"])
    return 2 if should_fail else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
