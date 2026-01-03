---
name: init-project
description: 当用户要初始化一个新项目（在空目录或新建项目），需要生成 AGENTS.md 和 CLAUDE.md 项目指令文件时使用。完全自动化：自动检测操作系统默认语言，分析项目目录结构（支持 Python/Web/Rust/Go/Java/数据科学/文档项目等），推断项目类型和用途，一键生成规范的项目指令文档。适用于"初始化项目"、"新建项目配置"、"生成项目文档"、"自动生成 AGENTS.md"等场景。
metadata:
  short-description: 完全自动生成项目初始化文档（AGENTS.md + CLAUDE.md）
  keywords:
    - 项目初始化
    - 初始化项目
    - 新建项目
    - 项目配置
    - 项目文档
    - AGENTS.md
    - CLAUDE.md
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
---

# Init Project（项目初始化文档生成器）

## 目标

为全新项目快速生成规范的 **AGENTS.md** 和 **CLAUDE.md** 文件，使 AI 助手（Codex / Claude Code）能够理解项目目标、遵循工程原则、按预期行为协作。

## 核心特性

- **完全自动化**：一键生成，无需手动输入信息
- **智能项目分析**：自动检测项目类型（Python/Web/Rust/Go/Java/数据科学/文档等）
- **自动语言检测**：检测操作系统默认语言并设为对话默认语言
- **目录结构推断**：分析现有文件和目录，自动生成目录树
- **README 解析**：从 README.md 提取项目名称和描述
- **工程原则内置**：基于 SOLID、KISS、DRY、YAGNI、关注点分离等原则
- **有机更新框架**：生成的文档本身遵循有机更新原则，便于未来迭代

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
5. 生成并写入 AGENTS.md 和 CLAUDE.md

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

#### 4. 生成文档

根据检测到的项目类型，使用对应的工作流模板：

| 项目类型 | 默认工作流 |
|---------|-----------|
| Python | 代码开发 → 单元测试 → 文档更新 → 版本发布 |
| Web | 功能开发 → 组件测试 → 构建部署 → 监控反馈 |
| 数据科学 | 数据获取 → 探索分析 → 模型训练 → 验证评估 |
| Rust | API 设计 → 实现 → 单元测试 → 文档 → 发布 |
| Go | 需求分析 → API 设计 → 实现 → 集成测试 → 部署 |
| 通用 | 需求分析 → 设计 → 实现 → 验证 → 交付 |

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
| KISS | 追求极致简洁 |
| YAGNI | 只实现当前需要的功能 |
| DRY | 相似逻辑应抽象复用 |
| SOLID | 面向对象设计五大原则 |
| 关注点分离 | 不同层次逻辑应分离 |
| 奥卡姆剃刀 | 优先选择最简单的解决方案 |
| 最小惊讶原则 | 行为应符合用户直觉 |

## 默认语言

{自动检测的语言，如：除非用户明确要求其他语言，始终使用简体中文与用户对话与撰写文档/说明。}

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

### CLAUDE.md 结构

```markdown
# {项目名称} - Claude Code 项目指令

## Claude Code 环境特定说明

本文件保留用于 Claude Code 特定的配置和实践说明。通用项目指令见 AGENTS.md。

## 在 Claude Code 中的工作流

{平台特定工作流实现}

## 文件引用规范

在 Claude Code 中引用文件时，使用 markdown 链接语法：
- 文件：`[filename.md](路径/filename.md)`
- 特定行：`[filename.md:42](路径/filename.md#L42)`
- 行范围：`[filename.md:42-51](路径/filename.md#L42-L51)`
- 目录：`[目录名/](路径/目录名/)`

## Claude Code 特定验证要点

完成项目任务后，额外检查：
- [ ] 检查项根据项目类型自动调整
- [ ] 路径是否使用正斜杠
- [ ] 文件引用是否使用 markdown 链接

## 与 AGENTS.md 的关系

- **AGENTS.md**：通用项目指令（Codex + Claude Code 共享）
- **CLAUDE.md**：Claude Code 特定补充
```

## 配置参数（config.yaml）

本技能使用 `config.yaml` 管理语言映射和默认模板。

## 错误处理

- **文件已存在**：默认不覆盖，使用 `--overwrite` 参数强制覆盖
- **语言检测失败**：回退到简体中文
- **无法识别项目类型**：使用通用项目模板

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

**场景 2：现有项目补全文档**
```bash
# 在现有项目目录执行
python3 init-project/scripts/generate.py --auto
```

**场景 3：覆盖现有文档**
```bash
python3 init-project/scripts/generate.py --auto --overwrite
```

## 验证清单（交付前）

- [ ] 语言检测正确或用户已覆盖
- [ ] 项目信息完整（名称、目标、目录结构）
- [ ] AGENTS.md 包含所有必需章节
- [ ] CLAUDE.md 与 AGENTS.md 引用关系正确
- [ ] 工程原则章节完整
- [ ] 有机更新原则已包含
- [ ] 文件已成功写入磁盘

## 有机更新原则

当需要更新本文档时：

1. **理解意图**：用户真正想解决什么问题？
2. **定位生态位**：更新应该放在哪个位置？
3. **协调更新**：同步更新相关章节（如有）
4. **保持一致性**：术语、示例、引用保持统一
