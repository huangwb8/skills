---
name: git-commit
description: 当用户要提交 Git 改动时使用。仅用 Git 分析改动并自动生成 conventional commit 信息（可选 emoji）；必要时建议拆分提交，默认运行本地 Git 钩子（可 --no-verify 跳过）。适用于"提交代码"、"git commit"、"生成提交信息"、"提交改动"等场景。
metadata:
  short-description: 仅用 Git 分析改动并生成 conventional commit 信息（可选 emoji）
  keywords:
    - git commit
    - 提交代码
    - 提交改动
    - 生成提交信息
    - conventional commit
    - commit message
    - Git 提交
    - 自动提交
    - 拆分提交
    - emoji commit
    - commitizen
category: normal
---

# Git Commit

仅用 Git 分析改动并自动生成 conventional commit 信息（可选 emoji）；必要时建议拆分提交，默认运行本地 Git 钩子（可 --no-verify 跳过）。

## 触发场景

- 用户要提交代码改动
- 需要生成符合规范的提交信息
- 需要判断是否应该拆分提交
- 需要包含 emoji 的提交信息

## 工作流程

### 1. 仓库/分支校验

- 通过 `git rev-parse --is-inside-work-tree` 判断是否位于 Git 仓库
  - **如不在 Git 仓库**：提示 `git init` 初始化仓库后继续
- 读取当前分支/HEAD 状态：
  - **如处于 detached HEAD 状态**：提示风险并确认是否继续
    - 检测方法：`git rev-parse --symbolic-full-name HEAD` 返回 `HEAD`
    - 提示内容："⚠️ 当前处于 detached HEAD 状态，提交将不属于任何分支。建议先创建分支（`git switch -c <branch-name>`）或切换到现有分支（`git switch <branch-name>`）"
  - **如处于 rebase/merge 冲突状态**：给出明确指导
    - **检测到 Git 冲突**：当前处于 rebase/merge 冲突状态，请先处理冲突：
      1. 查看冲突文件：`git status`
      2. 解决冲突（编辑标记为 `<<<<<<<` 的文件）
      3. 标记冲突已解决：`git add <冲突文件>`
      4. 继续 rebase/merge：`git rebase --continue` 或 `git merge --continue`
      5. 完成后重新运行 git-commit
    - 或跳过当前提交：`git rebase --skip`
    - 或中止 rebase/merge：`git rebase --abort` / `git merge --abort`

### 2. 改动检测

- 用 `git status --porcelain` 与 `git diff` 获取已暂存与未暂存的改动
  - **如无改动**：提示 "当前无改动，无需提交"，退出
- 若已暂存文件为 0：
  - 若传入 `--all` → 执行 `git add -A`
  - 否则提示用户选择：
    - **选项 1**：暂存所有改动（`git add -A`）
    - **选项 2**：暂存部分文件（`git add <path>...`）
    - **选项 3**：取消命令，手动分组暂存后重试

### 3. 拆分建议

按以下决策树判断是否需要拆分提交：

**1. 强制拆分条件**（任一满足则建议拆分）：
- 超过规模阈值：改动行数 > 300 行或跨越目录数 > 5 个
- 多种提交类型：包含 2 种以上不同类型的改动（如 feat + fix）
- 多个独立功能：改动涉及 2 个以上互不相关的功能模块

**2. 建议拆分条件**（不满足强制条件时）：
- 文件类型混合：源代码 + 文档/测试在同一提交
- 可回滚性差：单个提交回滚会影响其他功能

**3. 单一提交条件**（以上都不满足）：
- 改动规模适中（< 300 行）
- 单一功能模块
- 单一提交类型
- 可独立回滚

若检测到多组独立变更或 diff 规模过大，给出每一组的 pathspec 拆分建议

### 4. 提交信息生成

#### 格式规范

遵循 Conventional Commits 规范：

```
[<emoji>] <type>(<scope>)?: <subject>

<body>

<footer>
```

#### 类型（type）

详见 config.yaml 中的 `commit_types` 定义。

#### Emoji 映射（使用 --emoji 时）

详见 config.yaml 中的 `emoji_map` 定义。

#### 自动识别 type 和 scope

**type 自动识别**：根据改动内容自动识别（如新增功能 → feat，修复缺陷 → fix）

