"""Canonical verifier identifier validation and compatibility helpers."""

from __future__ import annotations

import re


_TOKEN = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
_CANONICAL_ID = re.compile(
    rf"^(?P<owner>{_TOKEN}(?:\.{_TOKEN})*)\.(?P<domain>{_TOKEN})\.(?P<capability>{_TOKEN})$"
)


def validate_verifier_id(value: str) -> str:
    """Validate and return a canonical ``owner.domain.capability`` ID."""
    if (
        not isinstance(value, str)
        or not _CANONICAL_ID.fullmatch(value)
        or re.fullmatch(r"v\d+", value.rsplit(".", 1)[-1])
    ):
        raise ValueError(
            "canonical verifier ID must match owner.domain.capability using lowercase kebab-case"
        )
    return value


def parse_aliases(value: str | None) -> tuple[str, ...]:
    """Parse comma-separated legacy aliases without imposing canonical syntax."""
    if not value:
        return ()
    aliases = tuple(item.strip() for item in value.split(",") if item.strip())
    if len(set(aliases)) != len(aliases):
        raise ValueError("verifier aliases must be unique")
    return aliases
