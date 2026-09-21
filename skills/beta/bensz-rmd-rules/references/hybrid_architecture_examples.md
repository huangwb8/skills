# 双模式示例

## simple：单报告

输入规模小、整体重跑可接受时，只创建 `00.Environment.R`、一个 Rmd、renv 和 smoke test。Rmd 直接读取授权的 `raw/`，不创建 `_targets.R`、products 缓存或自制 runner。

## complex/pipeline：共享计算与多个报告

```text
R/analysis_functions.R
_targets.R: analysis_input -> prepared_data -> model_results
01-report.Rmd: tar_read("model_results") -> reports/
02-report.Rmd: tar_read("model_results") -> reports/
_targets/: targets metadata and computational state
products/: only explicitly exported scientific objects
```

报告参数变化只重渲染 Rmd；模型代码、输入或参数变化由 targets 失效必要节点。不要把报告层 Top N、配色或图表布局写进重型 target。

## 中断恢复

在 `tmp/tests/<run-id>/_targets` 中让 `model_results` 上游成功、下游报告 target 失败，保留 store 后再次 `tar_make()`。使用 `tar_meta()` 与执行日志确认上游 target 被跳过、失败节点继续；不创建 SUCCESS 或人工 identity 文件。

## 并行与观测

当 cohort/model/bootstrap target 足够独立且昂贵时，在 `_targets.R` 配置 crew controller；worker 数与内部线程数乘积必须在预算内。先用 `tar_poll()`/`tar_watch()` 观察 DAG，再用 crew 日志或 autometric 诊断资源。没有对应包或平台能力时明确记录降级。

## existing

已有编号脚本、旧 runner 或 checkpoint 的项目保持原入口并标记 `preserved-existing`。迁移不是新默认；必须有人类授权、结果比对和回退安排。
