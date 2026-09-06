# install-bensz-skills — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `install-bensz-skills` skill。
执行指令与硬性规范在 `SKILL.md`；默认远程源、legacy 清理名单和版本信息在 `config.yaml`。

## 快速开始

### 最推荐用法

```text
请使用 install-bensz-skills skill 将当前仓库中的 skills 安装到系统级目录，确保它们能在任意项目中被发现。
输入：当前 skills 仓库
输出：安装结果报告，以及 `~/.codex/skills/` 和 `~/.claude/skills/` 中的最新 skill 副本
```

### 进阶用法

```text
请使用 install-bensz-skills skill 安装并更新指定 skill。
输入：当前 skills 仓库
输出：系统级安装结果
另外，还有下列参数约束：
- 只安装/更新 `git-commit`
- 先 dry-run 预览
- 仅安装到 Codex
```

## 能做什么

`install-bensz-skills` 会把当前仓库 `skills/alpha/` 或远程生产源中的 skill **复制安装**到系统级目录，让这些 skill 在任意项目/对话中都更容易被发现和触发。`skills/beta/` 是未成熟技能区，默认不会扫描；只有显式 `--source` 才会安装。

本地安装器隐式发现的唯一生产源是当前项目（会从当前工作目录及其祖先目录查找）中的 `./skills/alpha/`，因此从项目子目录或 `skills/alpha` 内运行也能定位源。历史 `pipelines/skills/alpha/` 不会被默认扫描；迁移旧仓库时可显式使用 `--legacy-source`，或直接传入 `--source`。仓库开发与本地完整安装统一要求 Python 3.11+；bootstrap 作为唯一的首次/应急远程入口，最低支持 Python 3.8。Python 3.8–3.10 用户可继续使用 bootstrap 安装生产 Skill，但不能运行本地完整安装器或 Kernel。

| 你的需求 | 推荐方式 | 说明 |
|---------|----------|------|
| 安装或更新本仓库全部 skill | 默认运行 | 只更新内容变化的 skill，未变化的自动跳过 |
| 只更新某一个 skill | `--skill skill-name` | 不需要区分安装/更新；没有就安装，有就按 MD5 判断更新或跳过 |
| 只更新安装器自己 | `--skill install-bensz-skills` | 当前版本的安装器自身也是普通可安装 skill |
| 先看本地安装会发生什么 | `--dry-run` | 只打印动作，不写入系统级目录 |
| 只装到一个平台 | `--codex` 或 `--claude` | 默认同时安装到 Codex 和 Claude Code |
| 先看远程安装会发生什么 | `--remote --check` | 下载后先对比，再确认安装 |
| 自动远程安装 | `--remote --auto` | 无交互确认，适合明确要直接更新的场景 |
| 只安装某个远程源 | `--remote --check --general` | `--general`、`--research`、`--anthropic-docs` 来自 `config.yaml` |
| 加速大仓库远程源 | 配置 `skills_path` 为目标子目录 | 安装器会优先用 Git sparse checkout 只下载目标 skill 子目录 |
| 远程只更新某个 skill | `--remote --check --research --skill nsfc-bib-manager` | 只 sparse 拉取目标 skill 目录，避免下载整个远程 skills 集合 |
| 首次无依赖引导 | 运行 `scripts/bootstrap_install.py` | 标准库远程安装器，general 固定只取 `skills/alpha` |
| 重复远程更新 | 直接再次运行远程命令 | 复用本地远程 repo 缓存，通过浅 fetch 增量更新 |

## 使用示例

### 示例 1：本地仓库一次性安装

```text
请使用 install-bensz-skills skill 将当前仓库中的 skills 安装到系统级目录。
输入：当前 skills 仓库
输出：安装结果报告
```

### 示例 2：只安装/更新一个 skill

```text
请使用 install-bensz-skills skill 只安装或更新 `nsfc-bib-manager`。
输入：当前 skills 仓库
输出：`nsfc-bib-manager` 的系统级安装结果
```

### 示例 3：只安装到 Claude Code

```text
请使用 install-bensz-skills skill 安装这些 skills。
输入：当前 skills 仓库
输出：Claude Code 系统级 skills 目录中的最新副本
另外，还有下列参数约束：
- 仅安装到 Claude Code
```

