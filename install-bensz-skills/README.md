# install-bensz-skills — 用户使用指南

本 README 面向**使用者**：如何将 `pipelines/skills/` 中的技能安装到系统级位置，使其在任意项目中可用。

> **提示**：执行指令与硬性规范在 [SKILL.md](SKILL.md)；默认参数在 [config.yaml](config.yaml)。

---

## 快速开始

### 本地安装（最推荐）

```bash
# 默认：同时安装到 Codex 和 Claude Code（仅安装有更新的）
python3 install-bensz-skills/scripts/install.py
```

### 在任意目录运行（安装器已系统级安装时）

如果当前项目目录里只有 `skills/`（没有 `install-bensz-skills/`），可以直接运行系统级已安装位置的脚本；必要时用 `--source` 指定源目录：

```bash
# Codex 安装位置（优先）
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py

# 或 Claude Code 安装位置
python3 ~/.claude/skills/install-bensz-skills/scripts/install.py

# 显式指定源目录（示例：当前项目的 ./skills）
python3 ~/.codex/skills/install-bensz-skills/scripts/install.py --source ./skills
```

### 远程安装（从 GitHub 获取）

```bash
# 交互式检查模式：询问后再安装（推荐）
python3 install-bensz-skills/scripts/install.py --remote --check
```

---

## 功能概述

`install-bensz-skills` 是一个**系统级技能安装器**，它将当前仓库 `pipelines/skills/` 下的所有技能复制安装到：

- **Codex**：`~/.codex/skills/`
- **Claude Code**：`~/.claude/skills/`

### 核心特性

| 特性 | 说明 |
|------|------|
| 智能版本控制 | 使用 MD5 哈希值检测变化，仅安装有更新的技能 |
| 技能自动分类 | 自动识别普通技能/辅助技能/测试技能，仅安装普通技能 |
| 远程安装支持 | 支持从 GitHub 仓库下载并安装技能 |
| 双平台支持 | 同时支持 Codex 和 Claude Code |

---

## 使用场景与命令

### 场景 1：初次安装

你刚克隆了技能仓库，想要让所有技能在系统中可用。

```bash
python3 install-bensz-skills/scripts/install.py
```

### 场景 2：更新技能

你更新了仓库中的某些技能，想要同步到系统。

```bash
# 再次运行即可（仅安装有变化的）
python3 install-bensz-skills/scripts/install.py
```

### 场景 3：仅安装到 Claude Code

你只使用 Claude Code，不需要安装到 Codex。

```bash
python3 install-bensz-skills/scripts/install.py --claude
```

### 场景 4：预览模式

你想要查看将要安装哪些技能，但不实际执行。

```bash
python3 install-bensz-skills/scripts/install.py --dry-run
```

### 场景 5：从额外目录安装

你需要从其他 skills 目录合并安装。

```bash
# 单个源目录
python3 install-bensz-skills/scripts/install.py --source /path/to/skills

# 多个源目录（逗号分隔）
python3 install-bensz-skills/scripts/install.py --source /path/skills-a,/path/skills-b
```

### 场景 6：强制重装

某些技能出现异常，想要强制重新安装。

```bash
python3 install-bensz-skills/scripts/install.py --force
```

### 场景 7：从远程仓库安装

你想要从 GitHub 仓库获取最新技能，无需手动克隆。

```bash
# 交互式检查（推荐）：可以看到将要安装的技能并确认
python3 install-bensz-skills/scripts/install.py --remote --check

# 自动强制安装：适合 CI/CD 或自动化脚本
python3 install-bensz-skills/scripts/install.py --remote --auto
```

---

## 命令行参数速查表

### 本地安装参数

| 参数 | 说明 | 适用场景 |
|------|------|----------|
| `--dry-run` | 预览模式，不实际写入文件 | 查看将要安装的技能 |
| `--codex` | 仅安装到 Codex（`~/.codex/skills/`） | 只使用 Codex |
| `--claude` | 仅安装到 Claude Code（`~/.claude/skills/`） | 只使用 Claude Code |
| `--force` | 强制重新安装所有技能 | 技能异常需要重装 |
| `--source` | 指定额外的 skills 源目录路径 | 从其他目录安装 |

