"""Versioned, domain-neutral identities for State visits and attempts."""

from __future__ import annotations

from typing import Any, Mapping


STATE_IDENTITY_PROTOCOL = "bensz-state-identity-v2"
KERNEL_CAPABILITIES_PROTOCOL = "bensz-kernel-capabilities-v1"

_CAPABILITIES = (
    "state_visit_identity",
    "atomic_target_identity_handoff",
    "attempt_supersede",
    "state_bound_verifier_gate",
    "state_bound_action_authorization",
    "legacy_event_read",
)


def normalize_state_identity(value: Mapping[str, Any], *, label: str = "state identity") -> dict[str, str]:
    """Return a validated three-part State identity.

    ``run_id`` spans the business run, ``state_visit_id`` identifies one entry
    into a State, and ``attempt_id`` identifies one evidence attempt inside
    that visit.  All three are opaque, non-empty caller identifiers.
    """
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    identity: dict[str, str] = {}
    for key in ("run_id", "state_visit_id", "attempt_id"):
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{label}.{key} must be a non-empty string")
        identity[key] = item
    return identity


def kernel_capabilities(*, version: str | None = None) -> dict[str, Any]:
    """Describe stable protocol capabilities without probing user data."""
    if version is None:
        from . import __version__

        version = __version__
    result: dict[str, Any] = {
        "protocol": KERNEL_CAPABILITIES_PROTOCOL,
        "state_identity_protocol": STATE_IDENTITY_PROTOCOL,
        "event_protocols": ["bensz-event-v1", "bensz-event-v2"],
        "capabilities": list(_CAPABILITIES),
    }
    result["kernel_version"] = version
    return result
