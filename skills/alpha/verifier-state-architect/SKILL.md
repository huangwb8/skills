---
name: verifier-state-architect
description: 帮助设计或审查 Agent Skill 的 Verifier 与 State 架构。只要用户要为 skill 规划、评估、精简或接入 verifier/state，尤其担心形式主义、过度设计、硬编码或 Kernel 契约不匹配，就使用本技能。它先理解目标 skill 的业务流程，再判断是否真的需要这些外挂，输出可执行的 Markdown 设计计划；不直接创建状态机或验证器实现。
metadata:
  author: Bensz Conan
  short-description: 为 Agent Skill 规划最小、可解释、AI 友好的 Verifier/State 组合
  keywords:
    - verifier-state-architect
    - verifier design
    - state design
    - Kernel Pack
    - evidence contract
    - 状态机设计
    - 验证器设计
---

# Verifier-State Architect

## 目标

帮助设计或审查 Agent Skill 的 Verifier 与 State 架构。只要用户要为 skill 规划、评估、精简或接入 verifier/state，尤其担心形式主义、过度设计、硬编码或 Kernel 契约不匹配，就使用本技能。它先理解目标 skill 的业务流程，再判断是否真的需要这些外挂，输出可执行的 Markdown 设计计划；不直接创建状态机或验证器实现。

架构顾问 Skill：Verifier/State 是可插拔外挂，不为展示 Kernel 强行加入。只产出设计计划，不写 `VERIFIER.md`、`STATE.md`、Pack 脚本或 Kernel 源码。

## 流程

### 输入

#### 适用边界

- **适用**：规划/审查 Skill 的 Verifier/State 接入、把自然语言判断映射到 Kernel 契约、生成实现交接计划。
- **不适用**：直接实现已确定组件、修 Kernel bug、写普通 Skill 内容，或跳过分析直接改代码；这些任务可把本 Skill 计划作为前置阶段。

### 执行步骤

#### 核心工作流

##### 理解服务对象

读取目标 `SKILL.md`、`config.yaml`、脚本、references、模板和运行声明；按需读取 Kernel Pack、ID 与运行时文档。绘制目标、输入/输出、阶段、风险、失败/回退、人工介入和产物；从证据列出稳定命题的 Verifier 候选与持续阶段的 State 候选，标记来源和不确定性，不从文件名或关键词臆测。

##### 删除影响闸门

逐项回答：

- 删除 Verifier 是否损失可复核的安全/质量边界，而非只少形式检查？
- 删除 State 是否损失恢复、协作、Gate 或阶段可见性，而非只少标签？
- 组件是否改变下一步决策、阻止高代价错误、支持重放/审计或提供可行动的人工复核？
- 是否已有更通用的内置 Pack/State？只有通用组件无法表达稳定命题时才设计专用组件。

若删除不改变能力、决策或审计性，明确“不接入”；零组件或只保留一个均合法。

##### Kernel 复用与元组件二层审查

在专用设计前完成以下盘点，避免重复造轮子，也不默认新增 Kernel 功能：

1. 读取 `packages/bensz-skill-kernel` 的 `verifiers/index.json`、`states/index.json`、对应 `VERIFIER.md`/`STATE.md`、README 和版本声明；记录 canonical ID、版本、classification/kind、输入契约、入口及限制，不能只看名称/标签。
2. 为每个候选标记“直接复用 / 组合复用 / 适配后复用 / 不适用”，比较语义、输入/证据契约、Gate/转移、资源边界、版本兼容和失败路径；事实结构相同而仅词汇不同，优先适配器。
3. 检查是否有可在两个及以上不相邻领域复用、领域无关、契约稳定、可独立版本化和可回放的能力。Verifier 要能用 `subject/context/evidence` 表达稳定命题；State 要表达跨 Skill 的持续阶段/生命周期，而非动作、标签或一次性 helper。
4. 依赖领域规则、模型偏好、易变阈值、特定格式或单一 Skill 偶然流程的候选，留在 Skill/适配器层；证据不足时标为“待验证的 Kernel 提炼候选”。Kernel 建议只写入计划（范围、契约、兼容/迁移、测试、风险），不直接改 Kernel。
5. 最终计划必须单独列出“Kernel 复用结论”和“Kernel 元组件提炼结论”。无论复用、适配、暂不复用、推荐提炼还是明确不提炼，每项至少用 2 个项目符号说明证据、收益/代价和边界理由；证据不足还要列缺口与验证动作。

