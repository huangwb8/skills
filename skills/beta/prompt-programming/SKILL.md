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

## 目标

当用户明确要求“把 prompt 改写成伪代码”“将提示词翻译成可编程自然语言”“输出具有程序结构的人类语言指令”或直接提到 prompt-programming 时使用。将用户原始 prompt 翻译为一种简洁、严谨、可组合的 Prompt Program 方言：形式上像假代码，语义上仍是人类自然语言。

## 流程

### 输入

#### 适用与不适用

适用：

- 把普通 prompt 变成研究论文式假代码
- 把散乱任务说明重构成统一结构
- 把长 prompt 压缩成可组合、可讨论、可评审的逻辑骨架

不适用：

- 用户只想润色语气，不想改变表达结构
- 用户只想执行任务，不关心 prompt 的架构
- 原始输入不是 prompt，而是完整代码实现请求

### 执行步骤

#### 核心模型

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

#### 渲染方言

- 块顺序、必需块、可选块、块语义与句式模板，以 `config.yaml:rendering.*` 为准。
- 必守规则：
  - `输出` 只定义目标产物、目标格式或目标效果。
  - `返回` 只定义对 `输出` 的交付动作，不能引入新产物。
  - `程序`、`定义`、`缺口处理` 属于可选块；为空就省略。
  - 若 `config.yaml:rendering.omit_empty_blocks=true`，禁止为了“看起来完整”补空块。

#### 工作流

##### 输入验证

先按 `config.yaml:translation.input_validation` 检查输入：

- 空输入：拒绝翻译，并要求提供原始 prompt。
- 过短输入：说明信息不足，不输出伪完整结构。
- 非 prompt 型输入：说明本 skill 不适用。

##### 理解原始 prompt

恢复以下信息：

- 真实目标与交付物
- 输入对象与隐含上下文
- 输出契约与验收口径
- 强约束与软偏好
- 控制逻辑：条件、分支、迭代、失败回退

##### 映射为 6 个原子

- `Entity`：关键对象是什么
- `Intent`：最终要得到什么
- `Operation`：核心动作链是什么
- `Constraint`：哪些条件不能丢
- `Control`：是否存在 if / for each / until / fallback
- `Check`：如何判断结果合格

若原 prompt 混乱，先重建逻辑，再翻译；不要保留混乱结构。若没有显式控制逻辑，只能在“显式或强隐含”时补出最小控制结构，不凭空发明分支或循环。

##### 组织为 Prompt Program

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

##### 压缩表达

- 保留逻辑，不保留冗余修辞。
- 保留可执行约束，不保留客套表达。
- 能通过结构表达的，不重复解释。
- 句子预算以 `config.yaml:quality_bar.soft_sentence_budget` 为软上限；复杂任务可放宽，但不能丢逻辑。

##### 最小自检

输出前确认：

- 仍然等价于原 prompt 的真实意图
- 具备清晰的输入、输出、流程和校验
- 关键分支与缺口处理已显式表达
- 足够像“程序”，但仍是自然语言

#### 额外规则

##### 歧义处理

- 可用常识低风险补足时，直接补足并体现在结构中。
- 缺失信息会改变任务本质时，在 `缺口处理` 中显式标注，不擅自虚构。
- 默认不要频繁追问；只有任务语义无法成立时才要求澄清。

##### 风格处理

- 默认保持冷静、简洁、结构化。
- 不输出“你应该”“建议你”等评注性口吻，除非原 prompt 本身包含它们。
- 允许保留领域词汇，但要消除口语化噪音。

##### 等价性原则

- 允许重排表达，不允许改变目标。
- 允许补出隐式流程，不允许新增无依据能力。
- 允许强化校验，不允许削弱关键约束。
- 允许压缩表述，不允许丢失显式格式契约。
- 允许补足交付动作，不允许把“输出”偷换成“输出说明书”。

#### 参考资料

- `references/primitives.md`：6 个原子、块语义与省略规则
- `references/examples.md`：典型翻译示例
- `references/translation-rules.md`：输入验证、保真与冲突规则

### 输出

#### 输出

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

### 输出管理

#### BenszAPI 任务工作区


### 校验

#### 质量标准

合格的 Prompt Program 必须满足：

- **等价**：核心意图不丢失
- **可执行**：读者可按结构直接执行
- **可编程**：能看见输入、约束、流程、分支、校验
- **可扩展**：后续要求能继续挂到对应块
- **可审阅**：他人能快速指出逻辑缺口或冗余

### 失败与恢复

#### 输入缺口与翻译失败

- 空输入或低于 `config.yaml:translation.input_validation.min_length` 时拒绝翻译，并要求补充原始 prompt；非 prompt 型输入直接说明本 Skill 不适用。
- 缺失信息若会改变任务本质，放入“缺口处理”并要求澄清，不擅自虚构实体、分支、循环或输出格式；低风险且强隐含的信息才可按规则补足。
- 出现冲突时按“核心意图 → 硬约束 → 输出契约 → 校验要求 → 风格偏好”处理，并保留未解决冲突的显式标记。
- 若无法生成满足必需块和等价性要求的 Prompt Program，说明具体缺口并返回可恢复的补充要求，不输出伪完整结构，也不把翻译任务改成执行原 prompt。


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
