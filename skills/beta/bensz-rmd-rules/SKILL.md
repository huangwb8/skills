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

先理解研究目标与数据，再把任务组织为可审查、可复现的 R 分析流程。`.R` 负责完整数据、重型计算和持久数据产品；`.Rmd` 负责报告层筛选、可视化与证据锚定的专家解读。新项目必须使用 `renv` 并在真实 R/Rmd 入口上完成轻量测试；线性、低成本流程采用不含 targets 的 `simple`，存在非线性依赖、昂贵步骤、复用、局部失效、恢复、血缘或并行需求时采用 `complex` 并使用 targets。已有项目按实际架构维护，缺什么就保持什么，不自动补齐或迁移。

本 Skill 关注“分析怎样可靠地跑完并形成可信结果”，不是“R 软件组件怎样形成稳定公共 API”。触发依据是主要交付物和验收标准，不是文件扩展名：

| 场景 | 主导 Skill |
| --- | --- |
| 分析数据流、统计结果、可恢复产品、Rmd/HTML、图表与解释 | `bensz-rmd-rules` |
| 可独立测试、文档化、版本化或跨项目复用的函数、类、API、Package | `bensz-r-developer` |
| 分析流程需要可复用组件 | 本 Skill 定义分析需求与集成证据，`bensz-r-developer` 实现组件，本 Skill 接回流程验证 |

本 Skill 可以创建只服务当前分析单元的 `_functions.R` 和 helper，但不为追求“通用”而扩展成公共 Package。它还负责 Nature 级图表、弱背景读者的指标导读、数字追溯、HTML widget 可见性和跨平台路径。`luckyBase` 是唯一固定 Bensz 生态依赖，其它分析包由项目声明并写入 `renv.lock`。本 Skill 不自动接入 State、Verifier、Pack 或 Gate。

## 流程

### 输入

从已有上下文提取以下信息；只有缺失会改变行为或安全边界时才询问：

- 研究问题、报告用途、正式交付物、统计边界与完成判据；
- 原始输入、数据字典、样本/变量含义、隐私限制、授权范围与 `raw/` 只读边界；
- 重算成本、依赖形态、外部请求、随机性、关键参数和恢复需求；
- 现有 `.R`、`.Rmd`、`00.Environment.R`、产品路径、旧 `tmp/`、`_targets.R`、`renv.lock` 或 `renv/`；
- 可用测试数据、是否允许真实数据子集，以及需覆盖的分组、缺失和边缘条件；
- 主要验收对象，以及函数只在当前分析、当前项目或跨项目复用。

读取 `config.yaml`，再按任务读取最少必要 references：

- 项目状态、模式和目录：[`references/workflow_modes.md`](references/workflow_modes.md)、[`references/hybrid_architecture_guide.md`](references/hybrid_architecture_guide.md)；
- 新建或实质修改分析流：[`references/lightweight_testing.md`](references/lightweight_testing.md)；
- 多阶段产品与恢复：[`references/analysis_workflow_cache.md`](references/analysis_workflow_cache.md)、[`references/hybrid_architecture_examples.md`](references/hybrid_architecture_examples.md)；
- 审查：[`references/serial_review_protocol.md`](references/serial_review_protocol.md)；
- R 实现：[`references/code_style_guide.md`](references/code_style_guide.md)、[`references/no_overdefensive_code.md`](references/no_overdefensive_code.md)、[`references/cross_platform.md`](references/cross_platform.md)；
- 指标与解读：[`references/metric_explanation_protocol.md`](references/metric_explanation_protocol.md)、[`references/four_tier_interpretation_framework.md`](references/four_tier_interpretation_framework.md)、[`references/interpretation_templates.md`](references/interpretation_templates.md)、[`references/interpretation_narrative_examples.md`](references/interpretation_narrative_examples.md)、[`references/expert_discussion_template.md`](references/expert_discussion_template.md)；
- 图表/HTML：[`references/plot_quality_standards.md`](references/plot_quality_standards.md)、[`references/plot_language.md`](references/plot_language.md)、[`references/htmlwidget_visibility_rules.md`](references/htmlwidget_visibility_rules.md)、[`references/liquid_glass_theme_guide.md`](references/liquid_glass_theme_guide.md)；
- 生物医学 ID：[`references/gene_id_guidelines.md`](references/gene_id_guidelines.md)；可选函数库：[`references/candidate_r.md`](references/candidate_r.md)。

