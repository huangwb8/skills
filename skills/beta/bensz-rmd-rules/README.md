# bensz-rmd-rules

面向 R 数据分析、R Markdown 报告、可复现 targets 流水线、论文级图表与专家解读的工作流 Skill。版本号以 [config.yaml](config.yaml) 的 `skill_info.version` 为唯一来源。

## 什么时候使用

适合从原始数据完成整理、统计、模型、图表、Rmd/HTML 与结果解读，或维护已有 R/Rmd 项目。不适合主要交付物是跨项目复用的 R API、类或 Package（使用 `bensz-r-developer`），也不用于仅渲染既有 Rmd（使用 `knit-rmd-html`）。

## 最短用法

```text
请用 bensz-rmd-rules 完成这个 R 分析。先只读判断项目是 new 还是 existing；
说明为什么选择 simple 或 targets-first complex/pipeline（已有 _targets.R 的项目按 complex 维护）。
使用 renv，并在正式运行前用 synthetic_fixture 或 project_subset 从正式入口真实跑通轻量测试。
```

已有项目不会因为新默认而自动补 targets、renv 或迁移目录；历史编号 runner 已整体移除，旧编号脚本项目按 simple 语义维护（编号脚本只是顺序执行的普通入口），需要复杂能力时显式迁移到 targets。

## simple 与 complex/pipeline

| 模式 | 适用场景 | 固定要求 |
| --- | --- | --- |
| `simple` | 线性、低成本、整体重跑可接受的小分析/单报告 | renv、明确 R/Rmd 入口、真实 smoke test；不创建 targets |
| `complex`（说明性别名 `pipeline`） | 非线性依赖、昂贵步骤、多下游复用、局部失效、恢复或并行 | `_targets.R` 唯一 DAG、`R/` 计算函数、Rmd 消费 target、隔离恢复验收 |

`new`/`existing` 是项目状态不是模式：已有 `_targets.R` 的项目按 complex 维护；无 targets 的已有项目（含历史编号脚本）按 simple 语义维护。

复杂项目的核心关系是：

```text
renv.lock → _targets.R → R/ functions → target results → Rmd → reports/
                         ↘ optional products/
                         ↘ _targets/ (machine state)
```

`_targets/` 只承担 targets 的机器状态；`products/` 只保存需要审阅、复用或交付的科学对象，不实现第二套缓存、`SUCCESS`、identity hash 或恢复 runner。

## 新 pipeline 布局

```text
项目根目录/
├── 00.Environment.R
├── R/                         # target 调用的计算函数
├── _targets.R                 # 唯一 DAG 入口
├── _targets/                  # 正式机器计算状态
├── raw/                       # 只读
├── products/                  # 可选科学产物
├── reports/                   # 图、表、HTML、补充材料
├── scripts/tests/             # 可版本化测试代码
├── tmp/tests/<run-id>/        # 隔离输入、store、日志与运行记录
├── renv.lock
└── renv/activate.R
```

模板 [_targets.R](templates/_targets.R) 使用 `tar_source("R")`；模板 [R_data_template.R](templates/R_data_template.R) 提供 `prepare_data()`/`analyze_data()` 起点；模板 [Rmd_template.Rmd](templates/Rmd_template.Rmd) 通过 `targets::tar_read()` 消费 `analysis_results`。Rmd 的 Top N、阈值、配色和版式属于报告层，不应触发无关重型 target。

`_targets.R` 的人类可读性契约：target 按阶段注释块分组并语义化命名，交付摘要附 `tar_manifest()` 快照作为流程地图。

## 测试与恢复

每个新建或实质修改的分析流都要真实执行 `synthetic_fixture` 或 `project_subset`。complex 测试使用同一 target 图，但 store 位于唯一 `tmp/tests/<run-id>/_targets`，不能污染正式 store、products 或 reports。

恢复必须是真实行为：先让昂贵 target 成功，再中断后续 target，随后在输入、代码、参数和 renv 身份不变时再次 `tar_make()`；用 `tar_meta()`、outdated target 集合和执行记录证明有效前序 target 被跳过。删除 store、改变输入/代码/参数或显式强制重算时，targets 应重新计算必要节点。

## 并行与观测

普通 `tar_make()` 是默认入口。只有 DAG 中有足够多相互独立且昂贵的任务时才配置 `crew`；worker 数与 BLAS/OpenMP/future/BiocParallel 内部线程数必须受资源预算约束。进度使用 `tar_poll()`/`tar_watch()`，worker 日志/指标使用 crew，资源诊断按需使用 `autometric`。这些都是项目级可选依赖，Skill 不自制调度器或 dashboard。

## 检查入口

```bash
python3 <skill-root>/scripts/check_targets_renv.py <project> --project-state new --workflow-mode complex
python3 <skill-root>/scripts/check_pipeline_contract.py <project>
Rscript <project>/scripts/tests/smoke_test.R
```

所有 Rmd 仍需执行解读覆盖、解读质量、widget 可见性、图表可读性与数字追溯检查。未运行全量数据时，交付记录必须写明 `full_data_execution=NOT_RUN`。

## WHICHMODEL - 模型选择建议

普通 simple 报告可使用具备可靠代码编辑与文件操作能力的主流模型；targets 依赖、恢复契约和跨文件审查复杂时，优先选择推理与长上下文能力更强的模型。模型选择不能替代确定性检查、真实 R 执行、恢复验收和人工确认科学结论。
