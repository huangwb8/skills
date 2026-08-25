# GitHub Release 发布

智能分析项目历史变化，自动生成吸引人的 Release Notes 并发布到 GitHub。

## ✨ 特性

- 🤖 **智能分析**：AI 驱动的 commit 历史分析，自动提炼核心价值
- 📝 **专业模板**：生成简洁、有效、有煽动性的 Release Notes
- 🚀 **一键发布**：自动创建 GitHub Release，无需手动操作
- 🎯 **分类清晰**：自动分类新功能、Bug 修复、性能优化等
- 🌐 **联网验证**：与 GitHub API 集成，获取最新 release 信息

## 📋 使用场景

当你需要：
- 发布新版本到 GitHub
- 创建 GitHub Release 并生成 Release Notes
- 推送 tag 并自动创建 release
- 总结版本间的历史变化

## 🚀 快速开始

### 前置要求

1. **GitHub CLI**：需要安装并认证 `gh` CLI
   - 安装：`brew install gh`（macOS）或访问 https://cli.github.com
   - 认证：`gh auth login`

2. **Git 仓库**：项目必须是 Git 仓库，且有 GitHub remote

### 使用方式

在 Claude Code 中使用以下任一方式触发：

```
"帮我发布 v3.0.0 到 GitHub"
"创建一个 GitHub Release，tag 是 v2.5.0"
"发布当前项目到 GitHub，版本 v1.0.0"
"我要 release v4.0.0-beta.1"
```

技能会自动：
1. 确认项目路径和 tag
2. 获取最新 release 信息
3. 分析历史变化
4. 生成专业的 Release Notes
5. 发布到 GitHub

## 📖 使用示例

### 示例 1：首次发布

```
你：发布 v1.0.0 到 GitHub

技能：检测到这是首次发布，将创建项目第一个 Release。
[生成首次发布专用 Release Notes]
✅ Release 发布成功！
```

### 示例 2：常规版本发布

```
你：发布 v2.3.0

技能：将比较 v2.2.0 和 v2.3.0 之间的变化...
[分析 23 个 commits，生成分类 Release Notes]
✅ Release 发布成功！
```

### 示例 3：预发布版本

```
你：发布 v3.0.0-beta.1

技能：检测到这是预发布版本（beta），将标记为 prerelease。
[生成 Pre-release 专用 Release Notes]
✅ Release 发布成功！
```

### 示例 4：指定项目路径

```
你：为 /path/to/project 发布 v1.5.0

技能：正在处理 /path/to/project...
[在该项目下执行发布流程]
✅ Release 发布成功！
```

## 🎨 Release Notes 风格

生成的 Release Notes 具有以下特点：

### 结构清晰

```
🎉 版本号 - 吸引人的标题
一句话价值定位

🚀 核心亮点
• 亮点1
• 亮点2

✨ 主要更新（分类）
• 更新内容
• 更新内容

📋 完整变更日志
[链接]
```

### 语言风格

- **简洁有力**：每个要点不超过一行
- **价值导向**：强调"为什么"而非仅仅"是什么"
- **情感化表达**：使用"革命性"、"突破性"等词汇
- **数字量化**：用具体数字说明改进幅度
- **用户视角**：用用户能理解的语言

### 自动分类

| 类别 | 图标 | 关键词 |
|------|------|--------|
| 新功能 | ✨ | feat, feature, add, new |
| Bug 修复 | 🐛 | fix, bugfix, resolve |
| 性能优化 | ⚡ | perf, performance, optimize |
| 技术改进 | 🔧 | refactor, improve |
| 文档更新 | 📝 | docs, document, readme |
| 安全更新 | 🔐 | security, fix vulnerability |

## ⚙️ 配置选项

### 认证

通过 `gh auth login` 管理，无需手动配置 token。运行以下命令检查认证状态：

```bash
gh auth status
```

### Git Remote 格式支持

- HTTPS: `https://github.com/owner/repo.git`
- SSH: `git@github.com:owner/repo.git`

## 🛠️ 故障排查

### 问题：gh 未认证

**解决方案**：
```bash
gh auth login
```

### 问题：Tag 不存在

**解决方案**：先创建 tag
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 问题：权限不足

**解决方案**：运行 `gh auth status` 检查认证状态及仓库权限

### 问题：Release 已存在

**解决方案**：技能会询问是否覆盖，选择更新现有 release

## 📚 相关资源

