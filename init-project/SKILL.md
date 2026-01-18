---
name: init-project
description: 当用户要初始化一个新项目（在空目录或新建项目），需要生成 AI 项目指令文件时使用。完全自动化：自动检测操作系统默认语言，分析项目目录结构（支持 Python/Web/Rust/Go/Java/数据科学/文档项目等），推断项目类型和用途，一键生成规范的项目指令文档。生成文件包括：AGENTS.md（跨平台通用项目指令，Single Source of Truth）、CLAUDE.md（Claude Code 特定适配，通过 @./AGENTS.md 引用）、README.md（项目介绍与使用方法）、CHANGELOG.md（项目变更记录）。适用于"初始化项目"、"新建项目配置"、"生成项目文档"、"自动生成 AGENTS.md"等场景。
metadata:
  short-description: 完全自动生成 AI 项目指令文档（AGENTS.md + CLAUDE.md + README.md + CHANGELOG.md）
  keywords:
    - 项目初始化
    - 初始化项目
    - 新建项目
    - 项目配置
    - 项目文档
    - AGENTS.md
    - CLAUDE.md
    - README.md
    - CHANGELOG.md
    - 项目指令
    - 自动生成
    - 一键生成
    - generate project docs
    - create project structure
    - init project
    - 项目初始化文档
    - 系统级 prompt
    - 项目原则
    - 工程原则
    - 项目规范
    - 自动分析项目
    - 检测项目类型
    - OpenAI Codex
    - Claude Code
    - 跨平台指令
    - @ 引用语法
    - Single Source of Truth
# 版本号以 config.yaml:skill_info.version 为准
---

# Init Project（项目初始化文档生成器）

## 目标

为全新项目快速生成规范的 AI 项目指令文档，使 AI 助手（Claude Code / OpenAI Codex CLI）能够理解项目目标、遵循工程原则、按预期行为协作。

## 生成文件

| 文件 | 用途 | 平台适配 | 强制性 | 维护方式 |
|------|------|----------|--------|----------|
| **AGENTS.md** | 跨平台通用项目指令 | 20+ AI 编码工具 | **必须** | 手动维护（Single Source of Truth） |
| **CLAUDE.md** | Claude Code 特定适配 | Claude Code | **必须** | 自动引用 AGENTS.md |
| **README.md** | 项目介绍与使用方法 | 通用 | 可选 | 手动维护 |
| **CHANGELOG.md** | 项目变更记录 | 通用 | **必须** | 手动维护 |

**重要说明**：

