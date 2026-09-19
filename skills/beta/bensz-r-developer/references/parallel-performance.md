# 并行与性能

## 优化阶梯

1. 用 `bench`/`microbenchmark` 和 `profvis`/`Rprof()` 复现瓶颈。
2. 改善算法、数据结构和复杂度。
3. 使用向量化、矩阵库、`data.table` 或领域高性能包。
4. 减少复制、序列化、磁盘往返；按内存预算分块。
5. 对独立、粒度足够大的任务并行。
6. 热点仍在 R 解释器时再评估 `cpp11`/`Rcpp`。

每层保留同一基准数据、正确性断言和 wall time/峰值内存证据；不要只报告最佳一次。

## future 边界

Package 函数优先调用 `future.apply`/`furrr` 并尊重调用方 plan；不要在库函数里永久执行 `future::plan()`。顶层脚本可这样临时配置：

```r
local({
  old_plan <- future::plan()
  on.exit(future::plan(old_plan), add = TRUE)
  workers <- parallelly::availableCores(omit = 1L)
  future::plan(future::multisession, workers = workers)
  result <- run_job(job, parallel = TRUE, seed = 2026L)
})
```

macOS/Windows 优先 multisession；multicore 不可移植且对连接、GUI 和部分 native library 不安全。集群环境尊重调度器提供的核数，不以 `detectCores()` 当可用配额。

## 必查项

- RNG：使用 `future.seed` 或 L'Ecuyer-CMRG，测试相同 seed 可复现。
- 资源：默认 `availableCores(omit = 1)`；估算每 worker 内存，必要时减少 workers 或分块。
- 嵌套：外层并行时限制 BLAS/OpenMP/模型内部线程，避免过度订阅。
- 全局对象：避免把大对象重复 export 到 worker；优先共享文件、分块或批量任务。
- 错误：保留 job id、seed 和最小输入摘要；失败任务可单独重跑。
- 清理：显式 cluster 必须 `on.exit(parallel::stopCluster(cl), add = TRUE)`；future plan 由设置它的顶层恢复。

## Aggressive 模式

“榨干设备”是显式性能档位，不是默认值。只有任务可中断、内存/温度/交互需求允许、基准证明可扩展且用户同意时，才使用全部可用 worker 或 GPU。记录 backend、workers、线程环境变量、设备、seed 和回退配置。

## 原生代码门禁

引入 C++ 前回答：热点占总时长多少、现有包为何不够、数据复制是否抵消收益、R 参考实现是否冻结、等价容差是什么、CRAN/目标平台工具链是否可用。C++ kernel 应小、纯、可中断；业务编排、文件 I/O 和错误恢复留在 R。

