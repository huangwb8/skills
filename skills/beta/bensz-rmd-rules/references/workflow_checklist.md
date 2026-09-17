# 工作流检查清单

## 规划

- [ ] 目标、输入、数据字典、统计边界、报告用途和重跑成本已确认。
- [ ] 每项需求映射到分析单元或明确排除。
- [ ] 单元使用 `AA.BB.CC. 名称`，无重复、前向依赖或循环。
- [ ] 简单任务未被强拆；昂贵/复用/高风险边界已评估缓存。

## 目录与实现

- [ ] `00.Environment.R` 默认唯一，未吸收单元专属逻辑。
- [ ] `raw/` 只读；完整产品在 `products/`；正式材料在 `reports/`。
- [ ] `_functions.R` 未被视为执行节点；Rmd/HTML 留在根目录。
- [ ] 旧 `tmp/` 项目未被自动迁移或覆盖。
- [ ] 包经 `luckyBase::Plus.library()` 管理；基因 ID 转换使用 `luckyBase::convert()`。

## 缓存与恢复

- [ ] identity 覆盖输入、参数、代码、上游和输出契约，不含时间戳。
- [ ] 完整对象、可读副本/摘要、`metadata.yaml`、`SUCCESS` 职责齐全。
- [ ] `SUCCESS` 最后写；半成品、损坏输出和身份变化均为 miss。
- [ ] 首次运行、相同输入命中、参数/代码/上游失效、中途失败和恢复已测试。
- [ ] 只改报告阈值/配色不会重算重型产品。

## 审查与报告

- [ ] 三轮独立只读审查按序完成，或明确记录能力降级。
- [ ] 每轮读取前轮修正后的最新版本，只有主 Agent 修改文件。
- [ ] 图表 PDF、JPG 预览、HTML widget、图表/表格解读覆盖均通过。
- [ ] 不常用指标首次解释，关键数字可追溯，结论未越过不确定性边界。

## 交付命令

多阶段编号计算流：

```bash
python3 <skill-root>/scripts/check_analysis_workflow.py <项目根> --plan analysis-plan.yaml --strict
python3 <skill-root>/scripts/run_analysis_workflow.py <项目根> --dry-run
python3 <skill-root>/scripts/check_rmd_template_yaml.py
```

旧 `tmp/` 项目：`python3 <skill-root>/scripts/check_analysis_workflow.py <项目根> --legacy --strict`，不补 plan、不调用 runner。简单单报告跳过工作流/runner 检查。所有 Rmd 继续执行：

```bash
python3 <skill-root>/scripts/check_figure_table_interpretation.py <报告.Rmd> --strict
python3 <skill-root>/scripts/check_interpretation_quality.py <报告.Rmd> --strict
python3 <skill-root>/scripts/check_htmlwidget_visibility.py <报告.Rmd>
Rscript <skill-root>/scripts/check_plot_readability.R <正式图.pdf> --render-jpg --out-dir <任务根>/bensz-rmd-rules/output/plot-check
```