##### AI 与确定性分工

为每个设计项写一行分工：

- **确定性**：JSON/Markdown 结构、路径、哈希、存在性、超时、结果枚举、事件完整性等机械边界。
- **AI/自然语言**：业务语义、质量充分性、相关性、风险解释、冲突处理和下一步规划；结果带理由、证据锚点、置信度及 `uncertain/unchecked` 路径。
- **混合**：脚本只收集/规范化事实，AI 按 `VERIFIER.md` 与 Evidence Contract 判断；脚本不得编码领域结论。

逐条追问硬编码规则是否稳定、跨模型可复现且能安全 fail-closed；否则改为自然语言契约、证据字段和人工复核条件。语义 Verifier 至少定义 `subject`、`context`、`evidence`、`verdict`、`summary`、`evidence_refs`、`confidence`、`uncertainties`；`verdict` 只用 Kernel 枚举，证据不足/网络不可观测返回 `uncertain`/`unchecked`，不得把模型自评当 `pass`。

##### Kernel 对接

计划必须说明：

- Verifier 用 `owner.domain.capability`、State 用 `owner.machine.state`；版本和 alias 独立维护，不把 Skill 名、模型、实现或 Gate 策略写入 ID。
- Pack 的 `VERIFIER.md`/`STATE.md` 负责判断目标、入口条件、不变量、证据边界和转移；`index.json` 是元数据单一来源；入口仅 JSON-stdio，路径留在 Pack 内。
- Kernel 只负责发现、协议校验、超时/资源边界、结果归一化、Gate、事件和状态持久化；领域判断留在 Skill 契约或 AI 适配器。
- `required`/`advisory`、Gate 放行条件、`uncertain/unchecked` 人工复核去向、`run_id`/`attempt_id`、失败/恢复和事件重放策略。
- 无 Verifier 时将 Gate 写为“不适用/无需验证”，无 State 时说明由普通流程和工作区生命周期承担；接入时 required 缺失必须 fail-closed，advisory 只提示不阻塞。
- 状态图只保留稳定业务节点；动作放入 transition/event/helper；系统工作区状态与 Skill 领域状态分层，不把领域状态硬编码进 Kernel reducer。
- 外部路径、网络、子进程和大输入采用最小权限、超时、体积上限及越界拒绝；入口禁止 `..`、绝对路径和 symlink 逃逸。

附“Kernel 复用与提炼决策表”：候选能力、现有 Kernel ID/版本、复用方式、契约差异、是否跨领域、提炼建议、主要理由、验证动作；表格须与两个结论互相引用。

##### 最小设计

使用矩阵：

| 候选 | 保留/删除 | 稳定命题或状态含义 | AI/脚本分工 | 输入与证据 | Gate/转移 | 失败与人工复核 |
| --- | --- | --- | --- | --- | --- | --- |

给出最小状态图（初始、主要阶段、终止/失败、可选回退）和 Verifier 清单；每项写“为什么不可删除”，否则删除或降级为普通说明。

#### 业务流程与风险地图

#### Verifier 设计矩阵

#### State 设计矩阵与最小状态图

#### AI/确定性分工与 Evidence Contract

#### Kernel 对接、Gate、重放与资源边界

#### Kernel 复用与元 Verifier/State 提炼决策

#### 实施顺序（P0/P1/P2）

#### 已知不确定性、回退方案和不在范围内的事项

