# Changelog

All notable changes to the skills repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [Unreleased]

### Added（新增）
- 新增项目宣传图 `docs/assets/agent-skills-ecosystem.jpg`：以发光的 Skill 核心和 BUILD / TEST / RUN / KNOW 四条轨道，表达 Agent Skills 的开发、测试、运行与可观测质量保障闭环。

### Changed（变更）
- 优化仓库根目录中英文 README 首屏设计：引入居中 Hero、事实型徽章、任务导航与四阶段能力概览，改善语言入口、信息层级和项目辨识度。
- 重构仓库根目录中英文 README：按使用任务重新组织安装、Skill 导航、Kernel 入口、开发验证与贡献说明，并同步双语内容。
- 规划仓库 `v5.0.0` 发布：将 `bensz-skill-kernel` 更新至 `1.0.0`，并同步中英文 README 与当前源码、安装和发布流程。
- State 契约复用 Contract Pack 的 `mode: rule | prompt | hybrid | human` 字段，并在解析、序列化和执行描述中保持一致；旧 Markdown State 按是否有 entrypoint 兼容推断，历史索引的 `none` 保留兼容。

## [5.0.0] - 2026-09-03

### Changed（变更）
- 发布 `bensz-skill-kernel` `1.0.0`，同步包元数据及 PyPI 安装说明。
- 依据 `write-readme` 规范更新仓库与 Kernel 的中英文 README，补齐目录、BAC 和当前 Skill 清单。

### Added（新增）
- 新增 beta `write-readme`：基于仓库事实按项目类型生成对齐的中文 `README.md` 与英文 `README_EN.md`，内置库/CLI 服务/Web 应用/数据 ML/Agent Skill 模板、调研来源和双语结构检查脚本。

### Changed（变更）
- **Python 运行产物归档规则收敛**：在 `AGENTS.md` 中明确要求 pytest、Ruff、mypy、coverage、Python 字节码及临时虚拟环境统一归档到 `.bensz-api/`，并同步将 Ruff/Kernel 包级 pytest 配置及测试运行器指向该目录，避免根目录和包目录生成缓存。
- **Python 环境脚本路径收敛**：初始化模板与 Kernel README 的虚拟环境示例改为 `.bensz-api/.venv`，避免安装依赖时在项目根目录产生 `.venv`。
- `write-skill-readme` 转为 legacy：其 Agent Skill README 能力由 `write-readme` 承接；`install-bensz-skills` 的本地与 bootstrap legacy 清理名单同步更新至 0.6.2。
- `packages/bensz-skill-kernel` README 改为中英文对齐的面向使用者指南：补充安装闭环、State/Verifier/Workspace 导航、开发测试入口、Python API 与 CLI 边界及完整性/兼容性语义。

### Fixed（修复）
- 修复 `install-bensz-skills` 本地安装器从项目子目录运行时无法自动识别 `./skills/alpha` 的问题：改为沿当前目录祖先查找 canonical alpha 源，并同步 bootstrap fallback 版本至 0.6.2；远程 general 源继续固定为 `skills/alpha`。
- **Kernel 发布前主链路修复**：`bensz-skill-kernel` 更新至 `0.14.1` 并发布到 PyPI；将 PyYAML 声明为正式运行时依赖并移除不完整的 YAML fallback，使真实 Skill 的多行 State/Verifier 声明可稳定加载；同时保留 Contract 原始组件绑定字段进入事件账本，确保 `bsk verifier run --events` 返回的 Gate 与 Kernel 持久化 Gate 一致。
- **Kernel 依赖约束同步**：更新 `AGENTS.md` 的 Kernel 依赖边界，将 PyYAML 明确为读取 Skill `config.yaml` 的唯一第三方运行时依赖，避免治理约束与发布元数据冲突。

### Changed（变更）
- **Kernel PyPI 元数据补全**：为 `bensz-skill-kernel` 声明 README、MIT License、作者与仓库地址，并通过 `MANIFEST.in` 排除 sdist 中的 Python 缓存和系统文件。
- **补充 Verifier 教程的端到端示例**：在“一次实际验证怎样流过系统”小节加入报告缺字段、Gate 拒绝、修正重试到允许交付的逐步案例，帮助读者把流程图映射到具体输入、结果和状态变化。
- **Verifier 教程与最新 Kernel 行为对齐**：修正文档对默认只读/显式副作用授权、v1/v2 运行身份绑定、`error`/`unchecked` 错误分流、required/optional 组件 Gate、legacy Pack 诊断和 CLI 示例结果的描述，避免教程将兼容路径或示例命令误写成统一行为。
- **Kernel Contract Pack 混合执行层**：`bensz-skill-kernel` 更新至 `0.14.0`，新增 State/Verifier 共用的版本化组件描述、契约/计划哈希、`script`/`agent`/`human` 交接、依赖顺序、证据约束和保守合并；State 与 Verifier 继续通过独立适配器解释阶段条件及 verdict/Gate，旧单入口 Pack 保持兼容。
- **固化 State/Verifier 共用底层设计原则**：更新 `AGENTS.md`，明确 State 与 Verifier 共享 Contract Pack 的发现、执行、证据和审计基础设施，同时保留各自的状态迁移/invariant 与 verdict/Gate 语义适配，避免后续开发形成两套平行框架。
- **恢复 `prompt-programming` 的轻量执行模式**：移除该 Skill 的状态机、Verifier Pack、运行时门禁及相关说明，恢复至接入这些运行时能力之前的 `0.2.1` 配置与 Prompt Program 翻译流程。

### Added（新增）
- **BSK PyPI 发布助手**：新增 `tests/publish_bsk_pypi.py`，默认执行隔离构建、归档清洁度检查与 `twine check`，仅在显式 `--upload` 时使用本机标准鉴权上传，且发布产物统一写入 `tmp/bsk-pypi/`。
- **State/Verifier 共用 Contract Pack 执行层优化计划**：新增 `docs/plans/2026-09-01-verifier混合执行优化计划.md`，规划共享契约发现、脚本/Agent/人工执行、混合编排、证据审计和 State/Verifier 个性化适配路径。
- **版本绑定验证与错误完成文献记录**：新增 `docs/版本绑定验证与错误完成_经典研究文献.md`，整理 API/依赖兼容性、软件供应链证明、自动化偏信、目标错配、LLM verifier 与 Agent 任务完成评测等经典研究，并提出证据约束的完成声明框架。
- **Verifier 直观教程**：新增 `docs/verifier-tutorial.md`，通过真实请求/结果示例、Mermaid 执行图、Gate 分支和 Kernel 函数级代码地图，说明 Verifier 从发现、隔离执行到事件持久化与完成门禁的完整工作过程。
- **verifier-state-architect beta Skill**：新增面向 Verifier/State 架构规划的顾问型 Skill，允许“不接入”结论，强调删除影响测试、自然语言语义判断与 Kernel 契约对接。
- **状态机直观教程**：新增 `docs/state-machine-tutorial.md`，通过 Mermaid 流程图、完整迁移示例和 Kernel 代码映射，说明工作区状态、运行生命周期、Skill 领域状态、Verifier 与事件账本如何协作。

