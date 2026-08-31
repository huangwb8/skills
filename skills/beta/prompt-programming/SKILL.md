---
name: prompt-programming
description: 当用户明确要求“把 prompt 改写成伪代码”“将提示词翻译成可编程自然语言”“输出具有程序结构的人类语言指令”或直接提到 prompt-programming 时使用。将用户原始 prompt 翻译为一种简洁、严谨、可组合的 Prompt Program 方言：形式上像假代码，语义上仍是人类自然语言。
metadata:
  author: Bensz Conan
  short-description: 把任意 prompt 编译成具有程序结构的人类自然语言
  keywords:
    - prompt-programming
    - programmable natural language
    - pseudo code prompt
    - prompt compiler
    - 提示词编程
    - 假代码
---

# Prompt Programming

## BenszAPI 任务工作区

本 Skill 的新任务中间文件统一写入 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/{skill名}/input|output|log/`。同一任务复用一个任务根目录；多 Skill 协作才创建 `shared/`。正式交付物不写入该目录，历史隐藏目录只允许显式兼容读取、迁移或清理。

## 强制运行时门禁：状态机与验证器

这是本 Skill 的**必经执行协议**，不是建议项。凡是输入请求（包括最后判定为不适用或失败的请求）都必须先进入 Kernel 管理的状态流程；任何“只生成草稿”“跳过验证器”“手工判断后直接返回”都属于未完成执行，禁止交付结果。

### 固定生命周期

1. 复用或初始化任务工作区，并为本次尝试确定同一 `run_id`、`attempt_id` 和事件账本路径。
2. 通过 `bsk state transition` 进入 `bensz.prompt-programming.draft`，记录原始 prompt（只读）。输入为空、过短或非 prompt 时，记录失败路径并停止，不得伪造 Prompt Program。
3. 完成翻译后，**必须**运行 `bensz.prompt.contract-conformance@1.0.0`，并按 [`references/verifiers/semantic-equivalence/PROMPT.md`](references/verifiers/semantic-equivalence/PROMPT.md) 由当前 AI 执行 `bensz.prompt.semantic-equivalence@1.0.0`。前者检查结构，后者检查原始 prompt 与候选 Program 的语义保真；两者请求和结果分别保存到 Skill 工作区 `input/`、`output/`，不得把结果留在对话上下文中作为唯一证据。
4. 将两个 Verifier 结果作为同一批次交给 `bsk verification`；Gate 必须由 Kernel 重算，并与本次 `run_id`/`attempt_id` 绑定。只有两个 required Verifier 都是 `completed + pass` 且 Gate 为允许时，才可转移到 `bensz.prompt-programming.reviewed`。AI 不可用、超时或语义不确定时必须停在人工复核/失败路径。
5. 在 `reviewed` 阶段执行语义复核：确认核心意图、硬约束、输出契约和显式顺序均保留。复核通过后依次转移到 `bensz.prompt-programming.published`，再关闭工作区；未通过则转移到 `bensz.runtime.failed`，保留诊断。

### 不可绕过的执行规则

- 状态转移、Verifier 结果、Gate 和最终交付必须由 `bensz-skill-kernel` 记录；不得手写 `meta-state.json`、伪造 `verification.*` 事件或仅在 Markdown 中声称“已验证”。
- Verifier 执行错误、超时、`fail`、`uncertain`、`unchecked` 或缺少 Gate 时，必须停在检查/失败路径，不能进入 `reviewed`、`published` 或返回最终结果。
- 必须使用上述 canonical Verifier ID 与版本；不能以其它通用检查器替代，也不能因为任务简单而省略。
- 详细状态定义、命令参数和证据字段见 [`references/state-machine.md`](references/state-machine.md) 与 [`references/verifiers.md`](references/verifiers.md)。若命令不可用，保留失败证据并停止，不得静默降级。

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求“report bensz skills bugs”等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

## 语义验证要求

`bensz.prompt.semantic-equivalence@1.0.0` 是 AI 评审器，不是自动改写器。当前
Agent 必须把原始 prompt 和候选 Prompt Program 提交给 `PROMPT.md` 规定的六项评分表，
输出带来源/候选锚点、严重级别和置信度的标准 JSON。不得用“块存在”“文件可读”或模型
一句话自评替代逐项判断；语义验证结果必须与结构验证结果批量写入同一 Kernel Gate。

把原始 prompt 编译成 Prompt Program：像程序，但仍是自然语言。目标是把输入、输出、约束、流程、分支和校验整理成可维护、可评审的假代码。

## 核心模型

- 单一真相来源是 `config.yaml`。
- 底层只使用 `config.yaml:kernel.semantic_atoms` 定义的 6 个原子：
  - `Entity`：对象、角色、输入、输出、工具、状态
  - `Intent`：目标、交付物、成功条件
  - `Operation`：分析、生成、转换、比较、总结、规划
  - `Constraint`：必须、禁止、偏好、格式、长度、风格
  - `Control`：条件、分支、循环、顺序、回退、优先级
  - `Check`：自检、验收、异常处理、结束条件
- 不新增原子；复杂任务靠组合表达。
- 详细定义与块映射见 `references/primitives.md`。

## 渲染方言

- 块顺序、必需块、可选块、块语义与句式模板，以 `config.yaml:rendering.*` 为准。
- 必守规则：
  - `输出` 只定义目标产物、目标格式或目标效果。
  - `返回` 只定义对 `输出` 的交付动作，不能引入新产物。
  - `程序`、`定义`、`缺口处理` 属于可选块；为空就省略。
  - 若 `config.yaml:rendering.omit_empty_blocks=true`，禁止为了“看起来完整”补空块。

## 工作流

### 输入验证

先按 `config.yaml:translation.input_validation` 检查输入：

- 空输入：拒绝翻译，并要求提供原始 prompt。
- 过短输入：说明信息不足，不输出伪完整结构。
- 非 prompt 型输入：说明本 skill 不适用。

### 理解原始 prompt

恢复以下信息：

- 真实目标与交付物
- 输入对象与隐含上下文
- 输出契约与验收口径
- 强约束与软偏好
- 控制逻辑：条件、分支、迭代、失败回退

### 映射为 6 个原子

- `Entity`：关键对象是什么
- `Intent`：最终要得到什么
- `Operation`：核心动作链是什么
- `Constraint`：哪些条件不能丢
- `Control`：是否存在 if / for each / until / fallback
- `Check`：如何判断结果合格

若原 prompt 混乱，先重建逻辑，再翻译；不要保留混乱结构。若没有显式控制逻辑，只能在“显式或强隐含”时补出最小控制结构，不凭空发明分支或循环。

### 组织为 Prompt Program

- 默认按 `config.yaml:rendering.block_order` 输出。
- 组织顺序：
  - 先边界，后执行
  - 先主流程，后异常路径
  - 先硬约束，后风格偏好
- 若用户原 prompt 缺少显式校验，必须补出最小可执行校验。
- 若存在显式格式契约，必须保留到 `输出` 或 `约束`。
- 若用户指定字段、章节或步骤顺序，默认按原顺序保留。
- 若存在关键术语、变量名或实体名，默认保留原词，不擅自改名。

冲突时严格遵循 `config.yaml:translation.conflict_resolution_order`：

1. 核心意图
2. 硬约束
3. 输出契约
4. 校验要求
5. 风格偏好

### 压缩表达

- 保留逻辑，不保留冗余修辞。
- 保留可执行约束，不保留客套表达。
- 能通过结构表达的，不重复解释。
- 句子预算以 `config.yaml:quality_bar.soft_sentence_budget` 为软上限；复杂任务可放宽，但不能丢逻辑。

### 最小自检

输出前确认：

- 仍然等价于原 prompt 的真实意图
- 具备清晰的输入、输出、流程和校验
- 关键分支与缺口处理已显式表达
- 足够像“程序”，但仍是自然语言

## 输出

- 默认只输出最终 Prompt Program，不附带长篇分析。
- 推荐格式可按 `config.yaml:rendering.block_order` 省略空块：

```text
程序：……

