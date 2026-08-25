# bensz-rmd-rules — R Markdown 开发规范

当前版本：`0.22.0`。专家级解读默认兼顾相关背景较弱的读者：不常用指标先导读、首次详解、后续简写，同时保持论文级准确性与证据可追溯。

本 README 面向**使用者**：如何让 AI 帮你开发高质量的 R Markdown 分析脚本。
执行指令与硬性规范在 [SKILL.md](SKILL.md)；默认参数在 [config.yaml](config.yaml)。

## 用法

### 最推荐：开发完整的生信分析流程

```
写一个 Rmd 分析：分析 TCGA 肺癌数据中 TP53 突变与患者预后的关系
```

AI 将自动：
1. 创建 `.R` 数据脚本（数据加载、清洗、统计检验）
2. 创建 `.Rmd` 主脚本（可视化、专家级解读）
3. 创建 `_functions.R`（分析专用函数）
4. 创建 `00.Environment.R`（环境配置，如已存在则增量添加）

### 结合现有项目：在已有 Rmd 基础上新增分析

```
在 cf01.Rmd 中添加一个新的生存分析：比较 KRAS 突变型与野生型的 OS 差异
```

AI 将：
- 对已有 Rmd 仅做增量修改（不破坏现有代码）
- 在 `cf01_functions.R` 中添加所需函数
- 生成包含四层解读的专业分析（数据描述 + 统计见解 + 领域见解 + 局限与后续）

### 数据预处理 + 可视化分离

```
写一个分析：先预处理表达矩阵（log2 转化、标准化），再做 PCA 和热图可视化
```

AI 将：
- 在 `.R` 脚本中完成**所有预处理**，保存**完整数据**（不应用阈值筛选）
- 在 `.Rmd` 中加载完整数据，根据业务需求应用**阈值筛选**（如表达量过滤、p值截断）
- 阈值参数仅在 `.Rmd` 的 YAML `params` 中定义，便于调整而无需重跑 `.R`

### 快速迭代可视化（postprocess-only 模式）

```
我已经跑过 cf01.R 了，现在想调整热图的阈值和配色，别重新跑计算
```

AI 将：
- 在 `.Rmd` 中设置 `params$dv_mut_mode = "postprocess"` 启用快速模式
- 直接加载已有的 `.R` 输出文件，跳过耗时计算
- 仅应用新的阈值筛选和可视化调整

## 核心特性

| 特性 | 说明 | 好处 |
|------|------|------|
| **混合架构** | `.R` 负责重型计算，`.Rmd` 负责可视化与解读 | 计算一次，快速迭代可视化 |
| **数据筛选分离** | `.R` 保留完整数据，`.Rmd` 应用业务阈值 | 方便审查原始状态，确保分析科学价值 |
| **阈值参数灵活配置** | 阈值仅在 `.Rmd` 的 `params` 中定义 | 调整阈值无需重跑耗时计算 |
| **快速后处理模式** | 支持仅加载已有输出，跳过计算 | 快速迭代可视化和筛选策略 |
| **出版级图表默认值** | 图表默认按 Nature 级别可读性生成（PDF 矢量优先、色盲友好配色、主题统一） | 直接满足高水平投稿的可视化门槛 |
| **PDF 交付 + 预览自检** | 每张图以矢量 PDF 作为正式交付，并自动生成 JPG 预览用于视觉自检（可覆写 run 目录与 DPI） | 避免裁切/溢出/字体过小等“渲染后才暴露”的问题 |
| **现有资源优先** | 优先使用 lucky/ccs/GSClassifier 等已有 R 包 | 避免重复造轮子，代码更简洁 |
| **跨平台兼容** | 使用相对路径，macOS/Linux/Windows 通用 | 团队协作无缝切换 |
| **关键函数与参数可追溯** | 在“数据概览”后提供“关键函数、参数与源代码位置”章节 | 审查/复盘时可快速定位实现与关键决策 |
| **专家级解读** | 四层解读 + 指标导读 + 不常用指标首次解释 + 证据锚定 | 小白能跟上，资深读者仍可复核证据与边界 |
| **专家级讨论模板** | 提供基于真实项目的深度讨论模板 | 有理有据、有启发性、可操作的讨论 |
| **不过度保护** | 信任用户环境，避免冗余检查 | 代码简洁可读 |

