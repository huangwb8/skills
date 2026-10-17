# humanization — 用户使用指南

本 README 面向使用者：如何触发 `humanization`。执行规范见 [`SKILL.md`](SKILL.md)，默认策略见 [`config.yaml`](config.yaml)。

## 旧名兼容

正式 Skill 仅保留 `humanization` 目录。自然语言请求可沿用旧名 `nsfc-humanization`；安装器也接受旧安装参数并解析为 `humanization`，不创建旧名目录：

```bash
python3 skills/alpha/install-bensz-skills/scripts/install.py --skill humanization
```

名称调整不扩展业务范围，仍用于 NSFC 标书润色。

## 快速开始

最小 Prompt：

```text
请使用 humanization skill 润色下面的 NSFC 标书段落。
输入：以下文本
输出：只返回润色后的文本；不新增信息，不改 LaTeX、数字、代码状态或安全边界。

[粘贴文本]
```

需要审查而不改写时：

```text
请使用 humanization skill 做 diagnosis_only 诊断。
请按词语、句法、段落、章节四层列出“保留/改写/合并/人工确认”，并给出受保护 token 与安全不变量对照。

[粘贴文本]
```

## 能处理什么

- 清理套话、伪对立、抽象功能标签、括号/分号堆砌和边界声明过重；对“定义 + 多个否定排除项”先恢复正向判断，只保留会改变解释的必要限定。
- 识别工程协议腔、规格书式字段串、无主语流程句、混合技术语域、术语漂移、跨章节重复和元评论。
- 先建立术语表与安全不变量，再改写；不能证明零损失时保留原句并标记人工确认。
- 诊断会区分“正文保留的限定”和“建议删除或合并的限定”；真实的科学二分（如关系保持与临床获益）仍需保留。
- 保持 LaTeX 命令、引用、数学、数字、单位、变量、代码状态、路径、URL、邮箱、DOI、注释和结构不变。

不适用：非 NSFC 内容、补写研究内容、事实核查或版式修改。

## 常用参数

| 参数 | 可选值 | 作用 |
| --- | --- | --- |
| `section_type` | `通用`、`立项依据`、`研究内容`、`研究基础`、`工作条件`、`风险应对`、`其他` | 决定章节职责检查 |
| `field` | `general`、`cs`、`engineering`、`medicine`、`life_science` | 提供领域语域提示 |
| `strength` | `minimal`、`moderate`、`aggressive` | 控制改写幅度，默认 `aggressive` |
| `output_mode` | `text_only`、`text_with_change_summary`、`diagnosis_only`、`text_with_change_summary_and_style_card` | 控制输出形式 |
| `self_eval_rounds` | `1` 或 `2` | 第 1 轮看自然度/职责，第 2 轮看安全/结构 |

## 场景示例

### LaTeX 混合文本

```text
请用 humanization 润色以下段落，保持所有 LaTeX 命令、引用 key、数学公式、数字和代码状态逐字不变；section_type=研究内容，output_mode=text_with_change_summary。

[粘贴文本]
```

### 工程术语较多

```text
请用 humanization 诊断工程协议腔和规格书式字段串。
专业术语可保留但需首次中文释义；请区分保留、改写、合并和人工确认，不要删除 manifest、状态码、阈值、分母或失败处理。

[粘贴文本]
```

### 跨章节检查

```text
请用 humanization 检查研究目标、研究内容和风险应对三段的术语漂移与重复规则。
先给“事实—首次定义—后续引用”表，再决定哪些句子只保留短引用；若无法判断是否为不同对象，标记人工确认。

[粘贴文本]
```

### 边界声明过重

```text
请用 humanization 压缩下面段落中的边界声明：先写出研究检验的正向判断，每段只保留一个会改变解释的必要限定；把其余同义的“不能证明/不等同于/仍需验证”列入诊断表的“建议删除或合并的限定”列。彼此独立且分别改变解释的边界要保留并标记人工确认。不得改动引用、LaTeX、数字、阈值、分母、暂停条件或临床外推边界。

[粘贴文本]
```

## 输出与参考

技能默认直接返回文本，不写项目文件。若选择诊断或变更摘要，输出还应包含术语表、章节去重决定、受保护 token diff 和安全不变量对照。匿名回归样例见 [`references/regression-cases.md`](references/regression-cases.md)，模式说明见 [`references/machine-patterns.md`](references/machine-patterns.md)。

## FAQ

**会改 LaTeX 或代码状态吗？** 不会；这些片段逐字保护，无法证明时回退。

**会删除所有英文技术词吗？** 不会。受控 token 保留；可解释术语首次给中文释义；临时造词才建议改写。

**会把研究内容补得更具体吗？** 不会。只使用原文已有动作和事实，不新增方法、指标、样本或临床落点。

**为什么还要人工确认？** 术语可能确实指向不同对象，或安全不变量、证据强度和外推范围无法从改写句中证明；如果原文只有排除性边界而没有明确的研究对象或动作，也不能强行改成“本项目检验什么”。此时保留原句比追求顺滑更安全。

## 变更记录

版本以 [`config.yaml`](config.yaml) 为准，变更详见 [`CHANGELOG.md`](CHANGELOG.md)。