### Changed（变更）
- **Research-Idea 科学问题通俗解释**：在 `docs/plans/Research-Idea_skills科研化评估_20260831.md` 的“最佳科学问题-科学假设对”部分补充版本绑定验证的生活化类比、术语对照、前后对比和白话版问题/假设，帮助非本领域读者理解研究对象，同时保持原有变量、基线与可证伪边界不变。
- **状态机与验证器理论讨论补充**：在 `docs/状态机和验证器的理论基础的相关讨论.md` 中新增 Agent Skill 细粒度组件化、Kernel 共享协议层、Skill-like Pack、模糊端与精确端协作及工程创新性边界的讨论，明确其与单个普通 Skill 的比较层次。
- **Kernel 内置 State 阶段契约补全**：为 `packages/bensz-skill-kernel/src/bensz_skill_kernel/states/` 的内置 State 增加进入条件、Agent 行动、输入/证据、离开条件、转移指引、失败恢复与执行边界说明；同时在 `AGENTS.md` 固化完整阶段型 `STATE.md` 的最低内容要求，不改变现有生命周期转移表。
- **AGENTS.md Verifier/State 规则收敛**：将 Verifier/State 的规划、删留和 Kernel 复用判断明确委托给 `verifier-state-architect`，并把治理文件中的重复说明压缩为实现阶段不可下沉的协议、安全与兼容性门禁；详细设计继续以 Skill、ID 文档和 Kernel 契约为准。
- **verifier-state-architect beta Skill**：版本更新至 `0.2.1`；压缩工作型 `SKILL.md` 的重复说明，保持触发语义、输入输出、Kernel 复用/元组件审查、安全边界与计划契约不变。
- **verifier-state-architect beta Skill**：补充 Kernel 二层架构审查，要求在设计专用组件前盘点现有 Verifier/State 的复用可能，并评估可跨领域提炼进 `packages/bensz-skill-kernel` 的元组件；最终计划必须以独立章节和分点理由同时说明两类判断及其对人类决策的影响。
- **Kernel Verifier Pack 能力扩展**：版本更新至 `0.13.0`；支持目录化 Verifier 显式声明 `mode`，让 Skill 状态声明合并发现内置与本地 `references/verifiers` Pack，并在状态不变量中核对 required Verifier 的完整通过结果，支持 `prompt`/`llm_judge` 语义验证器。
- **prompt-programming 强制运行时门禁**：将状态机与 `bensz.prompt.contract-conformance@1.0.0` 从说明性接入改为每次执行必经流程；仅允许在 Kernel 记录验证结果/Gate、完成语义复核并推进至 `published` 后交付，并修正对应 CLI 与 Verifier 结果身份契约。
- **状态机与验证器改为显式可选**：更新 `AGENTS.md`，明确普通 Skill 开发默认不要求接入状态机、Verifier、Pack 或 Gate；仅在开发者明确提出时执行相关流程与门禁，并提示这些基础设施仍处于活跃开发阶段，采用前需评估风险与回退方案。

### Fixed（修复）
- **Kernel 混合结果 fail-closed、路径范围与构建清洁度修复**：`verification-v2` 事件会由 Kernel 复核组件哈希、run/attempt、执行者、人工确认、证据引用和 required 结果，拒绝组件漏跑、重复/串台或伪造 aggregate pass；同时修复允许目录尚未创建时 `path-scope` 将合法子路径误判越界的问题，并阻止本地 `__pycache__`/字节码进入发布 wheel。
- **Kernel Gate 缺失验证器 fail-closed**：`apply_gate` 现在在声明的 required Verifier 结果缺失时返回 `manual_review` 并列出缺失 canonical ID，避免公共 Gate API fail-open；Kernel 版本更新至 `0.12.4`。
- **Kernel Verifier 请求边界归一化**：`FilesystemVerifierRegistry.run` 对非 JSON object 请求返回结构化 `error` 结果，避免 `AttributeError` 泄露给调用方；`validate-md-ref` runtime kernel 版本同步至 `0.12.4`。
- **Kernel Gate 约束输入校验**：`apply_gate` 对非布尔 required 标志、缺失 ID 和非法版本格式统一 fail-closed，避免未经规范化的公共 API 输入静默放行。
- **Kernel 批量验证事务边界**：`record_verification_batch` 现在在同一事件账本锁内追加全部结果及 Gate，避免并发批次交错或半批次写入；Kernel 版本更新至 `0.12.3`，并补充并发连续性回归测试。
- **Kernel CLI 多验证器 Gate 绑定**：`bsk verification` 现在通过批量编排登记全部验证结果，并让 Kernel Gate 的 `result_refs` 覆盖当前批次，避免多验证器运行在 `checking → reported` 阶段因证据引用不完整而被错误阻塞；保留原有逐条 CLI 输出和“无 Gate 不写入 Gate”兼容性，并补充回归测试。该修复随 kernel `0.12.2` 引入，后续事务边界加固见 `0.12.3`。
- **validate-md-ref 运行时版本对齐**：同步 beta Skill 的 `runtime.kernel.version` 至 `0.12.3`，避免安装后的 Skill 因严格版本门禁拒绝使用已修复的 Kernel。

### Fixed（修复）
- **Kernel 证据边界与状态持久化加固**：Gate 由 Kernel 基于当前结果重算并绑定运行身份/结果事件；事件统一递归脱敏路径、原文和敏感字段；Skill 元状态采用可恢复的暂存、fsync 与原子发布协议，并在快照缺失、漂移或未完成提交时 fail-closed。

### Changed（变更）
- **validate-md-ref/kernel 运行契约加固**：区分确定性链接失效与网络不可观测状态，按 required/advisory requirements 计算 Gate，保留 instruction-only evidence refs，并校验 Verifier、Kernel 版本和运行来源。Kernel/Skill 版本分别更新至 `0.12.1`/`0.13.1`。
- **状态审计与运行隔离增强**：状态转移写入可回放的 `state.transition` 事件；验证证据要求成对 `run_id`/`attempt_id`，状态快照使用稳定字段哈希并在读取/回放时检测漂移。

### Fixed（修复）
- **状态回放完整性错误结构化**：`bsk rebuild` 遇到快照哈希不一致时返回稳定的 `integrity_error` 类别，缺失缓存仍可由事件账本恢复。

### Added（新增）
- **validate-md-ref 优化计划**：补充三份基于实际运行证据的缺陷分析、迁移策略和验收标准文档。
- **Kernel 状态 invariant 强制执行**：状态转移现在会检查 Kernel 已定义的
  `verifier-result-recorded` invariant；缺少 `verification.result` 或
  `verification.gate` 时拒绝离开检查状态，避免漏跑验证器仍进入 `reported`。
- **validate-md-ref 对齐最新 Kernel 协议**：事件记录补传稳定 `run_id`，验证输出同步 Kernel 的 assurance/覆盖指标，保持既有结果字段和调用方式兼容。
- **Agent 执行证据链静态加固（P0-P2）**：完成门禁现在强制检查 required phase、Verifier/Gate、产物路径与内容哈希；事件账本增加跨进程锁、幂等意图冲突检测及崩溃尾部恢复；Pack helper 增加受信执行、输入输出/错误上限、最小环境和进程组超时终止。

### Added（新增）
- **Kernel 边界测试补充**：新增事件幂等与授权、审计脱敏、崩溃尾部恢复、完成门禁路径/哈希校验、Pack helper 输入输出限制与超时，以及原子 Verifier pass/fail 回归测试；Kernel 运行时测试由 54 项增至 79 项。
- **Kernel 测试源码隔离**：为包级 pytest 配置声明 `src` 为源码路径，避免已安装旧版本遮蔽当前 checkout，保证直接运行包测试时验证本地源码。

- **运行契约与执行审计扩展**：事件支持协议、运行快照、授权/委托和 request hash 字段，工作区可记录契约快照；Verifier 增加 assurance tier、严格请求协议和确定性指标汇总，保留旧事件/CLI 兼容读取。

