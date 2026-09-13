"""Versioned, domain-neutral identities for State visits and attempts."""

from __future__ import annotations

import platform
import sys
from typing import Any, Mapping


STATE_IDENTITY_PROTOCOL = "bensz-state-identity-v2"
KERNEL_CAPABILITIES_PROTOCOL = "bensz-kernel-capabilities-v1"
KERNEL_DIAGNOSTICS_PROTOCOL = "bensz-kernel-diagnostics-v1"
STRICT_IDENTITY_POLICY = "state-identity-v2"

_CAPABILITIES = (
    "state_visit_identity",
    "atomic_target_identity_handoff",
    "attempt_supersede",
    "state_bound_verifier_gate",
    "state_bound_action_authorization",
    "legacy_event_read",
    "strict_identity_policy",
    "runtime_snapshot_binding",
    "environment_diagnostics",
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
        "identity_modes": {
            "legacy": {
                "required_fields": [],
                "downgrade_policy": "warn",
                "write_policy": "compatibility-only",
            },
            "v2": {
                "required_fields": ["run_id", "target_attempt_id"],
                "downgrade_policy": "forbid-after-v2",
                "write_policy": "explicit",
            },
            "strict-v2": {
                "runtime_policy": STRICT_IDENTITY_POLICY,
                "required_fields": ["run_id", "target_attempt_id"],
                "downgrade_policy": "forbid",
                "write_policy": "required",
            },
        },
    }
    result["kernel_version"] = version
    return result


def kernel_diagnostics(*, version: str | None = None) -> dict[str, Any]:
    """Report the actual interpreter and protocol implementation in use."""
    capabilities = kernel_capabilities(version=version)
    return {
        "protocol": KERNEL_DIAGNOSTICS_PROTOCOL,
        "kernel_version": capabilities["kernel_version"],
        "capabilities_protocol": capabilities["protocol"],
        "state_identity_protocol": STATE_IDENTITY_PROTOCOL,
        "python": {
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "version_info": list(sys.version_info[:3]),
        },
    }
