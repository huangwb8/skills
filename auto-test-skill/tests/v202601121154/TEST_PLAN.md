# 轻量测试计划（A4）

**测试ID**: v202601121154  
**目标**: 验证 CLI 友好错误输出 + `TEST_PLAN_TEMPLATE` 的 `ROUND_KIND` 与相对路径替换。  
**关联规划文档**: `auto-test-skill/plans/v202601121154.md`

---

## 变更范围

- `auto-test-skill/scripts/create_test_session.py`
- `auto-test-skill/templates/TEST_PLAN_TEMPLATE.md`

---

## 验证点

### P0（必须通过）

- [ ] `--kind c` 输出 usage + `error:`，且无 traceback
- [ ] 新会话 `tests/v202601121154/TEST_PLAN.md` 中 `轮次类型` 自动为 `A轮`
- [ ] `关联规划文档` 为相对路径（`plans/v202601121154.md`）

---

## 执行命令

- `python3 -m py_compile auto-test-skill/scripts/create_test_session.py`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind a --id v202601121154 --create-plan`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind c --id v202601121154`（预期失败；证据见 `_artifacts/invalid_kind.out`）