### Changed（变更）
- **Kernel Python 支持基线调整**：将 `bensz-skill-kernel` 的最低支持版本从 Python 3.10 提升到 3.11，补充 3.11–3.13 classifiers 与包级支持矩阵说明，推荐使用 Python 3.12。
- **新增 Agent 执行证据链静态加固计划**：根据《LLM约定执行与Agent可审计性》报告，规划完成门禁、事件并发与幂等、Pack helper 边界、契约快照、身份授权、执行审计回放和运行指标的分阶段加固；本计划仅定义范围与验收，不改变当前运行时行为。
- **AGENTS.md 开发规范补全**：补充 Skill、Verifier、State 与 `bensz-skill-kernel` 的可执行契约、Pack 索引一致性门禁、版本兼容矩阵、测试矩阵和文档分层入口；修正 frontmatter、Skill 路径及修改范围示例，并将“工程原则”调整到“有机更新原则”之前。
- **validate-md-ref 对齐最新 Kernel Pack 契约**：同步目录化 State Pack 索引与 kernel Verifier 事实输出，避免 Skill 继续依赖旧的本地网络验证路径，并补充对应回归验证。
- **抽取 State/Verifier 公共 Pack 基础设施**：新增 `bensz_skill_kernel.packs`，统一两类 Pack 的 `bensz-pack-index-v1` 索引发现、目录/契约一致性校验、入口路径约束、版本排序和 JSON-stdio 执行边界；State 与 Verifier 保留各自的状态图、结果归一化和 Gate 语义，公开 API 与 CLI 保持兼容。
- **Kernel 说明文档与代码同步**：更新 `docs/` 中非 `plans/`、`events/` 的工作区、State/Verifier ID 与理论协议说明，对齐 `bensz-pack-index-v1` 索引、`config.yaml.runtime`、workspace manifest、verdict/execution status 和 Gate 语义；同时在 `AGENTS.md` 固化重要源代码变更后的按需文档同步规则。
- **State/Verifier 索引清单**：在 `states/index.json` 与 `verifiers/index.json` 增加统一的 `bensz-pack-index-v1` 目录清单，集中定义包的 canonical ID、版本、classification、kind、tags、契约和入口；注册表校验清单与实际目录一致后再加载。
- **Kernel 生命周期 State 目录化**：在 `bensz_skill_kernel/states/<state>/` 为八个通用生命周期状态补齐独立 `STATE.md`、canonical ID、alias 与转移契约，并增加与 Runtime reducer 转移表的一致性测试；领域 Skill 阶段仍由各 Skill 托管。
- **原子 Verifier 目录化**：将首批通用原子 Verifier 从 `builtins.py` 的内存规则注册迁移到 `bensz_skill_kernel/verifiers/<slug>/`，为每项补充独立 `VERIFIER.md` 与 JSON-stdio 入口；保留 `build_builtin_registry()` 作为兼容 API。
- **Kernel 公共运行协议收敛**：`bensz-skill-kernel` 增加 Subject、Requirement、Artifact、Contract、Effect 等领域无关交接对象，投影补充正交 `effect_status`，并支持从 `config.yaml.runtime` 读取 Skill 状态声明；首批通用原子 Verifier 进入共享 Pack 注册表。
- **validate-md-ref 适配 Kernel 新协议**：状态包迁移至 `references/states/`，配置声明 required/advisory Verifier，脚本执行链接完整性与引用语义两个独立检查；旧状态声明入口继续兼容。

### Added（新增）
- **状态机与验证器理论基础讨论及 Premium 系统综述**：新增 `docs/状态机和验证器的理论基础的相关讨论.md`，并在 `docs/reviews/state-verifier-theory/` 保存关于过程监督、运行时验证、因果归因、序列优化与人机协同的系统综述及 PDF/Word/BibTeX 产物；提出 State–Verifier–Causal Optimization 研究框架、可证伪问题和最小实验路线。
- **全生态 Verifier/State 设计报告**：新增 `docs/events/2026-08-27-全生态-verifier与state设计报告.md`，基于本项目及六个外部只读 Skill 生态的业务盘点，划分通用/专用 Verifier 与 State，补充 Skill 官方目录内托管约定、共享 Pack 进入 kernel 的判定门槛、逐 Skill 对接矩阵，并给出可插拔接入、门禁、证据和渐进迁移路线。
- **State ID 命名规范与兼容解析**：新增 `owner.machine.state` canonical 规则、状态 alias 和迁移约束，并同步 kernel、内置 workspace 状态、`validate-md-ref` 与项目指令。
- **Verifier ID 命名规范与兼容解析**：新增官方命名空间、领域/能力格式、版本解耦和 legacy alias 约束，并同步 kernel、`validate-md-ref` 与项目指令。
- **validate-md-ref 状态机与 Verifier 调查日记**：新增 `docs/events/2026-08-27-validate-md-ref状态机与验证器协作调查日记.md`，记录本次任务的逐步协作过程、Mermaid 流程图、结果口径差异及后续优化建议。

### Changed（变更）
- **全生态 Verifier/State 报告升级为 Kernel 优化蓝图**：补充 Runtime/原子/组合/领域四层边界、核心 State 收缩、Kernel 模块依赖、公共交接契约、兼容迁移映射和分阶段工程路线，明确该报告是实施依据而非候选清单的全量实现承诺。
- **Verifier/State 计划分层收敛**：重构 `docs/plans/2026-08-25-verifiers基础设施评估与落地计划.md`，将 Runtime 原语、原子/组合/领域 Pack、生命周期 State 与 Gate 明确分层，收缩核心状态并修正示例 ID 的版本治理。
- **补全 Runtime State 配置示例**：在全生态 Verifier/State 设计报告中补充 `initial_state` 与 `states`，并明确它们与 `state_roots` 的职责及从 `state-machine.json` 迁移到 `config.yaml.runtime` 的兼容关系。
- **AGENTS.md 结构重构与去重**：按"项目目标 → 目录边界 → `.bensz-api` 协议 → 通用协作规范 → 核心工作流 → 工程原则 → Skill 开发 → 变更记录与版本号 → Codex 适配 → 有机更新"主线重组章节；将 CHANGELOG 提醒（3 处）、`tests/`/`tmp/` 目录职责（3 处）、标题无序号规范（3 处）、隐私敏感信息禁令（4 处）各收敛为单一声明处，其余场景改为引用；合并"代码优化与修改"与"变更边界"为"修改规范与边界"，合并项目级与技能级版本号规范为"变更记录与版本号"一节，全部行为规则内涵保持不变。
- **恢复"高质量技能开发原则"完整正文**：该节自 `a2200bc` 起仅存标题（"八项原则"正文在 git 全历史中从未存在，属悬空引用），从 `8410184` 找回六项原则原始正文（硬编码/AI 功能规划、脚本路径感知、多轮自检循环、冗余残留检查、安全性检查、过度设计与通用性检查），以紧凑形式恢复并适配当前 `tests/`/`tmp/` 目录约定；同步将"技能开发流程"中的"八项质量原则"引用修正为"六项质量原则"。
- **修复"技能版本号管理规范"残缺章节**：该节在所有历史版本中仅存核心原则一句与孤立代码块残片；重建为完整的技能初始化模板（`config.yaml:skill_info.version` + CHANGELOG 条目）与语义化版本、同步顺序说明，版本号检查命令改为面向技能 `config.yaml` 的可用形式。

### Changed（变更）
- **状态机 canonical ID 重构**：`bensz-skill-kernel` 升级至 `0.10.0`，为 State 定义、Filesystem/Combined Registry、状态声明、CLI 和新快照增加 canonical ID 与 alias 解析；内置 workspace 状态及 `validate-md-ref` 状态图完成迁移。
- **拆分 Markdown Verifier 实现边界**：将 Markdown 链接、锚点和 URL 采集逻辑从 `bensz_skill_kernel.builtins` 迁移到 `markdown-link-integrity` 自有 `collector.py`，Kernel 保留通用验证基础设施与内置通用 Pack，减少领域耦合。

- **启用项目 BAC 贡献记录**：将 `AGENTS.md` 与 `README.md` 从 `init-project --disable-bac` 关闭态切换为默认强制启用态，并以 `docs/contribution.bac` 作为项目内账本路径。

- **pytest 缓存目录集中管理**：将 pytest 默认缓存目录配置为 `.bensz-api/.pytest_cache`，减少仓库根目录的运行产物噪声。

- **AGENTS.md 工作区协议改为自包含**：移除对 `/Volumes/2T01/Github/sub2api/docs/prompts/005-bensz-skill-workspace.md` 的绝对路径依赖，改为在 `AGENTS.md` 内直接声明 `.bensz-api` 任务工作区规则，确保其它用户和环境可独立使用。

- **项目系统指令对齐 init-project 最新规范**：补齐 `AGENTS.md` 的贡献记录、代码优化与修改、BAC 状态和文档同步约束，并在 `README.md` 中说明当前未启用 BAC 的原因与重新启用方式；保持 `CLAUDE.md` 的 `@./AGENTS.md` 单一引用不变。

