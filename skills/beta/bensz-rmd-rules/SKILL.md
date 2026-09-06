---
name: bensz-rmd-rules
description: 当用户要求编写 R Markdown 分析、开发 R 脚本或进行 R 数据分析时使用。规范脚本与报告分工、图表表达、结果解读和跨平台路径处理。
metadata:
  author: Bensz Conan
  short-description: R Markdown 开发规范（.R+.Rmd 混合架构 + 专家级解读 + 跨平台兼容）
  keywords:
    - bensz-rmd-rules
    - R Markdown
    - Rmd
    - 数据分析
    - 可复现报告
    - R 脚本
---

# bensz-rmd-rules

## 目标

规范 AI 开发 R Markdown 分析脚本的行为准则。当用户要求"写 Rmd 分析"、"开发 R 脚本"、"做数据分析"时触发。核心原则：遵循主业与副业分离架构（.R 保留完整数据，.Rmd 应用业务阈值），优先使用用户已有 R 包资源；图表默认按 Nature 级别可读性与出版质量生成；专家级解读兼顾弱背景读者，提供四层框架、指标导读与不常用指标首次解释协议；路径验证确保跨平台兼容性。前提：luckyBase 为硬依赖。

## 流程

### 输入

输入为项目的 `.R`/`.Rmd` 文件、已有 R 包资源、数据字典、分析目标和输出要求；运行前确认 `luckyBase::Plus.library()` 可用，并读取 `config.yaml`、模板和与当前分析直接相关的 references。

### 执行步骤

#### 核心原则概览

| 原则 | 核心要求 |
|------|----------|
| 现有资源优先 | 优先使用用户已有的 R 包和函数，不重复造轮子 |
| 人类可读 | 代码简洁优雅，天然适合人类审查 |
| 混合架构 | .R 负责数据处理/计算（保留完整数据），.Rmd 负责可视化/分析（应用业务阈值） |
| 函数分离 | 专用函数脚本 `_functions.R`，避免污染全局环境 |
| 数据筛选分离 | .R 不应用阈值筛选（方便审查原始状态），.Rmd 根据业务需求应用阈值（确保分析价值） |
| 不过度保护 | 避免过多防御性代码，以人类为中心 |
| 跨平台兼容 | 代码在 macOS/Linux/Windows 上均可运行，路径使用相对路径 |
| 完整因果链 | 代码前解释"为什么"，结果后解读"意味什么" |
| 分层指标解释 | 默认读者背景较弱；不常用指标先导读、首次详解、后续简写 |

#### 现有资源优先原则

##### R 包资源清单

优先使用用户已有的 R 包资源。完整包清单详见 `[config.yaml:r_packages]`，主要包括：

| 包名 | 用途 | 典型场景 |
|------|------|----------|
| **ccs** | 泛癌症基因组分类计算框架 | 癌症分型、亚型分类 |
| **GSClassifier** | 转录组学综合分类工具 | 基因签名分类、预测模型 |
| **lucky** | 常规 R 函数集合 | 生存分析、差异表达、可视化 |
| **luckyBase** | lucky 系列基础辅助包 | 包管理、基础工具函数 |
| **luckyExperiment** | 生物学实验数据处理 | 实验数据处理 |
| **luckyGEO** | GEO 数据下载与处理 | GEO 数据下载、处理 |
| **luckyModel** | 第三方生物信息学模型 | 模型集成、预测 |

##### luckyBase 强制要求（硬性规定）

**⚠️ 关键 1：luckyBase 必须强制加载**

luckyBase 是本技能的核心依赖，必须强制加载，不得跳过或提供降级方案。

**⚠️ 关键 2：必须使用 luckyBase::Plus.library 自动安装/加载包**

```r
# 正确做法（强制）
luckyBase::Plus.library("ggplot2")
luckyBase::Plus.library("DT")

# 错误做法（禁止）
library(ggplot2)  # 禁止直接使用 library()
if (!requireNamespace("ggplot2", quietly = TRUE)) {  # 禁止手动检查
  install.packages("ggplot2")
}
```

**⚠️ 关键 3：必须使用 luckyBase::convert 进行基因 ID 转换**

在涉及基因 ID 转换的场景（如 ENSEMBL → SYMBOL、ENTREZID → SYMBOL），必须使用 `luckyBase::convert()` 函数：

```r
# 正确做法（强制）
gene_symbols <- luckyBase::convert(
  ids = gene_ensembl_ids,
  from_type = "ENSEMBL",
  to_type = "SYMBOL",
  organism = "human"
)

# 错误做法（禁止）
# 禁止使用 biomaRt、AnnotationDbi 等其他包手动转换
# 禁止硬编码 ID 映射表
```

**理由**：
- `luckyBase::Plus.library()` 自动处理包的安装和加载，无需手动检查
- `luckyBase::convert()` 提供统一的基因 ID 转换接口，支持多物种、多 ID 类型
- 避免重复造轮子，保持代码简洁

##### candidate_r 函数库（可选）

当 lucky 系列不能满足需求时，可使用 `candidate_r` 函数库（用户可能拥有的自定义函数目录）。

