<div align="center">

# Bensz Agent Skills

**让 Agent Skill 从文件，变成系统。**

一套遵循 [Agent Skills 开放标准](https://agentskills.io) 的可复用 Skill 集合、开发流水线，以及帮助检查和追踪 Skill 执行过程的工具。

[![Agent Skills](https://img.shields.io/badge/Agent_Skills-Open_Standard-7c3aed?style=flat-square)](https://agentskills.io)
[![Hosts](https://img.shields.io/badge/Hosts-Claude_Code_%C2%B7_Codex_%C2%B7_Cursor-2563eb?style=flat-square)](#兼容性与边界)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-Python_3.8%2B-0ea5e9?style=flat-square)](#兼容性与边界)
[![License](https://img.shields.io/badge/License-MIT-10b981?style=flat-square)](LICENSE)

[快速开始](#30-秒开始) · [Skill 导航](#skill-导航) · [Kernel](#kernel) · [Skill 身份与严格安装](#skill-身份与严格安装) · [English](README_EN.md)

</div>

Bensz Agent Skills 项目把 Skill 的创建、测试、文档、安装与发布连成可复用的工程流程；更进一步，执行内核`bensz-skill-kernel`（简称BSK）尝试回答：当 Skill 成为 Agent 系统的长期组成部分时，该用的时候它用上了吗？该做的步骤漏掉了吗？改动之后变差了吗？出错时，能查到是哪一步吗？

![Without BSK / With BSK：Skills, but better.](docs/assets/bsk-without-with.jpg)

## 项目在做什么

项目由三部分组成：

- **可直接使用的通用 Skills**：覆盖自动测试、多 Agent 协作、并行工作区、Prompt 优化、科研绘图、Git 操作、安装、文档和缺陷反馈。
- **Skills 开发与维护流水线**：用统一约定串起开发 → 测试 → 文档化 → 安装 → 使用 → 反馈 → 迭代。
- **Skill 执行与检查工具**：`bensz-skill-kernel` 正在提供任务阶段管理、自动检查、工作区、证据记录、事件账本、审计和执行记录重放。

独立的 Bensz Skill Identity（**BSI**，`bensz-skill-identity`）补充签名发行、文件验证、显式信任与精确依赖锁定，安装器提供严格发行入口。BSI 与 Bensz Skill Kernel（**BSK**）均由 Bensz Conan 开发，命令分别为 `bsi` 与 `bsk`；两个 Python 包分别发布，BSI 不依赖 BSK 或 router。

这些工具不试图把 Skill 变成传统程序，而是让复杂 Agent 工作流中的关键阶段、检查和证据更明确、更容易追踪。

## 为什么做这个项目

当 Skill 数量和流程复杂度增长，仅靠更长的 `SKILL.md` 很难回答：Skill 是否正确触发、是否遗漏步骤、修改后是否退化、协作过程是否可追踪、结果经过了哪些检查，以及失败发生在哪里。本项目因此尝试把关注点从“编写单个 Skill”推进到更完整的 **系统化建设 Skill**。

## 设计原则

- 开放标准优先，尽量不绑定单一平台。
- Skill 与通用工具分离：具体工作流程留在 Skill，通用的执行、检查和记录功能放在 Kernel。
- 显式状态优于隐式猜测，检查优于默认信任，可重放优于不可追踪。
- 渐进增强：普通 Skill 保持简单，仅在需要时使用更强的执行和检查功能。

## 30 秒开始

无需克隆仓库即可安装 `skills/alpha` 中的生产 Skill（需要 Python 3.8+ 与网络）：

```bash
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --source general
```

已克隆仓库、需要本地开发时：

```bash
python3 skills/alpha/install-bensz-skills/scripts/install.py --codex
```

安装器默认把 Skill 复制到 `~/.codex/skills/` 和 `~/.claude/skills/`；只安装某个 Skill 可追加 `--skill git-commit`。`skills/beta/` 仅在显式传入 `--source` 时处理。

安装成功后，新建 Codex 或 Claude Code 会话即可使用。例如输入：

```text
请用 humanization 润色下面这段文字，只返回正文，保留原意、事实和格式。
[粘贴原文]
```

预期返回润色后的文字；完整参数与保护规则见 [humanization 使用指南](skills/alpha/humanization/README.md)。本地完整安装器需要 Python 3.11+。

## 这个仓库提供什么

- **可直接安装的 Skill**：位于 `skills/alpha/`，每个目录都有面向使用者的 `README.md` 和面向 AI 的 `SKILL.md`。
- **开发流水线**：覆盖初始化、Prompt 优化、文档生成、批判性测试、多代理协作、Git 发布和缺陷反馈。
- **任务执行内核**：`packages/bensz-skill-kernel/` 提供 `bsk` CLI，用来管理任务阶段、执行检查、保存证据、记录事件，并重放执行记录。
- **Skill 发行身份库**：`packages/bensz-skill-identity/` 提供 Python API 与 `bsi` CLI，核对签名、实际文件和本地信任政策，并支持可恢复的严格安装。
- **可审计协作**：任务过程材料进入 `.bensz-api/`，贡献记录进入 `docs/contribution.bac`。

## Skill 导航

当前 `skills/alpha/` 包含 17 个生产 Skill：

| 方向 | Skill |
| --- | --- |
| 初始化与文档 | `init-project` · `write-readme` |
| 测试与协作 | `auto-test-code` · `auto-test-skill` · `auto-test-project` · `awesome-code` · `parallel-vibe` |
| Prompt 与创作 | `better-prompt` · `auto-draw-plot` · `compact-bensz-skills` · `humanization` |
| 安装与版本 | `install-bensz-skills` · `git-commit` · `git-pr-review` · `git-publish-release` |
| 治理 | `bensz-collect-bugs` · `verifier-state-architect` |

选择 Skill 后，阅读对应目录的 `README.md` 获取触发方式、最小 Prompt、输入输出和 FAQ；维护者同时阅读 `SKILL.md`、`config.yaml` 与 `CHANGELOG.md`。

常见任务可以从以下入口开始：

| 你想完成的任务 | 入口与当前行为 |
| --- | --- |
| 润色已有文章、邮件、报告、学术或技术文字 | [humanization](skills/alpha/humanization/README.md)：自动适配语域，保留事实、意图和格式；主 Agent 唯一润色，三个子 Agent 经 parallel-vibe 并行审查语义安全与防御性表达；两项均须三份判断齐全、至少两票通过，且实质异议已结案 |
| 为项目建立 AI 协作规范 | [init-project](skills/alpha/init-project/README.md)：生成项目指令与文档，初始化 `docs/` 和 `docs/plans/` |
| 组织多个 Agent 协作 | [awesome-code](skills/alpha/awesome-code/README.md) 负责规划和审查，[parallel-vibe](skills/alpha/parallel-vibe/README.md) 统一执行串行或并行任务 |

`humanization` 兼容旧名 `nsfc-humanization`，现已适用于通用文字润色；`init-project` 的默认初始化目录不包含根级 `skills/`。

`humanization` 最多进行五轮外部审查；达到上限仍未通过时，交付最后草案和未通过说明。新增专项审查用于清理无效免责、假想反驳等表达，同时保留必要限定；真实写作质量仍需结合作者评价判断。

beta 候选源中的 [bensz-rmd-rules](skills/beta/bensz-rmd-rules/README.md) 面向 R/Rmd 分析，保留已有项目架构，以 `renv` 配合 simple 或 targets-first complex 流程，要求从原始输入重建结果，并验证冷重建、交付文件丢失、同路径输入更新和项目迁移。它不进入默认安装；需要时显式指定本地源：

```bash
python3 skills/alpha/install-bensz-skills/scripts/install.py --source skills/beta --skill bensz-rmd-rules --codex
```

当然，我觉得最好的方式是：**在你的Codex/Claude Code里把本项目的地址粘贴上，然后开始用ai来探索它！**

## 安装方式

### 远程引导安装

`bootstrap_install.py` 只依赖 Python 标准库，最低 Python 3.8；它是仓库唯一兼容 Python 3.8、3.9 和 3.10 的首次/应急入口，该兼容范围不代表本地完整安装器或 Kernel 支持这些版本。默认远程源由 `skills/alpha/install-bensz-skills/config.yaml` 定义：

| 源 | 内容 |
| --- | --- |
| `general` | 本仓库 `skills/alpha` |
| `research` | `huangwb8/ChineseResearchLaTeX` 的科研 Skill |
| `anthropic-docs` | `anthropics/skills` 的文档处理 Skill |

常用参数：

```bash
# 预览安装差异，不写入 Skill 安装目录
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --check

# 只安装到 Codex 或 Claude Code
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --codex
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --claude

# 创建或更新统一的 benszapi Conda 运行时与 BSK
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/huangwb8/skills/main/skills/alpha/install-bensz-skills/scripts/bootstrap_install.py').read())" --ensure-runtime
```

### 本地安装与开发

本地完整安装器与仓库标准开发环境统一使用 Python 3.11+，支持 `--source`、`--skill`、`--force` 和 `--legacy-source` 等参数：

```bash
git clone https://github.com/huangwb8/skills.git
cd skills
python3 skills/alpha/install-bensz-skills/scripts/install.py
python3 skills/alpha/install-bensz-skills/scripts/install.py --skill write-readme
```

安装记录、MD5 清单和远程缓存位于用户目录的 `~/.bensz-skills/installation/`；安装器不会把 beta Skill 混入默认源。

### 更新已安装的技能

本地安装器提供静默增量更新入口：`--silent-update` 在 72 小时 TTL 到期后维护统一的 benszapi Conda 运行时并更新已安装技能，不能与安装/检查/筛选参数组合使用。远程安装可改用快速版本检查脚本：它并发读取远端版本，仅在远程版本更高或本地缺失时才调用远程安装器，支持 `--check-only`、`--skill`、`--source-contains` 等参数。

```bash
# 静默增量更新（TTL 到期后执行）
python3 skills/alpha/install-bensz-skills/scripts/install.py --silent-update

# 显式创建或更新托管运行时；只读检查可改用 --runtime-status
python3 skills/alpha/install-bensz-skills/scripts/install.py --ensure-runtime

# 只检查远程版本差异，不安装
python3 skills/alpha/install-bensz-skills/scripts/update_remote_skills.py --check-only
```

## Kernel

`bensz-skill-kernel` 当前发布版本为 `2.1.6`，要求 Python 3.11+，运行所需的依赖只有 PyYAML 和 Python 标准库。普通使用由安装器托管在 `~/.bensz-skills/envs/benszapi`，并通过 `~/.bensz-skills/bin/bsk` 固定入口调用，不依赖项目 Python、PATH 中的其它 `bsk` 或 `conda activate`。

它提供 `bsk` 命令，帮助你管理任务阶段与分层运行身份、授权阶段内动作、执行检查、保存证据和重放执行记录。普通使用者可以直接使用上面的命令；内部的 State、Verifier、Workspace 等概念主要面向维护者，详细说明见 [`docs/state-id-naming.md`](docs/state-id-naming.md)、[`docs/verifier-id-naming.md`](docs/verifier-id-naming.md)、[`docs/state-identity-protocol.md`](docs/state-identity-protocol.md) 与 [`packages/bensz-skill-kernel/README.md`](packages/bensz-skill-kernel/README.md)。

2.1.4 新增业务证据哈希与引用绑定；2.1.5 让 `bsk state transition` 显式消费 source Gate，并提供 Gate/result/transition 的只读绑定查询；2.1.6 让原子 `workspace initialize` 的首个 State identity 可直接进入声明的领域初始 State。历史无绑定事件仍可读取，但不会获得严格完成资格。

源码开发仍使用仓库自己的隔离环境：

```bash
python3 -m venv .bensz-api/.venv
.bensz-api/.venv/bin/python -m pip install -e packages/bensz-skill-kernel
.bensz-api/.venv/bin/bsk --version
.bensz-api/.venv/bin/bsk verifier list
```

常用入口：

```bash
BSK="$HOME/.bensz-skills/bin/bsk"
"$BSK" capabilities
"$BSK" state list
"$BSK" verifier list --tag citation
"$BSK" workspace init . --description citation-review
"$BSK" workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

## Skill 身份与严格安装

Bensz Skill Identity（BSI，`bensz-skill-identity`）1.0.0 要求 Python 3.11+，依赖 PyYAML 与 cryptography。它把根公钥指纹和稳定 `skill_key` 组成 Skill 身份，为完整文件集合生成 Ed25519 签名，按管理员显式信任与有限撤销信息验证，并锁定精确依赖。

```bash
python3 -m pip install "bensz-skill-identity==1.0.0"
bsi capabilities
```

能力查询返回 `assurance: files_verified`、`strict_install: true`、`host_binding: false`，不需要密钥或信任文件。已取得签名发行并准备管理员信任策略后，可以预览严格安装：

```bash
python3 skills/alpha/install-bensz-skills/scripts/install.py --release ./release --trust-store ./trust.json --codex --dry-run
```

确认预览后去掉 `--dry-run` 执行安装。签名发行与普通源码安装是两种入口；普通 bootstrap 命令不会替每个 Skill 建立签名或信任。严格入口保留旁路签名证据和安全修订状态，受管目录后续更新须继续走严格入口；历史客户端和直接文件写入不受该 guard 强制约束。

严格安装建议先使用独立临时目录（见包指南的 `bsi install --target`）。混合目录含严格受管项时，未筛选的快速更新目前会整体拒绝；可用 `--skill` 显式更新其它未受管项。

当前保证限于文件验证；宿主实际加载、工具执行绑定及 router 接入尚未实施。API、发行构建、安装恢复和退出码见[Identity 包指南](packages/bensz-skill-identity/README.md)，协议见[身份协议](docs/skill-identity-protocol.md)，实际宿主证据见[能力报告](docs/skill-identity-host-capability.md)。

## 目录与工作区

```text
skills/alpha/                  # 可发布、默认安装的 Skill
skills/beta/                   # 候选 Skill，必须显式指定源
packages/bensz-skill-kernel/   # 独立 Python 内核包
packages/bensz-skill-identity/ # 独立签名发行与文件身份包
docs/                          # 现行文档、教程与设计记录
tests/                         # 仓库公开入口与跨包测试
tmp/                           # 测试报告和临时产物
.bensz-api/                    # AI 任务工作区与工具缓存
```

每个需要落盘的逻辑任务使用一个 `.bensz-api/task-{yyyymmdd-hhmm}-{描述}/`；正式 README、源代码和计划仍写入项目约定目录，不放入隐藏工作区。

## 开发与验证

```bash
# 根级测试（缓存写入 .bensz-api）
python3 -m pytest

# 检查中英文 README 标题、代码块、链接和命令 token 是否对齐
python3 skills/alpha/write-readme/scripts/check_readme_pair.py README.md README_EN.md

# 报告所有 alpha/beta Skill 的正文规范缺项；迁移后的 Skill 可加 --mode strict
python3 tests/check_skill_structure.py --mode report

# 查看 BAC 贡献账本
bac --root . --bac-file docs/contribution.bac inspect
```

修改 Skill 时保持 `SKILL.md`、`config.yaml`、README 和 CHANGELOG 同步；重要仓库变更先记录到 `CHANGELOG.md` 的 `[Unreleased]`。

## 兼容性与边界

- Agent Skills 文件格式遵循开放标准；实际触发能力取决于宿主对 Skill 目录的支持。
- 仓库开发、本地完整安装器和 Kernel 统一要求 Python 3.11+；仅远程 bootstrap 为首次/应急安装保留 Python 3.8+ 兼容。
- Kernel 的进程级超时、输入输出限制和 fail-closed 选项不是容器或操作系统沙箱；不可信代码仍应在独立环境运行。
- 远程安装需要访问 GitHub；网络失败时可改用本地安装器或已有缓存，并检查安装退出码。

## 贡献与许可证

请先阅读 [`AGENTS.md`](AGENTS.md) 和 [`CLAUDE.md`](CLAUDE.md)。本项目暂不接受未经沟通的普通 PR；如需贡献，请先联系 [huangwb8](https://github.com/huangwb8)。

项目采用 MIT License，见 [`LICENSE`](LICENSE)。

## 更多入口

下面这些入口分别介绍版本变化、结果检查、任务阶段和 Skill 安装；按你的目标选择即可。

- [`CHANGELOG.md`](CHANGELOG.md)：这是项目的更新日志，记录每次版本的新增功能、修复问题和重要调整；想了解最近改了什么，可以先看这里。
- [Gitee 镜像](https://gitee.com/huangwb8/skills)：如果访问 GitHub 不便，也可以从 Gitee 镜像获取本项目。
- [`docs/bsk-tutorial.md`](docs/bsk-tutorial.md)：这是 `bsk` 的总教程，用通俗例子和 Mermaid 图介绍 State、Verifier、Gate、Contract Pack 四种重要抽象，以及它们如何协作。
- [`skills/alpha/install-bensz-skills/README.md`](skills/alpha/install-bensz-skills/README.md)：这是 Skill 安装器的使用指南，介绍安装方式、参数和常见用法；准备安装 Skill 时，可以按这份指南操作。
- [`docs/templates/skill-body.md`](docs/templates/skill-body.md)：这是新建或修改 Skill 时使用的四段式正文骨架。
- [`docs/templates/verifier-body.md`](docs/templates/verifier-body.md)：这是新建或修改 `VERIFIER.md` 时使用的五段轻量骨架，覆盖判断目标、输入证据、执行、输出判定和失败边界。
- [`docs/templates/skill-common-constraints.md`](docs/templates/skill-common-constraints.md)：这是工作区、BAC、隐私和缺陷协作的公共约束长版本。
