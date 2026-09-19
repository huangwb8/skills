# bensz-rmd-rules 优化计划

## 通俗解释：究竟发生了什么

- **一句话说明：** 当前 Skill 同时描述了编号脚本、旧 runner、checkpoint 和缓存规则，但还没有把 `targets` 流程管理与 `renv` 环境管理纳入统一入口，也把一组偏个人研究方向的 R 包列成了优先依赖。
- **具体场景：** 新项目需要一套固定的流程账本和环境锁；已有项目则像正在运行的生产线，不能因为 Skill 更新就被强行换轨。
- **对应到本问题：** `targets` 管理分析步骤之间的依赖，`renv` 锁定 R 包环境，`products/` 与 `SUCCESS` 记录可交付的数据产品；`luckyBase` 是 Bensz 生态的固定基础包，其它个人包不再进入默认依赖。
- **改变前后：** 现在新旧项目的规则边界不够清楚；优化后，新项目必须从一开始启用 `targets + renv`，已有项目缺什么就保持什么，不自动补齐、不自动迁移，也不建立旧 runner 回退链。

## 专业判断：问题在哪里

- **当前现象：** `SKILL.md` 明确把 `luckyBase` 作为硬依赖，但配置还把 `ccs`、`GSClassifier`、`lucky`、`luckyExperiment`、`luckyGEO`、`luckyModel` 和 `candidate_r` 放在默认或优先使用路径中；同时，`targets`/`renv` 还未形成正式的项目生命周期规则。
- **影响范围：** 普通用户可能被引导安装不需要的个人包；新项目可能继续采用编号脚本 + 自定义 runner，而不是统一使用 `targets`；已有项目则可能被误判为应该迁移。
- **已确认的产品决策：**
  1. 新项目强制启用 `targets` 和 `renv`，包括只有一个分析步骤的最小项目。
  2. 已有项目按实际状态独立判断：没有 `targets` 就不启动 `targets`，没有 `renv` 就不启动 `renv`；不能把缺失机制作为自动优化目标。
  3. 不设计“新 targets 流程失败后回退旧 runner”的双入口。已有项目如果本来就在使用旧 runner，继续尊重其现有架构，但 Skill 不为 targets 项目新建或维护回退入口。
  4. `luckyBase` 保留为唯一固定 Bensz 生态依赖；其它个人化包和 `candidate_r` 从默认依赖与优先推荐中移除。

## 要达到什么目标

- **完成后的变化：** Skill 能先识别项目是新建还是已有，再选择唯一适用的流程策略；新项目自动按契约建立 `targets + renv`，已有项目保持原状。
- `targets` 成为新项目的唯一流程编排入口，负责依赖图、增量重建和执行顺序；分析产品仍按 Skill 的产品目录、元数据和 `SUCCESS` 契约交付。
- `renv` 成为新项目的环境锁定入口；R 包来源、版本和锁文件变化可以参与结果身份判断。
- 默认 R 依赖只保留 `luckyBase`；具体分析包由用户项目决定并写入该项目的 `renv.lock`。
- **不在本次处理范围：** 不替已有项目迁移目录、不替已有项目补建 `_targets.R` 或 `renv.lock`、不重写 Bensz Skill Kernel、不设计 State/Verifier/Pack、不删除用户项目已有 runner 或缓存。

## 改进方向

### 1. 建立新项目与已有项目的互斥策略

在输入盘点阶段增加项目状态判定。空项目或用户明确声明新建的项目进入“新项目策略”；含有现有 R/Rmd、产品、报告、runner、`_targets.R` 或 `renv/` 的项目进入“已有项目策略”。状态不明确时先做只读盘点并请求澄清，不猜测迁移意图。

新项目策略必须初始化 `targets` 和 `renv`；已有项目策略只维护已经存在的机制。`targets` 和 `renv` 独立判断，已有项目可以处于两者都没有、只启用其中一个或两者都启用的状态，Skill 不主动补齐缺失项。

### 2. 让 targets 成为新项目的唯一流程编排方式

设计最小 `_targets.R` 模板，将每个有独立输入、输出和失败边界的分析单元映射为 target。`targets` 负责依赖图、增量重建和并行调度；`products/`、`metadata.yaml`、摘要/预览和 `SUCCESS` 继续负责可审查产品的落盘与完整性。

不再把旧 runner 设计成 targets 的回退方案。旧 runner 相关脚本和文档需要区分“已有项目继续使用的历史入口”和“新项目默认入口”，不得在新项目流程中同时维护两套执行器或让两者写同一产品目录。

### 3. 让 renv 成为新项目的唯一环境管理方式

新项目初始化 `renv`，生成 `renv.lock` 和激活入口；`00.Environment.R` 只负责载入环境、加载包和项目配置，不在每次运行中静默初始化、安装、升级、snapshot 或 restore。环境状态检查和锁文件更新必须有明确的执行时机与验证证据。

