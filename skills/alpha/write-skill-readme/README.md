# Write Skill README

本 README 面向**使用者**：如何触发并正确使用 `write-skill-readme` skill。
执行指令与硬性规范在 `SKILL.md`。

---

## 用法

- 最推荐用法（生成标准风格 README）

```
请使用 write-skill-readme skill 为 skills/your-skill 生成 README.md
输入：skills/your-skill（技能目录）
输出：skills/your-skill/README.md
```

- 为已有技能更新 README（保留手动修改的内容）

```
请使用 write-skill-readme skill 更新 skills/your-skill/README.md
输入：skills/your-skill（技能目录）+ 已有 README.md
输出：更新后的 skills/your-skill/README.md（尽量保留你手动添加的内容）
```

- 基于特定风格模板生成

```
请使用 write-skill-readme skill 为 skills/your-skill 生成 README.md
输入：skills/your-skill（技能目录）
输出：skills/your-skill/README.md
另外，还有下列参数约束：
- 模板：功能型技能
```

---

## 设计理念

`write-skill-readme` 遵循以下核心原则：

1. **Prompt 优先**：快速开始默认给“常规 Prompt（skill+输入+输出）+ 进阶 Prompt（参数约束，可选）”，并按需补充少量场景化变体
2. **小白友好**：用表格、对话式呈现、渐进式复杂度降低学习曲线
3. **明确受众**：区分"使用者"和"维护者"，README 面向使用者
4. **硬编码后置**：脚本命令放在"备选用法"章节
5. **场景化组织**：按使用场景而非技术参数组织内容

> **核心价值**：让小白用户用最短的路径学会最核心的用法

---

## 功能概述

| 特性 | 说明 |
|------|------|
| **智能模板选择** | 根据技能特性自动选择合适的 README 模板（功能型/工具型/混合型） |
| **Prompt 优化** | 生成“常规 Prompt（skill+输入+输出）+ 进阶 Prompt（参数约束，可选）”，并按需补充少量场景化变体 |
| **小白友好设计** | 自动生成表格化决策指南、丰富别名、对话式呈现 |
| **风格规范检查** | 确保生成的 README 符合项目的风格规范 |
| **增量更新** | 支持更新已有 README，保留手动添加的内容 |

---

## 提示词示例

### 示例 1：为新建技能生成 README（最简单）

```
请使用 write-skill-readme skill 为 skills/my-new-skill 生成 README.md
输入：skills/my-new-skill（技能目录）
输出：skills/my-new-skill/README.md
```

**技能行为**：
1. 分析 `skills/my-new-skill/` 目录结构
2. 读取 SKILL.yaml、SKILL.md、config.yaml、scripts/ 等文件
3. 根据技能特性选择合适的模板
4. 生成包含"快速开始 + 设计理念 + 使用示例 + FAQ"的 README.md

---

### 示例 2：指定模板类型

```
请使用 write-skill-readme skill 为 skills/data-processor 生成 README.md
输入：skills/data-processor（技能目录）
输出：skills/data-processor/README.md
另外，还有下列参数约束：
- 模板：工具型技能
```

**技能行为**：
1. 使用"工具型技能"模板（命令优先而非 Prompt 优先）
2. 生成以脚本调用为核心的 README 结构

**可用模板**：
- **功能型技能**（默认）：主要用 Prompt 触发，有明确工作流
- **工具型技能**：主要用脚本/命令行调用
- **混合型技能**：Prompt 优先 + 脚本备选

---

### 示例 3：更新已有 README

```
请使用 write-skill-readme skill 更新 skills/existing-skill/README.md
输入：skills/existing-skill（技能目录）+ 已有 README.md
输出：更新后的 skills/existing-skill/README.md（尽量保留你手动添加的内容）
```

**技能行为**：
1. 对比已有 README.md 和当前技能状态
2. 更新过时的内容（如新增参数、变更的工作流）
3. 保留手动添加的章节和内容
4. 标注需要手动检查的部分

