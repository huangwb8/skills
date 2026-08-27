"""Canonical state identifier validation and compatibility helpers."""

from __future__ import annotations

import re


_TOKEN = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
_CANONICAL_ID = re.compile(
    rf"^(?P<owner>{_TOKEN}(?:\.{_TOKEN})*)\.(?P<machine>{_TOKEN})\.(?P<state>{_TOKEN})$"
)


def validate_state_id(value: str) -> str:
    """Validate and return a canonical ``owner.machine.state`` ID."""
    if (
        not isinstance(value, str)
        or not _CANONICAL_ID.fullmatch(value)
        or re.fullmatch(r"v\d+", value.rsplit(".", 1)[-1])
    ):
        raise ValueError(
            "canonical state ID must match owner.machine.state using lowercase kebab-case"
        )
    return value


def parse_state_aliases(value: object) -> tuple[str, ...]:
    """Parse legacy state aliases accepted by the compatibility resolver."""
    if value is None:
        return ()
    if isinstance(value, str):
        aliases = tuple(item.strip() for item in value.split(",") if item.strip())
    elif isinstance(value, (list, tuple)):
        aliases = tuple(str(item).strip() for item in value if str(item).strip())
    else:
        raise ValueError("state aliases must be a string or list")
    if len(set(aliases)) != len(aliases):
        raise ValueError("state aliases must be unique")
    return aliases
