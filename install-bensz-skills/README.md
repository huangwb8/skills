# install-bensz-skills

这个 skill 用来把当前仓库里的 skills 复制安装到系统级目录，让它们在任意项目里都能被发现和触发；如果你只是想在当前仓库里临时试用，不一定需要先执行它。

## 用法

### 最推荐用法

```text
请使用 install-bensz-skills skill 将当前仓库中的 skills 安装到系统级目录，确保它们能在任意项目中被发现。
输入：当前 skills 仓库；必要时指定目标平台或额外 source
输出：安装结果报告，以及系统级 skills 目录中的最新技能副本
```

### 进阶用法

```text
请使用 install-bensz-skills skill 安装并更新这批 skills。
输入：当前 skills 仓库
输出：系统级安装结果
另外，还有下列参数约束：
- 仅安装到 Codex：是
- 只安装远程 research 源：是
- 先 dry-run 再正式安装：是
```

## 能做什么

- 把 skill 复制安装到 `~/.codex/skills/` 和 `~/.claude/skills/`。
- 用 MD5 判断哪些 skill 真正发生了变化，避免无意义重装。
- 根据 `config.yaml` 中的 `legacy_skill_names` 自动清理已弃用的旧 skill 名称。
- 支持本地仓库安装、远程 GitHub 安装、平台定向安装和 dry-run 预览。
- 让 skill 的可发现性不再依赖“当前 workdir 恰好在这个仓库里”。
- 不适合当作普通的 README 浏览器或项目构建工具使用。

## 使用示例

### 示例 1：本地仓库一次性安装

```text
请使用 install-bensz-skills skill 将当前仓库中的 skills 安装到系统级目录。
输入：当前 skills 仓库
输出：安装结果报告
```

### 示例 2：只安装到某个平台

```text
请使用 install-bensz-skills skill 安装这些 skills。
输入：当前 skills 仓库
输出：系统级安装结果
另外，还有下列参数约束：
- 仅安装到 Claude Code：是
```

### 示例 3：远程安装

```text
请使用 install-bensz-skills skill 从远程仓库安装技能。
输入：远程源配置
输出：下载并安装后的技能
另外，还有下列参数约束：
- 只安装 `anthropic-docs`
- 交互检查模式：是
```

## 输出

- 系统级 skill 副本，默认安装到：
  - `~/.codex/skills/`
  - `~/.claude/skills/`
- 运行期工作目录统一放在 `~/.bensz-skills/installation/`，其中安装历史记录位于 `~/.bensz-skills/installation/manifests/`。
- 安装过程中的更新、跳过和失败信息。
- dry-run 模式下只打印动作，不写文件。
- 远程安装时会创建并清理临时目录。

## 配置

- 配置文件：`install-bensz-skills/config.yaml`
- 关键配置节：
  - `remote_sources`
  - `legacy_skill_names`
- 高频参数：
  - `--codex`
  - `--claude`
  - `--force`
  - `--dry-run`
  - `--remote`
  - `--check`
  - `--auto`

## 备选用法（脚本/硬编码）

这个 skill 的脚本入口是高频主用法之一，适合你明确知道自己要装什么、装到哪里时直接使用。脚本入口应直接来自系统级 skill 目录，不再先检查当前项目目录是否存在本地安装脚本。

### 定位系统级安装器

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

### 本地安装

```bash
python3 "$INSTALLER"
python3 "$INSTALLER" --codex
python3 "$INSTALLER" --claude
python3 "$INSTALLER" --dry-run
python3 "$INSTALLER" --force
```

### 指定额外源目录

```bash
python3 "$INSTALLER" --source /path/to/skills
```

### 仅清理 legacy skill 名称

```bash
python3 "${INSTALLER%install.py}remove_legacy_skills.py"
python3 "${INSTALLER%install.py}remove_legacy_skills.py" --codex
python3 "${INSTALLER%install.py}remove_legacy_skills.py" --claude --dry-run
```

### 远程安装

```bash
python3 "$INSTALLER" --remote --check
python3 "$INSTALLER" --remote --auto
python3 "$INSTALLER" --remote --check --research
```

## 常见问题

### Q：为什么安装后在任意项目里更容易触发这些 skill？

A：因为系统级目录会被工具统一扫描，而不再依赖你当前正好位于 skill 仓库内。

### Q：`--dry-run` 有什么意义？

A：它可以先告诉你哪些 skill 会安装、更新或跳过，避免误操作。

### Q：远程安装和本地安装有什么区别？

A：本地安装直接复制你当前仓库里的 skill；远程安装会先从配置里的 GitHub 源下载再安装。

### Q：skill 改名后，为什么旧名字也会被清理？

A：因为安装器现在会读取 `legacy_skill_names`，把这些已弃用目录从系统级 skills 目录里删掉，避免旧名继续误触发。

### Q：为什么不是软链接？

A：这个 skill 的定位是“复制安装”，目的是提升兼容性和独立性，避免链接失效或环境差异问题。
