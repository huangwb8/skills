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

这是一个架构顾问 Skill：Verifier/State 是可插拔外挂，不是为了展示 Kernel 而强行加入。只产出设计计划，不写 `VERIFIER.md`、`STATE.md`、Pack 脚本或 Kernel 源码。

## 适用边界

用于：规划或审查 Skill 的 Verifier/State 接入、把自然语言判断映射到 Kernel 契约、生成实现交接计划。

不用于：直接实现已确定组件、修 Kernel bug、写普通 Skill 内容或跳过分析直接改代码；这些任务可把本 Skill 计划作为前置阶段。

## 输入与默认输出

- **必需**：目标 Skill 根目录或完整内容；用户的业务目标和已知约束。
- **可选**：Kernel 包路径（默认 `packages/bensz-skill-kernel`）、现有 `runtime` 声明、Pack、测试、历史报告和用户指定的输出路径。
- **默认中间输出**：`./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/verifier-state-architect/output/design-plan.md`。
- **用户指定路径优先**：若用户要求正式计划，写入 `docs/plans/` 或其指定位置；不要把正式交付物藏在 `.bensz-api`。

计划是给后续 Agent 使用的短契约，不复制完整源文件。所有引用都写相对路径和行号/标题锚点，敏感内容只记录脱敏摘要。

开始前先复用会话中已声明的任务根目录；没有任务根目录时，用 `bsk workspace init . --description verifier-state-architect` 初始化，并在 Skill 专属 `input|output|log` 边界工作。记录目标 Skill 路径、读取清单、Kernel 版本和计划路径；不把用户提供的完整原文复制进日志。

## 核心工作流

### 理解服务对象

1. 读取目标 `SKILL.md`、`config.yaml`、脚本、references、模板和运行声明；按需读取 Kernel Pack、ID 与运行时文档。
2. 画出目标、输入、输出、阶段、失败/回退、人工介入和产物；不从文件名或关键词推断。
3. 从证据列出 Verifier 候选（稳定命题）与 State 候选（持续阶段），标注来源和不确定性。

### 先证明“值得存在”

逐项执行删除影响测试：

- **删除 Verifier 后**，是否会失去可复核的安全/质量边界，或只是少一段形式检查？
- **删除 State 后**，是否会失去恢复、协作、Gate 或阶段可见性，或只是给流程贴标签？
- 它是否改变下一步决策、阻止高代价错误、支持重放/审计，或提供可行动的人工复核入口？
- 是否已有更通用的内置 Pack/状态可以复用？专用组件只有在通用组件无法表达稳定命题时才成立。

若删除不改变能力、决策或审计性，明确“不接入”。零组件或只保留一个都是合法结果；数量不是指标。

### 划分 AI 与确定性边界

为每个设计项写一行“能力分工”：

- **确定性实现**：JSON/Markdown 结构、路径范围、哈希、存在性、超时、结果枚举、事件完整性等可机械复现的边界。
- **AI/自然语言判断**：业务语义、质量充分性、相关性、风险解释、冲突处理、下一步规划。输出必须带理由、证据锚点、置信度与 `uncertain/unchecked` 路径。
- **混合实现**：脚本只收集/规范化事实，AI 按 `VERIFIER.md` 的命题和 Evidence Contract 判断；脚本不得偷偷编码领域结论。

对“硬编码规则”逐条追问：规则是否稳定、跨模型可复现、能安全地 fail-closed？若不是，把它改成自然语言契约、证据字段和人工复核条件，而不是新增阈值或关键词表。

语义 Verifier 的计划至少定义 `subject`、`context`、`evidence`、`verdict`、`summary`、`evidence_refs`、`confidence` 和 `uncertainties`；`verdict` 只能使用 Kernel 支持的枚举。证据不足或网络不可观测时返回 `uncertain`/`unchecked`，不得把模型自评当作 `pass`。

### 映射到 bensz-skill-kernel

计划必须说明：

