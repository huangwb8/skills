#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from _config import get_nested


@dataclass(frozen=True)
class DispatchRequirement:
    role: str
    dispatch_level: str
    reason: str
    policy_source: str
    matched_keywords: list[str]


def load_required_routes(config: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    routes = get_nested(config, "multi_agent", "dispatch_policy", "required_routes", default={})
    if not isinstance(routes, dict):
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    for route_name, route_config in routes.items():
        if not isinstance(route_config, dict):
            continue
        agents = route_config.get("agents", [])
        keywords = route_config.get("keywords", [])
        if not isinstance(agents, list):
            continue
        normalized[str(route_name)] = {
            "agents": [str(agent) for agent in agents if str(agent).strip()],
            "keywords": [
                str(keyword).strip().lower()
                for keyword in keywords
                if str(keyword).strip()
            ]
            if isinstance(keywords, list)
            else [],
        }
    return normalized


def find_missing_required_route_agents(
    required_routes: Mapping[str, Mapping[str, Any]],
    available_roles: Iterable[str],
) -> list[str]:
    available = {str(role) for role in available_roles}
    missing: list[str] = []
    for route in required_routes.values():
        agents = route.get("agents", [])
        if not isinstance(agents, list):
            continue
        for role in agents:
            role_name = str(role)
            if role_name and role_name not in available:
                missing.append(role_name)
    return sorted(dict.fromkeys(missing))


def missing_required_agents(
    requirements: Iterable[DispatchRequirement],
    registry: Mapping[Any, Any] | Iterable[str],
) -> list[str]:
    registry_roles = _normalize_registry_roles(registry)
    missing = [
        requirement.role
        for requirement in requirements
        if requirement.role not in registry_roles
    ]
    return sorted(dict.fromkeys(missing))


def resolve_skill_path(skill_root: Path, agents_root: Path, role: str) -> str | None:
    skill_path = agents_root / role / "SKILL.md"
    if not skill_path.exists():
        return None
    try:
        return str(skill_path.relative_to(skill_root.parent))
    except ValueError:
        return str(skill_path)


def _normalize_registry_roles(registry: Mapping[Any, Any] | Iterable[str]) -> set[str]:
    if isinstance(registry, Mapping):
        values = registry.keys()
    else:
        values = registry

    roles: set[str] = set()
    for key in values:
        value = getattr(key, "value", None)
        roles.add(value if isinstance(value, str) else str(key))
    return roles
