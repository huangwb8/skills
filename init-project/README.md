# Init Project — 用户使用指南

本 README 面向**使用者**：教你如何使用 `init-project` 快速生成 AI 项目指令文档。

如果你在编辑/维护该 skill：执行指令与强制规范在 `init-project/SKILL.md`；可配置的数值口径集中在 `init-project/config.yaml`。

## 快速开始（推荐）

**完全自动化模式** — 一条命令搞定：

```bash
python3 init-project/scripts/generate.py --auto
```

脚本会自动：
- 检测项目类型（Python/Web/Rust/Go/Java/数据科学等）
- 从 README.md 提取项目名称和描述
- 生成目录树
- 检测操作系统语言
- 生成 CLAUDE.md（Claude Code 主指令文件）
- 生成 AGENTS.md（OpenAI Codex CLI 适配版本）
- 生成 README.md（如不存在）
- 生成 CHANGELOG.md（AI 优化历史记录）

## 生成的文件

| 文件 | 用途 | 平台 |
|------|------|------|
| **CLAUDE.md** | Claude Code 项目指令（主文件） | Claude Code |
| **AGENTS.md** | OpenAI Codex CLI 项目指令 | Codex CLI |
| **README.md** | 项目介绍与使用方法 | 通用 |
| **CHANGELOG.md** | AI 优化历史记录 | 通用 |

## 使用方式

### 方式一：命令行直接运行（最快）

```bash
# 在项目根目录执行
python3 init-project/scripts/generate.py --auto

# 如需覆盖现有文件
python3 init-project/scripts/generate.py --auto --overwrite
```

### 方式二：通过 Claude Code 触发

在 Claude Code 中说：

```
帮我生成项目的 AI 指令文件
```

或：

```
初始化项目
```

然后 AI 会运行自动模式脚本。

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--auto` | 完全自动模式：分析当前目录并生成文档 |
| `--overwrite` | 覆盖已存在的文件 |
| `--skip-readme` | 跳过 README.md 生成 |
| `--skip-changelog` | 跳过 CHANGELOG.md 生成 |
| `--only-readme` | 仅生成 README.md |
| `--only-changelog` | 仅生成 CHANGELOG.md |
| `--project-name` | 手动指定项目名称 |
| `--project-description` | 手动指定项目描述 |
| `--workflow` | 手动指定工作流 |
| `--language` | 手动指定默认语言 |
| `--output-dir` | 指定输出目录（默认当前目录） |
| `--detect-language-only` | 仅检测并显示系统语言 |

## 使用示例

### 完整生成（默认）

```bash
python3 init-project/scripts/generate.py --auto

# 输出：
# ✅ 已生成 AI 项目指令文档:
#    - /path/to/project/CLAUDE.md
#    - /path/to/project/AGENTS.md
#    - /path/to/project/README.md
#    - /path/to/project/CHANGELOG.md
#
# 📊 项目分析结果:
#    名称: my-awesome-project
#    类型: Python 项目
#    语言: 简体中文
```

### 仅生成 AI 指令（跳过 README 和 CHANGELOG）

```bash
python3 init-project/scripts/generate.py --auto --skip-readme --skip-changelog
```

### 仅更新 README.md

```bash
python3 init-project/scripts/generate.py --auto --only-readme --overwrite
```

### 手动指定项目信息

```bash
python3 init-project/scripts/generate.py \
  --project-name "my-project" \
  --project-description "数据科学项目" \
  --workflow "数据获取 → 分析 → 可视化"
```

## 支持的项目类型

脚本会自动识别以下项目类型：

| 类型 | 标志文件 |
|------|---------|
| Python | pyproject.toml, requirements.txt, setup.py |
| Web | package.json, yarn.lock, webpack.config.js |
| Rust | Cargo.toml, Cargo.lock |
| Go | go.mod, go.sum |
| Java | pom.xml, build.gradle |
| 数据科学 | *.ipynb, *.R, environment.yml |
| 文档 | docs/, mkdocs.yml |

## CLAUDE.md vs AGENTS.md

两个文件的核心内容保持一致，区别在于：

| 方面 | CLAUDE.md | AGENTS.md |
|------|-----------|-----------|
| 平台 | Claude Code | OpenAI Codex CLI |
| 文件引用 | Markdown 链接语法 | 内联代码格式 |
| 特定说明 | Claude Code 特定 | Codex CLI 特定 |
| 主/从关系 | 主文件 | 基于主文件适配 |

## CHANGELOG.md 用途

- 记录每次 CLAUDE.md 和 AGENTS.md 的修改
- 方便用户回顾 AI 的优化过程
- 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式
- 使用语义化版本号

## 常见问题

### Q: 生成后想修改怎么办？

A: 直接编辑生成的文件。修改后建议更新 `CHANGELOG.md` 记录变更。

### Q: 可以重新生成吗？

A: 使用 `--overwrite` 参数覆盖现有文件：
```bash
python3 init-project/scripts/generate.py --auto --overwrite
```

### Q: 语言检测错了怎么办？

A: 手动指定语言：
```bash
python3 init-project/scripts/generate.py --auto --language "English"
```

### Q: 我只想生成 CLAUDE.md 和 AGENTS.md？

A: 使用跳过参数：
```bash
python3 init-project/scripts/generate.py --auto --skip-readme --skip-changelog
```

### Q: 如何让 CLAUDE.md 和 AGENTS.md 保持同步？

A: 修改 CLAUDE.md 后，手动同步更新 AGENTS.md 的对应部分（核心内容保持一致，仅平台特定说明不同）。

## 验证生成结果

生成后，检查以下内容：

- [ ] `CLAUDE.md` 存在且包含项目目标、工作流、工程原则
- [ ] `AGENTS.md` 存在且与 CLAUDE.md 核心内容一致
- [ ] `README.md` 存在且包含项目介绍和使用方法（如生成）
- [ ] `CHANGELOG.md` 存在且包含初始版本记录（如生成）
- [ ] 默认语言设置正确
- [ ] 目录树与实际结构一致

## 技能触发关键词

在 Claude Code 中，以下表述会触发本技能：
- 初始化项目 / 新建项目 / init project
- 生成 AGENTS.md / 生成 CLAUDE.md
- 生成 AI 指令 / 生成项目指令
- 创建项目配置 / 项目文档
- 自动生成项目文档
- project initialization / setup project

---

**需要更多帮助？** 参考 `SKILL.md` 了解完整工作流和执行细节。