**核心原则**：
- `candidate_r` 是**可选的**，不是必需的
- 用户已在 `00.Environment.R` 加载时，AI 可直接使用（轻量检查函数是否存在）
- 用户指定 `candidate_r_path` 时，AI 按该路径 `source()` 脚本
- **不猜路径、不扫描磁盘**，优先提供回退方案（lucky/CRAN/最小实现）

详细用法参见 `[references/candidate_r.md](references/candidate_r.md)`。

##### 资源使用优先级

1. **用户已有/已约定的 R 包**：在 `00.Environment.R` 里用 `luckyBase::Plus.library()` 统一加载；在分析脚本中优先使用 `pkg::fn()` 调用（避免到处 `library()`）
2. **candidate_r 函数库**（可选）：仅在用户已加载或用户提供 `candidate_r_path` 时再 `source()`（详见 `references/candidate_r.md`）
3. **CRAN/Bioconductor 包**：确实需要时，仍通过 `00.Environment.R` 用 `luckyBase::Plus.library()` 引入
4. **最小自定义函数**：最后选择，写入 `{主脚本名}_functions.R`（不要散落在 .Rmd 内）

#### 人类可读原则

代码风格、命名规范、注释要求等详细内容见 `[references/code_style_guide.md](references/code_style_guide.md)`。

**核心要点**：
- 管道优先：使用 `%>%` 或 `|>` 构建可读的数据处理流程
- 向量化思维：优先使用向量化操作，避免遍历 + if 判断
- 函数式编程：使用 `purrr::map()` 等函数式工具替代循环
- 数据驱动：用查找表、join 等数据驱动方式替代硬编码逻辑
- 不过度防御：避免对已由 `00.Environment.R` 管理的包/函数做冗余检查；仅在 I/O 边界与硬性前提（如 `00.Environment.R`、关键输入文件/目录）做明确的 `file.exists()`/`dir.exists()` + `stop()`，以提供更清晰的失败信息（见 `references/no_overdefensive_code.md`）

#### 图表语言规范

默认英文；如确需中文（如中文期刊投稿），通过 `.Rmd` 的 YAML `params.plot_language` 显式切换。

详细规则与示例见 `[references/plot_language.md](references/plot_language.md)`。

#### Rmd 标题规范

标题应描述“内容是什么”，而非“如何做/用什么函数做”。本规范适用于 `.Rmd` 正文中的 Markdown 标题（`##/###/####`）。

##### 禁止形式

| 禁止形式 | 示例 | 问题 |
|---|---|---|
| 括号备注 | `结果解读（专家叙事）` | 增加形式化感，不自然 |
| 主标题-副标题 | `决策曲线分析 - get_dca` | 暴露实现细节，冗余 |
| 函数名标题 | `数据筛选 - filter_data()` | 标题不应包含实现细节 |
| 流程化标注 | `数据加载与处理（第一步）` | 把过程编号写进标题，降低可读性 |

##### 推荐形式

| 推荐形式 | 示例 | 理由 |
|---|---|---|
| 简洁描述 | `结果解读` | 自然语言，简洁明了 |
| 内容导向 | `决策曲线分析` | 描述内容，不描述方法 |
| 专业术语 | `多因素 Cox 回归` | 使用领域标准术语 |
| 层级清晰 | `## 单因素筛选` `### Top 25 基因` | 结构清晰，读者易定位 |

##### 实践示例

❌ 错误示范：

```markdown
## 数据加载与处理（第一步）

### 单因素筛选 - univ_screen()

#### 结果解读（专家叙事）
```

✅ 正确示范：

```markdown
## 数据加载与处理

### 单因素筛选

#### 结果解读
```

#### 主业与副业分离原则

硬性要求（最小口径）：

- 采用 `.R` + `.Rmd` + `{主脚本名}_functions.R` + `00.Environment.R` + `tmp/{主脚本名}/` 的混合架构（默认结构见 `config.yaml:file_structure`）
- `.R` 负责重型计算与保存全量产物（不做业务阈值筛选）；`.Rmd` 基于 YAML `params` 做阈值筛选、可视化与专家级解读
- 命名一致：`{name}.R` / `{name}.Rmd` / `{name}.html`（除后缀外完全相同）

起手与细节（下沉到 references/templates）：

- 指南：[`references/hybrid_architecture_guide.md`](references/hybrid_architecture_guide.md)
- 示例：[`references/hybrid_architecture_examples.md`](references/hybrid_architecture_examples.md)
- 模板入口：`templates/`（R_data_template/Rmd_template/functions_template/00.Environment）

#### 不过度保护原则

核心口径：

- 主脚本/主 Rmd 不做冗余包检查与降级分支（包加载集中在 `00.Environment.R`）
- 禁止“占位性代码”掩盖失败：要么切实落地，要么显式 `stop()`，如需容错必须提供有效降级方案

详细反模式与边界规则见 `[references/no_overdefensive_code.md](references/no_overdefensive_code.md)`。

#### 跨平台兼容性原则

