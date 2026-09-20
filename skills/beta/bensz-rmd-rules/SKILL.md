---
name: bensz-rmd-rules
description: 当主要交付物是基于 R 的数据分析流程、科学结果、可复现数据产品、R Markdown/HTML 报告或论文级图表与解读时使用；即使流程中包含 `.R` 脚本和仅服务当前分析的辅助函数，也由本 Skill 主导。⚠️ 不适用：主要交付物是可独立复用的 R 函数、稳定公共 API、类或 R Package；这些任务使用 bensz-r-developer。也不用于仅渲染既有 Rmd 或其它语言的数据分析。
metadata:
  author: Bensz Conan
  short-description: R/Rmd 多阶段分析、可恢复数据产品与论文级报告规范
  keywords:
    - bensz-rmd-rules
    - R Markdown
    - Rmd
    - 数据分析
    - 断点续算
    - 可复现报告
---

# bensz-rmd-rules

## 目标

先理解研究目标与数据，再把任务组织为可审查、可恢复的 R 分析单元。`.R` 负责完整数据、重型计算和持久数据产品；`.Rmd` 负责报告层筛选、可视化与证据锚定的专家解读。新项目无论只有一个分析步骤还是多阶段流程，都必须从一开始启用 `targets` 与 `renv`；已有项目按实际状态独立兼容，缺什么就保持什么，不自动补齐或迁移。

本 Skill 关注的是“分析怎样可靠地跑完并形成可信结果”，而不是“R 软件组件怎样形成稳定公共 API”。触发依据是主要交付物和验收标准，不是文件扩展名：

| 场景 | 主导 Skill |
| --- | --- |
| 主要交付物是分析数据流、统计结果、可恢复产品、Rmd/HTML 报告、图表与解释 | `bensz-rmd-rules` |
| 主要交付物是可独立测试、文档化、版本化或跨项目复用的函数、类、API、Package | `bensz-r-developer` |
| 分析流程需要一个可复用组件 | 本 Skill 先定义分析需求、输入输出与集成证据，`bensz-r-developer` 实现组件，本 Skill 再接回流程验证结果与报告 |

本 Skill 可以创建只服务当前分析单元的 `_functions.R` 和 helper，但不为追求“通用”而把它们扩展成公共 Package。若用户的主要验收标准转为 API 稳定性、Package 结构、roxygen2/testthat 或跨项目复用，应将该组件交给 `bensz-r-developer`。

本 Skill 还负责 Nature 级图表、弱背景读者的指标导读、数字追溯、HTML widget 可见性和跨平台路径。`luckyBase` 是唯一固定 Bensz 生态依赖。具体分析包由项目声明并写入 `renv.lock`；`targets` 是新项目唯一流程编排入口，`renv` 是新项目唯一环境锁定入口。本 Skill 不自动接入 State、Verifier、Pack 或 Gate。

## 流程

### 输入

确认以下信息；已有上下文足够时直接提取，不重复询问：

- 研究问题、报告用途、正式交付物和可接受的统计边界；
- 主要验收对象，以及函数的复用范围是当前分析、当前项目还是跨项目公共 API；
- 原始输入、数据字典、样本/变量含义、隐私限制与只读范围；
- 重算成本、外部请求、随机性、关键参数与已有项目布局；
- 现有 `.R`、`.Rmd`、`00.Environment.R`、`products/`、旧 `tmp/`、`_targets.R`、`renv.lock` 或 `renv/` 资产；
- 用户已有 R 包与函数，以及项目是否已有 `targets`/`renv`。固定加载入口只有 `luckyBase`，其它包由项目 `renv.lock` 决定。

读取 `config.yaml`。按任务选择 references：

- 新建/重构数据流：[`references/hybrid_architecture_guide.md`](references/hybrid_architecture_guide.md)、[`references/hybrid_architecture_examples.md`](references/hybrid_architecture_examples.md)、[`references/analysis_workflow_cache.md`](references/analysis_workflow_cache.md)；新项目初始化还需读取 `templates/_targets.R` 与 `templates/renv/activate.R`。
- 审查流程：[`references/serial_review_protocol.md`](references/serial_review_protocol.md)；
- R 实现：[`references/code_style_guide.md`](references/code_style_guide.md)、[`references/no_overdefensive_code.md`](references/no_overdefensive_code.md)、[`references/cross_platform.md`](references/cross_platform.md)；
- 指标与解读：[`references/metric_explanation_protocol.md`](references/metric_explanation_protocol.md)、[`references/four_tier_interpretation_framework.md`](references/four_tier_interpretation_framework.md)、[`references/interpretation_templates.md`](references/interpretation_templates.md)、[`references/interpretation_narrative_examples.md`](references/interpretation_narrative_examples.md)、[`references/expert_discussion_template.md`](references/expert_discussion_template.md)；
- 图表/HTML：[`references/plot_quality_standards.md`](references/plot_quality_standards.md)、[`references/plot_language.md`](references/plot_language.md)、[`references/htmlwidget_visibility_rules.md`](references/htmlwidget_visibility_rules.md)、[`references/liquid_glass_theme_guide.md`](references/liquid_glass_theme_guide.md)；
- 生物医学 ID：[`references/gene_id_guidelines.md`](references/gene_id_guidelines.md)；可选函数库：[`references/candidate_r.md`](references/candidate_r.md)。

