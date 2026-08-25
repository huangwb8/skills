# Find Best Skill

本 README 面向**使用者**：如何触发并正确使用 `find-best-skill` skill。

执行指令与硬性规范在 [SKILL.md](SKILL.md)；默认参数在 [config.yaml](config.yaml)。

---

## 用法

### 最推荐 - 简单需求

```
我想找一个能做 TDD 的 skill
```

### 场景化变体

#### 结合需求解构（推荐用于复杂需求）

```
帮我找最适合的数据分析 skill，要求：支持 Python、有可视化功能、社区活跃
```

#### 对比替代方案

```
现在最好的 code review skills 有哪些？帮我对比一下
```

#### 发现专业领域技能

```
找一些做科学计算或材料模拟的 skills
```

---

## 功能概述

**find-best-skill** 是一个智能技能推荐助手，帮你从 GitHub 生态的 37,000+ Agent Skills 中找到最合适的工具。

### 核心价值

- **需求解构**：自动分析你的真实需求
- **社区调研**：搜索 GitHub、SkillsMP、Reddit 等平台
- **舆情分析**：综合社区评价和 AI 评价
- **客观推荐**：提供推荐理由 + 局限性分析

### 工作原理

```
你的需求 → 需求解构 → 多平台搜索 → 舆情分析 → 排序推荐
                    ↓
         (GitHub + SkillsMP + Reddit + awesome-claude-skills)
```

### 与其他技能的区别

| 技能 | 作用 | 配合使用 |
|------|------|----------|
| **get-review-theme** | 解构需求 | find-best-skill 会自动调用它 |
| **find-best-skill** | 推荐技能 | 使用后可直接安装推荐技能 |
| **awesome-code** | 协调多技能开发 | 找到技能后用它来执行开发 |

---

## 使用示例

### 示例 1：寻找测试工具（最简单）

**你**：找一个能做 TDD 的 skill

**find-best-skill** 输出（摘要）：

```markdown
基于您的需求 "测试驱动开发（TDD）"，我为您推荐以下 skills：

## 1. test-driven-development

**GitHub**: [obra/test-driven-development](https://github.com/VoltAgent/awesome-claude-skills)

### 推荐理由

**社区评价**：
- ⭐ 1.2k+ | 🍴 150+ | 📅 2周前更新
- 被多个团队采用，社区活跃讨论

**AI 评价**：
- 强制 Red-Green-Refactor 循环，确保 TDD 严格执行
- 支持多种测试框架
- 渐进式加载设计，性能优秀

### 局限性

- 对测试框架有预设（可能不支持您使用的框架）
- 初次使用需要适应其严格的流程要求

## 2. tdd-workflow

**GitHub**: [anthropics/tdd-workflow](https://github.com/anthropics/skills)

### 推荐理由

**社区评价**：
- ⭐ 官方维护 | 📅 持续更新
- Anthropic 官方最佳实践

**AI 评价**：
- 与 Claude Code 深度集成
- 简洁的工作流设计
- 灵活的测试适配

### 局限性

- 功能相对基础，高级特性较少
- 专注于 Claude Code 生态

[... 继续推荐 3-8 个 skills]
```

---

### 示例 2：寻找复杂功能技能

**你**：找一个能做 Git commit 信息自动生成的 skill，最好支持 Conventional Commits

**find-best-skill** 会：
1. 解构需求 → 关键词：`git`、`commit`、`conventional commits`
2. 搜索平台 → GitHub、SkillsMP、awesome-claude-skills
3. 分析舆情 → Stars、更新时间、社区讨论
4. 推荐输出 → `git-commit`（多个实现，按推荐度排序）

---

### 示例 3：对比同类技能

**你**：现在最好的 debugging skills 有哪些？帮我对比一下

**find-best-skill** 输出特点：
- 并列推荐多个调试技能
- 每个技能的适用场景说明
- 帮你选择最适合你工作流的

---

## 输出格式

每个推荐技能包含：

