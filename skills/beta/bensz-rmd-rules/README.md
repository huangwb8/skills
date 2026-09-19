# bensz-rmd-rules

为 R 与 R Markdown 数据分析提供“先规划、再计算、可恢复、可审查”的工作流。它把复杂任务拆成编号分析单元，只缓存值得保留的科学数据产品，并让报告阈值、配色和解读迭代不重复昂贵计算。

版本号以 [config.yaml](config.yaml) 的 `skill_info.version` 为唯一来源。新项目统一采用 `targets + renv`；已有项目按现状兼容，不自动迁移。

## 什么时候使用

适合：

- 新建或维护 R Markdown 分析、R 数据脚本和可复现报告；
- 多阶段、昂贵或容易中断的分析，需要缓存命中、局部失效和断点恢复；
- 需要 Nature 级图表、弱背景读者的指标导读、数字追溯和专家解读；
- 需要在 macOS、Linux、Windows 间保持相对路径与输出一致。

不适合：仅把已有 Rmd 渲染为 HTML（使用 `knit-rmd-html`）、其它语言的数据分析，或只做图片格式转换。

## 最短用法

```text
请使用 bensz-rmd-rules 分析 raw/clinical.tsv。先给出最小分析单元表，
再生成描述性统计和生存分析；原始数据只读，正式图表写入 reports/，
昂贵结果应支持缓存命中和中途恢复。
```

Skill 会先只读盘点项目状态。空目录或明确新建的项目必须初始化 `targets + renv`，单步骤也保留一个 target；已有项目的 targets 与 renv 独立维护，缺失机制不自动补齐。

## 进阶 Prompt

### 多阶段昂贵分析

```text
请使用 bensz-rmd-rules 处理 raw/ 下的表达矩阵和临床表。
要求先生成 analysis-plan.yaml，依次完成样本清洗、特征计算、模型拟合和综合报告。
特征计算与模型需要 checkpoint；相同输入重跑应命中缓存，修改模型参数只失效模型及必要下游。
首次真实计算前完成结构数据流、R 实现恢复、科学统计三轮串行只读审查。
```

### 只调整报告

```text
现有 products/ 已完成。请只修改 03.00.00. 综合报告.Rmd 的 q_cutoff、Top N 和配色，
重新渲染同名 HTML，不重跑上游计算，并验证图表/表格解读与数字追溯。
```

### 维护旧项目

```text
这是仍使用 tmp/cohort_analysis/ 的旧项目。请用 bensz-rmd-rules 增量修复 Rmd，
保留现有目录和文件名，不迁移到 products/，列出兼容性风险。
```

## 新项目布局

```text
项目根目录/
├── 00.Environment.R
├── _targets.R
├── renv.lock
├── renv/activate.R
├── analysis-plan.yaml              # 需求/产品契约，可选
├── 01.00.00. 数据整理.R
├── 01.00.00. 数据整理_functions.R   # 按需
├── 02.00.00. 结果报告.Rmd
├── 02.00.00. 结果报告.html
├── templates/checkpoint_helpers.R   # 需要产品 checkpoint 时复制
├── raw/                              # 原始输入，只读
├── products/main/01.00.00. 数据整理/
│   ├── main.rds
│   ├── preview.tsv                   # 按对象类型选择
│   ├── summary.md
│   ├── metadata.yaml
│   └── SUCCESS
└── reports/
    ├── figures/
    ├── tables/
    └── supplementary/                # 按需
```

`AA.BB.CC. 名称` 同时标识代码、产品和报告。数字元组升序是默认执行顺序；上游必须早于下游；`_functions.R` 不是独立步骤。四类 R/Rmd/HTML 文件均按需创建，不要求每个单元凑齐。

## R 与 Rmd 如何分工

| 层 | 负责 | 典型变化 |
| --- | --- | --- |
| 编号 `.R` | 原始/上游产品读取、完整计算、模型、可恢复产品 | 输入、科学参数、算法、代码变化 |
| 编号 `.Rmd` | 报告筛选、Top N、配色、图表、表格和解读 | q 阈值、展示数量、视觉与叙事变化 |

