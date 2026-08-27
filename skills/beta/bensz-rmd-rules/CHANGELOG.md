# Changelog

All notable changes to bensz-rmd-rules will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [Unreleased]

### Added

- `references/metric_explanation_protocol.md`：新增面向弱背景读者的指标解释协议，定义常用指标白名单、不常用指标兜底判定、指标导读表及首次出现完整解释规则。
- `plans/TOC移动支持-v202603011129.md`：新增 Liquid Glass 的 TOC 移动端支持优化计划（sticky 折叠目录条、跳转后自动收起、锚点偏移与触控可用性等）。
- `tests/TOC移动支持-v202603011129/`：新增对应轻量测试会话（PLAN/REPORT + demo.Rmd/render.sh + 静态断言脚本 + 3 组 viewport 截图证据，含“存储不可用”模拟）。
- `templates/plot_delivery_helpers.R`：新增“PDF 交付 + JPG 预览”最小 helper（`bensz_run_dir()` / `bensz_pdf_to_jpg()`），优先使用 poppler/ImageMagick，R 依赖可选。
- `tests/图片可读性-v202603011109/`：新增轻量测试会话（PLAN/REPORT + 3 个自生成 fixture），覆盖“PDF 产出 + 预览生成 + checker 渲染”闭环。

### Changed

- `SKILL.md` / `README.md` / `templates/Rmd_template.Rmd` / `references/four_tier_interpretation_framework.md` / `references/workflow_checklist.md` / `references/delivery_verification.md`：专家级解读默认假定读者背景较弱；存在不常用指标时，要求先给“指标导读”表，首次出现解释定义、原理、选用理由、判读方向与不确定性，后续出现改为简洁结果解读。
- `scripts/check_interpretation_quality.py` / `config.yaml`：教学口吻检测移除“用于评估/反映关系/当……时……”等中性指标解释表达，只保留模板化提示语；新增 `qa/test_metric_explanation_protocol.py` 防止必要的首次解释被误拦截。
- `config.yaml`：新增 `metric_explanation` 默认分类与解释策略，并将版本号 `0.21.3 → 0.22.0`。
- `config.yaml`：版本号 `0.21.1 → 0.21.2`；JPG 预览 run 目录默认从 `/tmp/bensz-rmd-rules/` 迁移到当前项目下 `.bensz-api/skills/bensz-rmd-rules/`。
- `SKILL.md` / `templates/Rmd_template.Rmd` / `templates/plot_delivery_helpers.R` / `scripts/check_plot_readability.R`：同步更新 PDF→JPG 预览中间目录口径，避免默认写入系统 `/tmp`。
- `SKILL.md`：新增“参数面向用户 + PDF 交付 + JPG 视觉自检”硬约束口径，并补齐推荐落地方式与 YAML params（`plot_run_dir/plot_preview_dpi`）。
- `SKILL.md`：补充“HTML 表格默认使用 DT（DT::datatable）渲染”的规范口径（用户另有指定时以用户要求为准）。
- `SKILL.md` / `templates/Rmd_template.Rmd`：补充“HTML 展示图默认使用由 PDF 渲染得到的 JPG 预览图，以保证 HTML 与 PDF 比例一致；展示可用 out.width 缩小但避免 out.height 失真”的规范口径。
- `SKILL.md` / `templates/*.R*` / `plans/Nature级别图-v202601270654.md` / `references/plot_language.md`：图表默认不在图内使用 `title/subtitle`（例如 `ggplot2::labs(title=..., subtitle=...)`、`ggtitle()`、`plotly::layout(title=...)`），改用文件名 + `.Rmd` 标题/图注承载语义；仅在用户明确要求或确有必要时才添加。
- `templates/Rmd_template.Rmd`：在模板中加入“集中参数块 + PDF 交付 + JPG 预览”的示例口径，并在 `plot-style` chunk 约定 `run_dir` 以支持预览生成。
- `scripts/check_plot_readability.R`：新增 `--render-jpg/--out-dir/--dpi/--page`（轻依赖渲染预览 + proxy 指标），保留原有仅检查 PDF 的用法不变。
- `templates/liquid_glass_theme.css`：TOC 窄屏（≤1024px）升级为“顶部 sticky 折叠目录条”，并补齐触控可用性（按钮/链接 ≥44px hitbox）与移动端锚点跳转偏移口径，降低跳转遮挡与滚动后不可达的问题。
- `templates/liquid_glass_lightbox.html`：窄屏下点击任意 TOC 条目后自动收起（并持久化折叠态），避免跳转后遮挡；同时补充 `resize/orientationchange` 下的按钮文案同步兜底。
- `references/liquid_glass_theme_guide.md` / `README.md`：同步更新“移动端目录（窄屏）”口径（sticky + 点击后自动收起 + 跳转偏移）。
- `config.yaml`：新增 `params.plot_run_dir/plot_preview_dpi`（与模板同步），并更新版本号 `0.20.0 → 0.21.1`（Single Source of Truth）。
- `SKILL.md`：对齐“不过度防御”边界口径（允许 I/O 边界与硬前提做显式检查+stop，避免冗余包/函数检查），并澄清 Liquid Glass YAML 字段的单一真相来源。
- `config.yaml`：澄清 `references/liquid_glass_theme_guide.md` 为说明文档，具体字段以 `rmd_template.yaml_header` 为准。
- `templates/Rmd_template.Rmd`：补齐 `templates/datatables_helper.R` 缺失时的 fail-fast 提示（指向 `bootstrap_liquid_glass.py --with-extras`）。

### Fixed

- `templates/liquid_glass_theme.css`：修复桌面端动态 TOC 悬停展开时偶发抖动的问题。移除圆角半径过渡，避免展开动画改变鼠标命中边界并触发 `mouseenter`/`mouseleave` 振荡；版本号 `0.22.0 → 0.22.1`。
- `scripts/*.py`、`scripts/*.R` 与可执行 R 模板统一使用 `[PASS]` / `[FAIL]` / `[WARN]` ASCII 状态前缀，修复 Windows GBK 控制台因 emoji/符号不可编码而在成功或失败分支崩溃的问题；版本号 `0.21.2 → 0.21.3`。
- `figure_interpretation_check.check_patterns.table_generation` 补齐推荐 helper `render_dt_output()` / `render_dt()`，使图表解读覆盖检查与 htmlwidget 可见性检查采用一致的 DT helper 边界。
- `templates/liquid_glass_theme.css`：修复 Liquid Glass 主题对 Plotly 使用过宽的 `.plotly` 选择器会误伤 Plotly.js 内部节点，导致“双层背景/额外阴影与内边距/图像像浮在背景上”的观感问题；改为仅作用于 `.plotly.html-widget` 外层容器并采用更保守的默认样式。
- `scripts/check_figure_table_interpretation.py`：修复将 `results='hide'` 误判为“隐藏输出”导致的漏检；新增 `fig.show='hide'` 与 `fig.keep='none'` 的隐藏判定。
- `scripts/validate_paths.R`：修复仅扫描 `.Rmd` 与“行首绝对路径”的检测盲区；降低“路径拼接”误报；重复运行时重置结果避免累积旧告警。

## [0.20.0] - 2026-02-13

### Added

- `plans/结果解读-流于表面-v202602130728.md`：新增优化计划，将“结果解读”硬约束从“写作枷锁”调整为“交付前质检门禁”，并明确保留/放松项的取舍口径。
- `tests/结果解读-流于表面-v202602130728/`：新增轻量测试会话（PLAN/REPORT + 4 个最小 Rmd fixture），覆盖探索期通过、覆盖缺失失败、不可追溯数字失败、严格模式叙述式通过。

### Changed

