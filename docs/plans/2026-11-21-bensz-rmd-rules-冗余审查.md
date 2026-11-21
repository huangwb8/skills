# bensz-rmd-rules：运行链路与冗余审查

审查对象是 `skills/beta/bensz-rmd-rules` 的当前工作树，`config.yaml` 声明版本 0.30.2，基线为 `eaeb6d7`，包含审查开始时已有的未提交修订。一共 70 个受版本控制的文件：根目录 5 个，参考 Markdown 28 个，脚本 16 个，模板与资产 21 个。本轮不修改目标 Skill。

## 判断

核心设计成立，应该保留：低成本分析走 simple，昂贵、可增量的流水线交给 targets；renv 锁定新项目的 R 依赖；结果能够从受保护输入和正式入口重建；关键统计结论能回到计算产品。复杂度主要来自外围：同一规则在四五份文件中重复声明；用语言特征的打分规则模拟科学验收；HTML 样式和测试框架被抬升为默认分析依赖。

旧自制缓存不是当前的负担。提交 `fc14b79` 已删除编号 runner、`checkpoint_helpers.R`、`SUCCESS` 和 `preserved-existing` 模式。仍在代码里的旧接口是 `check_targets_renv.py --mode` 及等价 JSON `mode`；其它大多是散落各处的反复声明和旧示例。已有项目保留现有入口是一条授权边界，建议保留。

## 这些文件怎样协作