**scope 自动识别**：
- 取改动文件的最上层模块名（如改动 `src/auth/login.ts` → scope 为 `auth`）
- 如跨越多个模块，省略 scope（如 `feat: add user feature`）
- 用户可通过 `--scope` 参数覆盖自动识别的 scope

#### 内容要求

- **主题行**：首行 ≤ 72 字符，祈使语气，使用动词开头
- **正文**：
  - 必须在 subject 之后空一行
  - 使用列表格式，每项以 `-` 开头
  - 每项必须使用动词开头的祈使句
  - 禁止使用冒号分隔的格式（如 "Feature: description"）
  - 说明变更的动机、实现要点或影响范围（3 项以内为宜）
- **脚注**：
  - 必须在 Body 之后空一行
  - 破坏性变更：`BREAKING CHANGE: <description>`
  - 其它采用 git trailer 格式（如 `Closes #123`）

#### 破坏性变更检测与处理

**检测规则**（满足任一条件即为破坏性变更）：
- 删除了公开 API（函数、类、方法）
- 修改了公开 API 的签名（参数、返回值）
- 修改了配置文件的格式
- 删除了配置项或改变了配置项的语义
- 数据库 schema 变更（不兼容旧版本）

**处理方式**：
- 在 type 后添加 `!` 标记（如 `feat(api)!: redesign authentication API`）
- 在脚注中说明 `BREAKING CHANGE: <description>`
- 建议将破坏性变更拆分为独立提交（如与修复混在同一提交）

#### 语言选择

按以下优先级选择提交信息语言：
1. 用户显式配置（详见 config.yaml 中的 `default_language`）
2. 检查最近 50 个提交的主要语言（`git log -n 50 --pretty=%s`）
3. 若仓库为空或无法判断，检查项目主要文件的语言（如 README.md）
4. 降级到英文（作为默认值）

### 5. 执行提交

- 单提交场景：`git commit [-S] [--no-verify] [-s] -F .git/COMMIT_EDITMSG`
- 多提交场景（如接受拆分建议）：按分组给出 `git add <paths> && git commit ...` 的明确指令

### 6. 安全回滚

如误暂存，可用 `git restore --staged <paths>` 撤回暂存（命令会给出指令）

## 使用参数

- `--no-verify`：跳过本地 Git 钩子
- `--all`：当暂存区为空时，自动 `git add -A`
- `--amend`：修补上一次提交（⚠️ 危险操作：仅在未推送的本地分支使用，已推送的分支使用会导致历史不一致）
- `--signoff`：附加 `Signed-off-by` 行
- `--emoji`：在提交信息中包含 emoji 前缀
- `--scope <scope>`：指定提交作用域
- `--type <type>`：强制提交类型

## 输出示例

### 使用 emoji

```
✨ feat(ui): add user authentication flow

- implement Google and GitHub third-party login
- add user authorization callback handling
- improve login state persistence logic

Closes #42
```

### 不使用 emoji

```
feat(auth): add OAuth2 login flow

- implement Google and GitHub third-party login
- add user authorization callback handling
- improve login state persistence logic
```

### 包含破坏性变更

```
feat(api)!: redesign authentication API

- migrate from session-based to JWT authentication
- update all endpoint signatures
- remove deprecated login methods

BREAKING CHANGE: authentication API has been completely redesigned, all clients must update their integration
```

### 拆分提交示例

**检测到多组独立变更，建议拆分为以下提交**：

#### 提交 1：feat(ui): add user authentication flow
```bash
git add src/components/LoginForm.tsx src/hooks/useAuth.ts
git commit -m "feat(ui): add user authentication flow

- implement login form with email and password fields
- add authentication state management hook

Closes #42"
```

#### 提交 2：fix(api): resolve token validation error
```bash
git add src/api/auth.ts
git commit -m "fix(api): resolve token validation error

- add proper error handling for expired tokens
- update token refresh logic"
```

#### 提交 3：docs(auth): update authentication documentation
```bash
git add docs/auth-guide.md
git commit -m "docs(auth): update authentication documentation

- add OAuth2 integration guide
- update troubleshooting section"
```

## 重要约束

- **仅使用 Git**：不调用任何包管理器/构建命令
- **尊重钩子**：默认执行本地 Git 钩子；使用 `--no-verify` 可跳过
- **不改源码内容**：命令只读写 `.git/COMMIT_EDITMSG` 与暂存区
- **安全提示**：在 rebase/merge 冲突、detached HEAD 等状态下会先提示处理/确认再继续
