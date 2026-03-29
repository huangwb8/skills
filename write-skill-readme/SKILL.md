---
name: write-skill-readme
description: 当用户明确要求"生成技能 README"、"编写用户指南"或"更新技能文档"时使用。为 Agent Skills 编写符合最佳实践的 README.md 用户使用指南。自动分析技能结构（SKILL.md、config.yaml、scripts/），按模板生成小白友好的文档。

metadata:
  author: Bensz Conan
  short-description: 自动生成技能的用户使用指南 README.md
  keywords:
    - write-skill-readme
    - README generation
    - skill documentation
---

# Write Skill README

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求“report bensz skills bugs”等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

为 Agent Skills 编写符合最佳实践的 README.md 用户使用指南。

## 触发条件

用户要求为技能生成/编写/更新 README.md、用户使用指南、技能文档时使用本技能。

## 核心工作流

> ⚠️ 安全限制：本技能**仅用于生成/更新 README.md 文件**，**永远不能修改目标技能的任何现有内容**（包括但不限于 SKILL.md、SKILL.yaml、config.yaml、scripts/、references/ 等）。只能读取这些文件作为分析输入，不能对它们执行任何写入或编辑操作。

### 步骤 1：分析技能结构

读取并分析以下文件：

1. **SKILL.yaml** — 技能元数据（name、description、version、author、metadata）
2. **SKILL.md** — 技能核心规范（触发条件、工作流、输入输出）
3. **config.yaml**（可选）— 可配置参数
4. **scripts/** 目录（可选）— 硬编码用法
5. **references/** 目录（可选）— 参考文档

### 步骤 2：确定 README 类型

根据技能特性选择模板：

| 技能类型 | 特征 | 推荐模板 |
|---------|------|---------|
| **功能型** | 主要通过 Prompt 触发，有明确工作流 | 模板 A：systematic-literature-review 风格 |
| **工具型** | 主要通过脚本/命令行调用 | 模板 B：install-bensz-skills 风格 |
| **混合型** | Prompt 优先 + 脚本备选 | 模板 C：make_latex_model 风格 |

### 步骤 3：生成核心章节

按以下顺序生成 README.md 内容：

#### 3.1 标题与受众声明

```markdown
# {技能名称} — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `{技能名称}` skill。
执行指令与硬性规范在 `SKILL.md`；默认参数在 `config.yaml`。
```

#### 3.2 快速开始（核心章节）

**原则**：Prompt 章节要**短、直观、可复制**。优先给用户一个“最小可用”的通用格式，让用户一眼就知道：用哪个 skill、输入是什么、会产出什么。

包含内容（推荐最小集合）：
- **常规 Prompt（最小可用）**（1 个）— 必须用统一格式说明“用哪个 skill / 输入 / 输出”
- **进阶 Prompt（可选）**（1 个）— 在常规 Prompt 基础上追加“参数约束”，不展开长篇叙述

常规 Prompt 模板（写进 README，作为“最推荐用法”）：

```text
请使用 {skill_name} skill {完成xxx任务}
输入：{输入是什么（文件/路径/URL/文字/文件夹等）}
输出：{输出是什么（文件/路径/格式/数量等）}
```

进阶 Prompt 模板（写进 README，作为“进阶用法/带参数约束”）：

```text
{常规Prompt}
另外，还有下列参数约束：
- 参数1：{说明}
- 参数2：{说明}
```

#### 3.3 设计理念 / 功能概述

解释：
- 技能的核心价值
- 工作原理（简化版，面向小白）
- 设计哲学（如有）
- 与其他技能的区别/配合使用

#### 3.4 提示词示例 / 使用示例

按**场景分类 + 渐进式复杂度**组织（但每条示例仍保持短小，避免把 README 写成“参数手册”）：

```
### 示例 1：[场景描述]（最简单）

```
Prompt
```

### 示例 2：[场景描述]

```
Prompt
```

```

#### 3.5 输出文件 / 配置选项

列出技能生成的文件或可配置参数，用表格或列表呈现。

#### 3.6 备选用法（如有硬编码）

**仅当技能有脚本调用方式时**添加此章节：

```markdown
## 备选用法（脚本/硬编码流程）

### 步骤 1：[做什么]

```bash
command
```
```

#### 3.7 常见问题（FAQ）

预测小白用户可能遇到的问题，用 Q&A 形式解答。

### 步骤 4：应用风格规范

遵循以下风格规范：

#### 4.1 小白友好设计

- 使用**表格**呈现决策指南（如"你的需求 → 推荐档位 → 理由"）
- 提供**丰富别名**（如"旗舰级、顶刊级、高级"）
- 使用**对话式呈现**（"你：... / 技能：..."）
- 代码块添加**行内注释**（注释在命令前）

#### 4.2 硬编码用法处理

- **Prompt 调用**标记为"推荐用法"
- **脚本调用**标记为"备选用法"
- 硬编码用法放在 README **最后**

#### 4.3 语言风格

- 使用**第二人称**（"你"）
- **有选择地使用 emoji**（特性列表 ✨、状态标记 ✅、章节标题 📖）
- 技术术语用**代码高亮**（`` `SKILL.md` ``、`` `/path/to/file` ``）

### 步骤 5：输出 README.md

将生成的内容写入技能目录下的 `README.md`。

## 输出文件

- `README.md` — 技能的用户使用指南

## 参考文档

- [README 结构模板](references/README-templates.md) — 三种典型模板的详细结构
- [风格规范清单](references/style-guidelines.md) — 完整的风格规范和检查清单
- [Prompt 编写指南](references/prompt-writing-guide.md) — 如何编写经典 Prompt 和变异 Prompt

## 常见问题

### Q：如何确定"经典 Prompt"？

A：经典 Prompt 应该是：
1. **最简单**的可用用法（最小可执行）
2. **最常用**的场景（覆盖 80% 用户需求）
3. **已验证可靠**（在实际使用中测试过）

### Q：变异 Prompt 要写多少个？

A：默认 1-2 个就够（常规 Prompt + 进阶 Prompt）。只有当技能确实存在多个高频输入源/输出形态时，再补 1-2 个场景化变体：
- 按复杂度递增（最小可用 → 带参数约束）
- 按场景分类（不同输入源、不同输出格式）
- 避免过度细分（不要为每个参数组合都写一个 Prompt）

### Q：什么时候需要"备选用法"章节？

A：仅当技能满足以下条件之一时：
1. 有独立的 `scripts/` 可以直接运行
2. 支持命令行参数调用
3. 有 API 或其他编程接口

如果技能只能通过 Prompt 触发，则不需要此章节。

### Q：如何处理"小白用户看不懂的技术细节"？

A：
1. **移除**：如果对使用者没用，直接删除
2. **简化**：用通俗语言解释，避免专业术语
3. **后置**：放在 FAQ 或"更多文档"章节
4. **引用**：指向 SKILL.md 或 references/
