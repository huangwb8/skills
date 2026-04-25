# Init Project

这个 skill 用来为当前项目初始化标准化的 AI 协作文档和基础仓库文件，适合新项目起步或已有项目补齐指令体系；它只应该在当前项目目录内工作，不应越界修改其它目录。

## 用法

### 最推荐用法

```text
请使用 init-project skill 为本项目进行初始化。
输入：当前项目根目录
输出：`AGENTS.md`、`CLAUDE.md`、`README.md`、`CHANGELOG.md`、`.gitignore`、`docs/`、`docs/plans/`
```

### 进阶用法

```text
请使用 init-project skill 为本项目进行初始化。
输入：当前项目根目录
输出：标准化项目指令与说明文档
另外，还有下列参数约束：
- 尽量保留已有内容
- 默认语言自动检测
- 不修改当前目录之外的文件
```

## 能做什么

- 为项目生成 `AGENTS.md`、`CLAUDE.md`、`README.md`、`CHANGELOG.md`、`.gitignore`，并初始化 `docs/` 与 `docs/plans/`。
- 把 `AGENTS.md` 作为跨平台通用指令的单一真相来源。
- 让 `CLAUDE.md` 成为面向 Claude Code 的轻量适配层。
- 自动分析项目结构、项目类型和默认语言。
- 不适合拿来扫描父目录、批量改多个项目，或无边界地覆盖已有文件。

## 使用示例

### 示例 1：初始化一个新项目

```text
请使用 init-project skill 为本项目进行初始化。
输入：当前项目根目录
输出：完整的项目指令文件与说明文档
```

### 示例 2：为已有项目补齐协作文档

```text
请使用 init-project skill 初始化这个已有仓库。
输入：当前项目根目录
输出：`AGENTS.md`、`CLAUDE.md`、`README.md`、`CHANGELOG.md`、`.gitignore`、`docs/`、`docs/plans/`
另外，还有下列参数约束：
- 尽量保留已有 README 的有效信息
- 不破坏现有项目结构
```

### 示例 3：只补某一类文档

```text
请使用 init-project skill 为本项目补齐说明文档。
输入：当前项目根目录
输出：README 或 CHANGELOG
另外，还有下列参数约束：
- 只更新 README
```

## 输出

- `AGENTS.md`：跨平台通用项目指令，应该被长期维护。
- `CLAUDE.md`：Claude Code 适配层，核心内容应与 `AGENTS.md` 保持一致。
- `README.md`：项目介绍、快速开始和目录说明。
- `CHANGELOG.md`：项目变更记录。
- `.gitignore`：默认的安全与项目类型忽略规则。
- `docs/`：项目文档根目录。
- `docs/plans/`：计划文档固定目录；其余 `docs/` 文档在代码变化时也应及时同步更新。

## 配置

- 配置文件：`init-project/config.yaml`
- 关键配置节：
  - `language_mapping`
  - `agents_required_sections`
  - `claude_required_sections`
  - `readme_required_sections`
  - `changelog_required_sections`
- 这个 skill 的默认定位是“完整初始化”，不是只生成一份孤立文档。

## 备选用法（脚本/硬编码）

如果你想直接在命令行下执行项目初始化，脚本入口最方便。

### 自动分析当前目录并生成文件

```bash
python3 init-project/scripts/generate.py --auto
```

### 自动分析并覆盖已有文件

```bash
python3 init-project/scripts/generate.py --auto --overwrite
```

### 只生成部分文档

```bash
python3 init-project/scripts/generate.py --auto --only-readme
python3 init-project/scripts/generate.py --auto --only-changelog
```

### 跳过部分输出

```bash
python3 init-project/scripts/generate.py \
  --auto \
  --skip-readme \
  --skip-changelog \
  --skip-gitignore
```

## 常见问题

### Q：`AGENTS.md` 和 `CLAUDE.md` 到底谁是主文件？

A：`AGENTS.md` 是单一真相来源；`CLAUDE.md` 是平台适配层。维护时应优先保证 `AGENTS.md` 的口径正确。

### Q：它会不会改到当前项目目录之外？

A：不应该。这个 skill 的边界就是“当前目录内生成或更新项目文件”。

### Q：既然是自动化，是不是可以放心覆盖任何已有文件？

A：不能这么理解。自动化不等于无脑覆盖。是否覆盖应由你显式决定，例如使用 `--overwrite`。

### Q：为什么 `.gitignore` 也算初始化结果的一部分？

A：因为它直接关系到项目安全和仓库整洁度，尤其能防止敏感文件、系统文件和缓存文件被误提交。
