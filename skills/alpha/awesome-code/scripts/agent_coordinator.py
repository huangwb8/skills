#!/usr/bin/env python3
"""Collect awesome-code planning context for autonomous agent selection."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from _config import get_nested, load_skill_config
from subagent_policy import find_missing_required_route_agents, load_required_routes


def _load_yaml_mapping(text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception:
        return {}

    try:
        data = yaml.safe_load(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _frontmatter(markdown: str) -> dict[str, Any]:
    if not markdown.startswith("---"):
        return {}
    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return {}
    return _load_yaml_mapping(parts[1])


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


class AgentCoordinator:
    """Gather deterministic context and constraints for the LLM planner."""

    def __init__(self, agents_root: Path | None = None) -> None:
        self.skill_root = Path(__file__).resolve().parent.parent
        self.agents_root = agents_root or (self.skill_root / "agents")
        self.config = load_skill_config(self.skill_root)
        self.enabled_agents = self._load_enabled_agents()
        self.fail_on_missing_required_agent = bool(
            get_nested(
                self.config,
                "multi_agent",
                "dispatch_policy",
                "fail_on_missing_required_agent",
                default=True,
            )
        )

    def _load_enabled_agents(self) -> set[str] | None:
        configured = get_nested(self.config, "multi_agent", "enabled_agents", default=None)
        if not isinstance(configured, list):
            return None
        enabled = {str(agent).strip() for agent in configured if str(agent).strip()}
        return enabled or None

    def collect_context(self, task_description: str) -> dict[str, Any]:
        available_agents = self.discover_agents()
        required_routes = load_required_routes(self.config)
        missing_required_agents = find_missing_required_route_agents(
            required_routes,
            {agent["role"] for agent in available_agents if agent["enabled"]},
        )
        execution_contract = self._execution_contract()
        dispatch_gate = self._build_dispatch_gate(
            missing_required_agents,
            execution_contract,
        )
        backend_skill = execution_contract.get("backend_skill") or "the configured execution backend"

        return {
            "task": task_description,
            "planning_mode": "autonomous",
            "available_agents": available_agents,
            "agent_count": len(available_agents),
            "config_constraints": {
                "enabled_agents": sorted(self.enabled_agents) if self.enabled_agents else "all",
                "required_routes": required_routes,
                "dispatch_policy": {
                    "fail_on_missing_required_agent": self.fail_on_missing_required_agent,
                },
                "tdd": {
                    "framework": get_nested(self.config, "tdd", "framework", default="auto"),
                    "min_coverage": get_nested(self.config, "tdd", "min_coverage", default=None),
                },
                "code_review": {
                    "security_checks": get_nested(
                        self.config,
                        "code_review",
                        "security_checks",
                        default=None,
                    ),
                    "complexity_threshold": get_nested(
                        self.config,
                        "code_review",
                        "complexity_threshold",
                        default=None,
                    ),
                },
            },
            "dispatch_gate": dispatch_gate,
            "execution_contract": execution_contract,
            "dispatch_guidance": {
                "planner_responsibility": [
                    "read the task and available agent descriptions",
                    "choose single-pass, focused-agent, parallel, or sequential execution",
                    "load only the selected agents' SKILL.md files",
                    f"delegate every focused-agent, sequential, or parallel Agent execution to {backend_skill}",
                    "record dispatch_receipts for every required agent that is actually used",
                ],
                "minimal_change_scope_default": [
                    "files directly required by the requested behavior",
                    "tests that prove the requested behavior",
                ],
                "avoid": [
                    "unrelated formatting",
                    "opportunistic refactors",
                    "new abstractions without repeated complexity",
                ],
                "required_route_rule": (
                    "If the planner decides a configured required_route applies, all agents "
                    "listed for that route are required and missing agents must block execution."
                ),
            },
        }

    def _execution_contract(self) -> dict[str, Any]:
        configured = get_nested(self.config, "dependencies", "agent_execution", default=None)
        issues: list[str] = []
        if not isinstance(configured, dict):
            configured = {}
            issues.append("missing dependencies.agent_execution configuration")

        backend_skill = configured.get("skill")
        if not isinstance(backend_skill, str) or not backend_skill.strip():
            issues.append("dependencies.agent_execution.skill must be a non-empty string")
            backend_skill = None
        else:
            backend_skill = backend_skill.strip()

        required = configured.get("required")
        if required is not True:
            issues.append("dependencies.agent_execution.required must be true")

        modes = configured.get("modes")
        if not isinstance(modes, list) or not modes or not all(
            isinstance(mode, str) and mode.strip() for mode in modes
        ):
            issues.append("dependencies.agent_execution.modes must be a non-empty string list")
            modes = []
        else:
            modes = [mode.strip() for mode in modes]

        responsibility = configured.get("responsibility")
        if not isinstance(responsibility, str) or not responsibility.strip():
            issues.append("dependencies.agent_execution.responsibility must be a non-empty string")
            responsibility = None
        else:
            responsibility = responsibility.strip()

        return {
            "valid": not issues,
            "backend_skill": backend_skill,
            "required_for_multi_agent": required is True,
            "modes": modes,
            "responsibility": responsibility,
            "blocking_reason": "; ".join(issues),
        }

    def analyze_task(self, task_description: str) -> dict[str, Any]:
        """Backward-compatible alias for callers that still use analyze_task."""
        return self.collect_context(task_description)

    def discover_agents(self) -> list[dict[str, Any]]:
        if not self.agents_root.exists():
            print(f"[awesome-code] warning: agents_root does not exist: {self.agents_root}", file=sys.stderr)
            return []

        agents: list[dict[str, Any]] = []
        for skill_file in sorted(self.agents_root.glob("*/SKILL.md")):
            role = skill_file.parent.name
            meta = _frontmatter(skill_file.read_text(encoding="utf-8"))
            metadata = meta.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            enabled = self.enabled_agents is None or role in self.enabled_agents
            agents.append(
                {
                    "role": role,
                    "name": str(meta.get("name") or role),
                    "description": str(meta.get("description") or ""),
                    "short_description": str(metadata.get("short-description") or ""),
                    "keywords": _coerce_string_list(metadata.get("keywords")),
                    "skill_path": str(skill_file),
                    "enabled": enabled,
                }
            )
        return agents

    def _build_dispatch_gate(
        self,
        missing_required_agents: list[str],
        execution_contract: dict[str, Any],
    ) -> dict[str, Any]:
        missing_execution_contract = not bool(execution_contract.get("valid"))
        can_proceed = not (
            (self.fail_on_missing_required_agent and missing_required_agents)
            or missing_execution_contract
        )
        blocking_reasons: list[str] = []
        if missing_required_agents and self.fail_on_missing_required_agent:
            blocking_reasons.append("configured required route agent unavailable")
        if missing_execution_contract:
            blocking_reasons.append(
                execution_contract.get("blocking_reason") or "invalid agent execution contract"
            )
        return {
            "can_proceed": can_proceed,
            "blocking_reason": "; ".join(blocking_reasons),
            "missing_agents": missing_required_agents,
            "runtime_capability_required": bool(missing_required_agents) or missing_execution_contract,
        }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 agent_coordinator.py <task_description>")
        print("\nExample:")
        print('  python3 agent_coordinator.py "I need to fix a bug in the login feature"')
        sys.exit(1)

    task_description = " ".join(sys.argv[1:])
    coordinator = AgentCoordinator()
    print(json.dumps(coordinator.collect_context(task_description), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