### 远程安装参数

| 参数 | 说明 | 适用场景 |
|------|------|----------|
| `--remote` | 启用远程安装模式 | 从 GitHub 获取技能 |
| `--check` | 检查模式（交互式确认后再安装） | 手动确认安装内容 |
| `--auto` | 自动模式（强制安装，无需确认） | CI/CD 自动化 |
| `--{id}` | 仅安装指定远程源（如 `--general`、`--research`） | 只安装某个源 |

**常用组合**：
- `--remote --check`：交互式远程安装（推荐）
- `--remote --auto`：自动强制远程安装
- `--remote --check --claude`：仅对 Claude Code 执行远程检查
- `--remote --check --general`：仅检查并安装 general 源

---

## 技能自动分类

安装器会自动识别并分类技能，**仅安装普通技能**。

### 你的需求 → 技能类型 → 配置方式

| 你的需求 | 技能类型 | 是否安装 | 配置方式 |
|---------|---------|---------|---------|
| 供用户在项目中使用的功能技能 | 普通技能 | ✅ 安装 | 无需配置（默认） |
| 仅用于开发本仓库的工具 | 辅助技能 | ❌ 忽略 | 添加 `category: auxiliary` |
| 用于测试的临时技能 | 测试技能 | ❌ 忽略 | 添加 `category: test` |

### 如何标记技能类型

在 `SKILL.md` 的 YAML frontmatter 中添加 `category` 字段：

```yaml
---
name: my-skill
category: normal  # 可选值: normal, auxiliary, test（或省略，默认为 normal）
description: 技能描述
---
```

**推荐做法**：
- 普通技能：可省略 `category`（默认为 `normal`）
- 辅助技能：明确添加 `category: auxiliary`
- 测试技能：明确添加 `category: test`

---

## 远程安装配置

远程技能源通过 `config.yaml` 配置文件定义：

```yaml
remote_sources:
  - id: "general"
    name: "通用技能"
    url: "https://github.com/huangwb8/skills"
    branch: "main"
    skills_path: "skills"
    description: "通用技能，建议所有用户安装"
    recommended: true

  - id: "research"
    name: "科研技能"
    url: "https://github.com/huangwb8/ChineseResearchLaTeX"
    branch: "main"
    skills_path: "skills"
    description: "科研相关技能，建议有科研需要的用户安装"
    recommended: false
```

### 配置字段说明

| 字段 | 说明 | 必需 |
|------|------|------|
| `id` | 源 ID（用于 `--{id}` 过滤） | ✅ 必需 |
| `name` | 源名称（用于显示和提示） | ✅ 必需 |
| `url` | Git 仓库 URL | ✅ 必需 |
| `branch` | 分支名称（默认 `main`） | ❌ 可选 |
| `skills_path` | 技能目录相对于仓库根目录的路径 | ✅ 必需 |
| `description` | 源描述（用于提示用户） | ❌ 可选 |
| `recommended` | 是否推荐安装（影响默认提示行为） | ❌ 可选 |

---

## 安装报告示例

