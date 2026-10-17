---
name: awesome-code
description: 当用户明确要求使用 awesome-code、进行多代理协作或需要复杂任务规划时使用。它负责拆解任务、选择专业角色、设置门禁并审查结果；所有 Agent 的创建、隔离、串行或并行执行都必须交给 `parallel-vibe`。⚠️ 不适用：用户只需单一角色完成简单修改或咨询，或未表达多代理协作意图。
metadata:
  short-description: AI 自主规划多代理软件开发协调系统
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

# Awesome Code - AI 自主规划多代理软件开发协调系统

## 目标

当用户明确要求"使用 awesome-code / 多代理协作 / 并行协调开发"时使用。通过脚本收集可用 Agent 摘要、配置约束与 `dispatch_gate`，再由 AI 负责任务拆解、角色选择和策略规划；只要计划使用 Agent，就必须把创建、隔离、串行或并行执行交给 `parallel-vibe`，本 Skill 不得直接创建或调度 Agent。当配置中的 required route agent 缺失时必须阻塞继续执行。⚠️ 不适用：用户仅需单一角色的简单修改或咨询、用户未表达多代理协作意图、用户只是了解技能概念。

## 流程

### 输入

输入为用户的复杂开发任务、项目根目录和可用 Agent 配置；可选输入包括 `config.yaml` 的 required route、`parallel-vibe` 执行底座、脚本路径和已有任务工作区。仅在用户明确要求多代理/并行协调时触发；复杂开发任务可在获得该授权后由本 Skill 规划，单一角色的局部任务不走本 Skill。

### 执行步骤

#### 执行前置：动态发现技能安装路径（硬编码部分）

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

#### 核心理念

- 脚本做确定性操作：路径发现、`agents/*/SKILL.md` frontmatter 摘要提取、配置加载、Agent 缺失检查
- AI 做语义判断：理解任务、选择 Agent、决定 single-pass / focused-agent / parallel / sequential 策略
- 少分派优先：小而明确的任务直接完成；在用户已明确授权使用本 Skill 后，只有专业风险、跨模块依赖或用户明确要求协作时才升级
- 歧义先拦截：目标、边界或验收标准不清楚的高风险/宽泛任务，由 AI 主动澄清或显式记录保守假设
- 外科手术式修改：每轮遵守 `dispatch_guidance.minimal_change_scope_default`
- 目标驱动验证：执行前先决定怎样证明完成，执行后报告验证结果
- 强制门禁：配置中的 required route agent 缺失、禁用或不可调度时，必须通过 `dispatch_gate` 阻塞继续执行
- 留痕可审计：实际调用 required agent 后，需要补 `dispatch_receipts` 才能证明门禁已被满足
- 专业化分工：每个子代理专注一个领域，降低单模型的认知负担
- 执行底座分离：`awesome-code` 只负责规划、角色选择、门禁和结果审查；Agent 的创建、工作区隔离、串行/并行调度、回收与汇总统一由 `parallel-vibe` 负责
- 渐进式信息披露：只在需要时加载对应子代理的 `SKILL.md`

#### 代理团队

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

#### 核心工作流

1. 运行 `get_path.py`，拿到 `executable_scripts.agent_coordinator` 的绝对路径。
2. 调用 `agent_coordinator.py` 收集规划上下文，读取 `available_agents`、`config_constraints`、`dispatch_guidance` 与 `dispatch_gate`。
3. 若 `dispatch_gate.can_proceed = false`：
   - 停止继续执行，不要假装已经进入实现阶段
   - 明确说明 `blocking_reason` 与 `missing_agents`
   - 只给出“如何补齐 required route agent / 配置 / 运行条件”的下一步
4. 读取 `execution_contract`。若计划使用任何 Agent，必须调用配置中声明的执行底座；若契约缺失或无效，`dispatch_gate` 必须阻塞多代理路径，不得由本 Skill 补默认底座，也不得直接调用宿主的 spawn 或并发机制。
5. 若门禁允许继续，AI 自主规划：
   - 阅读任务描述和 `available_agents` 的 `description`
   - 判断是否需要澄清；用户要求自主推进时，选择最保守且可验证的假设
   - 自行选择 `single-pass`、`focused-agent`、`parallel` 或 `sequential`
   - 若选择子代理，只加载选中 Agent 的 `awesome-code/agents/{role}/SKILL.md`
   - 若判断某个 `config_constraints.required_routes` 适用，该 route 中的 agents 视为 required
6. 按规划执行：
   - single-pass：主模型直接完成
   - focused-agent：把一个 Agent 的执行计划交给 `parallel-vibe`
   - parallel：把相互独立的 Agent 任务交给 `parallel-vibe` 并行执行
   - sequential：把存在依赖链的 Agent 任务交给 `parallel-vibe` 按序执行
   - 全程遵守 `dispatch_guidance` 的最小变更边界
7. 聚合结果并留痕：
   - 统一口径（术语/目标/约束）
   - 标注 P0/P1/P2 优先级
   - 为实际调用的 required agent 回填 `dispatch_receipts`
   - 对照自定验收标准与验证计划给出结果

#### Agent 选择指导

- Bug、测试失败和异常优先考虑 `systematic-debugging`；先根因，后修复。
- test-first、回归测试和覆盖率任务优先考虑 `tdd-workflow`。
- 安全、认证、权限、注入和敏感数据任务优先考虑 `security-specialist`。
- 前端实现、UI/UX、设计系统、仪表盘和落地页任务优先考虑 `frontend-specialist`；需要先探索方向时可先用 `brainstorming`。
- API、服务端、数据库和业务逻辑任务优先考虑 `backend-specialist`。
- 部署、CI/CD、容器和运维任务优先考虑 `devops-specialist`。
- 文档、README 和 API 文档任务优先考虑 `documentation-specialist`。
- 计划、拆解和跨代理协调分别考虑 `writing-plans` 与 `multi-agent-coordinator`。

