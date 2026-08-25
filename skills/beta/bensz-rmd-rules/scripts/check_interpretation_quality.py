#!/usr/bin/env python3
"""
Lightweight static checks for Rmd interpretation text.

Goal: detect obvious "non-evidence-anchored" patterns before rendering/review.
This is intentionally heuristic (not 100% accurate).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


FENCE_RE = re.compile(r"^\s*```")
YAML_DELIM_RE = re.compile(r"^\s*---\s*$")
HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")

# Prefer multi-word phrases to reduce false positives.
DEFAULT_BLACKLIST = [
    r"建议进一步研究",
    r"值得进一步研究",
    r"建议进一步验证",
    r"需要进一步验证",
    r"值得深入探讨",
    r"提示可能",
    r"可能提示",
    r"为.*提供依据",
]

INLINE_R_RE = re.compile(r"`r\s+[^`]+`")
TOP_RE = re.compile(r"\bTop\s*\d+\b|\btop\s*\d+\b|前\s*\d+\b|最强信号")
UNCERTAINTY_RE = re.compile(
    r"\bCI\b|置信区间|\bSE\b|标准误|bootstrap|Bootstr|交叉验证|\bCV\b|稳定性|敏感性分析",
    re.IGNORECASE,
)
BOLD_SPAN_RE = re.compile(r"\*\*[^*\n]+\*\*")
NUMBER_RE = re.compile(r"(?<![A-Za-z_])\d+(?:\.\d+)?%?")
ENTITY_LIKE_RE = re.compile(r"`[^`\n]+`|\b[A-Za-z][A-Za-z0-9_.-]{2,}\b")

INTERP_SECTION_RE = re.compile(r"(结果解读|讨论与分析|讨论|interpretation|discussion)", re.IGNORECASE)
INTERP_BOLD_MARKER_RE = re.compile(r"\*\*\s*结果解读\s*\*\*|结果解读\s*[:：]")

TIER_LABEL_LINE_RE = re.compile(
    r"^\s*(?:\*\*)?\s*(数据描述|统计见解|领域见解|局限与后续)\s*(?:\*\*)?\s*[:：]\s*",
    re.IGNORECASE,
)

ACTION_SENTENCE_RE = re.compile(r"(后续|下一步|建议|可通过|可用|推荐|验证|复核)", re.IGNORECASE)
ACTION_METHOD_RE = re.compile(
    r"(用|采用|通过|进行|复算|复现|验证|检验|调整|校正|分层|多因素|bootstrap|CV)",
    re.IGNORECASE,
)
ACTION_INPUT_RE = re.compile(r"(在|使用|基于|输入|数据|表|列|图|队列|样本|模型|结果)", re.IGNORECASE)
ACTION_CRITERION_RE = re.compile(
    r"(判据|阈值|满足|支持|不支持|若|当|>=|<=|≥|≤|<|>|p\\s*[<=>]|q\\s*[<=>])",
    re.IGNORECASE,
)

STRONG_CLAIM_RE = re.compile(r"(更支持|支持真实|证明|证实|确定|无疑)", re.IGNORECASE)

# Mechanical anti-pattern: "fill-the-structure" four-part template.
DEFAULT_MECHANICAL_TEMPLATE_PATTERNS = [
    (
        r"这张(?:图|表|图/表).{0,20}?(?:在)?本次.{0,20}?直接观察是[:：].*?"
        r"统计.{0,20}?含义是[:：].*?"
        r"研究者.{0,20}?意义是[:：].*?"
        r"(?:你可以)?(?:立即)?(?:执行)?的?下一步"
    )
]

# Vague phrases are not forbidden *per se*; they become failures when they lack
# nearby evidence (entity + number/inline-R) and/or executable next steps.
DEFAULT_VAGUE_PHRASE_PATTERNS = [
    r"提示可能",
    r"可能提示",
    r"值得深入探讨",
    r"需要进一步研究",
    r"建议进一步研究",
    r"建议进一步验证",
    r"需要进一步验证",
    r"为.*提供依据",
]

# Broad markers for "this time / current data" statements.
# We combine this with NUMBER/INLINE_R evidence to reduce false positives.
CURRENT_OBS_MARKERS_RE = re.compile(
    r"(本次|当前数据|该结果|结果显示|数据显示|我们观察到|在本次分析中|在当前队列中|\bN\s*=\s*\d+\b|样本量|在\s*\d+\s*(?:个)?\s*(?:样本|患者))",
    re.IGNORECASE,
)

# Expression-style checks (optional, can be noisy).
TITLE_PAREN_RE = re.compile(r"[（(].+[）)]")
TITLE_SUBTITLE_RE = re.compile(r"\s-\s")
TEACHING_MARKERS = [
    r"提示：",
    r"注意：",
    r"需要注意的是",
    r"即：",
    r"即:",
    r"用于快速识别",
    r"用于快速判断",
    r"帮助你判断",
    r"用于把方向落到",
]


def _iter_non_fenced_non_yaml_lines(text: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for non-fenced lines, skipping YAML frontmatter if present."""
    out: list[tuple[int, str]] = []
    in_fence = False
    in_yaml = False
    yaml_delims_seen = 0

    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\n")

        if i <= 200 and YAML_DELIM_RE.match(line):
            # Only treat YAML frontmatter when it starts at the beginning of the file.
            if i == 1 and yaml_delims_seen == 0:
                in_yaml = True
                yaml_delims_seen = 1
                continue
            if in_yaml and yaml_delims_seen == 1:
                in_yaml = False
                yaml_delims_seen = 2
                continue

        if in_yaml:
            continue

        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        out.append((i, line))

    return out