只改报告阈值或配色时，应复用 `products/`，不重跑重型计算。正式静态图写入 `reports/figures/`，同名 HTML 留在项目根目录。

## 缓存为什么可信

缓存命中不靠“文件存在”，而要求：

- 输入、当前参数、相关代码、上游产品和输出契约共同形成 identity；
- `metadata.yaml` 可解析，声明的输出全部存在且摘要一致；
- 主对象与人类可读摘要/预览完成验证；
- `SUCCESS` 最后写入。

失败步骤不会留下 `SUCCESS`。前序有效产品保留，重跑按编号记录 cache hit，再从失败边界继续。

计算层支持两个可选环境变量：

```bash
python3 <skill-root>/scripts/run_analysis_workflow.py /path/to/project --force-step 01.00.00
python3 <skill-root>/scripts/run_analysis_workflow.py /path/to/project --resume-from 01.00.00
```

这些控制不属于 Rmd YAML；YAML 只保存展示、筛选和解读参数。

## 模板起步

| 模板 | 用途 |
| --- | --- |
| [analysis_plan_template.yaml](templates/analysis_plan_template.yaml) | 需求、依赖、产品和报告映射 |
| [00.Environment.R](templates/00.Environment.R) | 唯一项目环境入口 |
| [Rmd_simple_template.Rmd](templates/Rmd_simple_template.Rmd) | 直接只读 raw 的低成本单报告 |
| [R_data_template.R](templates/R_data_template.R) | 单个编号计算单元 |
| [functions_template.R](templates/functions_template.R) | 同词干单元专用函数 |
| [Rmd_template.Rmd](templates/Rmd_template.Rmd) | 从 products 读取的报告单元 |
| [checkpoint_helpers.R](templates/checkpoint_helpers.R) | 路径、身份、完整性与安全落盘 |

多阶段缓存流必须把 checkpoint helper 复制到项目的 `templates/checkpoint_helpers.R`，它也会进入代码 identity。已有文件只做增量修改；`00.Environment.R` 和 `_functions.R` 不应被模板覆盖。

Liquid Glass 主题与常用 helper 可按需复制：

```bash
python3 <skill-root>/scripts/bootstrap_liquid_glass.py --project-root /path/to/project --with-env --with-extras
```

默认不覆盖现有文件；需要覆盖时必须显式添加 `--force` 并先确认范围。

## 交付前检查

多阶段编号计算流在早期规划使用报告模式：

```bash
python3 <skill-root>/scripts/check_analysis_workflow.py /path/to/project --plan analysis-plan.yaml
```

首次昂贵运行和交付前使用严格模式：

```bash
python3 <skill-root>/scripts/check_analysis_workflow.py /path/to/project --plan analysis-plan.yaml --strict
python3 <skill-root>/scripts/run_analysis_workflow.py /path/to/project --dry-run
```

新项目即使只有一个报告也必须存在 `_targets.R`、`renv.lock` 和 `renv/activate.R`；可用一个 target 表示整个报告。已有项目不因检查而新增这些文件，旧 `tmp/` 项目沿用原运行入口：

```bash
python3 <skill-root>/scripts/check_targets_renv.py /path/to/legacy-project --mode existing
python3 <skill-root>/scripts/check_analysis_workflow.py /path/to/legacy-project --legacy --strict
```

所有 Rmd 报告继续执行：

```bash
python3 <skill-root>/scripts/check_figure_table_interpretation.py path/to/report.Rmd --strict
python3 <skill-root>/scripts/check_interpretation_quality.py path/to/report.Rmd --strict
python3 <skill-root>/scripts/check_htmlwidget_visibility.py path/to/report.Rmd
Rscript <skill-root>/scripts/check_plot_readability.R path/to/figure.pdf --render-jpg --out-dir <task-root>/bensz-rmd-rules/output/plot-check
```

