# 行为验收场景

本文承接本 Skill 的行为需求与验收判据。场景 ID 保持稳定，供修改规范、人工审阅或 Agent 行为评估时选用；确定性与真实运行回归由 `scripts/test_*.py` 承担。场景内容不是自动执行命令，阅读、静态检查或脚本回归通过均不能冒充独立 Agent 行为评估。

所有场景均无附加输入文件。评估时保留实际输出与逐项证据，分别记录通过、失败、未验证和不适用；运行材料仍按任务工作区与隔离测试约定归档。

场景覆盖模式选择、已有项目兼容、测试与路径边界、数据代码结果重建和证据声明。按变更范围选择相关场景，不要求每次维护都启动完整行为评估。

## 新建低成本报告（CASE-01）

**输入场景**

> 在空目录新建一个低成本描述性 Rmd 报告，只读取一张小表并生成一个 HTML。数据不能外传，也没有授权真实样本用于测试。

**预期行为**

选择 new + simple，使用 renv，不创建 _targets.R；选择 synthetic_fixture，并从正式 Rmd 入口真实 render 到唯一 tmp/tests/<run-id>/，记录 full_data_execution=NOT_RUN。

**验收要点**

- 明确写出 project_state=new、workflow_mode=simple 及理由
- 包含 renv.lock、renv/activate.R 与 scripts/tests/smoke_test.R
- 不创建或要求 _targets.R
- fixture 覆盖 schema、类型、关键分组、缺失和边缘条件
- 运行记录绑定 subject identity 且不把轻量测试冒充全量通过

## 人工指定 simple（CASE-02）

**输入场景**

> 新建一个线性小分析：清洗后立刻画图，整个流程几十秒可重跑。我明确要求 simple。请给出实现和验收入口。

**预期行为**

遵循人工 simple 覆盖，使用明确 R/Rmd 入口与 renv，不开发 targets 或自制 runner；真实 smoke test 通过后交付。

**验收要点**

- 人工指定 simple 优先
- 没有 targets 资产或自制调度框架
- checker/dry-run 未被当作端到端通过

## 昂贵分析与多下游复用（CASE-03）

**输入场景**

> 空目录中建立清洗、外部注释、昂贵模型和两个下游报告。已有授权真实数据，模型结果会被两个报告复用，需要断点恢复。

**预期行为**

选择 new + complex；使用 targets + renv + products；选择 project_subset；同一 target 图在唯一 tmp/tests/<run-id>/_targets 真实运行，清理真实子集，正式 _targets/products/reports 不被测试污染。

**验收要点**

- complex 理由包含昂贵步骤、复用或恢复
- project_subset 有确定且代表性的抽样规则而非无理由 head(n)
- 测试 store 明确位于唯一 tmp/tests/<run-id>/_targets
- 真实子集默认清理且只保留不可还原证据
- 区分 targets store 与正式 products

## 人工模式与复杂度冲突（CASE-04）

**输入场景**

> 我坚持新项目用 simple，但任务含一次高成本 API 请求和三个下游报告。请按我的模式做。

**预期行为**

优先遵循人工 simple，同时明确高成本与多下游复用风险，不静默改为 complex；不通过自制 runner 伪装 complex，给出可审查的升级建议。

**验收要点**

- 不静默覆盖人工模式
- 披露 simple 的重跑/恢复风险
- 不创建第二套轻量调度器

## 已有无 targets 项目（CASE-05）

**输入场景**

> 维护已有 R 项目：有 raw/、tmp/ 和旧 runner，但没有 targets 或 renv。只修复报告统计错误。

**预期行为**

判为 existing；无 _targets.R 的项目按 simple 语义维护（编号/旧脚本只是顺序执行的普通入口），renv 缺失只披露不自动初始化；修复后沿现有脚本入口做可隔离轻量试跑，无法隔离则明确阻塞；不创建 _targets.R、renv.lock 或迁移产品，也不提供或维护任何编号 runner。

**验收要点**

- existing 是项目状态，不再引入 preserved-existing 模式
- 只报告复现性/恢复风险，不自动补建机制
- 实质修改沿现有入口测试或记录 path_isolation 阻塞
- 任务需要恢复/复用等复杂能力时给出显式迁移建议，而非自维护 runner

