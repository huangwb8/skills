# Prompt Programming

这个 skill 用来把普通 prompt 翻译成一种“像程序、但仍然是人类自然语言”的表达形式。它不是简单润色，而是把目标、输入、约束、流程、分支和校验重组成统一的 Prompt Program，适合做假代码、研究式方法描述和可维护的提示词骨架。

## 用法

### 最推荐用法

```text
请使用 prompt-programming skill，把下面这段 prompt 翻译成具有可编程架构的人类自然语言。
输入：原始 prompt 文本
输出：等价的 Prompt Program
```

### 进阶用法

```text
请使用 prompt-programming skill，把下面这段 prompt 翻译成具有可编程架构的人类自然语言。
输入：原始 prompt 文本
输出：等价的 Prompt Program
另外，还有下列参数约束：
- 输出语言：中文
- 风格：极简、像研究论文里的 fake code
- 必须显式写出条件分支和校验步骤
```

## 能做什么

- 把散乱、口语化或冗长的 prompt 重构成统一结构。
- 为 prompt 补出隐含的输入、输出、控制流和验收逻辑。
- 用极少的底层语义原子表达复杂任务。
- 让 prompt 更适合评审、迭代、复用和组合。
- 保持自然语言可读性，而不是退化成真实代码语法。

## 核心设计

这个 skill 的底层不是“无限标签”，而是 6 个统一原子：

| 原子 | 作用 |
|------|------|
| `Entity` | 定义对象、角色、工具、状态 |
| `Intent` | 定义目标和产出 |
| `Operation` | 定义动作链 |
| `Constraint` | 定义必须项、禁止项和偏好 |
| `Control` | 定义分支、循环、回退和优先级 |
| `Check` | 定义校验、异常处理和结束条件 |

它会把这些原子渲染成固定块顺序的 Prompt Program：

`程序 → 目标 → 输入 → 输出 → 定义 → 约束 → 流程 → 校验 → 缺口处理 → 返回`

其中 `程序`、`定义`、`缺口处理` 默认是可选块；当这些信息为空时会直接省略，不会为了形式完整而硬塞空标题。

## 关键语义

- `输出`：定义目标产物、目标格式或目标效果。
- `返回`：定义如何交付上述输出；它不能偷偷引入新的产物。
- 如果用户显式写了 JSON 字段、表格列、章节顺序或步骤顺序，skill 默认按原契约保留。

## 输入要求

- 你需要提供一段原始 prompt。
- 如果输入为空、过短，或者本质上不是 prompt / 指令，skill 会先提示不适用，而不是编出一个假结构。

## 使用示例

### 示例 1：把普通任务 prompt 变成假代码

```text
请使用 prompt-programming skill。
输入：帮我读一批访谈记录，提炼主题，输出一个结构化总结，如果证据不足要标出来。
输出：等价的 Prompt Program
```

### 示例 2：把代码生成 prompt 重构成可编程自然语言

```text
请使用 prompt-programming skill。
输入：给我写一个 Python 脚本，把多个 CSV 合并，去重，记录异常行，最后输出报告。
输出：等价的 Prompt Program
另外，还有下列参数约束：
- 必须显式写出异常处理
- 不要使用真正的代码语法
```

### 示例 3：把复杂分析 prompt 变成研究式方法描述

```text
请使用 prompt-programming skill。
输入：分析一组论文摘要，按研究主题分组，比较方法差异，最后给出趋势和空白点。
输出：等价的 Prompt Program
另外，还有下列参数约束：
- 风格像论文里的方法假代码
- 尽量短，但逻辑要完整
```

## 输出

- 默认只输出最终的 Prompt Program。
- `程序`、`定义`、`缺口处理` 这些可选块只有在确实有信息时才会出现。
- 输出里通常会包含：
  - `目标`
  - `输入`
  - `输出`
  - `约束`
  - `流程`
  - `校验`
  - `缺口处理`
  - `返回`
- 如果原 prompt 存在高风险歧义，skill 会在 `缺口处理` 中显式暴露，而不是偷偷猜测。

## 配置

- 配置文件：`prompt-programming/config.yaml`
- 默认方言名：`Prompt Program`
- 默认输出语言：`zh-CN`
- 默认输出模式：`final_only`
- 默认会省略空块：`omit_empty_blocks = true`
- 显式格式契约默认强保留：`preserve_output_contract = true`
- 顺序约束默认强保留：`preserve_sequence_constraints = true`
- 控制流默认保守推断：`control_inference_policy = only_when_explicit_or_strongly_implied`
- 输入最小长度：`input_validation.min_length = 6`
- 固定块顺序：
  - `program`
  - `goal`
  - `input`
  - `output`
  - `definition`
  - `constraint`
  - `flow`
  - `validation`
  - `gap_handling`
  - `return`

## 参考文档

- `references/primitives.md`：底层原子、块语义与省略规则
- `references/examples.md`：典型翻译示例
- `references/translation-rules.md`：输入验证、控制流推断、冲突处理与保真规则

## 常见问题

### Q：它和普通的“优化 prompt”有什么区别？

