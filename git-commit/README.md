# Git Commit — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `git-commit` skill。
执行指令与硬性规范在 [`SKILL.md`](SKILL.md)；默认参数在 [`config.yaml`](config.yaml)。

---

## 快速开始 🚀

### 最推荐用法（自动模式）

```bash
# 自动分析改动、暂存、拆分并提交（无需任何确认）
提交 Git 改动
```

### 结合 emoji 和签名

```bash
# 自动模式 + emoji + 签名
提交 Git 改动，使用 emoji，然后签名
```

### 需要审核每个步骤（审核模式）

```bash
# 在暂存、拆分、提交前暂停，等待你确认
提交 Git 改动，使用审核模式
```

---

## 工作模式 📖

本技能支持两种工作模式，满足不同场景需求：

| 模式 | 触发方式 | 适用场景 | 行为特征 |
|------|----------|----------|----------|
| **自动模式** | 默认（无参数） | 日常开发、快速提交 | AI 自主决策所有步骤，无需确认 |
| **审核模式** | `--review` 参数 | 重要提交、需要精细控制 | 在关键决策点暂停，等待确认 |

### 自动模式（默认）

**适用场景**：大多数日常提交

**行为特征**：
- 暂存区为空时，自动执行 `git add -A`
- 检测到大规模改动时，自动拆分为多个提交
- 直接执行提交，不询问确认

**设计理念**：commit 的顺利提交比内容本身更重要；如不满意可直接 `git reset` 回退。

### 审核模式

**适用场景**：重要发布、多人协作项目、需要精细控制提交内容

**行为特征**：
- 暂存区为空时，提示你选择暂存方式
- 检测到大规模改动时，给出拆分建议并询问是否接受
- 提交前显示生成的 commit message，询问是否确认

---

## 使用示例

### 示例 1：快速提交日常改动

**场景**：你刚完成一个小功能，想快速提交

```
你：提交 Git 改动

技能：[自动执行]
1. 检测到 3 个文件改动
2. 自动暂存所有文件
3. 生成 commit message：
   feat(auth): add OAuth2 login flow
   - implement Google and GitHub third-party login
   - add user authorization callback handling
4. 提交成功
```

### 示例 2：带 emoji 的风格化提交

**场景**：你想让 commit 历史更生动

```
你：提交 Git 改动，使用 emoji

技能：[自动执行]
✨ feat(ui): add user authentication flow

- implement login form with email and password fields
- add authentication state management hook

Closes #42
```

### 示例 3：审核模式 - 大规模改动拆分

**场景**：你修改了很多文件，想确保提交粒度合理

```
你：提交 Git 改动，使用审核模式

技能：[暂停并询问]
检测到 15 个文件、450 行改动，建议拆分为 3 个提交：

1. feat(ui): add login component (src/components/LoginForm.tsx)
2. fix(api): resolve token validation (src/api/auth.ts)
3. docs(auth): update authentication guide (docs/auth-guide.md)

是否接受此拆分方案？[Y/n]

你：Y

技能：[按顺序执行 3 个提交]
```

### 示例 4：跳过 Git 钩子

**场景**：本地有 lint 钩子，但你想先提交稍后修复

```
你：提交 Git 改动，跳过钩子检查

技能：[自动执行，跳过 --no-verify]
提交成功（已跳过本地钩子）
```

---

## 使用参数

### 模式控制

| 参数 | 作用 |
|------|------|
| `--review` | 启用审核模式 |
| `--no-all` | 自动模式下跳过自动暂存 |

### 提交控制

| 参数 | 作用 |
|------|------|
| `--no-verify` | 跳过本地 Git 钩子 |
| `--amend` | 修补上一次提交（⚠️ 仅限未推送分支） |
| `--signoff` | 附加 `Signed-off-by` 行 |

### 内容控制

| 参数 | 作用 |
|------|------|
| `--emoji` | 在提交信息中包含 emoji 前缀 |
| `--scope <scope>` | 指定提交作用域 |
| `--type <type>` | 强制提交类型 |

---

## 提交类型与 Emoji

| 类型 | 说明 | Emoji |
|------|------|-------|
| `feat` | 新增功能 | ✨ |
| `fix` | 缺陷修复 | 🐛 |
| `docs` | 文档与注释 | 📝 |
| `style` | 风格/格式 | 🎨 |
| `refactor` | 重构 | ♻️ |
| `perf` | 性能优化 | ⚡️ |
| `test` | 新增/修复测试 | ✅ |
| `chore` | 构建/工具 | 🔧 |
| `ci` | CI/CD 配置 | 👷 |
| `revert` | 回滚提交 | ⏪️ |

---

## 智能拆分规则

当改动满足以下条件时，技能会自动拆分提交：

| 拆分类型 | 触发条件 |
|----------|----------|
| **规模过大** | 改动行数 > 300 或文件数 > 20 |
| **跨模块过多** | 跨越顶级目录数 > 5 个 |
| **类型混合** | 包含 2 种以上不同类型的改动（如 feat + fix） |
| **功能独立** | 涉及 2 个以上互不相关的功能模块 |

---

## 常见问题

### Q：自动模式会不会误提交不想要的内容？

A：可以使用 `--review` 参数启用审核模式，在暂存前确认要提交的文件；或者先用 `git add <path>` 手动暂存需要的文件。

