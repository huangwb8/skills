# bensz-rmd-rules

面向 **R 数据分析、R Markdown 报告、可复现 targets 流程、论文级图表与证据解读** 的 Agent Skill。当前版本以 [`config.yaml`](config.yaml) 中的 `skill_info.version` 为准；本目录属于 beta 候选源。

## 什么时候使用

使用场景：从原始数据完成整理、统计/模型、图表、Rmd/HTML、科学产品和结果解释，或维护已有 R/Rmd 项目。

不要用于：主要交付物是跨项目复用的 R 函数、类、稳定 API 或 Package（改用 `bensz-r-developer`）；仅渲染既有 Rmd（改用 `knit-rmd-html`）；其它语言的数据分析。

## 最短用法

```text
请用 bensz-rmd-rules 完成这个 R 分析。先只读判断项目是 new 还是 existing，再说明选择 simple 或 targets-first complex/pipeline 的理由。使用 renv，并在正式运行前从正式入口真实跑通 synthetic_fixture 或 project_subset 轻量测试。
```

Skill 会保留已有项目的现状：不因默认策略自动创建 targets/renv 或迁移目录；有 `_targets.R` 的项目按 complex 维护，无 targets（含历史编号脚本）的项目按 simple 语义维护。

## 工作流模式

| 模式 | 适用场景 | 固定要求 |
| --- | --- | --- |
| `simple` | 线性、低成本、整体重跑可接受 | `renv`、明确 R/Rmd 入口、真实轻量测试；不创建 targets |
| `complex`（说明性别名 `pipeline`） | 非线性依赖、昂贵步骤、多下游复用、局部失效、恢复或并行 | `_targets.R` 唯一 DAG、`R/` 计算函数、Rmd 消费 target、隔离 store 恢复验收 |

`new`/`existing` 是项目状态而不是第三种模式：已有 `_targets.R` 按 complex，否则按 simple。迁移必须由人类明确授权。

complex 的核心关系：

```text
renv.lock → _targets.R → R/ functions → target results → Rmd → reports/
                         ↘ optional products/
                         ↘ _targets/ (machine state)
```

`_targets/` 只存机器计算状态；`products/` 只存需要审阅、复用或交付的科学对象，不实现第二套缓存、`SUCCESS`、identity hash 或恢复 runner。

## 推荐项目布局

```text
项目根目录/
├── 00.Environment.R
├── R/                         # target 调用的计算函数
├── _targets.R                 # complex 的唯一 DAG 入口
├── raw/                       # 只读
├── products/                  # 可选科学产物
├── reports/                   # 图、表、HTML、补充材料
├── scripts/tests/             # 可版本化测试代码
├── tmp/tests/<run-id>/        # 隔离测试现场
├── renv.lock
└── renv/activate.R
```

模板 [`_targets.R`](templates/_targets.R) 使用 `tar_source("R")`；[`R_data_template.R`](templates/R_data_template.R) 提供数据处理起点；[`Rmd_template.Rmd`](templates/Rmd_template.Rmd) 通过 `targets::tar_read()` 消费 `analysis_results`；simple 可从 [`Rmd_simple_template.Rmd`](templates/Rmd_simple_template.Rmd) 开始。

## 统计推断完整性

论文级分析在计算前列出主要及影响结论的次要估计对象，确认目标人群、观察单位、对比、设计和推断目的。方法允许时，完整结果保留估计值与单位、有效 N/事件数、适当的默认 95% CI；只有零假设明确时才报告 p 值，批量检验同时说明校正方法及 q/调整后 p。预注册方案另定置信水平时按方案执行。报告引用计算结果并解释效应的实际意义和局限。固定常数或纯描述结果可标 `not_applicable`；数据或设计无法支持推断时标 `not_estimable` 并说明原因与替代分析；未运行标 `not_run`。不凭空补 CI/p，也不以文本关键词检查代替方法复核。详见 [`statistical_inference_protocol.md`](references/statistical_inference_protocol.md)。

## 轻量测试与恢复

新建或实质修改的流程必须真实运行一种测试：

- `synthetic_fixture`：无授权真实数据、数据敏感或数据过大时，保留 schema、类型、主键、分组、缺失和边缘条件，并固定随机种子。
- `project_subset`：有授权数据和现有代码时使用代表性子集，覆盖关键分组/结局/缺失/异常；不能只用 `head(n)`。

