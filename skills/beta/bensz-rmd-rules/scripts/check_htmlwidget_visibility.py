#!/usr/bin/env python3
"""
Static checker for R Markdown (.Rmd) htmlwidget visibility issues.

Goal: prevent the common failure mode "code chunk shows, but HTML doesn't render the widget"
when DT::datatable()/plotly/etc. are wrapped in print()/invisible() or are not returned as
the chunk's visible result.

This is intentionally heuristic (fast, no R execution). It focuses on high-signal patterns.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


_CHUNK_START_RE = re.compile(r"^\s*```+\s*\{r([^}]*)\}\s*$")
_CHUNK_END_RE = re.compile(r"^\s*```+\s*$")

# Common htmlwidget constructors / wrappers we want to keep visible in HTML.
_WIDGET_CALL_RE = re.compile(
    r"(?P<call>"
    r"DT::datatable\s*\("
    r"|render_dt_output\s*\("
    r"|render_dt\s*\("
    r"|plotly::"
    r"|leaflet::"
    r"|reactable::"
    r"|highcharter::"
    r"|visNetwork::"
    r"|dygraphs::"
    r"|htmlwidgets::"
    r")"
)

_BAD_WRAPPER_RE = re.compile(
    r"\b(?P<wrapper>print|invisible|suppressMessages|suppressWarnings)\s*\("
)

_ASSIGN_WIDGET_RE = re.compile(
    r"^\s*(?P<var>[.A-Za-z][\w.]*)\s*<-\s*.*("
    r"DT::datatable\s*\("
    r"|render_dt_output\s*\("
    r"|render_dt\s*\("
    r"|plotly::"
    r"|leaflet::"
    r"|reactable::"
    r"|highcharter::"
    r"|visNetwork::"
    r"|dygraphs::"
    r"|htmlwidgets::"
    r")"
)

_TAGLIST_RE = re.compile(r"\b(htmltools::)?tagList\s*\(")


@dataclass(frozen=True)
class Finding:
    severity: str  # "ERROR" | "WARN"
    path: Path
    line: int
    chunk: str
    message: str


def _chunk_label(chunk_header: str) -> str:
    # header like: " data-preview, message=FALSE"
    # We consider the first token as the label if it's not an option assignment.
    tokens = [t.strip() for t in chunk_header.strip().lstrip().split(",") if t.strip()]
    if not tokens:
        return "<unnamed>"
    first = tokens[0]
    if "=" in first:
        return "<unnamed>"
    return first


def _is_comment_or_blank(line: str) -> bool:
    s = line.strip()
    return (not s) or s.startswith("#")


def _last_meaningful_line(lines: list[str]) -> tuple[int, str] | None:
    for i in range(len(lines) - 1, -1, -1):
        if _is_comment_or_blank(lines[i]):
            continue
        return i, lines[i].strip()
    return None


def _has_bad_wrapper(line: str) -> bool:
    # High-signal: print(invisible(...)) etc around a widget call on the same line.
    if not _BAD_WRAPPER_RE.search(line):
        return False
    return _WIDGET_CALL_RE.search(line) is not None


def _is_assigned_widget_line(line: str) -> bool:
    return _ASSIGN_WIDGET_RE.search(line) is not None


_R_STRING_RE = re.compile(
    r"("  # Replace strings to avoid counting parentheses inside them.
    r"\"(?:[^\"\\\n]|\\.)*\""  # "..."
    r"|'(?:[^'\\\n]|\\.)*'"  # '...'
    r"|`[^`\n]*`"  # `...`
    r")"
)


def _strip_strings_and_comments(line: str) -> str:
    # Remove R comments (heuristic: everything after #) after stripping string literals.
    # This is intentionally lightweight; we only need stable parenthesis counting.
    no_str = _R_STRING_RE.sub('""', line)
    return no_str.split("#", 1)[0]


def _find_expr_end_idx0(lines: list[str], start_idx0: int) -> int | None:
    """
    Find the last (meaningful) line index of the expression starting at start_idx0.

    We use parenthesis depth counting across lines. This is heuristic but works well for
    common multi-line function calls like:

      DT::datatable(
        ...,
        options = list(...)
      )
    """
    depth = 0
    seen = False
    last_meaningful_idx0: int | None = None

    for j in range(start_idx0, len(lines)):
        raw = lines[j]
        if _is_comment_or_blank(raw):
            continue

        last_meaningful_idx0 = j
        s = _strip_strings_and_comments(raw)
        opens = s.count("(")
        closes = s.count(")")

        if opens or closes:
            seen = True
        depth += opens - closes

        # When we've returned to depth 0, the expression is closed.
        if seen and depth <= 0:
            return last_meaningful_idx0

    return None


def check_rmd(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_chunk = False
    chunk_header = ""
    chunk_name = "<outside>"
    chunk_start_line = 0  # 1-based
    chunk_lines: list[str] = []

    def flush_chunk() -> None:
        nonlocal chunk_lines
        if not in_chunk:
            chunk_lines = []
            return

        assigned_widget_vars: set[str] = set()
        naked_widget_calls: list[tuple[int, str]] = []  # (0-based chunk line idx, line)

        for idx0, l in enumerate(chunk_lines):
            if _has_bad_wrapper(l):
                findings.append(
                    Finding(
                        severity="ERROR",
                        path=path,
                        line=chunk_start_line + idx0,
                        chunk=chunk_name,
                        message=(
                            "htmlwidget 被 print()/invisible()/suppress*() 包裹，HTML 可能不渲染；"
                            "请让 widget 作为 chunk 的可见返回值输出（不要包裹）。"
                        ),
                    )
                )

            m_assign = _ASSIGN_WIDGET_RE.search(l)
            if m_assign:
                assigned_widget_vars.add(m_assign.group("var"))

            if _WIDGET_CALL_RE.search(l):
                if _is_assigned_widget_line(l):
                    continue
                # Heuristic: if '<-' appears before the match, treat it as assigned (avoid FP).
                m_call = _WIDGET_CALL_RE.search(l)
                assert m_call is not None
                before = l[: m_call.start()]
                if "<-" in before:
                    continue
                naked_widget_calls.append((idx0, l))

        last = _last_meaningful_line(chunk_lines)
        if last is None:
            chunk_lines = []
            return
        last_idx0, last_line = last

        # Rule: if we have naked widget calls, the chunk must end by returning a widget / tagList / widget var.
        if naked_widget_calls:
            ok = False
            if _WIDGET_CALL_RE.search(last_line):
                ok = True
            elif _TAGLIST_RE.search(last_line):
                ok = True
            elif last_line in assigned_widget_vars:
                ok = True
            else:
                # Multi-line widget call: the last meaningful line might be just ")". In that case,
                # check whether the last expression *started* with a naked widget call and ends at last_idx0.
                for idx0, _ in reversed(naked_widget_calls):
                    end_idx0 = _find_expr_end_idx0(chunk_lines, idx0)
                    if end_idx0 is not None and end_idx0 == last_idx0:
                        ok = True
                        break

            if not ok:
                first_idx0, _ = naked_widget_calls[0]
                findings.append(
                    Finding(
                        severity="ERROR",
                        path=path,
                        line=chunk_start_line + first_idx0,
                        chunk=chunk_name,
                        message=(
                            "检测到 htmlwidget 调用，但该 chunk 的最后表达式不是 widget/tagList/已赋值的 widget 变量；"
                            "这通常会导致 HTML 不出表/不出图。"
                        ),
                    )
                )

            # Rule: multiple naked widgets must be returned via tagList.
            if len(naked_widget_calls) > 1 and not _TAGLIST_RE.search(last_line):
                first_idx0, _ = naked_widget_calls[0]
                findings.append(
                    Finding(
                        severity="ERROR",
                        path=path,
                        line=chunk_start_line + first_idx0,
                        chunk=chunk_name,
                        message=(
                            "同一 chunk 内检测到多个 htmlwidget 需要展示，但末尾未使用 htmltools::tagList(...) 统一返回；"
                            "通常只会渲染最后一个。"
                        ),
                    )
                )

        chunk_lines = []

    for i, line in enumerate(lines, start=1):
        if not in_chunk:
            m = _CHUNK_START_RE.match(line)
            if m:
                in_chunk = True
                chunk_header = m.group(1) or ""
                chunk_name = _chunk_label(chunk_header)
                chunk_start_line = i + 1  # code starts next line
                chunk_lines = []
            continue

        # in chunk
        if _CHUNK_END_RE.match(line):
            flush_chunk()
            in_chunk = False
            chunk_header = ""
            chunk_name = "<outside>"
            chunk_start_line = 0
            chunk_lines = []
            continue

        chunk_lines.append(line)

    # Unclosed chunk (still analyze).
    if in_chunk:
        flush_chunk()

    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Check Rmd htmlwidget visibility pitfalls (DT/plotly/etc.)",
    )
    parser.add_argument("paths", nargs="+", help="Rmd file(s) to check")
    args = parser.parse_args(argv)

    all_findings: list[Finding] = []
    for p in args.paths:
        path = Path(p)
        if not path.exists():
            print(f"ERROR: not found: {path}", file=sys.stderr)
            return 2
        if path.is_dir():
            # Keep it simple: only *.Rmd directly under the directory (no recursion by default).
            for f in sorted(path.glob("*.Rmd")):
                all_findings.extend(check_rmd(f))
        else:
            all_findings.extend(check_rmd(path))

    if not all_findings:
        return 0

    # Stable output order.
    all_findings.sort(key=lambda f: (str(f.path), f.line, f.severity))

    for f in all_findings:
        loc = f"{f.path}:{f.line}"
        chunk = f"[chunk: {f.chunk}]"
        print(f"{f.severity}: {loc} {chunk} {f.message}")

    has_errors = any(f.severity == "ERROR" for f in all_findings)
    return 2 if has_errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