### Q：如何让技能默认使用中文 commit message？

A：编辑 [`config.yaml`](config.yaml:68) 中的 `default_language: "zh"`。

### Q：自动模式会跳过 Git 钩子吗？

A：不会。自动模式依然会执行本地 Git 钩子；如需跳过，请使用 `--no-verify` 参数。

### Q：如何查看最近的 commit message？

A：技能会在提交成功后显示完整信息；也可用 `git log -1 --format=full` 查看。

---

## 更多文档

- [`SKILL.md`](SKILL.md) — 技能执行规范和工作流
- [`config.yaml`](config.yaml) — 可配置参数
- [`CHANGELOG.md`](CHANGELOG.md) — 版本变更历史

---

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic, OpenAI（2/6 = 33%）
- **来源构成**：社区 70%, 官方 20%, 技术博客 10%
- **数据时效**：2024-10 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试 commit 信息生成准确率

---

### 场景化建议

#### 场景 1：标准提交信息生成（最常见）

**触发条件**：日常代码提交，需要生成规范的 commit message

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 |
| **推理强度** | low |
| **预期成本** | ~$0.001-0.01/次 |

**理由**：
- Haiku 是 Anthropic 最快的模型，响应时间 < 1 秒
- 成本仅为 Sonnet 的 20%
- commit 信息生成是简单的文本处理任务，主要是模式匹配和模板填充
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1ocpoye/haiku_45_better_than_sonnet/) 显示 Haiku 在简单脚本任务中表现优异

**避免**：无需升级，除非遇到复杂的代码逻辑分析需求

**来源**：[Haiku System Card](https://www.anthropic.com/claude-haiku-4-5-system-card) + Reddit 社区讨论

---

#### 场景 2：复杂改动分析

**触发条件**：
- 需要深度理解代码变更的业务逻辑
- 大规模改动的拆分决策（>300 行，多模块）
- 需要判断破坏性变更

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium |
| **预期成本** | ~$0.02-0.10/次 |

**理由**：
- Sonnet 在代码分析任务中表现出色
- 更适合需要"中等复杂度理解"的场景
- [社区对比](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249) 显示 Sonnet 在复杂场景下的优势
- **复杂改动拆分需要一定的推理能力**

**避免**：简单提交不需要 Sonnet，用 Haiku 即可

**来源**：社区对比讨论 + 官方模型选择指南

---

#### 场景 3：批量提交

**触发条件**：
- 需要连续生成多个 commit message
- 成本敏感，需要高性价比

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 |
| **推理强度** | low |
| **预期成本** | ~$0.005-0.03/批 |

**理由**：
- Haiku 成本最低，适合批量提交
- 批量提交中速度优势明显
- [社区验证](https://chatlyai.app/blog/claude-haiku-4-5-use-cases) 显示 Haiku 能"handle high-volume tasks without breaking the bank"

**避免**：复杂改动拆分时不要只用 Haiku

**来源**：社区反馈 + 官方文档

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Haiku 4.5** | 标准提交、批量提交 | 复杂改动分析 | $ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Sonnet 4.5** | 复杂改动拆分、破坏性变更判断 | 简单提交（浪费） | $$$ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Opus 4.5** | **不推荐** | 所有场景 | $$$$$ | ⭐ | ⭐ |

**说明**：
- Haiku 覆盖 95% 的 Git 提交场景
- Sonnet 仅在复杂改动拆分时才值得使用
- Opus 对此任务**完全不必要**，成本过高且无性能提升

---

### 通用原则

1. **默认从 Haiku 开始**：95% 的 Git 提交任务 Haiku 足够，无需升级
2. **简单任务、快速响应**：Git 提交是高频操作，Haiku 的 <1 秒响应时间明显优于 Sonnet 的 3-5 秒
3. **成本敏感**：批量提交时成本差异明显（Haiku 是 Sonnet 成本的 1/5）
4. **复杂度判断**：仅当改动规模 >300 行或跨 >5 个模块时，考虑升级 Sonnet
5. **避免过度设计**：commit 信息生成是简单的文本处理任务，Haiku 完全胜任

---

### ⚠️ 争议点

#### Haiku vs Sonnet：Git 提交真的可以用 Haiku 吗？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Haiku 足够** | Reddit 社区 | Git 提交是简单任务，Haiku 在文本生成任务中表现稳定 |
| **Sonnet 更保险** | 部分开发者 | 担心 Haiku 在复杂改动分析时出错 |

**数据支持**：
- [某用户测试](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)：Haiku 在编码任务中匹配 Sonnet 能力，成本降低 80%
- [官方文档](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)：Haiku 专为"高吞吐量、低延迟"场景设计

**建议**：
- **默认使用 Haiku**：Git 提交属于简单的文本处理任务，Haiku 完全胜任
- **仅在以下情况升级 Sonnet**：
  - 改动规模 >300 行或跨 >5 个模块
  - 需要深度理解业务逻辑才能确定提交类型
  - 需要判断破坏性变更（API 变更、配置格式变更）
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

## 致谢

本技能的开发参考了 [UfoMiao/zcf](https://github.com/UfoMiao/zcf) 项目，汲取了其在 Conventional Commits 规范实现方面的设计思路。感谢原作者的开源贡献。
