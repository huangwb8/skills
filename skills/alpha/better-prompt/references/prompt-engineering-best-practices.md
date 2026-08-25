# Prompt 工程最佳实践详解

本文档整理自 OpenAI 和 Anthropic 官方文档，提供详细的 Prompt 优化指南。

## 官方文档来源

- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Engineering Overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)

## 核心技术详解

### 1. 清晰直接（Be Clear and Direct）

**原则**：用最简洁的语言表达最明确的意图。

**检查清单**：
- [ ] 核心任务是否一句话能说清？
- [ ] 是否存在可能产生歧义的词汇？
- [ ] 指令是否足够具体？

**优化示例**：

| 原始 | 优化后 |
|------|--------|
| "帮我写点东西" | "请帮我写一封 200 字以内的商务邮件，主题是项目进度汇报" |
| "分析这个数据" | "请分析这份销售数据，重点关注：1）月度趋势；2）top 5 产品；3）异常值" |

### 2. 结构化组织（Use XML Tags / Markdown）

**原则**：使用结构化标记帮助模型理解内容边界和层级。

**推荐结构**：

```markdown
# Identity
[角色定义]

# Instructions
[核心指令]

## Sub-tasks（如需要）
[子任务分解]

# Examples
<example id="1">
<input>...</input>
<output>...</output>
</example>

# Context
<document name="reference">
[参考内容]
</document>
```

**XML 标签使用场景**：

| 场景 | 推荐标签 |
|------|---------|
| 示例 | `<example>`, `<input>`, `<output>` |
| 文档引用 | `<document>`, `<reference>` |
| 思考过程 | `<thinking>`, `<analysis>` |
| 约束条件 | `<constraints>`, `<rules>` |

### 3. Few-shot Learning（示例驱动）

**原则**：通过输入输出示例展示期望的模式。

**最佳实践**：
- 提供 2-5 个高质量示例
- 示例应覆盖典型场景和边界情况
- 输入输出格式保持一致

**示例模板**：

```xml
# Examples

<example id="1">
<input>
客户反馈：这款产品质量很好，但物流太慢了。
</input>
<output>
{"sentiment": "mixed", "aspects": {"quality": "positive", "logistics": "negative"}}
</output>
</example>

<example id="2">
<input>
客户反馈：非常满意，下次还会购买！
</input>
<output>
{"sentiment": "positive", "aspects": {"overall": "positive"}}
</output>
</example>
```

### 4. 角色定义（Give Claude a Role）

**原则**：为 AI 分配明确的角色和专业领域。

**有效角色定义示例**：

```markdown
# Identity

你是一位资深软件架构师，专注于分布式系统设计。你有 15 年的大规模系统开发经验，擅长：
- 微服务架构设计
- 高可用系统构建
- 性能优化和瓶颈分析

你的沟通风格是：简洁、技术性强、注重实际可行性。
```

### 5. 思考链（Chain of Thought）

**原则**：引导模型逐步思考复杂问题。

**触发方式**：

```markdown
# Instructions

请按以下步骤分析：
1. 首先，识别问题的核心要素
2. 然后，分析各要素之间的关系
3. 接着，评估可能的解决方案
4. 最后，给出推荐方案及理由

在给出最终答案前，请展示你的思考过程。
```

### 6. 约束条件（Constraints）

**原则**：明确边界，防止不期望的输出。

**约束类型**：

| 类型 | 示例 |
|------|------|
| **格式约束** | "输出必须是 JSON 格式" |
| **长度约束** | "回答不超过 100 字" |
| **内容约束** | "不要包含代码实现" |
| **风格约束** | "使用正式的商务语气" |
| **边界约束** | "只讨论技术层面，不涉及商业决策" |

## 模型类型适配

### GPT 模型优化策略

GPT 模型（如 gpt-4、gpt-3.5）需要精确指令：

```markdown
# Instructions

任务：将用户输入转换为结构化数据

步骤：
1. 读取用户输入
2. 识别关键实体（人名、地点、时间）
3. 提取关系
4. 输出 JSON 格式

输出格式：
{
  "entities": [...],
  "relations": [...]
}

规则：
- 如果信息不完整，用 null 填充
- 日期统一转换为 YYYY-MM-DD 格式
- 人名使用全称
```

### 推理模型优化策略

推理模型（如 o1、o3）只需高层指导：

```markdown
# Goal

分析用户的问题，找出最佳解决方案。

# Context
[背景信息]

# Success Criteria
- 方案可行且具体
- 考虑了边界情况
- 提供了清晰的执行步骤
```

## 场景专项指南

### 代码生成

```markdown
# Identity
你是一位精通 [语言] 的软件工程师。

# Instructions
请编写一个 [功能描述] 的 [语言] 函数。

## Requirements
- 使用 [框架/库]
- 遵循 [编码规范]
- 包含错误处理
- 添加类型注解

## Constraints
- 不使用第三方库（除非指定）
- 函数长度不超过 50 行
- 必须包含 docstring

# Examples
<example>
<input>实现一个去重函数</input>
<output>
```python
def unique(items: list) -> list:
    """返回列表中的唯一元素，保持原始顺序。"""
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))]
```
</output>
</example>
```

### 文本分析

```markdown
# Identity
你是一位文本分析专家，专注于情感分析和主题提取。

# Instructions
分析给定文本，输出：
1. 情感倾向（positive/negative/neutral）
2. 主要主题（top 3）
3. 关键词（top 5）

# Output Format
```json
{
  "sentiment": "...",
  "topics": ["...", "...", "..."],
  "keywords": ["...", "...", "...", "...", "..."]
}
```

# Examples
[提供 2-3 个示例]
```

### 创意写作

```markdown
# Identity
你是一位专业文案撰写人，擅长 [领域]。

# Instructions
撰写一篇 [类型] 文案。

## Style Guide
- 语调：[正式/轻松/专业/友好]
- 目标受众：[描述]
- 文案长度：[字数]

## Key Messages
- [要点 1]
- [要点 2]
- [要点 3]

## Constraints
- 避免使用 [禁止词汇/表达]
- 包含 [必要元素]
```

## 常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 输出格式不稳定 | 格式约束不明确 | 添加明确的输出格式模板和示例 |
| 回答偏离主题 | 任务定义模糊 | 重写 Identity 和 Instructions |
| 信息遗漏 | 上下文不完整 | 补充必要的背景信息 |
| 风格不一致 | 缺少风格约束 | 添加 Style Guide |
| 长度失控 | 缺少长度约束 | 添加明确的字数/行数限制 |

## 质量检查清单

在提交优化后的 prompt 前，确认：

- [ ] Identity 清晰定义了角色和专业领域
- [ ] Instructions 明确说明了任务和规则
- [ ] Examples 提供了足够的参考模式
- [ ] Context 包含了必要的背景信息
- [ ] Constraints 定义了清晰的边界
- [ ] Output Format 明确了期望的格式
- [ ] 整体结构清晰，易于理解
