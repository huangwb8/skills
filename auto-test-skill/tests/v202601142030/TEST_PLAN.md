# 轻量测试计划（TEST_PLAN）

**测试ID**: v202601142030
**目标技能**: auto-test-skill
**目标技能路径**: /Volumes/2T01/winE/PythonCloud/Agents/pipelines/skills/auto-test-skill
**轮次类型**: A轮
**关联规划文档**: plans/v202601142030.md
**计划时间**: 2026-01-14T20:25

---

## 目标

- 本轮要验证的核心行为是什么？
- 本轮要解决/验证的 P0-P2 问题是什么？
- 本轮的“通过”标准是什么？

---

## 变更范围（本轮）

- 修改文件：
  - {{CHANGED_FILE_1}}
  - {{CHANGED_FILE_2}}
- 重要行为变化：
  - {{BEHAVIOR_CHANGE_1}}
  - {{BEHAVIOR_CHANGE_2}}

---

## 验证点（轻量测试）

### P0（必须通过）
- [ ] {{P0_CHECK_1}}
- [ ] {{P0_CHECK_2}}

### P1（强烈建议通过）
- [ ] {{P1_CHECK_1}}
- [ ] {{P1_CHECK_2}}

### P2（可选）
- [ ] {{P2_CHECK_1}}

---

## 执行步骤

1. 准备：确认目标 skill 当前版本、目录结构与依赖
2. 按顺序执行验证点（每完成一个验证点就记录结果）
3. 如发现新问题：记录到本轮报告“新问题”章节，并标注优先级

---

## 产出清单

- `TEST_REPORT.md`（必需）
- `_artifacts/`（中间文件、输出、日志；可选但推荐）
- `_scripts/`（必要时的测试脚本；可选）
