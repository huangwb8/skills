# bensz-rmd-rules

面向 R 数据分析、R Markdown 报告、可恢复数据产品、论文级图表与专家解读的工作流 Skill。版本号以 [config.yaml](config.yaml) 的 `skill_info.version` 为唯一来源。

## 什么时候使用

适合：

- 从原始数据完成整理、统计、模型、图表、Rmd/HTML 与结果解读；
- 建立可复现、可恢复、可审查的 R 分析流程；
- 维护已有 R/Rmd 项目，同时保护现有入口和产品；
- 在分析中编写只服务当前单元或当前项目的 helper。

不适合：主要交付物是跨项目复用的 R API、类或 Package（使用 `bensz-r-developer`）；只渲染既有 Rmd（使用 `knit-rmd-html`）；其它语言的数据分析。

## 最短用法

```text
请用 bensz-rmd-rules 完成这个 R 分析。先只读判断项目是 new 还是 existing；
若为新项目，再说明为什么选择 simple 或 complex。使用 renv，并在正式运行前
选择 synthetic_fixture 或 project_subset，从正式入口真实跑通轻量测试。
```

Skill 会按固定优先级判断：人类显式要求 → 已有项目兼容 → AI 根据复杂度选择。已有项目不会因为新默认而自动补 targets、renv 或迁移目录。

## simple 与 complex

| 模式 | 适用场景 | 固定要求 | 不创建 |
| --- | --- | --- | --- |
| `simple` | 线性、低成本、整体重跑可接受的小分析/单报告 | renv、明确 R/Rmd 入口、真实轻量测试 | `_targets.R`、`_targets/`、自制调度器 |
| `complex` | 非线性依赖、昂贵步骤、多下游复用、局部失效、恢复、血缘或并行 | simple 全部要求 + targets | 第二套 runner |

代码行数和脚本数量不能单独决定模式。simple 后续出现实质复杂信号时升级到 complex；complex 不会因为当前数据量小而自动降级。

示例：

```text
# simple
在空目录创建一个低成本描述性报告。请使用 simple + renv，不创建 _targets.R；
用 synthetic_fixture 真实 render Rmd，并检查 raw/ 与正式输出未被测试污染。

# complex
建立清洗、模型、评估和报告四阶段流程。模型耗时且被多个报告复用；
请使用 complex + targets + renv，并用 project_subset 在 tmp/tests/<run-id>/_targets 中跑同一 target 图。

# existing
维护这个已有 R 项目。它只有旧 runner 和 tmp 产品；保留现有入口，不补 targets/renv，
只修复统计错误并说明复现性风险。
```

## 两种轻量测试

每个新建或实质修改的分析流都必须真实执行：

- `synthetic_fixture`：无授权真实数据、数据敏感或过大时使用；保留 schema、类型、主键、关键分组、缺失和边缘条件，固定随机种子。
- `project_subset`：有授权数据和现有代码时优先；使用确定、代表性的小子集覆盖关键分组、结局、缺失和异常，不能无理由只取 `head(n)`。

测试代码位于 `scripts/tests/`；每次运行建立唯一 `tmp/tests/<run-id>/`，容纳隔离输入、products/reports、日志、临时报告和 complex test store。simple 调用正式 R/Rmd 入口；complex 调用同一 `_targets.R`，store 为 `<run-id>/_targets`。checker、语法检查和 `--dry-run` 只是预检，不能写成“测试通过”。

失败时按环境/依赖、fixture/子集、路径隔离、分析代码、科学断言、报告渲染、外部服务分类，最小修正后重跑真实链。真实子集默认在断言后删除。运行记录绑定代码、配置和 lockfile 身份，并分别报告 `preflight`、`lightweight_execution`、`full_data_execution`；没跑全量时最后一项必须为 `NOT_RUN`。

已有项目实质修改后仍沿用原入口做可隔离的轻量试跑，但不会为测试补建新版 targets/renv/目录。无法隔离硬编码路径或覆盖副作用时，明确记录阻塞或风险。

## 新项目布局

按需创建，不预建空目录：

```text
项目根目录/
├── 00.Environment.R
├── AA.BB.CC. 名称.R / _functions.R / .Rmd / .html
├── raw/                         # 只读
├── products/                    # 正式派生产品，默认路径
├── reports/                    # 正式图、表、补充材料
├── templates/                  # 仅样式/渲染资产
├── scripts/
│   ├── operations/
│   ├── lib/checkpoint_helpers.R
│   └── tests/
├── tmp/tests/<run-id>/         # 每次测试的隔离现场，默认忽略
├── tmp/scratch/                # 可丢弃探索
├── renv.lock
├── renv/activate.R
├── _targets.R                  # 仅 complex
└── _targets/                   # 仅 complex 正式 store
```