A：普通优化更关注清晰度和可执行性；`prompt-programming` 进一步把 prompt 变成一种可审阅、可维护、可组合的程序化自然语言。

### Q：输出会不会太像代码，反而不自然？

A：不会。它追求的是“假代码感”，不是编程语言语法。句子仍然是自然语言，只是逻辑结构更像程序。

### Q：如果原 prompt 很乱、还缺信息怎么办？

A：skill 会先恢复最核心的任务逻辑；低风险缺口会直接补足，高风险缺口会在 `缺口处理` 中显式标出来。

### Q：它适合拿来写系统 prompt 吗？

A：适合做系统 prompt 的逻辑骨架，尤其适合先把结构搭清，再决定是否继续扩写成平台专用格式。

### Q：为什么有时看不到 `程序`、`定义` 或 `缺口处理`？

A：因为这些是可选块。没有额外价值时，skill 会省略它们，让输出保持紧凑，而不是为了模板完整性制造空结构。

### Q：什么时候不适合用它？

A：当你只想润色语气、不想改变结构，或者你给的根本不是 prompt / 指令，而是别的材料时，就不适合直接用这个 skill。

## WHICHMODEL - 模型选择最佳实践

### 披露信息

- **最后更新**：2026-04-11
- **覆盖厂商**：OpenAI、Anthropic
- **来源构成**：官方文档 100%
- **数据时效**：截至 2026-04-11 的公开官方资料
- **局限性**：这里聚焦“把 prompt 翻译为程序化自然语言”的任务，不覆盖超长上下文批处理或复杂多工具自动化链路

### 场景 1：标准 Prompt Program 翻译

| 项目 | 建议 |
|------|------|
| **推荐模型** | GPT-5.4 或 Claude Sonnet 4.6 |
| **推理强度** | medium |
| **适用任务** | 常规 prompt 重构、逻辑补全、结构统一 |

**理由**：
- 这类任务需要稳定的结构化改写和中等强度推理，不需要最高成本模型。
- OpenAI 官方模型总览当前明确建议：复杂推理与编码先从 `gpt-5.4` 开始。
- Anthropic 官方模型总览把 `Claude Sonnet 4.6` 定位为速度与智能的最佳平衡。

### 场景 2：高歧义、高压缩、高抽象 prompt

| 项目 | 建议 |
|------|------|
| **推荐模型** | GPT-5.4 high / xhigh 或 Claude Opus 4.6 |
| **推理强度** | high |
| **适用任务** | 原 prompt 混乱、隐含约束多、需要重建深层逻辑 |

**理由**：
- 当任务不是“改写”，而是“先理解再重建”时，更强的推理模型更稳定。
- OpenAI 把 `gpt-5.4` 放在 agentic、coding 和 professional workflows 的最高档位。
- Anthropic 明确建议最复杂任务优先从 `Claude Opus 4.6` 开始。

### 场景 3：轻量批量转换或快速预处理

| 项目 | 建议 |
|------|------|
| **推荐模型** | GPT-5.4 mini / nano 或 Claude Haiku 4.5 |
| **推理强度** | low / medium |
| **适用任务** | 大量简单 prompt 的初步结构化、快速筛查、草稿生成 |

**理由**：
- 如果原 prompt 逻辑简单，重点只是统一成固定方言，小模型的速度和成本优势更明显。
- OpenAI 官方把 `gpt-5.4-mini`、`gpt-5.4-nano` 定位为低延迟、低成本工作负载。
- Anthropic 官方把 `Claude Haiku 4.5` 定位为最快档。

### 通用原则

1. 默认先用中档模型，把它当成 `prompt-programming` 的基线档位。
2. 只有在“原 prompt 本身不成形”时，才升级到更强推理档。
3. 如果你要做的是批量规范化，而不是高质量重建，优先考虑小模型。
4. 对这类任务而言，提示结构设计通常比一味升级模型更重要。

### 参考来源

- OpenAI Models：<https://developers.openai.com/api/docs/models>
- OpenAI Model Selection Guide：<https://developers.openai.com/api/docs/guides/model-selection>
- Anthropic Models Overview：<https://platform.claude.com/docs/en/about-claude/models/overview>
- 这些模型版本变化较快；如果你在 2026-04-11 之后阅读本 README，建议重新核对官方文档。

## 运行时状态与结构验证

技能运行阶段由 [`references/state-machine.md`](references/state-machine.md) 定义，状态
从输入就绪、翻译、验证、通过到交付依次推进。每次执行同时使用两个 Verifier：
`bensz.prompt.contract-conformance@1.0.0` 负责结构门禁，
`bensz.prompt.semantic-equivalence@1.0.0` 按
[`references/verifiers/semantic-equivalence/PROMPT.md`](references/verifiers/semantic-equivalence/PROMPT.md)
由当前 AI 评估意图、契约、控制流和约束保真。两者结果必须批量交给 Kernel 重算 Gate；只有
两个结果均为 `completed + pass` 且 Gate 允许，才能返回最终 Prompt Program。模型不可用、
证据不足或语义不确定时不得静默降级。