维护本 Skill 模板时再运行：

```bash
python3 <skill-root>/scripts/check_rmd_template_yaml.py
```

## 图表与解读

- 静态正式图默认保存矢量 PDF；JPG 只用于视觉自检。
- 默认英文图表；中文期刊等场景通过 `params.plot_language` 显式切换。
- 逐图检查裁切、字体、线点、图例、密度、对比度和色盲友好性。
- 每个可见图/表附近必须有绑定当前对象和数值的解读。
- 不常用或自定义指标先提供指标导读，首次完整解释，后续不重复教学。
- 允许 `` `r ...` `` 动态嵌入数字，不允许代码拼接解释段落。

## R 包与函数资源

`luckyBase` 是唯一固定 Bensz 生态依赖。具体分析包由项目声明并写入 `renv.lock`，不会由 Skill 预装个人化包。包加载集中在 `00.Environment.R` 并使用：

```r
luckyBase::Plus.library("ggplot2")
luckyBase::Plus.library("yaml")
```

涉及基因 ID 转换时使用 `luckyBase::convert()`。用户已有的自定义函数只能按明确路径或已加载对象使用；Skill 不猜路径、不扫描磁盘。

## 与相邻 Skill 的区别

| 需求 | 入口 |
| --- | --- |
| 设计/开发 R + Rmd 分析 | `bensz-rmd-rules` |
| 只渲染已有 Rmd 为 HTML | `knit-rmd-html` |
| 项目级代码测试或审查 | 对应测试/审查 Skill |
| 修改图片格式 | 图片格式转换 Skill |

## 常见问题

### 单报告项目也必须使用 targets 和 renv 吗？

新项目必须使用。一个 `tar_target()` 就足以表达单报告，产品是否写入 `products/` 仍按实际交付和复用需求决定。已有项目保持原有机制，不因 Skill 更新自动补齐。

### 可以把 Rmd 和 HTML 放进 reports 吗？

不可以。编号 Rmd 与同名 HTML 位于项目根目录；`reports/` 只保存正式图、表和补充材料。

### RDS 不方便人工审查怎么办？

保留 RDS 作为完整主对象，同时提供全量矩形表，或在体量很大时提供 schema、列级统计、结构摘要和有限预览。

### 能自动迁移旧项目或补齐缺失机制吗？

不会。已有项目按 targets 与 renv 各自的实际状态维护；只有明确要求迁移时，才建立映射、校验新旧结果并保留原路径。旧 runner 只服务已有项目，不是新 targets 项目的回退入口。

### 宿主没有子 Agent 怎么办？

Skill 会披露降级并做三轮职责分离的顺序自检，但不会把它写成“独立审查”。若用户明确要求真实多 Agent 或任务高风险，应在正式运行前停止。

### 缓存损坏怎么办？

缺少 `SUCCESS`、元数据无法解析、identity 不同或任一输出摘要不一致都视为 cache miss；重算当前单元及必要下游，不手工补标记。

## 更多文档

- [多分析单元架构](references/hybrid_architecture_guide.md)
- [多分析单元示例](references/hybrid_architecture_examples.md)
- [缓存与恢复契约](references/analysis_workflow_cache.md)
- [三轮串行审查](references/serial_review_protocol.md)
- [工作流检查清单](references/workflow_checklist.md)
- [交付验证记录](references/delivery_verification.md)
- [图表质量](references/plot_quality_standards.md)
- [指标解释协议](references/metric_explanation_protocol.md)
- [专家讨论写作参考](references/expert_discussion_template.md)
- [CHANGELOG](CHANGELOG.md)

## WHICHMODEL - 模型选择建议

普通单报告开发可使用具备可靠代码编辑与文件操作能力的主流模型；涉及多阶段依赖、复杂统计、缓存失效设计或跨文件审查时，优先选择推理与长上下文能力更强的模型。模型选择不能替代确定性检查、真实 R 运行、三轮职责审查和人工确认科学结论。
