# 项目状态与工作流模式

## 两个判断维度

先判 `project_state`，再判 `workflow_mode`。新项目只有 `simple` 与 `complex`；`complex` 在文档中也称 **pipeline**，不是另一套模式。已有项目统一为 `preserved-existing`。

| 维度 | 取值 | 含义 |
| --- | --- | --- |
| 项目状态 | `new` / `existing` | 决定能否采用新布局；existing 永远保护现有架构 |
| 工作流模式 | `simple` / `complex` / `preserved-existing` | complex = targets-first pipeline |

决策优先级固定为：人类显式指定 → existing 兼容边界 → AI 根据依赖、重算成本、复用、恢复与并行需求选择。选择结果和理由进入分析计划或交付摘要。

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

不得再为新 pipeline 生成编号执行图、`SUCCESS`、identity hash、force-step/resume runner 或自定义 checkpoint helper。`products/` 不是第二个缓存系统；只有科学上需要持久化的对象才导出。

普通 `tar_make()` 是默认执行方式。只有存在足够多相互独立且昂贵的 target 时才增加 `crew` controller，并同时限制 worker 与内部线程，防止 CPU/内存超卖。

## existing / preserved-existing

只要项目已经存在任一 R/Rmd、raw、products、reports、runner、`_targets.R`、renv 或历史产品，就按 `existing` 维护。只读盘点并披露已观察的 targets、renv、旧 runner 与产品机制；不自动补建、迁移或删除。人类明确要求迁移时，先提供旧→新映射、结果比对、回退入口和清理确认。

## 检查入口

```bash
python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state new --workflow-mode simple
python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state new --workflow-mode complex
python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state existing --workflow-mode preserved-existing
python3 <skill-root>/scripts/check_pipeline_contract.py <project>
```

检查器只读：simple 拒绝 targets 入口；complex 要求 `_targets.R`、`R/` 与隔离 test store，并检查 Rmd 是否消费 target；existing 仅报告风险，不因缺失新机制失败。
