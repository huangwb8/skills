# Git Commit Skill

自动生成符合 Conventional Commits 规范的 Git 提交信息，支持 emoji 和智能拆分建议。

## 功能特点

- ✅ 仅依赖 Git，无需其他工具
- ✅ 自动生成符合规范的提交信息
- ✅ 支持可选的 emoji 前缀
- ✅ 智能判断是否需要拆分提交
- ✅ 根据仓库历史自动选择语言
- ✅ 默认运行本地 Git 钩子

## 使用方法

### 基本使用

```bash
# 分析当前改动，生成提交信息
/git-commit

# 暂存所有改动并提交
/git-commit --all

# 跳过 Git 钩子检查
/git-commit --no-verify

# 使用 emoji
/git-commit --emoji
```

### 高级选项

```bash
# 指定作用域和类型
/git-commit --scope ui --type feat --emoji

# 修补上次提交并签名
/git-commit --amend --signoff

# 组合使用
/git-commit --all --emoji --signoff
```

## 提交类型

| 类型 | 说明 | Emoji |
|------|------|-------|
| `feat` | 新增功能 | ✨ |
| `fix` | 缺陷修复 | 🐛 |
| `docs` | 文档与注释 | 📝 |
| `style` | 风格/格式 | 🎨 |
| `refactor` | 重构 | ♻️ |
| `perf` | 性能优化 | ⚡️ |
| `test` | 测试 | ✅ |
| `chore` | 构建/工具 | 🔧 |
| `ci` | CI/CD | 👷 |
| `revert` | 回滚 | ⏪️ |

## 配置文件

配置文件位于 `config.yaml`，可自定义：

- 提交类型定义
- Emoji 映射
- 拆分提交的阈值
- 提交信息约束

## 示例

### 使用 emoji 的提交

```
✨ feat(ui): add user authentication flow

- implement Google and GitHub third-party login
- add user authorization callback handling
- improve login state persistence logic

Closes #42
```

### 不使用 emoji 的提交

```
feat(auth): add OAuth2 login flow

- implement Google and GitHub third-party login
- add user authorization callback handling
- improve login state persistence logic
```

## 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本变更历史。

---

## 致谢

本技能的开发参考了 [UfoMiao/zcf](https://github.com/UfoMiao/zcf) 项目，汲取了其在 Conventional Commits 规范实现方面的设计思路。感谢原作者的开源贡献。

## 许可证

MIT License
