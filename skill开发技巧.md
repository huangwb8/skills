---
除非用户要求查看，否则ai工作时不应查看这个文件。
---

# Agent Skills 开发技巧集锦

本文档综合了 [Agent Skills 官方规范](https://agentskills.io)、[Claude 官方最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) 以及社区经验，为 Agent Skills 开发提供实用指导。

> **核心理念**：Skills 是"按需加载的结构化提示词"，遵循 **有机整体更新** 原则——每次更新都考虑其对整个技能生态系统的影响。

## 目录

- [核心原则](#核心原则)
- [YAML Frontmatter 最佳实践](#yaml-frontmatter-最佳实践)
- [SKILL.md 内容组织](#skillmd-内容组织)
- [目录结构设计](#目录结构设计)
- [脚本与代码规范](#脚本与代码规范)
- [测试与迭代](#测试与迭代)
- [常见反模式](#常见反模式)
- [平台特定注意事项](#平台特定注意事项)

---

## 核心原则

### 1. 简洁至上 (Concise is Key)

**上下文窗口是公共资源**。启动时只加载所有 Skills 的 metadata（name 和 description），SKILL.md 主体按需加载。

**编写时的自我拷问**：
- "Claude 真的需要这个解释吗？"
- "我能假设 Claude 已经知道这个吗？"
- "这个段落值得消耗这些 token 吗？"

**示例对比**：

```markdown
<!-- ✅ 好：简洁 (~50 tokens) -->
## Extract PDF text
Use pdfplumber for text extraction:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

<!-- ❌ 差：冗长 (~150 tokens) -->
## Extract PDF text
PDF (Portable Document Format) files are a common file format...
To extract text from a PDF, you'll need to use a library...
[冗长的安装说明和基础解释...]
```

### 2. 适度自由度原则 (Degrees of Freedom)

根据任务的脆弱性和可变性匹配指令的精确度：

| 自由度 | 适用场景 | 指令形式 |
|--------|----------|----------|
| **高自由度** | 多种有效路径、依赖上下文判断 | 文本指导 + 启发式规则 |
| **中自由度** | 有首选模式但可变通 | 伪代码 + 可配置参数 |
| **低自由度** | 操作脆弱、一致性关键 | 精确脚本 + 严格步骤 |

**类比**：想象 Claude 在探路
- **悬崖边的窄桥**：只有一条安全路径 → 提供具体护栏（低自由度）
- **开阔的平原**：多条路径可达目标 → 给出大致方向（高自由度）

### 3. 渐进式披露 (Progressive Disclosure)

**SKILL.md 是概览/导航，不是百科全书**。将详细内容分离到独立文件，按需加载。

**三层结构**：
```
启动时加载 → SKILL.md（触发时）
按需加载 → reference/*.md（需要时）
从不加载 → scripts/（执行，不读内容）
```

---

## YAML Frontmatter 最佳实践

### name 字段

- **最大 64 字符**
- **仅小写字母、数字、连字符**
- **推荐：动名词形式**（gerund form）
- **避免：** `helper`, `utils`, `tools`, `anthropic-*`, `claude-*`

**推荐命名**：
```yaml
name: processing-pdfs        # ✅ 清晰的活动描述
name: analyzing-spreadsheets  # ✅ 一目了然
name: pdf-helper             # ❌ 过于模糊
name: anthropic-pdf-tool     # ❌ 包含保留字
```

### description 字段

- **最大 1024 字符**
- **必须非空**
- **使用第三人称**
- **包含两个要素**：
  1. **做什么**（技能的核心能力）
  2. **何时用**（触发场景/关键词）

**有效示例**：
```yaml
# PDF Processing skill
description: Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

# Excel Analysis skill
description: Analyze Excel spreadsheets, create pivot tables, generate charts.
  Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.

# Git Commit Helper skill
description: Generate descriptive commit messages by analyzing git diffs.
  Use when the user asks for help writing commit messages or reviewing staged changes.
```

**避免的模糊描述**：
```yaml
description: Helps with documents     # ❌ 太模糊
description: Processes data          # ❌ 无触发场景
description: Does stuff with files   # ❌ 无实际信息
```

---

## SKILL.md 内容组织

### 1. 长度控制

- **SKILL.md 主体保持在 500 行以内**
- 接近限制时，考虑拆分到独立文件

### 2. 结构模式

#### 模式 A：概览 + 引用（推荐）

```markdown
---
name: pdf-processing
description: Extracts text and tables from PDF files...
---

# PDF Processing

## Quick start
Extract text with pdfplumber:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md) for complete guide
**API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
**Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

#### 模式 B：领域特定组织

适用于多领域技能，避免加载无关上下文：

```
bigquery-skill/
├── SKILL.md              # 概览和导航
└── reference/
    ├── finance.md        # 收入、账单指标
    ├── sales.md          # 机会、管道
    ├── product.md        # API 使用、功能
    └── marketing.md      # 活动、归因
```

**SKILL.md**：
```markdown
# BigQuery Data Analysis

## Available datasets
**Finance**: Revenue, ARR, billing → See [reference/finance.md](reference/finance.md)
**Sales**: Opportunities, pipeline → See [reference/sales.md](reference/sales.md)
**Product**: API usage, features → See [reference/product.md](reference/product.md)
```

#### 模式 C：条件性细节

```markdown
# DOCX Processing

## Creating documents
Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents
For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

### 3. 避免深层嵌套

**❌ 嵌套过深**（Claude 可能部分读取，导致信息不完整）：
```markdown
# SKILL.md
See [advanced.md](advanced.md)...

# advanced.md
See [details.md](details.md)...  # ← 嵌套第二层

# details.md
Here's the actual information...  # ← 嵌套第三层
```

**✅ 单层引用**（所有引用文件直接从 SKILL.md 链接）：
```markdown
# SKILL.md
**Basic usage**: [instructions in SKILL.md]
**Advanced features**: See [advanced.md](advanced.md)
**API reference**: See [reference.md](reference.md)
**Examples**: See [examples.md](examples.md)
```

### 4. 长文件添加目录

超过 100 行的参考文件，在顶部添加目录：

```markdown
# API Reference

## Contents
- Authentication and setup
- Core methods (create, read, update, delete)
- Advanced features (batch operations, webhooks)
- Error handling patterns
- Code examples

## Authentication and setup
...
```

### 5. 工作流与反馈循环

#### 复杂任务工作流

提供清晰的顺序步骤，对特别复杂的工作流提供清单：

```markdown
## Research synthesis workflow
Copy this checklist and track your progress:

```
Research Progress:
- [ ] Step 1: Read all source documents
- [ ] Step 2: Identify key themes
- [ ] Step 3: Cross-reference claims
- [ ] Step 4: Create structured summary
- [ ] Step 5: Verify citations
```

**Step 1: Read all source documents**
Review each document in the `sources/` directory...
[详细说明...]
```

#### 反馈循环模式

**验证器循环**：运行验证器 → 修复错误 → 重复

```markdown
## Document editing process
1. Make your edits to `word/document.xml`
2. **Validate immediately**: `python ooxml/scripts/validate.py unpacked_dir/`
3. If validation fails:
   - Review the error message carefully
   - Fix the issues in the XML
   - Run validation again
4. **Only proceed when validation passes**
5. Rebuild: `python ooxml/scripts/pack.py unpacked_dir/ output.docx`
```

### 6. 常见内容模式

#### 模板模式

**严格需求**（如 API 响应）：
```markdown
## Report structure
ALWAYS use this exact template structure:

```markdown
# [Analysis Title]

## Executive summary
[One-paragraph overview]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data
```
```

**灵活指导**：
```markdown
## Report structure
Here is a sensible default format, but use your best judgment:

```markdown
# [Analysis Title]

## Executive summary
[Adapt based on what you discover]

## Key findings
[Organize by discovered themes]
```
```

#### 示例模式

提供输入/输出对：

```markdown
## Commit message format
Generate commit messages following these examples:

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
```
fix(reports): correct date formatting in timezone conversion
```
```

---

## 目录结构设计

### 推荐结构

```
skill-name/
├── SKILL.md              # 主指令文件（触发时加载）
├── README.md             # 用户使用指南（AI 不读取）
├── config.yaml           # 可配置参数（AI 不读取）
├── FORMS.md              # 表单填写指南（按需加载）
├── REFERENCE.md          # API 参考（按需加载）
├── EXAMPLES.md           # 使用示例（按需加载）
└── scripts/
    ├── analyze_form.py   # 工具脚本（执行，不加载）
    ├── fill_form.py      # 功能脚本
    └── validate.py       # 验证脚本
```

### 配置与文档分离

**原则**：
- **config.yaml**：可配置的数值/路径/阈值
- **README.md**：用户使用说明、提示词示例
- **SKILL.md**：AI 执行所需的核心指令

**好处**：
1. 避免参数与指令矛盾
2. 用户可以修改 config.yaml 而无需懂 YAML frontmatter 语法
3. README.md 可以包含丰富的示例和截图，不消耗 AI 上下文

**示例 config.yaml**：
```yaml
# PDF Processing Configuration
extraction:
  default_method: "pdfplumber"
  ocr_fallback: true
  ocr_language: "eng"

validation:
  check_overlaps: true
  min_confidence: 0.8

output:
  format: "markdown"
  include_metadata: true
```

**在 SKILL.md 中引用**：
```markdown
## Configuration
Default extraction method and validation thresholds are defined in `config.yaml`.
To modify behavior, edit the relevant section in config.yaml before running.
```

---

## 脚本与代码规范

### 1. 解决问题，不要推诿 (Solve, Don't Punt)

**❌ 差：推诿给 Claude**
```python
def process_file(path):
    # Just fail and let Claude figure it out
    return open(path).read()
```

**✅ 好：显式处理错误**
```python
def process_file(path):
    """Process a file, creating it if it doesn't exist."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating default")
        with open(path, 'w') as f:
            f.write('')
        return ''
    except PermissionError:
        print(f"Cannot access {path}, using default")
        return ''
```

### 2. 避免"魔法数字"

**❌ 差：未解释的常量**
```python
TIMEOUT = 47  # Why 47?
RETRIES = 5   # Why 5?
```

**✅ 好：自文档化**
```python
# HTTP requests typically complete within 30 seconds
# Longer timeout accounts for slow connections
REQUEST_TIMEOUT = 30

# Three retries balances reliability vs speed
# Most intermittent failures resolve by the second retry
MAX_RETRIES = 3
```

### 3. 提供工具脚本

**好处**：
- 比生成代码更可靠
- 节省 token（无需加载代码）
- 节省时间（无需代码生成）
- 确保一致性

**使用方式明确说明**：
```markdown
## Utility scripts

**analyze_form.py**: Extract all form fields from PDF
```bash
python scripts/analyze_form.py input.pdf > fields.json
```

Output format:
```json
{
  "field_name": {"type": "text", "x": 100, "y": 200}
}
```

**validate_boxes.py**: Check for overlapping bounding boxes
```bash
python scripts/validate_boxes.py fields.json
# Returns: "OK" or lists conflicts
```
```

### 4. 可验证的中间输出

**"计划-验证-执行"模式**：

对于复杂、开放式的任务，让 Claude 先创建结构化计划，然后用脚本验证，再执行。

**示例**：批量更新 50 个表单字段
1. 分析 → **创建计划文件** → **验证计划** → 执行 → 验证

**为什么有效**：
- 早期捕获错误
- 机器可验证
- 可逆规划
- 清晰的调试信息

### 5. 路径规范

**始终使用正斜杠**，即使在 Windows 上：
```
✅ Good: scripts/helper.py, reference/guide.md
❌ Bad: scripts\helper.py, reference\guide.md
```

Unix 风格路径跨平台兼容，Windows 风格路径在 Unix 系统上会出错。

### 6. MCP 工具引用

使用完全限定名称：`ServerName:tool_name`

```markdown
Use the BigQuery:bigquery_schema tool to retrieve table schemas.
Use the GitHub:create_issue tool to create issues.
```

---

## 测试与迭代

### 1. 评估驱动开发

**在编写大量文档之前创建评估**：

1. **识别差距**：在没有 Skill 的情况下运行 Claude，记录具体失败
2. **创建评估**：构建测试这些差距的三个场景
3. **建立基线**：测量没有 Skill 时的性能
4. **编写最小指令**：创建足以解决差距并通过评估的内容
5. **迭代**：执行评估，与基线比较，改进

**评估结构示例**：
```json
{
  "skills": ["pdf-processing"],
  "query": "Extract all text from this PDF file and save it to output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "Successfully reads the PDF file using an appropriate PDF processing library",
    "Extracts text content from all pages without missing any pages",
    "Saves the extracted text to a file named output.txt"
  ]
}
```

### 2. 与 Claude 协作迭代

**最有效的 Skill 开发过程**：

1. **无 Skill 完成任务**：与 Claude A 一起工作，注意你反复提供的信息
2. **识别可重用模式**：找出对未来任务有用的上下文
3. **让 Claude A 创建 Skill**："创建一个捕获我们刚使用的 BigQuery 分析模式的 Skill"
4. **审查简洁性**：检查 Claude A 是否添加了不必要的解释
5. **改进信息架构**：让 Claude A 更有效地组织内容
6. **用 Claude B 测试**：在新实例上测试相关用例
7. **基于观察迭代**：如果 Claude B 遇到困难，返回 Claude A 进行改进

### 3. 多模型测试

Skill 对不同模型的效果不同：

- **Claude Haiku**（快速、经济）：Skill 是否提供足够指导？
- **Claude Sonnet**（平衡）：Skill 是否清晰高效？
- **Claude Opus**（强大推理）：Skill 是否过度解释？

---

## 常见反模式

### 1. 启动时加载所有内容

**问题**： defeats the purpose of lazy loading

**修复**：启动时只加载 metadata，按需激活 Skills

### 2. 模糊的 Skill 描述

**问题**：LLM 使用描述来决定激活哪个 Skill

**❌ 差**："Helps with code"

**✅ 好**："Reviews Python/JavaScript code for security vulnerabilities, PEP 8 compliance, and performance issues"

### 3. 提供太多选项

**❌ 差**（令人困惑）：
```markdown
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image, or...
```

**✅ 好**（提供默认 + 逃生舱）：
```markdown
Use pdfplumber for text extraction:
```python
import pdfplumber
```

For scanned PDFs requiring OCR, use pdf2image with pytesseract instead.
```

### 4. 假设工具已安装

**❌ 差**：
```markdown
Use the pdf library to process the file.
```

**✅ 好**：
```markdown
Install required package: `pip install pypdf`

Then use it:
```python
from pypdf import PdfReader
```
```

### 5. 时间敏感信息

**❌ 差**（会变得错误）：
```markdown
If you're doing this before August 2025, use the old API.
After August 2025, use the new API.
```

**✅ 好**（使用"旧模式"部分）：
```markdown
## Current method
Use the v2 API endpoint: `api.example.com/v2/messages`

## Old patterns
<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>

The v1 API used: `api.example.com/v1/messages`

This endpoint is no longer supported.
</details>
```

---

## 平台特定注意事项

### Claude Code

- **语义发现机制**：通过语义匹配触发 Skills
- **description 特殊地位**：是技能的"语义入口"
- **表头-正文一致性**：更新工作逻辑时必须同步更新 `description`

### 通用 Agent Skills 标准

遵循 [agentskills.io](https://agentskills.io) 规范：
- SKILL.md 命名约定
- YAML frontmatter 模式
- 目录结构
- 最佳实践

**好处**：Skills 跨项目、跨团队、跨平台可移植

---

## 检查清单

在分享 Skill 之前，验证：

### 核心质量
- [ ] Description 具体，包含关键术语
- [ ] Description 包含"做什么"和"何时用"
- [ ] SKILL.md 主体在 500 行以内
- [ ] 额外细节在独立文件中（如需要）
- [ ] 无时间敏感信息（或在"旧模式"部分）
- [ ] 全文术语一致
- [ ] 示例具体，不抽象
- [ ] 文件引用仅一层深
- [ ] 适当使用渐进式披露
- [ ] 工作流步骤清晰

### 代码和脚本
- [ ] 脚本解决问题，不推诿给 Claude
- [ ] 错误处理显式且有帮助
- [ ] 无"魔法数字"（所有值都有解释）
- [ ] 列出所需包并验证可用性
- [ ] 脚本有清晰文档
- [ ] 无 Windows 风格路径（全部正斜杠）
- [ ] 关键操作有验证/验证步骤
- [ ] 质量关键任务包含反馈循环

### 测试
- [ ] 至少创建三个评估
- [ ] 在 Haiku、Sonnet 和 Opus 上测试
- [ ] 用真实使用场景测试
- [ ] 团队反馈（如适用）

---

## 参考资源

### 官方文档
- [Agent Skills Specification](https://agentskills.io)
- [Claude Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Agent Skills GitHub](https://github.com/agentskills/agentskills)

### 社区资源
- [Building Agent Skills from Scratch - DEV.to](https://dev.to/onlyoneaman/building-agent-skills-from-scratch-lbl)
- [Skills Development Guide - MCP Market](https://mcpmarket.com/tools/skills/skills-development-guide)
- [VoltAgent/awesome-claude-skills](https://github.com/VoltAgent/awesome-claude-skills)

---

**文档版本**：2025-12-30
**维护者**：基于 Claude 官方文档和社区实践整理
