# Git 工作流参考文档

## Conventional Commits 规范

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat(auth): add OAuth2 login support |
| `fix` | Bug 修复 | fix(payment): resolve race condition in refund |
| `docs` | 文档变更 | docs(api): update authentication endpoints |
| `style` | 代码格式（不影响功能） | style: fix indentation in utils.py |
| `refactor` | 重构（不是新功能也不是修复） | refactor(database): extract query builder |
| `perf` | 性能优化 | perf(cache): implement Redis caching layer |
| `test` | 测试相关 | test(auth): add login validation tests |
| `chore` | 构建/工具变更 | chore: upgrade to Node.js 20 |
| `ci` | CI 配置 | ci: add GitHub Actions workflow |

### Subject 规则

- 使用现在时态（"add" 而非 "added"）
- 首字母小写
- 不以句号结尾
- 不超过 50 字符

### Body 规则（可选）

- 包含"什么"和"为什么"
- 每行 ≤ 72 字符
- 解释动机而非代码

### Footer 规则（可选）

- 关联 Issue：`Closes #123`
- 破坏性变更：`BREAKING CHANGE:`

### 提交示例

#### 简单提交

```bash
git commit -m "feat(api): add user registration endpoint"
```

#### 完整提交

```bash
git commit -m "feat(auth): add OAuth2 login support

Implement Google and GitHub OAuth2 providers.
Update authentication middleware to handle OAuth callbacks.
Add session management for OAuth users.

Closes #123"
```

#### 破坏性变更

```bash
git commit -m "feat(api): remove deprecated endpoints

Remove /v1/users and /v1/products endpoints.
Clients should use /v2/ equivalents.

BREAKING CHANGE: /v1/ endpoints removed
Closes #456"
```

## Pull Request 最佳实践

### PR 标题格式

与 Conventional Commits 一致：

- `feat: add user dashboard`
- `fix: resolve memory leak in worker`
- `refactor: extract payment service`

### PR 描述模板

```markdown
## 📋 变更类型
- [ ] `feat` 新功能
- [ ] `fix` Bug 修复
- [ ] `refactor` 重构
- [ ] `docs` 文档
- [ ] `style` 代码格式
- [ ] `test` 测试
- [ ] `chore` 构建/工具

## 📝 变更说明
<!-- 简要描述这个 PR 的目的和实现方式 -->

<!-- 回答：这个 PR 解决了什么问题？为什么需要这个变更？ -->

## 🧪 测试
- [ ] 添加了单元测试
- [ ] 添加了集成测试
- [ ] 手动测试通过
- [ ] 性能测试通过（如适用）

## ✅ 检查清单
- [ ] 代码符合团队规范
- [ ] 自我审查完成
- [ ] 注释充分且准确
- [ ] 文档已更新
- [ ] 无新的警告产生
- [ ] 测试覆盖率未降低

## 📸 截图/演示（可选）
<!-- 添加 UI 变更的截图 -->

## 🔗 相关链接
- 关联 Issue: #123
- 设计文档: [链接]
```

## 分支策略

### 分支命名规范

| 分支类型 | 命名模式 | 示例 |
|---------|---------|------|
| 功能开发 | `feature/*` | `feature/user-dashboard` |
| Bug 修复 | `bugfix/*` | `bugfix/login-timeout` |
| 紧急修复 | `hotfix/*` | `hotfix/security-patch` |
| 发布版本 | `release/*` | `release/v1.5.0` |

### 工作流程

#### 1. 开始新功能

```bash
# 从 main 创建功能分支
git checkout main
git pull origin main
git checkout -b feature/user-dashboard

# 开发功能
# ... 编写代码 ...

# 提交变更
git add .
git commit -m "feat(dashboard): add user profile section"

# 推送分支
git push -u origin feature/user-dashboard
```

#### 2. 创建 Pull Request

```bash
# 使用 GitHub CLI
gh pr create \
  --title "feat: add user dashboard" \
  --body "PR 描述..." \
  --base main \
  --head feature/user-dashboard
```

#### 3. 代码审查与合并

