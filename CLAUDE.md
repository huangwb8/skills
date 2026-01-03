# Skills 开发流水线 - Claude Code 项目指令

你正在 `pipelines/skills/` 中工作：该目录用于开发与维护一组"可复用 Agent Skills"。Codex 和 Claude Code 已统一遵循 **Agent Skills 开放标准**（[agentskills.io](https://agentskills.io)）。本项目现采用**单一技能库**架构，技能同时兼容 Codex、Claude Code 及其他支持 Agent Skills 的平台。

本文件保留用于 Claude Code 特定的配置说明。通用项目指令（包括**有机整体更新哲学**和**工程原则基础**）请参阅 [AGENTS.md](AGENTS.md)。

> **工程原则快速参考**：有机整体更新建立在奥卡姆剃刀、KISS、YAGNI、DRY、SOLID、关注点分离、最小惊讶原则、早期返回原则等已被广泛验证的工程原则之上。详见 [AGENTS.md](AGENTS.md) 中的"工程原则基础"章节。

## Claude Code 环境下的有机更新实践

在 Claude Code 中应用有机更新原则时，需注意以下平台特定要点：

### 1. 语义发现机制（Semantic Discovery）

Claude Code 使用**语义匹配**触发技能，这意味着：

**YAML `description` 的特殊地位**：
- 它是技能的"语义入口"——决定了技能何时被触发
- 更新 `description` 时，必须考虑其对发现机制的影响：
  - 是否会让技能更容易被正确触发？
  - 是否会导致误触发（与其他技能语义重叠）？
  - 是否保留了原有触发场景的覆盖？

**有机更新实践**：
```yaml
# ❌ 补丁式：简单追加新触发词
description: 用于文献综述。2025-12-29 新增：也用于 related work。

# ✅ 有机式：重新组织语义结构
description: 当用户要写文献综述/系统综述（SLR/PRISMA）/related work/相关工作/调研并梳理某领域文献时使用：
  生成可复现检索方案、纳排标准、质量评价与数据抽取表，并输出带规范引用的综述初稿。
```

### 1.1 表头-正文一致性在 Claude Code 中的特殊重要性

在 Claude Code 中，**YAML frontmatter 是技能的唯一"语义接口"**，因此表头与正文的一致性要求比其他平台更为严格。

**核心原则**：
- 工作逻辑更新 → 必须同步更新 `description`
- 新增使用场景 → 必须同步更新 `metadata.keywords`
- 技能定位变化 → 必须同步更新 `name` 和 `metadata.short-description`

**具体要求**：

| 场景 | 表头更新项 | Claude Code 特殊考虑 |
|------|-----------|---------------------|
| 工作流步骤变化 | `description` | 确保触发场景的描述仍然准确 |
| 输入参数变化 | `description` | 确保用户理解的输入范围与实际一致 |
| 输出格式变化 | `description` | 确保承诺的输出与实际生成一致 |
| 新增触发场景 | `metadata.keywords` | 确保新场景能被语义匹配发现 |
| 技能范围扩展 | `name` + `metadata.short-description` | 避免名称与实际能力脱节 |

**更新后必做检查**：
```bash
# 在 Claude Code 中验证触发准确性
# 1. 新建会话（重新加载技能）
# 2. 用多种变体的用户输入测试触发
# 3. 确认触发后的行为与表头描述一致
```

> 详见 [AGENTS.md](AGENTS.md) 中的"表头-正文一致性原则（Frontmatter-Body Alignment）"。

### 2. Progressive Disclosure 在 Claude Code 中的体现

Claude Code 的加载机制天然支持三层渐进披露：

| 层级 | 加载时机 | 有机更新要点 |
|------|----------|--------------|
| **YAML frontmatter** | 会话启动时 | 确保 `name` 和 `description` 准确反映技能的核心价值，避免过度详细 |
| **SKILL.md 正文** | 技能触发时 | 保持简洁，只包含 AI 执行所需的核心信息 |
| **references/** | 按需加载 | 将详细策略、标准、参考文档独立存放，在正文中引用 |

**有机更新要求**：
- 更新任何一层时，考虑其对其他层的影响
- 例如：更新 references 中的详细策略后，检查 SKILL.md 中的引用是否仍然准确
- 例如：精简 SKILL.md 正文时，确保核心信息没有丢失（可以移至 references）

### 3. Claude Code 特定的更新场景

#### 场景 A：用户反馈"技能未被触发"

**补丁式（❌）**：在 `description` 中堆砌关键词
```yaml
description: 用于写综述、写review、写系统综述、写SLR、写PRISMA、写related work...
```

**有机式（✅）**：
1. 分析用户输入与当前 `description` 的语义距离
2. 识别缺失的语义维度（如：是否缺少"相关工作"这一学术场景的表达？）
3. 重写 `description`，用自然的语义表达覆盖场景（而非关键词堆砌）
4. 更新 `metadata.keywords` 以包含新的触发场景
5. 验证是否会与现有其他技能产生语义冲突

> 这体现了"表头-正文一致性"原则：当需要扩展触发场景时，不仅更新 `description`，也同步更新 `keywords`。

#### 场景 B：用户反馈"技能触发了但行为不对"

**补丁式（❌）**：在 SKILL.md 末尾追加"注意：当用户说 X 时，应该做 Y"

**有机式（✅）**：
1. 理解用户期望与当前行为的差异
2. 定位该行为在工作流中的生态位（是触发条件理解错误？还是工作流步骤设计问题？）
3. 更新相关章节（可能是"触发条件"章节，也可能是具体工作流步骤）
4. 同步更新示例和验证标准
5. **检查表头一致性**：如果工作逻辑发生了本质变化，同步更新 `description`

> 例如：如果从"仅输出 Markdown"变为"输出 Markdown + PDF + Word"，则 `description` 必须更新以反映新的输出能力。

#### 场景 C：技能文档变得过长

**补丁式（❌）**：继续追加，导致文档臃肿、上下文浪费

**有机式（✅）**：
1. 识别哪些内容是"核心执行必需"，哪些是"参考/背景信息"
2. 将参考内容移至 `references/`，在 SKILL.md 中保留引用
3. 重新组织 SKILL.md，确保其保持简洁但完整

#### 场景 D：创建/优化 README.md 和 config.yaml

**补丁式（❌）**：在 SKILL.md 中混入用户指导和参数配置

**有机式（✅）**：
1. **分离用户指南**：将"如何使用"的内容（提示词示例、触发场景）移至 `README.md`
2. **分离参数配置**：将可配置的数值/路径/阈值移至 `config.yaml`
3. **在 SKILL.md 中引用**：用引用方式而非硬编码值（如 `见 config.yaml 的 evidence 配置`）
4. **保持一致性**：确保 SKILL.md、README.md、config.yaml 三者之间的交叉引用准确

**Claude Code 特定考虑**：
- `README.md` 不被 Claude Code 加载到上下文，它是给用户看的独立文档
- `config.yaml` 也不被自动加载，如需在技能执行时读取，应在 `scripts/` 中实现加载逻辑
- SKILL.md 应保持简洁，不重复 README.md 和 config.yaml 的内容，而是引用它们

> 详见 [AGENTS.md](AGENTS.md) 中的"推荐文件（增强可维护性与可用性）"章节。

### 4. Claude Code 特定的验证要点

在验证有机更新效果时，额外检查：

#### 内容质量检查
- [ ] **上下文效率**：SKILL.md 是否保持了简洁？（Claude Code 对上下文长度敏感，建议 500 行以内）
- [ ] **引用可追踪性**：正文中对 `references/` 的引用是否清晰准确？
- [ ] **避免深层嵌套**：所有引用文件是否直接从 SKILL.md 链接（单层引用）？
- [ ] **长文件目录**：超过 100 行的参考文件是否在顶部添加了目录？

#### 表头一致性检查
- [ ] **表头-正文一致性**：YAML frontmatter 是否准确反映了当前的工作逻辑？
- [ ] `description` 与实际能力是否一致？
- [ ] `keywords` 是否覆盖了主要触发场景？
- [ ] `name` 是否采用动名词形式（gerund form）且符合命名规范？

#### YAML Frontmatter 最佳实践

**`name` 字段规范**：
- 最大 64 字符
- 仅小写字母、数字、连字符
- 推荐：动名词形式（如 `processing-pdfs`, `analyzing-spreadsheets`）
- 避免：`helper`, `utils`, `tools`, `anthropic-*`, `claude-*`

**`description` 字段规范**：
- 最大 1024 字符
- 必须非空
- 使用第三人称
- 包含两个要素：
  1. **做什么**（技能的核心能力）
  2. **何时用**（触发场景/关键词）

**有效示例**：
```yaml
# ✅ 好：具体且包含触发场景
description: Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

# ❌ 差：太模糊，无触发场景
description: Helps with documents
```

#### 常见反模式检查

- [ ] **避免启动时加载所有内容**：是否遵循 lazy loading？
- [ ] **避免模糊的 Skill 描述**：`description` 是否具体且包含关键术语？
- [ ] **避免提供太多选项**：是否提供默认方案而非罗列多个选择？
- [ ] **避免假设工具已安装**：是否明确列出所需包及安装方式？
- [ ] **避免时间敏感信息**：是否使用"旧模式"部分处理过时内容？

#### 脚本与代码检查
- [ ] **解决而非推诿**：脚本是否显式处理错误而非让 Claude 猜测？
- [ ] **避免魔法数字**：所有常量是否有注释解释其取值依据？
- [ ] **路径规范**：是否始终使用正斜杠（跨平台兼容）？
- [ ] **MCP 工具引用**：是否使用完全限定名称（`ServerName:tool_name`）？

---

> **静态自检 vs 动态测试**：以上检查均为静态分析。语义触发测试和完整流程验证由用户根据需要手动执行，详见 [AGENTS.md](AGENTS.md) 中的"静态自检 vs 动态测试"原则。

## Claude Code 特定配置

### 技能加载路径

Claude Code 从以下路径加载技能（按优先级）：

1. **项目级技能**：`{项目根目录}/.claude/skills/`
2. **用户级技能**：`~/.claude/skills/`

### 推荐安装方式（系统级复制安装）

软链接在某些环境下可发现性不稳定；推荐使用本仓库提供的 `install-bensz-skills` 做系统级复制安装，从而在任意项目都可被发现。

```bash
python3 install-bensz-skills/scripts/install.py
```

### 验证技能可用性

在 Claude Code 中测试技能是否正常工作：

1. **新建会话**：技能在会话启动时加载
2. **使用触发短语**：用与 `description` 匹配的表述测试
3. **检查行为**：确认技能按预期执行

## 与 Codex 的兼容性

由于两者遵循同一标准，同一技能文件在 Codex 和 Claude Code 中的行为应一致。如发现平台特定差异，请：

1. 在 SKILL.md 中添加平台特定说明
2. 使用条件逻辑处理差异
3. 在 [AGENTS.md](AGENTS.md) 中记录已知差异
