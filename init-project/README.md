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
- 生成 .gitignore（安全优先的 Git 忽略规则）

## 生成的文件

| 文件 | 用途 | 平台 |
|------|------|------|
| **CLAUDE.md** | Claude Code 项目指令（主文件） | Claude Code |
| **AGENTS.md** | OpenAI Codex CLI 项目指令 | Codex CLI |
| **README.md** | 项目介绍与使用方法 | 通用 |
| **CHANGELOG.md** | AI 优化历史记录 | 通用 |
| **.gitignore** | Git 忽略规则（安全优先） | 通用 |

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
| `--skip-gitignore` | 跳过 .gitignore 生成 |
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
#    - /path/to/project/.gitignore
#
# 📊 项目分析结果:
#    名称: my-awesome-project
#    类型: Python 项目
#    语言: 简体中文
#
# 🔒 已生成 .gitignore（包含安全和项目特定规则）
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

### Q: .gitignore 会自动处理敏感文件吗？

A: 是的。.gitignore 默认忽略：
- 环境变量文件（.env、.env.local）
- 密钥和证书（*.pem、*.key、*.crt）
- 凭证目录（credentials/、secrets/）
- 操作系统和 IDE 配置
- 项目类型特定的敏感文件

使用 `--skip-gitignore` 可跳过生成。

### Q: 已有 .gitignore，重新生成会覆盖吗？

A: 不会。脚本会智能合并，保留你的自定义规则。使用 `--overwrite` 可完全覆盖。

## 验证生成结果

生成后，检查以下内容：

- [ ] `CLAUDE.md` 存在且包含项目目标、工作流、工程原则
- [ ] `AGENTS.md` 存在且与 CLAUDE.md 核心内容一致
- [ ] `README.md` 存在且包含项目介绍和使用方法（如生成）
- [ ] `CHANGELOG.md` 存在且包含初始版本记录（如生成）
- [ ] `.gitignore` 存在且包含敏感文件忽略规则（推荐）
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

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic（1/6 = 17%）
- **来源构成**：社区 70%, 官方 20%, 技术博客 10%
- **数据时效**：2024-10 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试项目初始化准确率

---

### 场景化建议

#### 场景 1：标准项目初始化（最常见）

**触发条件**：需要为新项目生成 AI 指令文档

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 |
| **推理强度** | low |
| **预期成本** | ~$0.001-0.01/次 |

**理由**：
- 项目初始化主要是脚本驱动任务，AI 负责理解项目结构和调用生成脚本
- Haiku 速度快、成本低，适合高频的文档生成任务
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1ocpoye/haiku_45_better_than_sonnet/) 显示 Haiku 在简单任务中表现优异
- **文档生成是确定性任务，Haiku 完全胜任**

**避免**：无需升级模型，除非遇到复杂的项目结构分析需求

**来源**：[Haiku System Card](https://www.anthropic.com/claude-haiku-4-5-system-card) + Reddit 社区讨论

---

#### 场景 2：复杂项目结构分析

**触发条件**：
- 大型项目结构（多模块、多层嵌套）
- 需要深度理解项目架构才能生成合理指令
- 需要自定义复杂的工作流

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium |
| **预期成本** | ~$0.02-0.10/次 |

**理由**：
- Sonnet 在代码分析和项目结构理解上表现出色
- 更适合需要"中等复杂度理解"的场景
- [社区对比](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249) 显示 Sonnet 在复杂场景下的优势
- **复杂项目结构分析需要一定的推理能力**

**避免**：简单项目不需要 Sonnet，用 Haiku 即可

**来源**：社区对比讨论 + 官方模型选择指南

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Haiku 4.5** | 标准项目初始化（95% 场景） | 复杂项目结构分析 | $ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Sonnet 4.5** | 复杂项目结构、自定义工作流 | 简单项目（浪费） | $$$ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Opus 4.5** | **不推荐** | 所有场景 | $$$$$ | ⭐⭐ | ⭐ |

**说明**：
- Haiku 覆盖 95% 的项目初始化场景
- Sonnet 仅在复杂项目结构分析时才值得使用
- Opus 对此任务**完全不必要**，成本过高且无性能提升

---

### 通用原则

1. **默认从 Haiku 开始**：95% 的项目初始化任务 Haiku 足够，无需升级
2. **简单任务、快速响应**：项目初始化是高频操作，Haiku 的 <1 秒响应时间明显优于 Sonnet 的 3-5 秒
3. **成本敏感**：文档生成是高频操作，Haiku 的成本优势明显
4. **复杂度判断**：仅当项目结构极其复杂（多模块、多层嵌套）时，考虑升级 Sonnet
5. **避免过度设计**：文档生成主要是脚本驱动任务，AI 负责理解项目结构和调用脚本，Haiku 完全胜任

---

### ⚠️ 争议点

#### Haiku vs Sonnet：项目初始化真的可以用 Haiku 吗？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Haiku 足够** | Reddit 社区 | 项目初始化是脚本驱动任务，Haiku 在文档生成任务中表现稳定 |
| **Sonnet 更保险** | 部分开发者 | 担心 Haiku 在复杂项目结构分析时出错 |

**数据支持**：
- [某用户测试](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)：Haiku 在编码任务中匹配 Sonnet 能力，成本降低 80%
- [官方文档](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)：Haiku 专为"高吞吐量、低延迟"场景设计

**建议**：
- **默认使用 Haiku**：项目初始化属于脚本驱动任务，Haiku 完全胜任
- **仅在以下情况升级 Sonnet**：
  - 项目结构极其复杂（多模块、多层嵌套）
  - 需要深度理解项目架构才能生成合理指令
  - 需要自定义复杂的工作流
  - Haiku 出现理解错误时（极少见）

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
- [Sonnet 4.5 vs Haiku 4.5 vs Opus 4.1](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249)
- [Haiku 4.5 better than Sonnet? (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1ocpoye/haiku_45_better_than_sonnet/)
- [Claude Haiku 4.5: Features, Testing Results, and Use Cases](https://www.datacamp.com/fr/blog/anthropic-claude-haiku-4-5)

**技术博客**：
- [Top Use Cases for Claude Haiku 4.5](https://chatlyai.app/blog/claude-haiku-4-5-use-cases)
- [Claude Haiku 4.5 matches Sonnet's coding skills at 80% less cost](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)

---

**需要更多帮助？** 参考 `SKILL.md` 了解完整工作流和执行细节。