### 四层解读框架

本技能确保 AI 生成的是**资深专家级别**的结果解读，而非简单的统计罗列：
并且以“证据锚定 + 反套话”为核心（关键判断必须能指向本次结果中的具体数值/排序/对比）。

本 skill 采用“两阶段门禁”思路：

- **探索/写作阶段**：允许低密度解读（先产出结果，再逐步加深）；门禁以“提示”为主
- **交付/收敛阶段**：Fail Fast 门禁以“可追溯 + 不漏项”为主

交付阶段硬门槛：

- **数字可追溯**：关键数字优先用 `` `r ...` `` 内联（避免硬写不可追溯数字）
- **覆盖不漏项**：有图/表输出就必须有附近 prose 解读（Fail Fast）
- **禁止代码生成解释文本**：允许代码生成数字，不允许代码拼接解释段落

“四层框架 / Top 信号 / 不确定性提示 / 可执行后续”保留为**推荐结构**（适用于关键输出与终稿；严格模式下可能作为门禁）。
另外，禁止机械套用“四段式模板”（如“直接观察是…统计含义是…研究者意义是…下一步是…”）或机械输出“数据描述/统计见解/领域见解/局限与后续”四段标签。

写解读前建议先回答四个问题（关键输出/终稿强烈建议）：

1. 如果我是研究者，看到这个结果，我最想确认/反驳的是什么？
2. 这个统计发现如何改变我对机制/分层/风险的理解（只写可证伪推断）？
3. 基于这个结果，我会优先做什么？不做什么？为什么？
4. 如果不复现，最可能的原因是什么（样本量/混杂/批次/模型假设）？

| 层级 | 内容 | 示例 |
|------|------|------|
| **第一层：数据描述** | 输出的基本结构和内容 | "该表包含 700 行，覆盖 28 个癌种与 25 个基因" |
| **第二层：统计见解** | 效应大小、方向、实际意义 | "正值表示突变在 normCCS 高样本中富集，TP53 效应最显著（effect = X.XX, q < 0.001）" |
| **第三层：领域见解** | 机制/流程/决策含义（按分析领域调整） | "本次最强信号集中在 [对象/亚组] 并指向 [通路/机制/动作]；据此提出可检验假设，并给出验证路径（方法 + 输入 + 判据）" |
| **第四层：局限与后续** | 不确定因素、验证建议 | "当前未校正共突变混杂，后续需多因素回归验证" |

补充说明：四层框架是**内容门槛**而非固定写作格式；常规交付时，推荐把四层内涵自然写进 1–2 段连贯叙述，并单独输出 Top 1–3 汇总小表（便于复核）。

### 面向弱背景读者的指标解释

技能默认不假定你熟悉任务特有指标，但也不会把报告写成教科书。它采用“先搭桥，再分析”的方式：

- p 值、q/FDR、95% CI、HR/OR/RR、经典生存分析、ROC AUC、灵敏度和特异度等默认按常用指标处理。
- 自定义评分、组合指数，以及 Brier score、校准斜率、net benefit、NRI/IDI、SHAP 汇总量等窄领域指标，默认按不常用指标处理；无法判断时也按不常用处理。
- 只要存在不常用指标，报告会在分析前给出“指标导读”表，说明尺度、参考点、升降趋势、不确定性、选用理由和判读边界。
- 不常用指标在结果正文第一次出现时，会解释“是什么、如何计算、为什么用、价值在哪里、当前数值如何读”；第二次起只保留简洁的结果解读。
- 同名指标若公式、尺度、方向或时间窗发生变化，会重新解释，避免把不同定义误当成同一个指标。

详细判定与写作协议见 [references/metric_explanation_protocol.md](references/metric_explanation_protocol.md)。

### 避免“结果解读流于表面”（推荐默认策略）

- 若存在多个 cohort/亚组：建议每个 cohort 固定写一个“**核心结论（证据链收敛）**”段落（Top 1–3 + 数值证据 + 证据等级 + 3 条可执行后续）。
- 后续建议必须写成“方法 + 输入 + 判据”，并在正文中同时报告“阈值 + 当前值”（阈值统一来自 YAML `params`）。
- 把“领域见解”写成至少 1 条“如果...那么...”的可证伪推理，避免“提示可能/值得深入探讨/需要进一步研究”等空泛宣言。

