# 优化计划（{{TEST_ID}}）

**计划日期**: {{PLAN_DATE}}  
**计划ID**: {{TEST_ID}}  
**目标技能**: {{TARGET_SKILL_NAME}}  
**目标技能路径**: {{TARGET_SKILL_ROOT}}

---

## 独立评估与审查范围（强制）

- [ ] 本轮基于目标 skill 的**当前工作状态**独立评估
- [ ] **未查看**历史轮次的 `plans/` 与 `tests/`（计划阶段不依赖历史产物，避免确认偏差/路径依赖）

**必须审查文件**（参考 `config.yaml:a_round_check.independent_review.required_files`）：
- `SKILL.md` / `config.yaml`

**必须审查目录**（参考 `config.yaml:a_round_check.independent_review.required_dirs`）：
- `scripts/` / `references/` / `templates/` / `assets/`

**排除范围**：`plans/`、`tests/`、`README.md`、`CHANGELOG.md` 以及 `exclude_patterns` 命中的文件。

**扫描/审查证据（建议填入命令）**：
- `rg -n \"...\" ...`
- `find ...`

---

## 问题清单（按优先级）

> 每个问题至少包含：位置（文件:行号）、影响、修复方式、验证方法。

### P0（必须修复）

1) 标题：
- 位置：`path/to/file:line`
- 影响：
- 修复：
- 验证：

### P1（强烈建议）

1) 标题：
- 位置：`path/to/file:line`
- 影响：
- 修复：
- 验证：

### P2（可选）

1) 标题：
- 位置：`path/to/file:line`
- 影响：
- 修复：
- 验证：

---

## 执行步骤（按顺序）

1) ...
2) ...

---

## 本轮轻量测试

- 会话目录：`{{SESSION_DIR_REL}}/`
- 测试计划：`{{TEST_PLAN_REL}}`
- 测试报告：`{{TEST_REPORT_REL}}`