对 `raw/` 只做足以规划的轻量只读盘点；规划阶段不得意外启动完整计算。

### 执行步骤

#### 1. 判定主交付物并建立需求—分析图

先判断验收标准是否以分析结果、数据流、恢复能力和报告为中心。若任务只要求设计可复用函数/API/类/Package，而没有分析流程交付，本 Skill 不应主导，应转交 `bensz-r-developer`。若两类交付同时存在，记录主 Skill、组件边界和交接点；分析主导时，本 Skill 拥有需求与集成验收，`bensz-r-developer` 只负责被明确划出的可复用组件。

随后列出需求与交付物，再形成分析单元表。每行至少包含：`AA.BB.CC` 编号、目的、上游、输入、主要数据产品、缓存决定、报告关系与完成判据。只有在以下条件成立后才生成代码：

- 每项需求至少映射到一个单元或明确说明不处理；
- 依赖无环，且上游编号严格早于下游；
- 综合报告晚于其全部输入；
- 简单低成本任务保持一个必要单元，不为形式完整强拆步骤或制造缓存。

编号与文件契约：

```text
AA.BB.CC. 名称.R
AA.BB.CC. 名称_functions.R
AA.BB.CC. 名称.Rmd
AA.BB.CC. 名称.html
```

同一单元只创建实际需要的文件；`_functions.R` 不是执行节点。数字元组升序是默认执行顺序。`00.Environment.R` 默认全项目唯一，只负责包加载、项目根路径、全局选项和真正跨单元的配置。

#### 2. 判定项目状态并选择唯一策略

先运行 `<skill-root>/scripts/check_targets_renv.py <项目根> --mode auto` 做只读盘点。空目录或用户明确声明新建时进入新项目策略；发现任一 R/Rmd、产品目录、runner、`_targets.R`、`renv/` 或 `renv.lock` 时进入已有项目策略；信号冲突或半成品状态不明确时先请求澄清。

新项目必须复制最小 `_targets.R`、初始化 `renv` 并生成 `renv.lock` 与 `renv/activate.R`，即使只有一个分析步骤。`targets` 负责依赖图、增量重建和执行顺序；产品 helper 仍负责 `products/`、`metadata.yaml` 和 `SUCCESS`。已有项目对 `targets` 与 `renv` 独立判断：已有哪个就维护哪个，缺失哪个就不创建哪个；旧 runner 只作为已有项目的历史入口，不与 targets 共写一套产品，也不是新项目回退入口。

#### 3. 确定目录与兼容模式

新项目使用以下边界：

| 位置 | 职责 |
| --- | --- |
| 项目根目录 | `00.Environment.R`、编号 R/functions/Rmd 及同名 HTML |
| `raw/` | 用户原始输入；默认只读 |
| `products/<流程>/<编号名称>/` | 可恢复、可审查、供下游复用的完整数据产品 |
| `reports/figures\|tables\|supplementary/` | 论文可直接使用的正式图、表和补充材料 |
| `.bensz-api/` | AI 草案、审查结果、预览与验证日志；不得成为科学数据唯一副本 |

若现有项目仍以 `tmp/{主脚本名}/` 工作，先识别并保留，不迁移、不覆盖；只有用户明确要求迁移时才建立映射、保留原路径并提供回退。详见架构指南。

#### 4. 设计缓存边界

边界在以下任一条件下通常值得缓存：计算昂贵；被多个下游复用；经历高风险/有损转换；需要人工审查；依赖可变外部请求；中断后重做代价高。毫秒内可重建、只服务下一行或纯展示格式的对象不默认缓存。

每个持久检查点承担四类职责：

1. 可恢复的完整主对象；
2. 人类可读的全量表、受控预览、schema 或 `summary.md`；
3. `metadata.yaml`，记录单元、输入、参数、相关代码、上游身份、输出结构、契约版本和耗时；
4. 所有文件重新读取与完整性检查通过后才写入的 `SUCCESS`。

缓存身份至少覆盖输入摘要、影响本步骤的参数、相关代码摘要、上游产品身份和输出契约版本；必要时加入会改变结果的 R/包版本。时间戳不得进入身份。使用 `templates/checkpoint_helpers.R` 提供的路径、摘要、命中判断和“临时文件 → 验证 → 正式文件 → SUCCESS”协议，不即席复制一套 helper。