- [SKILL.md](SKILL.md) - 技能核心逻辑
- [Release Notes 生成策略](references/release-notes-strategy.md)
- [Release Notes 模板示例](references/release-templates.md)
- [GitHub CLI 文档](https://cli.github.com/manual/gh_release_create)

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic, OpenAI（2/6 = 33%）
- **来源构成**：社区 70%, 官方 20%, 技术博客 10%
- **数据时效**：2024-10 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试 Release Notes 生成质量

---

### 场景化建议

#### 场景 1：标准版本发布（最常见）

**触发条件**：常规版本发布，需要生成 Release Notes

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 或 Sonnet 4.5 |
| **推理强度** | low-medium |
| **预期成本** | ~$0.005-0.05/次 |

**理由**：
- Release Notes 生成主要是文本处理和模式匹配任务
- Haiku 成本最低，适合简单版本发布
- Sonnet 在 commit 分类和内容整理上表现更好
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1ocpoye/haiku_45_better_than_sonnet/) 显示 Haiku 在简单任务中表现优异

**避免**：复杂大规模版本（100+ commits）建议用 Sonnet

**来源**：[Haiku System Card](https://www.anthropic.com/claude-haiku-4-5-system-card) + Reddit 社区讨论

---

#### 场景 2：大规模版本发布

**触发条件**：
- 大规模版本（100+ commits）
- 跨越多个功能模块
- 需要深度理解业务价值

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium |
| **预期成本** | ~$0.03-0.15/次 |

**理由**：
- Sonnet 在代码分析和内容整理上表现出色
- 更适合需要"中等复杂度理解"的场景
- [社区对比](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249) 显示 Sonnet 在复杂场景下的优势
- **大规模 commit 历史分析需要一定的推理能力**

**避免**：简单版本（<20 commits）不需要 Sonnet，用 Haiku 即可

**来源**：社区对比讨论 + 官方模型选择指南

---

#### 场景 3：首次发布

**触发条件**：
- 项目首次发布（v1.0.0）
- 需要生成完整的初始介绍
- 需要创造性撰写项目定位

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium |
| **预期成本** | ~$0.05-0.20/次 |

**理由**：
- 首次发布需要理解和总结整个项目
- 需要创造性撰写吸引人的标题和价值定位
- Sonnet 在内容组织和语言表达上更有优势
- **首次发布是项目的"第一印象"，值得投入更多资源**

**避免**：如果不是首次发布，优先使用 Haiku

**来源**：社区反馈 + 官方文档

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Haiku 4.5** | 小版本发布、常规版本 | 大规模版本、首次发布 | $ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Sonnet 4.5** | 大规模版本、首次发布 | 小版本（浪费） | $$$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Opus 4.5** | **不推荐** | 所有场景 | $$$$$ | ⭐⭐ | ⭐ |

**说明**：
- Haiku 覆盖 80% 的版本发布场景（小版本、常规版本）
- Sonnet 用于大规模版本（100+ commits）和首次发布
- Opus 对此任务**完全不必要**，成本过高且无性能提升

---

### 通用原则

1. **默认从 Haiku 开始**：80% 的版本发布任务 Haiku 足够，无需升级
2. **复杂度判断**：根据 commit 数量选择模型
   - <20 commits：Haiku
   - 20-100 commits：Haiku 或 Sonnet
   - >100 commits：Sonnet
   - 首次发布：Sonnet
3. **成本敏感**：版本发布是高频操作，Haiku 的成本优势明显
4. **速度优先**：Haiku 的 <1 秒响应时间明显优于 Sonnet 的 3-5 秒
5. **避免过度设计**：Release Notes 生成主要是模式匹配和文本整理，Haiku 完全胜任

---

### ⚠️ 争议点

#### Haiku vs Sonnet：Release Notes 生成真的可以用 Haiku 吗？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Haiku 足够** | Reddit 社区 | Release Notes 生成是简单任务，Haiku 在文本处理任务中表现稳定 |
| **Sonnet 更保险** | 部分开发者 | 担心 Haiku 在大规模版本分析时出错 |

**数据支持**：
- [某用户测试](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)：Haiku 在编码任务中匹配 Sonnet 能力，成本降低 80%
- [官方文档](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)：Haiku 专为"高吞吐量、低延迟"场景设计

**建议**：
- **默认使用 Haiku**：小版本和常规版本发布，Haiku 完全胜任
- **仅在以下情况升级 Sonnet**：
  - 大规模版本（>100 commits）
  - 首次发布（需要项目理解和创造性撰写）
  - 跨多个功能模块的复杂版本
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

---

## 🤝 贡献

欢迎反馈和改进建议！请提交 issue 或 PR。

## 📄 许可

MIT License
