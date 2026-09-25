# 工作流检查清单

## 状态、模式与环境

- [ ] 已分开记录 `project_state` 与 `workflow_mode`，并说明选择理由。
- [ ] 人类显式模式优先；existing 未被按新默认重构。
- [ ] 新 simple 有 renv 和测试入口，无 `_targets.R`；新 complex 额外有 `_targets.R`、`R/`，且 Rmd 消费 target。
- [ ] 已有项目未因检查新增 targets、renv、目录或 runner。
- [ ] 目标、输入、授权、数据字典、统计边界、报告用途和重跑成本已确认。
- [ ] 论文级主要/关键次要估计对象在计算前逐项记录目标人群、分析单位、对比、效应尺度、设计、推断目的、CI/检验可用性及方法理由；预注册方案优先。

## 目录与产品

- [ ] `raw/` 只读；正式派生产品与 targets store 没有混淆。
- [ ] `templates/` 只有样式/渲染资产；新 pipeline 不复制 checkpoint helper。
- [ ] 测试代码在 `scripts/tests/`；每次运行现场在唯一 `tmp/tests/<run-id>/` 并默认忽略。
- [ ] products 路径来自一个项目设置，留在授权项目范围内，无散落硬编码。
- [ ] `tmp/scratch/` 的正式发现已晋升到代码、产品和报告并补测试。
- [ ] 只创建实际使用的目录；旧 `tmp/` 项目未自动迁移或覆盖。

## 轻量测试

- [ ] 明确选择 `synthetic_fixture` 或 `project_subset`，并记录理由。
- [ ] fixture/子集覆盖 schema、类型、主键、关键分组、缺失和边缘条件。
- [ ] simple 真实执行正式 R/Rmd 入口；complex 真实执行同一 target 图。
- [ ] complex test store 是 `tmp/tests/<run-id>/_targets`，未接触正式 `_targets/`。
- [ ] 未向业务逻辑加入 `analysis_mode`/`test_mode` 分支。
- [ ] 输入、主键/分组、统计不变量、产品、报告/图表与 raw 不变性断言通过。
- [ ] 每次尝试有命令、退出状态、失败分类、修正、断言和剩余风险。
- [ ] 运行记录绑定最新 subject identity，并区分 preflight/lightweight/full-data；未跑全量时明确 `NOT_RUN`。
- [ ] project subset 已默认删除，或有明确保留授权与访问控制。
- [ ] 审查后若代码、配置或 lockfile 改变，受影响轻量真实链已重跑。

## targets、审查与报告

- [ ] 完整结果未按显著性筛掉参数；关键项可追溯到估计值、单位/尺度、有效 N/事件数、方法、CI 界限/水平、适用的 p/q、数据与代码来源。
- [ ] `not_applicable`、`not_estimable`、`not_run` 分别写明理由；受设计或数据限制时给替代分析和结论边界，不造区间或显著性结论。
- [ ] 逐项复核 CI/p 是否来自一致的设计、样本与参数；配对/聚类/删失/权重/缺失、模型诊断和多重比较已按实际情况处理。
- [ ] 报告的关键结论与计算结果逐项相符；静态文本检查只作启发式预检。
- [ ] `_targets/` 由 targets 管理；`products/` 只保存需要审阅、复用或交付的科学对象。
- [ ] 中断后再次 `tar_make()` 跳过仍有效前序 target；store/输入/代码/参数变化会正确失效。
- [ ] Rmd 通过 `tar_read()`/`tar_load()` 消费结果，不从 raw/ 重做昂贵计算。
- [ ] 三项只读审查按序完成，或明确记录非独立降级。
- [ ] PDF/JPG、HTML widget、图表/表格解读覆盖、数字追溯均通过。

## 交付命令

```bash
# simple
python3 <skill-root>/scripts/check_targets_renv.py <项目根> --project-state new --workflow-mode simple
Rscript -e 'renv::status()'
Rscript <项目根>/scripts/tests/smoke_test.R

# complex/pipeline：smoke_test 内部使用 tmp/tests/<run-id>/_targets
python3 <skill-root>/scripts/check_targets_renv.py <项目根> --project-state new --workflow-mode complex
python3 <skill-root>/scripts/check_pipeline_contract.py <项目根>
Rscript -e 'renv::status()'
Rscript <项目根>/scripts/tests/smoke_test.R
Rscript -e 'targets::tar_make()'

# existing（有 _targets.R 时 auto 解析为 complex，否则 simple）
python3 <skill-root>/scripts/check_targets_renv.py <项目根> --project-state existing --workflow-mode auto
```

所有 Rmd 继续执行解读覆盖、解读质量、widget 可见性和图表可读性检查。checker/`--dry-run` 不替代上面的真实轻量运行。
