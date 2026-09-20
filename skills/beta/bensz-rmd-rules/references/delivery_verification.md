# 交付验证记录

交付摘要只记录可复核证据，不复制敏感数据或绝对私有路径。

| 检查项 | 结论 | 证据 |
| --- | --- | --- |
| 项目状态与模式 | PASS/FAIL | `project_state`、`workflow_mode`、选择理由与人工覆盖 |
| renv | PASS/FAIL/NA | lockfile、activation、`renv::status()`；existing 可为风险披露 |
| 需求—单元映射 | PASS/FAIL/NA | 分析单元表或 `analysis-plan.yaml` |
| 目录与产品路径 | PASS/FAIL | raw/products/reports/scripts/templates/tmp 边界与单一路径设置 |
| 测试风格 | PASS/FAIL | `synthetic_fixture` 或 `project_subset` 及选择理由 |
| 真实轻量运行 | PASS/FAIL/BLOCKED | 正式入口、唯一 run root、命令、退出码；不得用 dry-run 替代 |
| 测试隔离 | PASS/FAIL | raw/正式 products/reports/_targets 前后不变；test store 路径 |
| 数据与科学断言 | PASS/FAIL | schema、主键/分组、范围/不变量、边缘条件 |
| 预期交付生成 | PASS/FAIL | 产品、报告、图表可读性与数字追溯 |
| 缓存与恢复 | PASS/FAIL/NA | identity、SUCCESS、损坏/失效/恢复用例 |
| 串行审查 | PASS/FAIL/DEGRADED | 三项只读结果与修正摘要 |
| 旧项目兼容 | PASS/FAIL/NA | 未自动补机制、迁移或覆盖旧路径 |

## 尝试记录

每次执行追加一行：

| 尝试 | 命令 | 退出状态 | 失败类别 | 修正摘要 | 断言 | 剩余风险 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 |  |  | environment_dependency / fixture_or_subset / path_isolation / analysis_code / scientific_assertion / report_rendering / external_service / none |  |  |  |

## 运行摘要

- 正式入口与测试入口：
- simple R/Rmd 或 complex target 实际执行证据：
- test store / 临时输出：
- 正式路径前后不变性：
- subject identity 与环境来源：
- preflight / lightweight_execution / full_data_execution（未跑全量为 NOT_RUN）：
- project subset cleanup：
- 未运行、阻塞或无法确认的项目：
- 剩余风险与恢复入口：

宿主无独立子 Agent 时写 `DEGRADED: 三项职责分离顺序自检，非独立审查`；不得写 PASS 冒充。