核心口径：相对路径 + `file.path()`；跨平台细节与可选验证脚本见 `[references/cross_platform.md](references/cross_platform.md)`。

#### 完整因果链原则

本原则要求 AI 像顶级科学家面向跨专业读者写作：默认读者相关背景较弱，先提供不失真的理解支架，再给出从**数据描述**到**深刻见解**的完整因果链，而非简单罗列统计结果。通俗表达不得牺牲定义、计算边界或不确定性。

##### 基因 ID 优先级（生物医学分析专用）

在生物信息学、医学统计等涉及基因的分析中，需遵循基因 ID 优先级规范：

- **展示优先级**：可视化、表格、文本解读中使用 **SYMBOL**（如 `TP53`），而非 ENSEMBL ID 或 ENTREZID
- **数据完整性**：保存的数据应包含 SYMBOL、ENSEMBL、ENTREZID 多种 ID，确保准确性和可追溯性
- **核心理由**：增强可读性，让临床医生、生物学家等非生信专业读者也能理解

详细规范参见 `[references/gene_id_guidelines.md](references/gene_id_guidelines.md)`。

##### 代码块前解释

代码块前解释的模板与示例已下沉：[`references/code_block_explanations.md`](references/code_block_explanations.md)。

##### 指标分层与首次解释（必须）

- 先按 `config.yaml:metric_explanation` 盘点指标；默认白名单包括描述统计、p/q/FDR/CI、常见效应量与相关系数、经典生存分析以及 ROC AUC 等经典诊断指标。未命中、无法确定或采用非标准定义时，按不常用指标处理。
- 只要出现不常用指标，就在首个分析模块前增加“指标导读”表，至少说明尺度/参考点、升降趋势、置信区间或其它不确定性、本次选用理由与判读边界。
- 不常用指标在结果正文首次出现时，先自然解释“是什么、如何计算、为什么使用、带来什么价值、如何判读”，随后立即结合本次数字解读；第二次起不再重复原理，只解读当前证据。
- 同名指标的公式、量纲、方向、参考点或时间窗发生变化时，视为新指标并重新解释。常用指标通常不展开教学，但存在反直觉方向或非标准设定时需简短澄清。

完整分类、表格字段、首次/后续出现协议与边界见 [`references/metric_explanation_protocol.md`](references/metric_explanation_protocol.md)。

##### 结果后解读（专家级，非模板化）
对重要输出（图表/表格/统计量）在**交付/收敛阶段**必须满足：
- **证据锚定 + 数字可追溯**：关键判断尽量用 `` `r ...` `` 内联数字（或明确可追溯的字面数字），避免“凭空写数字”
- **覆盖不漏项**：任何可见图/表输出块附近必须有 prose 解读（Fail Fast 门禁）
- **禁止代码生成解释文本**：允许代码生成数字，不允许代码拼接解释段落
“四层框架 / Top 信号 / 不确定性提示 / 可执行后续”保留为**推荐结构**（适用于关键输出与终稿；探索期可先低密度写解读，再逐步加深）。
解读是**思考的输出**，不是结构的填空。目标是让研究者在 30–60 秒内回答：**这个结果对我意味着什么？我下一步应该优先做什么？**（而不是解释“这个统计量是什么/这个图表用于做什么”）。
###### 解读前：建议先回答的四个问题（关键输出/终稿强烈建议）
1. **研究者视角**：如果我是项目负责人，看到这个结果，我最想确认/反驳的是什么？
2. **领域映射**：这个统计发现如何改变我对机制/病程/人群差异的理解（只给“可证伪”的推断，不写玄学结论）？
3. **决策帮助**：基于这个结果，我会优先做什么？不做什么？为什么？
4. **风险边界**：如果该结论不复现，最可能的原因是什么（分层样本量、构成混杂、批次、模型假设等）？
###### 禁止：机械套用模板（硬门槛）
以下写法属于“**不看数据也能写**”的空壳，必须避免：
- ❌ “这张图/表在本次数据中的直接观察是：... 这在统计层面的含义是：... 对研究者的直接意义是：... 你可以立即执行的下一步是：...”
- ❌ “数据描述：... 统计见解：... 领域见解：... 局限与后续：...” 的机械分项（把四层当成固定四段/固定四行标签）
###### 必须：分层解释 + 连贯叙述 + 证据锚定
- 面向弱背景读者时，先按指标解释协议搭建理解支架；这不是降低专业性，也不是允许重复教学。
- 默认采用**1–2 段连贯叙述**，自然融入四层内涵（四层是**内容门槛**，不是固定写作格式）。
- 每个关键判断至少包含：对象 + 对比/排序/方向 + 数值证据（优先 `` `r ...` `` 或明确可追溯的字面数字），并解释统计量在**本次结果**中的量级含义。
- 推荐（关键输出/终稿；严格模式下可能作为门禁）：Top 1–3 + 不确定性线索（CI/SE/bootstrap/CV 等）+ 至少 1 条可证伪推理 + 至少 1 条可执行后续（方法 + 输入 + 判据；阈值来自 `params`）。
###### 交付前自检（推荐；严格模式强烈建议）
- [ ] 判断是否绑定“对象 + 方向/对比 + 数值证据（优先 `` `r ...` ``）”，并解释量级含义（不只报 p/q/rho/HR）？
- [ ] 是否至少给出 1 条可执行后续（方法 + 输入 + 判据，阈值来自 `params`），并避免空泛句式缺少本地证据？
###### 禁止通用套话（硬门槛）
解读中的每个判断必须绑定**当前数据的具体对象与数值**，禁止写成教学口吻或通用规则。
**强制要求**：必须指出"当前数据中，哪几组/变量呈现什么模式"，优先用 `` `r ...` `` 嵌入具体数值（或明确可追溯的字面数字），必须解释统计量在当前数据中的量级含义。
黑白名单详见：[`references/four_tier_interpretation_framework.md`](references/four_tier_interpretation_framework.md) / [`references/interpretation_templates.md`](references/interpretation_templates.md) / [`references/interpretation_narrative_examples.md`](references/interpretation_narrative_examples.md)。
交付前静态预检（覆盖 + 质量）：
1) 图表/表格解读覆盖检验（强制，Fail Fast）：
```bash
# 探索期：仅报告（不阻断）
python3 bensz-rmd-rules/scripts/check_figure_table_interpretation.py your_report.Rmd
# 交付期：Fail Fast 门禁（不通过则阻断）
python3 bensz-rmd-rules/scripts/check_figure_table_interpretation.py your_report.Rmd --strict
```
若未通过：必须先补齐/加强对应输出块的解读（按“证据锚定 + 当前数据观察”口径；不强制四层标签），直到 `--strict` 命令通过，才允许进入后续步骤。
判定口径与可调参数见：`references/figure_interpretation_criteria.md` 与 `config.yaml:figure_interpretation_check`。
少数“命中输出模式但确实不产生可见输出”的 chunk，可在 chunk 头部加 `interp_check=FALSE` 手动豁免（避免误杀）。
2) 解读质量预检（启发式，推荐）：
```bash
# 探索期：仅提示不阻断
python3 bensz-rmd-rules/scripts/check_interpretation_quality.py your_report.Rmd --warn-only
# 交付期：默认门禁（不通过则阻断）
python3 bensz-rmd-rules/scripts/check_interpretation_quality.py your_report.Rmd
```
该脚本会读取 `bensz-rmd-rules/config.yaml:interpretation_quality_check` 作为默认阈值与检查开关（如环境缺少 PyYAML 则降级为内置默认值）。
如需更强的“反模板化/反流于表面”检查（机械模板识别、Top 名单落地、后续动作可执行句、强语气与稳健性约束等），使用：