渲染/交付前可用静态预检脚本自检（默认读取 `config.yaml`；更严格模式可加 `--strict`）：

探索期（不阻断，只提示）：

```bash
# 覆盖检查：默认仅报告
python3 bensz-rmd-rules/scripts/check_figure_table_interpretation.py your_report.Rmd

# 质量检查：仅提示不阻断
python3 bensz-rmd-rules/scripts/check_interpretation_quality.py your_report.Rmd --warn-only
```

交付期（Fail Fast 门禁）：

```bash
python3 bensz-rmd-rules/scripts/check_figure_table_interpretation.py your_report.Rmd --strict
python3 bensz-rmd-rules/scripts/check_interpretation_quality.py your_report.Rmd
python3 bensz-rmd-rules/scripts/check_interpretation_quality.py your_report.Rmd --strict
```

更详细的“Fail Fast 质量门槛 / 反套话机制 / 结果锚点句式 / 深度模板”见：
- [references/four_tier_interpretation_framework.md](references/four_tier_interpretation_framework.md)
- [references/interpretation_templates.md](references/interpretation_templates.md)
- [references/interpretation_narrative_examples.md](references/interpretation_narrative_examples.md)

## 提示词示例

### 示例 1：基础生存分析

```
写一个生存分析：比较 EGFR 高表达组与低表达组的总生存期差异
```

AI 将生成：
- **数据脚本**（`analysis.R`）：加载表达数据、计算生存曲线
- **主脚本**（`analysis.Rmd`）：KM 曲线图 + Log-rank 检验 + 专家级解读

### 示例 2：差异表达 + 富集分析

```
做生信分析：鉴定肺癌与正常组织的差异基因，然后做 GO 和 KEGG 富集分析
```

AI 将：
- 使用 `lucky::DE_analysis()`（如可用）进行差异表达分析
- 应用表达量阈值和 p 值筛选（在 `.Rmd` 中）
- 生成富集分析可视化并解读生物学意义

### 示例 3：泛癌症分析

```
使用 ccs 包做 Pan-Cancer 分析：比较各癌种的 CCS 分型与预后的关系
```

AI 将：
- 调用 `ccs::classify_cohort()` 进行分型
- 跨癌种生存分析（考虑样本量阈值）
- 解读癌种异质性和临床潜力

### 示例 4：探索性分析（无预设假设）

```
探索这个基因表达数据集：找找有什么有趣的模式或异常
```

AI 将：
- 进行多维度探索（分布、相关性、聚类）
- 对发现提供统计和生物学解读
- 指出局限性和后续验证方向

## 输出文件结构

AI 将在你的项目目录下创建以下文件：

```
项目目录/
├── {主脚本名}.R            # 数据脚本：预处理、计算、保存完整数据
├── {主脚本名}.Rmd          # 主脚本：可视化、阈值筛选、专家级解读
├── {主脚本名}_functions.R  # 函数脚本：当前分析专用函数（增量添加）
├── 00.Environment.R        # 环境脚本：R 包加载（如已存在则增量添加）
├── tmp/{主脚本名}/         # 临时文件夹：中间结果
└── {主脚本名}.html         # 最终输出（使用 knit-rmd-html skill 渲染）
```

### 核心约定

1. **文件命名一致**：`.R`、`.Rmd`、`.html` 除后缀外名称完全相同（如 `cf01.R`, `cf01.Rmd`, `cf01.html`）
2. **数据流向**：`.R` → `tmp/{主脚本名}/` → `.Rmd`
3. **增量操作**：对已有文件（`_functions.R`、`00.Environment.R`、已有 Rmd）仅增量添加，不覆盖

### .R 与 .Rmd 的职责分离

| 组件 | 职责 | 数据状态 |
|------|------|----------|
| **`.R` 数据脚本** | 数据处理、重型计算、特征工程 | **未经阈值筛选的完整数据** |
| **`.Rmd` 主脚本** | 可视化、分析、解读 | **根据业务需求应用阈值筛选** |

**好处**：
- 计算一次，保存结果；后续可灵活调整筛选策略和可视化，无需重复计算
- 方便审查数据最原始的状态
- 确保分析具有科学价值和临床意义

## AI 行为准则

### 做什么

