<div align="center">

# Skills 开发流水线

[![Version](https://img.shields.io/github/v/tag/huangwb8/skills?label=version&sort=semver)](https://github.com/huangwb8/skills/releases)
[![Standard](https://img.shields.io/badge/Agent%20Skills-Standard%20v1.0-blue.svg)](https://agentskills.io)
[![Platforms](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Codex%20%7C%20Cursor-lightgrey.svg)](#平台兼容性)
[![Built with](https://img.shields.io/badge/built%20with-Python%203.10%2B-orange.svg)](https://www.python.org/)

[中文](README.md) | [English](README_EN.md)

<strong>遵循 Agent Skills 开放标准的可复用 AI 技能库</strong>

</div>

统一的 AI 技能开发流水线，维护符合 [Agent Skills 开放标准](https://agentskills.io) 的可复用技能，实现跨平台无缝兼容。技能遵循**一次编写，到处运行**原则——在 Claude Code、OpenAI Codex、Cursor 及其他兼容平台上表现完全一致。

## 核心特性

- **🔄 统一技能库** – 单一代码库支持多个 AI 平台
- **📋 开放标准** – 遵循 [agentskills.io](https://agentskills.io) 规范
- **🚀 系统级安装** – 通过安装器使技能在任何项目中可用
- **🎯 有机更新** – 遵循 SOLID、KISS、YAGNI、DRY 原则
- **📚 渐进披露** – 三层架构：元数据 → 操作 → 知识
- **🔍 语义发现** – 基于自然语言意图触发技能

## 平台兼容性

| 平台 | 状态 | 安装路径 |
|------|------|----------|
| [Claude Code](https://code.anthropic.com) | ✅ 原生支持 | `~/.claude/skills/` |
| [OpenAI Codex](https://openai.com/index/introducing-codex/) | ✅ 原生支持 | `~/.codex/skills/` |
| Cursor | ✅ 兼容 | `~/.cursor/skills/` |
| GitHub | ✅ 兼容 | `.github/skills/` |
| VS Code | ✅ 兼容 | `.vscode/skills/` |

## 推荐开发环境

### 💡 VS Code + Claude Code / Codex 插件

为获得最佳技能开发体验，我们推荐使用 **VS Code** 配合 **Claude Code** 或 **Codex** 插件。

**为什么选择这个组合？**

| 优势 | 说明 |
|------|------|
| **🎯 原生技能集成** | 插件自动从 `~/.claude/skills/` 或 `~/.codex/skills/` 加载技能 |
| **⚡ 实时验证** | 使用自然语言提示即时测试技能触发 |
| **🔍 上下文感知编辑** | AI 理解项目结构并应用有机更新原则 |
| **🛠️ 集成工作流** | 无需上下文切换——编辑、测试、迭代在同一环境 |
| **📝 智能文档维护** | AI 帮助维护 SKILL.md、README.md 和 config.yaml 之间的表头-正文一致性 |

<iframe src="//player.bilibili.com/player.html?isOutside=true&aid=116055804483400&bvid=BV1tpcezbERB&cid=36003450097&p=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"></iframe>

### AI算力

大家看这个视频即可：

<iframe src="//player.bilibili.com/player.html?isOutside=true&aid=116067800191453&bvid=BV1a7ZLBuE5z&cid=36055748012&p=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"></iframe>

## 项目结构

```
skills/
├── AGENTS.md              # 核心项目指令（工程原则）
├── CLAUDE.md              # Claude Code 特定配置
├── README.md              # 中文说明（本文件）
├── README_EN.md           # 英文说明
│
├── @install/              # 快速安装脚本（一键安装）
│   ├── install.sh        # macOS/Linux/WSL
│   ├── install.ps1       # Windows PowerShell
│   ├── install.bat       # Windows CMD
│   └── README.md         # 安装说明
│
├── init-project/          # 技能：项目文档生成器
│   ├── SKILL.md          # 技能定义（面向 AI）
│   ├── README.md         # 用户指南（面向人类）
│   ├── config.yaml       # 配置参数
│   ├── scripts/          # 自动化脚本
│   │   └── generate.py   # 生成 AGENTS.md + CLAUDE.md
│   └── templates/        # 文档模板
│
├── install-bensz-skills/  # 技能：系统级安装器
│   ├── SKILL.md          # 技能定义
│   ├── README.md         # 用户指南
│   ├── CHANGELOG.md      # 更新日志
│   ├── config.yaml       # 配置参数
│   └── scripts/          # 安装脚本
│
├── git-commit/            # 技能：智能 Git 提交
│   ├── SKILL.md          # 技能定义
│   ├── README.md         # 用户指南
│   └── scripts/          # 自动化脚本
│
├── git-publish-release/   # 技能：GitHub 发布
│   ├── SKILL.md          # 技能定义
│   ├── README.md         # 用户指南
│   └── scripts/          # 自动化脚本
│
├── auto-test-skill/       # 技能：技能级自动测试
│   ├── SKILL.md          # 技能定义
│   ├── README.md         # 用户指南
│   ├── config.yaml       # 配置参数
│   └── scripts/          # 测试脚本
│
├── auto-test-project/     # 技能：项目级自动测试
│   ├── SKILL.md          # 技能定义
│   ├── README.md         # 用户指南
│   └── config.yaml       # 配置参数
│
├── write-skill-readme/    # 技能：技能文档生成器
│   ├── SKILL.md          # 技能定义
│   ├── README.md         # 用户指南
│   └── config.yaml       # 配置参数
│
├── awesome-code/          # 技能：多代理协作开发
│   ├── SKILL.md          # 技能定义
│   ├── README.md         # 用户指南
│   └── config.yaml       # 配置参数
│
├── better-prompt/         # 技能：Prompt 优化
│   ├── SKILL.md          # 技能定义
│   ├── README.md         # 用户指南
│   └── config.yaml       # 配置参数
│
└── parallel-vibe/         # 技能：并行 Vibe Coding
    ├── SKILL.md          # 技能定义
    ├── README.md         # 用户指南
    └── config.yaml       # 配置参数
```

## 快速开始

### 🚀 如何安装本项目的 skill

#### 方法一：一键快速安装（推荐）

**无需克隆项目，一行命令完成安装！**

| 平台 | 命令 |
|------|------|
| **macOS / Linux / WSL** | `curl -fsSL https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.sh \| bash` |
| **Windows PowerShell** | `irm https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.ps1 \| iex` |

安装完成后，技能将自动安装到：
- `~/.claude/skills/` (Claude Code)
- `~/.codex/skills/` (OpenAI Codex)

#### 方法二：本地安装

**第一步：克隆本项目**

```bash
git clone https://github.com/huangwb8/skills.git
cd skills
```

**第二步：本项目的根目录打开 Claude Code 或 Codex，输入：**

> `"install-bensz-skills 这个 skill 将本项目里的 skill 安装到 Codex 和 Claude Code 里"`

就这么简单！所有 skill 将被安装到系统级，可在任何项目中使用。

#### 方法三：手动安装

```bash
# 进入项目目录
cd skills

# 运行安装脚本
python3 install-bensz-skills/scripts/install.py --claude --codex
```

### 🎯 如何使用本项目的 skills

**在 Claude Code 或 Codex 中打开本项目，直接使用自然语言触发技能：**

```text
# 项目初始化
"init-project 这个 skill 帮我初始化项目"

# 系统级安装
"install-bensz-skills 这个 skill 将本项目里的 skill 安装到 Codex 和 Claude Code 里"

# 自动化测试
"auto-test-skill 这个 skill 帮我测试 init-project 这个 skill"

# 技能文档生成
"write-skill-readme 这个 skill 帮我生成技能的 README.md"

# Prompt 优化
"better-prompt 这个 skill 帮我优化这个 prompt"

# 多代理协作
"awesome-code 这个 skill 帮我通过多代理协作开发"

# 并行 Vibe Coding
"parallel-vibe 这个 skill 帮我并行执行多个方案"
```

**就是这么简单！** 自然语言编程才是 Vibe Coding 的灵魂！

## 技能开发

### 文件结构

```
my-skill/
├── SKILL.md           # 必需：AI 指令（包含 YAML frontmatter）
├── README.md          # 推荐：用户指南
├── config.yaml        # 推荐：配置参数
├── CHANGELOG.md       # 可选：版本历史
├── references/        # 可选：详细文档
│   └── advanced-guide.md
└── scripts/           # 可选：自动化脚本
    └── process.py
```

### 快速创建

```bash
mkdir my-new-skill
cd my-new-skill
touch SKILL.md README.md config.yaml
```

### 架构层次

| 层次 | 文件/目录 | 用途 | 加载时机 |
|------|----------|------|----------|
| **元数据层** | YAML Frontmatter | 技能发现与激活 | 会话启动时 |
| **操作层** | SKILL.md | AI 执行指令 | 技能触发时 |
| **知识层** | references/ | 详细背景和理论 | 按需加载 |
| **工具层** | scripts/ | 自动化和计算 | 需要时调用 |

### 最佳实践

- **YAML Frontmatter** – 保持 `description` 清晰且语义化
- **渐进披露** – 保持 SKILL.md 精简（<500 行），详细内容移至 references/
- **表头-正文一致性** – 同步元数据与实际行为
- **延迟加载** – 启动时不要加载所有内容
- **平台无关** – 尽可能避免平台特定代码

完整的开发指南请参阅 [AGENTS.md](AGENTS.md)。

## 贡献指南

欢迎贡献！请确保：

1. **遵循标准** – 符合 [agentskills.io](https://agentskills.io)
2. **完整文档** – 至少包含 SKILL.md + README.md
3. **有机更新** – 保持表头-正文一致性
4. **跨平台测试** – 如可能，在 Claude Code 和 Codex 上验证

## 资源链接

- [Agent Skills 开放标准](https://agentskills.io)
- [AGENTS.md](AGENTS.md) – 项目指令和哲学
- [CLAUDE.md](CLAUDE.md) – Claude Code 特定说明
- [技能目录](https://github.com/huangwb8/skills) – 浏览所有技能

## 许可证

MIT License – 详见 [LICENSE](LICENSE)。
