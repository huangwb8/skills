# GitHub Release 发布 — 用户使用指南

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

1. **GitHub Token**：需要具有 `repo` 权限的 GitHub Personal Access Token
   - 创建地址：https://github.com/settings/tokens
   - 所需权限：`repo` (完整仓库访问权限)

2. **设置环境变量**：
   ```bash
   export GH_TOKEN="your_github_token_here"
   ```

3. **Git 仓库**：项目必须是 Git 仓库，且有 GitHub remote

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

### 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `GH_TOKEN` | 是 | GitHub Personal Access Token |
| `GIT_REMOTE` | 否 | 指定 git remote（默认：origin） |

### Git Remote 格式支持

- HTTPS: `https://github.com/owner/repo.git`
- SSH: `git@github.com:owner/repo.git`

## 🛠️ 故障排查

### 问题：GH_TOKEN 未设置

**解决方案**：
```bash
export GH_TOKEN="your_token_here"
```

或创建 token：https://github.com/settings/tokens

### 问题：Tag 不存在

**解决方案**：先创建 tag
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 问题：权限不足

**解决方案**：检查 token 权限，确保包含 `repo` scope

### 问题：Release 已存在

**解决方案**：技能会询问是否覆盖，选择更新现有 release

## 📚 相关资源

- [SKILL.md](SKILL.md) - 技能核心逻辑
- [Release Notes 生成策略](references/release-notes-strategy.md)
- [Release Notes 模板示例](references/release-templates.md)
- [GitHub API 文档](https://docs.github.com/en/rest/releases/releases)

## 🤝 贡献

欢迎反馈和改进建议！请提交 issue 或 PR。

## 📄 许可

MIT License