def _compile_many(patterns: object) -> list[re.Pattern[str]]:
    res: list[re.Pattern[str]] = []
    if not isinstance(patterns, list):
        return res
    for p in patterns:
        if not isinstance(p, str) or not p.strip():
            continue
        try:
            res.append(re.compile(p))
        except re.error:
            continue
    return res


def _untracked_number_issues(text: str, *, exempt_res: list[re.Pattern[str]]) -> list[str]:
    """
    Heuristic: report literal numbers in non-code prose lines that do not have inline `r ...`.
    Returns issue strings with line numbers for actionable fixes.
    """
    issues: list[str] = []
    for ln, line in _iter_non_fenced_non_yaml_lines(text):
        if not line.strip():
            continue
        if INLINE_R_RE.search(line):
            # Treat inline-R presence on this line as "tracked enough" to avoid over-blocking.
            continue
        bad = False
        for m in NUMBER_RE.finditer(line):
            window = line[max(0, m.start() - 24) : min(len(line), m.end() + 24)]
            if any(r.search(window) for r in exempt_res):
                continue
            bad = True
            break
        if bad:
            issues.append(f"L{ln}: literal numbers without inline `r ...`: {line.strip()[:200]}")
    return issues


def strip_fenced_blocks(text: str) -> str:
    """Remove fenced code blocks (``` ... ```), keeping only prose."""
    lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def split_sentences(prose: str) -> list[str]:
    parts = re.split(r"[。！？!?]+|\n{2,}", prose)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        sub = re.split(r"\n(?=(?:\s*[-*]\s+|\s*\d+[.)]\s+))", p)
        out.extend([s.strip() for s in sub if s.strip()])
    return out


def count_current_observations(prose: str) -> int:
    """
    Count sentences that look like "current-data observations":
    - has a marker like '本次/当前数据/结果显示/...'
    - AND has numeric evidence (inline `r ...` OR a literal number)
    """
    count = 0
    for sent in split_sentences(prose):
        if not CURRENT_OBS_MARKERS_RE.search(sent):
            continue
        if INLINE_R_RE.search(sent) or NUMBER_RE.search(sent):
            count += 1
    return count


def _skill_root() -> Path:
    # scripts/xxx.py -> {skill_root}/scripts/xxx.py
    return Path(__file__).resolve().parents[1]


def _load_yaml_config() -> dict[str, object]:
    config_path = _skill_root() / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except Exception:
        return {}
    try:
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(cfg, dict):
            return {}
        return cfg
    except Exception:
        return {}


