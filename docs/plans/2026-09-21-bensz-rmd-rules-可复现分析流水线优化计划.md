# `bensz-rmd-rules` 可复现分析流水线优化计划

## 通俗解释：究竟发生了什么

- **一句话说明：** 当前 Skill 同时维护了 targets 的计算状态和一套自定义的产品缓存、检查点与运行入口，像同一批包裹既由仓库系统登记，又由人工账本重复登记，长流程恢复时容易出现两套记录不一致。
- **具体场景：** 把一次需要数天的分析想成一条生产线：`renv` 固定工厂使用的工具和材料，`targets` 记录每个工序及其依赖，`R/` 放工序所需的函数，Rmd 最后把已经完成的结果编成科学报告。只有当许多相互独立的工序值得同时处理时，才让 `crew` 增加工人；`tar_watch()`、`tar_poll()` 和 `autometric` 用来观察生产线和工人的运行状况。
- **对应到本问题：** `_targets/` 是机器记录的计算状态，不再和自定义 `SUCCESS`、identity hash、checkpoint runner 共同决定是否重算；`products/` 和 `reports/` 是人要审阅、复用或交付的科学产物；Rmd 不再承担重型计算。
- **改变前后：** 现在中断后既要理解 targets，又要理解自定义 checkpoint/runner；优化后，只要 targets store、输入、代码和环境仍有效，重新运行 `tar_make()` 就沿用已完成昂贵 target，用户可用 targets 的进度视图查看 DAG，用 crew/autometric 的成熟日志和资源指标诊断 worker，而不需要学习另一套缓存系统。

## 专业判断：问题在哪里

### 当前现象

`skills/beta/bensz-rmd-rules` 当前版本为 `0.25.0`。它已经具备 `renv`、`targets`、simple/complex 模式和轻量测试，但 complex 叙事仍同时保留：

- 编号 `.R` 分析单元作为计算入口；
- `products/` 数据产品；
- checkpoint helper、`metadata.yaml`、`SUCCESS` 和自定义身份/恢复协议；
- `analysis-plan.yaml` 与历史 runner 相关契约；
- targets 的 DAG、store 和增量执行。

这样会让“计算状态”和“科学产物”边界不够清楚，也可能让 targets 与自定义机制重复决定缓存命中、失效和恢复。现有 Skill 还没有把 `R/ + _targets.R` 作为 pipeline 计算代码的主流组织方式，也没有把 `Rmd` 消费 targets 的关系写成核心契约。

### 影响范围

- 新建大型分析项目可能同时生成两套计算组织方式和两套缓存心智模型。
- 长时间运行流程虽然有 targets，但断点恢复尚未作为必须真实验证的行为写清楚。
- 并行能力容易被误读成复杂项目的固定依赖，或与模型/BLAS 等内部并行叠加。
- 运行观测容易被误写成 Skill 自己设计的日志、状态或资源采样系统，偏离 R 生态已有能力。
- README、references、模板、检查器、QA/evals 和 CHANGELOG 需要同步，否则会继续出现“文档描述一个架构、模板实现另一个架构”的漂移。

### 已知原因与待验证假设

- **已知事实：** 当前 config 将 `targets` 限定为 complex，并保留自定义产品/checkpoint 与历史兼容入口；`SKILL.md` 也把这些机制写入输出和校验路径。
- **待验证假设：** 现有 `qa/` 用例中，部分测试直接验证旧 runner 或自定义 checkpoint，而不是验证 targets 的真实恢复语义；实施前需按用例逐项分类，不能凭文件名批量删除。
- **待验证假设：** `crew`、`autometric` 和当前锁定的 targets 版本在目标平台上的 API、日志路径和资源采集能力可能不同，必须以项目 `renv.lock` 和官方文档为准，不能把某个开发版 API 写成永久 Skill 契约。

## 要达到什么目标

### 完成后的变化

1. 将 Skill 的主概念明确为 **Reproducible Analysis Pipeline + Scientific Report**。
2. 大型、多阶段或昂贵分析使用 `renv + targets`；`_targets.R` 的 DAG 是执行顺序、依赖和增量重建的唯一事实来源。
3. 计算函数优先放在项目 `R/`，由 target 调用；Rmd 只消费 targets 结果，并可作为 DAG 的报告 target。
4. `_targets/` 只承担机器计算状态；`products/` 和 `reports/` 只承担正式科学产物，不重复实现 targets 的缓存、失效和恢复。
5. 中断后再次 `tar_make()` 的复用行为成为 pipeline 的硬性验收条件。
6. `crew` 作为有足够独立昂贵任务时的渐进增强；并行配置明确防止 CPU oversubscription。
7. 运行观测直接组合成熟组件：`tar_poll()` / `tar_watch()`、crew logging/metrics、`autometric` 资源日志与绘图；Skill 不自制调度器、日志协议或资源采样器。
8. 既有历史项目继续按原架构兼容维护；迁移是显式任务，不由新默认规则隐式触发。

