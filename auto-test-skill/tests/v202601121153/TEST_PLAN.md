# 轻量测试计划（A3）

**测试ID**: v202601121153  
**目标**: 验证版本号同步与文档口径补齐后，一致性与脚本行为均正常。  
**关联规划文档**: `auto-test-skill/plans/v202601121153.md`

---

## 变更范围

- `auto-test-skill/config.yaml`
- `auto-test-skill/SKILL.md`
- `auto-test-skill/README.md`

---

## 验证点

### P0（必须通过）

- [ ] `auto-test-skill/config.yaml` 的 `skill_info.version` 为 `2.0.1`
- [ ] `auto-test-skill/SKILL.md` 的 YAML `version` 为 `2.0.1`
- [ ] `rg -n "2\\.0\\.0" auto-test-skill` 无输出（无旧版本残留）

### P1（强烈建议）

- [ ] `auto-test-skill/README.md` 明确说明版本号以 `skill_info.version` 为准
- [ ] `--create-plan --seed-test-plan-from-plan` 可一次性生成并“用计划文档初始化 TEST_PLAN”（仅作为可选能力验证）

---

## 执行命令

- `python3 -m py_compile auto-test-skill/scripts/create_test_session.py`
- `rg -n "^version:|version: \\\"|version\\\"" auto-test-skill/SKILL.md auto-test-skill/config.yaml`
- `rg -n "2\\.0\\.0" auto-test-skill`
