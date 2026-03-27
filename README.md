<div align="center">

# Skills 开发流水线

[![Version](https://img.shields.io/github/v/tag/huangwb8/skills?label=version&sort=semver)](https://github.com/huangwb8/skills/releases)
[![Standard](https://img.shields.io/badge/Agent%20Skills-Standard%20v1.0-blue.svg)](https://agentskills.io)
[![Platforms](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Codex%20%7C%20Cursor-lightgrey.svg)](#平台兼容性)
[![Built with](https://img.shields.io/badge/built%20with-Python%203.10%2B-orange.svg)](https://www.python.org/)

[中文](README.md) | [English](README_EN.md)

<strong>遵循 Agent Skills 开放标准的可复用 AI 技能库与技能开发流水线</strong>

</div>

这是一个遵循 Agent Skills 开放标准的技能库与开发流水线，覆盖 skills 的创建、测试、文档化、安装、发布和缺陷反馈。仓库内既包含可直接安装使用的通用 skills，也包含维护这些 skills 所需的约束、脚本和协作流程。

## 🎯 这个仓库适合谁

- 想把一组 skills 复制安装到系统级目录，在任意项目里都能触发的人
- 想开发、优化、测试、发布自己 skills 的维护者
- 想复用本仓库里的工程约束、文档约束和质量流程的人
- 想基于 Agent Skills 标准，兼容 Claude Code、Codex、Cursor 等平台的人

## 💡 推荐开发环境

### 🧰 VS Code + Claude Code / Codex 插件

推荐使用 VS Code 配合 Claude Code 或 Codex 插件进行技能开发、测试和维护。

| 优势 | 说明 |
|------|------|
| 原生技能集成 | 自动从系统级 skills 目录加载已安装技能 |
| 实时验证 | 直接用自然语言测试技能触发与执行效果 |
| 上下文感知编辑 | AI 能结合项目结构理解技能、脚本和文档之间的关系 |
| 集成工作流 | 编辑、测试、安装、迭代可以在同一环境中完成 |
| 文档协同维护 | 便于同步维护 `SKILL.md`、`README.md`、`config.yaml` 与 `CHANGELOG.md` |

📺 [观看演示视频（Bilibili）](https://www.bilibili.com/video/BV1tpcezbERB)

## ⚡ AI 算力

仓库相关的 AI 算力说明与使用背景，可参考下面的视频：

📺 [观看 AI 算力介绍视频（Bilibili）](https://www.bilibili.com/video/BV1a7ZLBuE5z)

## 🧩 核心技能

仓库根目录下可直接安装的技能有 12 个：

| 技能 | 主要用途 | 适用场景 |
|------|----------|----------|
| `init-project` | 初始化项目指令文件 | 为新项目生成 `AGENTS.md`、`CLAUDE.md`、`README.md`、`CHANGELOG.md` 等 |
| `install-bensz-skills` | 系统级安装 skills | 把本仓库 skills 复制到 `~/.codex/skills/`、`~/.claude/skills/` |
| `write-skill-readme` | 生成技能用户文档 | 为单个 skill 产出面向使用者的 `README.md` |
| `auto-test-skill` | skill 级批判性测试 | 测试某个 skill 的流程设计、输出质量和鲁棒性 |
| `auto-test-project` | 项目级批判性测试 | 对整个项目做多轮问题发现、修复和复验 |
| `better-prompt` | Prompt 优化 | 把简陋 prompt 重写成更清晰、可执行的版本 |
| `awesome-code` | 多代理协作开发 | 任务拆解、子代理协作、并行推进复杂开发任务 |
| `parallel-vibe` | 多工作区并行尝试 | 同一指令开多个独立工作区并行探索方案 |
| `git-commit` | Git 提交自动化 | 生成 conventional commit，按需自动 push |
| `git-pr-review` | GitHub PR 只读审查 | 判断某个 PR 是否值得 merge，输出结构化报告 |
| `git-publish-release` | GitHub Release 发布 | 生成 release notes 并创建 release |
| `bensz-collect-bugs` | 收集并公开上报 skill 设计缺陷 | 规范化记录 bug，并在用户明确要求时用 `gh` 公开上报 |

想看每个 skill 的详细用法，可以直接进入对应目录阅读其 `README.md` 和 `SKILL.md`。

## ✨ 仓库能力

- 一套面向多平台的 Agent Skills 标准化开发方式
- 一组可直接使用的通用 skills
- 一条完整维护链路：创建、测试、文档化、安装、发布、缺陷反馈
- 面向系统级可发现性的安装机制
- 面向长期演进的工程约束：KISS、YAGNI、DRY、Single Source of Truth、有机更新

## 🌐 平台兼容性

根据本仓库约定与 Agent Skills 生态，当前重点兼容平台包括：

| 平台 | 状态 | 常见技能目录 |
|------|------|--------------|
| [Claude Code](https://code.anthropic.com) | 已验证 | `~/.claude/skills/` |
| [OpenAI Codex](https://openai.com/index/introducing-codex/) | 已验证 | `~/.codex/skills/` |
| Cursor | 兼容 | `~/.cursor/skills/` |
| GitHub | 兼容 | `.github/skills/` |
| VS Code | 兼容 | `.vscode/skills/` |
| Amp | 兼容 | 依平台约定 |
| Letta | 兼容 | 依平台约定 |
| Goose | 兼容 | 依平台约定 |

## 🚀 快速开始

### ⚡ 方法一：一键快速安装

无需先克隆仓库，直接安装到系统级目录。

| 平台 | 命令 |
|------|------|
| macOS / Linux / WSL | `curl -fsSL https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.sh \| bash` |
| Windows PowerShell | `irm https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.ps1 \| iex` |

默认会把技能安装到：

- `~/.claude/skills/`
- `~/.codex/skills/`

### 🛠️ 方法二：克隆仓库后本地安装

```bash
git clone https://github.com/huangwb8/skills.git
cd skills
python3 install-bensz-skills/scripts/install.py
```

如果你只想装到某一个平台：

```bash
python3 install-bensz-skills/scripts/install.py --codex
python3 install-bensz-skills/scripts/install.py --claude
```

### 🤖 方法三：让 AI 直接调用安装 skill

在 Claude Code 或 Codex 中打开本仓库后，可以直接说：

```text
请使用 install-bensz-skills skill 将当前仓库中的 skills 安装到系统级目录，确保它们在任意项目中可被发现。
```

这适合你想把“安装动作”也放进自然语言工作流里时使用。

## 📘 开发约束与核心文档

- [AGENTS.md](AGENTS.md)：跨平台通用项目指令，也是本仓库工程约束的单一真相来源
- [CLAUDE.md](CLAUDE.md)：Claude Code 特定适配说明
- [CHANGELOG.md](CHANGELOG.md)：所有重要更新都应先写入这里的 `Unreleased`

如果你打算修改项目指令、工作流或 README，请先读 `AGENTS.md`，因为这个仓库要求文档更新要和工程约束保持一致，并同步维护 `CHANGELOG.md`。

## 🤝 贡献建议

- 优先做“优化”而不是“重写”，保留已有可复用资产
- 修改技能时，同时检查 `SKILL.md`、`README.md`、`config.yaml` 是否还一致
- 重要仓库级变更要先补 `CHANGELOG.md`
- 尽量验证系统级安装后的可发现性，而不只是在当前仓库内试跑

## 🔗 相关资源

- [Agent Skills 开放标准](https://agentskills.io)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [install-bensz-skills 用户指南](install-bensz-skills/README.md)
