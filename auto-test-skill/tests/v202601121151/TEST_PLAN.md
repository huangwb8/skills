# 轻量测试计划（A1）

**测试ID**: v202601121151  
**目标**: 验证 `scripts/create_test_session.py` 的新增参数与默认安全策略可用、可复现。  
**关联规划文档**: `auto-test-skill/plans/v202601121151.md`

---

## 变更范围

- `auto-test-skill/scripts/create_test_session.py`

---

## 验证点

### P0（必须通过）

- [ ] `--create-plan` 可创建缺失的 `plans/{id}.md`，且默认不覆盖已有文件
- [ ] `--kind` 非法值会失败并给出明确错误（不产生半成品目录）
- [ ] 默认不覆盖：重复运行同一 `--id` 不会改写现有 `TEST_PLAN.md` / `TEST_REPORT.md`

### P1（强烈建议通过）

- [ ] `TEST_PLAN.md` 会用 `templates/TEST_PLAN_TEMPLATE.md` 初始化，并替换关键占位符（如 `TEST_ID`、路径、计划文档路径）
- [ ] `TEST_REPORT.md` 若存在 `templates/TEST_REPORT_TEMPLATE.md` 则用其初始化

---

## 执行命令

- `python3 -m py_compile auto-test-skill/scripts/create_test_session.py`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind a --id v202601121151 --create-plan`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind c --id v202601121151`（预期失败；证据落盘到 `_artifacts/`）
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind a --id v202601121151`（重复运行；预期不覆盖）