---

### 示例 4：为技能系列批量生成 README

```
请使用 write-skill-readme skill 为 skills/nsfc-* 系列技能批量生成 README.md
输入：skills/nsfc-*（匹配到的技能目录集合）
输出：每个目录下的 README.md
```

**技能行为**：
1. 匹配所有 `skills/nsfc-*` 目录
2. 为每个技能生成独立的 README.md
3. 确保系列技能的 README 风格一致

---

### 示例 5：生成 README 并进行风格检查

```
请使用 write-skill-readme skill 为 skills/complex-skill 生成 README.md
输入：skills/complex-skill（技能目录）
输出：skills/complex-skill/README.md
另外，还有下列参数约束：
- 风格检查：运行完整清单，并报告需要手动调整的项目
```

**技能行为**：
1. 生成 README.md
2. 运行 [风格规范清单](references/style-guidelines.md#静态检查清单) 中的所有检查
3. 报告需要手动调整的项目

---

## 三种模板对照表

| 模板类型 | 适用技能 | Prompt 位置 | 硬编码位置 | 典型技能 |
|---------|---------|-----------|-----------|---------|
| **功能型** | 主要用 Prompt 触发 | 快速开始（最前） | 无或很少 | systematic-literature-review<br>get-review-theme |
| **工具型** | 主要用脚本调用 | 无或很少 | 快速开始 | install-bensz-skills<br>init-project |
| **混合型** | Prompt + 脚本 | 快速开始（推荐） | 备选用法（最后） | make-latex-model<br>nsfc-*-writer |

**如何选择模板**：

| 你的技能特征 | 推荐模板 |
|-------------|---------|
| 用户主要用 Prompt 触发，有明确工作流程 | **功能型** |
| 用户主要运行脚本/命令，功能相对简单 | **工具型** |
| 支持 Prompt 和脚本两种方式，推荐 Prompt | **混合型** |

---

## 输出文件

- `README.md` — 技能的用户使用指南

**典型章节结构**（功能型模板）：

```markdown
# 技能名称 — 用户使用指南

本 README 面向**使用者**...

## 用法
（常规 Prompt + 进阶 Prompt；按需补充场景化变体）

## 设计理念
（核心价值、工作原理）

## 提示词示例
（按场景分类的 Prompt）

## 配置选项
（参数说明）

## 常见问题
（FAQ）
```

---

## 更多文档

- `SKILL.md` — 技能执行指令与硬性规范
- [README 结构模板](references/README-templates.md) — 三种典型模板的详细结构
- [风格规范清单](references/style-guidelines.md) — 完整的风格规范和检查清单
- [Prompt 编写指南](references/prompt-writing-guide.md) — 如何编写经典 Prompt 和变异 Prompt

---

## 常见问题

### Q：技能会覆盖我手动修改的 README.md 吗？

A：默认情况下，如果 README.md 已存在，技能会：
1. 先读取已有内容
2. 识别手动添加的章节
3. 更新过时内容
4. 保留手动添加的内容

如果你希望完全重新生成，使用：

```
请使用 write-skill-readme skill 为 skills/your-skill 重新生成 README.md
输入：skills/your-skill（技能目录）
输出：覆盖写入 skills/your-skill/README.md
```

---

### Q：如何确定应该用哪种模板？

A：技能会根据以下特征自动选择：

- **有独立的 `scripts/` 目录** → 倾向于"工具型"或"混合型"
- **YAML description 包含"用自然语言"等关键词** → 倾向于"功能型"或"混合型"
- **config.yaml 包含大量可配置参数** → 倾向于"功能型"

你也可以在 Prompt 中明确指定模板（见[示例 2](#示例-2指定模板类型)）。

---

### Q：生成的 Prompt 示例是固定的吗？

A：不是。技能会：

1. **分析 SKILL.yaml 的 description** — 理解技能的核心功能和触发场景
2. **分析 SKILL.md 的工作流** — 提取关键步骤和参数
3. **分析 config.yaml** — 识别可配置参数及其默认值
4. **分析 scripts/** — 如有脚本，生成对应的硬编码用法示例
5. **生成 Prompt** — 默认生成“常规 Prompt + 进阶 Prompt（带参数约束）”，并按需补充 0-2 个不同场景的变体

---

### Q：如何让生成的 README 更符合我的技能特点？

A：确保以下文件质量高：

1. **SKILL.yaml** — 特别是 `description` 和 `metadata.keywords`
2. **SKILL.md** — 特别是"触发条件"和"工作流"章节
3. **config.yaml** — 添加有意义的参数注释
4. **scripts/** — 如有脚本，确保有清晰的步骤说明

技能会基于这些文件生成 README，源文件质量越高，生成的 README 越准确。

---

### Q：生成后需要手动调整什么？

A：技能会标注以下需要手动检查的内容：

- [ ] **经典 Prompt 是否覆盖了最常用的场景？**
- [ ] **进阶 Prompt 是否用“参数约束”清晰表达可选控制项？**
- [ ] **场景化变体（如有）是否覆盖主要使用场景？**
- [ ] **FAQ 是否预测了小白用户的常见疑问？**
- [ ] **表格化决策指南是否准确？**
- [ ] **别名是否丰富且准确？**

建议生成后至少检查一次"快速开始"章节的 Prompt 示例。

---

### Q：可以为多个技能批量生成 README 吗？

A：可以。使用：

```
用 write-skill-readme 为 skills/nsfc-* 系列技能批量生成 README.md
```

技能会：
1. 匹配所有符合条件的技能目录
2. 为每个技能生成独立的 README.md
3. 确保系列技能的 README 风格一致
4. 报告生成的 README 列表

---

### Q：生成后发现内容不对怎么办？

A：可能的原因和解决方案：

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| Prompt 示例不准确 | SKILL.yaml 的 description 不够详细 | 更新 description 后重新生成 |
| 缺少关键章节 | SKILL.md 中缺少对应内容 | 补充 SKILL.md 后重新生成 |
| 模板选择错误 | 技能特征不明显 | 在 Prompt 中明确指定模板 |
| 硬编码用法缺失 | scripts/ 目录未被识别 | 检查 scripts/ 是否有可执行文件 |

你也可以在生成后手动编辑 README.md，技能不会覆盖手动添加的内容（除非使用"重新生成"）。

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic（1/6 = 17%）
- **来源构成**：社区 70%, 官方 20%, 技术博客 10%
- **数据时效**：2024-10 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试 README 生成质量

---

### 场景化建议

#### 场景 1：标准 README 生成（最常见）

**触发条件**：需要为技能生成用户使用指南 README.md

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium |
| **预期成本** | ~$0.02-0.10/次 |

**理由**：
- README 生成需要分析技能结构（SKILL.md、config.yaml、scripts/）并生成用户友好的文档
- Sonnet 在文档生成任务中表现出色，能够理解技能的核心价值并以小白友好的方式呈现
- [社区对比](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249) 显示 Sonnet 在文档生成场景下的优势
- **文档生成需要理解和组织能力，Sonnet 的性价比最高**

**避免**：简单技能的 README 生成不需要 Opus，用 Sonnet 即可

**来源**：社区对比讨论 + 官方模型选择指南

---

#### 场景 2：复杂技能文档生成

**触发条件**：
- 需要为复杂技能（多工作流、多参数、多模板）生成 README
- 需要深度理解技能的设计理念并准确传达
- 需要生成大量场景化 Prompt 示例

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium-high |
| **预期成本** | ~$0.05-0.20/次 |

**理由**：
- Sonnet 在复杂文档生成任务中表现优异，能够理解技能的复杂性并生成结构清晰的文档
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/) 显示 Sonnet 在文档生成任务中与 Opus 质量相当
- **复杂技能文档生成需要较强的理解和组织能力，Sonnet 足够胜任**

**避免**：极少需要 Opus，除非技能极其复杂且有大量交叉引用

**来源**：Reddit 社区讨论 + 90 天对比测试

---

#### 场景 3：批量 README 生成

**触发条件**：
- 需要为多个技能批量生成 README
- 成本敏感，需要高性价比

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium |
| **预期成本** | ~$0.10-0.50/批 |

**理由**：
- Sonnet 在文档生成任务中表现出色，适合批量处理
- [社区验证](https://chatlyai.app/blog/claude-haiku-4-5-use-cases) 显示 Sonnet 能"handle medium-complexity tasks with good balance"
- **批量生成需要平衡质量和成本，Sonnet 是最佳选择**

**避免**：批量生成不要只用 Haiku，可能无法理解复杂的技能结构

**来源**：社区反馈 + 官方文档

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Sonnet 4.5** | 所有 README 生成场景（95%） | 极端复杂的文档系统 | $$$$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Haiku 4.5** | 简单技能 README | 复杂技能文档（理解不足） | $$ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Opus 4.5** | **不推荐** | 所有场景（浪费） | $$$$$ | ⭐⭐ | ⭐ |

**说明**：
- Sonnet 覆盖 95% 的 README 生成场景
- Haiku 仅用于简单技能的 README 生成（单一功能、无复杂工作流）
- Opus 对此任务**完全不必要**，成本过高且无性能提升

---

### 通用原则

1. **默认从 Sonnet 开始**：95% 的 README 生成任务 Sonnet 足够，无需 Opus
2. **复杂度判断**：根据技能的复杂程度选择模型
   - 简单技能（单一功能）：Sonnet 或 Haiku
   - 标准技能（多工作流、多参数）：Sonnet
   - 复杂技能（多模板、大量交叉引用）：Sonnet（极少需要 Opus）
3. **质量优先**：README 是技能的"门面"，不应只追求低成本而牺牲文档质量
4. **文档生成需要推理**：分析技能结构 + 理解设计理念 + 生成用户友好文档，需要较强的理解和组织能力
5. **Haiku 的局限性**：虽然 Haiku 速度快、成本低，但 [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1o856eb/tested_haiku_45_it-is-fast-but-cant-complete/) 显示它在完成复杂文档生成任务时可能遇到困难

---

### ⚠️ 争议点

#### Sonnet vs Haiku：README 生成可以用 Haiku 吗？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Sonnet 更保险** | 社区多数意见 | README 生成需要理解技能结构和设计理念，Haiku 可能无法胜任 |
| **Haiku 足够** | 部分开发者 | 简单技能的 README 生成是简单任务，Haiku 完全胜任 |

**数据支持**：
- [某用户测试](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)：Haiku 在编码任务中匹配 Sonnet 能力，成本降低 80%
- [官方文档](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)：Haiku 专为"高吞吐量、低延迟"场景设计

**建议**：
- **默认使用 Sonnet**：README 生成需要理解和组织能力，Sonnet 完全胜任
- **仅在以下情况使用 Haiku**：
  - 生成非常简单技能的 README（单一功能、无复杂工作流）
  - 批量生成简单技能的 README（成本敏感）
  - Sonnet 出现理解错误时（极少见）

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
- [Claude Opus 4.5 is insane (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/)

**技术博客**：
- [Top Use Cases for Claude Haiku 4.5](https://chatlyai.app/blog/claude-haiku-4-5-use-cases)
- [Claude Haiku 4.5 matches Sonnet's coding skills at 80% less cost](https://medium.com/@cognidownunder/claude-haiku-4-5-matches-sonnets-coding-skills-at-80-less-cost-changes-everything-297f4b163d4e)
