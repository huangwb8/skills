#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any


def _strip_comment(text: str) -> str:
    if "#" not in text:
        return text.rstrip()
    in_quote = False
    quote_char = ""
    out: list[str] = []
    for ch in text:
        if ch in {'"', "'"}:
            if in_quote and ch == quote_char:
                in_quote = False
                quote_char = ""
            elif not in_quote:
                in_quote = True
                quote_char = ch
        if ch == "#" and not in_quote:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _parse_scalar(value: str) -> Any:
    value = _strip_comment(value).strip()
    if value == "":
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.isdigit():
        return int(value)
    return value


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _next_meaningful(lines: list[str], index: int) -> int:
    while index < len(lines):
        stripped = _strip_comment(lines[index]).strip()
        if stripped:
            return index
        index += 1
    return index


def _parse_block(lines: list[str], index: int, indent: int) -> tuple[Any, int]:
    index = _next_meaningful(lines, index)
    if index >= len(lines):
        return {}, index

    stripped = _strip_comment(lines[index]).strip()
    if stripped.startswith("- "):
        result: list[Any] = []
        while index < len(lines):
            index = _next_meaningful(lines, index)
            if index >= len(lines):
                break
            line = lines[index]
            current_indent = _indent_of(line)
            stripped = _strip_comment(line).strip()
            if current_indent < indent or not stripped.startswith("- "):
                break
            item_text = stripped[2:].strip()
            if item_text:
                result.append(_parse_scalar(item_text))
                index += 1
                continue
            child, index = _parse_block(lines, index + 1, current_indent + 2)
            result.append(child)
        return result, index

    result_dict: dict[str, Any] = {}
    while index < len(lines):
        index = _next_meaningful(lines, index)
        if index >= len(lines):
            break
        line = lines[index]
        current_indent = _indent_of(line)
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"Unexpected indentation at line {index + 1}: {line!r}")
        stripped = _strip_comment(line).strip()
        if stripped.startswith("- "):
            raise ValueError(f"Unexpected list item at line {index + 1}: {line!r}")
        key, sep, rest = stripped.partition(":")
        if not sep:
            raise ValueError(f"Invalid line {index + 1}: {line!r}")
        key = key.strip()
        rest = rest.strip()
        if rest:
            result_dict[key] = _parse_scalar(rest)
            index += 1
            continue
        next_index = _next_meaningful(lines, index + 1)
        if next_index >= len(lines) or _indent_of(lines[next_index]) <= current_indent:
            result_dict[key] = {}
            index = next_index
            continue
        child, index = _parse_block(lines, next_index, _indent_of(lines[next_index]))
        result_dict[key] = child
    return result_dict, index


def load_config(skill_root: Path) -> dict[str, Any]:
    config_path = skill_root / "config.yaml"
    text = config_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except Exception:
        yaml = None  # type: ignore
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    parsed, _ = _parse_block(text.splitlines(), 0, 0)
    if not isinstance(parsed, dict):
        raise ValueError("config.yaml must parse to a mapping")
    return parsed


def get_skill_root(script_path: Path) -> Path:
    return script_path.resolve().parent.parent
