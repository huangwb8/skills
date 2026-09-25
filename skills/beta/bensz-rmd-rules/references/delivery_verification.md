# 交付验证记录

交付摘要只记录可复核证据，不复制敏感数据或绝对私有路径。

| 检查项 | 结论 | 证据 |
| --- | --- | --- |
| 项目状态与模式 | PASS/FAIL | `project_state`、`workflow_mode`、选择理由与人工覆盖 |
| renv | PASS/FAIL/NA | lockfile、activation、`renv::status()`；existing 可为风险披露 |
| 需求—target—报告映射 | PASS/FAIL/NA | targets 清单或 `analysis-plan.yaml` |
| 目录与产品路径 | PASS/FAIL | raw/R/_targets/products/reports/scripts/templates/tmp 边界与单一路径设置 |
| 测试风格 | PASS/FAIL | `synthetic_fixture` 或 `project_subset` 及选择理由 |
| 真实轻量运行 | PASS/FAIL/BLOCKED | 正式入口、唯一 run root、命令、退出码；不得用 dry-run 替代 |
| 测试隔离 | PASS/FAIL | raw/正式 products/reports/_targets 前后不变；test store 路径 |
| 数据与科学断言 | PASS/FAIL | schema、主键/分组、范围/不变量、边缘条件 |
| 主要估计对象推断 | PASS/FAIL/NA/NOT_RUN | 逐项列参数、估计值/CI/有效 N/方法及适用的 p/q，或明确 `not_applicable`、`not_estimable`、`not_run` 和理由 |
| 方法与报告对应 | PASS/FAIL/NA/NOT_RUN | 计算代码/完整结果表/报告位置；配对、聚类、删失、缺失、模型假设和多重比较复核；文本检查不作方法证明 |
| 预期交付生成 | PASS/FAIL | 产品、报告、图表可读性与数字追溯 |
| targets 恢复 | PASS/FAIL/NA | `tar_meta()`、outdated 集合、store 损坏/失效/中断恢复用例 |
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
- 逐参数推断状态（已计算并验证 / 不适用 / 受数据或设计限制 / 未运行）与报告数字来源：
- project subset cleanup：
- 未运行、阻塞或无法确认的项目：
- 剩余风险与恢复入口：

宿主无独立子 Agent 时写 `DEGRADED: 三项职责分离顺序自检，非独立审查`；不得写 PASS 冒充。
