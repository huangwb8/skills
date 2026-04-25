#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
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


def _normalize_keywords(task_keywords: Iterable[str]) -> set[str]:
    return {str(keyword).strip().lower() for keyword in task_keywords if str(keyword).strip()}


def _split_phrase_tokens(keyword: str) -> list[str]:
    normalized = keyword.replace("_", " ").replace("-", " ").strip().lower()
    return [part for part in normalized.split() if part]


def _normalize_registry_roles(registry: Mapping[Any, Any]) -> set[str]:
    roles: set[str] = set()
    for key in registry.keys():
        if isinstance(key, Enum):
            roles.add(key.value)
            continue
        value = getattr(key, "value", None)
        if isinstance(value, str):
            roles.add(value)
            continue
        roles.add(str(key))
    return roles


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
        if not isinstance(agents, list) or not isinstance(keywords, list):
            continue
        normalized[str(route_name)] = {
            "agents": [str(agent) for agent in agents if str(agent).strip()],
            "keywords": [str(keyword).strip().lower() for keyword in keywords if str(keyword).strip()],
        }
    return normalized


def _dedupe_requirements(
    requirements: Iterable[DispatchRequirement],
) -> list[DispatchRequirement]:
    order = {"required": 0, "preferred": 1, "optional": 2}
    merged: dict[str, DispatchRequirement] = {}
    for requirement in requirements:
        existing = merged.get(requirement.role)
        if existing is None or order[requirement.dispatch_level] < order[existing.dispatch_level]:
            merged[requirement.role] = requirement
            continue
        if existing.dispatch_level == requirement.dispatch_level:
            matched = sorted(set(existing.matched_keywords) | set(requirement.matched_keywords))
            merged[requirement.role] = DispatchRequirement(
                role=existing.role,
                dispatch_level=existing.dispatch_level,
                reason=existing.reason,
                policy_source=existing.policy_source,
                matched_keywords=matched,
            )
    return list(merged.values())


def _match_route_keywords(
    normalized_keywords: set[str],
    configured_keywords: Iterable[str],
) -> list[str]:
    matched: set[str] = set()
    for keyword in configured_keywords:
        normalized = keyword.strip().lower()
        if not normalized:
            continue
        if normalized in normalized_keywords:
            matched.add(normalized)
            continue
        phrase_tokens = _split_phrase_tokens(normalized)
        if len(phrase_tokens) > 1 and all(token in normalized_keywords for token in phrase_tokens):
            matched.add(normalized)
    return sorted(matched)


def classify_dispatch_requirements(
    task_keywords: Iterable[str],
    config: Mapping[str, Any],
    registry: Mapping[Any, Any],
) -> dict[str, list[DispatchRequirement]]:
    normalized_keywords = _normalize_keywords(task_keywords)
    required_routes = load_required_routes(config)
    registry_roles = _normalize_registry_roles(registry)

    required: list[DispatchRequirement] = []
    preferred: list[DispatchRequirement] = []
    optional: list[DispatchRequirement] = []

    for route_name, route_config in required_routes.items():
        matched_keywords = _match_route_keywords(normalized_keywords, route_config["keywords"])
        if not matched_keywords:
            continue
        for agent in route_config["agents"]:
            required.append(
                DispatchRequirement(
                    role=agent,
                    dispatch_level="required",
                    reason=f"task matches {route_name} route",
                    policy_source=f"config.required_routes.{route_name}",
                    matched_keywords=matched_keywords,
                )
            )

    frontend_required = {item.role for item in required if item.role == "frontend-specialist"}
    if frontend_required:
        companion_agents = get_nested(
            config,
            "multi_agent",
            "frontend_design_companion_agents",
            default=["brainstorming"],
        )
        if not isinstance(companion_agents, list):
            companion_agents = ["brainstorming"]
        design_direction_keywords = get_nested(
            config,
            "multi_agent",
            "dispatch_policy",
            "design_direction_keywords",
            default=[],
        )
        if not isinstance(design_direction_keywords, list):
            design_direction_keywords = []
        direction_hits = _match_route_keywords(normalized_keywords, design_direction_keywords)
        for agent in (str(name) for name in companion_agents if str(name).strip()):
            if agent not in registry_roles and agent != "brainstorming":
                continue
            dispatch_level = "required" if direction_hits else "preferred"
            target = required if dispatch_level == "required" else preferred
            target.append(
                DispatchRequirement(
                    role=agent,
                    dispatch_level=dispatch_level,
                    reason=(
                        "task asks for explicit design direction before implementation"
                        if direction_hits
                        else "design-first companion for frontend redesign tasks"
                    ),
                    policy_source="config.multi_agent.frontend_design_companion_agents",
                    matched_keywords=direction_hits or ["design-first"],
                )
            )

    return {
        "required": _dedupe_requirements(required),
        "preferred": _dedupe_requirements(preferred),
        "optional": _dedupe_requirements(optional),
    }


def missing_required_agents(
    requirements: Iterable[DispatchRequirement],
    registry: Mapping[Any, Any],
) -> list[str]:
    registry_roles = _normalize_registry_roles(registry)
    missing = sorted(
        requirement.role
        for requirement in requirements
        if requirement.role not in registry_roles
    )
    return list(dict.fromkeys(missing))


def resolve_skill_path(skill_root: Path, agents_root: Path, role: str) -> str | None:
    skill_path = agents_root / role / "SKILL.md"
    if not skill_path.exists():
        return None
    try:
        return str(skill_path.relative_to(skill_root.parent))
    except ValueError:
        return str(skill_path)
