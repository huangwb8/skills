# Write Skill README — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `write-skill-readme` skill。
执行指令与硬性规范在 `SKILL.md`。

---

## 快速开始

- 最推荐用法（生成标准风格 README）

```
用 write-skill-readme 为 skills/your-skill 生成 README.md
```

- 为已有技能更新 README（保留手动修改的内容）

```
用 write-skill-readme 更新 skills/your-skill/README.md，保留我手动添加的内容
```

- 基于特定风格模板生成

```
用 write-skill-readme 为 skills/your-skill 生成 README.md，使用"功能型技能"模板
```

---

## 设计理念

`write-skill-readme` 遵循以下核心原则：

1. **Prompt 优先**：始终将"经典 Prompt + 场景化变异 Prompt"放在最前面
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
| **Prompt 优化** | 生成符合"经典 Prompt 优先 + 场景化变异"结构的 Prompt 示例 |
| **小白友好设计** | 自动生成表格化决策指南、丰富别名、对话式呈现 |
| **风格规范检查** | 确保生成的 README 符合项目的风格规范 |
| **增量更新** | 支持更新已有 README，保留手动添加的内容 |

---

## 提示词示例

### 示例 1：为新建技能生成 README（最简单）

```
用 write-skill-readme 为 skills/my-new-skill 生成 README.md
```

**技能行为**：
1. 分析 `skills/my-new-skill/` 目录结构
2. 读取 SKILL.yaml、SKILL.md、config.yaml、scripts/ 等文件
3. 根据技能特性选择合适的模板
4. 生成包含"快速开始 + 设计理念 + 使用示例 + FAQ"的 README.md

---

### 示例 2：指定模板类型

```
用 write-skill-readme 为 skills/data-processor 生成 README.md，使用"工具型技能"模板
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
用 write-skill-readme 更新 skills/existing-skill/README.md，保留我手动添加的内容
```

**技能行为**：
1. 对比已有 README.md 和当前技能状态
2. 更新过时的内容（如新增参数、变更的工作流）
3. 保留手动添加的章节和内容
4. 标注需要手动检查的部分

---

### 示例 4：为技能系列批量生成 README

```
用 write-skill-readme 为 skills/nsfc-* 系列技能批量生成 README.md
```

**技能行为**：
1. 匹配所有 `skills/nsfc-*` 目录
2. 为每个技能生成独立的 README.md
3. 确保系列技能的 README 风格一致

---

### 示例 5：生成 README 并进行风格检查

```
用 write-skill-readme 为 skills/complex-skill 生成 README.md，并运行完整风格检查
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

## 快速开始
（经典 Prompt + 场景化变异 Prompt）

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
用 write-skill-readme 为 skills/your-skill 重新生成 README.md（覆盖已有内容）
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
5. **生成场景化 Prompt** — 基于以上分析，生成 2-4 个不同场景的 Prompt 示例

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
- [ ] **变异 Prompt 是否覆盖了主要使用场景？**
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
