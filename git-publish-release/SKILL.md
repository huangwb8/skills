---
name: git-publish-release
description: 当用户明确要求"发布项目到 GitHub"、"创建 GitHub Release"或"生成 Release Notes"时使用。智能分析 tag 间历史变化，生成专业且吸引人的 Release Notes，自动创建 GitHub Release。支持首次发布、常规版本、预发布版本（alpha/beta/rc），自动识别 prerelease 标记。

metadata:
  author: Bensz Conan
  short-description: GitHub Release 自动发布与 Release Notes 生成
  keywords:
    - git-publish-release
    - GitHub Release
    - release notes
    - version publish
---

# GitHub Release

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求“report bensz skills bugs”等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

智能分析项目历史变化，自动生成吸引人的 Release Notes 并发布到 GitHub。

## 触发条件

用户需要：
- 发布项目的新版本到 GitHub
- 创建 GitHub Release 并自动生成 Release Notes
- 推送某个 tag 到 GitHub 并创建 release
- 总结版本间的历史变化

## 你需要确认的输入

1. **目标 tag**（如 `v3.0.0`）
   - 如未指定，列出最近 tags 供选择
2. **项目路径**（可选，默认当前工作目录）

> 认证通过 `gh auth login` 管理，无需手动配置 token。

## 前置检查

确认 `gh` CLI 已安装并已认证：

```bash
gh auth status
```

如未认证，提示用户运行：

```bash
gh auth login
```

## 工作流程

### 确认项目信息

```bash
# 获取 owner/repo
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
```

### 获取最新 Release 信息

```bash
# 获取最近一次 release 的 tag
PREVIOUS_TAG=$(gh release list --limit 1 --json tagName -q '.[0].tagName')
```

- 如果存在历史 release，比较范围为：`PREVIOUS_TAG..TARGET_TAG`
- 如果是首个 release，比较范围为：从初始 commit 到 `TARGET_TAG`

### 分析历史变化

获取两个版本之间的 commit 历史：

```bash
# 如果有历史 release
git log ${PREVIOUS_TAG}..${TARGET_TAG} --pretty=format:"%h|%s|%an|%ad" --date=short

# 如果是首个 release
git log ${TARGET_TAG} --pretty=format:"%h|%s|%an|%ad" --date=short
```

### 生成 Release Notes

根据 commit 历史和项目特点，智能生成 Release Notes。

#### Release Notes 结构

```
🎉 [版本号] - [吸引人的标题]
[一句话总结本次发布的核心价值/意义]

🚀 核心亮点：
• [亮点1]
• [亮点2]
• [亮点3]

✨ 主要更新：
[类别1]
• 更新内容1
• 更新内容2

[类别2]
• 更新内容3
• 更新内容4

🔧 技术改进：
• 技术改进1
• 技术改进2

📋 完整变更日志：
[简略说明获取方式或列出主要 commits]
```

#### 标题撰写原则

- **情感化表达**：使用"革命性"、"突破性"、"里程碑"等词汇
- **场景化描述**：说明这个版本解决什么问题、带来什么价值
- **时效性关联**：如"为 2026 年就绪"、"拥抱新范式"

#### 内容分类原则

根据 commit 信息自动分类：

| 类别图标 | 类别名称 | Commit 关键词示例 |
|---------|---------|-----------------|
| 🚀 | 核心亮点 | breakthrough, major, feature |
| ✨ | 新功能 | add, new, feature |
| 🐛 | Bug 修复 | fix, bugfix, resolve |
| 🔧 | 技术改进 | refactor, optimize, improve |
| 📝 | 文档更新 | docs, readme, guide |
| 🔐 | 安全更新 | security, fix vulnerability |
| 💥 | 破坏性变更 | breaking, deprecate |

#### 语言风格

- **简洁有力**：每个要点不超过一行
- **价值导向**：强调"为什么"而非仅仅"是什么"
- **用户视角**：用用户能理解的语言，避免技术术语堆砌
- **适当煽动**：使用感叹号、emoji 营造氛围，但不过度

### 判断是否为 Prerelease

根据 tag 名称自动判断：
- 包含 `alpha`, `beta`, `rc`, `pre` 等标识 → `prerelease: true`
- 否则 → `prerelease: false`

### 创建 GitHub Release

```bash
# 将 Release Notes 写入临时文件（避免 shell 转义问题）
NOTES_FILE=$(mktemp /tmp/release-notes-XXXXXX.md)
cat > "$NOTES_FILE" << 'NOTES_EOF'
[生成的 Release Notes 内容]
NOTES_EOF

# 正式版
gh release create "$TARGET_TAG" \
  --title "$TARGET_TAG" \
  --notes-file "$NOTES_FILE"

# 预发布版（tag 含 alpha/beta/rc/pre 时）
gh release create "$TARGET_TAG" \
  --title "$TARGET_TAG" \
  --notes-file "$NOTES_FILE" \
  --prerelease

# 清理临时文件
rm -f "$NOTES_FILE"
```

## 输出格式

完成发布后，向用户输出：

```
✅ Release 发布成功！

📍 Release URL: [release 链接]
🏷️ Tag: [tag 名称]
📅 发布时间: [时间]

📝 Release Notes 预览：
[生成的前 10 行 notes]
```

## 参考资源

- Release Notes 生成策略：[references/release-notes-strategy.md](references/release-notes-strategy.md)
- Release Notes 示例模板：[references/release-templates.md](references/release-templates.md)
- GitHub CLI 文档：https://cli.github.com/manual/gh_release_create

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| `gh` 未安装 | 提示安装：`brew install gh` 或访问 https://cli.github.com |
| `gh` 未认证 | 提示运行 `gh auth login` |
| Tag 不存在 | 提示用户可用的 tags 列表 |
| 网络请求失败 | 重试 3 次，仍失败则报错并给出手动创建指南 |
| 权限不足 | 提示检查 `gh auth status` 及仓库权限 |
| Release 已存在 | 询问用户是否覆盖（使用 `gh release edit`） |

## 实现注意事项

1. **跨平台兼容**：始终使用正斜杠 `/` 处理路径
2. **Notes 转义**：使用 `--notes-file` 传递临时文件，避免 shell 特殊字符转义问题
3. **Git 远程解析**：`gh repo view` 自动处理 HTTPS 和 SSH 两种 remote URL 格式
4. **认证管理**：`gh` CLI 使用系统 keychain 或 `~/.config/gh/hosts.yml` 存储凭证，无需手动管理 token