```bash
python3 bensz-rmd-rules/scripts/check_interpretation_quality.py your_report.Rmd --strict
```

###### 禁止代码生成解释
解释性文本必须由 AI 直接写出；允许用 `` `r ...` `` 动态嵌入数字以保证精确与同步，但不得通过代码逻辑拼接/生成解释句子。

| 场景 | 允许 | 禁止 |
|---|---|---|
| 数字嵌入 | ✅ `` `r sprintf('%.2f', hr)` `` | ❌ 在正文硬写不可追溯数字 |
| 轻量词语选择 | ✅ `ifelse()` 选择“升高/降低”等词 | ❌ 通过代码拼接完整解释段落 |
| 结果引用 | ✅ `` `r nrow(tbl)` `` | ❌ `cat()`/字符串拼接输出解释文本 |

❌ 错误做法（代码生成解释）：

```r
interpretation <- ifelse(hr > 1, "提示风险增加", "提示风险降低")
cat("从统计上看，", interpretation)
```

✅ 正确做法（数字动态、解释直接）：

```markdown
从统计上看，该效应为 `r sprintf('%.2f', hr)`（95% CI: `r ci_low`–`r ci_high`），**提示暴露组风险显著高于参照组**。
```

##### 解读语气与风格

默认采用“论文口吻”：克制、客观、推论式。避免模板化教学提示与括号解释堆叠。不常用指标首次出现时的必要解释是例外，但应自然融入结果叙述，并从第二次起收敛。

| 维度 | 教学口吻（避免） | 论文口吻（推荐） |
|---|---|---|
| 括号使用 | `（即...）` `（注意：...）` | 尽量融入正文，括号主要用于 CI/单位等必要信息 |
| 提示语 | `提示：` `注意：` | 直接陈述结论与边界，不使用提示标记 |
| 解释重心 | “这是什么”式定义 | “意味着什么”式推论（绑定本次结果证据） |
| 语气 | 教导式、向导式 | 克制、客观、可验证 |

❌ 教学口吻（避免）：

```markdown
该效应为 1.85（95% CI: 1.32-2.59），这表明风险增加。（即：HR > 1 意味着暴露组风险更高）
需要注意的是，该结论可能受混杂因素影响。
```

✅ 论文口吻（推荐）：

```markdown
该效应为 `r sprintf('%.2f', hr)`（95% CI: `r ci_low`–`r ci_high`），**提示暴露组风险显著高于参照组**。
该结论的不确定性主要来自潜在混杂因素，需在多因素模型中进一步检验其稳健性。
```

