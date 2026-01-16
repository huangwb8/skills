# A 轮优化计划模板

**计划版本**: v{{TIMESTAMP}}
**制定时间**: {{PLAN_DATE}}
**当前版本**: {{CURRENT_VERSION}}
**目标技能**: {{TARGET_SKILL_NAME}}
**目标技能路径**: {{TARGET_SKILL_ROOT}}

---

## 第一部分：独立评估与审查范围（必填）

### 独立评估原则（强制）

- [ ] 本轮 A 轮评估基于目标 skill 的**当前工作状态**独立完成
- [ ] **未查看** `plans/` 与 `tests/`（避免确认偏差/路径依赖）
- [ ] 不以历史问题清单为先验，仅以“当前工作文件”的证据为准

**当前轮次**: A 轮 #{{ROUND_NUMBER}} / 共 {{TOTAL_ROUNDS}} 轮

### 审查范围（强制）

**必须审查文件**（参考 `config.yaml:a_round_check.independent_review.required_files`）：
- `SKILL.md`
- `config.yaml`

**必须审查目录**（参考 `config.yaml:a_round_check.independent_review.required_dirs`）：
- `scripts/`
- `references/`
- `templates/`
- `assets/`（如不存在无需补）

**排除范围**：
- `plans/`、`tests/`、`README.md`、`CHANGELOG.md` 以及 `exclude_patterns` 命中的文件（测试产物、用户文档和变更记录不属于工作代码）

**审查方法（建议）**：使用 Glob/Read/Grep（如 `rg`/`find`）对上述范围做全量扫描，确保不遗漏。

### 本轮的批判性思维聚焦维度

⚠️ **必须选择至少一个聚焦维度**（从以下选择）：

- [ ] **系统架构**：工作流/配置/文件结构的设计合理性
- [ ] **过度设计**：不必要的抽象/配置/灵活性
- [ ] **一致性**：跨文件/跨文档的矛盾
- [ ] **安全性**：路径遍历/命令注入/信息泄露
- [ ] **边缘情况**：极端输入/恶意输入/隐式假设
- [ ] **用户体验**：可理解性/可预测性/错误恢复

**聚焦维度**: {{FOCUS_DIMENSION}}

### 本轮解决的核心问题（一句话）

{{ONE_LINE_SUMMARY}}

---

## 第二部分：批判性思维分析（必填）

⚠️ **必须使用「刁钻角度」思考**（从 references/CRITICAL_THINKING_GUIDE.md 选择）：

### 选择的刁钻角度

- [ ] **边缘情况**: {{EXTREME_INPUT}} → {{EXTREME_ACTUAL}} → 应该是 {{EXTREME_EXPECTATION}}
- [ ] **恶意输入**: {{MALICIOUS_SCENARIO}} → 攻击向量 {{ATTACK_VECTOR}} → 当前防御 {{CURRENT_DEFENSE}}
- [ ] **隐式假设**: {{IMPLICIT_ASSUMPTION}} → 失效场景 {{ASSUMPTION_FAILURE_SCENARIO}}
- [ ] **自我质疑**: {{QUESTIONED_DESIGN}} → 质疑理由 {{REASON_FOR_QUESTIONING}}
- [ ] **跨文件矛盾**: 文件 A ({{FILE_A_STATEMENT}}) vs 文件 B ({{FILE_B_STATEMENT}}) → 是否矛盾 {{IS_CONTRADICTORY}}

### 发现的系统性问题

⚠️ **必须列出至少 3 个系统性问题**（架构/过度设计/一致/安全）：

1. {{SYSTEMIC_ISSUE_1}}
2. {{SYSTEMIC_ISSUE_2}}
3. {{SYSTEMIC_ISSUE_3}}

---

## 第三部分：问题清单（P0-P2）

### 优先级定义