- **validate-md-ref 强制运行时门禁**：要求每次执行先通过 `bsk` 状态机完成 `input-ready` → `checking` → `reported` 生命周期，并强制调用 `markdown.link-integrity@1.0.0` Verifier；kernel、状态转移或 Verifier 不可用时必须失败并保留诊断，不得静默降级。
- **validate-md-ref 文档分层收敛**：Skill 升级至 `0.8.1`，将状态机与 Verifier 的详细契约迁移到 `references/` 下的独立 Markdown，主 `SKILL.md` 聚焦 Markdown 引用适配、事实采集与结果汇总。
- **Verifier 包内资产迁移**：将 `bensz-skill-kernel` 的内置 `verifiers/` 移入 `src/bensz_skill_kernel/verifiers/`，CLI 和 `validate-md-ref` 通过公开 `builtin_verifier_root()` 定位，wheel package data 同步包含状态与 verifier 资产，消除对源码仓库层级的依赖。
- **状态机协议重构**：`bensz-skill-kernel` 升级至 `0.8.0`，状态包新增可选 JSON-stdio helper、系统与 Skill 状态组合发现、Skill 声明文件、转移检查与持久化标准回执；工作区为每个 Skill 保存独立元状态快照，并创建共享目录边界。`validate-md-ref` 升级至 `0.8.0`，作为声明式状态机试点。
- **macOS 系统文件忽略规则修正**：在项目级测试目录放行规则之后重新屏蔽 `.DS_Store`、AppleDouble、资源分叉和 Finder 图标元数据，避免显式放行测试资产时产生系统文件噪声。
- **状态机运行时目录化重构**：`bensz-skill-kernel` 升级至 `0.7.0`，新增可发现的元状态注册表与 BenszAPI 任务工作区解析器；通过 `bsk state` 查询状态定义、通过 `bsk workspace` 初始化和解析 Skill 的 `input`/`output`/`log` 路径，保留原有生命周期事件账本与 CLI 兼容入口。
- **Verifier 系统目录化重构**：`bensz-skill-kernel` 升级至 `0.6.0`，新增基于 `verifiers/<name>/VERIFIER.md` 的发现与执行协议，支持可选脚本、JSON stdio、超时/错误归一化和 instruction-only verifier；`validate-md-ref` 升级至 `0.7.0` 并接入 `markdown.link-integrity` 目录 verifier。
- **引用 Verifier 定位修正**：内置引用 Verifier 统一为不受文档类型限制的 `citation.truth-and-fit`；Markdown、LaTeX、Word 等仅作为输入适配器，提交论断上下文、来源元数据和来源摘录。缺少语义引擎时保守返回 `unchecked`。kernel 升级至 `0.5.0`，`validate-md-ref` 升级至 `0.6.0`。
- **恢复 validate-md-ref 的 `.bensz-api` 工作区说明**：补回 Skill 级任务根目录、`input`/`output`/`log` 分层、跨 Skill 共享材料、正式交付物分流、敏感信息保护与 legacy 路径约束。
- **AGENTS.md 增补 `.bensz-api` 任务工作区协议**：对齐 `sub2api/docs/prompts/005-bensz-skill-workspace.md`，明确任务根目录锁定、Skill 调用前透明播报、`shared`/Skill 隔离、`input`/`output`/`log` 分层、正式交付物分流、失败兜底、敏感信息保护与质量门禁。
- **validate-md-ref Skill 执行契约增强**：补充 `SKILL.md` 的适用范围、输入输出、最小执行流程和相对路径调用说明；明确脚本与直接 verifier 的配置加载差异，并增强触发描述的能力与场景信息。
- **Verifier ID 与版本解耦**：将内置 `markdown.references.v1` 重命名为稳定 ID `markdown.references`，版本统一通过 `--version` / `VerifierSpec.version` 管理；`bsk verifier run` 新增版本参数。该兼容性变更使 kernel 升级至 `0.4.0`，`validate-md-ref` 升级至 `0.5.0`。
- **validate-md-ref 使用说明简化**：将 beta Skill 的 SKILL.md 收敛为工具包、任务到命令的映射和 references 索引；移除状态机、Gate 和复杂验证流程说明，保留简单的输入输出定义（该阶段版本为 `0.4.2`）。

### Fixed（修复）
- **bensz-rmd-rules 动态 TOC 悬停抖动**：移除桌面动态 TOC 的 `border-radius` 过渡，避免圆角命中边界在展开期间变化造成 `mouseenter`/`mouseleave` 振荡；Skill 版本 `0.22.0 → 0.22.1`，并新增静态回归断言。
- **Markdown verifier 重定向安全**：`bensz-skill-kernel` 在每一跳 HTTP 重定向发起前重新校验协议、白名单、显式黑名单和私网地址，阻止公开 URL 经重定向访问内网；新增回归测试。

### Changed（变更）
- **validate-md-ref 调用契约**：Skill 与 README 明确 kernel runtime 预检、审计事件的写入副作用，以及直接 CLI 调用和 YAML 配置封装各自的域名/超时策略传入方式；Skill 升级至 `0.4.1`，kernel 升级至 `0.3.1`。

### Added（新增）
- **Skill Runtime Verifier 命令接口重构**：`bensz-skill-kernel` 新增带标签的内置 verifier 目录及 `bsk verifier list/describe/run` 命令；`validate-md-ref` 改为只声明 `markdown.references.v1`，减少 Skill 自行拼接验证与状态机细节。
- **kernel 使用说明**：新增 `packages/bensz-skill-kernel/README.md`，列出内置 verifier、标签和 Skill 调用示例。

### Changed（变更）
- **validate-md-ref Skill 文档层级收敛**：description 仅保留触发条件，正文去除重复 `#` 标题，并拆分适用范围、调用方式和验证器边界。
- **validate-md-ref 声明边界收敛**：删除未被 Runtime 消费的 `verifier-pack.yaml`、`calibration.json` 及重复 Skill 侧 Pack 注册器；回退路径统一使用 kernel 内置 verifier registry，落实 Skill 只声明调用方式与验证边界。
- **Runtime 接入调查报告状态同步**：在原始调查结论后补充 `validate-md-ref` 通过 `bsk verifier run` 写入事件账本的落地状态，区分“验证事实记录”与“领域状态转移策略”。

### Added（新增）
- **validate-md-ref Runtime 接入调查报告**：新增 `docs/events/2026-08-26-validate-md-ref与状态机验证器交互调查报告.md`，说明试点 Skill 已实现的 Verifier Pack 调用链、尚未接通的事件账本闭环，以及后续最小接入建议。

### Added（新增）
- **Verifier 原型基础设施与 `validate-md-ref` 试点**：在 `packages/bensz-skill-kernel` 增加版本化 Verifier Pack、证据快照、统一结果、保守 Gate 与可重放 kernel 事件；`skills/beta/validate-md-ref` 接入 `markdown.references.v1` hybrid Pack，在保留兼容字段的同时输出结构化验证结果和 verification gap。

### Added（新增）
- **Skill Runtime 规模化优化计划**：新增 `docs/plans/2026-08-26-skill-runtime规模化优化计划.md`，将状态机、Verifier、运行事件、用户反馈和版本治理整合为可观测、可验证、可演进的 Skill Runtime 路线，明确渐进试点、非目标、验收标准与规模化前置条件。

