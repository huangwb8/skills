# 轻量测试计划（A2）

**测试ID**: v202601121152  
**目标**: 验证模板“轻量化”改造 + 文档示例对齐后，脚本生成物可直接使用。  
**关联规划文档**: `auto-test-skill/plans/v202601121152.md`

---

## 变更范围

- `auto-test-skill/templates/TEST_REPORT_TEMPLATE.md`
- `auto-test-skill/templates/OPTIMIZATION_PLAN_TEMPLATE.md`
- `auto-test-skill/SKILL.md`
- `auto-test-skill/README.md`

---

## 验证点

### P0（必须通过）

- [ ] `--create-plan` 生成的 `plans/v202601121152.md` 结构满足 A.2 要求（位置/影响/修复/验证）
- [ ] 新生成的 `tests/v202601121152/TEST_REPORT.md` 为轻量模板（非超长大表格）
- [ ] 关键占位符已被脚本替换（`TEST_ID`/路径/关联规划/时间等）

### P1（强烈建议）

- [ ] `auto-test-skill/SKILL.md` 示例命令可复制使用（两种调用方式都成立）
- [ ] `auto-test-skill/README.md` 对脚本与 `--create-plan` 的说明清晰且不矛盾

---

## 执行命令

- `python3 -m py_compile auto-test-skill/scripts/create_test_session.py`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind a --id v202601121152 --create-plan`
- `rg -n "\\{\\{(TEST_ID|TARGET_SKILL_ROOT|PLAN_DOC_PATH|PLAN_TIME|SESSION_NAME)\\}\\}" auto-test-skill/tests/v202601121152 auto-test-skill/plans/v202601121152.md`（预期无输出）
