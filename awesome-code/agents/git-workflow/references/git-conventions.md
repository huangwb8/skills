# Git Conventions Reference

详细的 Git 约定和操作参考。供 agent 在需要深入信息时查阅。

## Conventional Commits Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(auth): add OAuth2 login` |
| `fix` | Bug 修复 | `fix(api): resolve timeout issue` |
| `docs` | 文档变更 | `docs(readme): update installation` |
| `style` | 代码格式 | `style(lint): fix indentation` |
| `refactor` | 重构 | `refactor(utils): extract validator` |
| `perf` | 性能优化 | `perf(db): add query index` |
| `test` | 测试相关 | `test(user): add login tests` |
| `chore` | 构建/工具 | `chore(deps): upgrade to v2.0` |
| `revert` | 回滚提交 | `revert: feat(auth)` |

## 提交大小参考

| 类型 | 行数变化 | 建议 |
|------|----------|------|
| **小型** | < 100 行 | 理想 |
| **中型** | 100-400 行 | 可接受 |
| **大型** | > 400 行 | 应拆分 |

## 分支命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| **功能** | `feature/*` | `feature/user-auth` |
| **修复** | `bugfix/*` | `bugfix/login-timeout` |
| **热修复** | `hotfix/*` | `hotfix/security-patch` |
| **发布** | `release/*` | `release/v1.2.0` |
| **实验** | `experiment/*` | `experiment/new-ui` |

## 分支工作流示意

```
main (生产)
  ↑
  ├── release/v1.2.0 (发布准备)
  │     ↑
  │     ├── feature/user-auth (功能开发)
  │     ├── feature/payment-api (功能开发)
  │     └── bugfix/login-issue (Bug 修复)
  │
  └── hotfix/security-patch (紧急修复)
```

## PR 描述模板

```markdown
## 📝 变更类型
- [x] ✨ feat 新功能
- [ ] 🐛 fix Bug修复
- [ ] ♻️  refactor 重构
- [ ] 📚 docs 文档
- [ ] 💄 style 代码格式
- [ ] ⚡ perf 性能优化
- [ ] ✅ test 测试
- [ ] 🔧 chore 构建/工具

## 🎯 变更说明
<!-- 简要描述这个 PR 的目的和实现方式 -->

## 🔄 变更内容
<!-- 列出主要的文件变更 -->

## 🧪 测试
- [ ] 添加了单元测试
- [ ] 手动测试通过

## ✅ 检查清单
- [ ] 代码符合团队规范
- [ ] 自我审查完成
- [ ] 文档已更新
- [ ] 测试覆盖充分
- [ ] 无合并冲突

## 🔗 相关链接
- Closes #
- Related #
```

## Git Hooks 自动化

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

npm run lint
if [ $? -ne 0 ]; then
    echo "❌ Lint failed, please fix before committing"
    exit 1
fi

npm test
if [ $? -ne 0 ]; then
    echo "❌ Tests failed, please fix before committing"
    exit 1
fi

echo "✅ Pre-commit checks passed"
```

### Commit Message Hook

```bash
#!/bin/bash
# .git/hooks/commit-msg

commit_regex='^(feat|fix|docs|style|refactor|perf|test|chore|revert)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ Invalid commit message format"
    echo "✅ Expected format: <type>(<scope>): <subject>"
    exit 1
fi

echo "✅ Commit message format valid"
```

## 常见操作

### 修改最后一次提交

```bash
git add forgotten_file.py
git commit --amend
git commit --amend --no-edit
```

### 撤销提交

```bash
# 撤销最后一次提交（保留变更）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃变更）
git reset --hard HEAD~1
```

### 交互式变基

```bash
git rebase -i HEAD~3
# pick  - 保留提交
# reword - 修改提交信息
# edit - 编辑提交
# squash - 合并到前一个提交
# drop - 删除提交
```

### 解决合并冲突

```bash
git rebase origin/main
git status                    # 查看冲突文件
# 手动解决冲突，删除 <<<<<<< ======= >>>>>>> 标记
git add <resolved-files>
git rebase --continue
# 如果需要放弃：git rebase --abort
```