##### 文本强调规范

在结果解读中，对**核心发现、关键判断、重要结论、不确定性来源**做适度加粗，帮助读者快速抓住重点；避免“满篇加粗”。

- 一个解读段落中，加粗内容通常不超过 2–3 处
- 不加粗方法说明、流程描述、一般属性（如“表格包含 700 行”）

##### 末尾讨论与分析

每个 Rmd 末尾必须包含讨论章节（主要发现 + 局限 + 可落地后续），随后添加“数字准确性验证”章节。深度模板见 `[references/expert_discussion_template.md](references/expert_discussion_template.md)`。

#### Rmd 模板规范

##### 章节结构（硬门槛）

每个 `.Rmd` 默认采用以下章节顺序（允许在中间插入具体分析模块，但不要删掉硬门槛章节）：

- `## 数据概览`
- `## 关键函数、参数与源代码位置`（**强制**，紧跟“数据概览”之后）
- `## 指标导读`（条件强制：存在不常用指标时保留；否则删除）
- （一个或多个）分析模块：如 `## 单因素筛选` / `## 多因素模型` / `## 模型性能与验证` / `## 可视化分析` 等
- `## 讨论与分析`（强制：主要发现 + 局限 + 可落地后续）
- `## 数字准确性验证`（强制：末尾检验）

##### 关键函数、参数与源代码位置（强制）

该章节的目标是“可追溯性”：让任何读者都能快速定位本报告的关键实现（以及为什么这样设）。

必须包含：

- 关键的分析过程是什么（按顺序，建议覆盖 3–10 个关键步骤）
- 用了哪些关键函数（推荐写成 `pkg::fn()`，并注明关键输入/输出对象名）
- 函数的关键参数是什么；为什么要这么设置（理由必须绑定本次数据/假设/阈值/限制）
- 源代码在哪个文件的第几行（写项目内的 `.R/.Rmd/_functions.R` 为主；格式建议 `相对路径:行号`）

推荐表格模板（直接复制到 Rmd 正文填写）：

```markdown
| 分析过程/产物 | 关键函数/对象 | 关键参数（是什么） | 为什么这样设置（理由） | 源代码位置（文件:行号） |
|---|---|---|---|---|
| 数据加载与整理 | `readRDS()` / `dplyr::mutate()` | `path=...` / `na.rm=TRUE` | 读取主脚本产物；避免 NA 影响统计量 | `cf01.R:42` / `cf01.Rmd:28` |
| 主要统计分析 | `survival::coxph()` | `formula=...` / `ties="efron"` | 选择 Cox 模型；ties 处理与数据规模匹配 | `cf01_functions.R:85` |
| 可视化输出 | `ggplot2::ggplot()` / `ggplot2::ggsave()` | `width/height/base_size` | 确保 Nature 级别可读性与打印清晰 | `cf01.Rmd:92` |
```

##### YAML 头部

Rmd 的 YAML 头以 `config.yaml:rmd_template.yaml_header` 为准；`templates/Rmd_template.Rmd` 内保留一份便于起手的拷贝，维护时需与 config 同步（可用 `scripts/check_rmd_template_yaml.py` 校验）。

##### HTML 主题（Liquid Glass / glassmorphism）

默认使用 **Liquid Glass 主题**（`templates/liquid_glass_theme.css`），这是一套 glassmorphism 风格的专业级样式：
- **Glassmorphism**：玻璃拟态效果，背景模糊与半透明层次
- **Motionless by Default**：默认无无限动画，避免选中文本/代码时出现"高亮漂移"的干扰
- **Auto Dark Mode**：根据系统偏好自动切换深色模式
- **Floating TOC（两种模式）**：静态浮动（常驻）/ 动态浮动（收起为左上角小圆点，悬停展开；默认）；移动端自动折叠，可点击顶部按钮展开

**使用方式**：
- 详细的 YAML 配置、特性说明、自定义选项见 [references/liquid_glass_theme_guide.md](references/liquid_glass_theme_guide.md)（说明文档；具体字段以 `config.yaml:rmd_template.yaml_header` 为准）
- 一键初始化脚本见下方"一键初始化新项目"

###### 一键初始化新项目（推荐）

本 skill 的默认模板假设你在“项目根目录”存在如下文件：
- `templates/liquid_glass_theme.css`
- `templates/liquid_glass_lightbox.html`（图片点击放大 + 刷新后缩放/阅读位置尽量保持）

为避免手工拷贝，推荐在新项目根目录运行（脚本对安装位置不敏感，会基于 `__file__` 自动定位 skill 目录）：

```bash
python3 /path/to/bensz-rmd-rules/scripts/bootstrap_liquid_glass.py --with-env
```

说明：
- `--with-env` 会在项目根目录创建 `00.Environment.R`（如已存在则跳过）
- 如需同时复制 DT/主题等常用模板，可加 `--with-extras`

##### 表格渲染

###### 默认规则（HTML：DT 优先）