### Changed
- **Verifier 计划加入 NSFC 端到端 Pack 示例**：在 `docs/plans/2026-08-25-verifiers基础设施评估与落地计划.md` 增设 `nsfc-justification-writer` 的详细 Verifier 章节，展示最小证据契约、规则/Prompt/Rubric 分工、统一结果、Gate 决策、受限写入与写后核验、降级和脱敏校准集，明确领域规则通过 Pack 注入而非写入核心。
- **Verifier 计划补充架构总览**：在 `docs/plans/2026-08-25-verifiers基础设施评估与落地计划.md` 增加面向零背景读者的组件流转说明和 Mermaid 架构图，直观展示验证请求、证据采集、规则/Prompt/人工判断、结果标准化与门禁之间的关系。
- **通用 Verifiers 计划改为 Prompt/规则融合架构**：重新定义 Verifier 为可版本化、可审计的判断包，新增 Prompt Pack、Rubric、Evidence Contract、Rule Pack、混合执行模式、不确定性处理与语义/精确规则融合的实施路线；将引用核验、数学证明等仅作为通用插件示例，不把任何业务 Skill 写入核心。
- **通用 Agent Verifiers 计划重构**：将 `docs/plans/2026-08-25-verifiers基础设施评估与落地计划.md` 从开放式知识工作评价方案重构为 Agent 完成声明的通用证据与门禁层；冻结 `Subject`、`Requirement`、`Claim`、`Evidence`、`VerificationResult`、`GateDecision` 核心协议，区分检查执行状态与业务 verdict，覆盖静态产物、可执行行为、过程来源、外部状态、副作用、安全、语义质量和人工审批，并补充插件边界、信任/冲突规则、kernel 适配器及四类代表性任务验收矩阵。
- **Verifier 参考文章定位修正**：保留文章启发的专门化能力、按需路由、成本分层、依赖 DAG、早停和校准原则；将 pairwise、Meta-Judge、`ProjectSpec` 与专家偏好数据降为开放式语义质量的可选扩展，不再主导通用核心模型。
- **install-bensz-skills 安装入口契约对齐**：本地默认源收敛为 `skills/alpha`，历史 `pipelines/skills/alpha` 仅可通过显式兼容参数使用；本地与 bootstrap manifest 统一包含版本、来源、目标和逐 skill 状态核心字段，并补充安装器回归测试。
- **仓库约定一致性修正**：统一 AGENTS.md 的原则数量与标题格式，修正 Prompts.md 中 alpha/beta 的反义描述，并同步安装器 Python 支持矩阵与版本来源说明。
- **测试边界补充公开入口**：AGENTS.md 明确根级 `tests/` 可承载安装器等仓库公开入口的 smoke/integration 测试，保持测试脚本与运行产物目录分离。
- **根级功能测试显式纳入 Git**：强化 `.gitignore` 对 `tests/**/*.py` 的放行规则，明确测试脚本可版本控制，仅忽略测试缓存。
- **清理无用途的根级脚本目录**：删除空的 `./scripts/`；各 Skill 的功能脚本仍保留在自身 `skills/<channel>/<skill>/scripts/` 边界内。
- **测试过程目录约定明确**：根级 `tests/` 仅保存可执行测试脚本；测试计划、报告、artifacts、fixture、日志和缓存统一承载于 `./tmp/`，并通过 `.gitignore` 排除运行产物。
- **工作区约定文档归档**：将根目录 `WORKSPACE.md` 重命名并移动至 `docs/bensz-api-workspace.md`，使运行时工作区契约归入统一文档目录。
- **根级测试目录职责收敛**：删除历史 Skill 测试会话、报告、artifacts、fixture 与缓存；`tests/` 仅保留用于验证 `packages/` Python 包核心公开 API 的可执行脚本，包内单元测试仍保留在各自包边界内。
- **仓库目录与安装边界重构**：吸收只读 legacy 项目的 `skills/`、`packages/`、`docs/`、根级测试与工作区约定；将当前已有 Skill 迁移到 `skills/alpha/`，将 legacy 独有 Skill 迁移到 `skills/beta/`，同名 Skill 以当前仓库版本为准。
- **install-bensz-skills 安装器整合**：将根级 `@install` 标准库远程引导能力并入 `install-bensz-skills` Skill；本地与远程默认只扫描/安装 `skills/alpha/`，beta Skill 仅在显式指定 beta 源目录时处理。
- **目录治理对齐 legacy 约定**：正式 Skill 统一位于 `skills/<alpha|beta>/<skill-name>/`，运行时包位于 `packages/`，计划文档位于 `docs/plans/`，仓库级测试位于 `tests/`，清理 Skill 目录内的历史 `plans/` 与 `tests/` 夹具。
- **忽略规则同步**：调整 `.gitignore`，保留根级与包级正式测试资产，仅忽略缓存及 Skill 内历史测试/计划目录。

## [4.3.8] - 2026-08-23

### Changed
- **auto-draw-plot 升级到 `0.2.18`**：Windows、Git Bash 与 PowerShell 统一解析 Codex 配置路径，优先兼容 `%USERPROFILE%` / `%HOMEDRIVE%%HOMEPATH%` 并兼容 `HOME`；诊断证据新增实际配置路径、来源和不可逆 API Key 短指纹，便于定位配置来源。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 更新为 `v4.3.8`。

### Fixed
- **auto-draw-plot 配置冲突拦截**：当 Codex 配置与 BenszAPI 环境变量同时存在且 Base URL 或 API Key 不一致时，在提交图片请求前报告 `base_url_mismatch` / `api_key_mismatch` 并停止，避免静默读取旧配置；完整密钥不会写入诊断日志。

## [4.3.7] - 2026-08-18

### Changed
- **awesome-code 升级到 `3.0.3`，实施计划面向零背景读者**：`writing-plans` 默认假设读者没有相关专业背景，计划结构新增“通俗解释：究竟发生了什么”固定理解层——先用一句无术语的话说明发生了什么，再给出生活类比或具体场景、类比与实际问题的对应关系及改变前后差别；“问题是什么”章节升级为“专业判断：问题在哪里”，每项专业建议补充它对普通用户意味着什么；最终检查新增零背景读者复述与类比准确性门禁，类比不能歪曲事实或代替专业判断。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.3.6` 更新为 `v4.3.7`。

### Fixed
- **init-project 升级到 `2.3.6`，修复手动模式 BAC 占位符残留**：手动模式改为在 CLI 侧内联构造完整模板变量，与自动模式的 `_prepare_variables()` 解耦；按启用状态生成的五条贡献记录说明收敛为 `_bac_notes()` 单一来源供两种模式共用，修复手动模式生成的 `AGENTS.md` 残留 `{贡献记录政策说明}` 未替换占位符的问题，并恢复手动模式禁用 BAC 的内容回归断言。

## [4.3.6] - 2026-08-10

### Fixed
- **init-project 禁用 BAC 后的指令一致性**：修复 `--disable-bac` 生成的 `AGENTS.md` 仍声明 BAC“默认且强制”的问题；统一自动与手动模式的模板变量构造，确保关闭状态不残留启用态政策或未替换占位符，并补充启用/禁用分支回归测试。该修复对应 `huangwb8/bensz-bugs#3`。

### Changed
- **init-project 升级到 `2.3.5`**：README 明确关闭 BAC 后的生成结果，子技能变更日志同步记录修复范围。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.3.5` 更新为 `v4.3.6`。

## [4.3.5] - 2026-08-09

### Fixed
- **auto-draw-plot 升级到 `0.2.17`，修复 BenszAPI 子域名根地址落入边缘 HTML fallback**：`gpt-image-2` 配置加载在完成 HTTPS、子域名与路径校验后，若 base URL 仅给出子域名根地址（无路径），统一补齐 `/v1`，确保文本出图（`/v1/images/jobs/generations`）、参考图编辑（`/v1/images/jobs/edits`）、异步 job 轮询与结果下载都使用规范 API 基址，避免请求落到站点边缘层 HTML fallback；已显式配置 `/v1` 时保持不变。`SKILL.md` 与 `README.md` 同步说明该规范化行为。

### Changed
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.3.4` 更新为 `v4.3.5`。

## [4.3.4] - 2026-08-09