- `SKILL.md`：将“结果后解读”从“写法强制”调整为“两阶段门禁”口径；明确硬门禁（证据锚定/数字可追溯/覆盖不漏项/禁止代码生成解释）与推荐结构（四层/Top/不确定性/可执行后续）；补充探索期/交付期自检命令。
- `config.yaml`：
  - `figure_interpretation_check`：默认 `strict_mode=false`（仅报告），交付期用 `--strict` 显式 Fail Fast；marker 默认改为更中性词（不再隐性要求四层标签）；并将 `min_cjk_chars/min_en_words/min_content_elements/require_markers` 作为默认参数来源。
  - `interpretation_quality_check`：放松零容忍阈值（teaching/vague/actionability）；默认不强制 Top/不确定性/可执行后续；新增“不可追溯字面数字”启发式门禁与白名单。
  - 版本号 `0.19.0 → 0.20.0`（Single Source of Truth）。
- `scripts/check_interpretation_quality.py`：默认不再强制 Top/不确定性/行动建议；`--strict` 下强制；新增“不可追溯字面数字”检测并输出行号示例，降低解释性表达误杀与模板化填空。
- `scripts/check_figure_table_interpretation.py`：marker/长度/要素门槛从 `config.yaml` 读取为默认值（CLI 可覆盖）；支持 `require_markers` 配置；默认 marker 口径改为更中性词。

### Fixed

- **Liquid Glass TOC 点击定位精确度**：修复目录（TOC）链接点击后标题定位贴边或不够精确的问题
  - `templates/liquid_glass_theme.css`：为所有标题（h1-h6）添加 `scroll-margin-top: 2rem`，确保锚点跳转时预留顶部空间
  - 测试验证：`tests/liquid_glass_demo.html` 已包含修复后的样式
- **Liquid Glass 代码块复制工具条样式**：将“复制/Hide”工具条改为代码块右上角浮动胶囊样式，减少空白占用并统一按钮视觉
  - `templates/liquid_glass_theme.css`：工具条改为 `position: absolute` 浮动展示；为工具条按钮提供一致的玻璃拟态样式；为代码块增加顶部内边距以避免遮挡首行
  - `templates/liquid_glass_lightbox.html`：复制按钮不再依赖 Bootstrap 的 `.btn*` class，避免被主题/外部 CSS 干扰
  - 测试验证：`tests/代码复制样式优化-v202602102004/`（PLAN/断言脚本/REPORT）

## [0.19.0] - 2026-02-10

### Added

- Liquid Glass：代码块右上角新增“复制/Copy”按钮（支持 `code_folding` 场景，将按钮放在 Hide 左侧；并兼容 Clipboard API 与 `execCommand('copy')` 降级）。
- `tests/代码复制功能-新增-v202602082340/`：轻量测试会话（PLAN/脚本断言/产物证据）。

### Changed

- `templates/liquid_glass_theme.css`：新增代码块工具条与复制按钮样式（玻璃拟态 + 交互反馈）。
- `templates/liquid_glass_lightbox.html`：新增代码块复制按钮注入逻辑（after_body）。
- `references/liquid_glass_theme_guide.md`：补充复制按钮使用说明与兼容性说明。
- `config.yaml`：版本号 `0.18.0 → 0.19.0`（Single Source of Truth）。

## [0.18.0] - 2026-02-09

### Added

- `tests/结果解读-流于表面-v202602091747/`：轻量测试会话，覆盖“机械四段式模板”与“空泛句式缺少本地证据”两类反例，并提供正例 Rmd。
- `config.yaml:interpretation_quality_check`：新增机械模板检测与空泛句式缺少证据检测（可配置开关、阈值与正则）。

### Changed

- `SKILL.md`：将“结果后解读”从“结构门槛”进一步收敛为“思考路径 + 可证伪推理 + 可执行后续”，并显式禁止机械模板化四段式。
- `references/interpretation_narrative_examples.md`：从“替换变量名的示例库”重写为“专家解读思维示例（非模板）”，强调推理链条与风险边界。
- `references/interpretation_templates.md`：强化“写作前列要点、交付时合并为叙述”的使用方式，增加解读前四问与反机械模板说明。
- `scripts/check_interpretation_quality.py`：新增机械四段式模板识别与空泛句式缺少本地证据检测；相关阈值默认从 `config.yaml` 读取。
- `config.yaml`：将结果解读检查从“硬黑名单”迁移到“反模板 + 证据邻域”口径，并更新版本号 `0.17.9 → 0.18.0`（Single Source of Truth）。

### Fixed

- `scripts/check_interpretation_quality.py`：修复 `config.yaml` 中空列表（如 `blacklist_patterns: []`）会被误回退到内置默认值的问题。

## [0.17.9] - 2026-02-09

### Added

- `tests/结果解读-流于表面-v202602091308/`：轻量测试会话与证据（PLAN/REPORT + 正反例 Rmd）。
- `references/interpretation_templates.md`：新增“核心结论（证据链收敛）”模板（面向 cohort/亚组收敛叙事）。
- `references/interpretation_narrative_examples.md`：新增“核心结论（证据链收敛）”连贯叙述式示例段。

### Changed

- `scripts/check_interpretation_quality.py`：强化“教学口吻 / 不可落地后续 / 模板化分层标签”静态阻断，并支持 `--strict` 做更强反模板化检查；默认从 `config.yaml:interpretation_quality_check` 读阈值与开关。
- `SKILL.md`：明确“连贯叙述式”为默认交付形态，并补充 `check_interpretation_quality.py --strict` 用法。
- `README.md`：补充“避免结果解读流于表面”的推荐默认策略与自检命令。
- `config.yaml`：补齐 `rmd_template.yaml_header.params`（与模板一致）并扩展 `interpretation_quality_check` 配置；版本号 `0.17.8 → 0.17.9`。
- `templates/Rmd_template.Rmd`：补齐解读相关 `params` 与“结果解读”占位段，减少“有结果无收敛解读”的漏项风险。

## [0.17.8] - 2026-02-09

### Changed

- **B 轮 P1/P2 遗留问题修复**
  - `SKILL.md`：从 508 行精简到 486 行（≤500 行），将"禁止通用套话"详细黑白名单表格下沉到 references，仅保留核心口径和引用链接
  - `config.yaml`：新增 `interpretation_quality_check` 配置节，包含 blacklist_patterns（单一真相来源）
  - `scripts/check_figure_table_interpretation.py`：更新注释说明脚本默认值为降级方案，config.yaml 为真相来源
  - `config.yaml`：版本号 `0.17.7 → 0.17.8`
  - references 目录审计：所有 20 个文件均被引用，建议后续合并 `hybrid_architecture_guide.md` + `hybrid_architecture_examples.md`

## [0.17.7] - 2026-02-09

### Changed

- **A 轮一致性修复（v202602090010）**
  - `references/four_tier_interpretation_framework.md:58`：将"每句必须包含至少一个 `` `r ...` ``"改为"每句必须包含数值证据（优先 `` `r ...` `` 动态嵌入，或明确可追溯的字面数字）"，对齐 check_interpretation_quality.py 的实际检测行为
  - `references/no_overdefensive_code.md:56`：增加 00.Environment.R 存在性检查的白名单例外说明，解决与 Rmd_template.Rmd 的矛盾
  - `references/workflow_checklist.md:40`：新增 YAML 头一致性检查项，引用 `scripts/check_rmd_template_yaml.py`
  - `config.yaml`：版本号 `0.17.6 → 0.17.7`

- **B 轮质量检查（v202602090010）**
  - 完成 8 维度质量评估，得分 101/115（88%）
  - 确认 A 轮修复生效，无新增 P0 问题
  - 遗留 P1：SKILL.md 508 行超限、配置集中化；遗留 P2：references 文件数可精简

### Added

- **强化结果解读当前数据观察门槛**
  - `bensz-rmd-rules/SKILL.md`：在"结果后解读"章节新增"禁止通用套话"硬门槛（黑名单示例 + 强制要求 + 白名单示例）
  - `bensz-rmd-rules/references/four_tier_interpretation_framework.md`：将示例从"骨架版"改为"血肉版"，每句话都绑定 `` `r ...` `` 动态数值；新增"半成品解读"反例说明；将"当前数据观察"门槛从 2 句提升到 3 句
  - `bensz-rmd-rules/references/interpretation_templates.md`：增强"反模式"章节，新增典型模板化句式黑名单、专家级写作公式、示例对比表格
  - `bensz-rmd-rules/scripts/check_interpretation_quality.py`：新增 8 个教学口吻检测标记（如"用于判断"、"展示...的...形态"、"当...时...更支持"等）；将 `--min-current-observation` 默认值从 2 提高到 3
  - `bensz-rmd-rules/tests/结果解读-流于表面-v202602082340/`：问题修复的轻量测试会话（PLAN + REPORT）