| 部分 | 内容 |
|------|------|
| **GitHub 链接** | 项目地址（可点击） |
| **推荐理由** | 社区评价 + AI 评价 |
| **局限性** | 潜在短板、适用场景限制 |
| **排序** | 按推荐度降序（最合适在前） |

---

## 配置选项

默认配置在 [config.yaml](config.yaml)，主要参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `recommendation.target_count` | 8 | 目标推荐数量 |
| `recommendation.default_min` | 5 | 默认最少推荐数量 |
| `recommendation.default_max` | 10 | 默认最多推荐数量 |
| `recommendation.absolute_min` | 3 | 绝对最少数量（找不到更多时） |
| `recommendation.absolute_max` | 20 | 绝对最多数量（避免信息过载） |
| `recommendation_criteria.min_stars` | 10 | 最少 Stars 数量 |
| `recommendation_criteria.max_age_months` | 12 | 最大未更新月数 |

如需自定义，可以在调用时说明：
- "只推荐前 3 个"
- "至少找 10 个"
- "只要最近 6 个月更新的"

---

## 备选用法（辅助脚本）

以下脚本主要用于**开发调试**，普通用户无需使用。

### 生成研究清单

```bash
# 为指定仓库生成研究检查清单
python scripts/get_skill_info.py "obra/test-driven-development,anthropics/skills"

# 输出结构化清单，包含需要收集的信息点
```

---

## 常见问题

### Q：推荐结果包含哪些平台？

A：主要从以下平台搜索：
- **GitHub**：开源项目主阵地
- **SkillsMP**：37,000+ 技能市场
- **awesome-claude-skills**：社区精选列表
- **Reddit**（/r/ClaudeCode）：真实用户讨论

### Q：如何保证推荐质量？

A：通过以下筛选标准：
- 必须有 GitHub 仓库
- 必须有有效的 SKILL.md 文件
- 优先推荐高 Stars（>100）
- 优先推荐最近更新（6个月内）
- 排除已归档仓库

### Q：推荐的数量为什么是 5-10 个？

A：这是经验值：
- **少于 3 个**：选择太少，可能错过好工具
- **多于 10 个**：信息过载，难以决策
- **5-8 个**：最佳平衡点（默认目标 8 个）

### Q：如果找不到合适的技能怎么办？

A：可能的原因：
- 需求太新，社区还没有相关技能
- 需求太偏，属于小众领域
- 关键词不够准确

建议：
- 尝试更通用的关键词
- 描述问题而非解决方案
- 考虑创建自定义技能

### Q：可以直接安装推荐的技能吗？

A：推荐报告包含 GitHub 链接，你可以：
1. 克隆仓库到 `~/.claude/skills/`
2. 使用 SkillsMP 的一键安装（如果支持）
3. 手动复制 SKILL.md 到本地

### Q：推荐结果会保存吗？

A：不会自动保存。如需保存，建议：
- 复制推荐报告到 Markdown 文件
- 保存推荐的 GitHub 链接到书签
- 使用 Claude Code 的会话历史功能

---

## 更多文档

- [SKILL.md](SKILL.md) — 完整的工作流和执行规范
- [config.yaml](config.yaml) — 可配置参数
- [references/agent-skills-research.md](references/agent-skills-research.md) — Agent Skills 生态调研
- [references/skillsmp-guide.md](references/skillsmp-guide.md) — SkillsMP 使用指南

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic（1/6 = 17%）
- **来源构成**：社区 70%, 官方 20%, 技术博客 10%
- **数据时效**：2024-10 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试技能推荐准确率

---

### 场景化建议

#### 场景 1：标准技能搜索（最常见）

**触发条件**：需要寻找特定功能的 Agent Skill

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium |
| **预期成本** | ~$0.02-0.10/次 |

**理由**：
- 技能搜索需要需求解构、多平台搜索、舆情分析和 AI 评价等多个步骤
- Sonnet 在多步骤任务协调中表现出色，能够理解需求并综合多源信息
- [社区对比](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249) 显示 Sonnet 在复杂场景下的优势
- **技能搜索需要平衡推理能力与效率，Sonnet 的性价比最高**

