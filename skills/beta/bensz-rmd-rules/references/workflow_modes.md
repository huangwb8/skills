# 项目状态与工作流模式

## 两个判断维度

先判 `project_state`，再判 `workflow_mode`。二者不可混为一个 `mode`：

| 维度 | 取值 | 含义 |
| --- | --- | --- |
| 项目状态 | `new` / `existing` | 决定能否采用新布局，existing 永远优先保护现有架构 |
| 工作流模式 | `simple` / `complex` / `preserved-existing` | 前两者只用于新项目；已有项目统一保留现状 |

决策优先级固定为：人类显式指定 → existing 兼容边界 → AI 根据任务复杂度选择。选择结果和理由必须进入分析计划或交付摘要。

## 项目状态

- 空目录或人类明确声明从零新建：`new`。
- 已存在 R/Rmd、产品、报告、历史 runner、`_targets.R`、`renv/` 或 `renv.lock`：`existing`。
- 信号冲突时保持只读；在不能安全推断迁移意图时才请求澄清。

`existing` 检查永远是只读的，`workflow_mode` 固定记为 `preserved-existing`，并另行输出实际观察到的 renv、targets、旧 runner 与产品路径。缺少机制只报告复现性/恢复风险，不创建文件。只有人类明确要求规范化或迁移时，才先提供旧→新映射、结果校验和回退入口，再改结构。

## simple

适合线性、低成本、整体重跑可接受的小分析或报告：

- 必须有 `renv.lock` 与 `renv/activate.R`；
- 不创建 `_targets.R` 或 `_targets/`；
- 正式入口是明确的 Rscript、`rmarkdown::render()` 或项目专用 `scripts/operations/`；
- `scripts/tests/smoke_test.R` 使用同一正式入口完成真实轻量测试；
- 不开发自制调度器。若出现复杂失效与恢复需求，升级到 complex。

## complex

出现以下任一实质信号时选择 complex：

- 非线性依赖或多个有真实失败边界的计算阶段；
- 计算昂贵、外部请求或失败代价高；
- 中间产品被多个下游复用；
- 需要局部失效、断点恢复、数据血缘或并行。

脚本数量和代码行数只能作为线索。complex 继承 simple 的 renv、目录和测试契约，并增加 `_targets.R`。正式 store 是 `_targets/`；测试必须执行同一图但显式使用 `tmp/tests/<run-id>/_targets`。targets 管依赖和增量执行，`products/` 管可审查、可恢复、供下游复用的正式派生产品，二者不能互相替代。

## 人工覆盖、升级与降级

- 人类指定 simple/complex 时，在安全且可执行的前提下优先遵循，并披露明显风险。
- 首次交付前，在建 simple 出现实质复杂信号时可记录理由并升级；首次交付后已是 existing，升级属于迁移，必须由人类明确要求。不要靠第二套 runner 延长 simple。
- complex 不因当前数据较小而自动降级；降级会改变恢复和血缘契约，必须有人类明确意图。
- existing 不能仅因“看起来像 simple/complex”而迁移。

## 检查入口

```bash
python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state new --workflow-mode simple

python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state new --workflow-mode complex

python3 <skill-root>/scripts/check_targets_renv.py <project> \
  --project-state existing --workflow-mode preserved-existing
```

兼容参数 `--mode auto|new|existing` 仅作为 `--project-state` 的旧别名，不改变旧含义。检查器只读：simple 要求 renv 与测试入口且拒绝 `_targets.R`；complex 额外要求 `_targets.R` 和唯一 run root 下的隔离 test store；existing 只接受 `preserved-existing`，不因缺失机制失败。