### 示例 4：只更新安装器自己

```text
请使用 install-bensz-skills skill 只安装或更新 `install-bensz-skills` 自身。
输入：当前 skills 仓库
输出：系统级目录中的最新版 `install-bensz-skills`
另外，还有下列参数约束：
- 只处理 `install-bensz-skills`
```

### 示例 5：远程检查后安装

```text
请使用 install-bensz-skills skill 从远程仓库安装技能。
输入：远程源配置
输出：下载、对比并确认后的技能安装结果
另外，还有下列参数约束：
- 只检查 `general` 源
- 使用交互检查模式
```

### 示例 6：远程只更新一个 skill

```text
请使用 install-bensz-skills skill 从远程 general 源只安装或更新 `git-commit`。
输入：远程源配置
输出：`git-commit` 的远程对比与安装结果
另外，还有下列参数约束：
- 只处理 `general` 源
- 只处理 `git-commit`
- 安装前先确认
```

## 输出结果

- 系统级 skill 副本，默认安装到：
  - `~/.codex/skills/`
  - `~/.claude/skills/`
- 安装报告：显示哪些 skill 已安装/更新、哪些已跳过，以及跳过原因。
- 平台级版本 manifest：`.skill-manifest.codex.json` 或 `.skill-manifest.claude.json`。
- 安装历史记录：`~/.bensz-skills/installation/manifests/`。
- 远程安装临时目录：`~/.bensz-skills/installation/tmp-remote-install`，运行结束后会清理。
- 远程仓库缓存：`~/.bensz-skills/installation/cache/remote-sources/`，重复远程更新时通过浅 fetch 增量更新；缓存损坏、GitHub reset 或 sparse 超时会自动重试，已有可用缓存时会复用 last-known-good 缓存完成本轮安装。
- 远程源下载策略：`skills_path` 为 `.` 时浅克隆/浅 fetch 仓库根；`skills_path` 为子目录时优先 sparse checkout 该子目录；指定 `--skill` 时只 sparse checkout 目标 skill 目录。非 `--skill` 场景遇到 sparse/path 回退问题时才完整浅克隆。

## 参数速查

### 通用参数

| 参数 | 什么时候用 | 效果 |
|------|------------|------|
| `--codex` | 只想更新 Codex | 只写入 `~/.codex/skills/` |
| `--claude` | 只想更新 Claude Code | 只写入 `~/.claude/skills/` |
| `--skill NAME` | 只想处理指定 skill | 可重复传入，也可用逗号分隔，如 `--skill a,b` |

### 本地安装参数

| 参数 | 什么时候用 | 效果 |
|------|------------|------|
| `--dry-run` | 想先预览本地安装 | 打印将执行的动作，不实际安装 |
| `--force` | 想强制重装本地源中的 skill | 忽略 MD5 检查，重新复制目标 skill |
| `--source PATH` | 自动识别不到源目录，或要指定额外源 | 从指定 skills 根目录扫描并安装 |

### 远程安装参数

| 参数 | 什么时候用 | 效果 |
|------|------------|------|
| `--remote --check` | 想先看远程差异再确认 | 下载远程源、对比本地、询问是否安装 |
| `--remote --auto` | 想自动完成远程安装 | 下载远程源并自动安装/更新 |
| `--general` | 只处理通用技能源 | 过滤 `config.yaml` 中 id 为 `general` 的源 |
| `--research` | 只处理科研技能源 | 过滤 `config.yaml` 中 id 为 `research` 的源 |
| `--anthropic-docs` | 只处理 Anthropic 文档技能源 | 过滤 `config.yaml` 中 id 为 `anthropic-docs` 的源 |

## 备选用法（脚本/硬编码流程）

Prompt 调用是推荐用法。下面的脚本入口适合你明确知道要装什么、装到哪里时直接运行。

### 定位系统级安装器

```bash
# 优先使用 Codex 系统级安装器；没有时再使用 Claude Code 系统级安装器
CODEX_INSTALLER="$HOME/.codex/skills/install-bensz-skills/scripts/install.py"
CLAUDE_INSTALLER="$HOME/.claude/skills/install-bensz-skills/scripts/install.py"
if [ -f "$CODEX_INSTALLER" ]; then
  INSTALLER="$CODEX_INSTALLER"
elif [ -f "$CLAUDE_INSTALLER" ]; then
  INSTALLER="$CLAUDE_INSTALLER"
else
  echo "未找到系统级 install-bensz-skills 安装器" >&2
  exit 1
fi
```

