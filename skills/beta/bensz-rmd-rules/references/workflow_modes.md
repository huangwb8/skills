# 项目状态与工作流模式

## 两个判断维度

先判 `project_state`，再判 `workflow_mode`。工作流模式只有 `simple` 与 `complex`；`complex` 在文档中也称 **pipeline**，不是另一套模式。`existing` 是项目状态，不是第三种工作流模式。

| 维度 | 取值 | 含义 |
| --- | --- | --- |
| 项目状态 | `new` / `existing` | 决定能否采用新布局；existing 不自动迁移或补齐 |
| 工作流模式 | `simple` / `complex` | complex = targets-first pipeline |

决策优先级固定为：人类显式指定 → existing 不自动迁移边界 → AI 根据依赖、重算成本、复用、恢复与并行需求选择。选择结果和理由进入分析计划或交付摘要。

## simple

适合线性、低成本、整体重跑可接受的小分析或单报告：

- 必须有 `renv.lock` 与 `renv/activate.R`；
- 不创建 `_targets.R` 或 `_targets/`；
- 正式入口是明确的 Rscript、`rmarkdown::render()` 或项目操作脚本；
- smoke test 调用同一正式入口并真实执行；
- 不开发自制 runner、checkpoint 或缓存命中协议。

## complex / pipeline

出现非线性依赖、昂贵步骤、多下游复用、局部失效、断点恢复、血缘或并行需求时选择 complex。其唯一计算组织方式是：

```text
renv.lock + renv/activate.R
_targets.R       # 唯一 DAG、依赖与增量重建入口
R/               # target 调用的计算函数
Rmd              # tar_read()/tar_load() 消费结果并负责科学沟通
_targets/        # targets 自己管理的机器计算状态
products/        # 需要审阅、复用或交付的科学对象（可选）
reports/         # 图、表、HTML 与补充材料
```

不得再为 pipeline 生成编号执行图、`SUCCESS`、identity hash、force-step/resume runner 或自定义 checkpoint helper。`products/` 不是第二个缓存系统；只有科学上需要持久化的对象才导出。

`_targets.R` 的人类可读性契约：target 按阶段用注释块分组（输入/计算/交付），target 一律语义化命名；交付摘要附 `targets::tar_manifest()` 快照，作为人类可读的流程地图。

普通 `tar_make()` 是默认执行方式。只有存在足够多相互独立且昂贵的 target 时才增加 `crew` controller，并同时限制 worker 与内部线程，防止 CPU/内存超卖。

## existing 项目

已有任一 R/Rmd、raw、products、reports、`_targets.R`、renv 或历史产品的项目判为 `existing`；只读盘点、披露观察到的机制，不自动补建、迁移或删除：

- 已有 `_targets.R`：按 complex 契约维护现有 DAG 与正式 store。
- 无 targets（含历史编号脚本）：按 simple 语义维护。编号脚本只是顺序执行的普通 Rscript 入口，本 Skill 不提供、不维护任何编号 runner、编号单元检查器或第二套执行编排。
- 任务出现非线性依赖、昂贵步骤、恢复或复用等复杂信号时，先给出旧→新映射、结果比对和回退入口的显式迁移方案，经人类授权后再迁移到 complex；缺失 renv/targets 机制只披露风险，不隐式初始化。

## 检查入口

```bash
python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state new --workflow-mode simple
python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state new --workflow-mode complex
python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state existing --workflow-mode auto
python3 <skill-root>/scripts/check_pipeline_contract.py <project>
```

检查器只读：simple 拒绝 targets 入口；complex 要求 `_targets.R`、`R/` 与隔离 test store，并检查 Rmd 是否消费 target；existing 的缺失机制降级为 warning，不因缺失新机制失败，模式契约冲突仍报 error。