### 不在本次处理范围

- 不把 `crew`、`autometric` 或集群插件提升为所有项目的固定依赖。
- 不为 Skill 编写新的 observability runtime、事件协议、worker 状态机、dashboard 或告警平台。
- 不重写具体研究方法、统计模型、领域指标或用户数据处理逻辑。
- 不将 `products/` 删除为目录；只移除其作为第二套计算缓存和失效引擎的职责。
- 不自动迁移已有 `tmp/`、旧 runner、旧产品或没有 targets/renv 的 existing 项目。
- 不修改 `skills/alpha/auto-draw-plot/` 或其它不属于本 Skill 的目录。

## 改进方向

### 方向一：把 pipeline 设为 targets-first 的核心架构

重新定义新项目的复杂分析路径：`renv` 锁定环境，`_targets.R` 声明 DAG，项目 `R/` 承载被 target 调用的计算函数，Rmd 消费 target 结果并负责科学沟通。当前 `complex` 若继续保留名称，应在文档中明确它实际代表 pipeline；若决定采用 `pipeline` 作为公开模式名，应把 `complex` 处理为过渡兼容别名，而不能让两套含义长期并存。

同步更新 `SKILL.md`、`config.yaml`、README、`workflow_modes.md`、混合架构说明、模板和 evals，使“脚本数量”“编号”不再决定是否使用 targets；决定因素改为依赖图、重算成本、复用、恢复和并行需求。新建项目的计算代码模板应转向 `R/` 与 `_targets.R`，并提供 Rmd 作为 pipeline 下游，而不是把编号 `.R` 作为第二套执行编排。

**对使用者意味着：** 只需理解一张 targets 依赖图；函数在哪里组织与 DAG 如何运行不再是两种竞争的项目结构。

### 方向二：明确 `_targets/`、科学产品和报告的职责

将 `_targets/` 定义为 targets 自己管理的机器计算状态和 computational checkpoint。把 `products/` 定义为需要人工检查、下游消费或正式交付的科学对象，把 `reports/` 定义为图、表、HTML 和补充材料。

逐项盘点并退出新 pipeline 路径中重复 targets 的 `metadata.yaml`、`SUCCESS`、identity hash、force-step/resume runner 和自定义 checkpoint helper。只有当某个元数据是科学产物的说明、数据字典或交付记录，而不是缓存命中判定时，才保留其科学文档职责。历史 existing 项目继续保留原机制，并在文档中标成 legacy/preserved-existing，不与新 pipeline 共享第二套入口。

**对使用者意味着：** 不再需要判断两个缓存系统哪个是真的；targets 决定是否重算，科学产品只记录要交付的结果。

### 方向三：把 Rmd 固定为 targets 的消费者

模板和示例改为：计算函数位于 `R/`，target 产生完整、未按展示阈值截断的结果，Rmd 通过 `tar_read()`/`tar_load()` 或 `tarchetypes::tar_render()` 消费这些结果。展示阈值、Top N、配色和图表布局仍属于报告参数；报告变化不应触发不相关的重型计算。

增加对 target→Rmd 关系的静态和轻量运行检查，阻止 Rmd 在报告层偷偷重做昂贵计算，阻止报告直接依赖 raw 而绕过 DAG。报告 target 的输出仍写入 `reports/` 或项目约定的正式位置，不能把 Rmd 渲染临时文件当成计算缓存。

**对使用者意味着：** 修改报告排版或解释时可以复用已完成的计算，Rmd 是科学叙述层而不是隐藏的第二个计算入口。

### 方向四：把断点恢复作为 pipeline 的硬验收

新增一个真实的中断/恢复验收场景，而不是只检查文件存在或运行 dry-run：先让至少一个昂贵 target 成功，再让后续 target 中断或失败，重新执行 `tar_make()`，确认仍有效的前序 target 被跳过且只执行未完成或失效的部分。

验收条件应明确包含 targets store、输入、相关代码、参数和 renv 身份没有变化，且没有显式强制重算；store 被删除、代码/参数变化或 targets 判断过期时，允许并要求重新计算。删除自定义 `SUCCESS` 后，恢复证据以 targets 的 metadata、outdated 状态和实际执行记录为准。

**对使用者意味着：** 数天流程被中断后重新运行不会无条件从头开始，且可以用 targets 的真实行为证明这一点。

### 方向五：把 crew 作为按需并行能力