- **优先使用**：lucky、ccs、GSClassifier、candidate_r 等已有资源
- **生成代码**：简洁、人类可读、跨平台兼容
- **结果解读**：四层解读（数据描述 + 统计见解 + 领域见解 + 局限与后续），并强制证据锚定与反套话；默认采用自然标题与论文口吻，关键观点适度加粗；数字必须可追溯且 Rmd 末尾需给出“数字准确性验证”，禁止通过代码生成解释文本
- **可追溯性**：在 `## 数据概览` 之后增加 `## 关键函数、参数与源代码位置`，说明关键分析过程、关键函数、关键参数及设置理由，并标注项目内源代码位置（文件 + 行号）
- **增量修改**：对已有代码只添加新内容，不大幅重写

### 不做什么

- **不重复造轮子**：优先调用已有函数，而非重新实现
- **不过度保护**：不检查 R 包是否已加载（`00.Environment.R` 已统一管理）
- **不破坏用户代码**：用户已有代码块默认保留
- **不做硬编码路径**：始终使用相对路径和 `file.path()`

## R 包资源

AI 将优先使用以下用户开发的 R 包（包加载统一在 `00.Environment.R` 里通过 `luckyBase::Plus.library()` 完成；分析脚本中优先用 `pkg::fn()` 调用，不在各处散落 `library()`）：

说明：本 skill 自带的“自检脚本/环境入口模板”允许使用 `requireNamespace(..., quietly=TRUE)` 做最小依赖边界检查（用于更清晰的报错与可选增强），但用户项目的分析脚本不应复制这种“到处检查/降级”的写法。

| 包名 | 用途 | 典型场景 |
|------|------|----------|
| **ccs** | 泛癌症基因组分类 | 癌症分型、亚型分类 |
| **GSClassifier** | 转录组学综合分类 | 基因签名分类、预测模型 |
| **lucky** | 常规 R 函数集合 | 生存分析、差异表达、可视化 |
| **luckyBase** | lucky 系列基础 | 包管理、基础工具函数 |
| **luckyExperiment** | 生物学实验 | 实验数据处理 |
| **luckyGEO** | GEO 数据系列 | GEO 数据下载、处理 |
| **luckyModel** | 第三方模型 | 模型集成、预测 |

### candidate_r 函数库

当 lucky 系列不满足需求时，AI 将使用 `candidate_r` 函数库：

- **默认行为**：先加载 `00.Environment.R`，如相关函数已存在则直接使用
- **可选路径**：如你在 `00.Environment.R` 中定义了 `candidate_r_path`，AI 将按该路径加载脚本

**推荐做法**：在 `00.Environment.R` 中一次性配置 candidate_r 加载，避免每个 Rmd 都重复指定路径。

## 配置选项

可通过 [config.yaml](config.yaml) 调整：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `rmd_template.yaml_header` | 见 config.yaml | Rmd YAML 头（单一真相来源；模板内会保留一份拷贝用于起手，需与此处保持一致） |
| `file_structure` | 见 config.yaml | 文件命名和结构约定 |
| `output.html_skill` | `"knit-rmd-html"` | HTML 渲染使用的 skill |
| `plot_quality` | 见 config.yaml | 图表质量默认口径（Nature 级别）与支持的绘图包范围 |
| `plot_readability` | 见 config.yaml | 图表可读性硬检查阈值（如 max_ticks/min_font_pt/长标签长度） |

## 模板快速起手

AI 可从本技能的模板快速创建新分析：

- **数据脚本模板**：`templates/R_data_template.R`
- **主脚本模板**：`templates/Rmd_template.Rmd`
- **函数脚本模板**：`templates/functions_template.R`
- **环境脚本模板**：`templates/00.Environment.R`
- **图表配色（Nature）**：`templates/nature_colors.R`
- **图表主题（Nature）**：`templates/nature_theme.R`（`theme_nature()` / `theme_nature_readable()`）
- **ComplexHeatmap 模板**：`templates/complexheatmap_template.R`（`make_heatmap_nature()` / `make_heatmap_nature_safe()`）
- **plotly 模板**：`templates/plotly_template.R`

如需手动创建，可直接复制这些模板到你的项目目录。

## 辅助脚本

