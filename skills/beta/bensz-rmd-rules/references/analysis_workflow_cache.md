# Pipeline 状态、科学产品与恢复契约

## 1. 唯一计算事实来源

在新 `complex/pipeline` 项目中，`_targets.R` 是唯一 DAG、依赖、失效和增量重建入口；`_targets/` 是 targets 自己管理的机器状态。不要再复制一套 `SUCCESS`、identity hash、metadata checkpoint 或编号 runner 来决定是否重算。

`analysis-plan.yaml` 只做需求映射、target/报告关系和验收记录，不是调度器。历史项目已有的 runner 或 checkpoint 只在 `existing/preserved-existing` 分支保留，迁移必须显式授权。

## 2. 科学产品与报告

`products/` 只保存需要人工审阅、下游复用或正式交付的科学对象，例如完整结果 RDS、矩形表、数据字典或结果摘要；并非每个 target 都要导出。`reports/` 保存 PDF、图、表、HTML 和补充材料。二者不承担 targets 的缓存命中、失效或恢复。

产品元数据可以记录科学说明、数据字典和交付来源，但不得成为第二个缓存判定协议，也不应写入凭据、绝对私有路径或大体积原始数据。

## 3. R/ 与 Rmd 边界

计算函数放在项目 `R/`，由 `_targets.R` 的 `tar_source("R")` 发现并调用。target 产出完整、未按展示阈值截断的结果。Rmd 通过 `tar_read()`/`tar_load()` 消费结果；若使用 `tarchetypes::tar_render()`，报告 target 必须在 DAG 中明确声明且不能形成循环。

Top N、阈值、配色和版式是报告参数。只改报告参数时，应只重渲染报告或报告 target，不触发无关重型 target；Rmd 不得从 `raw/` 绕过 DAG 重做昂贵计算。

## 4. 中断与恢复验收

恢复不是“文件存在”检查，而是真实运行证据：

1. 在隔离 `tmp/tests/<run-id>/_targets` store 中先让至少一个昂贵 target 成功；
2. 让后续 target 中断或失败并保留 store；
3. 在不改变输入、代码、参数和 renv 身份、且未显式强制重算的条件下再次执行 `targets::tar_make()`；
4. 从 `tar_meta()`、outdated target 集合和执行日志确认前序 target 被跳过，仅未完成或失效部分继续；
5. 删除 store、改变输入/代码/参数或显式请求重算时，确认 targets 重新计算必要节点。

恢复证据以 targets metadata 和实际执行记录为准，不手工补写标记，也不把 worker 日志当作 DAG 状态。

## 5. 可选并行与观测

无 `crew` 时普通 `tar_make()` 必须正常运行。仅当独立昂贵 target 的收益覆盖 worker 启动和传输开销时，才在 `_targets.R` 中配置 crew controller；worker 内 BLAS/OpenMP/future/BiocParallel 线程数必须受资源预算约束。

进度优先使用 `tar_poll()` 或 `tar_watch()`；worker 日志/指标使用 crew 能力；资源诊断按需使用 `autometric::log_start()`、`log_read()` 和 `log_plot()`。Skill 不定义新的调度器、事件字段、心跳、资源采样器、dashboard 或告警平台；缺少可选依赖时记录观测降级。
