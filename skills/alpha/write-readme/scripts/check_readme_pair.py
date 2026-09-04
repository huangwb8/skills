#!/usr/bin/env python3
"""Deterministic checks for the bilingual README contract.

The checker deliberately avoids judging prose quality. It reports structural
and reference drift so an AI or human can perform the semantic review.
"""
from __future__ import annotations

import argparse
import re
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


def check_pair(chinese: Path, english: Path) -> dict[str, object]:
    """Return the deterministic README-pair result used by the CLI and Pack.

    The function intentionally reports token drift as a warning.  It is a
    useful signal for semantic review, but does not claim that translated
    prose is equivalent.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if not chinese.is_file():
        errors.append("missing chinese README")
    if not english.is_file():
        errors.append("missing english README")
    if errors:
        return {"errors": errors, "warnings": warnings, "facts": {"heading_count": 0, "code_fences": 0}}

    zh = chinese.read_text(encoding="utf-8")
    en = english.read_text(encoding="utf-8")
    zh_head, en_head = headings(zh), headings(en)
    if zh_head != en_head:
        errors.append("heading tree differs (keep identical heading levels and order; translate heading text freely)")
    zh_fences, en_fences = fence_count(zh), fence_count(en)
    if zh_fences % 2 or en_fences % 2:
        errors.append("unbalanced Markdown code fence")
    if zh_fences != en_fences:
        errors.append(f"code fence count differs: zh={zh_fences}, en={en_fences}")
    for label, text in (("zh", zh), ("en", en)):
        path = chinese if label == "zh" else english
        for target in relative_links(text):
            if not (path.parent / target).resolve().exists():
                errors.append(f"{label} relative link target missing: {target}")
        for target in relative_images(text):
            if not (path.parent / target).resolve().exists():
                errors.append(f"{label} image target missing: {target}")
    zh_tokens, en_tokens = tokens(zh), tokens(en)
    token_drift: dict[str, dict[str, list[str]]] = {}
    for name in TOKEN_PATTERNS:
        missing = sorted(zh_tokens[name] - en_tokens[name])
        extra = sorted(en_tokens[name] - zh_tokens[name])
        if missing or extra:
            warning = f"{name} token drift: missing_in_en={missing[:8]}, extra_in_en={extra[:8]}"
            warnings.append(warning)
            token_drift[name] = {"missing_in_en": missing, "extra_in_en": extra}
    return {
        "errors": errors,
        "warnings": warnings,
        "facts": {
            "heading_count": len(zh_head),
            "code_fences": zh_fences,
            "relative_links": len(relative_links(zh)),
            "relative_images": len(relative_images(zh)),
            "token_drift": token_drift,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check aligned README.md and README_EN.md")
    parser.add_argument("chinese", type=Path)
    parser.add_argument("english", type=Path)
    args = parser.parse_args(argv)
    result = check_pair(args.chinese, args.english)
    errors = list(result["errors"])
    warnings = list(result["warnings"])
    if errors and not args.chinese.is_file() and not args.english.is_file():
        print("ERROR")
        print(f"- missing file: {args.chinese}")
        print(f"- missing file: {args.english}")
        return 1
    if errors:
        # Preserve the historical detailed CLI wording for existing callers.
        if not args.chinese.is_file():
            errors[0] = f"missing file: {args.chinese}"
        if not args.english.is_file():
            errors[-1] = f"missing file: {args.english}"
        print("ERROR")
        print("\n".join(f"- {item}" for item in errors))
        return 1
    print(f"README pair: {args.chinese} <-> {args.english}")
    facts = result["facts"]
    print(f"headings={facts['heading_count']}, code_fences={facts['code_fences']}, relative_links={facts['relative_links']}, relative_images={facts['relative_images']}")
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
