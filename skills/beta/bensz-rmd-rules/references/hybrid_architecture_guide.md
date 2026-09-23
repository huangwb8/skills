# R + Rmd 双模式架构

## 新项目目录职责

```text
项目根目录/
├── 00.Environment.R
├── R/                         # targets 调用的计算函数
├── reports/                   # 正式图、表、HTML 与补充材料
├── products/                  # 可选科学产品，不是缓存命中协议
├── raw/                       # 只读原始输入
├── templates/                 # 样式/渲染资产
├── scripts/tests/             # 可版本化测试代码
├── tmp/tests/<run-id>/        # 隔离测试现场与 test store
├── renv.lock
├── renv/activate.R
├── _targets.R                 # complex 的唯一 DAG 入口
└── _targets/                  # complex 的正式 targets store
```

| 组件 | 负责 | 不负责 |
| --- | --- | --- |
| `00.Environment.R` | 包加载、项目根、路径与全局配置 | 具体统计逻辑 |
| `R/` | 可被 target 调用的计算函数 | DAG 编排、报告展示 |
| `_targets.R` | 依赖、失效、增量执行与可选报告 target | 科学解释与自定义缓存协议 |
| `.Rmd` | `tar_read()`/`tar_load()`、展示参数、图表和解读 | 从 raw 重做昂贵计算 |
| `_targets/` | targets 机器计算状态 | 正式科学产品 |
| `products/` | 审阅、复用或交付的科学对象 | 缓存命中与恢复判断 |
| `reports/` | 论文图、表、HTML、补充材料 | 源码、模型缓存、运行日志 |
| `tmp/tests/<run-id>/` | 测试输入、隔离 store、日志与运行记录 | 正式结论唯一来源 |

## simple

线性、低成本单报告使用 renv 和明确的 R/Rmd 入口，smoke test 真实 render；不创建 targets、编号执行图或自制缓存。

## complex / pipeline

复杂项目采用 `renv + _targets.R + R/ + Rmd`。普通 `tar_make()` 为默认执行；Rmd 只消费 target 结果。`products/` 按科学交付需要选择性导出，不能重新变成第二个 store。恢复验收必须真实证明中断后再次 `tar_make()` 会复用有效前序 target。

## 并行和观测

`crew`、集群插件和 `autometric` 都是项目级可选依赖。先以 targets 状态判断 DAG，再用 `tar_poll()`/`tar_watch()` 看进度，最后用 worker 日志或资源图诊断。限制 worker 与内部线程乘积；没有资源预算时保持串行。

## existing 与迁移

已有编号脚本或旧 runner 的项目按 simple 语义维护：编号脚本只是顺序执行的普通 Rscript 入口，不设专门兼容模式；自制 checkpoint、编号 runner 与 `tmp/{主脚本名}/` 产品路径模式已移除，不再维护。只有人类明确授权迁移时，才建立旧→新映射、结果比对、回退入口和清理计划；新默认不隐式迁移。