- **TOC 动画问题记录**
  - `bensz-rmd-rules/plans/TOC动画优化-v202602052237.md`：记录动态浮动 TOC 的动画不自然问题与位置

- **Liquid Glass 目录（TOC）两种浮动模式：静态/动态**
  - `bensz-rmd-rules/templates/liquid_glass_theme.css`：新增动态浮动目录的收起/展开样式；静态模式下正文为目录预留空间
  - `bensz-rmd-rules/templates/liquid_glass_lightbox.html`：新增目录模式切换逻辑与目录头部（“静态/动态”按钮），并在桌面宽屏下将 TOC 从 bootstrap 栅格中移出以释放正文空间
  - `bensz-rmd-rules/references/liquid_glass_theme_guide.md` / `bensz-rmd-rules/README.md`：补充用户侧切换方式与行为说明

- **HTML 视图状态保持（刷新后缩放 + 阅读位置尽量维持）**
  - `bensz-rmd-rules/templates/liquid_glass_lightbox.html`：新增内部缩放快捷键（`Ctrl/Cmd + (+/-/0)`）与刷新后 scroll 恢复逻辑（基于 `sessionStorage`）
  - `bensz-rmd-rules/references/liquid_glass_theme_guide.md` / `bensz-rmd-rules/README.md` / `bensz-rmd-rules/SKILL.md`：补充使用说明与故障排除口径

- **图表/表格解读覆盖检验（Fail Fast）**
  - `bensz-rmd-rules/scripts/check_figure_table_interpretation.py`：静态检测“有输出但无解读”的漏项（支持 `--strict` 阻断交付）
  - `bensz-rmd-rules/references/figure_interpretation_criteria.md`：覆盖检验口径与参数说明
- **YAML header 一致性校验（维护者用）**
  - `bensz-rmd-rules/scripts/check_rmd_template_yaml.py`：校验 `templates/Rmd_template.Rmd` 的 YAML header 是否与 `config.yaml:rmd_template.yaml_header` 一致
- **SKILL.md 渐进披露下沉文档**
  - `bensz-rmd-rules/references/htmlwidget_visibility_rules.md`：htmlwidget/DT/plotly 的 HTML 可见性硬规则与示例（从 SKILL.md 下沉）
  - `bensz-rmd-rules/references/numeric_accuracy_verification.md`：数字准确性验证章节模板与规范（从 SKILL.md 下沉）
- **轻量测试会话**
  - `bensz-rmd-rules/tests/v202602041511/`：脚本级静态检查（PLAN/REPORT + 样例 Rmd + 产物）
  - `bensz-rmd-rules/tests/放大或当位位置维持-v202602042153/`：视图状态保持（缩放/scroll）相关静态校验与 bootstrap 复现（PLAN/REPORT + 断言输出）

### Changed

- **Liquid Glass 图片/代码块居中观感修复**
  - `bensz-rmd-rules/templates/liquid_glass_theme.css`：补充 `div.figure` 包裹场景的居中样式，修复图片偏左
  - `bensz-rmd-rules/config.yaml`：版本号 `0.17.3 → 0.17.4`
  - `bensz-rmd-rules/tests/v202602051015/`：figure 包裹图片居中的轻量测试计划与报告

- **Liquid Glass 图片默认居中**
  - `bensz-rmd-rules/templates/liquid_glass_theme.css`：独立图片自动居中，避免移动端/桌面端左对齐观感
  - `bensz-rmd-rules/references/liquid_glass_theme_guide.md`：补充图片居中说明
  - `bensz-rmd-rules/config.yaml`：版本号 `0.17.2 → 0.17.3`
  - `bensz-rmd-rules/tests/v202602050940/`：图片居中的轻量测试计划与报告

- **Liquid Glass 目录移动端可折叠**
  - `bensz-rmd-rules/templates/liquid_glass_theme.css`：移动端目录折叠卡片样式、触控友好间距与安全区适配
  - `bensz-rmd-rules/templates/liquid_glass_lightbox.html`：窄屏下按钮改为“展开/收起”，并记忆折叠状态
  - `bensz-rmd-rules/references/liquid_glass_theme_guide.md` / `bensz-rmd-rules/README.md` / `bensz-rmd-rules/SKILL.md`：补充移动端行为说明
  - `bensz-rmd-rules/config.yaml`：版本号 `0.17.1 → 0.17.2`
  - `bensz-rmd-rules/tests/v202602050900/`：移动端目录折叠的轻量测试计划与报告

- **Liquid Glass 目录（TOC）字体层级更协调**
  - `bensz-rmd-rules/templates/liquid_glass_theme.css`：覆盖 tocify 默认的 subheader 12px，缩小 # / ## 的字号落差，使目录更易读

- **Liquid Glass 动态 TOC 动画节奏对齐**
  - `bensz-rmd-rules/templates/liquid_glass_theme.css`：统一容器过渡节奏并为内容显隐增加轻微延迟
  - `bensz-rmd-rules/config.yaml`：版本号 `0.17.4 → 0.17.5`
  - `bensz-rmd-rules/tests/v202602052300/`：轻量测试计划与报告

- **结果解读避免“教学口吻/通用套话”**：强化“当前数据观察”门槛，减少“流于表面”的解读
  - `bensz-rmd-rules/SKILL.md`：在“四层硬门槛”处新增“必须陈述本次结果具体观察”的硬门槛
  - `bensz-rmd-rules/references/interpretation_templates.md`：新增“反模式：模板化写作 vs 专家级写作”
  - `bensz-rmd-rules/references/four_tier_interpretation_framework.md`：Fail Fast Gate 增加“当前数据观察”项，并收敛示例的通用推断写法
  - `bensz-rmd-rules/references/interpretation_narrative_examples.md`：示例收敛教学式“用于判断”句式
  - `bensz-rmd-rules/scripts/check_interpretation_quality.py`：新增 `--min-current-observation`（默认 2）并在 PASS 输出 `current_obs`
  - `bensz-rmd-rules/tests/v202602082340/`：新增轻量测试（bad/good Rmd + 输出证据）
  - `bensz-rmd-rules/config.yaml`：版本号 `0.17.5 → 0.17.6`

- **交付前强制检查链路**：新增“图表/表格解读覆盖检验”作为交付前必跑步骤
  - `bensz-rmd-rules/SKILL.md`：新增强制命令与失败处理口径
  - `bensz-rmd-rules/README.md`：同步用户侧运行方式
  - `bensz-rmd-rules/config.yaml`：新增 `figure_interpretation_check` 配置段
  - `bensz-rmd-rules/references/workflow_checklist.md` / `bensz-rmd-rules/references/delivery_verification.md`：同步检查项

- **配置/模板口径对齐**
  - `bensz-rmd-rules/config.yaml`：明确 YAML header 的 SSOT 口径，并移除易误导的 `plot_quality.enforce_nature_level`；版本号 `0.15.1 → 0.16.0`
  - `bensz-rmd-rules/templates/Rmd_template.Rmd`：去除时间/品牌绑定叙事（iOS 26），并明确“模板 YAML 为便捷拷贝，需与 config 同步”
  - `bensz-rmd-rules/templates/liquid_glass_theme.css` / `bensz-rmd-rules/references/liquid_glass_theme_guide.md`：将主题描述改为时间无关的 glassmorphism 叙事

- **最小惊讶原则（模板副作用收敛）**
  - `bensz-rmd-rules/templates/00.Environment.R`：默认不自动启用 `showtext::showtext_auto(TRUE)`；改为显式开关/环境变量启用

