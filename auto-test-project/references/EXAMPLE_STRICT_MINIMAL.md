# 严格模式最小示例（P0-1 编号）

本示例用于演示如何让“计划文档 + 测试报告”在严格模式下通过一致性检查：

- 计划文档包含 `#### P0-1:` 这类可引用编号
- 测试报告中出现相同编号
- 运行验证脚本时使用 `--require-plan`

## 示例：plans/vYYYYMMDDHHMM.md（节选）

```markdown
#### P0-1: create_test_session 的 B 轮创建崩溃

位置: auto-test-project/scripts/create_test_session.py:120

影响: --kind b 无法使用

修复建议: 先计算 session_name 再构造模板变量

验证方法: 运行 create_test_session.py --kind b 并确认返回 0
```

## 示例：tests/vYYYYMMDDHHMM/TEST_REPORT.md（节选）

```markdown
### P0-1: create_test_session 的 B 轮创建崩溃

修复前: --kind b 运行报错

修复措施: 调整变量初始化顺序

修复后: --kind b 可创建 tests/B轮-vYYYYMMDDHHMM/

验证方法:
python3 auto-test-project/scripts/create_test_session.py --project-root . --kind b --id vYYYYMMDDHHMM
```

## 严格验证命令

在项目根目录执行：

```bash
python3 auto-test-project/scripts/verify_test_session.py --require-plan tests/vYYYYMMDDHHMM
```