保留普通 `tar_make()` 作为默认执行方式。只有当 DAG 中存在足够多相互独立且计算成本足以抵消 worker 开销的任务（例如 cohort、model、bootstrap）时，才在 `_targets.R` 中配置 crew controller；集群场景通过 `crew.cluster`、`crew.aws.batch` 等成熟插件接入，不由 Skill 自己实现 launcher。

加入并行决策清单：任务独立性、单任务成本、worker 启动/传输开销、资源预算、随机数可复现性和外部服务限制。明确禁止未经资源预算的嵌套并行：crew worker 内的 BLAS/OpenMP/future/BiocParallel 等线程数必须受控，避免 worker 数乘以内部线程数超过可用 CPU/内存。

**对使用者意味着：** 有并行收益时可以按标准方式加速，没有并行收益时不必为了“复杂”而安装或维护额外执行后端。

### 方向六：直接组合 R 生态的运行观测能力

不新增自定义 observability 层，按职责组合成熟工具：

- `targets::tar_poll()`：控制台周期性进度；
- `targets::tar_watch()`：DAG 和 target 状态的 Shiny 视图；
- `crew` 的 worker logging 与 `crew_options_metrics()`：worker 输出和资源指标；
- `autometric::log_start()`、`log_read()`、`log_plot()`：主进程/worker 的 CPU、内存和阶段资源诊断；
- 集群或云平台自身的日志和调度器：平台级 worker 生命周期与作业日志。

Skill 只规定启用条件、推荐调用位置、日志/图表产物边界和“targets 状态优先于 worker 日志”的解释顺序，不规定新的事件字段、心跳协议或 dashboard。所有可选包由项目 `renv.lock` 管理；没有对应依赖或平台能力时，记录观测降级，不伪造完整监控。

**对使用者意味着：** 可以先用 targets 看流程，再用 crew/autometric 查某个 worker 的资源问题，三个工具互相补充而不是重复维护。

### 方向七：同步文档、模板、检查器、QA 和兼容策略

按新架构重写 `SKILL.md` 的目标、模式选择、输出、校验和失败恢复；重写 `README.md` 的最短用法和目录示例；更新 `config.yaml` 的唯一真相来源，删除仅服务旧 runner/自定义缓存的新项目配置。

同步 `references/workflow_modes.md`、`lightweight_testing.md`、`analysis_workflow_cache.md`、`hybrid_architecture_guide.md`、`delivery_verification.md` 和 `workflow_checklist.md`，明确 pipeline、legacy existing、scientific product、targets store、可选 crew 和观测工具的关系。更新 `templates/_targets.R`、`R_data_template.R`、`Rmd_template.Rmd`、`Rmd_simple_template.Rmd`、`functions_template.R` 与测试骨架，使它们不再生成第二套 checkpoint/runner。

QA/evals 应覆盖：targets-only pipeline、R/ 函数发现、Rmd 消费 target、真实中断恢复、products/reports 与 `_targets/` 分离、crew 可选性、嵌套并行防护、tar_watch/tar_poll 观测入口和 existing legacy 保留。逐项确认未被用例引用的旧自定义缓存脚本、模板和文档，避免删除后残留引用。

**对使用者意味着：** 说明、模板和检查结果会指向同一条工作流，不会出现“文档建议 targets、模板却生成旧 runner”的情况。

## 实施范围与顺序

1. **先冻结架构决策和兼容边界。** 明确 `complex` 是否改名为公开的 `pipeline`，确定 simple 保留为低成本线性报告、existing 作为不迁移兼容层；同时标记 targets store、科学产品和 legacy checkpoint 的职责。
2. **再重写 Skill 契约和配置。** 先调整 `SKILL.md`、`config.yaml`、README 与核心 references，使 targets-first、R/、Rmd consumer、crew optional、观测组合和恢复硬门禁成为唯一新项目口径。
3. **随后调整模板和运行入口。** 将 `_targets.R`、`R/` 和 Rmd 模板连成可运行最小 pipeline；把 `tarchetypes::tar_render()` 或等价 targets 报告 target 的选择写清楚；移除新路径对自定义 checkpoint/runner 的依赖，保留历史入口的明确 compatibility 分支。
4. **最后迁移验证资产并清理残留。** 以真实 fixture 验证计算、恢复、报告消费、可选 crew 和观测；更新 QA/evals、CHANGELOG、必要的安装发现检查，并全局搜索旧术语和已退出机制。

## 如何确认完成

### 架构与静态一致性

