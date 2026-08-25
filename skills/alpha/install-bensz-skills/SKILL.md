---
name: install-bensz-skills
category: normal
description: "当需要把本仓库 skills/alpha 下的生产 skills 安装到系统级（默认同时安装到 Codex: ~/.codex/skills 和 Claude Code: ~/.claude/skills），以便在任意项目/对话中可被发现与调用时使用。默认不安装 skills/beta；只有显式指定 beta 源目录时才处理 beta skill。使用 MD5 哈希进行版本控制，仅安装有更新的 skills；支持 --skill 指定单个或少量技能安装/更新、强制覆盖安装、指定单一目标安装和远程安装模式（--remote --check/--auto）。"
metadata:
  author: Bensz Conan
  keywords:
    - install-bensz-skills
---

# Install Bensz Skills（系统级安装器）

## BenszAPI 任务工作区

本 Skill 的新任务中间文件统一写入 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/{skill名}/input|output|log/`。同一任务复用一个任务根目录；多 Skill 协作才创建 `shared/`。正式交付物不写入该目录，历史隐藏目录只允许显式兼容读取、迁移或清理。

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求“report bensz skills bugs”等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

目的：把当前仓库 `skills/alpha/` 中的生产 skills（**包括 install-bensz-skills 自身**）**复制安装**到：

- Codex：`~/.codex/skills/`
- Claude Code：`~/.claude/skills/`

从而让这些 skills 在**任意项目**里都能被发现与触发（不依赖当前 workdir，也不使用软链接）。

## 安装模式

### 本地安装模式（默认）

直接从本地仓库安装 skills。

### 远程安装模式

从远程 GitHub 仓库下载并安装 skills，支持交互式确认和自动强制安装。

#### 远程安装前置条件

- 本地已安装 Git（`git --version` 可用）
- 具备 PyYAML 依赖（`python3 -m pip install pyyaml`）

#### 标准库 bootstrap 安装

本 Skill 内置 `scripts/bootstrap_install.py`，它整合了原根级 `@install/install.py` 的无第三方依赖远程引导能力。首次安装或无法使用 Git/PyYAML 时，可从 GitHub 下载本文件后直接运行；其 `general` 源固定为 `skills/alpha`，不会安装 beta：

```bash
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())"
```

## 你要做的事（触发后必须执行）

执行时不要检查当前项目目录下是否存在 `./install-bensz-skills/scripts/install.py`，也不要把本地脚本作为优先入口。触发本 skill 后，直接从系统级已安装位置查找安装器脚本：优先 `~/.codex/skills/install-bensz-skills/scripts/install.py`，其次 `~/.claude/skills/install-bensz-skills/scripts/install.py`。安装源目录默认自动识别当前仓库的 `./skills/alpha/`；`./skills/beta/` 永不自动选中，只有用户明确传入 `--source ./skills/beta`（或其它 beta 根目录）时才允许安装 beta。

### 本地安装

1) 先定位系统级安装器脚本：

```bash
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

2) 运行安装脚本：

```bash
# 默认：同时安装到 Codex 和 Claude Code（仅安装有更新的）
# 说明：脚本默认只自动识别 ./skills/alpha；beta 必须显式 --source
python3 "$INSTALLER"

# 仅安装到 Claude Code
python3 "$INSTALLER" --claude

# 仅安装到 Codex
python3 "$INSTALLER" --codex

# 强制重新安装所有 skills（忽略版本检查）
python3 "$INSTALLER" --force

# 仅安装/更新指定 skill（不存在则新安装，已存在则按 MD5 判断更新或跳过）
python3 "$INSTALLER" --skill nsfc-bib-manager

# 预览模式（不实际安装）
python3 "$INSTALLER" --dry-run

# 指定额外 skills 源目录
python3 "$INSTALLER" --source /path/to/skills

# 显式安装 beta（不会被默认扫描）
python3 "$INSTALLER" --source ./skills/beta

# 多个源目录（逗号分隔）
python3 "$INSTALLER" --source /path/skills-a,/path/skills-b
```