当输出格式为 **HTML** 时，所有“数据表/结果表”（R 代码生成的 `data.frame`/`tibble`）默认使用 **DT**（`DT::datatable()`）进行渲染，除非用户明确指定使用其他表格方案（如 `knitr::kable()` / `gt` / `flextable` / `reactable` 等）。

推荐做法（优先）：

- 在项目根目录的 `templates/` 下 `source("templates/datatables_helper.R")`，并使用 `render_dt(...)` / `render_dt_output(...)` 输出表格（该 helper 由本 skill 维护，路径见 `config.yaml:datatables_helper`）。
- 若项目内缺少该文件，优先用 `bootstrap_liquid_glass.py --with-extras` 一次性复制（或手动从本 skill 的 `templates/datatables_helper.R` 取用）。
- 若未使用 helper，直接使用 `DT::datatable()` 也可，但需遵守下方“HTML 可见性硬规则”。

最小示例：

```r
# 00.Environment.R（强制）
luckyBase::Plus.library("DT")

# in .Rmd（HTML）
source(file.path("templates", "datatables_helper.R"))
render_dt(head(df, 100), pageLength = 10)  # 让它成为 chunk 的最后表达式
```

###### HTML 可见性硬规则（htmlwidget/DT，强制）

R Markdown 渲染为 HTML 时，`DT::datatable()` 等 htmlwidget 必须作为 code chunk 的“可见结果”返回，否则容易出现“代码在但不渲染”的漏项。

硬规则与示例见：[references/htmlwidget_visibility_rules.md](references/htmlwidget_visibility_rules.md)。

###### 交付前强制检查（强制）

交付前必须先通过“图表/表格解读覆盖检验”，避免出现“有输出但无解读”的漏项：

```bash
python3 bensz-rmd-rules/scripts/check_figure_table_interpretation.py path/to/your.Rmd --strict
```

交付前必须运行一次 htmlwidget 可见性静态检查，避免出现“代码在但 HTML 不出表/不出图”的漏项：

```bash
python3 bensz-rmd-rules/scripts/check_htmlwidget_visibility.py path/to/your.Rmd
```

##### 输出 HTML

使用 `knit-rmd-html` skill 将 Rmd 渲染为同名 HTML，保存在同级目录。

### 输出

输出包括遵循主业/副业分离的 `.R`、`.Rmd`、同名 HTML、图表/表格及数字准确性验证结果；分析过程、检查报告和临时文件按本 Skill 的 `.bensz-api` 工作区规则保存，不把中间结果混入源文件目录。

### 输出管理

#### BenszAPI 任务工作区


### 校验

#### 图表质量规范（Nature 级别）

所有代码生成的图表必须默认达到 Nature 系列期刊的出版级别（“默认即专业”）。

唯一目标：最大程度保证人类可读性（屏幕阅读 + 打印均清晰）。

**⚠️ 关键 4：每画一个图，必须主动检查并修复可读性问题（画完即交付，无需人工调整）**

##### AI 自主规划原则（必须）

- 可读性优先：字体/线条/点大小/图例/比例等参数以“读者能否清晰阅读”为第一准则。
- 场景自适应：根据数据量、图表类型、展示场景动态调整；必要时可偏离默认值，但需说明原因。
- 避免视觉缺陷：主动处理标签重叠、图例遮挡、乱码/缺字、低对比度、过密/过空等问题。

##### 可读性硬检查（生成绘图代码后必须显式检查）

每次生成绘图代码后，必须对以下项目逐条“检查→处理→再检查”，并在代码附近用 1-2 句说明你做了哪些可读性修复（避免只写一句“已优化”）。

阈值与默认策略以 `config.yaml:plot_readability` 为准（如用户另有要求，则以用户要求为准并说明偏离理由）。

| 检查项 | 常见触发条件（经验阈值） | 处理策略（至少做 1 个） |
|--------|--------------------------|--------------------------|
| 标签溢出 | 长标签导致超出画布边界（尤其 x 轴分类） | 旋转/换行/缩写 + 增加边距/增大画布 |
| 标签遮挡 | 文字与点/线/图例/注释发生重叠 | 调整 label 位置、只标注关键点、移动图例、分面 |
| 轴刻度过密 | 刻度数量过多导致挤在一起 | 减少 breaks、采样显示、增大画布 |
| 字体过小 | 预估打印或投影不可读（过密时尤甚） | 提高 `base_size`、增大图尺寸、减少信息量 |
| 图例遮挡 | 图例与数据区域重叠或挤压数据 | 改为 `"bottom"`/`"left"`/外置，调整 `guides()` |
| 中文/特殊字符 | 出现方块/乱码/缺字（或包含中文字符） | 显式指定支持中文的字体族（跨平台候选），必要时降级为英文 |

##### 可读性自检清单（生成代码时必须自检）

- [ ] 字体大小是否清晰可读（轴标题/图例/注释）？
- [ ] 线宽/点大小是否与数据密度匹配？
- [ ] 标签是否重叠（必要时旋转/缩写/分面）？
- [ ] 中文/特殊符号是否正确显示（必要时指定字体）？
- [ ] 图例是否遮挡数据（必要时外置/调整方向）？
- [ ] 配色是否色盲友好、对比充足（避免彩虹色）？
- [ ] 宽高比是否合理（避免信息拥挤）？