- 新 pipeline 的唯一计算编排是 `_targets.R`；没有第二个 runner、编号执行图或自定义缓存命中逻辑。
- 计算函数可以从项目 `R/` 被 targets 发现并执行；Rmd 读取 target 结果，不从 raw 绕过 DAG 重做昂贵计算。
- `_targets/`、`products/`、`reports/` 的职责在 SKILL、config、README、模板和 references 中一致。
- 新项目不会因为使用 targets 而额外生成 `SUCCESS`/identity checkpoint；历史 existing 的旧机制有明确 legacy 标识。
- `crew`、`autometric`、集群插件均是项目级可选依赖，不进入 Skill 的固定依赖清单。

### 真实运行与恢复

- 使用一个最小但真实的 pipeline fixture，成功运行 `tar_make()`，并能通过 `tar_poll()` 或 `tar_watch()`观察 target 进度。
- 中断后再次 `tar_make()` 时，仍有效的已完成昂贵 target 不重新执行；未完成或失效 target 按 DAG 继续执行。
- 修改报告参数只重新渲染报告或必要的报告 target，不触发无关重型 target。
- 删除或损坏 targets store、改变输入/代码/参数或显式请求重算时，测试能证明 targets 正确失效；不靠人工补写标记恢复。

### 并行与观测

- 无 crew 时 pipeline 正常运行；有足够独立任务时可以切换到 crew controller，不改变 DAG 和结果契约。
- crew worker 日志和 `crew_options_metrics()` 能在受支持平台生成；`autometric::log_read()` 能读取，`log_plot()` 能生成资源诊断图。
- 主 targets 进程的资源观测和 worker 资源观测可以区分；资源观测失败会被记录为降级，不冒充科学计算失败。
- 明确限制 worker 数与任务内部线程数，至少有一个验证用例或静态检查防止明显的嵌套 oversubscription 配置。

### 兼容与文档

- existing 项目仍能使用原入口并得到 preserved-existing 说明；没有隐式创建 targets/renv 或迁移旧产品。
- 相关 QA/evals、references、模板和 CHANGELOG 全部使用新术语与新边界；全局搜索不再留下会误导新项目的旧缓存/runner说明。
- 运行前后的 `raw/`、正式 products/reports 和正式 targets store 均无测试污染；测试现场与日志按仓库约定隔离。

## 技术补充（按需阅读）

### 推荐参考的成熟组件资料

- `targets` 分布式计算与 crew 集成：<https://books.ropensci.org/targets/crew.html>
- `targets::tar_poll()`：<https://docs.ropensci.org/targets/reference/tar_poll.html>
- `targets::tar_watch()`：<https://docs.ropensci.org/targets/reference/tar_watch.html>
- `crew` logging：<https://wlandau.github.io/crew/articles/logging.html>
- `autometric` 资源记录与绘图：<https://wlandau.github.io/autometric/>、<https://wlandau.github.io/autometric/reference/log_plot.html>

这些资料用于确认具体 API 和版本行为；Skill 不应复制它们的实现，也不应把某个开发版参数未经项目锁定就写成永久接口。

### 迁移判定原则

迁移只针对新项目默认路径或人类明确授权的 existing 项目。旧 `tmp/`、自定义产品、旧 runner 和旧 checkpoint 只有在显式迁移计划中完成结果比对、回退安排和清理确认后才能退出；本次优化本身不隐式搬迁它们。

## 风险与待确认事项

- **公开模式命名：** 需要在实施开始前决定是保留 `complex` 作为正式名称，还是引入 `pipeline` 并把 `complex` 设为过渡别名；不能同时让两者各自表达不同架构。
- **targets 版本兼容：** `tar_poll()`、`tar_watch()`、crew controller 和 `autometric` 的具体签名随项目 `renv.lock` 版本变化；验证应使用锁定版本，不以当前开发文档代替项目依赖。
- **报告 target 的依赖图：** Rmd 若直接 `tar_read()`，需要明确其是在 pipeline 外渲染还是作为 `tarchetypes::tar_render()` target；两种方式不能形成循环依赖。
- **产品是否需要持久化：** 不是所有 target 都应导出到 `products/`；只有科学上需要审阅、复用或交付的结果才持久化为产品，避免把产品目录重新变成第二个 store。
- **观测能力边界：** crew/autometric 主要提供进程级 worker 资源与日志，不能宣称覆盖所有集群级指标、GPU、网络、配额或告警；这些由平台插件和基础设施负责。
- **并行资源预算：** 需要根据目标机器、BLAS/OpenMP 设置和集群调度规则确定 worker/线程上限；没有资源预算时保持普通 `tar_make()`。
- **测试目录治理：** 当前 beta Skill 有 `qa/` 测试资产，实施时需逐个判断是否应迁移到仓库测试边界或继续作为 Skill 专属质量资产，不应因新架构一次性删除。
- **既存工作区状态：** `docs/contribution.bac` 当前已有未提交改动；实施时必须保留并单独记录，不得覆盖或重写。