| 优先级 | 定义 | 示例 |
|--------|------|------|
| **P0** | 阻塞性问题：不修复就无法继续；或安全风险 | 路径遍历漏洞、核心功能缺失 |
| **P1** | 重要优化：显著提升质量/安全性/可维护性 | 过度设计、冗余、不一致 |
| **P2** | 锦上添花：改进体验、完善细节 | 注释优化、代码风格 |

**数量要求**：
- P0 + P1 + P2 总和 ≥ 10
- P0 + P1 占比 ≥ 60%
- 系统性问题 ≥ 3 个

---

### P0（阻塞/安全/核心）

#### 问题 1: {{P0_1_TITLE}}

**位置**: `{{FILE}}:{{LINE}}`

**问题类型**: [架构设计/安全性/核心功能缺失]

**现象**:
{{P0_1_PHENOMENON}}

**影响**:
{{P0_1_IMPACT}}

**修复建议**:
{{P0_1_FIX}}

**验证方法**:
{{P0_1_VERIFY}}

---

### P1（重要优化）

#### 问题 1: {{P1_1_TITLE}}

**位置**: `{{FILE}}:{{LINE}}`

**问题类型**: [过度设计/冗余/不一致/用户体验]

**现象**:
{{P1_1_PHENOMENON}}

**影响**:
{{P1_1_IMPACT}}

**修复建议**:
{{P1_1_FIX}}

**验证方法**:
{{P1_1_VERIFY}}

---

### P2（锦上添花）

#### 问题 1: {{P2_1_TITLE}}

**位置**: `{{FILE}}:{{LINE}}`

**现象**:
{{P2_1_PHENOMENON}}

**修复建议**:
{{P2_1_FIX}}

**验证方法**:
{{P2_1_VERIFY}}

---

## 第四部分：问题质量检查（必填）

⚠️ **提交前必须确认**：

- [ ] **数量达标**: P0+P1+P2 ≥ 10，P0+P1 占比 ≥ 60%
- [ ] **系统问题**: 至少 3 个系统性问题（架构/过度设计/一致/安全）
- [ ] **位置精确**: 每个问题都有精确的 `文件:行号`
- [ ] **现象具体**: 每个问题都描述了具体现象（不是"应该XX"）
- [ ] **影响明确**: 每个问题都说明了"为什么重要"
- [ ] **修复具体**: 每个问题都有具体的修复方案（不是"建议优化"）
- [ ] **验证明确**: 每个问题都有可执行的验证方法
- [ ] **独立评估**: 未查看 `plans/` 与 `tests/`，避免确认偏差/路径依赖
- [ ] **范围覆盖**: 已覆盖 required_files/required_dirs（并明确排除 tests/plans）

---

## 第五部分：执行计划（可选）

{{EXECUTION_PLAN}}

---

## 第六部分：完成后的下一轮预告

**预计下一轮聚焦**: {{NEXT_ROUND_FOCUS}}

**预计完成时间**: {{NEXT_ROUND_TIME}}

---

**模板说明**:

本模板用于 A 轮优化计划的生成。使用时：

1. **替换占位符**: 将 `{{VAR}}` 替换为实际内容
2. **删除不需要的章节**: 如某些章节不适用，可删除
3. **核心章节**: 第一部分（全局视图）+ 第二部分（批判性思维）+ 第三部分（问题清单）+ 第四部分（质量检查）必须完整

**关键原则**:

- **独立评估**: 每轮 A 轮基于当前工作状态独立审查，不看 `plans/` 与 `tests/`
- **批判性思维**: 必须使用"刁钻角度"思考
- **系统视角**: 必须发现至少 3 个系统性问题
- **问题质量**: 每个问题都必须有精确的位置、具体的修复方案、可执行的验证方法

**参考文档**:

- 批判性思维框架：`references/CRITICAL_THINKING_GUIDE.md`
- 问题挖掘技巧：`references/ISSUE_DISCOVERY_TECHNIQUES.md`
- 建设性建议标准：`references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md`
- 反例库：`references/ANTI_PATTERNS_LIBRARY.md`