- `scripts/check_figure_table_interpretation.py`：图/表“有输出但无解读”的覆盖检查（可用 `--strict` 阻断交付）
- `scripts/check_htmlwidget_visibility.py`：htmlwidget（DT/plotly 等）在 HTML 中是否可见的静态检查（避免“代码在但不渲染”）
- `scripts/check_plot_readability.R`：对导出的 PDF 图表做基础可读性检查（文件存在/大小；可选文本提取）
- `scripts/bootstrap_liquid_glass.py`：把 Liquid Glass 主题资源拷贝到项目（默认不覆盖；`--force` 会覆盖目标文件，建议先在空目录执行）
- `scripts/check_rmd_template_yaml.py`：校验 `templates/Rmd_template.Rmd` 的 YAML header 是否与 `config.yaml:rmd_template.yaml_header` 一致（维护者用）

## 常见问题

### Q：AI 会修改我的已有代码吗？

A：默认**不会**。AI 对已有 Rmd、`_functions.R`、`00.Environment.R` 仅做增量添加（新代码块、新函数），不大幅重写。如需修改，AI 会先询问确认。

### Q：.R 和 .Rmd 的区别是什么？

A：**职责分离设计**：
- **`.R`**：数据处理、重型计算、保存**完整数据**（不应用阈值筛选）
- **`.Rmd`**：加载 `.R` 的完整数据，应用**业务阈值筛选**，专注于可视化和解读

好处：计算一次，保存结果；后续可灵活调整筛选策略和可视化，无需重复计算。

### Q：什么是"专家级解读"？

A：AI 将按**四层框架**解读结果，避免仅有"是什么"的浅层描述：

1. **数据描述**：输出包含什么
2. **统计见解**：统计结果意味着什么
3. **领域见解**：机制/流程/决策价值是什么（按分析领域调整）
4. **局限与后续**：哪些不确定，如何验证

同时默认假定读者对任务特有指标不熟悉：不常用指标会先出现在“指标导读”表中，并在结果正文首次出现时完整解释；后续不再重复，以兼顾易懂与阅读效率。

详细规范与深度模板：
- [references/four_tier_interpretation_framework.md](references/four_tier_interpretation_framework.md)
- [references/metric_explanation_protocol.md](references/metric_explanation_protocol.md)
- [references/interpretation_templates.md](references/interpretation_templates.md)

### Q：如何让 AI 使用我的 candidate_r 脚本？

A：在 `00.Environment.R` 中一次性配置：

```r
# 推荐做法：在 00.Environment.R 中统一加载
candidate_r_path <- "/path/to/candidate_r"
source(file.path(candidate_r_path, "feature_selection.R"))
```

之后所有 Rmd 都可使用这些函数，无需重复指定路径。

### Q：渲染出的 HTML 为什么刷新后缩放/阅读位置会丢失？

A：在某些场景下（尤其是 `file://` 打开本地 HTML 或 IDE 内置预览器），浏览器不一定会记忆“页面级缩放”和滚动位置。为提升阅读体验，本 skill 的 Liquid Glass 模板默认在 `includes.after_body: "templates/liquid_glass_lightbox.html"` 中启用了“视图状态保持”：

- 使用 `Ctrl/Cmd + (+/-/0)` 进行缩放（可在刷新后保持）
- 刷新后尽量恢复刷新前的阅读位置（scroll）

如你希望关闭该行为，可移除 YAML 中的 `includes.after_body`（或改为仅包含 Lightbox 的 after_body 文件）。

### Q：目录（TOC）如何“静态浮动/动态浮动”切换？

A：Liquid Glass 的目录支持两种模式（仅桌面宽屏生效）：

- **动态浮动（默认）**：左上角显示小圆点（`TOC`），鼠标悬停/键盘聚焦后展开，移出后回缩；正文空间最大。
- **静态浮动**：目录常驻显示，正文会为目录预留左侧空间，避免遮挡。

切换方式：在目录面板顶部点击“静态/动态”按钮即可（刷新后仍保持）。

**移动端提示**：手机/窄屏下目录会自动折叠为“顶部 sticky 目录条”，按钮变为“展开/收起”；点击任意目录项跳转后会自动收起，滚动阅读时也能随手再次打开。

### Q：生成的代码能在 Windows 上运行吗？

A：**可以**。AI 使用相对路径和 `file.path()` 自动处理路径分隔符，确保跨平台兼容。

### Q：如何渲染 HTML？