- **配置集中化更安全**
  - `bensz-rmd-rules/scripts/check_figure_table_interpretation.py`：缺少 PyYAML 或 config 解析失败时输出清晰警告，避免“以为配置生效但实际静默回退”

- **SKILL.md 瘦身**
  - `bensz-rmd-rules/SKILL.md`：将长示例/模板块下沉到 references，并将主体收敛到 500 行以内

### Changed

- **Rmd 报告可追溯性**：在“数据概览”后新增 `## 关键函数、参数与源代码位置` 章节规范与模板
  - `bensz-rmd-rules/SKILL.md`：新增“章节结构（硬门槛）”与该章节的填写要求（关键过程/关键函数/关键参数与理由/源代码文件+行号）
  - `bensz-rmd-rules/templates/Rmd_template.Rmd`：新增对应章节模板与示例表格
  - `bensz-rmd-rules/README.md`：同步用户侧说明

- **templates/liquid_glass_theme.css**：增大解释类文字的字体大小
  - `p`（段落）：字体从继承 16px 调整为 1.05rem（约 16.8px）
  - `li`（列表项）：字体从继承 16px 调整为 1.05rem（约 16.8px）
  - `figcaption`（图片说明）：字体从 0.9rem 调整为 0.95rem
  - 所有解释类文字行高从 1.6 调整为 1.7，提升可读性

### Added

- **references/code_style_guide.md**：新增 R 代码风格指南（从 SKILL.md 下沉）
  - 核心原则：管道优先、向量化思维、函数式编程、数据驱动
  - 减少 if 语句使用：场景对照表（条件赋值/分类映射/数值替换/存在性检查/多分支逻辑）
  - 禁止防御性文件存在性检查：让代码在文件缺失时自然报错
  - 代码注释规范：代码块头部、分步注释、业务逻辑注释
  - 常见反模式：遍历+if、嵌套 if-else、防御性文件检查

### Changed

- **SKILL.md**："人类可读原则"章节重构
  - 移除详细的代码风格要求内容（基础代码风格、减少 if 语句使用、命名规范、代码注释规范）
  - 改为引用 `references/code_style_guide.md`，保留核心要点摘要
  - 遵循渐进披露原则，降低 SKILL.md 维护负担

- **templates/liquid_glass_theme.css**：新增 Liquid Glass HTML 主题（iOS 26 风格）
  - Glassmorphism 效果（背景模糊与半透明层次）
  - 流体渐变动画与有机色彩过渡
  - 弹性动效系统（类似 iOS 交互反馈）
  - 多层深度阴影营造空间感
  - 自动深色模式支持（根据系统偏好切换）
  - 保留完整的浮动目录功能
- **references/liquid_glass_theme_guide.md**：新增 Liquid Glass 主题使用指南
  - 快速开始教程
  - 设计特性详解
  - 组件样式展示
  - 自定义工具类说明
  - 故障排除与进阶定制

### Changed

- **config.yaml**：更新 `rmd_template.yaml_header` 配置
  - `theme: default`（满足 `toc_float` 的 rmarkdown 约束；主要视觉由 Liquid Glass CSS 覆盖）
  - 仅使用 `css` 引用 Liquid Glass 样式（避免把原始 CSS 作为“头部文本”插入导致页面顶部出现代码墙）
- **templates/Rmd_template.Rmd**：更新模板 YAML 头部
  - 同步 config.yaml 中的主题配置
  - 添加 Liquid Glass 主题说明注释
- **SKILL.md**：新增"HTML 主题（Liquid Glass，iOS 26 风格）"章节
  - 核心特性说明
  - YAML 配置示例
  - 使用前提与文档链接

### Fixed

- **代码选中高亮“漂移/闪动”**：默认关闭 Liquid Glass 主题中的无限动画（尤其是代码块光泽划过效果），避免复制/选中时视觉干扰

- **Liquid Glass HTML 样式异常**：修复“页面顶部出现一大段 CSS 代码墙”的问题
  - 移除 `includes.in_header` 直接 include `.css` 的写法，统一通过 `css:` 引入
- **浮动目录位置**：桌面端 TOC 默认固定到左侧（响应式逻辑保持不变）
- **测试演示文档**：Liquid Glass demo 表格改为 `DT::datatable()`（不再使用 knitr 表格渲染）
- **DataTables 表头/表体列宽错位**：将 Liquid Glass 的“卡片化 table”样式限制为 `table:not(.dataTable):not(.display)`（兼容 DT 初始化前的 `class="display"`），并对 `.dataTables_wrapper table.dataTable/.display` 禁用影响列宽计算的装饰样式，避免滚动模式下列对齐异常
  - `bensz-rmd-rules/tests/v202602041426/`：轻量回归测试（PLAN/REPORT + 渲染产物）
- **中文字体**：在 `templates/00.Environment.R` 增加绘图字体自动选择/注册逻辑，降低中文字符乱码风险
- **静态检查脚本**：修复 `scripts/check_htmlwidget_visibility.py` 对多行 `DT::datatable(...)` 等 widget 调用的误报
- **代码块滚动条**：移除代码折叠块底部的横向滚动条（通过强制换行与禁用横向 overflow）
- **图片查看体验**：新增点击图片放大预览（Lightbox），并在模板 YAML 中默认启用（`includes.after_body`）
- **图片可拷贝**：修复 Liquid Glass 主题 HTML 中右键菜单无法“拷贝图像”的问题
  - `templates/liquid_glass_theme.css`：将 `img` 的 `transition: all` 收敛为仅动画视觉属性，并显式启用交互相关属性
  - `templates/liquid_glass_lightbox.html`：Lightbox 仅响应左键点击，避免影响右键上下文菜单

### Added

- **新项目初始化脚本**：新增 `scripts/bootstrap_liquid_glass.py`，一键将 Liquid Glass 主题资源复制到新项目根目录

- **scripts/check_plot_readability.R**：新增 PDF 图表可读性基础检查脚本（文件存在/大小/可选文本提取）
- **templates/nature_theme.R**：新增 `theme_nature_readable()`，为旋转标签/边距/图例外置提供更友好默认值
- **templates/complexheatmap_template.R**：新增 `make_heatmap_nature_safe()` 与 `truncate_labels()`，默认处理行/列名过长

- **references/plot_quality_standards.md**：新增 Nature 级别图表质量规范（跨包）
- **templates/nature_colors.R**：新增 Nature 调色板（色盲友好）
- **templates/nature_theme.R**：新增 ggplot2 Nature 级别主题 `theme_nature()`
- **templates/complexheatmap_template.R**：新增 ComplexHeatmap 可读性模板（动态字体/尺寸）
- **templates/plotly_template.R**：新增 plotly 交互图模板（统一字体/布局/配色）

- **references/interpretation_narrative_examples.md**：新增“连贯叙述式”专家解读示例库
  - 覆盖差异分析/生存分析/PCA/模型性能/缺失模式等常见输出类型
  - 用自然段落内化四层内涵（数据描述 + 统计见解 + 领域映射 + 局限与后续），避免机械分点
- **references/expert_discussion_template.md**：新增专家级讨论模板文档
  - 完整的讨论章节模板结构（基于 PanTCGA Mutation 分析）
  - 七大核心特征：量化陈述、动态数值、层次递进、辩证思考、具体示例、可操作建议、启发性
  - 避免的浅层讨论 vs 推荐的深度讨论示例
- **references/four_tier_interpretation_framework.md**：新增四层解读框架文档
  - AI 解读图表的独特优势说明（代码+数据 vs 视觉感知）
  - 最佳实践：动态数值嵌入（使用 Rmd 内联代码）
  - 数据溯源要求和解读-代码一致性验证
  - 按分析类型的解读模板（表格类、图表类）
  - 解读质量自检清单
- **references/interpretation_templates.md**：新增“证据锚定版”深度解读模板
  - 覆盖 3 类高频输出：单因素筛选、多因素模型、模型性能与验证
  - 强制模板包含：Top 信号 + 方向/效应 + 不确定性 + 领域映射 + 可落地后续（方法+输入+判据）
