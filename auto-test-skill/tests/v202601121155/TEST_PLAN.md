# 轻量测试计划（A5）

**测试ID**: v202601121155  
**目标**: 回归验证脚本在 A/B 轮的关键字段渲染与错误输出，并确认 B 轮报告不会“默认写错对应A轮ID”。  
**关联规划文档**: `auto-test-skill/plans/v202601121155.md`

---

## 变更范围

- `auto-test-skill/scripts/create_test_session.py`

---

## 验证点

### P0（必须通过）

- [ ] A 轮会话创建正常：`tests/v202601121155/` 结构完整
- [ ] B 轮会话创建正常：`tests/B轮-v202601121155/` 结构完整
- [ ] B 轮计划文档 `plans/B轮-v202601121155.md` 中 `{{A_TEST_ID}}` 保持占位符（不被默认替换）

### P1（强烈建议）

- [ ] 非法 `--kind` 输出无 traceback（证据：`_artifacts/invalid_kind.out`）
- [ ] A/B 轮 `TEST_PLAN.md` 的 `轮次类型` 分别为 `A轮` / `B轮`
- [ ] A/B 轮 `关联规划文档` 均为 `plans/...` 相对路径

---

## 执行命令

- `python3 -m py_compile auto-test-skill/scripts/create_test_session.py`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind a --id v202601121155 --create-plan`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind b --id v202601121155 --create-plan`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind c --id v202601121155`（预期失败）
