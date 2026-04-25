---
name: awesome-code
description: 当用户明确要求"使用 awesome-code / 多代理协作 / 并行协调开发"时使用。通过脚本解析任务，输出 `required / preferred / optional` 三层子代理分派、`dispatch_gate` 门禁与可执行的下一步；当 required agent 缺失时必须阻塞继续执行。⚠️ 不适用：用户仅需单一角色的简单修改或咨询、用户未明确表达多代理协作意图、用户只是了解技能概念。
metadata:
  short-description: 智能多代理软件开发协调系统
  keywords:
    - 多代理协调
    - 任务拆解
    - 并行执行
    - 软件工程
    - 专业化代理
    - awesome-code
  category: 软件开发工具
  author: Bensz Conan
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Awesome Code - 智能多代理软件开发协调系统

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求“report bensz skills bugs”等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

本技能用于“复杂开发任务”的多代理编排：先用确定性脚本做任务拆解与路径发现，再按策略驱动分派加载子代理规范并执行。

## 执行前置：动态发现技能安装路径（硬编码部分）

在调用任何脚本之前，必须先运行 `scripts/get_path.py` 动态发现真实安装路径，并使用返回的绝对路径执行后续命令（避免硬编码 `~/.claude/skills/` / `.claude/skills/`）。

```bash
python3 ~/.claude/skills/awesome-code/scripts/get_path.py
python3 ~/.codex/skills/awesome-code/scripts/get_path.py
# 或（项目级安装）
python3 .claude/skills/awesome-code/scripts/get_path.py
python3 .codex/skills/awesome-code/scripts/get_path.py
```

从 JSON 输出中读取：
- `skill_root`
- `executable_scripts.*`（例如 `executable_scripts.agent_coordinator`）

## 核心理念

- 智能任务识别：用脚本把“需求描述”转成可执行的任务拆解/策略建议
- 多代理协调：对独立子任务并行，对有依赖的子任务顺序执行
- 分层分派：把子代理分成 `required / preferred / optional` 三层，而不是只给一组泛化推荐
- 强制门禁：命中 required 路由时，若对应 agent 缺失、禁用或不可调度，必须通过 `dispatch_gate` 阻塞继续执行
- 留痕可审计：输出 `dispatch_manifest`，执行后需要补 `dispatch_receipts` 才能证明 required agent 真的被调用过
- 专业化分工：每个子代理专注一个领域，降低单模型的认知负担
- 渐进式信息披露：只在需要时加载对应子代理的 `SKILL.md`
- 前端设计优先：UI/UX 任务先定视觉方向、布局策略与设计护栏，再进入真实代码实现

## 代理团队（14 个子代理）

| role | 领域 |
|------|------|
| tdd-workflow | TDD 测试驱动开发 |
| systematic-debugging | 系统化调试与根因分析 |
| code-reviewer | 代码审查与质量保证 |
| git-workflow | Git 工作流与版本控制 |
| frontend-specialist | 前端开发与组件设计 |
| backend-specialist | 后端开发与 API 设计 |
| devops-specialist | DevOps 与自动化运维 |
| security-specialist | 应用安全与合规 |
| documentation-specialist | 技术文档与 API 文档 |
| context-optimizer | 上下文管理与优化 |
| brainstorming | 交互式设计优化 |
| mirror-optimizer | 镜像源优化 |
| writing-plans | 实施计划与任务拆解 |
| multi-agent-coordinator | 多代理协调 |

## 核心工作流（AI 执行）

1. 运行 `get_path.py`，拿到 `executable_scripts.agent_coordinator` 的绝对路径。
2. 调用 `agent_coordinator.py` 进行任务分析，读取 `required_agents`、`preferred_agents`、`optional_agents`、`dispatch_gate` 与 `dispatch_manifest`。
3. 若 `dispatch_gate.can_proceed = false`：
   - 停止继续执行，不要假装已经进入实现阶段
   - 明确说明 `blocking_reason` 与 `missing_agents`
   - 只给出“如何补齐 required agent / 配置 / 运行条件”的下一步
4. 若 `dispatch_gate.can_proceed = true`：
   - 先按需加载 required agents 的 `awesome-code/agents/{role}/SKILL.md`
   - 再按任务复杂度补充 preferred / optional agents
   - 按协调策略执行：
   - 并行：相互独立的任务（例如“写测试 + 改文档 + 做静态检查”）
   - 顺序：存在依赖链的任务（例如“先修 bug → 再补测试 → 再重构”）
