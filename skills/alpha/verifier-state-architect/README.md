# verifier-state-architect — 用户使用指南

本 README 面向使用者：如何触发并使用 `verifier-state-architect`。执行规范在 `SKILL.md`，可配置默认值在 `config.yaml`。

## 快速开始

### 推荐用法

```text
请使用 verifier-state-architect skill，为 skills/beta/my-skill 设计 verifier 和 state。
先判断是否真的需要接入；输出设计计划到默认 .bensz-api 工作区。
```

### 进阶用法

```text
请使用 verifier-state-architect skill，审查 skills/alpha/reporting 的现有状态机和验证器。
要求：优先复用 Kernel 内置 Pack；语义判断交给 AI；列出删除影响测试、Gate 和回退方案。
计划文件请保存到 docs/plans/reporting-verifier-state.md。
```

## 它解决什么问题？

这个 Skill 是架构顾问，不是“多装几个组件”的生成器。它会先读懂目标 Skill 的业务流程，再逐个回答：

- 删除这个 Verifier/State 后，能力、决策或审计是否真的变差？
- 哪些工作适合脚本做，哪些必须由 AI 依据自然语言和证据判断？
- 如何使用 `bensz-skill-kernel` 的 Pack、canonical ID、Evidence Contract、Gate 和可回放事件？
- Kernel 里是否已经有可直接复用或组合的 Verifier/State，避免重复造轮子？
- 当前需求是否暴露出跨多个领域、值得提炼进 Kernel 的元 Verifier/State？如果复用或提炼都不成立，也会分点说明证据、代价和原因。

因此，最终结果可能是接入多个组件，也可能是只保留一个，甚至明确“不需要 Verifier/State”。

## 工作方式

1. 阅读目标 Skill、配置、脚本、references 和现有运行声明。
2. 绘制业务目标、阶段、风险、证据和人工介入点。
3. 做删除影响测试，过滤形式主义组件。
4. 盘点 Kernel 现有索引与契约，逐项判断直接复用、组合、适配或不适用。
5. 评估可否提炼跨领域的元 Verifier/State，并把复用与提炼结论及分点理由写入独立计划章节。
6. 设计 Verifier/State 矩阵，划分 AI 与确定性边界。
7. 映射到 Kernel 的 Pack、ID、Gate、事件、重放和资源限制。
8. 输出最小状态图、验收测试和实施顺序。

它不会直接创建 `VERIFIER.md`、`STATE.md` 或修改 Kernel 源码；后续实现可依据计划继续进行。

## 输出文件

默认计划位于：

`.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/verifier-state-architect/output/design-plan.md`

若你指定了 `docs/plans/` 或其它路径，则按指定路径输出。计划通常包含业务风险地图、删除影响测试、Verifier/State 矩阵、AI/脚本分工、Kernel 对接、Kernel 复用与元组件提炼决策（含分点理由）、P0-P2 实施顺序和回归测试。

## 常见场景示例

### 新 Skill 尚未接入基础设施

```text
请分析 skills/beta/data-cleaner，给出是否需要 verifier/state 的最小设计。
如果内置 Pack 已足够，请不要设计专用组件。
```

### 审查过度设计

```text
请审查 skills/alpha/review-tool 的所有 verifier/state。
逐项做删除影响测试，找出只贴标签、重复检查或把业务规则硬编码进脚本的部分。
```

### 为实现团队交接

```text
请为 skills/beta/prompt-programming 规划 Kernel 对接方案。
输出 canonical ID、Evidence Contract、required/advisory Gate、uncertain 路径、状态转移和测试清单。
```

## 使用边界

- 只读分析目标 Skill；不会自动覆盖源文件。
- 不把领域判断硬编码进 Kernel；脚本只做协议、路径、哈希等可复现工作。
- 信息不足时会列出缺口和待确认项，不凭空发明状态。
- 中间材料遵循 `.bensz-api` 任务工作区协议，并自动避开密钥、令牌、Cookie、私有指令和隐私。

## WHICHMODEL：模型选择建议

### 推荐策略

| 场景 | 建议 | 原因 |
| --- | --- | --- |
| 首次理解复杂 Skill、做删除影响测试和架构取舍 | 当前可用的高推理模型 | 需要跨文件整合业务语义并质疑自身假设 |
| 将结论整理成矩阵、计划和验收清单 | 中高能力通用模型 | 结构化写作多，仍需保持契约精度 |
| 纯格式检查、链接检查、字段核对 | 轻量模型或确定性脚本 | 不应让模型承担机械校验 |

不要在文档中写死具体型号：模型能力和命名会变化。复杂度、上下文长度、证据量和是否需要联网应由调用方按当前平台选择；若语义判断不确定，应保留 `uncertain/unchecked` 并转人工复核，而不是换模型硬凑通过。

## FAQ

**一定要设计 Verifier 和 State 吗？** 不一定。删除影响测试是第一道门，零组件是合法且常见的结果。

**为什么不把所有规则写进脚本？** 脚本适合稳定、机械、可复现的边界；业务语义和质量判断需要 AI 读取自然语言契约与证据，否则容易变成僵硬的形式主义。

**计划能直接当实现规格吗？** 可以作为交接规格，但仍需实现阶段依据当前 Kernel 版本验证 ID、索引、入口和测试；本 Skill 本身不改实现。