- 至少一人审查通过
- CI 检查全部通过
- 使用 Squash and Merge 保持历史清晰

#### 4. 清理分支

```bash
# 合并后删除本地分支
git branch -d feature/user-dashboard

# 删除远程分支
git push origin --delete feature/user-dashboard
```

## Git Hooks 配置

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# 运行 linter
npm run lint || exit 1

# 运行类型检查
npm run type-check || exit 1

# 运行测试
npm run test || exit 1

echo "✅ Pre-commit checks passed!"
```

### Commit-msg Hook（强制 Conventional Commits）

```bash
#!/bin/bash
# .git/hooks/commit-msg

commit_regex='^(feat|fix|docs|style|refactor|perf|test|chore|ci)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ Invalid commit message format!"
    echo "Expected format: <type>(<scope>): <subject>"
    echo "Types: feat, fix, docs, style, refactor, perf, test, chore, ci"
    exit 1
fi

echo "✅ Commit message format valid!"
```

## 常用 Git 命令

### 日常操作

```bash
# 查看状态
git status

# 暂存变更
git add .
git add <file>

# 提交变更
git commit -m "type(scope): description"

# 推送变更
git push
git push -u origin <branch>

# 拉取最新
git pull
git pull --rebase  # 避免 merge commit
```

### 历史查看

```bash
# 查看提交历史
git log --oneline
git log --graph --all  # 图形化

# 查看文件历史
git log -p <file>

# 查看分支
git branch -a
```

### 问题修复

```bash
# 撤销最后一次提交（保留变更）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃变更）
git reset --hard HEAD~1

# 撤销已推送的提交（创建新提交）
git revert <commit-hash>

# 修改最后一次提交信息
git commit --amend

# 交互式 rebase（清理历史）
git rebase -i HEAD~3
```

## 高级技巧

### Git Bisect（二分查找 Bug）

```bash
# 开始二分查找
git bisect start

# 标记当前版本为坏
git bisect bad

# 标记已知好的版本
git bisect good <good-commit-hash>

# Git 会切换到中间版本，测试后标记
git bisect good  # 或 git bisect bad

# 重复直到找到引入问题的 commit
git bisect reset  # 结束
```

### Git Blame（查看每行是谁写的）

```bash
# 查看文件每行的最后修改者
git blame <file>

# 查看特定行
git blame -L 10,20 <file>
```

### Git Stash（临时保存变更）

```bash
# 保存当前变更
git stash

# 保存并添加描述
git stash save "work in progress"

# 查看 stash 列表
git stash list

# 应用最近一次 stash
git stash pop

# 应用指定 stash
git stash apply stash@{1}

# 删除 stash
git stash drop
```

## 团队协作最佳实践

### 提交频率

- **小而频繁**：每完成一个小功能就提交
- **原子性**：每次提交是一个逻辑单元
- **可回滚**：任何提交都应能独立回滚

### 分支管理

- **短期分支**：功能分支应在几天内完成
- **及时清理**：合并后立即删除分支
- **保护 main**：main 分支应设置保护规则

### 代码审查

- **Pull Request**：所有代码通过 PR 合并
- **审查者**：至少一人审查
- **自动化**：CI 检查必须通过

## 检查清单总结

### 提交前检查

- [ ] 提交信息符合 Conventional Commits 规范
- [ ] 代码通过 linter
- [ ] 测试全部通过
- [ ] 无敏感信息泄露
- [ ] 注释充分

### PR 前检查

- [ ] PR 标题格式正确
- [ ] PR 描述完整
- [ ] 关联 Issue
- [ ] CI 检查通过
- [ ] 代码自我审查完成

### 合并后清理

- [ ] 删除本地分支
- [ ] 删除远程分支
- [ ] 更新文档（如需要）

## 参考资源

- [Git Commit (getsentry/commit)](https://github.com/getsentry/sentry-skills)
- [Git & GitHub Workflow Skills (fvadicamo/dev-agent-skills)](https://github.com/fvadicamo/dev-agent-skills)
- [Conventional Commits](https://www.conventionalcommits.org/)
