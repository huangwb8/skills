#!/usr/bin/env python3
"""Conservative lexical protection checks, not a semantic or full TeX parser."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


class UnsupportedInput(ValueError):
    """Input needs a human or a full document parser."""


COMPLEX_TEX = re.compile(
    r"\\(?:verb\*?|catcode|def|gdef|edef|newcommand|renewcommand)\b"
    r"|\\begin\{(?:verbatim\*?|lstlisting|minted)\}"
)
PLAIN_MARKUP = re.compile(
    r"\\|[$`%]|(?m:^[ \t]*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|>|```|~~~|\|))"
    r"|(?m:^(?: {4}|\t)\S|^[ \t]*(?:=+|-+)[ \t]*$)"
)
ATOM = re.compile(
    r"[A-Za-z][A-Za-z0-9_]*(?:[-+/.@:/][A-Za-z0-9_]+)*"
    r"|[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
    r"(?:[ \t]*(?:%|‰|℃|°C|μg|µg|mg|kg|mm|cm|km|ms|mL|ml|Hz|天|周|个月|月|年|例|人))?"
    r"|[{}_^&#~]"
)
MARKER = re.compile(r"[ \t]*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*|\|)")


def balanced_end(text: str, start: int) -> int:
    opening = text[start]
    closing = {"{": "}", "[": "]"}[opening]
    depth, index = 1, start + 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "%":
            newline = text.find("\n", index)
            index = len(text) if newline < 0 else newline + 1
            continue
        # Optional arguments may contain braces enclosing a closing bracket.
        if opening == "[" and char == "{":
            index = balanced_end(text, index)
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    raise UnsupportedInput("unbalanced_argument")


def delimited_end(text: str, start: int, opening: str, closing: str) -> int:
    index = start + len(opening)
    while index < len(text):
        if text.startswith(closing, index):
            return index + len(closing)
        if text[index] == "\\":
            index += 2
        else:
            index += 1
    raise UnsupportedInput("unclosed_delimiter")


def protected_tokens(text: str) -> list[tuple[str, str]]:
    if COMPLEX_TEX.search(text):
        raise UnsupportedInput("complex_tex_requires_review")
    tokens: list[tuple[str, str]] = []
    index = 0
    while index < len(text):
        start = index
        char = text[index]
        if char == "%":
            end = text.find("\n", index)
            index = len(text) if end < 0 else end
            tokens.append(("comment", text[start:index]))
        elif char == "`":
            match = re.match(r"`+", text[index:])
            assert match
            delimiter = match.group()
            index = delimited_end(text, index, delimiter, delimiter)
            tokens.append(("code", text[start:index]))
        elif char == "$" or text.startswith((r"\(", r"\["), index):
            opening = "$$" if text.startswith("$$", index) else char
            closing = opening
            if char == "\\":
                opening = text[index:index + 2]
                closing = r"\)" if opening == r"\(" else r"\]"
            index = delimited_end(text, index, opening, closing)
            tokens.append(("math", text[start:index]))
        elif char == "\\":
            match = re.match(r"\\(?:[A-Za-z]+\*?|[^\r\n])", text[index:])
            if not match:
                raise UnsupportedInput("incomplete_command")
            index += len(match.group())
            while index < len(text):
                probe = index
                while probe < len(text) and text[probe] in " \t\r\n":
                    probe += 1
                if probe < len(text) and text[probe] in "[{":
                    index = balanced_end(text, probe)
                else:
                    break
            tokens.append(("latex", text[start:index]))
        elif text.startswith("~~~", index):
            raise UnsupportedInput("tilde_fence_requires_review")
        elif match := ATOM.match(text, index):
            index = match.end()
            tokens.append(("atom", match.group()))
        else:
            index += 1
    return tokens


def structure_signature(text: str) -> list[tuple[str, str, str, str, bool]]:
    result = []
    for line in text.splitlines(keepends=True):
        ending = "\r\n" if line.endswith("\r\n") else line[-1:] if line.endswith(("\n", "\r")) else ""
        body = line[:-len(ending)] if ending else line
        indent = re.match(r"[ \t]*", body).group()
        trailing = re.search(r"[ \t]*$", body).group()
        marker = MARKER.match(body)
        result.append((ending, indent, trailing, marker.group() if marker else "", not body.strip()))
    return result


def compare(original: str, revised: str, structure_mode: str = "preserve") -> dict:
    if structure_mode not in {"preserve", "reflow_plain"}:
        raise UnsupportedInput("invalid_structure_mode")
    if structure_mode == "reflow_plain" and any(PLAIN_MARKUP.search(t) for t in (original, revised)):
        raise UnsupportedInput("reflow_requires_plain_text_use_preserve")
    before, after = protected_tokens(original), protected_tokens(revised)
    differences = []
    if before != after:
        differences.append("protected_sequence_changed")
    if structure_mode == "preserve" and structure_signature(original) != structure_signature(revised):
        differences.append("line_structure_changed")
    return {
        "status": "pass" if not differences else "fail",
        "differences": differences,
        "protected_counts": {"original": len(before), "revised": len(after)},
        "semantic_review": "required",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("revised", type=Path)
    parser.add_argument("--structure-mode", choices=("preserve", "reflow_plain"), default="preserve")
    args = parser.parse_args()
    try:
        # Bytes preserve CRLF; errors never echo potentially sensitive source text.
        result = compare(args.original.read_bytes().decode("utf-8"), args.revised.read_bytes().decode("utf-8"), args.structure_mode)
    except (OSError, UnicodeError, UnsupportedInput) as error:
        reason = str(error) if isinstance(error, UnsupportedInput) else type(error).__name__
        print(json.dumps({"status": "unchecked", "reason": reason, "semantic_review": "required"}))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