- **scripts/check_interpretation_quality.py**：新增解读静态预检脚本（可选）
  - 启发式检测：内联 `r ...` 数量、Top 信号提示、不确定性/稳定性提示、常见套话黑名单
- **references/hybrid_architecture_examples.md**：新增混合架构示例（从 SKILL.md 下沉）
  - 展示 `.R` 生成全量结果、`.Rmd` 基于 `params` 做阈值筛选的典型写法
- **references/hybrid_architecture_guide.md**：新增混合架构指南（从 SKILL.md 下沉）
  - 汇总 `.R/.Rmd/_functions/00.Environment/tmp` 的职责边界、模板入口与最小口径
- **references/plot_language.md**：新增图表语言规范文档（从 SKILL.md 下沉）
  - 英文优先 + `params.plot_language` 例外切换 + 示例与检查清单
- **references/no_overdefensive_code.md**：新增“不过度保护/禁止占位性代码”反模式说明（从 SKILL.md 下沉）
- **references/code_block_explanations.md**：新增“代码块前解释（分析决策叙述）”模板与示例（从 SKILL.md 下沉）
- **references/delivery_verification.md**：新增交付自检报告模板（从 SKILL.md 下沉）
- **references/workflow_checklist.md**：新增工作流检查清单（从 SKILL.md 下沉）

### Changed

- **htmlwidget/DT 输出可见性加固（避免“代码在但 HTML 不出表/不出图”）**：
  - `bensz-rmd-rules/SKILL.md`：新增“HTML 可见性硬规则（htmlwidget/DT）”与正误示例，并将“交付前强制检查”写成硬门槛
  - `bensz-rmd-rules/README.md`：新增 FAQ，解释根因与推荐写法/检查命令
  - `bensz-rmd-rules/templates/datatables_helper.R`：新增 `render_dt_output()`（用于稳定输出为可见结果）
  - `bensz-rmd-rules/templates/Rmd_template.Rmd`：表格示例改为 `render_dt_output(...)` 并确保为 chunk 最后表达式
  - `bensz-rmd-rules/scripts/check_htmlwidget_visibility.py`：新增 Rmd 静态检查脚本，拦截 print()/invisible 包裹与“widget 非最后表达式”等高风险模式；版本号 `0.14.1 → 0.14.2`

- **图表可读性硬检查升级**：
  - `bensz-rmd-rules/SKILL.md`：将“图表可读性自检”升级为“生成后必做硬检查”，并补充高频问题场景的最小可复用示例
  - `bensz-rmd-rules/config.yaml`：新增 `plot_readability` 阈值配置（max_ticks/min_font_pt/long_label_chars/heatmap_max_label_chars）；版本号 `0.14.0 → 0.14.1`
  - `bensz-rmd-rules/references/plot_quality_standards.md`：新增“可读性问题诊断流程”与“常见反模式”章节
  - `bensz-rmd-rules/templates/nature_theme.R`：新增 `theme_nature_readable()`，减少长标签/旋转标签场景的重复样板代码
  - `bensz-rmd-rules/templates/complexheatmap_template.R`：新增 `make_heatmap_nature_safe()`，默认处理行/列名过长
  - `bensz-rmd-rules/README.md`：补齐 `plot_readability` 配置说明与新增模板/脚本的可发现性

- **图表默认质量升级（Nature 级别）**：
  - `bensz-rmd-rules/SKILL.md`：新增“图表质量规范（Nature 级别）”章节与必检清单
  - `bensz-rmd-rules/config.yaml`：新增 `plot_quality` 配置；版本号 `0.13.4 → 0.14.0`
  - `bensz-rmd-rules/templates/Rmd_template.Rmd`：新增 plot-style 代码块与三包示例骨架
  - `bensz-rmd-rules/references/delivery_verification.md` / `bensz-rmd-rules/references/workflow_checklist.md`：交付自检新增“图表质量（Nature）”检查项
  - `bensz-rmd-rules/references/hybrid_architecture_examples.md` / `bensz-rmd-rules/references/interpretation_templates.md`：补齐图表质量与解读联动说明
  - 兼容性与鲁棒性修复：
    - `bensz-rmd-rules/templates/nature_theme.R`：移除 `linewidth` 用法，兼容旧版 ggplot2
    - `bensz-rmd-rules/templates/plotly_template.R`：修复 hover 默认值（避免空提示）；保存前创建父目录
    - `bensz-rmd-rules/templates/complexheatmap_template.R`：补齐数值/有限值校验与 `min==max` 处理；保存前创建父目录并校验尺寸
    - `bensz-rmd-rules/templates/R_data_template.R` / `bensz-rmd-rules/templates/Rmd_template.Rmd` / `bensz-rmd-rules/references/cross_platform.md`：统一 `file.path()`，避免硬编码路径写法
    - `bensz-rmd-rules/config.yaml`：`plot_quality.allowed_levels` 收敛为仅 `nature`（避免暗示未实现的多期刊切换）

- **基因 ID 指南示例与口径修复**：
  - `bensz-rmd-rules/references/gene_id_guidelines.md`：移除 `biomaRt`/`useMart` 示例，统一为 `luckyBase::convert()`；示例路径改为 `file.path()` 并补齐目录创建

- **代码注释规范落地**：
  - `bensz-rmd-rules/SKILL.md`：新增代码注释规范（头部说明 + Step 注释 + 复杂逻辑说明）
  - `bensz-rmd-rules/templates/R_data_template.R`：补齐头部注释模板与 Step 注释示例
  - `bensz-rmd-rules/templates/Rmd_template.Rmd`：补齐代码块头部注释模板与 Step 注释示例
  - `bensz-rmd-rules/config.yaml`：版本号 `0.13.3 → 0.13.4`

- **解读表达规范升级（标题/语气/数字/加粗）**：
  - `bensz-rmd-rules/SKILL.md`：新增“Rmd 标题规范”“解读语气与风格”“文本强调规范”“数字准确性验证（末尾检验）”，并在“结果后解读”补充“禁止代码生成解释”条款
  - `bensz-rmd-rules/config.yaml`：版本号 `0.13.2 → 0.13.3`，description 同步表达规范口径
  - `bensz-rmd-rules/templates/Rmd_template.Rmd`：补齐 `## 数字准确性验证` 章节骨架
  - `bensz-rmd-rules/references/four_tier_interpretation_framework.md` / `bensz-rmd-rules/references/interpretation_narrative_examples.md` / `bensz-rmd-rules/references/interpretation_templates.md`：示例统一为论文口吻与自然标题，并加入关键观点适度加粗示例
  - `bensz-rmd-rules/scripts/check_interpretation_quality.py`：新增可选表达规范检查 flags（标题括号/主-副标题/教学式标记/加粗密度），默认关闭以保持兼容
  - `bensz-rmd-rules/tests/v202601211445/`：新增轻量测试会话，覆盖脚本默认检查与新增 flags 行为

- **luckyBase 硬前提口径统一**：
  - `bensz-rmd-rules/SKILL.md`：资源优先级调整为“包加载集中在 `00.Environment.R`（`luckyBase::Plus.library()`）+ 分析脚本优先 `pkg::fn()`”
  - `bensz-rmd-rules/templates/00.Environment.R`：补齐 luckyBase 的最小依赖边界与集中包加载骨架（不提供降级）
- **YAML 头单一真相来源**：
  - `bensz-rmd-rules/SKILL.md`：移除 YAML 头的硬编码示例，改为引用 `config.yaml:rmd_template.yaml_header`
  - `bensz-rmd-rules/templates/Rmd_template.Rmd`：移除 `author` 行（避免与 config 重复口径）
  - `bensz-rmd-rules/README.md`：配置项表格改为引用 `rmd_template.yaml_header`，不再单独展示 `author`
- **SKILL.md 瘦身（渐进披露）**：
  - 将“实践示例/模板代码/长篇示例”下沉到 `references/` 与 `templates/`，SKILL.md 仅保留硬规则与入口指引
