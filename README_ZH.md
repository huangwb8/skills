<div align="center">

# Skills 开发流水线

[![Version](https://img.shields.io/github/v/tag/bensz/skills?label=version&sort=semver)](https://github.com/bensz/skills/releases)
[![Standard](https://img.shields.io/badge/Agent%20Skills-Standard%20v1.0-blue.svg)](https://agentskills.io)
[![Platforms](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Codex%20%7C%20Cursor-lightgrey.svg)](#平台兼容性)
[![Built with](https://img.shields.io/badge/built%20with-Python%203.10%2B-orange.svg)](https://www.python.org/)

[English](README.md) | [中文](README_ZH.md)

<strong>遵循 Agent Skills 开放标准的可复用 AI 技能库</strong>

</div>

统一的 AI 技能开发流水线。本项目维护了一系列符合 [Agent Skills 开放标准](https://agentskills.io) 的可复用 **Agent Skills**，实现跨平台无缝兼容。

技能遵循**一次编写，到处运行**原则——同一技能在 Claude Code、OpenAI Codex、Cursor 及其他兼容平台上表现完全一致。

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
| [OpenAI Codex](https://openai.com) | ✅ 原生支持 | `~/.codex/skills/` |
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

**安装步骤：**

```bash
# 1. 安装 VS Code
# 从 https://code.visualstudio.com/ 下载

# 2. 安装 Claude Code 插件（推荐）
# VS Code → 扩展 → 搜索 "Claude Code" → 安装

# 3. 系统级安装技能
python3 install-bensz-skills/scripts/install.py

# 4. 在 VS Code 中打开项目
code .

# 5. 打开 Claude Code 侧边栏开始开发！
```

**备选方案：** 如果您更喜欢基于终端的工作流，可使用独立的 Claude Code CLI。

## 项目结构

```
skills/
├── AGENTS.md              # 核心项目指令（工程原则）
├── CLAUDE.md              # Claude Code 特定配置
├── README.md              # 英文说明
├── README_ZH.md           # 中文说明（本文件）
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
│   └── scripts/          # 安装脚本
│       ├── install.py    # 核心安装逻辑
│       └── i18n.py       # 国际化支持
│
└── [更多技能]/           # 遵循相同结构的附加技能
```

## 快速开始

### 🚀 最快方法：AI 辅助安装（推荐）

只需在 **Claude Code** 或 **Codex** 中打开本项目并输入：

> "请安装本项目的 skills 到 codex 和 claude code 里"

AI 会自动检测 `install-bensz-skills/` 技能并为您执行安装。这是最简单的方法——无需手动输入命令。

### 📦 手动安装

如果您更喜欢手动安装或需要从终端运行：

```bash
# 克隆仓库
git clone https://github.com/bensz/skills.git
cd skills

# 运行安装器
python3 install-bensz-skills/scripts/install.py
```

安装器将：
- 复制技能到 `~/.claude/skills/` 和 `~/.codex/skills/`
- 使用 MD5 版本控制，仅更新有变化的技能
- 支持技能分类：普通、辅助、测试

### 📁 项目本地安装

仅需在单个项目中使用，无需系统级安装：

```bash
# 对于 Claude Code
mkdir -p .claude/skills
cp -r init-project .claude/skills/

# 对于 Codex
mkdir -p .codex/skills
cp -r init-project .codex/skills/
```

### ✅ 验证安装

在 AI 助手中启动新会话，使用触发短语测试：

**`init-project` 技能示例：**
> "帮我初始化一个新项目的 AI 上下文文件"

**`install-bensz-skills` 技能示例：**
> "系统级安装这些技能"

## 可用技能

### init-project

**项目文档生成器** – 自动为新项目生成 `AGENTS.md` 和 `CLAUDE.md`。

**功能特性：**
- 自动检测项目类型（Python/Web/Rust/Go/Java/数据科学/文档）
- 自动检测操作系统语言以实现本地化
- 生成全面的 AI 上下文文件
- 基于模板的定制化

**使用方式：**
```text
"初始化一个新的 Python 项目"
"为我的 Rust 项目生成 AGENTS.md"
"创建 Web 应用的项目指令"
```

详见 [init-project/README.md](init-project/README.md)。

### install-bensz-skills

**系统级安装器** – 管理跨平台技能安装。

**功能特性：**
- 跨平台安装（Claude Code、Codex 等）
- 基于 MD5 的版本控制（增量更新）
- 技能分类（普通/辅助/测试）
- 国际化支持（en/zh）

**使用方式：**
```text
"系统级安装这些技能"
"更新所有已安装的技能"
```

详见 [install-bensz-skills/README.md](install-bensz-skills/README.md)。

## 创建自定义技能

技能遵循 **Agent Skills 开放标准**的三文件架构：

### 1. SKILL.md（必需）

面向 AI 的指令文件，定义：
- 触发条件
- 工作流步骤
- 输入/输出规范
- 验证标准

### 2. README.md（推荐）

面向用户的指南，解释：
- 技能功能
- 触发方式
- 提示词示例
- 最佳实践

### 3. config.yaml（推荐）

配置文件包含：
- 可调参数
- 阈值和数值
- 平台特定设置

**最小 SKILL.md 结构：**

```markdown
---
name: my-new-skill
description: 这个技能的作用以及何时使用它
version: 1.0.0
author: 您的名字
metadata:
  keywords: [关键词1, 关键词2]
  short-description: 单行摘要
---

# 技能名称

## 触发条件
何时使用此技能。

## 工作流
1. 步骤一
2. 步骤二

## 验证
如何验证成功。
```

完整的技能开发指南请参阅 [AGENTS.md](AGENTS.md)。

## 有机更新哲学

本项目遵循基于成熟工程原则的**有机整体更新**：

- **KISS** – 保持设计简单直接
- **YAGNI** – 只实现当前需要的功能
- **DRY** – 通过抽象避免重复
- **SOLID** – 单一职责、开闭原则、里氏替换、接口隔离、依赖倒置

**核心原则：** 更新技能时，考虑其整个生态系统——元数据、文档、配置和引用必须协同进化。

详见 [AGENTS.md](AGENTS.md) → "工程原则基础"。

## 开发指南

### 添加新技能

```bash
# 创建技能目录
mkdir my-new-skill
cd my-new-skill

# 创建必需文件
touch SKILL.md README.md config.yaml

# 如需脚本，添加 scripts 目录
mkdir scripts
touch scripts/my-script.py
```

### 技能文件结构

```
my-skill/
├── SKILL.md           # 必需：AI 指令
├── README.md          # 推荐：用户指南
├── config.yaml        # 推荐：配置
├── CHANGELOG.md       # 可选：版本历史
├── references/        # 可选：详细文档
│   └── advanced-guide.md
└── scripts/           # 可选：自动化
    └── process.py
```

### 最佳实践

1. **YAML Frontmatter** – 保持 `description` 清晰且语义化，便于发现
2. **渐进披露** – 保持 SKILL.md 精简，详细内容移至 references/
3. **表头-正文一致性** – 同步元数据与实际行为
4. **延迟加载** – 启动时不要加载所有内容
5. **平台无关** – 尽可能避免平台特定代码

## 架构层次

### 1. 元数据层（YAML Frontmatter）

- **用途：** 技能发现与激活
- **字段：** name、description、version、keywords
- **加载时机：** 会话启动时
- **关键：** `description` 决定语义匹配

### 2. 操作层（SKILL.md）

- **用途：** AI 执行指令
- **内容：** 工作流、步骤、验证
- **加载时机：** 技能触发时
- **目标：** 保持简洁（理想情况 <500 行）

### 3. 知识层（references/）

- **用途：** 详细背景和理论
- **内容：** 标准、最佳实践、示例
- **加载时机：** 按需
- **结构：** 从 SKILL.md 单层引用

### 4. 工具层（scripts/）

- **用途：** 自动化和计算
- **内容：** Python/bash 脚本
- **执行方式：** AI 需要时调用
- **风格：** 显式错误处理，带注释的常量

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
- [技能目录](https://github.com/bensz/skills) – 浏览所有技能

## 许可证

MIT License – 详见 [LICENSE](LICENSE)。

---

<div align="center">

**为 AI 代理生态系统用 ❤️ 构建**

[agentskills.io](https://agentskills.io) • [GitHub](https://github.com/bensz/skills)

</div>