1. **AGENTS.md 是唯一需要手动维护的项目指令文件**
   - 包含跨平台通用的核心指令
   - 符合 [AGENTS.md 标准](https://agents.md/)（60k+ 开源项目采用）
   - 支持 OpenAI Codex、Google Jules、Cursor、Devin、Windsurf 等 20+ 工具

2. **CLAUDE.md 通过 `@./AGENTS.md` 语法自动引用**
   - 修改 AGENTS.md 后，CLAUDE.md 自动生效
   - 无需运行任何同步命令
   - 仅包含 Claude Code 特定的适配内容

3. **CHANGELOG.md 是项目管理的强制性要求**
   - 凡是项目的更新，都要统一在 CHANGELOG.md 文件里记录
   - 遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式

## 核心特性

- **完全自动化**：一键生成，无需手动输入信息
- **智能项目分析**：自动检测项目类型（Python/Web/Rust/Go/Java/数据科学/文档等）
- **跨平台通用**：生成符合 AGENTS.md 标准的跨平台指令文件
- **零维护成本**：CLAUDE.md 通过 `@./AGENTS.md` 自动引用，修改 AGENTS.md 即可
- **自动语言检测**：检测操作系统默认语言并设为对话默认语言
- **目录结构推断**：分析现有文件和目录，自动生成目录树
- **README 解析与生成**：从 README.md 提取信息，或自动生成项目介绍
- **强制变更记录**：自动创建 CHANGELOG.md，**这是项目管理的强制性要求**
- **工程原则内置**：基于 SOLID、KISS、DRY、YAGNI、关注点分离等原则
- **有机更新框架**：生成的文档本身遵循有机更新原则，便于未来迭代
- **智能增量更新**：对已存在的 AGENTS.md，自动保留用户自定义内容，仅更新标准化部分
- **符合社区标准**：遵循 [AGENTS.md 官方规范](https://agents.md/)，与 60k+ 开源项目保持一致

## AGENTS.md 与 CLAUDE.md 的关系

**核心原则**：AGENTS.md 是跨平台通用项目指令（Single Source of Truth），CLAUDE.md 通过 `@./AGENTS.md` 语法自动引用。

### 架构设计

```
项目根目录/
├── AGENTS.md              # 跨平台通用指令（手动维护）
│   ├── 项目目标
│   ├── 核心工作流
│   ├── 工程原则
│   ├── 默认语言
│   ├── 目录结构
│   ├── 变更边界
│   └── 有机更新原则
│
└── CLAUDE.md              # Claude Code 特定适配（自动引用）
    ├── @./AGENTS.md       # 自动引用 AGENTS.md 的全部内容
    └── Claude Code 特定说明
        ├── 文件引用规范（markdown 链接语法）
        ├── 任务管理（TodoWrite 工具）
        └── 代码变更规范（Read/Edit 工具）
```

### 维护工作流

**标准流程**：
1. **修改 AGENTS.md**（唯一需要手动维护的文件）
2. **CLAUDE.md 自动生效**（无需任何操作）
3. **记录变更到 CHANGELOG.md**

**优势**：
- ✅ 零维护成本：修改 AGENTS.md 后，CLAUDE.md 自动生效
- ✅ Single Source of Truth：AGENTS.md 是唯一的事实来源
- ✅ 符合社区标准：遵循 [AGENTS.md 官方规范](https://agents.md/)
- ✅ 跨平台兼容：AGENTS.md 支持 20+ AI 编码工具

### Claude Code 的 @ 引用语法

根据 [Claude Code Issue #990](https://github.com/anthropics/claude-code/issues/990)，Claude Code 支持 `@` 语法来引用其他文件：

```markdown
# CLAUDE.md

## 核心指令

@./AGENTS.md

## Claude Code 特定说明
...
```

**工作原理**：
- Claude Code 启动时，会自动将 `@./AGENTS.md` 引用的文件内容"拉入"上下文
- 修改 AGENTS.md 后，CLAUDE.md 会自动读取最新内容
- 无需运行任何同步命令或构建步骤

## 触发条件

用户明确表示要：
- 初始化一个新项目
- 创建项目配置文件
- 生成 AGENTS.md / CLAUDE.md
- 为现有项目补全项目指令文档
- 自动生成项目文档

## 执行方式

### 方式一：完全自动化（推荐）

直接运行脚本，自动分析当前目录并生成文档：

```bash
python3 init-project/scripts/generate.py --auto
```

**脚本会自动完成**：
1. 检测项目类型（通过 pyproject.toml、package.json、Cargo.toml 等标志文件）
2. 从 README.md 提取项目名称和描述（如存在）
3. 生成目录树（自动过滤 .git、node_modules、__pycache__ 等）
4. 检测操作系统语言
5. 生成 AGENTS.md（跨平台通用项目指令）
6. 生成 CLAUDE.md（使用 `@./AGENTS.md` 引用 + Claude Code 特定适配）
7. 检查并生成 README.md（如不存在）
8. 检查并生成 CHANGELOG.md（如不存在）

### 方式二：通过 Claude Code 触发

在 Claude Code 中触发本 skill 后：

1. **运行自动模式**：
   ```bash
   python3 init-project/scripts/generate.py --auto
   ```

2. **如需覆盖现有文件**：
   ```bash
   python3 init-project/scripts/generate.py --auto --overwrite
   ```

3. **仅生成指定文件**：
   ```bash
   # 仅生成 AGENTS.md 和 CLAUDE.md（CHANGELOG.md 仍会生成，因为它是强制性的）
   python3 init-project/scripts/generate.py --auto --skip-readme

   # 仅更新 README.md
   python3 init-project/scripts/generate.py --auto --only-readme

   # 注意：不建议使用 --skip-changelog，因为 CHANGELOG.md 是强制性的
   ```

## 工作流程

### 自动模式流程

当使用 `--auto` 参数时，脚本执行以下流程：

#### 1. 项目类型检测

扫描目录中的标志性文件，自动识别项目类型：

| 项目类型 | 标志文件 |
|---------|---------|
| Python | pyproject.toml, requirements.txt, setup.py |
| Web | package.json, yarn.lock, webpack.config.js |
| Rust | Cargo.toml, Cargo.lock |
| Go | go.mod, go.sum |
| Java | pom.xml, build.gradle |
| 数据科学 | *.ipynb, *.R, environment.yml |
| 文档 | docs/, mkdocs.yml, docusaurus.config.js |

#### 2. 项目信息提取

- **项目名称**：优先从 README.md 的标题提取，回退到目录名
- **项目描述**：从 README.md 第一段提取，回退到默认模板
- **目录树**：自动生成（最大深度 2 层），过滤常见忽略项

#### 3. 语言检测

自动检测操作系统语言并映射到对话语言。

#### 4. 生成 AI 指令文档

根据检测到的项目类型，使用对应的工作流模板：

| 项目类型 | 默认工作流 |
|---------|-----------|
| Python | 代码开发 → 单元测试 → 文档更新 → 版本发布 |
| Web | 功能开发 → 组件测试 → 构建部署 → 监控反馈 |
| 数据科学 | 数据获取 → 探索分析 → 模型训练 → 验证评估 |
| Rust | API 设计 → 实现 → 单元测试 → 文档 → 发布 |
| Go | 需求分析 → API 设计 → 实现 → 集成测试 → 部署 |
| 通用 | 需求分析 → 设计 → 实现 → 验证 → 交付 |

**生成顺序**：
1. **AGENTS.md**：跨平台通用项目指令（Single Source of Truth）
2. **CLAUDE.md**：使用 `@./AGENTS.md` 引用 + Claude Code 特定适配

#### 5. 检查并生成 README.md

- 如果 README.md **不存在**：自动生成项目介绍
- 如果 README.md **已存在**：跳过（除非使用 `--overwrite`）

**README.md 内容**：
- 项目名称和描述
- 主要功能和特性
- 快速开始指南
- 目录结构说明
- AI 辅助开发说明（如何使用 Claude Code / Codex）

#### 6. 检查并生成 CHANGELOG.md（强制性）

- 如果 CHANGELOG.md **不存在**：自动创建初始版本
- 如果 CHANGELOG.md **已存在**：追加新的更改记录

**CHANGELOG.md 是项目管理的强制性要求**：
- **重要原则**：凡是项目的更新，都要统一在 CHANGELOG.md 文件里记录
- 记录范围：
  - 项目指令文件变更（CLAUDE.md、AGENTS.md 的任何修改）
  - 项目结构变更（新增/删除/重命名目录或关键文件）
  - 工作流变更（核心工作流程的调整）
  - 工程原则变更（新增、修改或删除工程原则）
  - 重要配置变更（影响项目行为的配置文件修改）
- 遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式
- 记录时机：
  - **修改前**：先在 `[Unreleased]` 部分草拟变更内容
  - **修改后**：完善变更描述，添加具体细节和影响范围

### 手动模式流程（可选）

如需手动指定信息，使用命令行参数：

```bash
python3 scripts/generate.py \
  --project-name "my-project" \
  --project-description "数据科学项目" \
  --workflow "数据获取 → 分析 → 可视化"
```

## 输出规范

生成的文档包含以下内容：

### AGENTS.md 结构

```markdown
# {项目名称} - 项目指令

你正在 `{工作目录}` 中工作：该目录用于 {项目用途}。

## 项目目标

{核心功能描述}

## 核心工作流

{根据项目类型自动生成的工作流}

## 工程原则

| 原则 | 在本项目中的体现 |
|------|------------------|
| KISS | 追求极致简洁；文档标题不使用序号前缀（用 `##` 而非 `## 1)`） |
| YAGNI | 只实现当前需要的功能 |
| DRY | 相似逻辑应抽象复用 |
| SOLID | 面向对象设计五大原则 |
| 关注点分离 | 不同层次逻辑应分离 |
| 奥卡姆剃刀 | 优先选择最简单的解决方案；Markdown 本身有层级结构，序号是冗余的形式化标记 |
| 最小惊讶原则 | 行为应符合用户直觉 |

## 默认语言

{自动检测的语言}

## 目录结构

{自动生成的目录树}

## 变更边界

- {修改范围限制}
- {保护性规则}

## 有机更新原则

1. 理解意图
2. 定位生态位
3. 协调更新
4. 保持一致性
```

### CLAUDE.md 结构（Claude Code 特定适配）

```markdown
# {项目名称} - Claude Code 项目指令

## 核心指令

@./AGENTS.md

## Claude Code 特定说明

### 文件引用规范

在 Claude Code 中引用文件时，使用 markdown 链接语法：
- 文件：`[filename.md](路径/filename.md)`
- 特定行：`[filename.md:42](路径/filename.md#L42)`
- 行范围：`[filename.md:42-51](路径/filename.md#L42-L51)`
- 目录：`[目录名/](路径/目录名/)`

### 任务管理

- 使用 TodoWrite 工具跟踪复杂任务的进度
- 完成任务后及时标记为 completed
- 拆分大任务为可管理的小步骤

### 代码变更规范

- 修改代码前先使用 Read 工具阅读文件
- 优先使用 Edit 工具进行精确修改
- 避免不必要的格式化或重构

### 与 AGENTS.md 的关系

- **AGENTS.md**：跨平台通用项目指令（Single Source of Truth）
- **CLAUDE.md**：通过 `@./AGENTS.md` 自动引用 + Claude Code 特定适配
- **维护流程**：修改 AGENTS.md → CLAUDE.md 自动生效 → 记录到 CHANGELOG.md
```

### README.md 结构（项目介绍）

{项目描述}

## 特性

- {特性 1}
- {特性 2}
- {特性 3}

## 快速开始

{根据项目类型生成的快速开始指南}

## 目录结构

{简化的目录说明}

## AI 辅助开发

本项目配置了 AI 辅助开发支持：

- **Claude Code**: 使用 `CLAUDE.md` 作为项目指令
- **OpenAI Codex CLI**: 使用 `AGENTS.md` 作为项目指令

### 使用方式

1. 在项目目录启动 Claude Code 或 Codex CLI
2. AI 会自动读取对应的指令文件
3. 按项目工作流进行开发

## 许可证

{默认 MIT，可根据需要修改}
```

### CHANGELOG.md 结构（项目变更记录 - 强制性）

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式：

```markdown
# Changelog

**重要**：本文件是项目变更的**唯一正式记录**。凡是项目的更新，都要统一在本文件里记录。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

## [{版本号}] - {日期}

### Added（新增）
- 初始化项目指令文件
- 生成 CLAUDE.md（Claude Code 项目指令）
- 生成 AGENTS.md（OpenAI Codex CLI 项目指令）

### Changed（变更）
{记录每次修改的内容，例如：修改了 XXX 章节：原因是 YYY}

### Fixed（修复）
{记录修复的问题}
```

**CHANGELOG.md 更新规则（强制性）**：
- 每次修改 CLAUDE.md 或 AGENTS.md 时，**必须**追加记录
- 记录修改原因、具体变更内容、影响范围
- 使用语义化版本号（推荐）
- 记录时机：修改前草拟，修改后完善
- 记录质量：清晰具体、可追溯、格式统一、及时更新

## 配置参数（config.yaml）

本技能使用 `config.yaml` 管理语言映射和默认模板。

## 错误处理

- **CLAUDE.md / AGENTS.md 已存在**：默认启用智能合并模式
  - **保留**：用户自定义的项目目标、核心工作流、变更边界、自定义章节
  - **更新**：工程原则、默认语言、目录结构、平台特定说明
  - **强制覆盖**：使用 `--overwrite` 参数完全替换现有内容
- **README.md 已存在**：默认跳过，使用 `--overwrite` 覆盖
- **语言检测失败**：回退到简体中文
- **无法识别项目类型**：使用通用项目模板

## 智能合并策略

当 CLAUDE.md 或 AGENTS.md 已存在时，脚本会自动进行智能合并：

### 保留的用户自定义内容
- `## 项目目标` 章节中的自定义描述（排除默认模板内容）
- `## 核心工作流` 章节中的自定义工作流
- `## 变更边界` 章节中的自定义规则
- 用户添加的自定义章节（不在标准模板中的章节）

### 更新的标准化内容
- `## 工程原则`：更新为最新的工程原则标准
- `## 默认语言`：更新为检测到的语言
- `## 目录结构`：更新为最新的目录树
- 平台特定说明：Claude Code / Codex CLI 特定部分

### 示例

假设用户已在 CLAUDE.md 中自定义了项目目标和工作流：

```markdown
## 项目目标
开发一个高性能的数据处理引擎，支持实时流处理和批量处理。
（这是用户自定义的内容）

## 核心工作流
需求分析 → 架构设计 → 核心开发 → 性能测试 → 部署上线
（这是用户自定义的工作流）
```

再次运行 `init-project` 时，这些自定义内容会被保留，而目录结构、工程原则等标准化内容会被更新。

## 使用示例

**场景 1：全新项目（完全自动化）**
```bash
# 在项目根目录执行
python3 init-project/scripts/generate.py --auto

# 输出示例：
# ✅ 已生成项目初始化文档:
#    - /path/to/project/AGENTS.md
#    - /path/to/project/CLAUDE.md
#
# 📊 项目分析结果:
#    名称: my-project
#    类型: Python 项目
#    语言: 简体中文
```

**场景 2：现有项目补全文档（智能合并）**
```bash
# 在现有项目目录执行（CLAUDE.md 和 AGENTS.md 已存在）
python3 init-project/scripts/generate.py --auto

# 输出示例：
# 🔄 /path/to/project/CLAUDE.md 已智能更新（保留了自定义内容）
# 🔄 /path/to/project/AGENTS.md 已智能更新（保留了自定义内容）
# ✅ 已生成 AI 项目指令文档:
#    - /path/to/project/CLAUDE.md
#    - /path/to/project/AGENTS.md
#
# 📊 项目分析结果:
#    名称: my-project
#    类型: Python 项目
#    语言: 简体中文
```

**场景 3：覆盖现有文档（完全替换）**
```bash
python3 init-project/scripts/generate.py --auto --overwrite

# 输出示例：
# ✅ 已生成 AI 项目指令文档:
#    - /path/to/project/CLAUDE.md
#    - /path/to/project/AGENTS.md
```

## 验证清单（交付前）

- [ ] 语言检测正确或用户已覆盖
- [ ] 项目信息完整（名称、目标、目录结构）
- [ ] AGENTS.md 包含所有必需章节（包括变更记录规范）
- [ ] CLAUDE.md 与 AGENTS.md 引用关系正确
- [ ] 工程原则章节完整
- [ ] 有机更新原则已包含
- [ ] **变更记录规范已明确**（CHANGELOG.md 强制性要求）
- [ ] 文件已成功写入磁盘
- [ ] CHANGELOG.md 已创建（强制性）

## 有机更新原则

当需要更新本文档时：

1. **理解意图**：用户真正想解决什么问题？
2. **定位生态位**：更新应该放在哪个位置？
3. **协调更新**：同步更新相关章节（如有）
4. **保持一致性**：术语、示例、引用保持统一
