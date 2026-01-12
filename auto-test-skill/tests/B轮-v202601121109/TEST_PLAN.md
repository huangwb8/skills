# TEST_PLAN: auto-test-skill B轮-v202601121109

**测试ID**: B轮-v202601121109
**目标**: 基于 `auto-test-skill/plans/B轮-v202601121109.md` 对关键结论做最小验证

---

## 验证点（轻量）

- [ ] `config.yaml` 中 `templates.*` 引用的文件均存在
- [ ] `scripts/create_test_session.py` 输入校验与“不覆盖默认策略”工作正常
- [ ] `SKILL.md` 与 `README.md` 的目录/产出描述一致

---

## 执行命令

- `python3 -m py_compile auto-test-skill/scripts/create_test_session.py`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind a --id v209901010001`
- `python3 auto-test-skill/scripts/create_test_session.py --skill-root auto-test-skill --kind b --id v209901010001`

