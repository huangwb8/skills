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

`skills/alpha/` 提供可发布的核心技能；`skills/beta/` 保存尚未成熟、默认不安装的候选技能：

| 技能 | 主要用途 | 适用场景 |
|------|----------|----------|
| `init-project` | 初始化项目指令文件 | 为新项目生成 `AGENTS.md`、`CLAUDE.md`、`README.md`、`CHANGELOG.md`、`.gitignore`，并补齐 `docs/` 与 `docs/plans/` |
| `install-bensz-skills` | 系统级安装 skills | 把本仓库 skills 复制到 `~/.codex/skills/`、`~/.claude/skills/` |
| `write-skill-readme` | 生成技能用户文档 | 为单个 skill 产出面向使用者的 `README.md` |
| `auto-test-skill` | skill 级批判性测试 | 测试某个 skill 的流程设计、输出质量和鲁棒性 |
| `auto-test-project` | 项目级批判性测试 | 对整个项目做多轮问题发现、修复和复验 |
| `better-prompt` | Prompt 优化 | 把简陋 prompt 重写成更清晰、可执行的版本 |
| `auto-draw-plot` | 模式化科研绘图 | 根据需求生成通用图、技术路线图或机制图，并支持参考图保真迭代 |
| `awesome-code` | 多代理协作开发 | 任务拆解、三层代理分派、required agent 门禁与并行推进 |
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

## 🗂️ 目录结构

```text
skills/alpha/      # 可发布、默认安装的成熟 Skill
skills/beta/       # 候选 Skill，需显式指定源目录
packages/          # 独立运行时包及其测试
docs/              # 项目文档；计划统一放在 docs/plans/
tests/             # 根级 smoke/integration 测试脚本
tmp/               # 测试运行过程产物
```

## 🗂️ 任务工作区

需要落盘的 skill 任务默认把过程材料集中到项目内的 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/`，避免把计划、日志和临时输出散落到项目根目录。单 skill 任务只创建该 skill 的边界；多 skill 协作时才使用 `shared/` 传递任务级材料。

```text
.bensz-api/task-20260717-1432-优化-skill-工作区/
├── shared/                 # 仅多 skill 任务的共享输入与来源说明
└── {skill-name}/
    ├── input/              # 输入、参数快照、上游引用
    ├── output/             # 草案和供后续阶段消费的中间结果
    └── log/                # 命令、验证、错误与决策摘要
```

正式交付物、用户要求保存的文件、项目文档和源代码仍按项目原有目录约定存放，不会默认写入该隐藏工作区。历史隐藏目录只用于显式兼容读取、迁移或清理。

## 🧾 贡献记录

本仓库当前未初始化 `bensz-auto-contribution` 的 BAC 账本；默认文件位置为 `docs/contribution.bac`。本次系统文件维护按 `init-project --disable-bac` 处理，未安装外部 `bac` 依赖或创建空账本。后续如需启用，可在仓库根目录运行：

```bash
python3 skills/alpha/init-project/scripts/generate.py --auto
```

贡献记录启用后只保存协作过程与验证证据，不记录密钥、完整私有 Prompt 或无关个人隐私，也不替代最终署名、责任或合规判断。

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

### ⚡ 推荐：一行远程安装

无需先克隆仓库，直接运行 `install-bensz-skills` 内置的标准库 bootstrap 脚本。它会从 GitHub zip 包下载远程源，遇到临时网络错误会自动重试，按 MD5 跳过未变化的 skill，并写入安装清单；本仓库的 `general` 源固定只包含 `skills/alpha`。

| 平台 | 命令 |
|------|------|
| 全平台（Python） | `python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())"` |
| macOS / Linux 备用 | `python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())"` |

支持矩阵：仓库开发与本地完整安装使用 Python 3.10+；无第三方依赖的 bootstrap 入口最低支持 Python 3.8，并只使用标准库。

默认安装的远程源：

- `general`：`huangwb8/skills` 通用技能
- `research`：`huangwb8/ChineseResearchLaTeX` 科研技能
- `anthropic-docs`：`anthropics/skills` 官方文档处理技能

默认安装位置：

- `~/.claude/skills/`
- `~/.codex/skills/`

常用参数：

```bash
# 只安装本仓库通用技能
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --source general

# 只安装到 Codex 或 Claude Code
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --codex
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --claude

# 预览安装动作，不写入文件
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --check

# 使用中文安装输出
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --lang zh
```

### 🛠️ 本地开发安装

如果你已经克隆仓库，或正在开发本仓库里的 skills，可以使用本地安装脚本。它默认只识别 `skills/alpha/`；`skills/beta/` 必须通过 `--source` 显式指定。

```bash
git clone https://github.com/huangwb8/skills.git
cd skills
python3 skills/alpha/install-bensz-skills/scripts/install.py
```

如果你只想装到某一个平台：

```bash
python3 skills/alpha/install-bensz-skills/scripts/install.py --codex
python3 skills/alpha/install-bensz-skills/scripts/install.py --claude
```

如果安装器已经系统级安装，也可以在其它项目中直接调用已安装脚本，并显式指定源目录：

```bash
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py --source ./skills/alpha
python3 ~/.claude/skills/install-bensz-skills/scripts/install.py --source ./skills/alpha

# beta 仅在明确需要时安装
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py --source ./skills/beta

# 迁移旧仓库时才显式启用历史 pipelines/skills/alpha
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py --legacy-source
```

### 🤖 让 AI 调用安装 skill

在 Claude Code 或 Codex 中打开本仓库后，可以直接说：

```text
请使用 install-bensz-skills skill 将当前仓库中的 skills 安装到系统级目录，确保它们在任意项目中可被发现。
```

这适合你想把“安装动作”也放进自然语言工作流里时使用。

## 如何贡献？

本项目暂时不支持常规pr。如果确有需求，需要请示 [huangwb8](https://github.com/huangwb8)。

## 🔗 相关资源

- [Agent Skills 开放标准](https://agentskills.io)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [install-bensz-skills 用户指南](skills/alpha/install-bensz-skills/README.md)
