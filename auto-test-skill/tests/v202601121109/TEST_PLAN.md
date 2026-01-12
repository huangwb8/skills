# TEST_PLAN: auto-test-skill v202601121109

**测试ID**: v202601121109
**目标**: 按 `auto-test-skill/plans/v202601121109.md` 完成 P0-P2 的结构升级与一致性修复

---

## 验证点（必须通过）

### P0

- [ ] `auto-test-skill/config.yaml` 包含测试轮次 + B轮检查配置 + 目录规范
- [ ] `auto-test-skill/SKILL.md` 工作流明确描述 A轮×N + B轮
- [ ] 测试目录命名统一为 `tests/`（不再使用 `test/` 作为主路径）

### P1

- [ ] 存在 B轮质量检查模板：`auto-test-skill/templates/B_ROUND_CHECK_TEMPLATE.md`
- [ ] `auto-test-skill/README.md` 示例与目录结构与 SKILL.md 一致

### P2

- [ ] 补齐缺失模板：`auto-test-skill/templates/TEST_PLAN_TEMPLATE.md`、`auto-test-skill/templates/FINAL_SUMMARY_TEMPLATE.md`
- [ ] 提供确定性辅助脚本：`auto-test-skill/scripts/create_test_session.py`
- [ ] 补齐参考文档：`auto-test-skill/references/TESTING_BEST_PRACTICES.md`
- [ ] `auto-test-skill/CHANGELOG.md` 记录变更

---

## 轻量测试命令

- `python3 -m py_compile auto-test-skill/scripts/create_test_session.py`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind a --id v209901010000`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind b --id v209901010000`
- `rg -n \"\\btest/\" auto-test-skill -S`（确保无旧路径残留在核心文档）