- Verifier 使用 `owner.domain.capability` canonical ID；State 使用 `owner.machine.state` canonical ID；版本和 alias 独立维护，不把 Skill 名、模型、实现或 Gate 策略塞进 ID。
- 每个 Pack 的 `VERIFIER.md`/`STATE.md` 负责判断目标、入口条件、不变量、证据边界和转移；`index.json` 是元数据单一来源。入口脚本只通过 JSON-stdio 工作，路径必须留在 Pack 目录内。
- Kernel 只负责发现、协议校验、超时/资源边界、结果归一化、Gate、事件记录和状态持久化；领域判断留在 Skill 的契约或 AI 适配器。
- 明确 `required` 与 `advisory`、Gate 放行条件、`uncertain/unchecked` 的人工复核去向、`run_id`/`attempt_id` 绑定、失败和恢复策略，以及如何从事件重放。
- 若没有 Verifier，Gate 应明确为“不适用/无需验证”，而不是伪造通过结果；若没有 State，说明由普通 Skill 流程和工作区生命周期承担边界。若接入组件，写清 required 缺失时 fail-closed、advisory 如何提示但不阻塞。
- 状态图只保留对业务有意义的稳定节点；动作放在 transition/event/helper 名称中。系统工作区状态与 Skill 领域状态分层，不把领域状态硬编码进 Kernel reducer。
- 对外部路径、网络、子进程和大输入给出最小权限、超时、体积上限和越界拒绝策略；入口脚本必须是 Pack 内相对路径，禁止 `..`、绝对路径和 symlink 逃逸。

### 生成最小设计

用一张矩阵让后续 Agent 能直接实现：

| 候选 | 保留/删除 | 稳定命题或状态含义 | AI/脚本分工 | 输入与证据 | Gate/转移 | 失败与人工复核 |
| --- | --- | --- | --- | --- | --- | --- |

然后给出最小状态图（初始、主要阶段、终止/失败、可选回退）和 Verifier 清单。每项都必须有“为什么不可删除”的一句话；没有这句话就删掉或降级为普通说明。

## 计划文件固定结构

```markdown
# Verifier/State 设计计划：<skill>
## 结论摘要
## 业务流程与风险地图
## 删除影响测试（含“不接入”结论）
## Verifier 设计矩阵
## State 设计矩阵与最小状态图
## AI/确定性分工与 Evidence Contract
## Kernel 对接、Gate、重放与资源边界
## 实施顺序（P0/P1/P2）
## 验收与回归测试
## 已知不确定性、回退方案和不在范围内的事项
```

实施顺序只写下一步可执行的改动，不直接修改源代码。P0 是安全、数据完整性或不可恢复错误；P1 是重要契约/可观测性问题；P2 是可选改进。每一项包含文件位置、证据、影响、验证命令和完成条件。

## 质量闸门

交付前自问：

- 是否存在“删掉也不影响能力”的 Verifier/State？若有，删除或解释保留理由。
- 是否把业务规则硬编码进 Kernel、脚本阈值或 ID？若有，迁移到自然语言契约或证据适配器。
- 是否区分事实收集与语义判断，并为不确定结果保留人工复核？
- 是否能用内置 Pack 表达，是否真的需要专用 Pack？
- 是否能从事件和快照重放，且失败不会伪装成通过？
- 是否有最小测试覆盖 canonical/alias、非法输入、超时、越界路径、Gate 缺证据和删除后的回退？
- 计划是否包含目标 Skill/Kernel 版本、读取证据、决策日期和可追溯的实现文件位置？

若资料不足，停止在“待确认”并写缺口，不凭空补状态或规则。中间分析、快照和验证日志遵循 BenszAPI 工作区协议，不记录密钥、令牌、Cookie、私有 Prompt 或不必要的原始数据。

若本 Skill 作为更大任务的中间环节，只交付计划和机器可读摘要，不重复向用户解释；若它是独立任务，在结束时用通俗语言说明保留/删除了什么、为什么、下一步如何实现，并列出计划路径和验证证据。

## 与 bensz-collect-bugs 的边界

仅当发现本 Skill 或 Bensz 基础设施的设计缺陷（例如触发漏判、契约不完整、环境假设错误）时记录 bug；用户数据错误、第三方抖动、用户主动改源码和偶发模型波动不属于此范围。先脱敏记录到 `~/.bensz-skills/bugs/`，本轮不中断；只有用户明确要求才用本机 `gh api` 公开上报。禁止直接修改用户本地已安装 Skill 来“顺手修 bug”。