最小示例：

```bash
python3 ~/.claude/skills/awesome-code/scripts/get_path.py
python3 /ABS/PATH/awesome-code/scripts/agent_coordinator.py "fix login bug"
```

#### 常用脚本

注意：脚本路径以 `get_path.py` 输出为准。

- `scripts/get_path.py`：输出 `skill_root` 与可执行脚本绝对路径（JSON）
- `scripts/agent_coordinator.py`：Agent 摘要收集 + 配置约束 + `dispatch_gate`
- `scripts/subagent_policy.py`：读取 required routes 并校验配置中 required route agents 是否可用
- `scripts/subagent_dispatch_audit.py`：生成 `dispatch_manifest` 并校验 `dispatch_receipts`
- `scripts/create_test_session.py`：创建 A/B 轮会话目录与计划骨架（便于追溯）
- `scripts/test_runner.py`：运行测试/覆盖率
- `scripts/code_analyzer.py`：静态分析与质量检查
- `scripts/performance_benchmark.py`：基准测试与报告

#### Single Source of Truth

- 版本号仅在 `awesome-code/config.yaml:skill_info.version` 维护；`SKILL.md` 不记录版本历史。
- 代理启用状态：`awesome-code/config.yaml:multi_agent.enabled_agents`
- 多代理执行底座：`awesome-code/config.yaml:dependencies.agent_execution`（当前声明为 `parallel-vibe`；运行时不补默认值）
- 强制分派策略：`awesome-code/config.yaml:multi_agent.dispatch_policy.*`
- 质量阈值/开关：`awesome-code/config.yaml:tdd`、`awesome-code/config.yaml:code_review` 等
- 变更记录：`awesome-code/CHANGELOG.md`

#### 参考资料（仅一层深度；需要时按需加载）

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

### 输出

#### 自主规划输出

`agent_coordinator.py` 不再输出 `recommended_agents`、`confidence` 或 `execution_plan`。这些属于 AI 的语义规划职责。

脚本输出至少包含：

- `planning_mode`
- `available_agents`
- `agent_count`
- `config_constraints.required_routes`
- `dispatch_gate.can_proceed`
- `dispatch_gate.blocking_reason`
- `dispatch_gate.missing_agents`
- `dispatch_guidance`
- `execution_contract`

### 输出管理

#### BenszAPI 任务工作区


本技能用于“复杂开发任务”的多代理规划：确定性脚本只负责路径发现、Agent 摘要收集、配置约束读取和 required route 可用性门禁；任务理解、Agent 选择与执行策略由 AI 自主完成，实际 Agent 执行必须通过 `parallel-vibe`。

### 校验

校验 `get_path.py` 与 `agent_coordinator.py` 的输出是否包含 `available_agents`、`agent_count`、required routes、`dispatch_gate` 和 `execution_contract` 字段；确认执行契约完全来自配置，配置缺失或无效时门禁阻塞；确认所选策略与任务风险匹配、实际调用的 required agent 有 `dispatch_receipts`，并且结果与验证计划可追溯。

### 失败与恢复

路径发现、配置读取或 required route 检查失败时保留脚本输出并阻塞后续分派，明确缺失 Agent 或阻塞原因；代理执行失败时保留已产生的结果及宿主提供的 workspace 证据，由主 Agent 决定安全重试或回退，不把未执行的代理工作标记为完成。


## 约束

<!-- BEGIN COMMON CONSTRAINTS -->
<!-- Source-Hash: sha256:15120201e9e0c7569517261d57ecefb63ac279c26ed13876f8e95b6dc35854d3 -->
<!-- Template-ID: skill-common-constraints; Template-Version: 1; Sync-Policy: exact-block -->

### 公共硬约束

本块由 `docs/templates/skill-common-constraints.md` 统一维护；每个 `SKILL.md` 的 `## 约束` 必须逐字同步本块，不得在副本中改写公共规则。

- 任务需要落盘时，使用唯一的 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/` 根目录；共享材料放入 `shared/`，Skill 专属材料放入该 Skill 的 `input/`、`output/`、`log/`。
- 正式交付物、源代码和正式计划按项目约定保存，不写入任务工作区；未经授权不覆盖、删除、迁移或远程写入。
- 项目维护变更检查 BAC 可用性并记录需求、AI 产出、工具结果、文件改动和验证摘要；BAC 只做过程审计，不替代署名、责任或合规判断。
- 不记录 API Key、访问令牌、密码、Cookie、环境/凭据文件、私有 Prompt、身份信息、本地用户名、主机名或不必要的大体积原始数据。
- 文件路径必须规范化并限制在授权项目范围内；外部 URL、子进程和网络访问遵循最小权限，防止路径遍历、SSRF 和命令注入。
- Skill 版本唯一记录在自身 `config.yaml:skill_info.version`；公开 API、协议、目录或配置变更同步文档与 `CHANGELOG.md`。
- `bensz-collect-bugs` 是一个 Agent Skill；仅将 Bensz Agent Skill 或 Bensz 基础设施本身的设计缺陷交给它。先脱敏写入 `~/.bensz-skills/bugs/`，当前任务不中断，只有用户明确要求才公开上报，禁止直接修改用户已安装的 Skill 源码。

<!-- End of canonical common constraints. -->
<!-- END COMMON CONSTRAINTS -->