### Changed
- **init-project 升级到 `2.3.4`**：在所有业务输出前集中配置 `stdout`/`stderr` 编码容错，保持宿主编码不变，仅把无法编码字符的错误策略收敛为 `backslashreplace`；不支持 `reconfigure()` 的嵌入流只在底层抛出 `UnicodeEncodeError` 时转义重试，普通 `OSError` 与业务异常继续传播，修复 Windows 中文（GBK）locale 下的初始化崩溃；新增自动模式、手动模式、UTF-8 与异常传播回归测试。
- **bensz-collect-bugs 升级到 `0.4.0`**：数据模型扩展为「原始证据 + 追加式 resolution」两层结构，新增 `scripts/resolve_bug.py` 与 `templates/RESOLUTION_TEMPLATE.md`，在保留原始 `BUG_REPORT.md` / `bug-context.json` 前提下追加 `RESOLUTION.md`，支持 `fixed`、`duplicate`、`--dry-run` 与重复执行幂等检查，并补充 resolution 专项回归。
- **auto-test-project 升级到 `1.3.2`**：新增统一运行态 task-root 解析器（`scripts/workspace_paths.py`），创建、单会话验证、批量验证与自检共用 `<task-root>/auto-test-project/output/{plans,tests}`；显式 task root 支持续跑原样复用、缺省时只分配新任务、legacy 根仅允许显式只读验证。`config.yaml:directories` 只保留 task-local 相对后缀，同步更新 SKILL、README、FAQ、严格模式示例、模板与 CLI help。
- **@install 远程安装器跨平台编码容错**：对齐 init-project 的控制台编码策略，远程一键安装器在 Windows 中文（GBK）终端下使用 `--lang zh` 输出中文消息不再因 `UnicodeEncodeError` 中断；保持「仅标准库、轻量 bootstrap」设计与正常 UTF-8 输出语义不变。
- **awesome-code 文档精简**：`README.md` 移除与 `writing-plans` 现状重复的「实施计划白话主线/逐行清单」说明与对应问答，避免与 SKILL 规则双写漂移。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.3.3` 更新为 `v4.3.4`。

### Fixed
- **bensz-collect-bugs Windows GBK 解码崩溃**：`common.py` 的 `run_command` / `gh_auth_ok` 与 `report_bugs.py` 的 `gh_api` 显式指定 `encoding="utf-8", errors="replace"`，修复 Windows 中文 locale 下用系统编码（GBK）解码 `gh` 的 UTF-8 输出导致的 `UnicodeDecodeError`，提升 macOS/Windows/Linux 跨平台一致性。
- **auto-test-project 工作区迁移落地修复**：补齐此前「文档与配置已迁移、脚本仍写入 `.bensz-api/skills/auto-test-project/`」的断层，并新增 task root 越界、`..`、symlink、同分钟冲突、A/B continuation、legacy 只读与缺失路径的结构化失败测试，默认流程新增否定断言确保不再创建 `.bensz-api/skills/`。

## [4.3.3] - 2026-08-06

### Changed
- **auto-draw-plot 升级到 `0.2.16` 并明确为自包含图片工作流**：技能自身经 BenszAPI 完成 prompt、generation/edit 与多轮迭代，选中后不得默认调用或依赖 `imagegen`；只有用户明确要求同时使用 `imagegen` 时才额外调用，避免"先写 prompt 再交给 imagegen 出图"造成的重复生成与重复计费。`SKILL.md` 新增"技能边界"章节，`README.md` 同步自包含说明、fallback 边界与协议错误问答。
- **图片协议错误可观测性补齐**：`image_provider_client.py` 对 `2xx` 空正文或非 JSON 正文新增 `PROVIDER_EMPTY_RESPONSE` / `PROVIDER_NON_JSON_RESPONSE` 分类，替代原先只抛出裸解析异常；错误证据仅记录 HTTP 状态、origin/path、Content-Type、声明/实际长度、正文 SHA-256、首字节类别与重定向变化，不保存 query、鉴权头、prompt 或原始正文。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.3.2` 更新为 `v4.3.3`。

### Fixed
- **submit 端到端关联证据修复**：JSON 与 multipart 请求自动发送安全 `X-Client-Request-ID`，空/非 JSON 协议错误优先保留服务端回传的 `X-Request-ID` 与 `X-Client-Request-ID`，并对关联 ID 执行长度（≤128）和字符白名单校验；此类任务创建状态不确定的协议错误不会重试 submit、也不会跨 provider 重放，避免掩盖真实业务故障或导致重复计费。

## [4.3.2] - 2026-07-20

### Changed
- **awesome-code 升级到 `3.0.2`**：`writing-plans` 改用“问题优先”的实施计划结构，先解释现状、影响、目标和改进方向，再按需补充技术细节；计划深度会随风险调整，但高风险任务不再默认展开为机械化逐步脚本。
- **计划质量门禁完善**：`writing-plans` 明确以当前 Skill 规则为准，识别并在交付前重写旧版 `Implementation Plan`、`For Claude` 和 `Task—Files—Step` 模板；正式计划统一保存到 `docs/plans/`，中间材料归档到任务工作区。
- **版本与使用说明同步**：`awesome-code/config.yaml` 和 `pyproject.toml` 统一为 `3.0.2`，修复后者仍为 `3.0.0` 的版本漂移；README 同步说明新的计划产出边界与适用场景。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.3.1` 更新为 `v4.3.2`。

## [4.3.1] - 2026-07-19

### Changed
- **auto-draw-plot 升级到 `0.2.13`**：`gpt-image-2` 默认显式请求 `quality=low`、`size=1024x1024`、`output_format=jpeg` 与压缩质量 `85`，以可控成本生成图片；支持通过参数覆盖质量、原生尺寸、格式与压缩率，并在提交前进行白名单和范围校验。
- **图片格式与参考图契约完善**：输出按 PNG/JPEG/WebP 的文件扩展名、magic bytes 与 MIME 一致性校验；参考图编辑记录 SHA-256 与稳定来源，并在有参考图时附加主体、构图和背景保真约束。默认交付格式调整为 JPEG，旧 `--output-png` 参数仍可兼容使用。
- **README 核心能力清单更新**：补充 `auto-draw-plot` 的模式化科研绘图能力，避免首页清单与仓库实际可用技能不一致。

### Fixed
- **异步图片任务重试安全性修复**：在服务端尚未提供持久幂等语义时，generation/edit submit 固定只提交一次；`BILLING_PRICING_NOT_CONFIGURED` 等明确不可重试的计费错误立即停止，避免重复扣费或无效退避。

## [4.3.0] - 2026-07-17

### Changed
- **统一 BenszAPI 任务工作区契约**：`auto-draw-plot`、三类 auto-test、`parallel-vibe`、`git-pr-review`、`compact-bensz-skills` 及相关通用 skills 的新任务统一使用 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/`；每个实际调用的 skill 在各自 `input/`、`output/`、`log/` 边界内保存中间产物，多 skill 任务才创建共享 `shared/`。正式交付物不写入该目录，旧隐藏目录仅允许显式兼容读取、迁移或清理。
- **auto-draw-plot 升级到 `0.2.12`**：图片 provider 预检明确只覆盖配置、连接和鉴权，真实 Images submit 才判定生图资格；`gpt-image-2` 的错误记录改为脱敏结构化字段，计费、订阅、余额、权限及客户端策略错误不会触发跨 provider 回退，临时平台错误仅在同一 provider 内重试。
- **parallel-vibe 运行目录迁移**：脚本 runner 在任务根内创建 `parallel-vibe` 专用目录及标准子目录，并保留原有 plan、线程工作区和日志契约；重用目录时忽略自动创建的空分类目录，避免误判为已有运行内容。
- **首页任务工作区说明**：`README.md` 与 `README_EN.md` 新增工作区结构、跨 skill 引用和正式交付物边界，便于使用者核对本地中间产物。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.6` 更新为 `v4.3.0`。

## [4.2.6] - 2026-07-05

### Changed
- **install-bensz-skills 版本升级到 `0.5.10`**：远程 Git 源更新链路新增传输重试、Git HTTP low-speed 失败阈值、sparse checkout 失败兜底和 last-known-good 缓存复用；当远程更新失败或只能复用旧缓存时返回非零退出码，避免自动化场景误判为最新安装成功。同步更新 `SKILL.md`、README、i18n 文案与测试口径。
- **@install 标准库安装器下载稳定性优化**：GitHub zip archive 与 raw config 下载新增重试，并通过临时 `.part` 文件落盘，避免中断下载留下半成品 zip；保持无 Git、无第三方依赖的远程 bootstrap 设计。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.5` 更新为 `v4.2.6`。

## [4.2.5] - 2026-07-04