- **“完整因果链”实践形式升级（从模板化到内化式叙述）**：
  - `bensz-rmd-rules/SKILL.md`：将“代码块前解释”升级为分析决策叙述（数据特征 → 方法选择 → 输出解读），并补充 3 个不同分析类型示例
  - `bensz-rmd-rules/SKILL.md`：在“结果后解读”中新增“连贯叙述式 vs 分项式”的双模式指南，并提供段落骨架与写完后自检清单
  - `bensz-rmd-rules/SKILL.md`：在“交付验证”新增“解读-代码一致性自检”与报告检查项（关键数值/Top 信号/不确定性可追溯）
  - `bensz-rmd-rules/references/four_tier_interpretation_framework.md`：新增连贯叙述式框架、正向写作指南（不确定性/Top 信号句式）与分项式 vs 连贯式对比示例
  - `bensz-rmd-rules/README.md`：补充“四层是内容门槛而非固定格式”的说明，并增加示例库入口
- **SKILL.md 瘦身优化**（遵循渐进披露原则）：
  - **R 包资源清单**：删除镜像展示，改为引用 `config.yaml:r_packages`，消除维护冗余
  - **结果后解读章节**：从 ~180 行精简至 ~20 行，详细内容移至 `references/four_tier_interpretation_framework.md`
  - **末尾讨论与分析章节**：从 ~80 行精简至 ~40 行，详细模板移至 `references/expert_discussion_template.md`
  - 总行数：从 1161 行精简至 ~969 行（减少约 16%）
- **自动化验证增强**：
  - 路径验证脚本说明从"可选"改为"推荐"
  - 新增两种运行方式说明（R 中运行、命令行运行）
  - 新增检测项说明（硬编码路径、绝对路径、路径拼接、路径分隔符）
  - 新增引用 `references/cross_platform.md`
- **四层解读框架通用化**：
  - 第三层从"生物学/临床见解"改为"领域见解"（domain insights）
  - 适用于所有数据分析领域，不限定生信/医学场景
- **config.yaml**：
  - `skill_info.version`：0.10.0 → 0.11.0
  - `skill_info.description`：移除领域限定，强调通用性
- **结果解读质量门槛（反套话 / 证据锚定）**：
  - `references/four_tier_interpretation_framework.md`：新增 Fail Fast Gate、结果锚点句式库、黑名单套话→替代写法对照表，并补充可选静态预检说明
  - `SKILL.md`：在“结果后解读”章节新增硬性最小内容（Minimum Content Requirements）与反套话机制，并在工作流检查清单中新增硬门槛检查项
  - `README.md`：术语统一为“领域见解”，并补充证据锚定要求与参考文档入口
- **config.yaml**：
  - `skill_info.version`：0.11.0 → 0.12.0
  - `skill_info.version`：0.12.0 → 0.13.0
  - `skill_info.description`：补充“连贯叙述式写法”和“解读-代码一致性自检”
- **config.yaml**：
  - `skill_info.version`：0.13.0 → 0.13.1
  - `skill_info.description`：补充 luckyBase 为硬依赖的前提说明
- **config.yaml**：
  - `skill_info.version`：0.13.1 → 0.13.2
- **SKILL.md 瘦身（继续下沉到 references）**：
  - 将“图表语言规范/混合架构细节/反模式/代码块前解释/交付验证/检查清单”等内容进一步下沉到 `references/`
  - SKILL.md 保留硬规则与入口链接，降低维护冗余与口径漂移风险

### Removed

- 移除 SKILL.md 中的包清单镜像展示（仅保留简要表格，完整清单引用 config.yaml）
- 移除 SKILL.md 中专家级讨论模板的长篇示例（已移至 references/expert_discussion_template.md）
- 移除 SKILL.md 中四层解读框架的详细说明（已移至 references/four_tier_interpretation_framework.md）

- **禁止占位性代码模式**：在"不过度保护原则"章节中新增占位性代码的禁止规则
  - **占位性代码定义**：使用 `try()` 捕获错误后，将结果赋值为 `NULL`、`NA`、空数据框，或直接跳过/打印警告继续，从而保证代码表面运行成功的模式
  - **绝对禁止的占位性模式表格**：列出四种危险模式（try-catch 后赋值 NULL、打印警告继续、降级到占位符、条件分支后无有效逻辑）及其危害
  - **切实落地要求**：功能必须确保在正常流程中切实落地，不得使用占位符保证"不报错"；如功能失败应 `stop()` 报错；如需容错必须有有效降级方案
  - **正确示例对比**：提供占位性代码 vs 正确处理的对比示例（包含 LDA 建模和包依赖场景）
  - **权衡原则**：科研分析 > 代码美观、显式失败 > 静默成功、有效降级 > 占位符
  - **交付验证更新**：自检报告新增"无占位性代码"检查项，自检报告示例同步更新
  - **工作流检查清单更新**：新增两项占位性代码相关检查项
- **图表语言规范**：新增可视化图表英文优先原则
  - 在 SKILL.md"人类可读原则"章节后新增"图表语言规范"小节
  - 核心规则：所有可视化图表的文本元素（轴标题、图例、标题、副标题）必须使用英文
  - 提供正确/错误实践示例对比
  - 特殊场景例外说明：中文期刊投稿可通过 YAML params 设置 `plot_language: "zh"`
  - 实现建议：提供全局标签函数模板和 YAML params 配置方式
  - 检查清单：四项自检标准确保图表语言符合规范
- **图表语言配置**：在 config.yaml 中新增 `plot_language` 配置项
  - 默认语言：`"en"`（英文）
  - `force_english: true` 强制英文规则
  - 支持通过 YAML params 覆盖配置（用于中文期刊投稿等特殊场景）
- **gene_id_guidelines.md 示例更新**：将图表示例代码中的中文轴标题改为英文
  - 原示例：`labs(x = "基因", y = "表达量")`
  - 更新为：`labs(x = "Gene Symbol", y = "Expression Level")`
  - 新增反面示例展示应避免的中文轴标题用法
- **基因 ID 优先级指南**：新增生物医学分析专用的基因标识符使用规范
  - 新增 `references/gene_id_guidelines.md`：完整的基因 ID 优先级与可读性指南
  - 展示优先级：可视化、表格、文本解读中使用 SYMBOL（如 `TP53`），而非 ENSEMBL ID 或 ENTREZID
  - 数据完整性：保存的数据应包含 SYMBOL、ENSEMBL、ENTREZID 多种 ID，确保准确性和可追溯性
  - 核心理由：增强可读性，让临床医生、生物学家等非生信专业读者也能理解
  - 在"完整因果链原则"章节中添加引用和简要说明
- **数据筛选分离实例化说明**：新增基于真实项目的代码示例
  - .R 脚本示例：展示如何保存全量表（不筛选 p/q 值）
  - .Rmd 脚本示例：展示如何动态应用阈值筛选
  - 阈值参数配置原则：明确阈值仅在 .Rmd 的 YAML params 中定义
  - YAML params 配置示例：提供完整的阈值参数配置模板
- **postprocess-only 快速模式**：新增针对耗时分析的优化模式
  - 支持通过环境变量控制运行模式（`DV_MUT_MODE`）
  - 首次运行后，调整可视化时无需重跑耗时计算
  - 在 Rmd 中通过 params 控制运行模式
  - 使用方式和好处说明
- **文件写入最佳实践**：新增跨平台兼容的文件操作规范
  - 安全写入 CSV 函数示例（`.dvmut_safe_write_csv`）
  - 安全读取 CSV 函数示例（`.dvmut_safe_read_csv`）
  - 统一路径分隔符、自动创建目录、统一 UTF-8 编码
  - 错误处理和降级方案
- **专家级讨论模板**：新增基于真实项目的深度讨论写作指南
  - 完整的讨论章节模板（约900字级别）
  - 专家级讨论的七大核心特征（量化陈述、动态数值、层次递进、辩证思考、具体示例、可操作建议、启发性）
  - 避免浅层讨论的反面示例
  - 推荐的深度讨论示例