A：使用 `knit-rmd-html` skill：

```
用 knit-rmd-html 渲染 cf01.Rmd
```

AI 将在 Rmd 同级目录生成 `cf01.html`。

### Q：为什么 DT 表格“代码在但 HTML 不出表”？

A：这是 R Markdown/knitr 的常见坑：`DT::datatable()` 这类 **htmlwidget** 必须作为 code chunk 的“可见结果”返回，才能稳定被捕获并渲染到 HTML。最常见的失败写法是：
- 把 widget 包在 `print()` / `invisible()` 里
- widget 输出后又继续执行其它表达式（导致 widget 不是最后一个表达式）
- 一个 chunk 里输出多个 widget，但没有用 `htmltools::tagList(...)` 把它们作为单个返回值

推荐写法：

```r
# 最稳妥：让 widget 成为 chunk 的最后表达式
DT::datatable(head(data, 100))
```

交付前建议（本 skill 强制）运行静态检查脚本：

```bash
# 1) 覆盖检验：防止“有图/表但无解读”
python3 bensz-rmd-rules/scripts/check_figure_table_interpretation.py cf01.Rmd --strict

# 2) 可见性检验：防止“代码在但 HTML 不出表/不出图”
python3 bensz-rmd-rules/scripts/check_htmlwidget_visibility.py cf01.Rmd
```

若 1) 未通过：按报告提示为对应输出块补齐/加强解读后重跑，直到通过。

### Q：为什么 DT（DataTables）表头和表体列会“错位”？

A：高概率是 **主题 CSS 对 `table/th/td` 的全局样式**影响了 DataTables 的列宽计算（尤其是 `scrollX/scrollY` 时，DataTables 可能将表头/表体拆成不同的 `<table>`）。本 skill 已在 `templates/liquid_glass_theme.css` 中做了隔离：将“卡片化 table”样式限制为 `table:not(.dataTable):not(.display)`（兼容 DT 初始化前的 `class="display"`），并把玻璃卡片效果放在 `.dataTables_wrapper` 上。

排查建议：
- 临时禁用 `templates/liquid_glass_theme.css`：若错位消失，基本可锁定为 CSS 冲突。
- 若你复制/修改过旧版主题 CSS：确认仍保留 `table:not(.dataTable):not(.display)` 与 `.dataTables_wrapper table.dataTable/.display` 的兼容规则。

### Q：`00.Environment.R` 会被覆盖吗？

A：**不会**。这是铁律：
- 文件不存在：可从模板初始化
- 文件已存在：仅增量添加函数，严禁覆盖

## 更多文档

- **[SKILL.md](SKILL.md)**：AI 执行指令和硬性规范
- **[config.yaml](config.yaml)**：可配置参数和版本号
- **[CHANGELOG.md](CHANGELOG.md)**：版本变更记录

## 版本

当前版本：**见 [config.yaml](config.yaml)**

主要特性：混合架构 + 数据筛选分离 + 专家级结果解读框架

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic（1/6 = 17%）
- **来源构成**：社区 70%, 官方 20%, 技术博客 10%
- **数据时效**：2024-10 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试 R Markdown 开发准确率

---

### 场景化建议

#### 场景 1：标准 R Markdown 开发（最常见）

**触发条件**：需要开发 R Markdown 分析脚本或 R 数据分析代码

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium-high |
| **预期成本** | ~$0.05-0.30/次 |

**理由**：
- R Markdown 开发需要理解数据分析需求、生成符合规范的代码、编写专家级解读
- Sonnet 在代码生成和文档写作任务中表现出色，能够理解生信学领域知识
- [社区对比](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249) 显示 Sonnet 在复杂场景下的优势
- **R Markdown 开发需要较强的推理和写作能力，Sonnet 的性价比最高**

**避免**：简单代码生成不需要 Opus，用 Sonnet 即可

**来源**：社区对比讨论 + 官方模型选择指南

---

#### 场景 2：复杂生信分析流程

**触发条件**：
- 需要开发复杂的生物信息学分析流程（如多组学整合分析）
- 需要深度理解领域知识并生成专业级解读
- 需要结合多个 R 包进行高级分析

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | high |
| **预期成本** | ~$0.10-0.50/次 |