对 `raw/` 只做足以规划与选取测试样本的轻量只读盘点；不得在规划阶段意外启动完整计算。

### 执行步骤

#### 1. 判定主交付物并建立需求—分析图

先确认验收是否以分析结果、数据流、恢复能力和报告为中心。若只要求可复用函数/API/类/Package，应转交 `bensz-r-developer`。两类交付并存时记录主 Skill、组件边界和交接点。

形成分析单元表，每行至少包含 `AA.BB.CC` 编号、目的、上游、输入、主要产品、缓存决定、报告关系与完成判据。每项需求必须映射到单元或明确排除；依赖无环且上游编号更早；简单任务保持一个必要单元，不为形式完整强拆。文件按需使用：

```text
AA.BB.CC. 名称.R
AA.BB.CC. 名称_functions.R
AA.BB.CC. 名称.Rmd
AA.BB.CC. 名称.html
```

`_functions.R` 不是执行节点。`00.Environment.R` 默认全项目唯一，只负责包加载、项目根、产品路径、全局选项和真正跨单元的配置。

#### 2. 先判项目状态，再选工作流模式

运行只读检查：

```bash
python3 <skill-root>/scripts/check_targets_renv.py <项目根> --project-state auto --workflow-mode auto
```

决策优先级是：人类显式要求 → 已有项目兼容边界 → AI 按复杂度选择。已有任一 R/Rmd、产品、历史 runner、targets 或 renv 信号时按 `existing` 维护；检查器不得创建文件。新项目没有复杂信号时默认 `simple`；出现非线性依赖、昂贵/高失败代价步骤、多下游复用、局部失效、断点恢复、血缘或并行需求时选 `complex`。脚本数量和代码行数不能单独决定模式。把选择和理由写入分析计划或交付摘要。

- `simple`：使用 `renv`，不创建 `_targets.R`/`_targets/`；通过明确的 Rscript、Rmd render 或项目专用 `scripts/` 入口整体运行。
- `complex`：继承 simple 的环境、目录和测试底线，额外使用 `_targets.R` 管理依赖和增量执行。
- `existing`：统一记录为 `workflow_mode: preserved-existing`，另行报告实际观察到的 renv、targets、旧 runner 和产品机制；缺失机制只披露风险，不自动补齐。迁移必须由人类明确要求并先给出映射、结果校验和回退方式。

完整判据、人工覆盖和升级边界见 [`references/workflow_modes.md`](references/workflow_modes.md)。

#### 3. 固定目录、产品路径与临时边界

新项目按需创建：根目录放编号 R/Rmd/HTML 与标准 renv/targets 入口；`raw/` 只读；`reports/` 放正式图表；`templates/` 只放运行所需样式/渲染资产；`scripts/operations/` 放项目操作；`scripts/lib/` 放 checkpoint 等共享 helper；`scripts/tests/` 放可版本化测试；`tmp/tests/<run-id>/` 放每次隔离测试现场；`tmp/scratch/` 放可丢弃探索。不要为了目录树完整而预建空目录。

`products/` 默认保存可恢复、可审查、供下游复用的派生产品，不是可随意删除的技术缓存；`_targets/` 才是 targets 运行状态。产品路径优先级为人类显式指定 → 已有项目路径 → 项目统一设置 → `products/`。新项目只通过 `BENSZ_PRODUCTS_DIR`/`00.Environment.R` 的单一设置与路径 helper 读取，路径必须留在项目内且不得与 `raw/`、`reports/`、`tmp/`、`_targets/` 或 `.bensz-api/` 重叠。

已有 `tmp/{主脚本名}/` 项目保持原样；显式迁移前不移动历史产品、不删除旧入口。

#### 4. 设计产品与缓存边界

昂贵、复用、高风险/有损、需人工审查、依赖可变外部请求或中断重做代价高的边界才持久化。每个 checkpoint 包含完整主对象、可读摘要/受控预览、`metadata.yaml` 和最后写入的 `SUCCESS`。身份至少覆盖输入、影响结果的参数、相关代码、上游产品和输出契约；必要时加入会改变结果的 R/包版本，禁止时间戳参与身份。

新项目把 `templates/checkpoint_helpers.R` 复制到 `scripts/lib/checkpoint_helpers.R`；旧项目可继续维护原 helper 位置。不得即席复制缓存协议。详见 [`references/analysis_workflow_cache.md`](references/analysis_workflow_cache.md)。