#### 5. 实现计算层与报告层

- 所有包在 `00.Environment.R` 中经 `luckyBase::Plus.library()` 加载；分析脚本优先用 `pkg::fn()`。基因 ID 转换使用 `luckyBase::convert()`。
- `.R` 读取 `raw/` 或上游 `products/`，保留未经报告阈值筛选的完整结果，并写入自己的产品目录。
- `_functions.R` 只承载当前分析单元或当前项目的 helper，不要求公共 API、独立版本或跨项目兼容；达到这些复用条件时，明确契约后交给 `bensz-r-developer`。
- 报告阈值、Top N、配色和展示策略放在 `.Rmd` YAML `params`；修改这些参数只重渲染报告，不使重型产品失效。
- `.Rmd` 从 `products/` 读取全量结果；正式图表写 `reports/`，同名 HTML 留在根目录。图表标题由 Rmd 小节与图注承担，默认不在图内重复标题。
- 只在 I/O 边界和硬前提做明确检查；不以占位代码、静默降级或过度防御掩盖失败。
- 涉及不常用、任务自定义或非标准定义指标时，先写指标导读，首次完整解释，后续只解释当前证据；同名指标定义变化时重新解释。

新项目从 `templates/_targets.R`、`templates/renv/activate.R` 和 `00.Environment.R` 起步；先执行一次 `renv::init(bare = TRUE)` 或等价初始化，确认 `renv.lock` 已生成，再运行 `targets::tar_make()`。单报告也保留一个最小 target，不为形式拆出多个节点。多阶段项目再使用 `analysis_plan_template.yaml`、`R_data_template.R`、`functions_template.R`、`Rmd_template.Rmd` 和 `templates/checkpoint_helpers.R`。已有项目只增量维护已经存在的机制，不能因模板缺失就创建 `_targets.R`、`renv.lock` 或迁移目录。图表、DT、plotly 和主题 helper 按需复制，不创建未使用的模板文件。

#### 6. 在真实昂贵运行前串行审查

主 Agent 完成全部初稿后，按顺序启动三个新的、彼此独立且只读的子 Agent：

1. 结构与数据流：需求覆盖、编号、依赖、目录、缓存边界、`raw/` 只读；
2. R 实现与恢复：对象生命周期、路径、随机性、缓存身份、原子落盘、损坏识别、断点恢复；
3. 科学与统计：方法、偏差/混杂、多重检验、数据泄漏、模型假设、不确定性、结论边界。

每轮读取主 Agent 修正后的最新版本，只输出问题、证据和建议；只有主 Agent 修改文件。记录“通过”也是有效结论，不制造形式性修改。完整权限与降级规则见串行审查协议。

#### 7. 运行、缓存命中与恢复

新项目先运行 `<skill-root>/scripts/check_targets_renv.py <项目根> --mode new`，再由 `targets::tar_make()` 统一执行；`_targets/` 是 targets 的内部状态目录，不进入正式交付。`analysis-plan.yaml` 可作为需求与产品契约，但不再驱动第二个 runner。旧 `run_analysis_workflow.py` 与编号 checker 仅用于已有项目中已经采用该历史入口的维护和只读检查；已有项目不补 plan、不创建 targets/renv，也不建立双入口。

编号计算流遵循：

- 身份和完整性均匹配：记录 `cache hit`，读取产品；
- 缺少 `SUCCESS`、元数据/输出损坏或身份变化：当前单元重算；
- 上游身份变化：必要下游自然失效；不相关的更早单元继续复用；
- “从某步恢复”仍按顺序记录更早步骤命中，再从失败边界执行；
- 强制重算和恢复控制属于计算层，不写入 Rmd YAML。

```bash
python3 <skill-root>/scripts/run_analysis_workflow.py <项目根> --force-step 01.00.00
python3 <skill-root>/scripts/run_analysis_workflow.py <项目根> --resume-from 01.00.00
```

严禁仅因文件存在就命中缓存。失败单元不得留下 `SUCCESS`，已成功的前序产品保留。

#### 8. 完成报告与交付

图表默认英文；中文期刊等场景通过 `params.plot_language` 显式切换。静态正式图保存矢量 PDF，生成 JPG 预览并逐图检查裁切、字体、线点、图例、密度与配色；预览进入任务工作区，不进入正式报告目录。

每个可见图/表附近写基于当前数据的连贯解读：对象 + 方向/对比 + 可追溯数值 + 量级含义；关键结果补不确定性、可证伪推理和“方法 + 输入 + 判据”的后续。允许 `` `r ...` `` 嵌入数字，不允许代码拼接解释段落。

### 输出

