## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic, OpenAI（2/6 = 33%）
- **来源构成**：社区 70%, 官方 20%, 技术博客 10%
- **数据时效**：2024-10 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试性能

---

### 场景化建议

#### 场景 1：单文件快速转换（最常见）

**触发条件**：转换单个图片格式，简单直接的任务

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 |
| **推理强度** | low |
| **预期成本** | ~$0.001-0.01/张 |

**理由**：
- Haiku 是 Anthropic 最快的模型，响应时间 < 1 秒
- 成本仅为 Sonnet 的 20%
- 对于简单工具调用任务，Haiku 的性能完全足够
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1ocpoye/haiku_45_better_than_sonnet/) 显示 Haiku 在简单脚本任务中表现优异

**避免**：无需升级，除非遇到复杂错误处理需求

**来源**：[Haiku System Card](https://www.anthropic.com/claude-haiku-4-5-system-card) + Reddit 社区讨论

---

#### 场景 2：批量文件夹转换

**触发条件**：批量处理大量图片（10+ 文件）

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 |
| **推理强度** | low |
| **预期成本** | ~$0.01-0.10/批 |

**理由**：
- Haiku 专为高吞吐量、低延迟任务优化
- 可在相同时间内执行近 2 倍于 Sonnet 的工具调用
- 批量任务中速度优势明显
- [社区验证](https://chatlyai.app/blog/claude-haiku-4-5-use-cases) 显示 Haiku 能"handle high-volume tasks without breaking the bank"

**避免**：无需升级，批量任务不需要复杂推理

**来源**：社区反馈 + 官方文档

---

#### 场景 3：复杂转换逻辑（特殊情况）

**触发条件**：
- 需要复杂的条件判断（如根据文件大小动态选择质量参数）
- 需要多步骤决策流程
- 需要与用户进行复杂对话确认参数

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium |
| **预期成本** | ~$0.05-0.20/任务 |

**理由**：
- Sonnet 在复杂推理和多文件任务中表现更好
- 更适合需要"中等复杂度决策"的场景
- [社区对比](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249) 显示 Sonnet 在复杂场景下的优势

**避免**：简单转换任务不需要 Sonnet，用 Haiku 即可

**来源**：社区对比讨论 + 官方模型选择指南

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Haiku 4.5** | 单文件转换、批量转换 | 复杂决策任务 | $ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Sonnet 4.5** | 复杂转换逻辑、多步骤决策 | 简单格式转换 | $$$ | ⭐⭐⭐ | ⭐⭐ |
| **Opus 4.5** | **不推荐** | 所有场景 | $$$$$ | ⭐ | ⭐ |

**说明**：
- Haiku 覆盖 95% 的图片格式转换场景
- Sonnet 仅在需要复杂决策时才值得使用
- Opus 对此任务**完全不必要**，成本过高且无性能提升

---

### 通用原则

1. **默认从 Haiku 开始**：95% 的图片转换任务 Haiku 足够，无需升级
2. **脚本驱动、AI 协调**：此 skill 的核心是 Python 脚本（Pillow），AI 只负责理解意图和调用脚本，无需强推理
3. **成本敏感**：批量处理时成本差异明显（Haiku 是 Sonnet 成本的 1/5）
4. **速度优先**：图片转换是低延迟任务，Haiku 的 <1 秒响应时间明显优于 Sonnet 的 3-5 秒
5. **避免过度设计**：简单任务用简单模型，Haiku 在工具调用任务中表现稳定

---

### ⚠️ 争议点

#### Haiku vs Sonnet：简单任务真的可以用 Haiku 吗？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Haiku 足够** | Reddit 社区 | Haiku 在简单工具调用任务中表现稳定，速度快且成本低 |
| **Sonnet 更保险** | 部分开发者 | 担心 Haiku 在边缘情况下出错，Sonnet 更可靠 |

**数据支持**：
- [某用户测试](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)：Haiku 在编码任务中匹配 Sonnet 能力，成本降低 80%
- [官方文档](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)：Haiku 专为"高吞吐量、低延迟"场景设计

**建议**：
- **默认使用 Haiku**：图片格式转换属于简单工具调用，Haiku 完全胜任
- **仅在以下情况升级 Sonnet**：
  - 需要复杂的条件判断逻辑
  - 需要与用户进行多轮对话确认复杂参数
  - Haiku 出现理解错误时（极少见）

---

### 更新记录

- 2026-01-25：首次调研，覆盖 Anthropic/OpenAI
- 建议：2026-07 重新调研（6 个月后）

---

### 来源链接

**官方文档**：
- [Claude Tool Use Documentation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Choosing the right model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)
- [Claude Haiku 4.5 System Card](https://www.anthropic.com/claude-haiku-4-5-system-card)

**社区讨论**：
- [Sonnet 4.5 vs Haiku 4.5 vs Opus 4.1](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249)
- [Haiku 4.5 better than Sonnet? (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1ocpoye/haiku_45_better_than_sonnet/)
- [Claude Haiku 4.5: Features, Testing Results, and Use Cases](https://www.datacamp.com/fr/blog/anthropic-claude-haiku-4-5)

**技术博客**：
- [Top Use Cases for Claude Haiku 4.5](https://chatlyai.app/blog/claude-haiku-4-5-use-cases)
- [Claude Haiku 4.5 matches Sonnet's coding skills at 80% less cost](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)