#### 5. 实现计算层与报告层

- 包在 `00.Environment.R` 中经 `luckyBase::Plus.library()` 加载；分析脚本优先用 `pkg::fn()`；基因 ID 转换使用 `luckyBase::convert()`。
- `.R` 读取 `raw/` 或上游产品，保留未经报告阈值筛选的完整结果；`.Rmd` 读取产品并把 Top N、阈值、配色等展示参数放入 YAML `params`。
- 正式静态图写 `reports/`，同名 HTML 留在根目录；默认不在图内重复标题。
- 只在 I/O 边界和硬前提做明确检查；不以占位代码、静默降级或过度防御掩盖失败。
- 不常用或非标准指标先写指标导读，首次完整解释，后续只解释当前证据。

simple 从 `templates/Rmd_simple_template.Rmd` 或明确 Rscript 入口起步；complex 再使用 `templates/_targets.R`、分析计划、计算模板和 checkpoint helper。两种新模式都先真实初始化 renv 并生成 `renv.lock` 与 `renv/activate.R`。首次交付前出现复杂信号时可记录理由并把在建 simple 提升为 complex；首次交付后项目已是 existing，模式变化属于迁移，不能自动执行。已有项目只增量维护已有机制。

#### 6. 选择测试风格并真实跑通

每个新建或实质修改的分析流程必须选一种测试风格：

1. `synthetic_fixture`：无授权真实数据、数据敏感或原始数据过大时，构造保留 schema、类型、主键、关键分组、缺失和至少一个边缘条件的最小数据；固定随机种子。
2. `project_subset`：有授权数据和现有代码时优先使用确定且有代表性的小子集；覆盖关键分组、结局、缺失与异常边界，不能默认用 `head(n)` 代替抽样理由。

测试代码写入 `scripts/tests/`，每次运行建立唯一 `tmp/tests/<run-id>/`，其中包含隔离输入、products/reports/store、渲染结果、日志和运行记录；该目录默认忽略。测试只改变输入规模和路径，不复制删减版分析脚本，不向业务逻辑加入 `analysis_mode`/`test_mode` 分支。simple 调用同一个正式 R/Rmd 入口；complex 执行同一 target 图，但 store 位于 `<run-id>/_targets`，不污染正式 `_targets/`、products 或 reports。

existing 项目发生实质修改时仍沿用原入口做可隔离的轻量试跑，但不得为了测试补建新版 renv/targets/编号布局或持久测试框架；无法隔离硬编码路径或覆盖副作用时，记录测试阻塞或剩余风险，等待人类授权最小可测试性改造。

至少断言输入契约、行列/类型、主键/关键分组、重要数值范围或统计不变量、预期产品、报告/图表生成以及 `raw/` 无写入。真实子集默认在断言后删除，只保留抽样规则、schema、非敏感摘要与不可还原证据。checker、语法检查和 `--dry-run` 只算 `preflight`；真实轻量链记为 `lightweight_execution`；未跑全量数据时 `full_data_execution` 必须记为 `NOT_RUN`。失败按环境/依赖、fixture/子集、路径隔离、分析代码、科学断言、报告渲染或外部服务分类，做最小修正并重跑真实受影响路径。

每次运行记录项目状态/模式、观察机制、测试风格、正式入口、run root、路径覆盖、R/renv 来源、代码/配置/lockfile 的 subject identity、三层执行状态、断言、正式路径前后对照、尝试和清理结果。详见 [`references/lightweight_testing.md`](references/lightweight_testing.md)。

#### 7. 在真实昂贵运行前串行审查

主 Agent 完成初稿与轻量测试后，按 [`references/serial_review_protocol.md`](references/serial_review_protocol.md) 顺序完成结构与数据流、R 实现与恢复、科学与统计三项只读审查。每项都读取前项修正后的最新版本，只有一个执行主体修改正式文件。任何影响执行、输出或断言的审查修正都会使旧证据失效，必须在最新 subject identity 上重跑受影响预检和轻量真实链。宿主不能提供独立 Agent 时明确记录降级，不得把自检冒充独立审查。

#### 8. 正式运行、恢复与报告

simple 运行明确 R/Rmd 入口；complex 先检查模式契约，再运行 `targets::tar_make()`，正式 store 为 `_targets/`。历史 `run_analysis_workflow.py` 只服务已经采用该入口的旧项目，不是新项目回退路径。缓存命中必须同时满足身份和完整性；失败单元不得留下 `SUCCESS`，已成功前序产品保留。

