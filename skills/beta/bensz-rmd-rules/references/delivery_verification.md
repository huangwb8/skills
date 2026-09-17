# 交付验证记录

交付摘要使用真实证据填写；不复制原始敏感数据或绝对私有路径。

| 检查项 | 结论 | 证据 |
| --- | --- | --- |
| 需求—单元映射 | PASS/FAIL | `analysis-plan.yaml` 与检查器输出 |
| 编号与依赖 | PASS/FAIL | 无重复、前向依赖、循环或缺失上游 |
| 目录边界 | PASS/FAIL | `raw/products/reports/.bensz-api` 抽查 |
| 缓存身份 | PASS/FAIL | 输入、参数、代码、上游、契约版本 |
| 完成标记 | PASS/FAIL | 半成品无 `SUCCESS`；成功产品复验通过 |
| 局部失效 | PASS/FAIL | 参数/代码/上游变化用例 |
| 断点恢复 | PASS/FAIL | 前序 hit、失败单元 run、必要下游失效 |
| 串行审查 | PASS/FAIL/DEGRADED | 三轮只读结果与轮间修正摘要 |
| 图表与 HTML | PASS/FAIL | PDF/JPG 视觉、widget 可见性 |
| 解读与数字 | PASS/FAIL | 覆盖、质量、指标导读、数字追溯 |
| 旧项目兼容 | PASS/FAIL/NA | 未迁移/覆盖旧 `tmp/` 路径 |

## 运行摘要

- 检查命令与退出码：
- 实际运行的编号单元：
- cache hit / miss 及原因：
- 未运行或无法确认的项目：
- 剩余风险与恢复入口：

若宿主无独立子 Agent，必须写 `DEGRADED: 三轮职责分离顺序自检，非独立审查`，不得写 PASS 冒充。