**理由**：
- Sonnet 在复杂分析任务中表现优异，能够理解生物信息学知识并生成专业解读
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/) 显示 Sonnet 在深度推理任务中与 Opus 质量相当
- **复杂生信分析需要较强的领域知识和推理能力，Sonnet 足够胜任**

**避免**：极少需要 Opus，除非分析极其复杂

**来源**：Reddit 社区讨论 + 90 天对比测试

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Sonnet 4.5** | 标准 R Markdown 开发（95% 场景） | 极端复杂的生信分析 | $$$$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Opus 4.5** | 极端复杂的生信分析 | 简单代码生成（浪费） | $$$$$ | ⭐⭐ | ⭐⭐ |
| **Haiku 4.5** | **不推荐** | 所有场景（能力不足） | $$ | ⭐⭐⭐⭐⭐ | ⭐ |

**说明**：
- Sonnet 覆盖 95% 的 R Markdown 开发场景
- Opus 用于极端复杂的生信分析（多组学整合、复杂网络分析）
- Haiku 不推荐用于 R Markdown 开发，因为需要较强的领域知识和推理能力

---

### 通用原则

1. **默认从 Sonnet 开始**：95% 的 R Markdown 开发任务 Sonnet 足够，无需 Opus
2. **复杂度判断**：根据分析的复杂程度选择模型
   - 简单分析（基础统计、简单可视化）：Sonnet
   - 标准分析（生存分析、差异表达、富集分析）：Sonnet
   - 复杂分析（多组学整合、复杂网络分析）：Sonnet 或 Opus
3. **质量优先**：R Markdown 分析是科研交付物，不应只追求低成本而牺牲分析质量
4. **领域知识需要推理**：理解生信学知识 + 生成专业级解读 + 编写符合规范的代码，需要较强的理解和写作能力
5. **Haiku 的局限性**：虽然 Haiku 速度快、成本低，但 R Markdown 开发需要较强的领域知识和推理能力，[社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1o856eb/tested_haiku_45_it-is-fast-but-cant-complete/) 显示 Haiku 在完成复杂多步骤任务时可能遇到困难

---

### ⚠️ 争议点

#### Sonnet vs Opus：R Markdown 开发应该用哪个？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Sonnet 够用** | 社区多数意见 | Sonnet 在代码生成和文档写作任务中表现接近 Opus，但速度快、成本低 |
| **Opus 必要** | 部分研究者 | 复杂生信分析是科研工作，值得投入更多资源确保质量 |

**数据支持**：
- [90 天对比测试](https://alirezarezvani.medium.com/claude-opus-4-5-vs-sonnet-i-tested-both-for-90-days-in-claude-code-bb4976923e3a)：Opus 在中等投入下成本与 Sonnet 相当
- [官方内部测试](https://spartner.software/blog/claude-sonnet-vs-opus-which-one-do-you-choose)：Sonnet 解决 64% 编程问题 vs Opus 38%（实际场景）

**建议**：
- **默认使用 Sonnet**：性价比最高，覆盖 95% R Markdown 开发场景
- **仅在以下情况升级 Opus**：
  - 极端复杂的生信分析（多组学整合、复杂网络分析）
  - 需要深度推理的科研问题
  - Sonnet 无法解决的复杂分析问题
  - 关键项目的最终分析审查

---

### 更新记录

- 2026-01-25：首次调研，覆盖 Anthropic
- 建议：2026-07 重新调研（6 个月后）

---

### 来源链接

**官方文档**：
- [Claude Tool Use Documentation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Choosing the right model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)
- [Claude Opus 4.5 vs Sonnet 4.5: Full Report](https://www.datastudios.org/post/claude-opus-4-5-vs-claude-sonnet-4-5-full-report-and-comparison-of-features-performance-pricing-a)

**社区讨论**：
- [Claude Opus 4.5 is insane (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/)
- [Opus or nothing for 90% of tasks (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1lqnqn6/anyone_else_in_the_mindset_of_its_opus_or_nothing/)

**对比测试**：
- [90-Day Claude Code Decision Framework](https://alirezarezvani.medium.com/claude-opus-4-5-vs-sonnet-i-tested-both-for-90-days-in-claude-code-bb4976923e3a)
- [Claude Sonnet 4 Vs Opus 4.1: Which Model To Use For Coding](https://labs.adaline.ai/p/claude-4)