安装完成后，脚本会生成详细的安装报告：

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
```

---

## 常见问题（FAQ）

### Q: 为什么某些技能没有被安装？

A: 检查技能是否被标记为**辅助技能**或**测试技能**。安装器仅安装普通技能。详见上面的"技能自动分类"部分。

### Q: 如何添加新的远程技能源？

A: 编辑 `config.yaml`，在 `remote_sources` 数组中添加新的源配置。详见"远程安装配置"部分。

### Q: 远程安装失败怎么办？

A: 检查：
1. 网络连接是否正常
2. Git 是否已安装（`git --version`）
3. PyYAML 依赖是否已安装（`python3 -m pip install pyyaml`）
4. 某些网络环境可能需要配置代理

### Q: 安装后技能没有生效？

A: Claude Code / Codex 需要**新会话**才会重新加载更新后的技能。安装后建议新建会话验证。

### Q: 如何回退到旧版本？

A: 使用 Git 回退源代码后，重新运行安装脚本即可（安装器不备份旧版本）。

### Q: 临时目录未清理怎么办？

A: 手动删除 `~/.install-bensz-skills/tmp-remote-install` 目录。

### Q: 版本控制是如何工作的？

A: 脚本使用 **MD5 哈希值**进行智能版本控制：
- **版本计算**：对技能目录内的可安装文件进行 MD5 计算（排除 `tests/`、`plans/`、缓存与临时文件）
- **版本存储**：安装后在目标目录生成平台特定 manifest（`.skill-manifest.{codex,claude}.json`）记录版本信息
- **智能安装**：
  - ✅ 已安装且版本未变：跳过，不重复安装
  - ✅ 版本已变化：强制覆盖安装
  - ✅ 新技能：直接安装

---

## 相关文件

- [SKILL.md](SKILL.md) — 技能定义（供 AI 加载）
- [config.yaml](config.yaml) — 配置文件（远程源、版本信息）
- [CHANGELOG.md](CHANGELOG.md) — 变更日志
- [scripts/install.py](scripts/install.py) — 核心安装脚本

---

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic（1/6 = 17%）
- **来源构成**：社区 70%, 官方 20%, 技术博客 10%
- **数据时效**：2024-10 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试安装脚本准确率

---

### 场景化建议

#### 场景 1：标准安装（最常见）

**触发条件**：需要将技能安装到系统级位置

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 |
| **推理强度** | low |
| **预期成本** | ~$0.001-0.005/次 |

**理由**：
- 技能安装是纯脚本驱动任务，AI 负责理解和调用安装脚本
- Haiku 速度快、成本低，适合高频的安装任务
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1ocpoye/haiku_45_better_than_sonnet/) 显示 Haiku 在简单任务中表现优异
- **安装任务是确定性任务，Haiku 完全胜任**

**避免**：无需升级模型

**来源**：[Haiku System Card](https://www.anthropic.com/claude-haiku-4-5-system-card) + Reddit 社区讨论

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Haiku 4.5** | 所有安装场景 | 无 | $ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Sonnet 4.5** | **不推荐** | 所有场景（浪费） | $$$ | ⭐⭐⭐⭐ | ⭐ |
| **Opus 4.5** | **不推荐** | 所有场景（浪费） | $$$$$ | ⭐⭐ | ⭐ |

**说明**：
- Haiku 覆盖 100% 的安装场景
- Sonnet 和 Opus 对此任务**完全不必要**，成本过高且无性能提升

---

### 通用原则

1. **始终使用 Haiku**：安装任务是脚本驱动任务，Haiku 完全胜任
2. **简单任务、快速响应**：安装是高频操作，Haiku 的 <1 秒响应时间明显优于 Sonnet 的 3-5 秒
3. **成本敏感**：安装是高频操作，Haiku 的成本优势明显
4. **避免过度设计**：安装主要是脚本驱动任务，AI 负责理解需求并调用脚本，Haiku 完全胜任

---

### 更新记录

- 2026-01-25：首次调研，覆盖 Anthropic
- 建议：2026-07 重新调研（6 个月后）

---

### 来源链接

**官方文档**：
- [Claude Tool Use Documentation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Choosing the right model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)
- [Claude Haiku 4.5 System Card](https://www.anthropic.com/claude-haiku-4-5-system-card)

**社区讨论**：
- [Haiku 4.5 better than Sonnet? (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1ocpoye/haiku_45_better_than_sonnet/)
- [Claude Haiku 4.5: Features, Testing Results, and Use Cases](https://www.datacamp.com/fr/blog/anthropic-claude-haiku-4-5)

**技术博客**：
- [Top Use Cases for Claude Haiku 4.5](https://chatlyai.app/blog/claude-haiku-4-5-use-cases)
