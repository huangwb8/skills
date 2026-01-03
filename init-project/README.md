# Init Project — 用户使用指南

本 README 面向**使用者**：教你如何使用 `init-project` 快速生成项目初始化文档。

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
- 生成 AGENTS.md 和 CLAUDE.md

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
帮我生成项目的 AGENTS.md 和 CLAUDE.md
```

然后 AI 会运行自动模式脚本。

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

## 手动模式（可选）

如需手动指定项目信息：

```bash
python3 init-project/scripts/generate.py \
  --project-name "my-project" \
  --project-description "数据科学项目" \
  --workflow "数据获取 → 分析 → 可视化"
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--auto` | 完全自动模式：分析当前目录并生成文档 |
| `--overwrite` | 覆盖已存在的文件 |
| `--project-name` | 手动指定项目名称 |
| `--project-description` | 手动指定项目描述 |
| `--workflow` | 手动指定工作流 |
| `--language` | 手动指定默认语言 |
| `--output-dir` | 指定输出目录（默认当前目录） |
| `--detect-language-only` | 仅检测并显示系统语言 |

## 输出示例

```bash
$ python3 init-project/scripts/generate.py --auto

✅ 已生成项目初始化文档:
   - /path/to/project/AGENTS.md
   - /path/to/project/CLAUDE.md

📊 项目分析结果:
   名称: my-awesome-project
   类型: Python 项目
   语言: 简体中文
```

## 常见问题

### Q: 生成后想修改怎么办？

A: 直接编辑生成的 `AGENTS.md` 和 `CLAUDE.md` 文件。这两个文件是你的项目文档，可以随时修改。

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

### Q: 我的项目很特殊，识别错了？

A: 使用手动模式指定信息，或编辑生成的文档。

## 验证生成结果

生成后，检查以下内容：

- [ ] `AGENTS.md` 存在且包含项目目标
- [ ] `CLAUDE.md` 存在且引用了 `AGENTS.md`
- [ ] 默认语言设置正确
- [ ] 目录树与实际结构一致
- [ ] 工程原则章节完整

## 技能触发关键词

在 Claude Code 中，以下表述会触发本技能：
- 初始化项目 / 新建项目 / init project
- 生成 AGENTS.md / 生成 CLAUDE.md
- 创建项目配置 / 项目文档
- 自动生成项目文档
- project initialization / setup project

---

**需要更多帮助？** 参考 `SKILL.md` 了解完整工作流和执行细节。