图表默认英文；中文期刊等场景通过 `params.plot_language` 切换。静态图保存矢量 PDF，并在任务工作区生成 JPG 预览检查裁切、字体、线点、图例、密度与配色。每个可见图/表附近写当前数据驱动的连贯解读：对象、方向/对比、可追溯数值和量级含义；关键结果补不确定性、可证伪推理与“方法 + 输入 + 判据”的后续。

### 输出

按模式交付分析单元表、唯一 `00.Environment.R`、必要的编号 R/Rmd/HTML、`renv.lock`、`renv/activate.R`、`scripts/tests/` 测试代码、`reports/` 正式材料和验证摘要。complex 额外交付 `_targets.R`，按需交付 `analysis-plan.yaml` 与产品；simple 不创建 targets 资产。测试记录绑定最新 subject identity，并分别报告 preflight、lightweight 与 full-data 状态，不能用轻量通过暗示全量已通过。

### 输出管理

正式代码、测试代码、Rmd/HTML、科学产品和报告留在用户项目约定位置。AI 草稿、审查、JPG 预览和任务日志进入本轮唯一 `.bensz-api/task-*`；项目测试现场进入 `tmp/tests/<run-id>/`，不成为正式结论唯一来源。`raw/` 不写入；`products/` 不放 Agent 草稿；`reports/` 不放源码、模型缓存或审查日志。`tmp/scratch/` 中的重要发现晋升为正式代码、产品和报告，并补 renv 与轻量测试证据。

### 校验

按项目状态和模式运行：

```bash
# 新 simple
python3 <skill-root>/scripts/check_targets_renv.py <项目根> --project-state new --workflow-mode simple
Rscript -e 'renv::status()'
Rscript <项目根>/scripts/tests/smoke_test.R

# 新 complex
python3 <skill-root>/scripts/check_targets_renv.py <项目根> --project-state new --workflow-mode complex
Rscript -e 'renv::status()'
Rscript <项目根>/scripts/tests/smoke_test.R   # 内部使用 tmp/tests/<run-id>/_targets
Rscript -e 'targets::tar_make()'              # 轻量测试通过后才运行正式 store

# 已有项目
python3 <skill-root>/scripts/check_targets_renv.py <项目根> --project-state existing --workflow-mode preserved-existing
```

所有 Rmd 继续执行解读覆盖、解读质量、widget 可见性与图表可读性检查；按项目实际情况执行 R 语法/运行、Rmd 渲染和数字追溯。检查清单见 [`references/workflow_checklist.md`](references/workflow_checklist.md)，证据格式见 [`references/delivery_verification.md`](references/delivery_verification.md)。最低验收包括：模式与理由可复述；renv 状态可信；测试真实执行且原项目、`raw/`、正式 products/reports 和正式 targets store 未被测试污染；custom products 路径全流程一致；缓存损坏不误命中；已有项目未隐式迁移；跳过项不写成通过。

### 失败与恢复

- 缺少 `luckyBase` 或新项目缺 renv 资产：停止并补齐明确前提，不静默换包管理逻辑。
- simple 出现复用、昂贵步骤、局部失效或恢复需求：评估升级到 complex，不扩展自制调度器；不得无理由自动降级 complex。
- 轻量测试失败：按环境、数据、路径隔离、代码、科学断言、渲染或外部服务分类，最小修正后重跑真实受影响链；权限、网络、数据授权或依赖无法满足时记录外部阻塞和未验证项，不伪造成功。
- complex 测试 store 指向 `_targets/`，或测试写入正式 products/reports/raw：停止并隔离后重跑，先确认正式路径未变化。
- 缓存不完整、哈希不符或无法解析：视为 miss，保留证据并重算必要路径；不手工伪造 `SUCCESS`。
- Rmd 渲染失败：保留计算产品，从报告层恢复，不重跑无关计算。
- 已有项目冲突：不覆盖、不迁移；继续使用原入口，只做授权范围内的增量修改。

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

- 只在授权范围内只读盘点 `raw/`；不得修改、覆盖或向其写入，也不在日志中记录绝对私有路径、凭据或不必要原始值。
- 不因模板存在就创建全部文件；模式、缓存边界和目录由真实需求决定。
- 不把业务统计规则写入通用 checkpoint helper；helper 只处理路径、摘要、身份、完整性与安全落盘。