**避免**：简单搜索不需要 Opus，用 Sonnet 即可

**来源**：社区对比讨论 + 官方模型选择指南

---

#### 场景 2：复杂需求分析

**触发条件**：
- 需要深度理解复杂需求并解构主题
- 需要对比多个技能的优缺点
- 需要分析社区舆情和 AI 评价

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium-high |
| **预期成本** | ~$0.05-0.20/次 |

**理由**：
- Sonnet 在复杂分析任务中表现优异，能够理解需求的复杂性并生成准确的推荐
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/) 显示 Sonnet 在分析任务中与 Opus 质量相当
- **复杂需求分析需要较强的推理能力，Sonnet 足够胜任**

**避免**：极少需要 Opus，除非需求极其复杂

**来源**：Reddit 社区讨论 + 90 天对比测试

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Sonnet 4.5** | 所有技能搜索场景（95%） | 极端复杂的需求分析 | $$$$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Haiku 4.5** | 简单关键词搜索 | 复杂需求分析（理解不足） | $$ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Opus 4.5** | **不推荐** | 所有场景（浪费） | $$$$$ | ⭐⭐ | ⭐ |

**说明**：
- Sonnet 覆盖 95% 的技能搜索场景
- Haiku 仅用于简单关键词搜索（单一功能、无复杂分析）
- Opus 对此任务**完全不必要**，成本过高且无性能提升

---

### 通用原则

1. **默认从 Sonnet 开始**：95% 的技能搜索任务 Sonnet 足够，无需 Opus
2. **复杂度判断**：根据需求的复杂程度选择模型
   - 简单搜索（单一关键词）：Sonnet 或 Haiku
   - 标准搜索（多关键词、需要对比）：Sonnet
   - 复杂需求（需要深度解构和分析）：Sonnet（极少需要 Opus）
3. **质量优先**：技能推荐是"找到合适的工具"，不应只追求低成本而牺牲推荐质量
4. **多步骤任务需要推理**：需求解构 + 多平台搜索 + 舆情分析 + AI 评价，需要较强的推理能力
5. **Haiku 的局限性**：虽然 Haiku 速度快、成本低，但 [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1o856eb/tested_haiku_45_it-is-fast-but-cant-complete/) 显示它在完成复杂多步骤任务时可能遇到困难

---

### ⚠️ 争议点

#### Sonnet vs Haiku：技能搜索可以用 Haiku 吗？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Sonnet 更保险** | 社区多数意见 | 技能搜索需要理解需求并综合多源信息，Haiku 可能无法胜任 |
| **Haiku 足够** | 部分开发者 | 简单关键词搜索是简单任务，Haiku 完全胜任 |

**数据支持**：
- [某用户测试](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)：Haiku 在编码任务中匹配 Sonnet 能力，成本降低 80%
- [官方文档](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)：Haiku 专为"高吞吐量、低延迟"场景设计

**建议**：
- **默认使用 Sonnet**：技能搜索需要理解和综合能力，Sonnet 完全胜任
- **仅在以下情况使用 Haiku**：
  - 非常简单的关键词搜索（单一功能、无复杂分析）
  - 快速查找已知的技能名称
  - Sonnet 出现理解错误时（极少见）

---

### 更新记录

- 2026-01-25：首次调研，覆盖 Anthropic
- 建议：2026-07 重新调研（6 个月后）

---

### 来源链接

**官方文档**：
- [Claude Tool Use Documentation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Choosing the right model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)
- [Claude Haiku 4.5 System Card](https://www.anthropic.com/claude-haiku-4-5-system-card)

**社区讨论**：
- [Sonnet 4.5 vs Haiku 4.5 vs Opus 4.1](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249)
- [Claude Opus 4.5 is insane (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/)

**技术博客**：
- [Top Use Cases for Claude Haiku 4.5](https://chatlyai.app/blog/claude-haiku-4-5-use-cases)
- [Claude Haiku 4.5 matches Sonnet's coding skills at 80% less cost](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)