### 本地安装

```bash
# 默认：同时安装到 Codex 和 Claude Code，仅更新有变化的 skill
python3 "$INSTALLER"

# 只安装到 Codex
python3 "$INSTALLER" --codex

# 只安装到 Claude Code
python3 "$INSTALLER" --claude

# 预览，不实际写入
python3 "$INSTALLER" --dry-run

# 强制重装所有可安装 skill
python3 "$INSTALLER" --force
```

### 只安装/更新指定 skill

```bash
# 只处理一个 skill：不存在就安装，已存在就按 MD5 判断更新或跳过
python3 "$INSTALLER" --skill nsfc-bib-manager

# 只更新安装器自己
python3 "$INSTALLER" --skill install-bensz-skills

# 一次处理多个 skill
python3 "$INSTALLER" --skill git-commit --skill nsfc-bib-manager

# 也可以用逗号分隔
python3 "$INSTALLER" --skill git-commit,nsfc-bib-manager

# 只对 Codex 预览某个 skill 的安装/更新
python3 "$INSTALLER" --codex --dry-run --skill git-commit
```

### 指定源目录

```bash
# 显式指定一个 skills 根目录
python3 "$INSTALLER" --source /path/to/skills/alpha

# 显式安装 beta（默认不会扫描）
python3 "$INSTALLER" --source /path/to/skills/beta

# 指定多个 skills 根目录
python3 "$INSTALLER" --source /path/skills-a,/path/skills-b

# 仅在迁移旧仓库时显式启用历史 pipelines/skills/alpha
python3 "$INSTALLER" --legacy-source
```

### 远程安装

#### 快速版本更新（推荐给自动化流程）

如果只是希望“远程版本更高才更新”，直接运行独立的快速检查脚本。它从 GitHub 获取权威目录清单，并发读取版本；配置了 Gitee 镜像的源优先走 Gitee Raw，失败自动回退 GitHub。只有版本证据完整且远程版本更高（或本地缺失）时，才调用现有远程自动安装器。

```bash
# 默认检查并更新 URL、名称或 ID 包含 huangwb8 的远程源
python3 "$INSTALLER_DIR/update_remote_skills.py"

# 只检查，不安装
python3 "$INSTALLER_DIR/update_remote_skills.py" --check-only

# 检查全部 remote_sources，或指定源匹配字符串
python3 "$INSTALLER_DIR/update_remote_skills.py" --all-sources
python3 "$INSTALLER_DIR/update_remote_skills.py" --source-contains huangwb8

# 只处理指定 skill / 平台
python3 "$INSTALLER_DIR/update_remote_skills.py" --skill nsfc-bib-manager --codex
```

该机制**仅影响远程安装**。本地安装一般来自用户 fork 的完整仓库，继续沿用本地安装器的 MD5 检查，不增加远程版本约束。

```bash
# 远程检查模式：下载、对比、确认后安装
python3 "$INSTALLER" --remote --check

# 远程自动模式：下载后自动安装/更新
python3 "$INSTALLER" --remote --auto

# 只检查并安装 research 源
python3 "$INSTALLER" --remote --check --research

# 只从 general 源安装/更新 git-commit
python3 "$INSTALLER" --remote --check --general --skill git-commit

# 只对 Claude Code 自动安装 anthropic-docs 源
python3 "$INSTALLER" --remote --auto --anthropic-docs --claude
```

### 清理 legacy skill 名称

安装前会自动读取 `config.yaml` 中的 `legacy_skill_names` 并清理旧名。你也可以单独运行清理脚本：

当前清理名单包含若干历史命名，例如 `get-review-theme`、`guide-updater`、`check-review-alignment`、`make-research-plan`、`systematic-literature-review`，已弃用的 `nsfc-roadmap`、`nsfc-schematic`，以及已由 `write-readme` 吸收的 `write-skill-readme`。这些旧名不再保留系统级目录。