目标：……
输入：……
输出：……

定义：
- ……

约束：
- 必须……
- 优先……
- 不要……

流程：
1. ……
2. 若……，则……；否则……。
3. 对每个……，执行……。

校验：
- ……

缺口处理：
- 若信息不足，则……

返回：
- ……
```

## 适用与不适用

适用：

- 把普通 prompt 变成研究论文式假代码
- 把散乱任务说明重构成统一结构
- 把长 prompt 压缩成可组合、可讨论、可评审的逻辑骨架

不适用：

- 用户只想润色语气，不想改变表达结构
- 用户只想执行任务，不关心 prompt 的架构
- 原始输入不是 prompt，而是完整代码实现请求

## 额外规则

### 歧义处理

- 可用常识低风险补足时，直接补足并体现在结构中。
- 缺失信息会改变任务本质时，在 `缺口处理` 中显式标注，不擅自虚构。
- 默认不要频繁追问；只有任务语义无法成立时才要求澄清。

### 风格处理

- 默认保持冷静、简洁、结构化。
- 不输出“你应该”“建议你”等评注性口吻，除非原 prompt 本身包含它们。
- 允许保留领域词汇，但要消除口语化噪音。

### 等价性原则

- 允许重排表达，不允许改变目标。
- 允许补出隐式流程，不允许新增无依据能力。
- 允许强化校验，不允许削弱关键约束。
- 允许压缩表述，不允许丢失显式格式契约。
- 允许补足交付动作，不允许把“输出”偷换成“输出说明书”。

## 质量标准

合格的 Prompt Program 必须满足：

- **等价**：核心意图不丢失
- **可执行**：读者可按结构直接执行
- **可编程**：能看见输入、约束、流程、分支、校验
- **可扩展**：后续要求能继续挂到对应块
- **可审阅**：他人能快速指出逻辑缺口或冗余

## 参考资料

- `references/primitives.md`：6 个原子、块语义与省略规则
- `references/examples.md`：典型翻译示例
- `references/translation-rules.md`：输入验证、保真与冲突规则
