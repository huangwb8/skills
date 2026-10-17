from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/alpha/awesome-code/scripts"))

from agent_coordinator import AgentCoordinator  # noqa: E402


def test_init_template_uses_parallel_vibe_as_multi_agent_backend() -> None:
    template = (ROOT / "skills/alpha/init-project/templates/AGENTS.md.template").read_text(
        encoding="utf-8"
    )

    assert "parallel-vibe" in template
    assert "特别推荐使用 `awesome-code`" not in template
    assert "串行或并行" in template


def test_awesome_code_declares_required_execution_backend() -> None:
    config = yaml.safe_load((ROOT / "skills/alpha/awesome-code/config.yaml").read_text(encoding="utf-8"))
    backend = config["dependencies"]["agent_execution"]

    assert backend["skill"] == "parallel-vibe"
    assert backend["required"] is True
    assert set(backend["modes"]) == {"focused-agent", "sequential", "parallel"}

    skill = (ROOT / "skills/alpha/awesome-code/SKILL.md").read_text(encoding="utf-8")
    assert "不得直接创建或调度 Agent" in skill
    assert "parallel-vibe" in skill


def test_agent_coordinator_exposes_execution_backend_contract() -> None:
    script = ROOT / "skills/alpha/awesome-code/scripts/agent_coordinator.py"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, str(script), "coordinate a multi-agent refactor"],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    context = json.loads(result.stdout)

    contract = context["execution_contract"]
    assert contract["backend_skill"] == "parallel-vibe"
    assert contract["required_for_multi_agent"] is True
    assert set(contract["modes"]) == {"focused-agent", "sequential", "parallel"}
    assert contract["valid"] is True


def test_agent_coordinator_does_not_fallback_to_a_hardcoded_backend() -> None:
    coordinator = AgentCoordinator()
    coordinator.config = {}

    contract = coordinator._execution_contract()

    assert contract["valid"] is False
    assert contract["backend_skill"] is None
    assert contract["modes"] == []
    assert "missing dependencies.agent_execution configuration" in contract["blocking_reason"]


def test_invalid_execution_contract_blocks_dispatch() -> None:
    coordinator = AgentCoordinator()
    coordinator.config = {}
    contract = coordinator._execution_contract()

    gate = coordinator._build_dispatch_gate([], contract)

    assert gate["can_proceed"] is False
    assert gate["runtime_capability_required"] is True