```bash
# 同时清理 Codex 和 Claude Code
python3 "${INSTALLER%install.py}remove_legacy_skills.py"

# 只清理 Codex
python3 "${INSTALLER%install.py}remove_legacy_skills.py" --codex

# 只预览 Claude Code 的清理动作
python3 "${INSTALLER%install.py}remove_legacy_skills.py" --claude --dry-run
```

## 工作原理

- 安装器只扫描包含 `SKILL.md` 的顶级 skill 目录。
- `category: normal` 的 skill 会被安装；`auxiliary` 和 `test` 类型不会安装。
- 当前版本的 `install-bensz-skills` 自身也是 `normal` skill，因此全量安装或 `--skill install-bensz-skills` 都可以更新它自己。
- 每个 skill 会计算可安装文件的 MD5，未变化则跳过，变化则删除旧目录并复制新目录。
- skill 根目录下的 `README.md` 和 `CHANGELOG.md` 不会安装进系统级目录，避免把面向人类的文档带进 AI 技能上下文。
- `--skill` 只是过滤“要处理哪些 skill”，不会改变安装/更新判断逻辑。

## 常见问题

### Q：只想更新某一个 skill，要用安装参数还是更新参数？

A：只需要 `--skill skill-name`。安装器会自己判断：系统级目录里没有就新安装，有但内容变了就更新，内容没变就跳过。

### Q：`--skill` 可以和远程安装一起用吗？

A：可以。例如 `python3 "$INSTALLER" --remote --check --general --skill git-commit` 会只检查 `general` 源中的 `git-commit`。

### Q：安装器自己会被更新吗？

A：会。当前版本的 `install-bensz-skills` 自身也是可安装对象。全量安装会顺带更新它；只想更新它自己时，可以用 `python3 "$INSTALLER" --skill install-bensz-skills`。

### Q：如果用户机器上的安装器太旧，不能更新自己怎么办？

A：用当前仓库里的新脚本做一次 bootstrap。完成这一次后，后续就能用系统级安装器正常自我更新。

```bash
# 从当前仓库的新脚本强制安装，包括更新 install-bensz-skills 自身
python3 /path/to/skills/alpha/install-bensz-skills/scripts/install.py --source /path/to/skills/alpha --force
```

### Q：`--check` 和 `--auto` 有什么区别？

A：`--check` 会先下载、对比并询问你是否安装；`--auto` 会自动安装/更新，不再逐步确认。

### Q：远程更新总是在某个 GitHub 源失败怎么办？

A：安装器会自动重试 GitHub 传输错误；若已有可用缓存，会先用缓存完成本轮安装，避免一次 GitHub reset 触发完整重下。若某个源仍持续失败，可以先用源过滤参数只更新其它源，例如 `--remote --check --general`；也可以删除 `~/.bensz-skills/installation/cache/remote-sources/` 后重试。网络链路本身不稳定时，仍建议配置 Git 代理。

### Q：`--dry-run` 有什么意义？

A：它用于本地安装预览，可以先告诉你哪些 skill 会安装、更新或跳过，适合正式运行前确认影响范围。远程安装想先预览时，用 `--remote --check`。

### Q：安装后为什么需要新会话？

A：Codex / Claude Code 通常在会话开始时加载可用 skill。安装或更新后，新建会话更容易看到最新版本。

### Q：为什么不是软链接？

A：复制安装更稳定，系统级目录里的 skill 不依赖当前仓库路径，跨项目使用时更不容易失效。

### Q：远程技能与本地同名技能冲突怎么办？

A：同名 skill 会按 MD5 对比并覆盖更新。想先看影响范围时，用 `--remote --check` 做远程对比和确认。

### Q：如何回退到旧版本？

A：在源仓库用 Git 回退到旧版本后重新运行安装器即可。安装器本身不备份旧目录。

### 静默更新（后台入口）

```bash
python3 "$INSTALLER" --silent-update
# 只有标准库 bootstrap 时：
python3 /path/to/bootstrap_install.py --silent-update
```

静默入口按 72 小时 TTL 限制远程检查，默认只更新 `general`/`skills/alpha` 中已安装的生产 Skill，并按 Codex 与 Claude Code 分别处理。它不会安装新 Skill、扫描 beta/legacy 或扩展用户额外源；旧版安装器会先由 bootstrap 安全升级自身。运行状态和失败摘要保存在 `~/.bensz-skills/installation/state/silent-update.json`。
