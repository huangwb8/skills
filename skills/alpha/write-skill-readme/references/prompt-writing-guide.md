# Prompt 编写指南

本文档详细说明如何为技能 README 编写经典 Prompt 和场景化变异 Prompt。

目录
- [经典 Prompt 设计原则](#经典-prompt-设计原则)
- [场景化变异 Prompt 设计](#场景化变异-prompt-设计)
- [Prompt 模板库](#prompt-模板库)
- [常见场景的 Prompt 示例](#常见场景的-prompt-示例)

---

## 经典 Prompt 设计原则

### 定义

**经典 Prompt**（Classic Prompt）是技能 README 中"快速开始"章节的第一个 Prompt，代表：

- **最简单**的可用用法（最小可执行）
- **最常用**的场景（覆盖 80% 用户需求）
- **已验证可靠**（在实际使用中测试过）

### 设计步骤

#### 步骤 1：识别核心功能

问自己：这个技能解决的核心问题是什么？

**示例**（systematic-literature-review）：

- 核心问题：写一篇系统综述
- 关键要素：主题、档位、参考文献时间范围

#### 步骤 2：提炼最小可执行

问自己：最少的必需信息是什么？

**示例**：

```markdown
❌ 过于详细：
"请使用 systematic-literature-review skill 写一篇关于'HER2-ADC在乳腺癌中的研究进展'的Premium级综述，
参考文献以近2023-2025年为主，更早之前的文献如果特别相关特别重要的也可以纳入，
要有一个小节专门讨论未来3年较有前景的研究方向，工作目录名为HER2-ADC-01，
确保引用格式正确，输出PDF和Word版本..."

✅ 最小可执行：
"请使用 systematic-literature-review skill 写一篇'HER2-ADC在乳腺癌中的研究进展'的Premium级综述。
输入：主题（文字）
输出：该 skill 的默认交付物（见该 skill 的 README/说明）"
```

#### 步骤 3：添加关键参数

在最小可执行基础上，添加**最关键**的 1-2 个参数：

**示例**：

```markdown
✅ 经典 Prompt：
"请使用 systematic-literature-review skill 写一篇'HER2-ADC在乳腺癌中的研究进展'的Premium级综述。
输入：主题（文字）
输出：该 skill 的默认交付物（见该 skill 的 README/说明）
另外，还有下列参数约束：
- 参考范围：近 2023-2025 年为主（更早但特别重要的也可纳入）
- 结构要求：增加“未来 3 年研究方向”小节
- 输出控制：工作目录名为 HER2-ADC-01"
```

**添加的关键参数**：
- "更早之前的文献，如果特别相关、特别重要的，也可以纳入"（灵活性）
- "要有一个小节，专门讨论出未来3年较有前景的研究方向"（特定需求）
- "工作目录名为 HER2-ADC-01"（输出控制）

### 经典 Prompt 检查清单

- [ ] 是否能用**一句话**概括核心功能？
- [ ] 是否包含**必需参数**（不能省略）？
- [ ] 是否避免了**过度细节**（可选参数放后面）？
- [ ] 是否**已验证可靠**（测试过）？
- [ ] 是否用**自然语言**表达（非技术术语）？

---

## 场景化变异 Prompt 设计

### 定义

**场景化变异 Prompt**（Variant Prompt）是针对不同使用场景优化的 Prompt 变体，覆盖：

- 不同输入源（文件、图片、URL）
- 不同输出格式（PDF、Word、Markdown）
- 不同复杂度级别（简单、中等、复杂）
- 不同使用场景（首次使用、进阶用法、特殊需求）

### 设计原则

#### 原则 1：渐进式复杂度

按"最简单 → 中等 → 复杂"的顺序排列：

```markdown
### 示例 1：从自然语言提取（最简单）

```
用户：帮我提取综述主题：Transformer 在自然语言处理中的应用
```

### 示例 2：从文件提取

```
用户：从这个文件提取综述主题：/path/to/research-notes.md
```

### 示例 3：从图片提取

```
用户：从这张图片提取综述主题：/path/to/screenshot.png
```

### 示例 4：从网页 URL 提取（高级）

```
用户：从这个网页提取综述主题：https://arxiv.org/abs/2301.xxxxx
```
```

#### 原则 2：场景化标题

每个 Prompt 的标题应该：

- 说明**输入源**（从文件、从图片、从 URL）
- 标注**复杂度**（最简单、中等、高级）
- 描述**场景特征**（首次发布、常规版本、预发布）

**示例**：

```markdown
✅ 好的标题：
- "示例 1：从自然语言提取（最简单）"
- "示例 2：首次发布"
- "示例 3：指定项目路径"
- "示例 4：预发布版本（beta/rc）"

❌ 差的标题：
- "示例 1"
- "示例 2"
- "另一种用法"
- "高级"
```

#### 原则 3：对话式呈现

对于简单场景，使用对话式呈现（"你：... / 技能：..."）：

```markdown
### 示例 1：首次发布

```
你：发布 v1.0.0 到 GitHub

技能：检测到这是首次发布，将创建项目第一个 Release。
```
```

对于复杂场景，使用直接 Prompt：

```markdown
### 示例 4：指定项目路径和自定义 Release Notes

```
为 /path/to/project 发布 v2.3.0，
Release Notes 标题用"重大更新：XXX"，内容包括：...
```
```

### 变异 Prompt 的数量控制

**默认建议数量**：1-2 个（常规 Prompt + 进阶 Prompt）

只有在“用户确实会经常遇到不同输入源/不同输出形态”时，再补 1-2 个场景化变体（避免把 README 写成参数手册）。

**选择策略**：

| 用户群体 | 变异 Prompt 聚焦点 |
|---------|------------------|
| 小白用户 | 最简单用法 + 一个常见场景 |
| 中级用户 | 常规 + 进阶 + 1-2 个不同场景的变体 |
| 高级用户 | 2-4 个高价值示例（优先覆盖不同输入源/不同输出形态） |

**反模式**：不要为每个参数组合都写一个 Prompt

```markdown
❌ 差：
- 示例 1：Premium 档位
- 示例 2：Standard 档位
- 示例 3：Lite 档位
- 示例 4：Premium + 指定时间范围
- 示例 5：Standard + 指定时间范围
- 示例 6：Lite + 指定时间范围
...

✅ 好：
- 示例 1：基础用法（Standard 档位）
- 示例 2：高级用法（Premium 档位 + 自定义时间范围）
- 示例 3：快速用法（Lite 档位）
```

---

## Prompt 模板库

### 模板 1：功能型技能（Prompt 触发）

**适用**：主要用 Prompt 触发的技能

```markdown
## 快速开始

- 最推荐用法

```
请使用 {skill_name} skill {完成xxx任务}
输入：{输入是什么（文件/路径/URL/文字/文件夹等）}
输出：{输出是什么（文件/路径/格式/数量等）}
```

- 结合 {其他技能/工具} 用

```
请使用 {skill_name} skill {完成xxx任务}，基于 {前置条件}
输入：{输入是什么}
输出：{输出是什么}
```

## 提示词示例

### 示例 1：{场景描述}（最简单）

```
请使用 {skill_name} skill {完成xxx任务}
输入：{输入是什么}
输出：{输出是什么}
```

### 示例 2：{场景描述}

```
{Prompt}
```

### 示例 3：{场景描述}

```
{Prompt}
```
```

### 模板 2：混合型技能（Prompt + 脚本）

**适用**：Prompt 优先，脚本备选的技能

```markdown
## 推荐用法（Prompt 调用 Skill）

在 Claude Code / OpenAI Codex CLI 里，通常**优先用自然语言 Prompt** 触发 Skill
（而不是手动跑脚本）。下面这条 Prompt 已验证可靠：

```
请使用 {skill_name} skill {完成xxx任务}
输入：{输入是什么}
输出：{输出是什么}
```

也可以直接使用脚本（备选）：

```bash
python3 skills/{技能名}/scripts/{脚本名}.py {参数}
```

## 备选用法（脚本/硬编码流程）

### 步骤 1：{步骤描述}

```bash
{命令}
```
```

### 模板 3：工具型技能（脚本为主）

**适用**：主要用脚本调用的技能

```markdown
## 快速开始

```bash
# 最常用命令（带注释）
{命令}

# 其他常用命令
{命令}
```

## 使用示例

### 示例 1：{场景}

```bash
{命令}
```

### 示例 2：{场景}

```bash
{命令}
```
```

---

## 常见场景的 Prompt 示例

### 场景 1：文档生成类技能

**典型技能**：systematic-literature-review、nsfc-*-writer

**经典 Prompt**：

```markdown
请使用 {skill_name} skill {写/生成} {文档类型} "{主题}"
输入：主题（文字/文件/文件夹/URL 等）
输出：{输出文件与格式}
另外，还有下列参数约束：
- 档位：{Premium/Standard/Lite}
- 范围：{时间范围/地域范围/其他范围}
- 特殊需求：{可选的特殊要求}
```

**变异 Prompt 示例**：

```markdown
### 示例 1：基础用法（Standard 档位）

```
请用 systematic-literature-review 写一篇"Transformer在自然语言处理中的应用"的Standard级综述。
```

### 示例 2：高级用法（Premium 档位 + 自定义时间范围）

```
请用 systematic-literature-review 写一篇"大语言模型在医疗诊断中的应用"的Premium级综述。
参考文献以2024-2025年为主，重点关注临床试验研究。
```

### 示例 3：基于现有文档扩展

```
/Volumes/2T01/xxx/调研报告.md 是一个初步调研；
请基于相关主题，用 systematic-literature-review 写一篇Premium级综述。
```
```

### 场景 2：文件处理类技能

**典型技能**：get-review-theme、pdf-extractor

**经典 Prompt**：

```markdown
请使用 {skill_name} skill {提取/分析} {目标内容}
输入：{输入源（文件/图片/URL/文字等）}
输出：{结构化结果/文件/报告等}
```

**变异 Prompt 示例**：

```markdown
### 示例 1：从自然语言提取（最简单）

```
用户：帮我提取综述主题：Transformer 在自然语言处理中的应用，
关键词包括 BERT、GPT、注意力机制、预训练模型。
```

### 示例 2：从文件提取

```
用户：从这个文件提取综述主题：/path/to/research-notes.md
```

### 示例 3：从图片提取

```
用户：从这张图片提取综述主题：/path/to/screenshot.png
```
```

### 场景 3：项目初始化类技能

**典型技能**：init-project、make-latex-model

**经典 Prompt**：

```markdown
请使用 {skill_name} skill {初始化/改造} {项目路径}
输入：项目路径
输出：初始化后的项目结构/生成的文件
```

**变异 Prompt 示例**：

```markdown
### 示例 1：初始化新项目

```
用 init-project 初始化 /path/to/new-project
```

### 示例 2：改造现有项目

```
用 make-latex-model 对 projects/NSFC_Young 进行改造，
使其与 template/word_baseline.pdf 对齐。
```

### 示例 3：指定模板

```
用 init-project 初始化 /path/to/project，使用 python-data-science 模板。
```
```

### 场景 4：发布/版本管理类技能

**典型技能**：git-publish-release、release-project-to-github

**经典 Prompt**：

```markdown
{发布/推送} {版本号} {到 GitHub/远端}。
```

**变异 Prompt 示例**：

```markdown
### 示例 1：首次发布

```
你：发布 v1.0.0 到 GitHub

技能：检测到这是首次发布，将创建项目第一个 Release。
```

### 示例 2：常规版本发布

```
你：发布 v2.3.0

技能：将比较 v2.2.0 和 v2.3.0 之间的变化，生成 Release Notes。
```

### 示例 3：预发布版本

```
你：发布 v3.0.0-beta.1

技能：检测到这是预发布版本（beta），将标记为 prerelease。
```

### 示例 4：指定项目路径

```
你：为 /path/to/project 发布 v1.5.0
```
```

---

## Prompt 优化技巧

### 技巧 1：参数默认化

对于有默认值的参数，可以在 Prompt 中省略：

```markdown
❌ 过于详细：
"用 systematic-literature-review 写综述，档位 Standard，语言中文，
格式 PDF，引用格式 APA，..."

✅ 利用默认值：
"用 systematic-literature-review 写一篇'XXX'的Standard级综述。"
```

### 技巧 2：括号标注可选

用括号标注可选内容，降低认知负荷：

```markdown
✅ 好：
"用 systematic-literature-review 写一篇'XXX'的Premium级综述
（可选：指定参考文献时间范围为 2023-2025 年）"
```

### 技巧 3：分句降低复杂度

将复杂 Prompt 拆分为多个短句：

```markdown
❌ 一句到底：
"请用 systematic-literature-review 写一篇关于 HER2-ADC 在乳腺癌中的研究进展的 Premium 级综述参考文献以近 2023-2025 年为主更早之前的文献如果特别相关特别重要的也可以纳入要有一个小节专门讨论未来 3 年较有前景的研究方向工作目录名为 HER2-ADC-01"

✅ 分句表达：
"请用 systematic-literature-review 写一篇'HER2-ADC在乳腺癌中的研究进展'的Premium级综述。
参考文献以近2023-2025年为主，更早之前的文献，如果特别相关、特别重要的，也可以纳入。
要有一个小节，专门讨论出未来3年较有前景的研究方向。工作目录名为 HER2-ADC-01。"
```

### 技巧 4：示例先行

对于复杂概念，先用示例再说明：

```markdown
✅ 好：
### 三档位对照表

| 档位 | 字数范围 | 参考文献数 |
|------|---------|-----------|
| Premium | 10000–15000 | 80–150 |
| Standard | 6000–10000 | 50–90 |
| Lite | 3000–6000 | 30–50 |

**如何选择**：投稿顶刊用 Premium，学位论文用 Standard，快速了解用 Lite。

❌ 差：
**如何选择**：
Premium 档位适用于投稿顶刊的情况，字数范围 10000-15000，参考文献 80-150 篇...
Standard 档位适用于...
```
