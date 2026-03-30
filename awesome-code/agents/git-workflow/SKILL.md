---
name: git-workflow
description: "Use when making git commits, creating pull requests, managing branches, or performing version control operations. Enforces Conventional Commits, atomic commits, and PR best practices to maintain a clean, traceable history."
metadata:
  short-description: Git 工作流与版本控制
  keywords:
    - git-workflow
    - Git
    - 版本控制
    - Conventional Commits
    - Pull Request
    - 分支管理
    - 提交规范
  category: 版本控制
  author: Bensz Conan
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Git Workflow - Git 工作流专家

规范化版本控制，确保提交历史清晰可追溯。

**核心原则**：
- 提交历史即文档
- 原子提交，单一职责
- 清晰的可追溯性
- 易于 Code Review

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求"report bensz skills bugs"等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

---

## Workflow

Follow these steps for every git commit, branch, or PR operation.

### Step 1: Analyze the Change

Review staged/unstaged changes to understand scope and purpose.

```bash
git status
git diff --stat
```

**Validation:** Confirm changes are related and serve a single purpose. If changes span multiple concerns, plan to split into separate commits.

### Step 2: Determine Commit Type and Scope

Select the appropriate Conventional Commits type:

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(auth): add OAuth2 login` |
| `fix` | Bug 修复 | `fix(api): resolve timeout issue` |
| `docs` | 文档变更 | `docs(readme): update installation` |
| `refactor` | 重构 | `refactor(utils): extract validator` |
| `perf` | 性能优化 | `perf(db): add query index` |
| `test` | 测试相关 | `test(user): add login tests` |
| `chore` | 构建/工具 | `chore(deps): upgrade to v2.0` |
| `style` | 代码格式 | `style(lint): fix indentation` |
| `revert` | 回滚提交 | `revert: feat(auth)` |

**Validation:** Type must match the actual change. Scope should identify the affected module or component.

### Step 3: Craft the Commit Message

Format: `<type>(<scope>): <subject>`

Rules:
- Subject line: imperative mood, lowercase, no trailing period, max 72 characters
- Body (optional): explain **why**, not what; wrap at 72 characters
- Footer (optional): reference issues with `Closes #123` or `Related #456`

```
feat(payment): integrate Stripe payment gateway

Implement credit card payment processing using Stripe API.
Add webhook handling for payment status updates.

Closes #123
```

**Validation:**
- Subject follows `<type>(<scope>): <subject>` format
- Subject is under 72 characters
- Body explains motivation, not just listing files

### Step 4: Stage and Commit

Stage only the files relevant to this commit — avoid `git add .` when changes span multiple concerns.

```bash
git add src/auth/login.py src/auth/middleware.py
git commit -m "feat(auth): add JWT token validation"
```

**Validation:**
- Each commit has a single responsibility
- Commit size is reasonable (ideally < 400 lines changed)
- No sensitive information (secrets, credentials) included
- No unrelated files staged

### Step 5: Create Pull Request (when applicable)

PR title follows the same Conventional Commits format as the commit message.

PR description must include:
1. **变更说明** — what and why
2. **变更内容** — key files changed
3. **测试** — how it was tested
4. **相关链接** — linked issues

See [references/git-conventions.md](references/git-conventions.md) for a full PR description template.

**Validation:**
- PR title matches Conventional Commits format
- Description is complete with all required sections
- Branch naming follows convention (`feature/*`, `bugfix/*`, `hotfix/*`, `release/*`)
- No merge conflicts with target branch
- Documentation updated if behavior changed

---

## 分支管理

Create branches from `main` with descriptive names:

```bash
git checkout main && git pull origin main
git checkout -b feature/user-auth
# ... develop and commit ...
git fetch origin main && git rebase origin/main
git push origin feature/user-auth
```

Branch naming: `feature/*`, `bugfix/*`, `hotfix/*`, `release/*`, `experiment/*`

---

## Example: End-to-End Commit

Scenario: Added a rate limiting middleware to the API.

```
# 1. Check what changed
$ git diff --stat
 src/middleware/rate-limit.py | 45 +++++++++++++++
 tests/test_rate_limit.py    | 30 ++++++++++
 2 files changed, 75 insertions(+)

# 2. Type: feat, Scope: api

# 3. Craft message
# Subject: feat(api): add rate limiting middleware
# Body: Protect endpoints from abuse with configurable per-IP limits.

# 4. Stage and commit
$ git add src/middleware/rate-limit.py tests/test_rate_limit.py
$ git commit -m "feat(api): add rate limiting middleware

Protect endpoints from abuse with configurable per-IP limits.
Default: 100 requests per minute per IP.

Closes #234"

# 5. Push and open PR
$ git push origin feature/rate-limiting
```

---

## 相关参考

- [Git Conventions Reference](references/git-conventions.md) — 详细的类型表、分支策略、PR 模板、Git Hooks、常见操作
- [Conventional Commits](https://www.conventionalcommits.org/)