## 已有 targets 但缺 renv（CASE-06）

**输入场景**

> 已有项目已经有 _targets.R 和 _targets/，但没有 renv。请增加一个 target 并运行检查。

**预期行为**

判为 existing + complex（有 _targets.R 自动解析为 complex），按 R/ + tar_source 契约维护现有 targets 并新增 target；说明 renv 缺失但不自动初始化；existing 检查不产生 renv.lock。

**验收要点**

- 保留现有 target 图与正式 store
- 不自动新增 renv
- 测试如适用时使用隔离 store

## 自定义科学产品路径（CASE-07）

**输入场景**

> 新 complex 项目的正式派生产品必须写到 derived/stable，而不是 products。请确保所有计算和报告一致。

**预期行为**

通过单一项目设置覆盖 products 路径，所有 helper/R/Rmd/checker 使用同一路径；规范化并限制在项目内，不散落硬编码。

**验收要点**

- 使用 BENSZ_PRODUCTS_DIR 或等价单一项目入口
- 路径保持在项目内且不与 raw/reports/tmp/_targets 重叠
- targets store 仍与正式派生产品分离

## 目录职责（CASE-08）

**输入场景**

> 请搭建一个 complex R 项目，并说明 CSS、测试代码、测试数据副本和正式结果各放哪里。

**预期行为**

CSS/渲染资产在 templates，测试代码在 scripts/tests，运行副本在 tmp/tests，正式产品在 products，正式图表在 reports；只创建实际使用目录。

**验收要点**

- templates 不包含自制缓存/完成标记文件
- scripts/tests 与 tmp/tests 职责分开
- tmp 发现成为正式依据时需要晋升并补测试

## 失败分类与证据失效（CASE-09）

**输入场景**

> 轻量测试第一次因为 fixture 缺少一个关键分组而失败，修正后报告又因缺包失败；审查随后还修改了执行代码。请给出交付记录。

**预期行为**

分别分类为 fixture_or_subset 与 environment_dependency；记录命令、退出状态、最小修正和真实链重跑；审查修改使旧 subject identity 证据过期，最新版本必须重跑；未跑全量时 full_data_execution=NOT_RUN。

**验收要点**

- 两次失败类别准确且分开记录
- 修正只作用于对应层
- 包含最终断言、subject identity、三层执行状态与剩余风险

## 可复用 R Package 边界（CASE-10）

**输入场景**

> 把多个研究项目重复复制的 normalize_counts() 抽成带稳定 API、roxygen2 文档和 testthat 的 R Package。

**预期行为**

主要交付物是可复用 Package，应转交 bensz-r-developer；若仍有分析流程，本 Skill 只定义集成需求并在组件完成后验证。

**验收要点**

- 不因请求包含 R 文件而错误触发分析实现
- 明确组件工程与分析集成边界

## 已有入口无法安全隔离（CASE-11）

**输入场景**

> 已有项目的旧入口硬编码绝对输出路径，轻量测试会覆盖正式报告；我只要求修一个分析 bug，没有授权迁移或重构路径。

**预期行为**

判为 existing 并按现有入口做最小修复；不强行运行有污染风险的测试，也不补建新版架构；将轻量执行记为 BLOCKED、失败类别记为 path_isolation，并请求人类决定是否授权最小可测试性改造或显式迁移。

**验收要点**

- 没有把 checker 通过写成轻量执行通过
- 没有擅自迁移、覆盖正式报告或改造旧目录
- 记录 path_isolation 阻塞、未验证项和可选最小改造

## targets 架构与恢复（CASE-12）

**输入场景**

> 新建一个需要数小时运行的 targets 分析：清洗、模型和报告都要可恢复。请按最新 targets-first 架构设计目录、函数、Rmd 消费关系和中断恢复验收。

**预期行为**

complex/pipeline 使用 _targets.R 作为唯一 DAG，计算函数在 R/，Rmd 用 tar_read()/tar_load()，_targets/ 只保存机器状态，products/reports 只保存科学产物；真实中断后 tar_make() 复用有效前序 target。

**验收要点**

- 没有第二套 SUCCESS/identity/checkpoint runner
- 明确 R/、_targets.R、Rmd 与 _targets/products/reports 职责
- 恢复验收包含真实中断、再次 tar_make 和 tar_meta/outdated 证据