也可以直接运行某个系统级脚本路径：

```bash
# Codex 安装位置（优先）
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py

# 或 Claude Code 安装位置
python3 ~/.claude/skills/install-bensz-skills/scripts/install.py

# 若无法自动识别源目录，则显式指定 alpha
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py --source ./skills/alpha
```

### 远程安装

远程 `general` 源固定指向仓库的 `skills/alpha`，因此 bootstrap 与 Git 远程模式都不会下载或安装 beta。其它远程源沿用各自配置的生产 skills 路径。

**交互式检查模式**（`--remote --check`）：

```bash
# 检查并交互式安装远程技能
python3 "$INSTALLER" --remote --check

# 仅对 Claude Code 执行远程检查
python3 "$INSTALLER" --remote --check --claude

# 仅对 Codex 执行远程检查
python3 "$INSTALLER" --remote --check --codex
```

流程：
1. 创建临时目录 `~/.bensz-skills/installation/tmp-remote-install`
2. 询问是否安装每个远程源（根据配置文件）
3. 下载远程技能到本地缓存并更新工作树；重复运行时优先复用 `~/.bensz-skills/installation/cache/remote-sources/` 中的缓存 repo，通过浅 fetch 增量更新。当远程源配置了非根目录 `skills_path` 时，优先使用 Git sparse checkout 只拉取目标子目录；若同时指定 `--skill`，进一步只拉取 `skills_path/<skill-name>` 目录；GitHub 传输 reset/timeout 会自动重试，已有可用缓存时会复用 last-known-good 缓存完成本轮安装，缓存不可用时再重建或回退到完整浅克隆
4. 与本地已安装技能对比，生成更新报告
5. 询问是否确认安装/更新
6. 执行安装/更新
7. 清理临时目录

**自动强制模式**（`--remote --auto`）：

```bash
# 自动下载并强制安装所有远程技能（无确认）
python3 "$INSTALLER" --remote --auto

# 仅对 Claude Code 执行自动安装
python3 "$INSTALLER" --remote --auto --claude

# 仅安装/更新远程源中的指定 skill
python3 "$INSTALLER" --remote --check --general --skill git-commit
```

流程：
1. 创建临时目录
2. 直接更新远程技能缓存（无确认）；非根目录 `skills_path` 优先只拉取目标子目录，指定 `--skill` 时只拉取目标 skill 目录
3. 强制安装/更新（无对比，无确认）
4. 清理临时目录

### Legacy 技能清理

安装前会先读取 `install-bensz-skills/config.yaml` 中的 `legacy_skill_names`，并从 `~/.codex/skills/` / `~/.claude/skills/` 删除这些已弃用旧名，避免 skill 改名后旧目录继续留在系统级目录里干扰触发。

研究类 skill 重命名后，旧目录 `get-review-theme`、`guide-updater`、`check-review-alignment`、`make-research-plan`、`systematic-literature-review` 也属于 legacy 清理对象；兼容性由新 `research-*` skills 的触发描述承担。已弃用的 `nsfc-roadmap`、`nsfc-schematic` 也会作为 legacy 目录清理。

如果只想单独执行清理，可直接运行：

```bash
python3 "${INSTALLER%install.py}remove_legacy_skills.py"
python3 "${INSTALLER%install.py}remove_legacy_skills.py" --codex
python3 "${INSTALLER%install.py}remove_legacy_skills.py" --claude --dry-run
```

### 验证

建议在任意其它目录执行：

```bash
codex exec "列出所有可用的技能"
```

## MD5 版本控制机制

脚本使用 **MD5 哈希值**进行智能版本控制：

- **版本计算**：对 skill 目录内的可安装文件进行 MD5 计算（排除 `tests/`、`plans/`、缓存与临时文件，以及 skill 根目录下给人看的 `README.md` / `CHANGELOG.md`）
- **版本存储**：安装后在目标目录生成平台特定 manifest（`.skill-manifest.{codex,claude}.json`）记录版本信息
- **智能安装**：
  - ✅ **已安装且版本未变**：跳过，不重复安装
  - ✅ **版本已变化**：强制覆盖安装
  - ✅ **新 skill**：直接安装