##### 技术规范（默认值，可按场景调整）

| 维度 | 推荐默认值 | 说明 |
|------|------------|------|
| 格式（静态） | PDF（矢量图，优先） | 位图仅用于特殊场景并说明理由 |
| 字体 | Arial/Helvetica（无衬线） | 系统缺失时回退 `sans` |
| 配色 | Nature 调色板或 viridis | 必须色盲友好，避免彩虹色 |
| 背景 | 白底 + 低噪声 | 轻网格或无网格，强调数据本身 |

##### 参数面向用户（写在 .Rmd 里；必须）

AI 在 `.Rmd` 中生成每张图的绘图代码时，必须把“用户可能需要调整的参数”集中成一个参数区块，并为每个参数写清楚 `#` 注释说明（含：作用、推荐范围/常用取值、调大/调小的视觉后果）。

**硬约束**：禁止把关键值散落在 `theme()` / `geom_*()` / `scale_*()` 里让用户难以定位；所有可读性关键参数必须从参数区块引用。

##### 图表标题策略（默认不落图；必须）

**硬约束**：默认生成的图（ggplot2 / plotly / 其他）**不得**使用 `title` / `subtitle` 参数（例如 `ggplot2::labs(title=..., subtitle=...)`、`ggtitle()`、`plotly::layout(title=...)`）。

**理由**：
- 图的语义应由**文件名**、`.Rmd` 的小节标题与图前说明来承载；保存文件名即可推断图是什么。
- 发表/投稿场景通常也不在图内放大标题（避免占用空间、与正文/图注重复）。

**替代做法（推荐）**：
- 用 `.Rmd` 的 Markdown 标题（`##/###`）+ 图前 1–2 句说明定位图的目的与变量定义。
- 如需图注，优先用 Rmd 的 `fig.cap`（而不是把标题写进图里）。

**例外**：仅当用户明确要求，或场景确实需要（例如教学演示、单图独立传播、外部审稿要求）时，才允许添加标题/副标题；且默认必须英文（受 `references/plot_language.md` 约束）。

示意结构（每张图都应遵循；可按场景增删参数，但必须保留“集中参数块 + 注释说明”口径）：

```r
# ==== Figure 1: {短标题}（用户可调参数）====
# 说明：下面所有参数都是“面向用户”的调参入口；默认值是 Nature 级别可读性起点。
fig1 <- list(
  # 画布尺寸（英寸）。调大：更不拥挤、更适合长标签；调小：更紧凑但更易溢出/字体显得小。
  width_in  = 6.0,
  height_in = 4.0,

  # 字体基准（pt）。影响轴刻度/图例等整体尺度；打印/投影不清晰时优先调大。
  base_size = 10,

  # 线条/点大小。点太密：减小 point_size 或加 alpha；线看不清：增大 line_size。
  line_size   = 0.8,
  point_size  = 1.2,
  point_alpha = 0.85,

  # 图例位置：避免遮挡数据。常用："right" / "bottom" / "left" / "top" / "none"。
  legend_position = "right",

  # x 轴文字角度。长分类名常用 45/60；角度越大越不重叠，但需要更大的 bottom margin。
  x_text_angle = 0
)
```

落地要点：

- ggplot2：统一用 `theme_nature_readable(base_size=..., x_text_angle=..., legend_position=...)`，并把 `geom_*` 的 `size/alpha/linewidth` 等绑到 `fig$...`。
- ComplexHeatmap：`save_heatmap_pdf(..., width=fig$width_in, height=fig$height_in, ...)`；row/col 字号、legend 字号等至少暴露“常用可调项”。

##### 交付门禁：矢量 PDF + JPG 预览 + 视觉自检（必须）

1) **正式交付唯一格式：矢量 PDF**
每张图必须保存为矢量 PDF（例如 `figure_xxx.pdf`）。HTML 内联图仅作为阅读体验，不视作正式交付。

2) **保存 PDF 后，必须自动生成 JPG 预览图，并基于预览图做视觉自检**
默认 run 目录：当前项目下 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/bensz-rmd-rules/run_YYYYMMDDHHMMSS/`；用户可通过 `.Rmd` 的 YAML `params.plot_run_dir` 覆盖父目录。

推荐做法：将 `templates/plot_delivery_helpers.R` 复制到用户项目 `templates/` 下，并在 `.Rmd` 的 `plot-style` chunk `source()`；然后在每次 `ggsave()/save_heatmap_pdf()` 后调用 `bensz_pdf_to_jpg()` 生成 `*.jpg` 预览图（详见 `templates/Rmd_template.Rmd` 示例）。

**HTML 展示比例规则（必须）**：

- HTML 里“展示用的图”（内联图片）默认应使用 **由正式交付 PDF 渲染得到的 JPG 预览图**（即 `bensz_pdf_to_jpg()` 的产物），以保证 **HTML 展示比例与 PDF 完全一致**，便于用户对照查看。
- HTML 里图片可以刻意偏小：用 `out.width` 控制展示宽度（例如 `out.width="70%"` 或 `out.width="600px"`），但**不要**同时指定 `out.height`（避免拉伸导致比例失真）。Liquid Glass 默认支持点击放大，因此不需要把图放得很大。

常用可调参数（写在 `.Rmd` 的 YAML `params`，便于用户改动）：

- `params.plot_run_dir`：JPG 预览 run_* 的父目录；默认使用当前项目下 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/bensz-rmd-rules/`
- `params.plot_preview_dpi`：JPG 预览 DPI（越大越清晰但文件越大；默认 200）