- **自检报告真实示例**：新增基于 PanTCGA 项目的完整自检报告
  - 展示如何填写每个检查项的证据/说明
  - 包含 15 个检查项的详细证据
  - 新增"专家级讨论"检查项
- **DT::datatable() 标准化调用**：新增 `templates/datatables_helper.R` 辅助函数
  - 提供 `render_dt(data, n, scrollX, pageLength)` 标准化接口
  - 减少重复代码，统一表格渲染方式
  - DT 包已通过 `00.Environment.R` 加载，直接使用即可
- **references/candidate_r.md**：新增 candidate_r 详细使用指南
  - 明确 candidate_r 的可选性和使用场景
  - 提供两种使用模式（已加载 vs 指定路径）
  - 强调安全提示和实践原则
- **references/cross_platform.md**：新增跨平台兼容性最佳实践指南
  - 路径拼接、文件 I/O、平台差异处理详细说明
  - 常见陷阱和跨平台测试清单

### Changed

- **config.yaml**：
  - `rmd_template.yaml_header.author`：从占位符改为“技能作者名”（仅在 config.yaml 托管）
  - `rmd_template.yaml_header.output.html_document.number_sections`：新增 `true`
  - 新增 `rmd_template.datatables_helper` 配置，指向 DT 辅助函数
  - `skill_info.version`：0.7.0 → 0.10.0
  - `skill_info.description`：更新为包含实例化说明、postprocess-only 模式、安全写入函数、专家级讨论模板、自检报告示例、禁止占位性代码模式
- **SKILL.md**（功能增强 + 瘦身优化）：
  - **数据筛选分离原则**：新增优秀实践示例（.R 和 .Rmd 代码对比）
  - **阈值参数配置原则**：新增配置原则说明和 YAML params 示例
  - **数据脚本规范**：新增"支持快速后处理模式"要求和完整实现示例
  - **跨平台兼容性原则**：新增"文件写入最佳实践"章节（安全写入/读取函数）
  - **末尾讨论与分析**：新增专家级讨论模板（基于 PanTCGA Mutation 分析）
  - **专家级讨论的核心特征**：新增七大特征对比表和正反示例
  - **交付验证**：新增自检报告的真实示例（15 个检查项）
  - **candidate_r 章节**：简化为核心原则，详细用法移至 `references/candidate_r.md`
  - **跨平台兼容性章节**：从 ~160 行精简至 ~30 行，详细内容移至 `references/cross_platform.md`
  - **YAML header 章节**：改为引用 `config.yaml:rmd_template.yaml_header`，确保单一真相来源
  - **表格渲染章节**：新增 DT 辅助函数的使用方式，提供两种调用方法
  - **交付验证章节**：YAML 规范检查项改为"见 config.yaml"
  - **工作流检查清单**：最后一项更新为"见 config.yaml"
  - 总行数：约 1000+ 行（包含新增的实例化内容）
- **README.md**：
  - 新增"快速迭代可视化（postprocess-only 模式）"使用场景
  - 新增"阈值参数灵活配置"和"快速后处理模式"核心特性
  - 新增"专家级讨论模板"核心特性说明
  - 更新核心特性表格（从 6 项扩展到 9 项）
- **metadata.version**：0.8.0 → 0.9.0

### Removed

- 移除 SKILL.md 中 candidate_r 的重复代码示例（已在 references/candidate_r.md 详细说明）
- 移除 SKILL.md 中跨平台兼容性的详细示例代码（已在 references/cross_platform.md 详细说明）

## [0.6.0] - 2026-01-20

### Added

- **专家级结果解读框架**：新增四层解读指导原则，避免仅有"描述"而无"见解"的浅层解读
  - **第一层：数据描述**：清晰陈述输出的基本结构和内容
  - **第二层：统计见解**：解释效应大小和方向的实际意义
  - **第三层：生物学/临床见解**：将统计结果与生物学机制/临床实践关联
  - **第四层：局限与后续**：指出局限性和不确定因素，提出验证建议
- **AI 图表解读的独特优势**：明确 AI 应基于**代码+原始数据**解读图表，而非"看图说话"
  - 核心原则：AI 无需查看渲染后的图像，直接分析生成图表的代码和原始数据
  - 实践方式：读取代码理解图表类型和参数，分析数据提取精确数值，生成量化解读
  - 优势对比：精确量化、无视觉偏差、可复现
  - **最佳实践：动态数值嵌入**：解读中的关键数值应使用 `` `r ...` `` 动态生成，确保精确且可追溯
  - **数据溯源要求**：解读中提及的数值必须明确其来源（变量名、计算逻辑）
  - **解读-代码一致性验证**：自检每个数值是否都能在代码/数据中找到对应来源
  - 检查清单：六项标准确保基于代码和数据的精准解读（含动态嵌入和数据溯源）
- **示例对比**：提供浅层解读（仅有描述）与专家级解读（描述 + 见解）的具体对比示例
- **解读模板**：新增表格类和图表类输出的标准化解读模板
- **解读质量自检清单**：新增六项自检标准（数据层、统计层、科学层、局限层、后续层、避免套话）
- **交付验证更新**：自检报告新增"专家级解读"、"避免浅层描述"、"AI 图表解读"检查项
- **工作流检查清单更新**：新增四项解读质量相关检查项（含 AI 图表解读）

### Changed

- **完整因果链原则章节重构**：从简单示例升级为系统化的解读框架
- **末尾讨论与分析章节增强**：
  - 新增"与现有研究的关联"小节
  - 局限性细化为数据/方法/解释三个层面
  - 进一步分析建议细化为短期/中期/长期三个方向
- **config.yaml**：
  - `skill_info.version`：0.5.0 → 0.6.0
  - `skill_info.description`：新增专家级结果解读框架说明
- **SKILL.md**：
  - `metadata.version`：0.5.0 → 0.6.0
  - `metadata.short-description`：更新为包含专家级结果解读框架
  - YAML frontmatter `description`：新增专家级解读说明

## [0.5.0] - 2026-01-20

### Added

- **数据筛选分离原则**：明确 .R 和 .Rmd 关于数据筛选的职责分工
  - .R 脚本：生成未经阈值筛选的完整数据集，保存所有样本和特征，方便用户审查数据最原始的状态
  - .Rmd 分析：根据具体业务需求和统计要求，对 .R 提供的完整数据应用阈值筛选（如表达量阈值、p值阈值、样本量要求等），从而保证分析具有科学价值和临床意义
  - 新增数据流示意图，直观展示 .R 到 .Rmd 的数据传递和筛选职责分离
- **核心原则更新**：
  - 核心原则概览表格新增"数据筛选分离"原则
  - "核心设计理念"表格新增"数据状态"列，明确 .R 输出完整数据、.Rmd 应用业务阈值
- **规范更新**：
  - "数据脚本规范"新增"不应用阈值筛选"要求
  - "主脚本规范"新增"根据业务需求应用阈值筛选"要求，并明确加载完整数据
  - "交付验证"自检报告新增"数据筛选分离"检查项
  - "工作流检查清单"新增数据筛选相关检查项（3 项）
- **YAML frontmatter 更新**：
  - `description` 新增数据筛选分离原则说明
  - `metadata.short-description` 更新为"（.R 保留完整数据，.Rmd 应用业务阈值）"

### Changed

- **config.yaml**：
  - `skill_info.version`：0.4.0 → 0.5.0
  - `skill_info.description`：新增数据筛选分离原则说明
- **SKILL.md**：
  - `metadata.version`：0.4.0 → 0.5.0
  - `metadata.short-description`：更新为"R Markdown 开发规范与最佳实践（.R 保留完整数据，.Rmd 应用业务阈值）"

## [0.4.0] - 2026-01-18

### Added

- **混合架构支持**：从单 Rmd 架构升级为 .R + .Rmd 混合模式
  - `.R` 脚本负责数据处理、重型计算、保存结果
  - `.Rmd` 脚本基于 .R 结果进行可视化与分析
  - 核心优势：计算一次，保存结果，后续可快速迭代可视化