### 安装报告示例

```
============================================================
📦 正在安装到 CLAUUDE: /Users/xxx/.claude/skills
============================================================

【安装过程】
────────────────────────────────────────────────────────────
installed: /Users/xxx/.claude/skills/nsfc-bib-manager

【安装摘要】
────────────────────────────────────────────────────────────
┌────────────────────────┬──────────────┬─────────────────┐
│ Skill 名称              │ 状态         │ 原因            │
├────────────────────────┼──────────────┼─────────────────┤
│ nsfc-bib-manager        │ ✅ 已安装    │ 版本已更新...  │
│ git-commit              │ ⏭️  跳过     │ 版本未变化     │
└────────────────────────┴──────────────┴─────────────────┘

【辅助技能（已忽略，仅用于开发）】(1 个)
   • install-bensz-skills ⏭️ 跳过

────────────────────────────────────────────────────────────
📊 统计
────────────────────────────────────────────────────────────
普通技能: 1 个已安装, 1 个跳过

============================================================
🎯 总体安装摘要
============================================================

总计数:
  • 已安装/更新: 1 个
  • 跳过: 1 个
```

**注**：完整报告格式规范见 [references/install-report-template.md](references/install-report-template.md)。

## 安装策略（脚本保证）

- 仅安装"包含 `SKILL.md` 的目录"（即每个 skill 的根目录）。
- skill 根目录下的 `README.md`、`CHANGELOG.md` 不会被复制到系统级目录，避免把面向人的说明文档带进 AI 的技能上下文。
- **技能类型控制**：通过 SKILL.md 中的 `category` 字段控制（`normal` 可安装，`auxiliary` 和 `test` 不安装）。
- **MD5 版本检查**：优先检查 `.skill-manifest.{codex,claude}.json`，回退到重新计算
- **直接替换**：发现到目标路径已存在同名目录且版本变化时，直接删除旧版本并安装新版本（不备份）
  - 理由：Git 已提供版本控制，可随时回退；新版本通常比旧版本更好
- 若存在旧的 `pipeline-skills` 软链接：会移除该软链接（不删除真实目录）。
- 若 `config.yaml` 声明了 `legacy_skill_names`：安装前会先删除这些已弃用旧 skill 名称对应的系统级目录。

## 命令行参数

### 本地安装参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 预览模式，不实际写入文件 |
| `--codex` | 仅安装到 Codex |
| `--claude` | 仅安装到 Claude Code |
| `--force` | 强制重新安装所有 skills（忽略 MD5 检查） |
| `--skill` | 仅安装/更新指定 skill；可重复传入，也可用逗号分隔 |
| `--source` | 指定额外的 skills 源目录路径 |

### 远程安装参数

| 参数 | 说明 |
|------|------|
| `--remote` | 启用远程安装模式（必须与 `--check` 或 `--auto` 一起使用） |
| `--check` | 检查模式（交互式确认后再安装） |
| `--auto` | 自动模式（强制安装，无需确认） |
| `--{id}` | 仅安装指定远程源（如 `--general`、`--research`） |

**参数组合**：
- `--remote --check`：交互式远程安装
- `--remote --auto`：自动强制远程安装
- `--remote --check --codex`：仅对 Codex 执行远程检查
- `--remote --check --claude`：仅对 Claude Code 执行远程检查
- `--remote --check --general`：仅检查并安装 general 源
- `--remote --check --general --skill git-commit`：仅检查并安装/更新 general 源中的 `git-commit`

### 远程源配置

远程技能源通过 `config.yaml` 配置文件定义：