5. 聚合结果并留痕：
   - 统一口径（术语/目标/约束）
   - 标注 P0/P1/P2 优先级
   - 为实际调用的 agent 回填 `dispatch_receipts`
   - 给出可执行的下一步（含验证方式）

## 强制路由语义

- `required_agents`
  - 当前任务若缺这个 agent，就不能继续推进实现
  - 典型场景：安全漏洞、系统化调试、TDD/test-first、明确的 UI 重设计
- `preferred_agents`
  - 强烈建议一起参与；缺失时可以继续，但要在结果中说明降级
  - 典型场景：前端重设计时的 `brainstorming`
- `optional_agents`
  - 可以补充效率或覆盖面，但不是门禁

当前门禁输出至少包含：

- `dispatch_gate.can_proceed`
- `dispatch_gate.blocking_reason`
- `dispatch_gate.missing_agents`
- `dispatch_manifest`

## 前端/UI 特殊编排

当任务涉及 UI、设计系统、仪表盘、落地页或界面重设计时，优先按以下口径协调：

- `brainstorming`：负责风格方向、信息层级、交互概念；用户要求自主推进时，先内部完成静默设计简报，不把提问变成阻塞
- `frontend-specialist`：负责把设计判断落成真实前端代码，包括 typography、color tokens、layout、background 与 motion 策略
- 默认策略：`frontend-specialist` 通常进入 `required_agents`，`brainstorming` 默认进入 `preferred_agents`
- 若任务明确要求“先出方向 / 先出方案 / 先做设计简报”，`brainstorming` 升级为 `required_agents`
- 如任务进一步扩展到复杂多组件 artifact，可借鉴 `frontend-design` 的设计优先方法与 `web-artifacts-builder` 的工程化思路，但默认仍由现有代理团队完成

最小示例：

```bash
python3 ~/.claude/skills/awesome-code/scripts/get_path.py
python3 /ABS/PATH/awesome-code/scripts/agent_coordinator.py "fix login bug"
```

## 常用脚本（确定性操作）

注意：脚本路径以 `get_path.py` 输出为准。

- `scripts/get_path.py`：输出 `skill_root` 与可执行脚本绝对路径（JSON）
- `scripts/agent_coordinator.py`：任务分析 → 分层分派 + `dispatch_gate` + 协调策略
- `scripts/subagent_policy.py`：命中 required/preferred 路由并生成分派要求
- `scripts/subagent_dispatch_audit.py`：生成 `dispatch_manifest` 并校验 `dispatch_receipts`
- `scripts/create_test_session.py`：创建 A/B 轮会话目录与计划骨架（便于追溯）
- `scripts/test_runner.py`：运行测试/覆盖率
- `scripts/code_analyzer.py`：静态分析与质量检查
- `scripts/performance_benchmark.py`：基准测试与报告

## 配置管理（Single Source of Truth）

- 版本号仅在 `awesome-code/config.yaml:skill_info.version` 维护；`SKILL.md` 不记录版本历史。
- 代理启用与优先级：`awesome-code/config.yaml:multi_agent.*`
- 强制分派策略：`awesome-code/config.yaml:multi_agent.dispatch_policy.*`
- 质量阈值/开关：`awesome-code/config.yaml:tdd`、`awesome-code/config.yaml:code_review` 等
- 变更记录：`awesome-code/CHANGELOG.md`

## 参考资料（仅一层深度；需要时按需加载）

- TDD：`awesome-code/references/tdd-best-practices.md`
- 系统化调试：`awesome-code/references/debugging-systematic.md`
- 代码审查清单：`awesome-code/references/code-review-checklist.md`
- Git 工作流：`awesome-code/references/git-workflow.md`
- 多代理协调模式：`awesome-code/references/multi-agent-patterns.md`
- 上下文优化策略：`awesome-code/references/context-optimization.md`
- 批判性思维与测试优化：`awesome-code/references/CRITICAL_THINKING_GUIDE.md`
- A 轮计划模板：`awesome-code/references/A_ROUND_PLAN_TEMPLATE.md`
- 建设性建议：`awesome-code/references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md`
- 问题挖掘技巧：`awesome-code/references/ISSUE_DISCOVERY_TECHNIQUES.md`
- 反例库：`awesome-code/references/ANTI_PATTERNS_LIBRARY.md`
- 脚本调用策略：`awesome-code/references/SCRIPT_PATH_STRATEGY.md`
