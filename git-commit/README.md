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

## 致谢

本技能的开发参考了 [UfoMiao/zcf](https://github.com/UfoMiao/zcf) 项目，汲取了其在 Conventional Commits 规范实现方面的设计思路。感谢原作者的开源贡献。