### Changed
- **install-bensz-skills 版本升级到 `0.5.8`**：新增远程仓库持久缓存——远程源 repo 缓存在 `~/.bensz-skills/installation/cache/remote-sources/`，重复远程更新时通过 `git fetch --depth 1 --no-tags` 增量更新，避免每次从零 clone；clone/fetch 均禁用 tag 拉取，缓存损坏或 Git 更新失败时自动删除并重建。同步更新 `SKILL.md`、README 与测试，进一步缩短重复远程更新等待时间。
- **@install 远程一键安装器缓存对齐评估**：经核查，v0.5.8 的持久缓存是 Git clone/fetch 专属优化；`@install` 基于 GitHub zip archive 单次下载、无 Git 依赖，天然不涉及该流程。强制对齐需引入 HTTP 条件请求（ETag/Last-Modified）或 commit-sha 失效判断，违背其「仅标准库、轻量 bootstrap」设计哲学，故按 AGENTS.md「远程拉取特有逻辑允许不同」条款保持现状。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.4` 更新为 `v4.2.5`。

## [4.2.4] - 2026-07-04

### Changed
- **install-bensz-skills 版本升级到 `0.5.7`**：远程安装在 `skills_path` 指向仓库子目录时优先使用 Git sparse checkout，只拉取目标 skills 子树；指定 `--skill` 时进一步收窄到目标 skill 目录，减少大仓库远程更新时的等待和无关内容下载。
- **远程安装对比性能优化**：同一远程源安装到 Codex 与 Claude Code 时复用远程 skill MD5 计算结果，避免重复哈希；当指定单个 skill 且某个源缺失该 skill 时，不再为了确认缺失而完整下载该源。
- **@install 标准库安装器同步优化**：保持无 Git、无第三方依赖的 bootstrap 入口，同时按 `skills_path` 和 `--skill` 选择性解压 GitHub zip archive，降低大仓库安装时的解压与扫描成本。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.3` 更新为 `v4.2.4`。

## [4.2.3] - 2026-06-28

### Changed
- **@install legacy 清单可及性同步**：远程一键安装器优先从 `install-bensz-skills/config.yaml` 读取权威 `legacy_skill_names`，支持通过 GitHub raw 配置获取，下载源内配置作为次级兜底，内置清单仅保留为 bootstrap fallback，避免远程入口复制业务清单后漂移

### Fixed
- **@install 下载失败退出码修复**：当选定远程源下载失败或无法解析 skills 根目录时，安装器现在返回非零退出码，避免自动化场景误判为安装成功

## [4.2.2] - 2026-06-28