测试代码放 `scripts/tests/`，每次使用唯一 `tmp/tests/<run-id>/`。simple 调用正式入口；complex 执行同一 DAG，但 store 放在 `<run-id>/_targets`，不能污染正式 `_targets/`、`products/` 或 `reports/`。至少断言输入契约、关键类型/主键、重要数值不变量、产品/报告生成及 `raw/` 无写入。未跑全量时记录 `full_data_execution=NOT_RUN`。

恢复验收：先让昂贵 target 成功，再中断后续 target；在输入、代码、参数和 renv 身份不变时再次 `tar_make()`，用 `tar_meta()`、outdated 集合和执行记录证明有效前序 target 被跳过。

## 检查与脚本入口

先检查项目状态和模式：

```bash
python3 <skill-root>/scripts/check_targets_renv.py <project> --project-state auto --workflow-mode auto
```

常用检查：

```bash
python3 <skill-root>/scripts/check_pipeline_contract.py <project>
python3 <skill-root>/scripts/check_interpretation_quality.py <project>/report.Rmd
python3 <skill-root>/scripts/check_figure_table_interpretation.py <project>/report.Rmd
python3 <skill-root>/scripts/check_htmlwidget_visibility.py <project>/report.Rmd
python3 <skill-root>/scripts/check_rmd_template_yaml.py <project>/report.Rmd
Rscript <project>/scripts/tests/smoke_test.R
```

图表可读性检查器为 [`check_plot_readability.R`](scripts/check_plot_readability.R)，路径安全检查器为 [`validate_paths.R`](scripts/validate_paths.R)。Liquid Glass 主题可用 [`bootstrap_liquid_glass.py`](scripts/bootstrap_liquid_glass.py) 初始化；桌面动态目录会立即扩展可交互区域，避免鼠标移入时收回。HTML 渲染交给 `knit-rmd-html`。

## 图表与解读规范

默认图表语言为英文；中文期刊等场景通过 YAML `params.plot_language` 切换。每个可见图/表附近说明当前对象、方向/对比、可追溯数值、量级、不确定性和后续验证（方法 + 输入 + 判据）。参考：

- [`four_tier_interpretation_framework.md`](references/four_tier_interpretation_framework.md)：四层解读与 Fail Fast Gate。
- [`interpretation_templates.md`](references/interpretation_templates.md)：单因素、多因素和模型验证骨架。
- [`plot_quality_standards.md`](references/plot_quality_standards.md)：Nature 级图表可读性。
- [`liquid_glass_theme_guide.md`](references/liquid_glass_theme_guide.md)：HTML 主题与故障排查。

## 相关模板与参考

- 环境与依赖：[`00.Environment.R`](templates/00.Environment.R)、[`renv/activate.R`](templates/renv/activate.R)。
- 测试：[`templates/tests/`](templates/tests/)、[`lightweight_testing.md`](references/lightweight_testing.md)。
- 模式与架构：[`workflow_modes.md`](references/workflow_modes.md)、[`hybrid_architecture_guide.md`](references/hybrid_architecture_guide.md)。
- 交付与审查：[`delivery_verification.md`](references/delivery_verification.md)、[`serial_review_protocol.md`](references/serial_review_protocol.md)。

## FAQ 与边界

**可以把编号脚本自动迁移成 targets 吗？** 不可以。已有无 targets 项目按 simple 维护；迁移前需人类明确授权、映射、结果校验和回退方式。

**可以用自制 checkpoint 或 `SUCCESS` 文件吗？** 不可以。complex 使用 targets 的 metadata、失效和增量重建；不引入第二套缓存/恢复协议。

**轻量测试通过是否等于全量通过？** 不是。必须分别报告 `preflight`、`lightweight_execution` 和 `full_data_execution`；未运行全量写 `NOT_RUN`。

**需要通用 R 函数怎么办？** 由 `bensz-r-developer` 实现，本 Skill 负责分析需求、接入和流程证据。

## 许可证与贡献

仓库许可证见项目根目录的 `LICENSE`。修改 Skill 时请同步 `SKILL.md`、`config.yaml`、必要 references 和变更记录，并运行与风险匹配的检查；不要在 `raw/` 或 README 中写入凭据、隐私数据或私有提示词。