```

“Kernel 复用与元 Verifier/State 提炼决策”必须包含：

- **现有 Kernel 能力盘点**：实际读取的索引/契约及其对应候选。
- **Kernel 复用结论**：直接、组合、适配或不适用；每项至少两条理由，含契约匹配度及失败/维护成本。
- **元组件提炼结论**：推荐、暂缓验证或明确不提炼；每项至少两条理由，含跨领域证据、稳定性、版本化收益及领域耦合风险。
- **对人类决策的影响**：采纳/不采纳建议会改变的文件、兼容性、测试、迁移成本和维护责任。

两类结论即使均为“不复用/不提炼”也必须保留并分点说明。实施顺序只写下一步改动，不改源代码：P0 为安全/完整性/不可恢复错误，P1 为契约/可观测性，P2 为可选改进；每项含文件位置、证据、影响、验证命令和完成条件。

### 输出

#### 输入、输出与工作区

- **必需输入**：目标 Skill 根目录或完整内容、业务目标和已知约束。
- **可选输入**：Kernel 路径（默认 `packages/bensz-skill-kernel`）、`runtime` 声明、Pack、测试、历史报告和输出路径。
- **默认计划**：`./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/verifier-state-architect/output/design-plan.md`；用户指定正式计划时优先写 `docs/plans/` 或指定路径，不把正式交付藏在 `.bensz-api`。
- 计划只作后续 Agent 的短契约：引用用相对路径和行号/标题锚点，日志只写脱敏摘要。
- 复用会话已声明的任务根目录；否则用 `bsk workspace init . --description verifier-state-architect` 初始化，并在 Skill 专属 `input|output|log` 边界工作。记录目标路径、读取清单、Kernel 版本和计划路径。

#### 计划固定结构

```markdown
# Verifier/State 设计计划：<skill>

#### 结论摘要

### 输出管理

正式交付物、临时产物和日志继续遵循原有路径及覆盖边界；任务级中间文件使用当前会话声明的 `.bensz-api` 工作区。

### 校验

#### 删除影响测试（含“不接入”结论）

#### 验收与回归测试

#### 质量闸门

- 是否有删掉也不影响能力的组件？若有删除或解释保留理由。
- 是否把领域规则硬编码进 Kernel、脚本阈值或 ID？若有迁移到契约/适配器。
- 是否区分事实收集与语义判断，并保留不确定结果的人工复核？
- 是否逐项核对 Kernel 索引/契约，记录复用或不适用理由？
- 是否找到并论证跨至少两个领域的元组件？若没有，是否说明耦合、证据不足或维护成本原因？
- 是否能从事件/快照重放，且失败不会伪装为通过？
- 测试是否覆盖 canonical/alias、非法输入、超时、越界路径、Gate 缺证据和删除后的回退？
- 计划是否写出目标 Skill/Kernel 版本、读取证据、决策日期、实现位置，以及两个独立结论的分点理由和人类决策影响？

资料不足时停在“待确认”，不凭空补状态/规则；中间文件遵循 `.bensz-api` 协议，禁止记录密钥、令牌、Cookie、私有 Prompt 或不必要原始数据。作为更大任务中间环节时只交付计划和机器可读摘要；独立使用时说明保留/删除、原因、下一步、计划路径和验证证据。

### 失败与恢复

遇到原正文未覆盖的错误时停止、保留证据并报告，不猜测性继续。


## 约束

遵守 `.bensz-api` 任务工作区协议和 BAC 贡献记录；不记录 API Key、访问令牌、密码、Cookie、凭据、私有 Prompt 或用户隐私。文件操作限于授权范围，未经授权不执行远程写入、删除或覆盖；Skill 设计缺陷按 `bensz-collect-bugs` 先本地脱敏记录。

#### 与 bensz-collect-bugs 的边界

仅记录本 Skill 或 Bensz 基础设施的设计缺陷（触发漏判、契约不完整、环境假设错误等）；用户数据错误、第三方抖动、用户改源码和偶发模型波动不属于此范围。先脱敏写入 `~/.bensz-skills/bugs/`，本轮不中断；只有用户明确要求才用本机 `gh api` 上报 `huangwb8/bensz-bugs`，不 clone。禁止直接修改用户本地已安装 Skill 来“顺手修 bug”。