**Agent 决定流程，脚本不会自行串起来。** [SKILL.md](../../skills/beta/bensz-rmd-rules/SKILL.md#L42) 是 Agent 的调度说明：先读配置、根据复杂度和现有项目的授权范围做选择，按需读参考，再挑模板、填入实际分析并明确入口。没有入口程序把所有 Markdown、脚本和配置组装成统一运行时。

| 阶段 | Agent 读取或调用什么 | 下一步消费什么 |
| --- | --- | --- |
| 立项 | `SKILL.md`、`workflow_modes.md`、`rebuild_contract.md`；`check_targets_renv.py` 只读盘点 | Agent 用真实重算成本和依赖选择模式，记录原因。CLI 的 `auto` 只看有无 `_targets.R`，空目录默认解析为 simple，并以缺骨架报 fail；这不代表不宜采用 complex。 |
| 计算 | simple 从一条正式 R/Rmd 入口读输入；complex 从 `_targets.R` 调 `tar_source("R")`，把输入文件及分析参数挂进 DAG | simple 可整体廉价重跑；complex 交由 targets 维护 `_targets/` 和失效状态，结果由 `tar_read()`/ `tar_load()` 或持久化科学产品供下游使用；`analysis-plan.yaml` 只供人读。 |
| 报告 | `statistical_inference_protocol.md` 管能估计什么、如何估计；解读资料管如何说明；Rmd 用 knitr、Pandoc 渲染 | 关键数字引用完整结果中的估计值、适用的 CI/p/q 和方法；Rmd 展示参数不反向改变研究估计。HTML 样式、DT 和静态图资产独立于计算。 |
| 验证 | 项目里的 `scripts/tests/smoke_test.R` 调同一正式入口，选合成 fixture 或授权子集，路径和 store 指向单次运行目录 | 以真实结果断言、文件存在/可读、复用证据及恢复场景决定能宣称什么。各 Python/R checker 产生预检线索；另有 `scripts/test_*.py` 回归 Skill 自己的代码和模板。 |

例如，计算一次昂贵队列模型并交付两份报告时，正式图把队列文件声明为 file target，模型拟合放在 `R/`，两份报告读同一个结果对象。报告单独重渲染前查计算是否仍有效，HTML 丢失可单独补出；队列同路径替换后则应重算受影响模型。一个小表的描述性 Rmd 直接读正式输入和完整重渲染即可，冷重建无需 targets。两个例子都要用计算结果判断结论；正则检查不会判断统计方法、样本或区间是否正确。

## 优先处理的发现

### 1. 默认模板的使用路径没有闭合

- [bootstrap_liquid_glass.py](../../skills/beta/bensz-rmd-rules/scripts/bootstrap_liquid_glass.py#L81) 是样式复制器，却附带环境、绘图工具、DAG 和分析计划开关。实际运行全部可选开关返回 `11/11 copied`，仍不含 complex Rmd 硬要求的 `templates/plot_delivery_helpers.R`；`--with-extras` 会复制 DT helper，但另外的绘图 helper 漏掉了。脚本也不生成 Rmd、测试或真实 renv 环境，这可以接受，但不能把它当作完整的项目初始化入口。当前复制器把源文件缺失和已有目标跳过都汇总为计数，退出码始终为 0。
- [Rmd_template.Rmd](../../skills/beta/bensz-rmd-rules/templates/Rmd_template.Rmd#L65) 先把预览 helper 标成可选，接着缺失即报错；即使报告一张静态图也没有，仍要提供 `BENSZ_TASK_ROOT` 或 `params.plot_run_dir` 才能通过预览初始化。若把临时 JPG 用作正式 HTML 的图片来源，重建还会依赖任务工作区。两份 Rmd 都默认引用 Liquid Glass 的两个资产，与 simple 的低成本、少依赖定位冲突。
- simple 的 [真实渲染回归](../../skills/beta/bensz-rmd-rules/scripts/test_rebuild_contract.py#L171) 使用实际 simple 模板并补入结果断言；同文件的 [complex 报告回归](../../skills/beta/bensz-rmd-rules/scripts/test_rebuild_contract.py#L94) 使用自写短报告。它能证明隔离 store 可供报告读取，不能证明内置 complex 报告能沿文档步骤完整渲染。
- 建议保留普通 HTML 为可独立复制的起点。Liquid Glass、DT、PDF 视觉预览按交付选择；选中时由一个入口复制所需资产。用真实的内置 complex Rmd 做一次端到端验收，或清楚标为需要裁剪的示例。建议把 JPG 视觉核查作为渲染后的操作，将正式 HTML 图片来源放在能由正式入口重建的位置。

### 2. 正式环境有隐藏安装和不必要的职责

- [00.Environment.R](../../skills/beta/bensz-rmd-rules/templates/00.Environment.R#L19) 无条件加载 luckyBase，并调用 `luckyBase::Plus.library("yaml")`，但此模板不读取 YAML。核查本机 luckyBase 0.2.0 的函数体：缺 pacman 会调用 `install.packages("pacman")`，随后对传入的包调用默认 `install=TRUE` 的 `pacman::p_load()`。这是依赖缺失时的真实行为，与 [重建契约](../../skills/beta/bensz-rmd-rules/references/rebuild_contract.md#L30) 规定的运行时不静默安装冲突；审查未触发安装来验证这一分支。
- 同一入口还做系统字体发现、showtext 可选配置、正式路径解析和测试路径判断。计算步骤不需要常规扫描系统字体；`candidate_r` 分支只含注释，示例却将全局函数存在性作为算法替换开关。一个本地脚本若确实参与正式分析，应作为显式输入/代码依赖纳入项目，不能按交互会话载入情况换算法。
- 建议从环境模板删除无消费的 yaml 预加载，正式执行只检查已声明依赖并以 `pkg::fn()` 使用；将安装限制在初始化/恢复。保留 luckyBase 中确实需要且已锁定的领域能力（如需要时做 ID 转换）。CJK/图形配置放绘图侧；保留路径隔离，但可考虑在临时项目副本中用同一套正常目录，从而减少给每个正式项目复制测试专属路径协议。

### 3. 汇总文件很长，能验证高风险错误的检查反而不够集中

- [解读覆盖](../../skills/beta/bensz-rmd-rules/scripts/check_figure_table_interpretation.py#L231) 根据 R chunk 中的调用模式猜哪个块出图/表，再向后找正文，按词数、标记和语言特征打分。调用 `ggsave()` 不等于 HTML 有输出；动态循环、助手函数或别处组装的图容易漏检。同一段邻近正文也不自动绑定到正确图表。默认不因覆盖失败退出非零，配置 `required_layers` 读出来就丢弃。
- [解读质量](../../skills/beta/bensz-rmd-rules/scripts/check_interpretation_quality.py#L697) 是另一套解析和正则：内联 R 至少三处、当前观察句至少三句、套话、标题、粗体和后续动作；默认失败退出 2，`--strict` 再增加要求。实测一段只有清晰描述和不可估计理由的英文短报告因两个计数失败。这类检查可提示遗漏，但控制不了数值真伪和 CI/检验有效性，还可能推动小报告填充不必要的文字。
- [figure_interpretation_criteria.md](../../skills/beta/bensz-rmd-rules/references/figure_interpretation_criteria.md#L23) 没有现行入口链接，仍写 100 中文字符/50 英文词、四层关键词和强制 strict；现行配置是 80/40、一般解读词、默认非阻断。[SKILL.md](../../skills/beta/bensz-rmd-rules/SKILL.md#L102) 已正确降格为启发式，建议以这条边界统一 README 和 references。
- [check_htmlwidget_visibility.py](../../skills/beta/bensz-rmd-rules/scripts/check_htmlwidget_visibility.py#L160) 检查 widget 是否只赋值、被不合适包装或不是 chunk 最终值，和图表解读是不同问题，值得保留有代表性的 DT/plotly 规则与真实 HTML 渲染补查。
- 建议文本检查默认只报告异常。确需严格审查时，用明确的图表 ID 对应结果段落，以及逐项验算关键结论的数值、来源和统计设计。不要为了复用脚本另造 DSL 或完整 Rmd 解析框架。

### 4. 两套 PDF 预览实现重复，默认检查不等于真正可读

[check_plot_readability.R](../../skills/beta/bensz-rmd-rules/scripts/check_plot_readability.R#L54) 和 [plot_delivery_helpers.R](../../skills/beta/bensz-rmd-rules/templates/plot_delivery_helpers.R#L82) 分别维护 PDF→JPG 后端链、任务目录创建、失败兜底；两份可写性 probe 都无调用。两套均有未加引号的路径参数直接传 `system2()` 的后端。本机用普通文件名转换成功，带空格的等价 PDF 经检查器转换失败；R helper 走 pdftools 时可能避开该问题。保留一个转换实现并让 CLI 复用，或将转换移到已有图像工具。文件体积、文本层、像素和裁边仅能发出线索，不能检查轴刻度、字体大小、标签密度等；`config.yaml:plot_readability` 的阈值也没有接进检查器。发布前的人眼检查仍有独立价值。

### 5. 验收应该绑定真实产物，避免复制整套工程框架

- [test_harness.R](../../skills/beta/bensz-rmd-rules/templates/tests/test_harness.R#L103) 有实质用途：隔离路径、拉起干净 R、验证正式文件不变、保留退出和断言证据。这不是旧 identity 缓存机制。现实现会在每轮前后递归哈希全部正式 `raw/`、产品、报告和 store；轻量输入只缩减分析量，未缩减这部分 I/O。前后摘要也只能发现持久变化，不能阻止中途写原目录。更可靠的默认边界是只在授权的临时项目副本中执行，输入使用 fixture 或最小授权快照。
- 现行 smoke 是起点。simple 执行两遍并要求项目提供 `assert_results.R`；complex 验证 unchanged rerun、补出示例 RDS、冷重建，DAG 外报告要显式传入，项目特有科学断言、同路径输入改变和迁移须补充。缓存保留的 `missing_delivery=PASS` 在模板中验证的是产品文件，不等价于“所有报告和交付都做过丢失恢复”。未执行场景不要覆盖为通过。
- [serial_review_protocol.md](../../skills/beta/bensz-rmd-rules/references/serial_review_protocol.md) 的三种检查视角有价值。对任何小分析默认串行拉起三名独立审查者成本过高；建议普通项目一次聚焦核对，高成本、关键推断或复杂恢复才提升独立审查级别。重建、科学断言和无关节点不重算按风险择取实际有判别力的证据，保留 `NOT_RUN` 的区分。
- [check_targets_renv.py](../../skills/beta/bensz-rmd-rules/scripts/check_targets_renv.py#L163) 与 [check_pipeline_contract.py](../../skills/beta/bensz-rmd-rules/scripts/check_pipeline_contract.py#L82) 重复断言 simple 无 DAG、complex 有 `_targets.R`、`R/` 与 `tar_source("R")`。前者还检查锁文件和测试入口，后者的独有工作是报告消费检查。建议由一个 CLI 提供盘点/交付预检，给报告传明确的交付路径；不要把项目里所有候选 Rmd 的语法命中等同于报告依赖已验证。
- [validate_paths.R](../../skills/beta/bensz-rmd-rules/scripts/validate_paths.R#L149) 还以“文件中同时存在 I/O 与任一个 exists”作为有校验的代理，与规范反对重复防御冲突；递归不排除测试、依赖或产物目录，且 CLI 最后不按 findings 设置退出码。若保留，缩成可行动的可移植路径 lint，依赖运行证据判断输入和输出是否隔离。

## 文档和资产的处置清单

| 现有 Markdown | 实际用途与建议 |
| --- | --- |
| `SKILL.md`、`README.md`、`README_EN.md`、`CHANGELOG.md` | Agent 入口、双语用户入口、历史分别有用。README 链接到真正规则；旧版本行为仅留历史记录。 |
| `workflow_modes`、`hybrid_architecture_guide`、`hybrid_architecture_examples`、`analysis_workflow_cache` | 同一模式、目录、缓存、恢复和可选并行写了四遍。合成一份模式与数据流参考，保留一个 simple 和一个 complex 实例。 |
| `rebuild_contract`、`lightweight_testing`、`workflow_checklist`、`delivery_verification`、`serial_review_protocol` | 前两份分别是业务验收和执行做法，值得保留。将清单、证据格式并入测试参考的交付小节，审查独立性按变更风险配置。统一报告 HTML 与图表的产出路径；有些架构树说 HTML 在 `reports/`，入口说放项目根。 |
| `behavioral_acceptance` | 18 个维护场景，属于维护者参考，不应在每个分析任务加载；保留最有区分度的结构、迁移和科学结果反例。脚本回归和行为场景并非二选一。 |
| `statistical_inference_protocol`；`metric_explanation_protocol`、`four_tier_interpretation_framework`、`interpretation_templates`、`interpretation_narrative_examples`、`expert_discussion_template` | 保留统计推断契约独立；其余合并成报告解读参考，包含指标首次解释、图表结果证据和两三个对照示例。Top 1–3、后续 2/3 条按实际研究需要使用。 |
| `figure_interpretation_criteria`、`numeric_accuracy_verification`、`code_block_explanations` | 现行 Skill/README/参考没有入链。第一份漂移，后两份分别与 Rmd 数值追溯表和推断方法叙述重复。将有价值的规则各归一处，三文件可退役。 |
| `code_style_guide`、`no_overdefensive_code`、`cross_platform` | 合并为 R 实现参考。保留授权目录、编码、错误边界和显式依赖；压缩通用 if/else 教学和重复示例。 |
| `plot_quality_standards`、`plot_language`、`htmlwidget_visibility_rules`、`liquid_glass_theme_guide` | 语言规则并入可视化参考；widget 检查可合并进去但保留实例。主题指南独立，成为明确的 opt-in 入口。 |
| `gene_id_guidelines`、`candidate_r` | 注释映射、歧义和稳定 ID 是组学专属知识，按任务载入。后者压成“显式、已授权的项目本地依赖”，去掉专名分支和按函数是否碰巧加载的替换建议。 |

| 脚本或模板 | 实际消费者与建议 |
| --- | --- |
| 两个项目预检；覆盖、质量、widget 三个 Python 报告检查；两个 R 检查 | 消费者是 Agent 或直接调用 CLI 的项目维护者，没有集中 orchestrator。合并两项项目预检的共同职责；简化报告文字启发式；widget 保留，路径与 PDF 预览明确为提示。 |
| `bootstrap_liquid_glass.py`、`check_rmd_template_yaml.py` | 前者只复制资源；后者只供维护者校验配置与两份 Rmd 顶部 YAML 的一致性，当前通过。若 base YAML 和主题 YAML 分开，改测各模板能真实渲染，考虑以模板为头部唯一来源。 |
| 七个 `test_*.py` | `test_targets_renv` 检查 CLI 与模式；`test_dual_mode_integration` 查基本脚手架/双模式实际执行；`test_rebuild_contract` 查恢复/隔离；`test_code_ligature_rendering` 和 `test_toc_hover_stability` 属主题；`test_metric_explanation_protocol` 和 `test_windows_cli_and_dt_helper` 覆盖文本、DT 和编码回归。保持维护测试入口与用户项目测试模板分离；有真实历史故障且能观察输出的用例优先保留。当前重建套件的项目副本没有集中清理，运行后留有项目和 renv 依赖副本；可共享一套锁定库，默认清理成功现场，仅按需保留失败现场。 |
| `00.Environment.R`、`renv/activate.R`、`_targets.R`、`R_data_template.R`、`functions_template.R`、`analysis_plan_template.yaml` | 保留环境/计算最小模板。renv 官方生成激活脚本优先，随 Skill 的七行版本只是依赖现有 renv 的起点。未入链的 `functions_template.R` 与已接线的 `R_data_template.R` 重复，前者可退役。`_targets.R` 的 `pipeline_contract` 节点只返回三条说明，没有消费者，可移回注释；计划只记需求、估计对象、验收及入口，不手抄 DAG，也不自动复制空计划。 |
| 两份 `Rmd`、`datatables_helper.R`、`nature_colors.R`、`nature_theme.R`、`complexheatmap_template.R`、`plotly_template.R`、`plot_delivery_helpers.R` | simple/complex 分开保留，各自只放必需的计算/消费与结果例子；具体图形资产按需复制。DT helper 的最后表达式和图表字体可保留成真正可查的行为。 |
| Liquid Glass 的 CSS 与 HTML | 共 1,990 行；负责样式、暗色、桌面/移动目录、图片放大、复制、缩放/滚动持久化。属于报告可选增强，不是统计或可复现依赖。copy 的 `file://` 兼容回退可能仍有现实价值，不能简单按“旧浏览器 API”删除；主题也有已知交互回归测试。 |
| 五个 `templates/tests/*.R` | 两个正式入口调用模板、两种测试数据准备法，一个共享 harness。保留两个业务执行样例与隔离意识，减少通用框架内的工程协议；科学断言始终由项目提供。 |

## 配置与兼容如何收口

仓库内三个生产 Python 脚本实际读取 Skill 的 `config.yaml`：解读覆盖、解读质量和模板 YAML 一致性。两个项目预检使用代码中独立默认值，R/targets/报告也不加载 Skill 的整份 YAML。它并非全局运行配置，仍可供 Agent 阅读。建议保留技能元数据、被实际消费的配置和少数易变的项目约定；其余归到规则参考。典型清理候选：无人消费的 `analysis_workflow.contract_version`、仅一个合法值的图表质量枚举、未接到 R checker 的可读性阈值、两份 Rmd 都没有运行时使用的 `min_sample_n` 与多项 `interpret_*` 参数。不要为消费这些键再引入 runtime 或把固定设计变成可配开关。

对旧接口分三类处理：

1. **可删除候选：** 仓库当前没有非测试的 `--mode` 调用或 JSON `mode` 消费者。确认外部脚本后，去掉 deprecated 别名、错误冲突分支及相应测试。不能仅凭本仓库搜索断言外部没有消费者。若保留双写，也应宣布退役期限。
2. **仅需收敛措辞：** `pipeline` 还是当前公开文档中的 complex 别名，不代表另一条执行路。可统一术语为 complex 并保留很薄的 alias，或把退役与未来显式版本变更同步；旧编号示例换为 `R/analysis_functions.R`、`report.Rmd`，编号文件无需保留为新模板。
3. **应该保留：** 不自动迁移 existing；Windows 输出编码/路径、中文字体、浏览器的本地文件复制等有现行使用场景。兼容机制应放所属边界并以实际用例验证。

## 建议的整改顺序与验收

1. **先修使用链：** 对 simple 和 complex 各保留一个从新目录到报告的最小配方；解决 complex helper 缺失、生成普通 HTML 时不依赖工作区、运行时装包和预览空格路径。用真实随附模板、正式入口和干净 R 执行。
2. **再做减法：** 保留唯一模式说明、统计推断契约、重建契约、轻量测试与按需的报告/图表参考；把行为场景和主题放到各自入口。删除空节点、孤立骨架、废键；合并预检和 PDF 转换的重复代码；别名退役前确认外部消费者。
3. **最后压缩门槛：** 小分析用同入口 fixture 和少量科学断言；复杂/高成本项目追加交付丢失、输入失效、中断与迁移证据。用正确且很短的报告、确实缺说明的复杂报告做反例，确认文本提示不奖励填字数，也不把提示当科学验收。

## 本轮验证

- macOS 上使用现有 R 包库运行 Skill 的 30 项回归，全部通过，无跳过；包括 simple/complex 的合成输入、隔离 store、重建和 Chromium 目录交互。模板 YAML 一致性通过。
- 定向验证确认 bootstrap 复制遗漏、短报告被文本检查误拦、含空格的 PDF 转换失败。luckyBase 的安装行为通过本机函数定义核实，没有触发缺包安装。
- Linux 和 Windows 未实跑；没有对用户项目正式数据或系统安装副本执行验证。
