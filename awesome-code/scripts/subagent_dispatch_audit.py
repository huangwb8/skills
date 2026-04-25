#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable


def build_dispatch_manifest(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for dispatch_level in ("required_agents", "preferred_agents", "optional_agents"):
        level = dispatch_level.replace("_agents", "")
        for agent in analysis.get(dispatch_level, []):
            manifest.append(
                {
                    "role": agent["role"],
                    "dispatch_level": level,
                    "reason": agent.get("reason", ""),
                    "policy_source": agent.get("policy_source", ""),
                    "status": "pending",
                    "skill_path": agent.get("skill_path"),
                }
            )
    return manifest


def record_dispatch_receipt(role: str, status: str, evidence: str) -> dict[str, str]:
    return {
        "role": role,
        "status": status,
        "evidence": evidence,
    }


def validate_dispatch_completion(
    manifest: Iterable[dict[str, Any]],
    receipts: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    receipt_by_role = {
        str(receipt.get("role")): receipt
        for receipt in receipts
        if receipt.get("role")
    }
    missing_required_receipts: list[str] = []
    warnings: list[str] = []

    for entry in manifest:
        role = str(entry.get("role", ""))
        dispatch_level = str(entry.get("dispatch_level", ""))
        receipt = receipt_by_role.get(role)
        if dispatch_level == "required":
            if receipt is None or str(receipt.get("status", "")).lower() != "completed":
                missing_required_receipts.append(role)
        elif dispatch_level == "preferred" and receipt is None:
            warnings.append(f"preferred agent missing receipt: {role}")

    return {
        "ok": not missing_required_receipts,
        "missing_required_receipts": missing_required_receipts,
        "warnings": warnings,
    }
