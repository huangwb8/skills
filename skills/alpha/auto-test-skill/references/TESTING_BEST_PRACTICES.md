# 测试驱动优化：轻量测试最佳实践

本文件用于为 `auto-test-skill` 提供稳定、可复用的参考原则，避免在 SKILL.md 中反复硬编码细节。

## 轻量测试的边界

- 目标：验证“关键路径”与“最近修改的行为”是否正确，不追求全覆盖。
- 原则：快、明确、可重复、可追溯。

## 测试会话的最小产出

每轮测试会话目录至少包含：

- `TEST_PLAN.md`：本轮验证点与通过标准
- `TEST_REPORT.md`：本轮结果、证据与结论

推荐包含：

- `_artifacts/`：日志、输出、截图、对比结果等
- `_scripts/`：必要的临时测试脚本（尽量保持小且可删）

## 命名与目录

- 规划文档：`.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-skill/output/plans/vYYYYMMDDHHMM.md`
- A轮测试：`.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-skill/output/tests/vYYYYMMDDHHMM/`
- B轮检查：`.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-skill/output/plans/B轮-vYYYYMMDDHHMM.md`
- B轮验证：`.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-skill/output/tests/B轮-vYYYYMMDDHHMM/`

## 记录原则

- 一个结论必须对应至少一个可复现的证据（命令输出、文件、截图、对比结果）。
- 发现新问题时：立刻记录优先级（P0/P1/P2）与复现步骤。