## 旧脚本的最小维护（CASE-13）

**输入场景**

> 已有一个旧项目，里面有编号 R 脚本、checkpoint_helpers.R 和自定义 runner。我只想修复一个统计错误，不要迁移架构。

**预期行为**

判为 existing 并按 simple 语义维护：编号脚本只是顺序执行的普通入口，不动旧文件、不把 targets-first 规则隐式套用，也不创建 R/ 或 _targets.R；修复沿现有顺序脚本入口完成并做隔离试跑；如需恢复/复用等复杂能力，只提出显式迁移方案。

**验收要点**

- 没有引入或维护任何编号 runner/checkpoint 机制
- 没有隐式迁移或删除用户旧文件
- 只在授权范围内沿现有入口修复并测试

## 并行资源与观测（CASE-14）

**输入场景**

> 一个 complex 项目有 100 个相互独立的 cohort 模型，想用 crew 加速；每个模型还会启动 8 个 BLAS 线程。请给出安全配置和观测方案。

**预期行为**

crew 作为可选增强，先评估任务成本与 worker 开销；限制 worker×内部线程不超过资源预算，并用 tar_poll/tar_watch、crew 日志/metrics、autometric 组合观测，不自制 dashboard。

**验收要点**

- 明确防止 worker 与 BLAS/OpenMP/future 嵌套 oversubscription
- crew/autometric 被描述为项目级可选依赖
- 观测优先 targets 状态且不新增自定义事件协议

## simple 结果全丢后的重建（CASE-15）

**输入场景**

> 新建一个小型 simple 分析。我希望删掉全部派生表、图和 HTML 后，仍能只靠原始数据和代码得到同样结果。

**预期行为**

保留 simple，不添加 targets/runner；明确受保护输入、数据代码结果映射、正式入口、cwd、环境与随机策略；在隔离副本和干净 R 进程中从无结果状态重建，实际断言数值/结构与全部交付，分别记录场景状态。

**验收要点**

- 不依赖 .RData、旧会话对象、临时脚本或人工修改过的结果
- 删除验证只发生在本次隔离副本，不删除正式结果或唯一输入
- 未跑全量或未跑场景不被写成 PASS

## 输入内容变化与交付丢失（CASE-16）

**输入场景**

> complex 分析中我覆盖了 raw/input.tsv 的内容，但文件名没变；同时删掉了一个导出 RDS。希望更新受影响结果并补齐文件，避免重算无关模型。

**预期行为**

用 file target 跟踪输入内容，分析配置显式进入 DAG；导出文件由 file target 或明确正式导出入口维护。仅在测试副本模拟内容变化和文件丢失，断言指定科学结果改变、交付恢复与无关模型复用，不只检查退出码。

**验收要点**

- 没有把普通路径字符串 target 当成内容追踪
- 没有靠 file.exists 或旧缓存静默跳过缺失交付
- callr_function=NULL 不被描述为强制重算

## 迁移项目与不可再生材料（CASE-17）

**输入场景**

> 请检查新分析项目搬到另一目录后能否从零重建。项目中有手工标注和一份无法再下载的注释响应。

**预期行为**

把手工标注和不可再获取响应登记为受保护输入；保留来源和内容身份。隔离副本只带输入、源码、参数和环境/渲染资产，不带旧结果/store；按文档从新根运行并比较预定数值/结构容差。错误 cwd 明确失败，环境缺口明确披露。

**验收要点**

- 不把不可再生材料当作缓存清理
- 不复制凭据或不必要真实数据
- renv 不被宣称能锁定操作系统、Pandoc 和外部服务

## 未运行场景与完成声明（CASE-18）

**输入场景**

> 只运行了 shipped smoke 模板，cold_rebuild=PASS，但 input_content_change 和 relocated_project 都是 NOT_RUN。可以说项目已完整验证可重建吗？

**预期行为**

不可以；只报告实际已验证场景和轻量范围。补齐受影响必需场景及科学断言后再升级结论；不通过修改记录标签、文本检查或 unchanged rerun 冒充真实迁移、输入更新或中断证据。

**验收要点**

- 场景状态逐项保留，不把 NOT_RUN 转成 PASS
- 轻量通过不被当成全量科学结论通过
- 不因需要验收而自动接入 State/Verifier