### Changed
- **auto-draw-plot 版本升级到 `0.2.11`**：收紧 `roadmap` / `schematic` 模式的中文标签正常字宽护栏，默认要求现代黑体/思源黑体/Noto Sans CJK 风格与自然字形比例；明确禁止窄体、长体、压缩体、condensed/narrow/compressed font、横向压缩和瘦长拉伸字体，并鼓励长标签自然换行而非压缩字形；同步更新 `SKILL.md`、README、prompt 指南、配置、脚本负面 prompt 与本地 fallback prompt
- **init-project 版本升级到 `2.3.3`**：补齐 `.gitignore` 模板与 PyYAML 缺失时脚本内置兜底规则，新增 `.systematic-literature-review/`、`.complete_example/`、`.latex-cache/`、`.make_latex_model/`、`.nsfc-budget/`、`.nsfc-code/`、`.nsfc-length-aligner/`、`.nsfc-qc/`、`*.nsfc-qc/`、`.nsfc-ref-alignment/`、`.research-idea/`、`.write-paper/` 与 `.secrets/` 等中间产物和敏感目录忽略项；`.check-review-alignment/` 继续保留在模板中
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.1` 更新为 `v4.2.2`

## [4.2.1] - 2026-06-21

### Changed
- **auto-test-project 版本升级到 `1.3.1`**：将项目级测试计划与测试会话默认目录从项目根 `plans/` / `tests/` 收敛到 `.bensz-api/skills/auto-test-project/output/plans/` 与 `.bensz-api/skills/auto-test-project/output/tests/`；同步更新 `SKILL.md`、README、references、配置与脚本帮助信息，并将 `.bensz-api/skills/auto-test-project/**` 纳入 A 轮独立评估排除范围
- **auto-test-skill 版本升级到 `2.3.1`**：将 skill 测试计划与测试会话默认目录从目标 skill 根 `plans/` / `tests/` 收敛到 `.bensz-api/skills/auto-test-skill/output/plans/` 与 `.bensz-api/skills/auto-test-skill/output/tests/`；同步更新 `SKILL.md`、README、references、配置与脚本说明，并将 `.bensz-api/skills/auto-test-skill/**` 纳入独立评估排除范围
- **parallel-vibe 版本升级到 `0.4.3`**：默认运行目录从 `.parallel-vibe/` 迁移到 `.bensz-api/skills/parallel-vibe/{yyyy-mm-dd-hh-mm}/`；默认 run id 改为分钟级时间戳，同一分钟重复运行自动追加 `-02` 等后缀；`--project-id` 改为安全 run/project id，`--resume` 现在必须显式指定 `--project-id`
- **git-pr-review 版本升级到 `0.5.4`**：同步 `parallel-vibe` 目录契约，下游并行评审产物路径从 `parallel_runs/.parallel-vibe/<project_id>/` 迁移到 `parallel_runs/.bensz-api/skills/parallel-vibe/<project_id>/`，并更新 `build_parallel_review_plan.py`、`SKILL.md`、README 与集成说明
- **awesome-code 版本升级到 `3.0.1`**：将 `cache.py`、`performance_benchmark.py` 与 `mirror_optimizer.py` 的独立运行 fallback 目录迁移到 `.bensz-api/skills/awesome-code/` 或 `.bensz-api/skills/mirror-optimizer/`；测试 watch 默认忽略 `.bensz-api/`
- **仓库忽略规则更新**：根 `.gitignore` 新增 `.bensz-api`，避免本地中间产物与 release notes 草案误入提交
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.0` 更新为 `v4.2.1`

### Fixed
- **嵌套测试目录验证修复**：`auto-test-project/scripts/verify_test_session.py` 不再假设 `session_dir.parent.parent` 是项目根，可根据配置的嵌套 tests 目录推断 project root，并在缺少计划文档时输出配置化 plans 路径
- **auto-test-skill 验证配置回退修复**：`verify_test_session.py` 优先读取目标 skill 的 `config.yaml:directories`，缺失时回退到 auto-test-skill 自带配置，避免验证脚本在外部目标 skill 上丢失默认目录契约
- **嵌套镜像输出目录修复**：`awesome-code/scripts/mirror_optimizer.py` 创建输出目录时使用 `parents=True`，适配 `.bensz-api/skills/mirror-optimizer/output/` 这类多级目录

## [4.2.0] - 2026-06-21

### Added
- **auto-draw-plot 中文标签字重护栏**：`roadmap` / `schematic` 模式新增护栏——中文标签使用清晰的无衬线常规到半粗体字重、深灰或黑色，缓解“字偏瘦”观感；版本号 `0.2.9 → 0.2.10`
- **工作区目录唯一分配机制**：`auto-draw-plot`、`compact-bensz-skills`、`git-pr-review` 的工作区初始化脚本新增时间戳冲突兜底——同一分钟多次运行自动追加 `-02` / `-03` 后缀避免目录覆盖；`git-pr-review` 报告文件名与 manifest 新增 `run_id` 字段用于追溯

### Changed
- **统一中间产物目录到 `.bensz-api/` 命名空间**：将分散在各 skill 下的隐藏工作区收敛到 `.bensz-api/skills/<skill-name>/`，并结构化为 `input` / `output` / `log` 子目录，降低多 skill 并存时的目录污染与命名冲突：
  - `auto-draw-plot`：`.draw-plot/` → `.bensz-api/skills/auto-draw-plot/`
  - `compact-bensz-skills`：`.compact-bensz-skills/` → `.bensz-api/skills/compact-bensz-skills/`
  - `git-pr-review`：`.git-pr-review/` → `.bensz-api/skills/git-pr-review/`
  - `awesome-code`：`.awesome-code/{reports,benchmarks,logs,cache}` → `.bensz-api/skills/awesome-code/{output/reports,output/benchmarks,log,cache}`；镜像优化产物 `.mirror/` → `.bensz-api/skills/mirror-optimizer/output/`
  - `auto-test-code`：`tmp/` + `tests/` → `.bensz-api/skills/auto-test-code/{yyyy-mm-dd-hh-mm}/output/tests/`
  - `auto-test-project` / `auto-test-skill`：`tests/` → `.bensz-api/skills/<skill>/output/tests/`
  - 各 skill 的 `SKILL.md`、`README.md` 与初始化脚本同步更新路径契约
- **统一时间戳与 run_id 格式**：时间戳从 `%Y%m%d%H%M%S%f`（密集无分隔）改为 `%Y-%m-%d-%H-%M`（可读分隔）；`run_prefix` 由 `run-` / `run_` 收敛为空；`auto-test-code` 的 `create_session.py` 兼容新旧两种 run_id 格式
- **parallel-vibe 工作区更名**：默认目录 `.parallel_vibe/` → `.parallel-vibe/`（下划线改连字符），`copy_exclude` 同步更新；下游 `git-pr-review` 的并行评审产物路径与集成文档同步；版本号 `0.4.1 → 0.4.2`
- **git-pr-review 校验逻辑适配**：`validate_review_artifacts.py` 隐藏目录校验放宽为“路径含 `.bensz-api` 或目录名以 `.` 开头”；报告名正则适配新时间戳格式（含可选 `-NN` 后缀）
- **init-project .gitignore 模板**：新增 `.bensz-api/`、`/.bensz-api/`、`.parallel-vibe/` 忽略规则（保留 `.parallel_vibe/` 兼容旧产物）；版本号 `2.3.1 → 2.3.2`
- **install-bensz-skills legacy 清理**：将已弃用的 `nsfc-roadmap`、`nsfc-schematic` 加入 `legacy_skill_names`，安装时自动清理系统级残留目录；版本号 `0.5.4 → 0.5.5`
- **awesome-code 文档规范化**：`SKILL.md` 移除序号化标题前缀（如“代理团队（14 个子代理）”→“代理团队”），符合“层级标题不使用序号前缀”规范；`code-reviewer` 输入说明泛化计划文档来源（`PLAN.md` / `docs/plans/*.md` 等）
- **awesome-code frontend-specialist 增强**：补充表单与输入控件整齐度策略，覆盖输入框高度阶梯、宽度栅格、label/help/error 文案规则、行内基线对齐、状态样式与移动端表单分组
- **AGENTS.md 双安装器同步约束**：新增“双安装器与业务逻辑同步”章节，明确 `install-bensz-skills/scripts/install.py`（本地开发版，单一真理来源）与 `@install/install.py`（远程一键版）必须保持业务逻辑对齐，安装器业务变更时强制联动检查

## [4.1.3] - 2026-06-14

### Added
- **新增技能**：
  - `awesome-code`: 多代理协作开发技能，支持并行协调开发
  - `better-prompt`: Prompt 优化技能，基于 OpenAI 和 Anthropic 最佳实践
  - `parallel-vibe`: 并行 Vibe Coding 技能，支持多工作区并行尝试
  - `write-skill-readme`: 技能文档生成器，自动生成用户友好的 README.md
- **PR 审查归档**：
  - `docs/pr-reviews/Git-PR-Review_huangwb8_skills_pr-1_20260330184127.md`：新增对 `huangwb8/skills#1` 的评估报告，记录对外部 Tessl 评分优化 PR 的审查结论与证据
- **@install/**: 新增快速安装脚本目录
  - `install.py`: 基于 Python 标准库的单文件跨平台安装器
  - `README.md`: 安装说明文档
  - 支持通过一行 Python 命令从 GitHub 远程安装所有技能

### Changed
- **项目指令新增"双安装器业务逻辑同步"约束**：
  - 在 AGENTS.md「本机可发现性（系统级安装）」章节新增子节，明确 `install-bensz-skills/scripts/install.py`（本地开发版，安装逻辑单一真理来源）与 `@install/install.py`（远程一键版）必须保持业务逻辑对齐
  - 强制联动：当 `install-bensz-skills` 发生业务逻辑变更时，必须检查 `@install/install.py` 是否需要同步对齐；仅远程拉取特有逻辑（下载、解压、远程源发现）允许差异
- **项目指令文档重构**：
  - 重构 AGENTS.md，优化工程原则和工作流说明
  - 精简 CLAUDE.md，通过 `@./AGENTS.md` 引用核心指令
  - 统一文档格式规范：层级标题不使用序号前缀
- **README.md 首页重构**：
  - 按当前仓库状态重写首页结构，突出“技能库 + 技能开发流水线”的双重定位
  - 刷新核心技能清单，补充 `bensz-collect-bugs`、`git-pr-review` 等新增能力
  - 同步 `init-project` 与 `awesome-code` 的最新能力口径：补充标准 `docs/` 目录初始化、三层代理分派与 required agent 门禁说明
  - 优化快速开始、安装方式、项目结构和维护流程说明，降低新读者理解成本
  - 保留演示视频与 AI 算力视频入口，维持首页导览信息完整性
  - 同步对齐 `README_EN.md`，使中英文首页结构与信息范围保持一致
  - 为中英文首页标题补充克制风格的 emoji，提高辨识度与视觉质感
- **README 安装说明同步**：
  - 将首页快速开始口径更新为以 `@install/install.py` 标准库远程安装器为推荐入口
  - 明确一键安装默认会安装 `general`、`research`、`anthropic-docs` 三个远程源
  - 补充 `--source`、`--codex`、`--claude`、`--check`、`--lang zh` 等常用参数示例
  - 同步更新 `README_EN.md`，保持中英文安装说明一致
- **git-commit 技能增强**：
  - 实现动态语言检测，自动识别项目主要语言
  - 新增 `--lang` 参数，支持手动指定提交信息语言
- **install-bensz-skills 技能优化**：
  - 实现脚本路径感知机制
  - 新增配置化管理，支持自定义安装源
  - 配合 `@install/install.py` 形成远程快速安装与本地开发安装两类入口
- **@install 安装器重构**：
  - 将跨平台快速安装入口收敛为单文件 Python 脚本，降低 shell/PowerShell/CMD 多入口维护成本
  - 安装流程改为仅依赖 Python 标准库，不再要求 Git 或 PyYAML 作为启动期依赖
  - 默认安装语言调整为英文，保留中文输出选项
- **@install 安装器策略对齐**：
  - 为标准库远程安装器补齐 `--skill` 单技能过滤能力，支持重复传入和逗号分隔
  - 多远程源安装时只处理匹配的 production skill，并对缺失或非生产 skill 给出明确提示
  - 同步更新 `@install/README.md` 参数说明
- **文档规范化**：
  - 统一所有技能的 `description` 为单行格式
  - 统一 `metadata.author` 为 "Bensz Conan"
  - 新增 WHICHMODEL 模型选择指南
- **README.md**: 优化安装方法说明
  - 将推荐安装方式调整为一行远程安装
  - 将克隆仓库后的脚本安装定位为本地开发安装
  - 保留 AI 调用 `install-bensz-skills` 的自然语言安装方式
  - 更新项目结构，添加新增技能说明

### Fixed
- 修复 init-project 技能配置与脚本兼容性问题
- 修复 `install-bensz-skills` 远程安装对“仓库根目录即 skills 根目录”布局的兼容性问题
  - 安装器现在会在 `skills_path` 缺失时自动回退并识别仓库根目录
  - 修正 `general` 远程源配置为 `skills_path: "."`，恢复 `@install` 默认远程安装链路

## [0.1.0] - 2025-01-25

### Added
- 初始化 skills 仓库
- 添加核心技能：init-project, install-bensz-skills, git-commit, git-publish-release
- 添加测试技能：auto-test-skill, auto-test-project
- 添加项目文档：AGENTS.md, CLAUDE.md, README.md, README_EN.md