3) **AI 必须基于 JPG 逐图检查并处理**（交付前门禁）

- 文字是否溢出/裁切（贴边、超出边界、被上边界/边框挤压）
- 字体是否“人类可读”（过小、密集导致不可读）
- 线/点是否过细（打印/投影不清晰）
- 图例是否遮挡数据（或挤压主体导致过密）
- 信息是否过密（必要时采样 breaks / 只标注 topN / 分面 / 增大画布）

##### 标准化模板（强烈推荐复用）

本 skill 提供可直接复制到用户项目的模板（见 `templates/`）：

- `templates/nature_colors.R`：`nature_colors`
- `templates/nature_theme.R`：`theme_nature()`、`theme_nature_readable()`
- `templates/complexheatmap_template.R`：ComplexHeatmap 可读性模板
- `templates/plotly_template.R`：plotly 交互图模板
- `templates/plot_delivery_helpers.R`：PDF 交付 + JPG 预览（`bensz_run_dir()` / `bensz_pdf_to_jpg()`）

落地方式（推荐）：

- 将上述模板复制到用户项目根目录的 `templates/` 下（与本 skill 同名即可）。
- 在 `.Rmd` 开头 `source(file.path("templates", "..."))` 统一加载（见 `templates/Rmd_template.Rmd` 的 `plot-style` 代码块）。

图表质量的完整规范与检查项见：[references/plot_quality_standards.md](references/plot_quality_standards.md)。

常见可读性问题场景与可复制最小示例见：[references/plot_quality_standards.md](references/plot_quality_standards.md)。

#### 数字准确性验证（末尾检验）

每个 `.Rmd` 的末尾应包含“数字准确性验证”章节，确保解读中的关键数字可追溯到变量/计算逻辑，并优先使用 `` `r ...` `` 动态嵌入以避免漂移。

模板与规范见：[references/numeric_accuracy_verification.md](references/numeric_accuracy_verification.md)。

#### 交付验证（强制）

交付前必须附带自检报告（含“解读-代码一致性”证据）。

模板与真实示例入口见 `[references/delivery_verification.md](references/delivery_verification.md)`。

#### 工作流检查清单

内部检查清单见 `[references/workflow_checklist.md](references/workflow_checklist.md)`。

### 失败与恢复

缺少 `luckyBase`、R 包/模板、输入文件或渲染依赖时，保留命令输出和检查报告并停止相应阶段；图表/表格解读或 HTML 可见性门禁未通过时先修复或明确阻塞，不把未验证结果交付为完成。可在同一任务工作区重试。


## 约束

<!-- BEGIN COMMON CONSTRAINTS -->
<!-- Source-Hash: sha256:15120201e9e0c7569517261d57ecefb63ac279c26ed13876f8e95b6dc35854d3 -->
<!-- Template-ID: skill-common-constraints; Template-Version: 1; Sync-Policy: exact-block -->

### 公共硬约束

本块由 `docs/templates/skill-common-constraints.md` 统一维护；每个 `SKILL.md` 的 `## 约束` 必须逐字同步本块，不得在副本中改写公共规则。

- 任务需要落盘时，使用唯一的 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/` 根目录；共享材料放入 `shared/`，Skill 专属材料放入该 Skill 的 `input/`、`output/`、`log/`。
- 正式交付物、源代码和正式计划按项目约定保存，不写入任务工作区；未经授权不覆盖、删除、迁移或远程写入。
- 项目维护变更检查 BAC 可用性并记录需求、AI 产出、工具结果、文件改动和验证摘要；BAC 只做过程审计，不替代署名、责任或合规判断。
- 不记录 API Key、访问令牌、密码、Cookie、环境/凭据文件、私有 Prompt、身份信息、本地用户名、主机名或不必要的大体积原始数据。
- 文件路径必须规范化并限制在授权项目范围内；外部 URL、子进程和网络访问遵循最小权限，防止路径遍历、SSRF 和命令注入。
- Skill 版本唯一记录在自身 `config.yaml:skill_info.version`；公开 API、协议、目录或配置变更同步文档与 `CHANGELOG.md`。
- `bensz-collect-bugs` 是一个 Agent Skill；仅将 Bensz Agent Skill 或 Bensz 基础设施本身的设计缺陷交给它。先脱敏写入 `~/.bensz-skills/bugs/`，当前任务不中断，只有用户明确要求才公开上报，禁止直接修改用户已安装的 Skill 源码。

<!-- End of canonical common constraints. -->
<!-- END COMMON CONSTRAINTS -->