将 `renv.lock` 纳入影响结果的环境身份。`renv/library/`、staging、机器特定缓存和临时下载目录不进入版本库、正式报告或任务交付物。

### 4. 收缩默认 R 依赖并保留 Bensz 基础入口

从 `config.yaml` 的 `r_packages`、`SKILL.md` 输入说明、references、README、模板和示例中移除 `ccs`、`GSClassifier`、`lucky`、`luckyExperiment`、`luckyGEO`、`luckyModel` 与 `candidate_r` 的默认优先地位。

保留 `luckyBase` 为唯一固定生态依赖，并明确它只承担包加载、项目初始化和稳定的通用基础能力，不代表用户必须安装其它 `lucky*` 包。任务所需的 CRAN、Bioconductor 或用户自有包由具体项目声明并由 `renv` 锁定。

### 5. 同步文档、配置、模板和验证契约

同步更新 `SKILL.md`、`config.yaml`、`README.md`、CHANGELOG、架构指南、工作流检查清单、模板和必要的检查脚本。重点清理以下旧口径：简单新项目可以跳过 plan/runner、默认优先使用个人包、targets/drake 不属于默认设计、旧 runner 可以作为新流程替代入口。

增加可机器检查的规则：新项目必须能发现 `_targets.R`、`renv.lock` 和激活入口；已有项目不因验证而产生这些文件；target 输出不能绕过产品完整性协议；锁文件变化必须可追溯。

### 6. 增加面向行为的评估场景

为 Skill Creator 准备至少四类评估：新建多阶段项目、已有项目但没有 targets/renv、已有项目只启用其中一个、用户要求移除个人化包。验收重点是模型能否正确选择项目策略、拒绝隐式迁移、避免创建双入口，并只保留 `luckyBase` 作为固定依赖。

## 实施范围与顺序

1. 先盘点现有 `SKILL.md`、`config.yaml`、README、references、templates、runner/checker 和测试中的冲突口径，建立“新项目 / 已有项目 / 历史 runner”术语表。
2. 修改配置契约和正文规则：先落定项目状态判定、`targets + renv` 强制范围、旧项目不补齐和无回退入口，再改具体模板与脚本。
3. 清理个人化依赖声明，只保留 `luckyBase`，同步所有引用、示例和安装说明。
4. 为新项目补齐 targets/renv 最小模板、产品写入约定、环境身份规则和验证逻辑；已有项目的检查保持只读，不创建缺失资产。
5. 更新 README、架构指南、检查清单和 CHANGELOG，确保用户文档与 Skill 正文、配置单一真相一致。
6. 执行结构检查、YAML/配置解析、现有 R/Python 轻量测试和新增行为评估；验证通过后再决定版本号和是否进入 beta 发布流程。

## 如何确认完成

- 新项目示例首次初始化就包含 `_targets.R`、`_targets/`、`renv.lock` 和 `renv/activate.R`，且没有旧 runner 作为替代入口。
- 空项目以外的已有项目不会因为 Skill 执行而新增 `_targets.R`、`renv.lock`、`renv/` 或迁移目录。
- 已有项目只启用 `targets` 或只启用 `renv` 时，Skill 不会擅自启用另一个机制。
- `targets` 运行结果仍产生并验证 `metadata.yaml`、完整输出和 `SUCCESS`；失败 target 不会留下成功标记。
- `renv.lock` 可解析，环境状态检查结果可解释，机器特定库和缓存不进入交付。
- 全局搜索不再把 `ccs`、`GSClassifier`、`lucky`、`luckyExperiment`、`luckyGEO`、`luckyModel`、`candidate_r` 当作默认依赖或优先包；`luckyBase` 仍被正确声明为固定基础依赖。
- 结构检查和现有轻量测试通过；新增四类行为评估能区分新项目强制策略与已有项目兼容策略。

## 风险与待确认事项

- **项目状态判定：** 需要最终确定“已有项目”的最低识别条件，以及空目录之外的半成品项目如何处理。
- **简单新项目的 targets 形态：** 需要确定单报告项目是否也生成一个最小 target，还是统一生成一个包含渲染步骤的 target 图。
- **产品写入边界：** 需要确定 target 函数直接写 `products/`，还是由统一 helper 完成原子写入、metadata 和 `SUCCESS`。
- **旧 runner 资产：** 需要决定仓库中的旧 runner 脚本是保留为已有项目维护工具、标记为 legacy，还是在确认没有兼容需求后移除；无论选择哪种方式，都不能把它作为新 targets 项目的回退入口。
- **luckyBase 的必要范围：** 需要确认它在普通用户项目中的最小稳定 API，避免保留硬依赖却只承担品牌展示。