- **文件命名约定**：新增 `naming_convention` 配置，明确 `.R`、`.Rmd`、`.html` 除后缀外名称必须完全一致
- **新增模板文件**：
  - `templates/R_data_template.R`：数据脚本模板
  - `templates/functions_template.R`：函数脚本模板

### Changed

- **文件结构升级**：从三元架构（Rmd + Environment + tmp）升级为四元架构（.R + Rmd + _functions.R + Environment + tmp）
- **核心原则更新**："主副分离"重构为"混合架构 + 函数分离"
- **config.yaml**：
  - `file_structure` 新增 `data_script` 和 `functions_script` 配置
  - 新增 `naming_convention` 配置节
- **SKILL.md**：
  - "主业与副业分离原则"章节全面重构，详细说明 .R + .Rmd 混合模式
  - 新增"数据脚本规范"章节，定义 .R 脚本的标准结构和数据保存约定
  - 新增"函数脚本规范"章节，定义 `_functions.R` 的使用方式
  - "主脚本规范"更新为专注于加载 .R 结果和可视化
  - 交付验证检查清单新增"混合架构"和"文件命名一致"检查项
- **templates/Rmd_template.Rmd**：环境代码块重构为数据加载代码块，检查 .R 脚本是否已运行

### Removed

- 移除 Rmd 模板中 DT 包的冗余加载逻辑（`00.Environment.R` 已统一管理）

## [0.3.0] - 2026-01-18

### Changed

- **强化"不过度保护原则"**：禁止主脚本中的包加载冗余检查和降级方案
  - 新增"绝对禁止的反模式"示例：包加载检查、包加载多重检查、表格渲染过度检查
  - 新增"硬性规定"：禁止主脚本使用 `requireNamespace()` 检查包可用性
  - 移除环境代码块中 DT 包的 else 降级分支，明确说明 `00.Environment.R` 已统一管理包加载
  - 简化表格渲染说明，移除"降级方案"表述
  - 更新"检查边界规则"，明确禁止对 R 包加载状态的检查
  - 理由：`00.Environment.R` 已通过 `luckyBase::Plus.library()` 自动安装/加载所有依赖，冗余检查违反简洁原则
  - 影响文件：SKILL.md（环境代码块示例、表格渲染说明、检查边界规则）

## [0.2.9] - 2026-01-18

### Fixed

- **表格渲染问题**：修复 `df_print: DT` 配置无法正常工作的问题：
  - 移除 YAML frontmatter 中无效的 `df_print: DT` 配置
  - 将 DT 包加载逻辑统一到 `luckyBase::Plus.library("DT")`（符合主业与副业分离原则）
  - 简化表格渲染方式：直接使用 `DT::datatable(df, options = list(...))`
  - 移除冗余的 `to_dt()` 辅助函数
  - 影响文件：templates/Rmd_template.Rmd、SKILL.md、config.yaml

## [0.2.8] - 2026-01-18

### Changed

- **表格渲染默认方案**：将 `df_print` 从 `kable` 改为 `DT`：
  - DT 包提供交互式表格（排序、搜索、分页），兼容性更好
  - 在环境设置代码块中添加 DT 包的自动安装逻辑（`install.packages()`）
  - 主动确保依赖可用，而非被动降级到 kable
  - 影响文件：SKILL.md、config.yaml、templates/Rmd_template.Rmd

## [0.2.6] - 2026-01-18

### Changed

- **SKILL.md**：将"用户代码识别规则"重构为"增量操作铁律"：
  - 移除不可靠的启发式规则（如依赖 `# USER CODE` 标签）
  - 明确增量修改为核心原则：只添加新内容，不大幅重写已有代码
  - 与副脚本规范的"增量添加，严禁覆盖"原则保持一致

## [0.2.5] - 2026-01-18

### Fixed

- **SKILL.md**：修复"模板快速起手"章节的安全隐患——`00.Environment.R` 改为增量操作策略：
  - 若文件不存在：可复制模板作为初始化
  - 若文件已存在：仅增量添加函数，严禁覆盖用户已有配置
  - 与"副脚本规范"中的"增量添加，严禁覆盖"原则保持一致

## [0.2.4] - 2026-01-18

### Changed

- **SKILL.md**：candidate_r 默认不再要求显式 `candidate_r_path`；改为 `00.Environment.R` 加载后“函数存在即用、否则跳过”，若用户提供 `candidate_r_path` 则优先按路径 `source()`
- **README.md**：同步 candidate_r 的默认判定规则与推荐用法（建议在 `00.Environment.R` 做一次性加载）
- **config.yaml** / **SKILL.md**：版本号更新至 0.2.4

## [0.2.3] - 2026-01-18

### Added

- `templates/Rmd_template.Rmd`：可复制到用户项目的 Rmd 起手模板（含环境代码块与讨论章节骨架）
- `templates/00.Environment.R`：可复制到用户项目的辅助函数脚本模板（避免使用 `T/F`）

### Changed

- **SKILL.md** / **README.md**：补充“从 templates 快速起手”的使用说明，并明确包清单以 `config.yaml` 为权威
- **SKILL.md**：补充 `candidate_r` 的 `source()` 安全提示（仅对可信本地代码）
- **README.md**：补充 `candidate_r_path` 用法示例与 `source()` 安全提示
- **config.yaml** / **SKILL.md**：版本号更新至 0.2.3

## [0.2.2] - 2026-01-18

### Changed

- **config.yaml**：将 Rmd YAML header（title/author/date/output）集中到 `rmd_template.yaml_header`，并将默认 author 设为通用占位符
- **SKILL.md**：修复示例中对 `T` 的依赖（原 `if (T)` 包裹）为 `if (TRUE)`，避免 `T` 被覆盖导致函数不定义
- **SKILL.md**：统一 candidate_r / candidate_r_path 命名，并在示例中加入最小 I/O 边界检查（缺失即 stop）
- **SKILL.md**：环境设置示例支持 `luckyBase::Plus.library()` 缺失时回退到 `library()`
- **SKILL.md**：将时间敏感示例文件名改为占位符（`analysis_YYYYMMDD.R`）
- **README.md**：同步 YAML header 的 author 占位符，并补充 luckyBase 不可用时的回退说明

## [0.2.1] - 2026-01-18

### Changed

- **config.yaml**：简化 r_packages 结构，删除冗余的 use_cases 数组
- **config.yaml**：添加优先级说明注释（user_developed > candidate_r > CRAN > 自定义）
- **config.yaml**：添加 author 字段修改提示
- **config.yaml**：添加 file_structure 核心约定说明
- **SKILL.md**：YAML 模板部分添加权威定义来源说明（以 config.yaml 为准）

## [0.2.0] - 2026-01-18

### Added

- **用户代码识别规则**：明确了 AI 如何识别哪些代码属于用户、不应修改（SKILL.md）
- **检查边界规则**：添加了"不过度保护原则"的白名单/黑名单，明确何时必须检查、何时不应检查
- **临时文件夹生命周期管理**：明确了创建时机、清理策略、冲突处理规则
- **交付验证章节**：要求 AI 在提交 Rmd 前必须输出自检报告表格（强制执行机制）
- CHANGELOG.md 文件

### Changed

- **candidate_r 使用说明**：简化并明确了使用前提和行为规则
- **README.md**：移除了 emoji 符号，符合项目规范

### Removed

- `references/r-resources-index.md`：信息与 config.yaml 重复，遵循 DRY 原则删除
- `config.yaml` 中的 `code_style` 配置：未被 SKILL.md 引用，属于过度设计

### Fixed

- 更新了 README.md 中对已删除文件的引用

## [0.1.0] - 2026-01-18

### Added

- 初始化技能，实现五大核心原则：
  - 现有资源优先原则
  - 人类可读原则
  - 主业与副业分离原则
  - 不过度保护原则
  - 完整因果链原则
- SKILL.md：技能执行规范
- config.yaml：R 包资源配置、Rmd 模板配置
- README.md：用户使用指南
- references/r-resources-index.md：R 资源索引
