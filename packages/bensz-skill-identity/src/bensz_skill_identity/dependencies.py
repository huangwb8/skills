"""Exact dependency closure; lock files are data, never reusable verification receipts."""

from __future__ import annotations

import copy
from pathlib import Path

from .protocol import SCHEMA, IdentityError, digest, fields, require
from .release import (
    TrustPolicy,
    inspect_release,
    requirement,
    validate_state,
    verify_release,
)


def resolve_lock(
    requirements: list[dict],
    candidates: list[Path],
    policy: TrustPolicy,
    *,
    state: dict,
    now=None,
) -> dict:
    require(type(requirements) is list and len(requirements) <= 256)
    validate_state(state)
    index = {}
    for candidate in candidates:
        manifest, _, _ = inspect_release(candidate, now=now)
        key = (manifest["skill_id"], manifest["version"], digest(manifest))
        # Identical mirrored releases are equivalent; no name-based selection occurs.
        index.setdefault(key, candidate)
    resolved, visiting = {}, set()
    pending_state = copy.deepcopy(state)

    def visit(wanted):
        requirement(wanted)
        sid = wanted["skill_id"]
        require(sid not in visiting, "dependency_cycle")
        if sid in resolved:
            require(resolved[sid] == wanted, "dependency_conflict")
            return
        key = (sid, wanted["version"], wanted["manifest_digest"])
        require(key in index, "dependency_missing")
        candidate = index[key]
        result = verify_release(
            candidate, policy, state=pending_state, request=wanted, now=now
        )
        require(result.decision == "allow", result.reason)
        visiting.add(sid)
        manifest, _, _ = inspect_release(candidate, now=now)
        for dep in manifest["dependencies"]:
            visit(dep)
        visiting.remove(sid)
        resolved[sid] = dict(wanted)

    try:
        for wanted in requirements:
            visit(wanted)
    finally:
        # Security observations survive a failed dependency business transaction.
        state["revisions"] = copy.deepcopy(pending_state["revisions"])
    lock = {
        "schema": SCHEMA + "/lock",
        "requirements": sorted(requirements, key=lambda d: d["skill_id"]),
        "releases": sorted(resolved.values(), key=lambda d: d["skill_id"]),
        "policy_digest": digest(policy.to_dict()),
    }
    state.clear()
    state.update(pending_state)
    return lock


def verify_lock(
    lock: dict, candidates: list[Path], policy: TrustPolicy, *, state: dict, now=None
) -> dict:
    fields(lock, {"schema", "requirements", "releases", "policy_digest"})
    require(lock["schema"] == SCHEMA + "/lock", "unsupported_protocol")
    require(lock["policy_digest"] == digest(policy.to_dict()), "policy_mismatch")
    fresh = resolve_lock(lock["requirements"], candidates, policy, state=state, now=now)
    require(fresh == lock, "lock_mismatch")
    return fresh


def resolve_name(name: str, verified: list) -> dict:
    """Caller supplies its explicit trusted display-name mapping as (name,result)."""
    matches = {
        digest(r.as_requirement()): r.as_requirement()
        for label, r in verified
        if label == name and r.decision == "allow"
    }
    if not matches:
        raise IdentityError("dependency_missing")
    require(len(matches) == 1, "dependency_ambiguous")
    return next(iter(matches.values()))
