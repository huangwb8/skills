#!/usr/bin/env python3
"""
Awesome Code Agent Coordinator

This script coordinates multiple specialized agents to handle complex development tasks.
It implements the orchestrator pattern for multi-agent coordination.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from _config import get_nested, load_skill_config

ASCII_MIN_TOKEN_LEN = 3
NON_ASCII_MIN_TOKEN_LEN = 2

STOPWORDS = {
    # English
    "the", "and", "with", "need", "please", "help", "want", "when", "what", "this", "that",
    "for", "from", "into", "over", "then", "than", "have", "has", "will", "would", "should",
    "a", "an", "to", "of", "in", "on", "at", "is", "are", "be", "as", "it", "i", "we", "you",
    # Chinese (keep minimal; avoid filtering meaningful 2-char words like "安全")
    "需要", "请", "帮我", "进行", "实现", "修复", "优化",
}

AMBIGUOUS_AUTH_KEYWORDS = {"login", "登录"}
FRONTEND_DESIGN_SIGNAL_KEYWORDS = {
    "frontend", "ui", "前端", "界面", "dashboard", "landing", "visual", "aesthetic",
    "layout", "motion", "animation", "typography", "design", "设计", "视觉", "审美",
    "布局", "排版", "动效", "动画", "仪表盘", "落地页",
}


class AgentRole(Enum):
    """Agent roles and their specializations"""

    TDD_WORKFLOW = "tdd-workflow"
    SYSTEMATIC_DEBUGGING = "systematic-debugging"
    CODE_REVIEWER = "code-reviewer"
    GIT_WORKFLOW = "git-workflow"
    FRONTEND_SPECIALIST = "frontend-specialist"
    BACKEND_SPECIALIST = "backend-specialist"
    DEVOPS_SPECIALIST = "devops-specialist"
    SECURITY_SPECIALIST = "security-specialist"
    DOCUMENTATION_SPECIALIST = "documentation-specialist"
    MIRROR_OPTIMIZER = "mirror-optimizer"
    WRITING_PLANS = "writing-plans"
    MULTI_AGENT_COORDINATOR = "multi-agent-coordinator"
    CONTEXT_OPTIMIZER = "context-optimizer"
    BRAINSTORMING = "brainstorming"


@dataclass
class AgentCapability:
    """Agent capability description"""

    role: AgentRole
    name: str
    description: str
    keywords: List[str]
    priority: int = 0  # Higher priority = preferred for conflicts


# Agent registry
AGENT_REGISTRY: Dict[AgentRole, AgentCapability] = {
    AgentRole.TDD_WORKFLOW: AgentCapability(
        role=AgentRole.TDD_WORKFLOW,
        name="TDD Workflow",
        description="Test-driven development workflow expert",
        keywords=["tdd", "test", "tests", "testing", "unit test", "test coverage", "测试", "单测", "覆盖率", "回归"],
        priority=8
    ),
    AgentRole.SYSTEMATIC_DEBUGGING: AgentCapability(
        role=AgentRole.SYSTEMATIC_DEBUGGING,
        name="Systematic Debugging",
        description="Systematic debugging and root cause analysis",
        keywords=["debug", "bug", "error", "issue", "fix", "调试", "排查", "定位", "根因", "错误", "登录"],
        priority=9
    ),
    AgentRole.CODE_REVIEWER: AgentCapability(
        role=AgentRole.CODE_REVIEWER,
        name="Code Reviewer",
        description="Code review and quality assurance",
        keywords=["review", "code quality", "refactor", "optimize", "代码审查", "代码质量", "重构", "规范"],
        priority=7
    ),
    AgentRole.GIT_WORKFLOW: AgentCapability(
        role=AgentRole.GIT_WORKFLOW,
        name="Git Workflow",
        description="Git workflow and version control",
        keywords=["git", "commit", "branch", "pr", "merge", "提交", "分支", "合并", "回滚"],
        priority=6
    ),
    AgentRole.FRONTEND_SPECIALIST: AgentCapability(
        role=AgentRole.FRONTEND_SPECIALIST,
        name="Frontend Specialist",
        description="Frontend development expert",
        keywords=[
            "frontend", "react", "vue", "ui", "css", "html", "dashboard", "landing",
            "layout", "responsive", "animation", "motion", "theme", "typography",
            "visual", "aesthetic", "design-system", "prototype", "wireframe",
            "前端", "界面", "组件", "视觉", "审美", "布局", "排版", "动效", "动画",
            "响应式", "仪表盘", "落地页", "设计系统",
        ],
        priority=7
    ),
    AgentRole.BACKEND_SPECIALIST: AgentCapability(
        role=AgentRole.BACKEND_SPECIALIST,
        name="Backend Specialist",
        description="Backend development and API design",
        keywords=["backend", "api", "server", "database", "service", "后端", "接口", "数据库", "服务", "登录", "认证"],
        priority=7
    ),
    AgentRole.DEVOPS_SPECIALIST: AgentCapability(
        role=AgentRole.DEVOPS_SPECIALIST,
        name="DevOps Specialist",
        description="DevOps, CI/CD, and infrastructure",
        keywords=["devops", "deploy", "ci/cd", "docker", "kubernetes", "部署", "ci", "cd", "容器", "流水线"],
        priority=5
    ),
    AgentRole.SECURITY_SPECIALIST: AgentCapability(
        role=AgentRole.SECURITY_SPECIALIST,
        name="Security Specialist",
        description="Application security and compliance",
        keywords=["security", "vulnerability", "auth", "encryption", "安全", "漏洞", "鉴权", "权限", "加密", "注入", "xss", "csrf", "sql"],
        priority=10  # High priority for security
    ),
    AgentRole.DOCUMENTATION_SPECIALIST: AgentCapability(
        role=AgentRole.DOCUMENTATION_SPECIALIST,
        name="Documentation Specialist",
        description="Technical documentation and API docs",
        keywords=["docs", "documentation", "readme", "api docs", "文档", "接口文档"],
        priority=4
    ),
    AgentRole.MIRROR_OPTIMIZER: AgentCapability(
        role=AgentRole.MIRROR_OPTIMIZER,
        name="Mirror Optimizer",
        description="Configure China mirror sources for faster dependency downloads",
        keywords=["mirror", "registry", "镜像", "镜像源", "加速部署", "依赖下载", "国内镜像"],
        priority=7
    ),
    AgentRole.WRITING_PLANS: AgentCapability(
        role=AgentRole.WRITING_PLANS,
        name="Writing Plans",
        description="Write detailed implementation plans before coding",
        keywords=["plan", "planning", "spec", "requirements", "方案", "计划", "需求", "拆解", "任务分解"],
        priority=6
    ),
    AgentRole.MULTI_AGENT_COORDINATOR: AgentCapability(
        role=AgentRole.MULTI_AGENT_COORDINATOR,
        name="Multi-Agent Coordinator",
        description="Coordinates multiple specialized agents",
        keywords=["coordinate", "orchestrate", "parallel", "协调", "编排", "并行"],
        priority=3
    ),
    AgentRole.CONTEXT_OPTIMIZER: AgentCapability(
        role=AgentRole.CONTEXT_OPTIMIZER,
        name="Context Optimizer",
        description="Context management and optimization",
        keywords=["context", "optimize", "efficiency", "token", "上下文", "压缩", "缓存"],
        priority=2
    ),
    AgentRole.BRAINSTORMING: AgentCapability(
        role=AgentRole.BRAINSTORMING,
        name="Brainstorming",
        description="Interactive design optimization through Socratic questioning",
        keywords=["design", "brainstorm", "requirements", "explore", "plan", "需求", "方案", "设计", "头脑风暴"],
        priority=8
    ),
}


@dataclass
class Task:
    """A task to be executed by agents"""

    description: str
    keywords: List[str] = field(default_factory=list)
    priority: int = 5
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentAssignment:
    """Assignment of a task to an agent"""

    agent_role: AgentRole
    task: Task
    confidence: float  # 0-1 score of how well the agent matches
    matched_keywords: List[str] = field(default_factory=list)


class AgentMatcher:
    """Matches tasks to appropriate agents"""

    def __init__(self, registry: Dict[AgentRole, AgentCapability] = None):
        self.registry = registry or AGENT_REGISTRY

    def match_agents(self, task: Task) -> List[AgentAssignment]:
        """
        Match a task to appropriate agents based on keywords and description

        Args:
            task: The task to match

        Returns:
            List of agent assignments sorted by confidence score
        """
        assignments = []

        # Extract keywords from task
        normalized = [str(k).lower() for k in (task.keywords or [])]
        task_keywords = set(normalized + self._extract_keywords(task.description))
        ctx_keywords = task.context.get("keywords", [])
        if isinstance(ctx_keywords, list):
            task_keywords.update([str(x).lower() for x in ctx_keywords])

        # Score each agent
        for role, capability in self.registry.items():
            confidence, matches = self._calculate_confidence(task_keywords, capability)

            # Only include agents with reasonable confidence
            if confidence >= 0.15:
                assignments.append(AgentAssignment(
                    agent_role=role,
                    task=task,
                    confidence=confidence,
                    matched_keywords=sorted(matches),
                ))

        # Stable ordering for ties: confidence desc -> priority desc -> role asc.
        assignments.sort(
            key=lambda a: (-a.confidence, -self.registry[a.agent_role].priority, a.agent_role.value)
        )

        return assignments

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Lightweight tokenizer (keeps hyphenated tokens). For Chinese, many meaningful words are 2 chars,
        # so we apply different length thresholds for ASCII vs non-ASCII tokens.
        base_tokens = re.findall(r"[\w]+(?:-[\w]+)*", text.lower())
        tokens: List[str] = []
        for t in base_tokens:
            tokens.append(t)
            # Heuristic for CJK: if the token is a long Chinese sentence without spaces,
            # add 2-char sliding windows to enable matching short keywords like "调试"/"安全"/"测试".
            if (not t.isascii()) and len(t) >= 4:
                for i in range(len(t) - 1):
                    tokens.append(t[i : i + 2])
                    if len(tokens) >= 120:
                        break
            if len(tokens) >= 120:
                break
        filtered: List[str] = []
        seen: set[str] = set()
        for t in tokens:
            min_len = ASCII_MIN_TOKEN_LEN if t.isascii() else NON_ASCII_MIN_TOKEN_LEN
            if len(t) < min_len:
                continue
            if t in STOPWORDS:
                continue
            if t in seen:
                continue
            seen.add(t)
            filtered.append(t)
            if len(filtered) >= 40:
                break
        return filtered

    def _calculate_confidence(
        self,
        task_keywords: set,
        capability: AgentCapability
    ) -> tuple[float, set]:
        """Calculate confidence score for agent capability"""
        agent_keywords = set(k.lower() for k in capability.keywords)

        # Direct keyword matches
        matches = task_keywords & agent_keywords

        # Base score: normalized by agent keyword set (avoids penalizing long task descriptions).
        if matches and agent_keywords:
            base_score = len(matches) / len(agent_keywords)
        else:
            base_score = 0.0

        # Apply agent priority modifier
        priority_modifier = capability.priority / 10.0

        # Final confidence is weighted combination
        # If there is no keyword match, priority should not dominate the decision.
        priority_weight = 0.3 if matches else 0.05
        confidence = (base_score * 0.7) + (priority_modifier * priority_weight)

        return round(confidence, 3), matches


class AgentCoordinator:
    """
    Coordinates multiple agents for complex tasks

    Implements the orchestrator pattern for managing multiple specialized agents.
    """

    def __init__(self, agents_root: Path = None):
        self.skill_root = Path(__file__).resolve().parent.parent
        self.agents_root = agents_root or (self.skill_root / "agents")

        config = load_skill_config(self.skill_root)
        enabled = get_nested(config, "multi_agent", "enabled_agents", default=None)
        enabled_set = set(enabled) if isinstance(enabled, list) else None
        priorities = get_nested(config, "multi_agent", "agent_priorities", default={})
        priorities = priorities if isinstance(priorities, dict) else {}
        frontend_design_keywords = get_nested(
            config,
            "multi_agent",
            "frontend_design_keywords",
            default=[],
        )
        if not isinstance(frontend_design_keywords, list):
            frontend_design_keywords = []
        self.frontend_design_keywords = [
            str(keyword).lower()
            for keyword in frontend_design_keywords
            if str(keyword).strip()
        ]
        frontend_design_companion_agents = get_nested(
            config,
            "multi_agent",
            "frontend_design_companion_agents",
            default=["brainstorming"],
        )
        if not isinstance(frontend_design_companion_agents, list):
            frontend_design_companion_agents = ["brainstorming"]
        self.frontend_design_companion_roles = {
            role
            for role in (
                self._coerce_agent_role(str(agent_name))
                for agent_name in frontend_design_companion_agents
            )
            if role is not None
        }

        self.registry: Dict[AgentRole, AgentCapability] = {}
        for role, cap in AGENT_REGISTRY.items():
            if enabled_set is not None and role.value not in enabled_set:
                continue
            override_pri = priorities.get(role.value, cap.priority)
            try:
                override_pri_int = int(override_pri)
            except Exception:
                override_pri_int = cap.priority
            self.registry[role] = AgentCapability(
                role=cap.role,
                name=cap.name,
                description=cap.description,
                keywords=self._build_keywords(cap),
                priority=override_pri_int,
            )

        # Validate agent SKILL.md existence; drop missing ones to avoid emitting broken paths.
        if self.agents_root.exists():
            missing: List[str] = []
            for role in list(self.registry.keys()):
                if not (self.agents_root / role.value / "SKILL.md").exists():
                    missing.append(role.value)
                    self.registry.pop(role, None)
            if missing:
                print(
                    f"[awesome-code] warning: missing agent SKILL.md for roles: {', '.join(sorted(missing))}",
                    file=sys.stderr,
                )
        else:
            print(f"[awesome-code] warning: agents_root does not exist: {self.agents_root}", file=sys.stderr)

        self.matcher = AgentMatcher(registry=self.registry)

    def _build_keywords(self, capability: AgentCapability) -> List[str]:
        """Merge base keywords with config-driven extensions."""
        keywords = list(capability.keywords)
        if capability.role == AgentRole.FRONTEND_SPECIALIST:
            keywords.extend(self.frontend_design_keywords)
        return keywords

    def _coerce_agent_role(self, value: str) -> Optional[AgentRole]:
        """Convert config values into known agent roles."""
        try:
            return AgentRole(value)
        except ValueError:
            return None

    def _is_frontend_design_task(self, task_keywords: set[str]) -> bool:
        """Detect UI tasks that need design-first routing."""
        if task_keywords & FRONTEND_DESIGN_SIGNAL_KEYWORDS:
            return True
        return bool(task_keywords & set(self.frontend_design_keywords))

    def _should_suppress_for_frontend_design(self, assignment: AgentAssignment) -> bool:
        """Drop auth/debug false positives for visual frontend redesign tasks."""
        if assignment.agent_role not in {AgentRole.SYSTEMATIC_DEBUGGING, AgentRole.BACKEND_SPECIALIST}:
            return False
        return bool(assignment.matched_keywords) and set(assignment.matched_keywords) <= AMBIGUOUS_AUTH_KEYWORDS

    def _frontend_design_matches(self, task_keywords: set[str]) -> List[str]:
        """Return readable matched keywords for promoted design companions."""
        matches = sorted((task_keywords & set(self.frontend_design_keywords)) or (task_keywords & FRONTEND_DESIGN_SIGNAL_KEYWORDS))
        return matches[:3]

    def _ensure_frontend_design_companions(
        self,
        task: Task,
        task_keywords: set[str],
        assignments: List[AgentAssignment],
    ) -> List[AgentAssignment]:
        """Ensure design tasks keep the intended design-thinking companion agents."""
        has_frontend = any(a.agent_role == AgentRole.FRONTEND_SPECIALIST for a in assignments)
        if not has_frontend:
            return assignments

        assigned_roles = {a.agent_role for a in assignments}
        frontend_confidence = max(
            (a.confidence for a in assignments if a.agent_role == AgentRole.FRONTEND_SPECIALIST),
            default=0.22,
        )
        for role in sorted(self.frontend_design_companion_roles, key=lambda item: item.value):
            if role in assigned_roles or role not in self.registry:
                continue
            assignments.append(
                AgentAssignment(
                    agent_role=role,
                    task=task,
                    confidence=round(max(0.18, frontend_confidence - 0.06), 3),
                    matched_keywords=self._frontend_design_matches(task_keywords),
                )
            )
        return assignments

    def analyze_task(self, task: Task) -> Dict[str, Any]:
        """
        Analyze a task and recommend appropriate agents

        Args:
            task: The task to analyze

        Returns:
            Analysis dictionary with agent recommendations
        """
        # Match agents to task
        assignments = self.matcher.match_agents(task)
        extracted_keywords = self.matcher._extract_keywords(task.description)
        task_keywords = set(str(k).lower() for k in (task.keywords or []))
        task_keywords.update(extracted_keywords)

        if self._is_frontend_design_task(task_keywords):
            assignments = [
                assignment
                for assignment in assignments
                if not self._should_suppress_for_frontend_design(assignment)
            ]
            assignments = self._ensure_frontend_design_companions(task, task_keywords, assignments)
            assignments.sort(
                key=lambda a: (-a.confidence, -self.registry[a.agent_role].priority, a.agent_role.value)
            )

        # Filter to top agents
        top_assignments = assignments[:5] if len(assignments) > 5 else assignments

        # Build analysis
        analysis = {
            "task": task.description,
            # Keep keyword list stable (dedup while preserving order).
            "keywords": list(dict.fromkeys(task.keywords + extracted_keywords)),
            "recommended_agents": [],
            "coordination_strategy": self._determine_strategy(top_assignments),
            "execution_plan": self._create_execution_plan(top_assignments)
        }

        for assignment in top_assignments:
            capability = self.registry[assignment.agent_role]
            analysis["recommended_agents"].append({
                "role": assignment.agent_role.value,
                "name": capability.name,
                "description": capability.description,
                "confidence": assignment.confidence,
                "priority": capability.priority,
                "matched_keywords": assignment.matched_keywords,
                "skill_path": str(self.agents_root / assignment.agent_role.value / "SKILL.md")
            })

        return analysis

    def _determine_strategy(self, assignments: List[AgentAssignment]) -> str:
        """Determine the best coordination strategy"""
        if len(assignments) == 0:
            return "no_agents"

        if len(assignments) == 1:
            return "single_agent"

        # Check if agents can work in parallel
        parallel_roles = {
            AgentRole.FRONTEND_SPECIALIST,
            AgentRole.BACKEND_SPECIALIST,
            AgentRole.DOCUMENTATION_SPECIALIST,
        }

        if any(a.agent_role in parallel_roles for a in assignments):
            return "parallel"

        # Sequential processing for dependent tasks
        return "sequential"

    def _create_execution_plan(
        self,
        assignments: List[AgentAssignment]
    ) -> List[Dict[str, Any]]:
        """Create an execution plan for the agents"""
        strategy = self._determine_strategy(assignments)

        if strategy == "parallel":
            return self._create_parallel_plan(assignments)
        elif strategy == "sequential":
            return self._create_sequential_plan(assignments)
        else:
            return self._create_single_plan(assignments[0] if assignments else None)

    def _create_parallel_plan(
        self,
        assignments: List[AgentAssignment]
    ) -> List[Dict[str, Any]]:
        """Create a parallel execution plan"""
        return [
            {
                "stage": 1,
                "type": "parallel",
                "agents": [
                    {
                        "role": a.agent_role.value,
                        "task": a.task.description,
                        "confidence": a.confidence
                    }
                    for a in assignments
                ]
            }
        ]

    def _create_sequential_plan(
        self,
        assignments: List[AgentAssignment]
    ) -> List[Dict[str, Any]]:
        """Create a sequential execution plan"""
        return [
            {
                "stage": i + 1,
                "type": "sequential",
                "agent": {
                    "role": a.agent_role.value,
                    "task": a.task.description,
                    "confidence": a.confidence
                }
            }
            for i, a in enumerate(assignments)
        ]

    def _create_single_plan(
        self,
        assignment: Optional[AgentAssignment]
    ) -> List[Dict[str, Any]]:
        """Create a single agent execution plan"""
        if not assignment:
            return []

        return [
            {
                "stage": 1,
                "type": "single",
                "agent": {
                    "role": assignment.agent_role.value,
                    "task": assignment.task.description,
                    "confidence": assignment.confidence
                }
            }
        ]

def main():
    """CLI interface for the agent coordinator"""
    if len(sys.argv) < 2:
        print("Usage: python3 agent_coordinator.py <task_description>")
        print("\nExample:")
        print('  python3 agent_coordinator.py "I need to fix a bug in the login feature"')
        sys.exit(1)

    task_description = " ".join(sys.argv[1:])

    # Create coordinator
    coordinator = AgentCoordinator()

    # Create task
    task = Task(description=task_description)

    # Analyze task
    analysis = coordinator.analyze_task(task)

    # Print results
    print(json.dumps(analysis, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
