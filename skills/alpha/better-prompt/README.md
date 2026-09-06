# Better Prompt

这个 skill 用来把简陋、含糊或结构松散的 prompt 重构成更清晰、更可执行的高质量版本，或把它严格等价翻译成伪代码式的 Prompt Program；如果你只想做概念讨论，或者明确要求完全保留原风格，就不一定要用它。

它有两种输出模式：

- **standard（默认）**：增强导向。补全缺失的约束、示例和上下文，输出符合最佳实践的散文式结构。
- **prompt_program**：保真导向。不新增无依据能力，把 prompt 翻译成“形式像伪代码、语义是自然语言”的块结构（程序/目标/输入/输出/约束/流程/校验/返回）。

## 用法

### 最推荐用法（standard 模式）

```text
请使用 better-prompt skill 优化下面这段 prompt。
输入：原始 prompt 文本
输出：优化分析、优化后的高质量 prompt，以及必要的使用建议
```

### 进阶用法

```text
请使用 better-prompt skill 优化下面这段 prompt。
输入：原始 prompt 文本
输出：优化后的 prompt
另外，还有下列参数约束：
- 目标模型：reasoning
- 保留原始语气：是
- 必须补充示例：是
```

### 伪代码翻译用法（prompt_program 模式）

```text
请使用 better-prompt skill 把下面这段 prompt 翻译成 Prompt Program（伪代码式结构）。
输入：原始 prompt 文本
输出：最终 Prompt Program
```

只要在请求中出现“伪代码”“程序结构”“可编程自然语言”等表述，就会自动进入该模式；一次任务只会使用一种模式。

## 能做什么

- 优先优化清晰度、完整性和结构化表达。
- 在需要时补充约束条件、示例和上下文。
- 区分偏执行型的 GPT 风格 prompt 和偏复杂推理的 reasoning 风格 prompt。
- 默认同时给出分析、优化结果和使用建议。
- 把 prompt 严格等价翻译成 Prompt Program：保留原意和格式契约，显式化分支、循环与校验，压缩冗余修辞。
- 不适合已经非常成熟的 prompt，或超长到需要先拆分的信息包。

## 使用示例

### 示例 1：优化一个简单任务型 prompt

```text
请使用 better-prompt skill 优化下面的 prompt。
输入：帮我写一个脚本处理 CSV
输出：优化分析和优化后的 prompt
```

### 示例 2：优化代码生成 prompt

```text
请使用 better-prompt skill 优化下面的代码生成 prompt。
输入：给我写一个 Python 爬虫
输出：优化后的结构化 prompt
另外，还有下列参数约束：
- 目标模型：gpt
- 必须明确输入输出和错误处理
```

### 示例 3：优化复杂推理 prompt

```text
请使用 better-prompt skill 优化下面的 prompt。
输入：请帮我分析一个复杂商业决策问题
输出：优化分析、优化后的 prompt 和使用建议
另外，还有下列参数约束：
- 目标模型：reasoning
- 给高层目标，不要写过死的步骤
```

## 输出

- `优化分析`：说明原 prompt 的主要问题和改进点（standard 模式）。
- `优化后的 prompt`：可直接复制使用的结果（standard 模式）。
- `使用建议`：告诉你哪些内容可以按场景继续微调（standard 模式）。
- `Prompt Program`：伪代码式块结构结果，默认只输出结果本身、不带长篇分析（prompt_program 模式）。
- 默认不会替你执行 prompt 对应任务，它的职责是把 prompt 本身优化好。

## 配置

- 配置文件：`better-prompt/config.yaml`
- 默认目标模型类型：`gpt`
- 最小输入长度：`10`
- “已足够完善”的默认阈值：`8/10`
- 默认输出包含：
  - `analysis`
  - `evaluation`
  - `suggestions`

## 常见问题

### Q：优化后的 prompt 变长了，是不是越长越好？

A：不是。更长只是为了更清楚、更可执行。真正目标是信息充分且结构合理，不是单纯堆字数。

### Q：我还需要把优化后的 prompt 全部照搬吗？

A：不一定。你可以保留核心结构，再按自己的任务、语气和平台微调。

### Q：它会区分 GPT 模型和推理模型吗？

A：会。默认更偏 `gpt` 风格；如果任务更依赖开放式推理，可以显式要求 `reasoning` 风格。

### Q：什么时候不该用它？

A：当你的 prompt 已经很成熟、只是想做小改动，或者明确要求保留原始写法时，就不一定要用这个 skill。

### Q：standard 和 prompt_program 两种模式有什么区别？

A：standard 允许补全信息，目标是“更完整、更专业”；prompt_program 严格保真，目标是“结构像程序、语义不变”。想要让 AI 更好地执行任务，用 standard；想要审视和讨论 prompt 的逻辑骨架，用 prompt_program。