`products/` 是可恢复、可审查、供下游复用的正式产品，不是可随意删除的技术缓存。需要更换路径时只设置一次 `BENSZ_PRODUCTS_DIR`；路径必须留在项目内，且不能与 `raw/`、`reports/`、`tmp/`、`_targets/` 或 `.bensz-api/` 重叠。

## R 与 Rmd 如何分工

- `.R`：读取 raw/上游产品，完成重型计算，保存未经展示阈值筛选的完整结果。
- `_functions.R`：当前分析单元或项目 helper，不是执行节点。
- `.Rmd`：读取产品，应用 Top N、阈值、配色等展示参数，生成图表、表格和解读。
- `00.Environment.R`：集中包加载、项目根、产品路径和跨单元配置。

只改 q cutoff、Top N 或配色时，应复用完整产品，不重算重型计算。

## 模板入口

| 模板 | 用途 |
| --- | --- |
| [Rmd_simple_template.Rmd](templates/Rmd_simple_template.Rmd) | simple 单报告起点 |
| [_targets.R](templates/_targets.R) | complex targets 起点 |
| [analysis_plan_template.yaml](templates/analysis_plan_template.yaml) | 复杂需求、依赖、产品与报告映射 |
| [00.Environment.R](templates/00.Environment.R) | 项目级单一环境/路径入口 |
| [R_data_template.R](templates/R_data_template.R) | 编号计算单元 |
| [Rmd_template.Rmd](templates/Rmd_template.Rmd) | 从正式产品读取的报告单元 |
| [checkpoint_helpers.R](templates/checkpoint_helpers.R) | 复制到项目 `scripts/lib/` 的产品 helper |
| [templates/tests](templates/tests) | 两种数据风格与 simple/complex smoke test |

Skill 内部用 `templates/` 托管脚手架；复制到项目后，只有 CSS/HTML/主题等样式资产留在项目 `templates/`。

## 检查与运行

```bash
# simple
python3 <skill-root>/scripts/check_targets_renv.py <project> --project-state new --workflow-mode simple
Rscript -e 'renv::status()'
Rscript <project>/scripts/tests/smoke_test.R

# complex
python3 <skill-root>/scripts/check_targets_renv.py <project> --project-state new --workflow-mode complex
Rscript -e 'renv::status()'
Rscript <project>/scripts/tests/smoke_test.R
Rscript -e 'targets::tar_make()'

# existing（只读检查）
python3 <skill-root>/scripts/check_targets_renv.py <project> --project-state existing --workflow-mode preserved-existing
```

旧 `--mode auto|new|existing` 仍可使用，含义不变，只是 `--project-state` 的兼容别名。历史 `run_analysis_workflow.py` 只服务已经采用它的旧项目。

所有 Rmd 还需运行图表/表格解读覆盖、解读质量、htmlwidget 可见性和图表可读性检查。正式静态图输出 PDF，JPG 只作为任务工作区内的视觉自检预览。

## R 包与函数资源

`luckyBase` 是唯一固定 Bensz 生态依赖；其它分析包由项目声明并写入 `renv.lock`。包加载集中在 `00.Environment.R`：

```r
luckyBase::Plus.library("ggplot2")
luckyBase::Plus.library("yaml")
```

基因 ID 转换使用 `luckyBase::convert()`。用户自定义函数只按明确路径或已加载对象使用，不猜路径、不扫描磁盘。

## 常见问题

### 单报告必须使用 targets 吗？

不必须。新建低成本单报告默认 simple：使用 renv 和真实 Rmd smoke test，但不创建 targets。只有复杂信号或人类明确指定时才使用 complex。

### 已有项目缺少 targets 或 renv 会怎样？

统一记录为 `workflow_mode: preserved-existing`，保持缺失状态并披露风险，不自动补建。显式迁移时才建立路径映射、校验新旧结果并保留回退入口。

### RDS 不方便人工审查怎么办？

保留 RDS 作为完整主对象，同时提供全量矩形表；体量过大时提供 schema、列级统计、结构摘要和有限预览。

### 缓存损坏怎么办？

缺少 `SUCCESS`、元数据不可读、identity 不同或输出摘要不一致都视为 miss；重算当前单元及必要下游，不手工补标记。

## 更多文档

- [项目状态与工作流模式](references/workflow_modes.md)
- [轻量测试协议](references/lightweight_testing.md)
- [双模式架构](references/hybrid_architecture_guide.md)
- [缓存与恢复契约](references/analysis_workflow_cache.md)
- [工作流检查清单](references/workflow_checklist.md)
- [交付验证记录](references/delivery_verification.md)
- [CHANGELOG](CHANGELOG.md)

## WHICHMODEL - 模型选择建议

普通 simple 报告可使用具备可靠代码编辑与文件操作能力的主流模型；涉及 complex 依赖、复杂统计、缓存失效设计或跨文件审查时，优先选择推理与长上下文能力更强的模型。模型选择不能替代确定性检查、真实 R 执行、职责审查和人工确认科学结论。
