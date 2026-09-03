#!/usr/bin/env python3
"""Deterministic checks for the bilingual README contract.

The checker deliberately avoids judging prose quality. It reports structural
and reference drift so an AI or human can perform the semantic review.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
TOKEN_PATTERNS = {
    "commands": re.compile(r"(?m)^\s*(?:[$>]\s*)?(?:python3?|pip|uv|npm|pnpm|yarn|cargo|go|docker|make|bsk|curl)\s+[^\n`]+"),
    "env": re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b"),
    "versions": re.compile(r"\bv?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?\b"),
}


def headings(text: str) -> list[int]:
    result = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            # Compare the structural tree, not translated heading text.
            result.append(len(match.group(1)))
    return result


def fence_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if FENCE_RE.match(line))


def relative_links(text: str) -> list[str]:
    links = []
    for raw in LINK_RE.findall(text):
        target = raw.strip().split(" ", 1)[0].strip("<>")
        if target and not re.match(r"(?:[a-z][a-z0-9+.-]*:|#|//)", target, re.I):
            links.append(target.split("#", 1)[0])
    return [x for x in links if x]


def relative_images(text: str) -> list[str]:
    targets = []
    for raw in IMAGE_RE.findall(text):
        target = raw.strip().split(" ", 1)[0].strip("<>")
        if target and not re.match(r"(?:[a-z][a-z0-9+.-]*:|//|data:)", target, re.I):
            targets.append(target.split("#", 1)[0])
    return [x for x in targets if x]


def tokens(text: str) -> dict[str, set[str]]:
    return {name: {m.group(0).strip() for m in pattern.finditer(text)} for name, pattern in TOKEN_PATTERNS.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check aligned README.md and README_EN.md")
    parser.add_argument("chinese", type=Path)
    parser.add_argument("english", type=Path)
    args = parser.parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    if not args.chinese.is_file():
        errors.append(f"missing file: {args.chinese}")
    if not args.english.is_file():
        errors.append(f"missing file: {args.english}")
    if errors:
        print("ERROR")
        print("\n".join(f"- {item}" for item in errors))
        return 1
    zh = args.chinese.read_text(encoding="utf-8")
    en = args.english.read_text(encoding="utf-8")
    zh_head, en_head = headings(zh), headings(en)
    if zh_head != en_head:
        errors.append("heading tree differs (keep identical heading levels and order; translate heading text freely)")
    if fence_count(zh) % 2 or fence_count(en) % 2:
        errors.append("unbalanced Markdown code fence")
    if fence_count(zh) != fence_count(en):
        errors.append(f"code fence count differs: zh={fence_count(zh)}, en={fence_count(en)}")
    for label, path in (("zh", args.chinese), ("en", args.english)):
        for target in relative_links(path.read_text(encoding="utf-8")):
            candidate = (path.parent / target).resolve()
            if not candidate.exists():
                errors.append(f"{label} relative link target missing: {target}")
        for target in relative_images(path.read_text(encoding="utf-8")):
            candidate = (path.parent / target).resolve()
            if not candidate.exists():
                errors.append(f"{label} image target missing: {target}")
    zh_tokens, en_tokens = tokens(zh), tokens(en)
    for name in TOKEN_PATTERNS:
        missing = zh_tokens[name] - en_tokens[name]
        extra = en_tokens[name] - zh_tokens[name]
        if missing or extra:
            warnings.append(f"{name} token drift: missing_in_en={sorted(missing)[:8]}, extra_in_en={sorted(extra)[:8]}")
    print(f"README pair: {args.chinese} <-> {args.english}")
    print(f"headings={len(zh_head)}, code_fences={fence_count(zh)}, relative_links={len(relative_links(zh))}, relative_images={len(relative_images(zh))}")
    for item in warnings:
        print(f"WARN - {item}")
    if errors:
        print("FAIL")
        print("\n".join(f"- {item}" for item in errors))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