def _get_cfg_section(cfg: dict[str, object], key: str) -> dict[str, object]:
    sec = cfg.get(key, {})
    if isinstance(sec, dict):
        return sec
    return {}


@dataclass(frozen=True)
class Block:
    title: str
    start_line: int
    end_line: int
    prose: str


def _non_fenced_lines(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((i, line))
    return out


def _extract_heading_blocks(text: str) -> list[Block]:
    lines = _non_fenced_lines(text)
    headings: list[tuple[int, int, str]] = []
    for line_no, line in lines:
        m = HEADING_RE.match(line)
        if not m:
            continue
        headings.append((line_no, len(m.group(1)), m.group(2).strip()))

    if not headings:
        return []

    blocks: list[Block] = []
    total_lines = len(text.splitlines())
    for idx, (h_line, h_level, h_title) in enumerate(headings):
        if not INTERP_SECTION_RE.search(h_title):
            continue
        start_line = h_line + 1
        end_line = total_lines
        for j in range(idx + 1, len(headings)):
            n_line, n_level, _ = headings[j]
            if n_line <= h_line:
                continue
            if n_level <= h_level:
                end_line = n_line - 1
                break
        buf: list[str] = []
        for line_no, line in lines:
            if start_line <= line_no <= end_line:
                buf.append(line)
        blocks.append(Block(title=h_title, start_line=start_line, end_line=end_line, prose="\n".join(buf).strip()))
    return blocks


def _extract_bold_marker_blocks(text: str) -> list[Block]:
    lines = _non_fenced_lines(text)
    markers = [line_no for line_no, line in lines if INTERP_BOLD_MARKER_RE.search(line)]
    if not markers:
        return []
    total_lines = len(text.splitlines())
    blocks: list[Block] = []
    for idx, marker_line in enumerate(markers):
        start_line = marker_line + 1
        end_line = (markers[idx + 1] - 1) if idx + 1 < len(markers) else total_lines
        buf: list[str] = []
        for line_no, line in lines:
            if start_line <= line_no <= end_line:
                buf.append(line)
        blocks.append(Block(title="**结果解读** marker", start_line=start_line, end_line=end_line, prose="\n".join(buf).strip()))
    return blocks


def extract_interpretation_blocks(text: str) -> list[Block]:
    blocks = _extract_heading_blocks(text)
    if blocks:
        return blocks
    return _extract_bold_marker_blocks(text)


def _top_grounded(prose: str) -> bool:
    for m in TOP_RE.finditer(prose):
        window = prose[m.start() : min(len(prose), m.end() + 120)]
        if INLINE_R_RE.search(window) or ENTITY_LIKE_RE.search(window):
            return True
    return False


def _actionability_issues(prose: str) -> list[str]:
    issues: list[str] = []
    for sent in split_sentences(prose):
        if not ACTION_SENTENCE_RE.search(sent):
            continue
        missing: list[str] = []
        if not ACTION_METHOD_RE.search(sent):
            missing.append("method")
        if not ACTION_INPUT_RE.search(sent):
            missing.append("input")
        if not ACTION_CRITERION_RE.search(sent):
            missing.append("criterion")
        if missing:
            issues.append(f"missing {','.join(missing)}: {sent[:160]}")
    return issues


def _strong_claim_issues(prose: str) -> list[str]:
    issues: list[str] = []
    for sent in split_sentences(prose):
        if not STRONG_CLAIM_RE.search(sent):
            continue
        if (INLINE_R_RE.search(sent) or NUMBER_RE.search(sent)) and UNCERTAINTY_RE.search(sent):
            continue
        issues.append(f"strong-claim without evidence+stability guard: {sent[:160]}")
    return issues


def _uncertainty_value_issues(prose: str) -> list[str]:
    issues: list[str] = []
    for sent in split_sentences(prose):
        if not UNCERTAINTY_RE.search(sent):
            continue
        if INLINE_R_RE.search(sent) or NUMBER_RE.search(sent):
            continue
        issues.append(sent[:160])
    return issues


def _mechanical_template_hits(prose: str, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for pat in patterns:
        try:
            if re.search(pat, prose, flags=re.DOTALL):
                hits.append(pat)
        except re.error:
            continue
    return hits


def _vague_phrase_issues(
    prose: str, patterns: list[str], window_chars: int = 160, require_entity: bool = True
) -> list[str]:
    issues: list[str] = []
    for pat in patterns:
        try:
            for m in re.finditer(pat, prose):
                start = max(0, m.start() - window_chars)
                end = min(len(prose), m.end() + window_chars)
                window = prose[start:end]

                has_number = bool(INLINE_R_RE.search(window) or NUMBER_RE.search(window))
                has_entity = bool(ENTITY_LIKE_RE.search(window))

                if require_entity:
                    if has_entity and has_number:
                        continue
                else:
                    if has_number or has_entity:
                        continue

                snippet = prose[m.start() : min(len(prose), m.end() + 40)].replace("\n", " ").strip()
                issues.append(f"{pat}: {snippet[:160]}")
        except re.error:
            continue
    return issues


def scan_headings(text: str) -> list[dict[str, object]]:
    """Return heading issues outside fenced code blocks."""
    in_fence = False
    bad: list[dict[str, object]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        issues: list[str] = []
        if TITLE_PAREN_RE.search(title):
            issues.append("parenthetical_note")
        if TITLE_SUBTITLE_RE.search(title):
            issues.append("main_subtitle_dash")
        if issues:
            bad.append({"line": i, "level": level, "title": title, "issues": issues})
    return bad


def scan_text(text: str) -> dict[str, object]:
    blocks = extract_interpretation_blocks(text)
    if blocks:
        prose = "\n\n".join(b.prose for b in blocks if b.prose.strip())
        mode = "interpretation_blocks"
    else:
        prose = strip_fenced_blocks(text)
        mode = "all_prose"

    inline_r = INLINE_R_RE.findall(prose)
    top_hits = TOP_RE.findall(prose)
    uncertainty_hits = UNCERTAINTY_RE.findall(prose)
    bold_spans = BOLD_SPAN_RE.findall(prose)
    current_obs_count = count_current_observations(prose)
    tier_label_line_count = sum(1 for ln in prose.splitlines() if TIER_LABEL_LINE_RE.search(ln))
    action_sentence_count = sum(1 for sent in split_sentences(prose) if ACTION_SENTENCE_RE.search(sent))

    blacklist_hits: list[str] = []
    for pat in DEFAULT_BLACKLIST:
        if re.search(pat, prose):
            blacklist_hits.append(pat)

    teaching_hits: list[str] = []
    for pat in TEACHING_MARKERS:
        if re.search(pat, prose):
            teaching_hits.append(pat)

    bad_headings = scan_headings(text)

    return {
        "mode": mode,
        "_prose": prose,
        "inline_r_count": len(inline_r),
        "current_observation_count": current_obs_count,
        "top_hits": top_hits,
        "uncertainty_hits": uncertainty_hits,
        "blacklist_hits": blacklist_hits,
        "bold_span_count": len(bold_spans),
        "teaching_hits": teaching_hits,
        "tier_label_line_count": tier_label_line_count,
        "action_sentence_count": action_sentence_count,
        "blocks": blocks,
        "top_grounded": _top_grounded(prose),
        "actionability_issues": _actionability_issues(prose),
        "strong_claim_issues": _strong_claim_issues(prose),
        "uncertainty_value_issues": _uncertainty_value_issues(prose),
        "bad_headings": bad_headings,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Heuristic checks for evidence-anchored interpretation in .Rmd files."
    )
    p.add_argument("files", nargs="+", help="One or more .Rmd files to check.")
    p.add_argument(
        "--min-inline-r",
        type=int,
        default=None,
        help="Minimum count of inline R snippets (`r ...`) in prose (default: 3).",
    )
    p.add_argument(
        "--min-current-observation",
        type=int,
        default=None,
        help=(
            "Minimum count of 'current data observation' sentences in prose (default: 3). "
            "A sentence counts if it includes a marker like '本次/当前数据/结果显示' and also includes numeric evidence "
            "(inline `r ...` or a literal number). Set to 0 to disable."
        ),
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Enable stricter anti-template checks: require grounded Top list in interpretation sections, "
            "flag strong claims without evidence+stability guard, and require stability mentions to include current values."
        ),
    )
    p.add_argument(
        "--warn-only",
        action="store_true",
        help="Print findings but always exit 0 (useful for CI pre-check).",
    )
    p.add_argument(
        "--check-title-style",
        action="store_true",
        default=None,
        help="Check headings for '(...)'/'（...）' and ' - ' main-subtitle style (off by default).",
    )
    p.add_argument(
        "--check-tone",
        action="store_true",
        default=None,
        help="Check for teaching-style markers like '提示：/注意：/需要注意的是' (off by default).",
    )
    p.add_argument(
        "--max-teaching-hits",
        type=int,
        default=None,
        help="Max allowed teaching-tone marker hits when check-tone is enabled (default: 0).",
    )
    p.add_argument(
        "--check-actionability",
        action="store_true",
        default=None,
        help="Check that next-step suggestions include method+input+criterion (off by default).",
    )
    p.add_argument(
        "--max-actionability-issues",
        type=int,
        default=None,
        help="Max allowed actionability issues when check-actionability is enabled (default: 0).",
    )
    p.add_argument(
        "--check-template-labels",
        action="store_true",
        default=None,
        help="Check for repeated '数据描述/统计见解/...' label-lines (off by default).",
    )
    p.add_argument(
        "--max-tier-label-lines",
        type=int,
        default=None,
        help="Max allowed tier-label lines when check-template-labels is enabled (default: 8).",
    )
    p.add_argument(
        "--check-bold",
        action="store_true",
        default=None,
        help="Check for excessive bold spans '**...**' in prose (off by default).",
    )
    p.add_argument(
        "--max-bold-per-1000",
        type=float,
        default=None,
        help="Max bold spans per 1000 chars when --check-bold is enabled (default: 10).",
    )

    args = p.parse_args(argv)

    global DEFAULT_BLACKLIST, TEACHING_MARKERS

    cfg = _load_yaml_config()
    cfg_sec = _get_cfg_section(cfg, "interpretation_quality_check")
    if cfg_sec.get("enabled") is False:
        print("[PASS] interpretation quality check disabled by config.yaml")
        return 0

    min_inline_r = args.min_inline_r
    if min_inline_r is None:
        min_inline_r = int(cfg_sec.get("min_inline_r", 3))

    min_current_observation = args.min_current_observation
    if min_current_observation is None:
        min_current_observation = int(cfg_sec.get("min_current_observation", 3))

    # Recommended structure gates (default: off; strict: on).
    require_top_hits = bool(cfg_sec.get("require_top_hits", False))
    require_uncertainty_hits = bool(cfg_sec.get("require_uncertainty_hits", False))
    require_actionability = bool(cfg_sec.get("require_actionability", False))
    if args.strict:
        require_top_hits = True
        require_uncertainty_hits = True
        require_actionability = True

    # Traceable numbers gate (heuristic).
    check_untracked_numbers = bool(cfg_sec.get("check_untracked_numbers", True))
    max_untracked_numbers = int(cfg_sec.get("max_untracked_numbers", 1))
    if args.strict:
        max_untracked_numbers = 0
    untracked_exempt_res = _compile_many(cfg_sec.get("untracked_number_exempt_patterns", []))

    blacklist_patterns = cfg_sec.get("blacklist_patterns", None)
    if blacklist_patterns is None:
        blacklist_patterns = DEFAULT_BLACKLIST
    if not isinstance(blacklist_patterns, list):
        blacklist_patterns = DEFAULT_BLACKLIST

    check_title_style = args.check_title_style
    if check_title_style is None:
        check_title_style = bool(cfg_sec.get("check_title_style", False))

    check_tone = args.check_tone
    if check_tone is None:
        check_tone = bool(cfg_sec.get("check_tone", False))

    max_teaching_hits = args.max_teaching_hits
    if max_teaching_hits is None:
        max_teaching_hits = int(cfg_sec.get("max_teaching_hits", 0))

    teaching_markers = cfg_sec.get("teaching_markers", None)
    if teaching_markers is None:
        teaching_markers = TEACHING_MARKERS
    if not isinstance(teaching_markers, list):
        teaching_markers = TEACHING_MARKERS

    check_actionability = args.check_actionability
    if check_actionability is None:
        check_actionability = bool(cfg_sec.get("check_actionability", False))

    max_actionability_issues = args.max_actionability_issues
    if max_actionability_issues is None:
        max_actionability_issues = int(cfg_sec.get("max_actionability_issues", 0))

    check_template_labels = args.check_template_labels
    if check_template_labels is None:
        check_template_labels = bool(cfg_sec.get("check_template_labels", False))

    max_tier_label_lines = args.max_tier_label_lines
    if max_tier_label_lines is None:
        max_tier_label_lines = int(cfg_sec.get("max_tier_label_lines", 8))

    check_bold = args.check_bold
    if check_bold is None:
        check_bold = bool(cfg_sec.get("check_bold", False))

    max_bold_per_1000 = args.max_bold_per_1000
    if max_bold_per_1000 is None:
        max_bold_per_1000 = float(cfg_sec.get("max_bold_per_1000", 10.0))

    mechanical_template_patterns = cfg_sec.get("mechanical_template_patterns", None)
    if mechanical_template_patterns is None:
        mechanical_template_patterns = DEFAULT_MECHANICAL_TEMPLATE_PATTERNS
    if not isinstance(mechanical_template_patterns, list):
        mechanical_template_patterns = DEFAULT_MECHANICAL_TEMPLATE_PATTERNS
    check_mechanical_templates = bool(cfg_sec.get("check_mechanical_templates", True))
    max_mechanical_template_hits = int(cfg_sec.get("max_mechanical_template_hits", 0))

    vague_phrase_patterns = cfg_sec.get("vague_phrase_patterns", None)
    if vague_phrase_patterns is None:
        vague_phrase_patterns = DEFAULT_VAGUE_PHRASE_PATTERNS
    if not isinstance(vague_phrase_patterns, list):
        vague_phrase_patterns = DEFAULT_VAGUE_PHRASE_PATTERNS
    check_vague_phrases = bool(cfg_sec.get("check_vague_phrases", True))
    vague_phrase_window_chars = int(cfg_sec.get("vague_phrase_window_chars", 160))
    max_vague_phrase_issues = int(cfg_sec.get("max_vague_phrase_issues", 0))

    DEFAULT_BLACKLIST = blacklist_patterns
    TEACHING_MARKERS = teaching_markers

    any_fail = False

    for fp in args.files:
        path = Path(fp)
        if not path.exists():
            print(f"[FAIL] {fp}: file not found")
            any_fail = True
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        r = scan_text(text)

        inline_r_count = int(r["inline_r_count"])
        current_obs_count = int(r["current_observation_count"])
        top_hits = r["top_hits"]
        uncertainty_hits = r["uncertainty_hits"]
        blacklist_hits = r["blacklist_hits"]
        bold_span_count = int(r["bold_span_count"])
        teaching_hits = r["teaching_hits"]
        tier_label_line_count = int(r.get("tier_label_line_count", 0))
        actionability_issues = list(r.get("actionability_issues", []))
        action_sentence_count = int(r.get("action_sentence_count", 0))
        top_grounded = bool(r.get("top_grounded", False))
        strong_claim_issues = list(r.get("strong_claim_issues", []))
        uncertainty_value_issues = list(r.get("uncertainty_value_issues", []))
        bad_headings = r["bad_headings"]
        prose_for_checks = str(r.get("_prose") or "")

        failures: list[str] = []
        if inline_r_count < min_inline_r:
            failures.append(f"inline `r ...` too few: {inline_r_count} < {min_inline_r}")
        if min_current_observation > 0 and current_obs_count < min_current_observation:
            failures.append(
                "current-data observations too few: "
                f"{current_obs_count} < {min_current_observation} "
                "(need sentences with markers like '本次/当前数据/结果显示' + numeric evidence; "
                "each observation must describe THIS data, not generic rules)"
            )
        if require_top_hits and (not top_hits):
            failures.append("missing Top signal hint (e.g. 'Top 3' / '前3' / '最强信号')")
        if require_uncertainty_hits and (not uncertainty_hits):
            failures.append("missing uncertainty/stability hint (e.g. CI/SE/bootstrap/CV)")
        if require_actionability and action_sentence_count <= 0:
            failures.append("missing actionable next-step sentence (need at least 1 sentence with method+input+criterion)")
        if blacklist_hits:
            failures.append(f"blacklist phrases found: {', '.join(blacklist_hits)}")

        if check_untracked_numbers:
            issues = _untracked_number_issues(text, exempt_res=untracked_exempt_res)
            if len(issues) > max_untracked_numbers:
                failures.append(
                    f"untracked literal numbers: {len(issues)} lines (limit={max_untracked_numbers}); e.g. {issues[0]}"
                )

        if check_mechanical_templates:
            hits = _mechanical_template_hits(prose=prose_for_checks, patterns=mechanical_template_patterns)
            if len(hits) > max_mechanical_template_hits:
                failures.append(
                    f"mechanical template detected: {len(hits)} (limit={max_mechanical_template_hits})"
                )

        if check_vague_phrases:
            issues = _vague_phrase_issues(
                prose=prose_for_checks,
                patterns=vague_phrase_patterns,
                window_chars=vague_phrase_window_chars,
                require_entity=True,
            )
            if len(issues) > max_vague_phrase_issues:
                failures.append(
                    f"vague phrases without local evidence: {len(issues)} issues (limit={max_vague_phrase_issues}); "
                    f"e.g. {issues[0]}"
                )

        if check_title_style and bad_headings:
            examples = "; ".join(
                f"L{h['line']}:{h['title']}({','.join(h['issues'])})" for h in bad_headings[:5]
            )
            failures.append(f"non-natural headings found: {len(bad_headings)} (e.g. {examples})")

        if check_tone and teaching_hits and len(teaching_hits) > max_teaching_hits:
            failures.append(
                f"teaching-style markers found (limit={max_teaching_hits}): {', '.join(teaching_hits)}"
            )

        if check_template_labels and tier_label_line_count > max_tier_label_lines:
            failures.append(
                f"tier-label lines too many: {tier_label_line_count} > {max_tier_label_lines} "
                "(suggest narrative style and hide '数据描述/统计见解/...' labels)"
            )

        if check_actionability and len(actionability_issues) > max_actionability_issues:
            failures.append(
                f"non-actionable next steps: {len(actionability_issues)} issues (limit={max_actionability_issues}); "
                f"e.g. {'; '.join(actionability_issues[:3])}"
            )

        if args.strict:
            if top_hits and not top_grounded:
                failures.append(
                    "Top mention looks ungrounded: found 'Top 3/前3/最强信号' but no nearby entity-like token or inline `r ...` "
                    "in interpretation sections"
                )
            if strong_claim_issues:
                failures.append("strong claims need evidence+stability guard; e.g. " + "; ".join(strong_claim_issues[:3]))
            if uncertainty_value_issues:
                failures.append(
                    "uncertainty/stability mentioned without current value evidence; e.g. "
                    + "; ".join(uncertainty_value_issues[:3])
                )

        if check_bold:
            per_1000 = bold_span_count / max(1.0, len(strip_fenced_blocks(text)) / 1000.0)
            if per_1000 > max_bold_per_1000:
                failures.append(
                    f"bold spans too dense: {bold_span_count} spans (~{per_1000:.1f}/1000 chars) > {max_bold_per_1000}"
                )

        if failures:
            any_fail = True
            print(f"[FAIL] {fp}")
            for f in failures:
                print(f"  - {f}")
        else:
            mode = r.get("mode", "scan")
            print(f"[PASS] {fp} ({mode}; inline_r={inline_r_count}, current_obs={current_obs_count})")

    if args.warn_only:
        return 0
    return 2 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