```yaml
# install-bensz-skills/config.yaml
remote_sources:
  - id: "general"
    name: "通用技能"
    url: "https://github.com/huangwb8/skills"
    branch: "main"
    skills_path: "skills/alpha"
    description: "通用技能，建议所有用户安装"
    recommended: true

  - id: "research"
    name: "科研技能"
    url: "https://github.com/huangwb8/ChineseResearchLaTeX"
    branch: "main"
    skills_path: "skills"
    description: "科研相关技能，建议有科研需要的用户安装"
    recommended: true

legacy_skill_names:
  - "make_latex_model"
  - "transfer_old_latex_to_new"
  - "write-paper-sci"
  - "explain-figures"
  - "complete_example"
  - "get-review-theme"
  - "guide-updater"
  - "check-review-alignment"
  - "make-research-plan"
  - "systematic-literature-review"
  - "nsfc-roadmap"
  - "nsfc-schematic"
```

配置字段说明：
- `id`：源 ID（用于 `--{id}` 过滤）
- `name`：源名称（用于显示和提示）
- `url`：Git 仓库 URL
- `branch`：分支名称（默认 `main`）
- `skills_path`：技能目录相对于仓库根目录的路径

本仓库的 `general` 源必须写为 `skills/alpha`；不要改成仓库根目录或 `skills/beta`。beta 仅允许通过本地 `--source` 显式安装。
如果 `skills_path` 指向子目录（如 `skills`），安装器会优先用 Git sparse checkout 只下载该子目录，避免把仓库中与 skill 无关的大文件一并拉取。指定 `--skill` 时，下载范围会进一步收窄到 `skills_path/<skill-name>`；如果某个源中没有该 skill，不再为了确认缺失而完整下载该源。远程 repo 会缓存在 `~/.bensz-skills/installation/cache/remote-sources/`，后续运行用 `git fetch --depth 1` 增量更新；缓存损坏、GitHub 连接 reset 或 sparse checkout 超时时会自动重试。若更新失败但缓存中仍有可安装 skill，安装器会复用 last-known-good 缓存完成本轮安装；只有缓存不可用或非 `--skill` 场景需要路径回退识别时，才重建缓存或回退到完整浅克隆。
- `description`：源描述（用于提示用户）
- `recommended`：是否推荐安装（影响默认提示行为）
- `legacy_skill_names`：需要从系统级目录主动清理的旧 skill 名称列表

## 常见问题

### 本地安装

- **如果你刚更新了本仓库的技能**：再次触发本 skill 运行脚本即可完成系统级更新（仅安装有变化的）。
- **只想更新一个 skill**：使用 `--skill skill-name`；目标不存在时会新安装，目标已存在时仍按 MD5 判断更新或跳过。
- **需要强制重装**：使用 `--force` 参数。
- **Claude Code / Codex 都需要新会话**才会重新加载更新后的技能；安装后建议新建会话验证。
- **如何回退到旧版本**：使用 Git 回退源代码后，重新运行安装脚本即可（不备份旧版本）。

### 远程安装

- **如何添加新的远程源**：编辑 `config.yaml`，在 `remote_sources` 数组中添加新的源配置。
- **远程安装失败**：安装器会自动重试 GitHub 传输错误；若已有可用缓存，会先用缓存完成本轮安装，避免一次 GitHub reset 导致完整重下。若某个源仍失败，可先用 `--general`、`--research` 等源过滤参数只更新可连通的源，或删除 `~/.bensz-skills/installation/cache/remote-sources/` 后重试。某些网络环境仍可能需要配置 Git 代理。
- **临时目录未清理**：手动删除 `~/.bensz-skills/installation/tmp-remote-install` 目录。
- **安装记录、缓存与临时目录在哪里**：统一保存在 `~/.bensz-skills/installation/` 下；其中 manifest 在 `~/.bensz-skills/installation/manifests/`，远程仓库缓存位于 `~/.bensz-skills/installation/cache/remote-sources/`，远程安装临时目录在 `~/.bensz-skills/installation/tmp-remote-install`。
- **远程技能与本地冲突**：远程安装会覆盖本地同名技能，建议先备份或使用 `--check` 模式预览变更。