按复杂度交付：分析单元表、唯一 `00.Environment.R`、必要的编号 `.R`/`_functions.R`/`.Rmd`、同名 HTML、`reports/` 正式材料，以及验证摘要。只有多阶段计算流才交付 `analysis-plan.yaml` 和 `products/` 数据产品；简单任务只产生最小必要集合。若协作开发可复用组件，还要记录组件来源、版本或接口契约及集成验证，但组件自身的公共 API、Package 文档和独立测试由 `bensz-r-developer` 负责。

### 输出管理

正式代码、Rmd/HTML、科学数据产品和报告留在用户项目约定位置。AI 输入引用、草稿、三轮审查、JPG 预览、命令和验证日志进入本轮唯一 `.bensz-api/task-*` 工作区。`raw/` 不写入；`products/` 不保存只服务本轮 Agent 的草稿；`reports/` 不放 Rmd、HTML、模型缓存或审查日志。

### 校验

交付前按适用模式完成检查。编号计算流额外执行：

```bash
python3 <skill-root>/scripts/check_targets_renv.py <项目根> --mode new
Rscript -e 'renv::status()'
targets::tar_make()
python3 <skill-root>/scripts/check_rmd_template_yaml.py
```

简单报告和旧 `tmp/` 项目不要求 plan/runner；旧项目可用 `--legacy` 显式确认兼容模式。所有 Rmd 报告继续执行：

```bash
python3 <skill-root>/scripts/check_figure_table_interpretation.py <报告.Rmd> --strict
python3 <skill-root>/scripts/check_interpretation_quality.py <报告.Rmd> --strict
python3 <skill-root>/scripts/check_htmlwidget_visibility.py <报告.Rmd>
Rscript <skill-root>/scripts/check_plot_readability.R <正式图.pdf> --render-jpg --out-dir <任务根>/bensz-rmd-rules/output/plot-check
```

按项目实际情况再执行 R 语法/运行、Rmd 渲染、PDF/JPG 视觉检查和数字追溯。检查清单见 [`references/workflow_checklist.md`](references/workflow_checklist.md)，交付证据格式见 [`references/delivery_verification.md`](references/delivery_verification.md)，数字规则见 [`references/numeric_accuracy_verification.md`](references/numeric_accuracy_verification.md)，代码块说明见 [`references/code_block_explanations.md`](references/code_block_explanations.md)，图表覆盖判据见 [`references/figure_interpretation_criteria.md`](references/figure_interpretation_criteria.md)。

最低验收：

- 编号、依赖、同词干文件、产品目录和报告文件可相互定位；
- 相同输入重跑命中缓存，参数/代码/上游变化只失效必要下游；
- 中途失败无 `SUCCESS`，损坏缓存不会被误命中；
- 修改报告阈值/配色不触发重型计算；
- 删除 `.bensz-api/` 不影响正式流程重跑；
- 旧 `tmp/` 项目未被隐式迁移；
- 新项目只有一个分析步骤时仍存在一个可运行 target；
- `renv.lock` 变化纳入环境身份，`renv/library/`、staging 和缓存不进入交付；
- 三轮审查及轮间修正可追溯，或按规则明确披露降级。

### 失败与恢复

- 缺少 `luckyBase`：立即停止并说明安装前提，不改用另一套包管理逻辑。
- 新项目缺少 `_targets.R`、`renv.lock` 或 `renv/activate.R`：在初始化阶段停止，补齐并验证后再运行；运行中不得静默安装、snapshot 或 restore。
- 已有项目缺少 targets 或 renv：保持缺失状态，继续维护现有入口，不把兼容任务变成迁移任务。
- 需求、数据字典或统计边界不足：完成安全的只读盘点与待确认分析图，不启动昂贵计算。
- 缓存不完整、哈希不符或无法解析：视为 miss，保留证据，重算该单元及必要下游；不手工伪造 `SUCCESS`。
- Rmd 渲染失败：保留 `.Rmd`、计算层产品和日志，从报告层恢复，不重跑无关计算。
- 宿主无子 Agent：披露降级，按三个职责串行自检并明确“非独立审查”；用户明确要求真实多 Agent 或任务高风险时停止在运行前。
- 已有项目冲突：不覆盖、不迁移；旧 `tmp/` 项目沿用原运行入口，不因新 checker 补建 plan；仅提供增量修改或显式迁移方案。

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

### Skill 专属约束

- 仅在授权范围内只读盘点和读取 `raw/` 输入；不修改、覆盖或向 `raw/` 写入。不在日志或元数据记录绝对私有路径、凭据或不必要的原始数据。
- 不因本 Skill 提供模板就强制创建全部文件；分析复杂度、缓存边界和报告数量由真实需求决定。
- 不把业务统计规则写入通用 checkpoint helper；helper 只处理路径、摘要、身份、完整性与安全落盘。
