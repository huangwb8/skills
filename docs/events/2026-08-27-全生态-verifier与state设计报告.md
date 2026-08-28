# 全生态 Verifier 与 State 设计报告

## 报告结论

这套生态不需要把每个 Skill 改造成一个“大状态机”，也不需要把业务规则搬进 kernel。最稳妥的方案是把 Verifier 与 State 设计成可选的外挂层：Skill 继续拥有自己的领域逻辑、脚本、提示词和正式产物；运行时只在输入、关键阶段、写入前后和交付前挂接少量标准检查。

建议采用“官方 Skill 目录内托管 + kernel 共享复用”的分层方式：

- `bensz-skill-kernel` 提供稳定的协议、注册表、证据快照、结果归一化、Gate、事件和系统工作区状态，并只托管跨多个 Skill/生态复用的通用 Pack。
- 单个 Skill 专用的 Verifier 与 State Pack 按 Agent Skills 目录习惯托管在自身 `references/` 与 `scripts/` 子目录中，不新增顶层 `verifiers/`、`states/` 或独立 JSON 清单。
- 多个 Skill 共享且规则稳定的 Pack 可酌情提升到 kernel 的共享目录；Skill 仍通过 manifest/Adapter 选择它们，移除适配器后原 Skill 仍可按原有方式工作。

核心判断如下：

1. 通用 Verifier 只判断跨领域可复用的命题，如文件范围、Schema、链接、引用可追溯性、构建结果、证据新鲜度、密钥脱敏、授权和远程副作用；不把 NSFC、临床或 Sub2API 术语写进核心。
2. 专用 Verifier 只判断一个稳定领域契约，如 NSFC 章节结构、病例红旗闸门、Sub2API 账单税额、dudu 订阅字段白名单。它们随领域 Skill 发布，不改变 kernel 的运行协议。
3. 通用 State 描述“已经成立的阶段”，不描述命令或实现；专用 State 描述领域阶段，但只做交接和不变量标记，不承载检索、推理、排版或 API 业务逻辑。
4. 确定性规则优先，语义判断后置；规则失败不能被模型平均分覆盖，证据不足必须返回 `unchecked`/`uncertain` 并进入 `wait` 或 `manual_review`。
5. 只读任务与远程写任务使用不同 Gate。远程写入必须有授权、幂等键、执行前快照、后置回查和“未知状态”分支，绝不把重试当成确认。

本报告的工程定位也需要明确：这里的“建议目录”不是一次性全部实现清单，而是候选能力地图；真正进入 `bensz-skill-kernel` 的内容必须先通过分层、复用、可重放和安全门槛。实施时应以“先冻结协议、再实现核心、最后迁移 Skill”为顺序，禁止根据单个 Skill 的临时需求直接扩张 kernel。

### 给 Kernel 优化的执行摘要

将整个系统收敛为以下责任链：

```text
Runtime 原语 → 原子 Verifier → 组合 Pack → 领域 Pack
       ↓              ↓             ↓          ↓
  事实/投影/证据   局部可证命题   多检查编排   Skill 专业契约
                         └────── Gate 独立决策层 ──────┘
```

第一阶段只实现 Runtime 原语和小型核心白名单；第二阶段通过兼容 Adapter 接入现有 Skill；第三阶段才把经两个以上 Skill 验证过的组合能力提升为共享 Pack。State 采用同样的分层：Kernel 只维护有限生命周期，Skill 业务阶段进入 `phase` DAG，等待原因、远程副作用和结果口径作为正交字段保存。

本报告后续出现的“已实现”“候选”“规划”分别表示：当前仓库已有可运行代码、设计上允许但尚未进入核心、需要按本路线实施；三者不得在迁移计划中混写。

## 盘点范围与证据

本报告于 2026-08-27 对以下 Skill 根目录进行只读扫描：本项目 `skills/`、ChineseResearchLaTeX、dudu、bensz-devtools、case_analysis、sub2api 运营和 sub2api。外部目录没有写入、上传、删除或修改。

盘点方法包括：读取每个 `SKILL.md` 的 frontmatter、输入/输出/工作流/安全边界；统计脚本、参考文档、测试和计划目录；检查现有 `VERIFIER.md`、`STATE.md`、`state-machine.json`、kernel API 和历史设计文档。扫描索引保存在本轮任务工作区的 `shared/output/skill-inventory.json`，不作为正式交付物。

### 规模与复杂度信号

| 生态 | `SKILL.md` 数量 | 说明 | 总行数（含说明） | 脚本数 | 参考/测试特征 |
|---|---:|---|---:|---:|---|
| 本项目 `skills/` | 38 | 24 个直接 Alpha/Beta Skill，另有 14 个 awesome-code 专家/协调 Skill | 9,232 | 85 | 105 个 references；覆盖安装、测试、Git、文档、图像、Rmd、引用和运行时 |
| ChineseResearchLaTeX | 25 | NSFC、SCI、论文、学位论文、简历及迁移/研究工具 | 3,967 | 178 | 大量渲染、字数、引用、像素比较和模板脚本 |
| dudu | 1 | prompt 优化流水线 | 199 | 7 | 有 plans、references、tests，依赖 awesome/parallel 协作 |
| bensz-devtools | 4 | 3 个远程桥梁 Skill，含一个历史兼容副本 | 686 | 31 | API 连接、鉴权、写入确认、幂等和冲突处理 |
| case_analysis | 9 | 从 raw 到 MDT/report 的病例链 | 580 | 0 | 以阶段交接文件和来源锚点为主，测试/计划在各 Skill 目录 |
| sub2api 运营 | 9 | 8 个直接 Skill，含历史兼容副本 | 1,605 | 20 | 真实站点只读采集、Rmd、账单、容量和敏感数据边界 |
| sub2api | 2 | 生图与 API Prompt 模板 | 199 | 18 | JSON 契约、路由元数据、测试和计划 |

行数不是质量评分，但能说明为什么需要“少量通用外挂 + 少量领域 Pack”：研究/模板生态的复杂性集中在长流水线和渲染，病例生态集中在证据交接和安全闸门，运营生态集中在远程状态和敏感数据；它们不应共享一套臃肿的业务状态。

### 业务逻辑分层

| 业务层 | 代表 Skill | 真实工作 | 主要风险 | 最合适的外挂 |
|---|---|---|---|---|
| 文本/Prompt 变换 | `better-prompt`、`prompt-programming`、`dudu-optimize-prompt`、`sub2api-prompts` | 理解意图、重写提示、维护 JSON 模板 | 语义漂移、字段漏项、路由误判 | Schema/字段/版本 Verifier；可选 Prompt Rubric；`draft → reviewed → published` State |
| 本地确定性转换 | `any-picture-format`、`md-to-word`、`download-fulltext-pdf`、`sub2api-ip-proxy`、`ycy-get-acounts` | 解析、转换、下载、格式化 | 覆盖输入、格式错误、凭据泄露 | 文件范围、Schema、输出存在、敏感扫描、转换结果 Verifier |
| 长流水线研究 | `research-literature-review`、`research-plan`、`research-idea`、`paper-select-journal` | 检索→去重→评分→选文→写作→渲染 | 网络失败、证据过时、恢复错位、引用不实 | 证据来源/新鲜度、阶段完整性、引用一致性、渲染和恢复 Verifier；阶段 State |
| LaTeX 工程 | `make-latex-model`、`transfer-old-latex-to-new`、`paper-write-sci`、`nsfc-*` | 项目/公共包分层、最小修改、PDF/DOCX/像素验收 | 改错层、破坏模板、数字/术语漂移 | 写入范围、编译、跨格式一致、章节/字数/引用专用 Pack |
| 质量/协作 | `auto-test-*`、`awesome-code`、`parallel-vibe`、`code-reviewer` | 多轮检查、并行方案、汇总与审查 | 结果互相覆盖、缺少独立证据、假通过 | 计划/结果 Schema、thread 完整性、汇聚和 Gate；协调 State |
| 临床证据链 | `case-intake-manager` → `case-structuring-extractor` → `triage-problem-gatekeeper` → `clinical-reasoning-engine` → `evidence-orchestrator` → `mdt-panel-and-report-writer` | raw 资料到事实、时间线、红旗、推理、循证、报告 | 漏读、把推断当事实、漏红旗、处方越权 | 来源锚点、缺失/冲突、红旗、证据时效、报告结构专用 Pack；阶段 State |
| 远程配置桥梁 | `dudu-vibe-config`、`bensz-channel-vibe-config`、`bensz-notes-vibe-config` | 受限 API 的读、写、同步、发布 | 越权、重复写入、发布副作用、revision 冲突 | 授权、只读范围、幂等、快照/回查、发布安全专用 Pack；effect State |
| Sub2API 运营 | `sub2api-summary`、`sub2api-account-cost`、`sub2api-add-users`、`sub2api-reimbursement`、`sub2api-codex-available` | 真实站点采集、成本/容量/报销/E2E 诊断 | 密钥和用户隐私、计费错误、把轻量 HTTP 当 Codex 证明 | 脱敏、端点覆盖、计费公式、容量保守性、目标账号命中、发票税额专用 Pack |

## 设计边界：什么属于外挂，什么仍属于 Skill

### Kernel 应该做什么

- 解析 `VERIFIER.md`、`STATE.md` 和可选声明，校验 canonical ID、版本和 alias。
- 冻结证据摘要与内容哈希，记录来源类型、采集方式、新鲜度和脱敏状态。
- 以统一 JSON-stdio 边界启动规则/探针 helper，处理超时、非零退出和非法 JSON。
- 把结果归一化为 `execution_status`、`verdict`、`findings`、`facts`、`evidence_refs`、`confidence` 和 `uncertainty_reason`。
- 应用保守 Gate，追加可重放的 `verification.result` / `verification.gate` 事件。
- 维护系统工作区状态、状态快照和生命周期事件；不取代现有事件账本。

### Skill 仍然拥有的东西

- 领域输入解析、检索策略、写作风格、医学推理、计费公式、远程 API 路径和正式产物格式。
- 何时调用哪个 Pack、哪些结果是 required、哪些只是 warning 的选择。
- 对用户的解释、修复建议和人工决策；Verifier 不能替用户做处方、发布或商业判断。

### 四层架构与进入 Kernel 的门槛

为了避免“通用”逐渐变成无边界的大目录，所有新增能力先归入四层：

| 层级 | 稳定职责 | 示例 | 默认托管位置 |
|---|---|---|---|
| Runtime 原语 | 保存事实、投影、证据、产物、执行上下文和 Gate 输入 | `Run`、`Event`、`Projection`、`Contract`、`Evidence`、`Artifact`、`VerificationResult`、`Effect` | `packages/bensz-skill-kernel` |
| 原子 Verifier | 证明单个局部、可重放、与领域无关的命题 | 合同/Schema、路径范围、文件存在、diff、脱敏、事件完整性 | Kernel 核心白名单 |
| 组合 Pack | 编排原子规则、只读探针、Prompt 或人工结果 | 渲染成功、链接完整性、引用可追溯、跨格式一致、远程回查 | Kernel 可选共享目录 |
| 领域 Pack | 判断领域契约、术语和语义质量 | NSFC 章节、病例红旗、Sub2API 账单、论文论证 | 对应 Skill 的 `references/` 与 `scripts/` |

只有同时满足以下条件，组合 Pack 才能从 Skill 专用实现提升为 Kernel 共享能力：

1. 至少两个已发布 Skill 已经重复使用，并且不是一次性复制；
2. 判断命题稳定，能通过 `subject/evidence/requirements` 表达；
3. 不依赖某个 Skill 的目录、模型、业务术语或私有 API；
4. 有独立版本、校准/回归测试、兼容策略和拆卸性验证；
5. 不引入敏感数据、远程写入或领域依赖到 Kernel。

未达到门槛的能力保留在 Skill 内部，即使它看起来“很通用”也不提前注册为官方 Verifier。Kernel 的首版原子白名单固定为：

```text
bensz.contract.conformance
bensz.artifact.path-scope
bensz.artifact.schema-conformance
bensz.artifact.file-existence
bensz.source.diff-scope
bensz.security.secret-redaction
bensz.evidence.provenance
bensz.runtime.event-integrity
bensz.runtime.state-transition
bensz.runtime.task-completeness
```

`Gate` 不属于某个 Verifier：Verifier 只返回局部事实、finding、证据引用和不确定性；Gate 根据 Skill Contract、严重度和不确定性计算 `allow`、`allow_with_warnings`、`reject`、`wait` 或 `manual_review`。这样可以阻止一个“语义通过”覆盖另一个 required 规则的确定性失败。

### Skill 内部目录与 Pack 托管约定

Skill 的顶层目录应尽量遵守 Agent Skills 官方形态，只保留 `SKILL.md`、`references/` 和 `scripts/` 等标准入口；本项目已经接受的 `README.md` 与 `config.yaml` 作为兼容扩展继续保留。专用 Verifier/State 不再新增为顶层目录，建议采用以下布局：

```text
<skill>/
├── SKILL.md
├── README.md
├── config.yaml
├── references/
│   ├── verifiers/
│   │   └── <verifier-slug>/VERIFIER.md
│   └── states/
│       └── <state-slug>/STATE.md
└── scripts/
    ├── verifiers/<verifier-slug>/verify.py
    └── states/<state-slug>/check.py
```

- `references/verifiers/<slug>/VERIFIER.md` 是领域 Verifier 契约；`references/states/<slug>/STATE.md` 是领域 State 契约。
- 可执行入口统一放在 `scripts/` 下，并按 `verifiers/`、`states/` 镜像分组；不把运行缓存、测试夹具或历史计划放入 Pack 目录。
- `config.yaml` 的 `runtime` 节声明 Pack 根目录、精确版本、调用阶段、required/advisory 策略，以及 State 的 `initial_state` 和 `states` 声明集合。不要再为同一 Skill 新增 `runtime.json`、`verifier-manifest.json` 或 `state-machine.json` 等重复清单。
- `SKILL.md` 只说明触发条件、Adapter、调用时机和结果解释；详细契约按需从 `references/` 读取。
- `VERIFIER.md`/`STATE.md` 中的入口路径相对于 Skill 根目录解析，Kernel 必须校验入口仍位于 Skill 根目录内，禁止路径遍历或执行 Skill 外部文件。

这一约定不改变 Verifier/State 的 canonical ID、版本和 alias 规则；物理位置是托管实现，不是公开身份。

### 共享 Pack 进入 kernel 的判定

多个 Skill 共享并不自动意味着 Pack 必须进入 kernel。只有同时满足以下条件时，才建议提升为 kernel 共享 Pack：

1. 至少两个已发布 Skill 或生态已经重复使用；
2. 判断命题跨 Skill 稳定，输入可通过通用 `subject/evidence/requirements` 表达；
3. 不依赖某个 Skill 的业务术语、目录结构、模型或私有 API；
4. 具备独立的版本、测试、变更记录和兼容策略；
5. 纳入 kernel 不会引入领域依赖、敏感数据或远程副作用。

未同时满足时，即使存在复用，也先由领域 Skill 或独立领域 Pack 托管。进入 kernel 后仍需由调用 Skill 提供 Adapter，Kernel 只负责发现、执行、归一化和 Gate，不承载领域流程。

### 拆卸性验收

每个接入 Skill 都应通过一次“拔掉外挂”测试：删除或禁用 `runtime` 适配器后，原有脚本、Prompt、输出目录和用户入口仍能运行；只失去标准验证/状态审计，不应失去核心业务能力。反向地，挂回适配器后不得改变原有输入文件和正式产物语义，只增加检查、事件和可见边界。

## Verifier 体系

### 统一 Pack 契约

每个 Verifier Pack 使用 `owner.domain.capability` canonical ID，版本独立记录；组件级 Rule/Prompt、输入 Adapter 和单次运行 ID 不提升为顶层 ID，除非它们需要独立注册和复用。

```yaml
id: bensz.document.schema-conformance
version: 1.0.0
mode: rule                 # rule | prompt | hybrid | human
tags: [common, artifact]
subject_kinds: [json, yaml]
evidence_requirements:
  - subject.snapshot
  - schema.snapshot
components:
  rules: [parse, required-fields, enum-values]
  prompts: []
uncertainty_policy:
  missing_required_evidence: unchecked
  tool_unavailable: manual_review
  required_rule_failure: reject
```

结果必须区分“执行失败”和“命题不成立”：网络超时是 `timed_out`，脚本崩溃是 `error`，证据不存在是 `unchecked`，规则反例是 `fail`，语义证据冲突是 `uncertain`。Gate 只看预先声明的严重度和不确定性政策，不重新发挥领域直觉。

### 通用 Verifier 候选目录

下列能力建议进入 `bensz` 通用目录。它们跨至少两个生态有复用价值，且不依赖某个 Skill 的业务术语。

| Canonical ID | 模式 | 证明的命题 | 最小证据 | 默认 Gate |
|---|---|---|---|---|
| `bensz.artifact.file-existence` | rule | required 文件是普通文件 | 规范化路径 | fail→reject |
| `bensz.artifact.path-scope` | rule | 读写只发生在允许目录/文件 | 前后文件清单、哈希 | fail→reject |
| `bensz.artifact.schema-conformance` | rule | JSON/YAML/NDJSON 符合 Schema | 文档快照、Schema 版本 | fail→reject |
| `bensz.artifact.encoding-format` | rule | 编码、扩展名和 MIME/魔数一致 | 文件元数据 | fail→reject |
| `bensz.artifact.render-success` | rule | PDF/DOCX/HTML 能由声明入口生成并打开 | 构建日志、产物探测 | fail→reject |
| `bensz.artifact.cross-format-consistency` | hybrid | LaTeX、PDF、Word 等派生物的关键字段一致 | 源/派生物摘要 | fail→reject；抽取失败 manual_review |
| `bensz.document.link-integrity` | rule | URL、相对路径和锚点可达且无 SSRF 越界 | 链接事实、网络策略 | fail→reject |
| `bensz.document.citation-traceability` | hybrid | 引用 key/DOI/URL 可定位，来源身份可复核 | Bib/metadata/URL | 缺失→manual_review |
| `bensz.document.section-contract` | rule | 标题骨架、必需章节和顺序满足契约 | AST/标题序列 | fail→reject |
| `bensz.document.length-budget` | rule | 字数/页数落在声明范围 | 去命令文本计数、配置 | advisory；硬限超出才 reject |
| `bensz.source.diff-scope` | rule | 只有声明文件发生预期改变 | before/after 快照 | fail→reject |
| `bensz.source.build-and-test` | rule | 官方构建、单测或 smoke 通过 | 命令、退出码、摘要 | required failure→reject |
| `bensz.evidence.provenance` | rule | 每个关键结论有来源、时间和哈希 | Evidence 列表 | 缺失→manual_review |
| `bensz.evidence.freshness` | rule | 证据不超过任务声明的新鲜度 | `collected_at`、阈值 | 过期→warning/manual_review |
| `bensz.security.secret-redaction` | rule | 输出/日志无 Key、Token、Cookie、密码和隐私字段 | 递归扫描摘要 | fail→reject |
| `bensz.security.authorization-scope` | hybrid/human | 本次动作获得了足够且明确的授权 | 用户确认、scope、命令 | 缺失→wait |
| `bensz.remote.read-only-scope` | rule | 只调用 GET/HEAD/声明的无副作用端点 | HTTP 方法/路径日志 | fail→reject |
| `bensz.remote.idempotency` | rule | 写 effect 有稳定键且重复执行可识别 | effect_id、幂等键 | 缺失→reject |
| `bensz.remote.postcondition` | hybrid | 写入后回查到目标状态 | 前后快照、回查响应 | 未知→wait/manual_review |
| `bensz.runtime.event-integrity` | rule | NDJSON 序号、哈希链和 evidence refs 可重放 | events.ndjson | fail→reject |
| `bensz.runtime.state-transition` | rule | 当前 State 到目标 State 合法且前置条件满足 | State registry、快照 | fail→reject |
| `bensz.runtime.task-completeness` | rule | required 阶段、产物、验证和交付报告齐全 | manifest、事件投影 | 缺失→reject |
| `bensz.coordination.thread-completeness` | rule | 每个 thread 有隔离结果、退出状态和汇聚引用 | plan、RESULT、done | 缺失→reject |
| `bensz.prompt.contract-conformance` | hybrid | Prompt/JSON 模板字段、版本、路由描述完整 | 模板 JSON、Schema、示例 | fail→reject |

其中现有 `bensz.artifact.file-existence`、`bensz.document.markdown-link-integrity` 和 `bensz.evidence.citation-truth-fit` 已经提供可复用起点。建议将当前命名为 `citation-truth-fit` 的 instruction-only Pack 保留为语义层，不把 URL 可达性误报为引用真实性。

### 专用 Verifier Pack

专用 Pack 只在满足“领域规则稳定、至少一个 Skill 反复需要、可明确写出证据契约”时新增。建议首批如下：

| 领域 Pack | 建议 ID（示例） | 关键规则/语义 | 不应做的事 |
|---|---|---|---|
| NSFC 写作 | `bensz.nsfc.justification-contract` | 立项依据四段闭环、科学问题/假说、引用键、章节写入范围、术语对位 | 不判断“能否获资助”，不替作者补事实 |
| NSFC 质控 | `bensz.nsfc.qc-findings` | P0/P1/P2 findings Schema、引用证据包、只读源文件、并行结果聚合 | 不直接改 `.tex/.bib` |
| LaTeX 模板 | `bensz.latex.template-build` | 产品线入口、编译、公共包影响项目回归、像素 compare | 不把所有产品线入口写入 kernel |
| 文献综述 | `bensz.research.review-pipeline` | 去重后单一候选集、评分字段、选文/Bib 一致、PDF/Word 交付 | 不把简单检索包装成系统综述 |
| SCI 论文 | `bensz.paper.manuscript-consistency` | 章节职责、数字/缩写/图表一致、协作模式禁止写回 | 不评判期刊接收概率 |
| Rmd 分析 | `bensz.analysis.rmd-interpretation` | 图表/表格有数据锚定解读、矢量 PDF、JPG 视觉检查、HTML widget 可见性 | 不凭模板套话生成结论 |
| 病例事实 | `bensz.clinical.fact-provenance` | raw 全读、来源锚点、事实/推断/冲突分离 | 不做诊断排序 |
| 病例安全 | `bensz.clinical.red-flag-triage` | 红旗置顶、急诊/加急门诊/观察分流、关键缺失信息 | 不给处方级长期方案 |
| 病例报告 | `bensz.clinical.report-contract` | 固定章节、证据链接、时效警告、三类就医清单 | 不重写上游事实 |
| dudu/Vibe | `bensz.remote.vibe-connection` | connect→操作→disconnect、heartbeat terminate、路径 allowlist | 不绕过 Vibe API 修改源码 |
| notes/channel | `bensz.remote.content-publish-safety` | 草稿优先、发布显式确认、revision/hash、软删除和回查 | 不用重复写入测试成功 |
| Sub2API 账号 | `bensz.sub2api.account-data-safety` | 白名单字段、代理/凭据脱敏、只读端点和覆盖率 | 不保存完整账号或代理凭据 |
| Sub2API 容量/成本 | `bensz.sub2api.capacity-cost-model` | 永久失效与临时不可用区分、池缺口不可被其它池抵消、情景口径标注 | 不把估算当事实，不直接补账号 |
| Sub2API Codex | `bensz.sub2api.codex-route-proof` | 本地 Codex E2E、目标 `account_id` usage 命中、前后差异 | 不以一次 `/responses` 成功冒充 Codex CLI 证明 |
| Sub2API 报销 | `bensz.sub2api.invoice-reconciliation` | 服务消费与充值分离、净额/税额/含税合计、订单锚定、附件命名 | 不输出银行卡/身份证，不重复计入邀请码余额 |
| Sub2API Prompt | `bensz.sub2api.prompt-template-contract` | `description`/`routing_description`/`tags`、模型路由和版本兼容 | 不把模型名或 Gate 策略写进 ID |

专用 Pack 的输入通过 Adapter 转换为通用 `subject/evidence/requirements`，而不是让 kernel 认识 `NSFC`、`account_id` 或 `红旗` 字段。这样可在未来替换领域脚本或提示词而不破坏运行时。

## State 体系

### State 的语义规则

继续遵循 `docs/state-id-naming.md`：canonical ID 使用 `owner.machine.state`，版本独立记录，状态名描述稳定阶段而不是动作；alias 只为兼容旧名。状态机只验证转移和不变量，阶段业务仍由 Skill 脚本执行。

现有 `bensz.workspace.ready` / `bensz.workspace.closed` 和 `validate-md-ref` 的三阶段状态是正确起点。不要把现有 runtime 的 `planned/active/checking/delivering/completed` 粗暴替换成 Skill State；前者是生命周期投影，后者是可插拔元状态，两者通过事件和 Adapter 对齐。

从工程实现角度，Kernel 只冻结八个生命周期状态：`planned`、`active`、`waiting`、`checking`、`delivering`、`completed`、`failed`、`cancelled`。`waiting` 的具体原因写入 `wait_reason`（如 `input`、`authorization`、`approval`、`dependency`、`children`、`quota`），不为每种原因新增 State。Skill 的 `raw-indexed`、`facts-structured`、`deduplicated`、`rendered` 等阶段属于 `phase` DAG；远程副作用属于 `effect_status`；`success`、`partial`、`degraded` 等属于闭合后的 `outcome`。

因此，本节后续的“可选元状态 Pack”是可组合的设计候选，不等于全部进入 Kernel 的 canonical 状态集合。新增 State 必须证明生命周期语义无法由上述字段表达，并通过兼容、重放和迁移评审。

### 可选元状态 Pack（不是 Kernel 核心生命周期）

以下状态可作为面向 CLI、适配器或旧协议的细粒度投影（按需启用，不要求所有 Skill 都声明）。它们应映射到上面的八个生命周期状态，而不是再增加一套彼此独立的事实来源：

| State ID | 成立条件/不变量 | 典型下一状态 |
|---|---|---|
| `bensz.workspace.ready` | 任务根目录已锁定，input/output/log 可用 | 任意声明的 Skill 状态 |
| `bensz.task.input-ready` | 输入已定位、可读、范围明确 | `bensz.task.plan-ready` 或等待 |
| `bensz.task.plan-ready` | requirements、预算、写入范围和验证计划已冻结 | `bensz.task.execution-ready` |
| `bensz.task.evidence-ready` | 必需证据已收集、脱敏、带哈希 | `bensz.task.execution-ready` / waiting |
| `bensz.task.execution-ready` | 前置条件和授权满足，可运行原 Skill | `bensz.task.executing` |
| `bensz.task.executing` | Skill 正在执行，产物/事件持续记录 | `bensz.task.verifying` / waiting |
| `bensz.task.verifying` | 关键结果已产生，Verifier 正在运行 | `bensz.task.delivery-ready` / waiting |
| `bensz.task.delivery-ready` | required 产物和 Gate 满足交付前条件 | `bensz.task.reported` |
| `bensz.task.reported` | 结果已向用户报告且不确定性已披露 | `bensz.workspace.closed` |
| `bensz.task.awaiting-input` | 缺少会改变结论的用户输入 | `bensz.task.input-ready` |
| `bensz.task.awaiting-authorization` | 需要用户授权或确认写操作 | `bensz.task.execution-ready` |
| `bensz.task.awaiting-approval` | 需要人工/专家签字 | `bensz.task.verifying` / rejected |
| `bensz.task.awaiting-dependency` | 外部工具、网络或子任务未完成 | 原等待前状态 |
| `bensz.task.failed` | 已知不可继续且保留失败证据 | 终态或人工恢复 |
| `bensz.task.cancelled` | 用户/系统取消，禁止继续副作用 | 终态 |
| `bensz.workspace.closed` | 本 Skill 不再写中间产物 | 终态 |

`awaiting-*` 是稳定等待状态；具体原因仍放 `wait_reason`（input、authorization、approval、dependency、children、quota 等），避免为每个 Skill 无限增加状态。

现有细粒度状态迁移到核心生命周期时，采用以下确定性映射，旧状态只作为兼容读取或 UI 投影：

| 旧/细粒度状态 | 核心生命周期 | 保留到哪个正交字段 |
|---|---|---|
| `input-ready`、`plan-ready`、`evidence-ready` | `planned` | `phase`、证据集合和契约快照 |
| `execution-ready`、`executing` | `active` | `phase`、`attempt_id`、工具执行事实 |
| `verifying` | `checking` | `verifications`、`gate_decisions` |
| `delivery-ready` | `delivering` | required 产物和交付前 Gate |
| `awaiting-*` | `waiting` | `wait_reason` 与恢复条件 |
| `reported` | `completed`（仅在完成守卫通过后） | `outcome`、交付报告 |

映射不得覆盖历史事件；新快照输出核心 canonical 状态，旧名称通过 alias 或投影层解释。若旧状态无法证明满足核心状态的入口条件，应进入 `waiting`、`failed` 或 `degraded`，不得直接映射为 `completed`。

### 通用副作用 State

远程桥梁和上传类 Skill 需要一个独立 effect 状态机，不应把“发布成功”混成任务 completed：

`bensz.effect.prepared → bensz.effect.authorized → bensz.effect.applied → bensz.effect.reconciled`。

异常分支为 `bensz.effect.unknown`（请求结果未知，先只读回查）、`bensz.effect.conflicted`（revision/hash 冲突）和 `bensz.effect.compensated`（已执行可控补偿）。`unknown` 绝不能自动回到 `prepared` 并重发。

### Kernel 的目标模块边界

为了让本报告可以直接指导 `packages/bensz-skill-kernel` 优化，建议把实现拆成以下模块；模块名是职责边界，不要求一次性按目录重写：

| 模块 | 必须提供的能力 | 不应承载的内容 |
|---|---|---|
| `contracts` | `Run`、`Event`、`Projection`、`Subject`、`Requirement`、`Evidence`、`Artifact`、`VerificationResult`、`GateDecision`、`Effect` 的最小 Schema | 任何 NSFC、临床或 Sub2API 字段特判 |
| `events` / `runtime` | 追加式账本、序号/哈希校验、幂等、确定性 reducer、快照重建 | Skill 自定义业务阶段的执行逻辑 |
| `states` | 系统状态发现、Skill 状态声明、canonical/alias 解析、合法转移和生命周期投影 | 检索、写作、推理、渲染等领域动作 |
| `evidence` | 摘要/哈希、来源、摘录、新鲜度、脱敏、最小化和引用解析 | 自动替用户补事实或保存完整 raw/凭据 |
| `verifiers` | Pack 注册、版本解析、JSON-stdio 执行、超时/错误归一化和结果校验 | 直接写正式产物或自行改变 Gate |
| `policy` / `gate` | required/advisory、冲突优先级、不确定性、等待和人工复核决策 | 重新解释领域语义或用总分覆盖硬失败 |
| `adapters` | 将 Skill 既有输入、阶段和产物转换为公共对象，并追加事件 | 复制一套业务流程或绕过权限边界 |

推荐的依赖方向是：

```text
contracts → events/runtime → states
contracts → evidence → verifiers → policy/gate
contracts → adapters → events/runtime
```

`verifiers` 可以调用 `evidence` 的只读接口，`policy/gate` 可以消费 Verifier 结果，但领域 Pack 不得反向修改 `contracts`、核心 State 或 reducer。这样新增领域能力时只增加 Pack 和 Adapter，不会把 kernel 变成领域流程引擎。

### 公共对象的最小交接契约

每次 Skill 运行至少要能交接以下信息；字段允许按风险裁剪，但不能用猜测填补缺失事实：

```yaml
run:
  run_id: stable-id
  skill_id: example.skill
  skill_version: 1.0.0
  runtime_protocol: bensz-skill-runtime-v1
  lifecycle: planned|active|waiting|checking|delivering|completed|failed|cancelled
phase:
  machine: skill-owned-machine
  current: skill-owned-phase
  required_before_delivery: [phase-id]
evidence_refs: [evidence-id]
artifacts: [artifact-id]
verifications: [verification-id]
gate:
  decision: allow|allow_with_warnings|reject|wait|manual_review
  unresolved: []
effect:
  status: none|prepared|authorized|applied|reconciled|unknown|conflicted|compensated
```

历史事件是事实来源；`state.json`、阶段文件和报告只是可重建投影或产物。缺少 required 字段或证据时应得到 `unchecked`、`wait` 或 `manual_review`，不能由 Runtime 自动推断为通过。

### 领域 Phase Pack（由 Skill 声明，不进入 Kernel 核心 State）

| 领域 | 建议 phase 序列（示例） | 关键不变量 |
|---|---|---|
| 研究综述 | `intake-ready → retrieval-complete → deduplicated → scored → selected → drafted → rendered → reported` | 后续阶段只能读去重集；PDF/Word 缺失不能 reported |
| LaTeX/论文 | `scope-locked → editing → compiled → compared → delivery-ready` | 公共包改动必须有受影响项目回归；协作模式不得 editing 写回 |
| 病例 | `raw-indexed → facts-structured → timeline-ready → triaged → reasoning-ready → evidence-ready → report-ready → reported` | raw 只读；红旗和缺失信息未处理不能进入深推理/报告 |
| 远程配置 | `connected → snapshot-ready → dry-run-ready → awaiting-approval → effect-applied → reconciled → disconnected` | 每次写前快照；terminate/冲突进入停止或 unknown |
| Sub2API 只读运营 | `auth-ready → snapshot-collected → analysis-ready → report-ready` | 核心端点失败停止；原始响应递归脱敏 |
| Prompt 模板 | `draft → schema-valid → reviewed → published` | published 必须显式审批；版本与路由描述一致 |
| 并行协作 | `plan-ready → workers-active → results-collected → synthesized → reviewed` | thread 隔离、结果完整、汇聚引用全部输入 |

这些 phase 只是 Skill 内部的声明式“路标”，不是 Kernel 的公共 State ID。例如 `case.triaged` 不执行医学分流，`triage-problem-gatekeeper` 仍执行分流；如果需要 State helper，也只读取已冻结证据并返回标准结果。适配器将 phase 映射到核心 `lifecycle`，而不是把每个 phase 注册成全局状态。

## 逐 Skill 对接矩阵：Verifier、State 与挂接点

本节回答“哪个 Skill 对接哪些 Verifier、领域 Pack 和 phase”。表中的 Verifier ID 是建议的 canonical ID；除前文列出的 3 个内置 Verifier、2 个系统 State 和 `validate-md-ref` 试点外，其余属于待按优先级实现的 Pack。`S-*` 表示领域 phase/State 投影集合，不是要求一次性注册到 Kernel 的公共状态；`V-*` 只是表格分组记号，不是新的公开 ID。

### 矩阵记号

| 记号 | 对应能力 |
|---|---|
| `V-artifact` | `bensz.artifact.file-existence`、`bensz.artifact.path-scope`、`bensz.artifact.schema-conformance`、`bensz.artifact.encoding-format` |
| `V-build` | `bensz.artifact.render-success`、`bensz.source.build-and-test`、`bensz.artifact.cross-format-consistency` |
| `V-doc` | `bensz.document.link-integrity`、`bensz.document.citation-traceability`、`bensz.document.section-contract`、`bensz.document.length-budget` |
| `V-safe` | `bensz.security.secret-redaction`、`bensz.security.authorization-scope`、`bensz.source.diff-scope` |
| `V-evidence` | `bensz.evidence.provenance`、`bensz.evidence.freshness` |
| `V-runtime` | `bensz.runtime.event-integrity`、`bensz.runtime.state-transition`、`bensz.runtime.task-completeness` |
| `V-coord` | `bensz.coordination.thread-completeness` |
| `V-remote` | `bensz.remote.read-only-scope`、`bensz.remote.idempotency`、`bensz.remote.postcondition` |
| `S-task` | `bensz.workspace.ready → planned → active → waiting/checking/delivering → completed|failed|cancelled → bensz.workspace.closed` |
| `S-build` | `phase: scope-locked → editing → compiled → compared → delivery-ready`，生命周期映射到 `active → checking → delivering` |
| `S-review` | `phase: intake-ready → retrieval-complete → deduplicated → scored → selected → drafted → rendered → reported` |
| `S-case` | `phase: raw-indexed → facts-structured → timeline-ready → triaged → reasoning-ready → evidence-ready → report-ready → reported` |
| `S-remote` | `effect: connected → snapshot-ready → dry-run-ready → awaiting-approval → applied → reconciled → disconnected` |
| `S-prompt` | `phase: draft → schema-valid → reviewed → published` |
| `S-coord` | `phase: plan-ready → workers-active → results-collected → synthesized → reviewed` |

这些 `S-*` 是矩阵中的便捷记号，不是新的公开 State ID。Skill 可以只声明其中的子集；若某个阶段需要公开身份，必须作为 Skill-owned phase/State 按 `owner.machine.state` 规则单独声明，并映射回核心生命周期，而不是把缩写直接注册到 Kernel。

### 本项目核心与治理 Skill

| Skill | 对接 Verifier | 对接 State | 具体挂接与 Gate |
|---|---|---|---|
| `auto-test-code` | `V-artifact`、`V-build`、`V-coord`、`V-runtime` | `S-task`、`S-coord` | 计划/测试报告 Schema 在执行前检查；每轮结果完整后才 verifying；required 测试失败 reject。 |
| `auto-test-project` | `V-artifact`、`V-build`、`V-safe`、`V-runtime` | `S-task` | 项目入口、构建、单测和报告作为 required；缺核心证据不得 reported。 |
| `auto-test-skill` | `V-artifact`、`V-safe`、`V-coord`、`bensz.prompt.contract-conformance` | `S-task`、`S-coord` | 检查 SKILL/config/README/CHANGELOG 一致性；A/B 结果汇聚后再给 Gate。 |
| `awesome-code` | `V-coord`、`bensz.prompt.contract-conformance` | `S-coord` | plan 生成后进入 plan-ready；未声明角色直接写文件则 reject。 |
| `brainstorming` | `bensz.prompt.contract-conformance`、`V-coord` | `S-coord` | 方案/问题澄清记录为 plan evidence；未达成选择不进入 execution-ready。 |
| `parallel-vibe` | `V-coord`、`V-runtime`、`V-safe` | `S-coord` | thread 隔离；`RESULT.md`、`done.json`、退出码齐全后 synthesized。 |
| `multi-agent-coordinator` | `V-coord`、`V-runtime` | `S-coord` | 父子依赖和结果传播可追溯；required 子任务失败阻断父任务。 |
| `code-reviewer` | `V-safe`、`V-coord`、`V-runtime` | `S-coord`、`S-task` | 只读审查 diff；Critical/Important findings 未处理不得 delivery-ready。 |
| `systematic-debugging` | `V-evidence`、`V-build`、`V-runtime` | `S-task` | 根因、假设测试、修复验证分开记录；无根因证据不能通过。 |
| `tdd-workflow` | `V-build`、`V-runtime` | `S-task` | RED/GREEN/回归证据分别登记；缺 RED 进入 warning/manual_review。 |
| `writing-plans` | `V-artifact`、`V-safe` | `S-task`（`planned → checking → completed`） | 只验证计划 Schema、范围和风险，不把计划当实现完成。 |
| `documentation-specialist` | `V-doc`、`V-safe`、`V-runtime` | `S-task` | 文档结构、引用和敏感扫描在交付前执行。 |
| `frontend-specialist` | `V-build`、`V-artifact`、`V-safe` | `S-task` | 构建、截图/视觉证据和改动范围作为交付证据。 |
| `backend-specialist` | `V-build`、`V-artifact`、`V-safe` | `S-task` | API Schema、测试、迁移/配置边界检查；高风险变更等待授权。 |
| `devops-specialist` | `V-build`、`V-safe`、`V-remote` | `S-task`、`S-remote` | 部署动作使用 effect 状态；远程状态未知时禁止重试。 |
| `security-specialist` | `V-safe`、`V-evidence`、`V-runtime` | `S-task`（`waiting + wait_reason=approval`） | 高危 finding 未消除不得 allow。 |
| `context-optimizer` | `bensz.context.evidence-budget`、`V-safe`、`V-runtime` | `S-task` | 压缩只作用于上下文副本；来源、关键约束和敏感边界不可丢失。 |
| `git-workflow` | `bensz.source.diff-scope`、`bensz.runtime.event-integrity` | `S-task` | 只验证分支/diff/提交契约，不触发发布。 |
| `git-commit` | `bensz.source.diff-scope`、`bensz.prompt.contract-conformance` | `S-task` | 提交前检查范围和 Conventional Commit；未授权不进入 effect。 |
| `git-pr-review` | `V-doc`、`V-evidence`、`V-coord`、`V-safe` | `S-coord`、`S-task` | PR 证据只读获取；高风险 findings 进入人工复核。 |
| `git-publish-release` | `V-build`、`V-doc`、`V-safe`、`V-remote` | `S-remote` | Release 资产先 dry-run；发布是显式授权 effect。 |
| `init-project` | `V-artifact`、`V-safe`、`bensz.prompt.contract-conformance` | `S-task` | AGENTS/CLAUDE/BAC 结构检查；覆盖已有文件需确认。 |
| `install-bensz-skills` | `V-artifact`、`V-safe`、`V-runtime` | `S-task`、`S-remote`（bootstrap） | manifest、版本、来源和目标路径校验后回查安装结果。 |
| `bensz-collect-bugs` | `V-artifact`、`V-safe` | `S-task` | 只验证 bug 契约与脱敏；公开上报是单独 remote effect。 |
| `write-skill-readme` | `V-doc`、`bensz.prompt.contract-conformance` | `S-prompt`、`S-task` | README 触发/输入/输出与 SKILL/config 对齐。 |
| `mirror-optimizer` | `V-artifact`、`V-safe`、`V-build` | `S-task`、`S-remote` | 镜像切换需授权并保留回滚信息。 |

### 本项目内容与数据 Skill

| Skill | 对接 Verifier | 对接 State | 具体挂接与 Gate |
|---|---|---|---|
| `auto-draw-plot`（本项目版） | `bensz.image.request-contract`、`V-artifact`、`V-safe` | `S-task` | 配置冲突、模型参数和图片产物先校验；外部调用结果未知时不重复提交。 |
| `any-picture-format` | `V-artifact`、`V-safe` | `S-task` | 输入存在、格式/透明度和输出不覆盖原件。 |
| `download-fulltext-pdf` | `V-artifact`、`V-doc`、`V-evidence`、`V-safe` | `S-task` | DOI/来源、PDF 魔数和完整性检查；来源不可验证 manual_review。 |
| `find-best-skill` | `V-evidence`、`bensz.prompt.contract-conformance` | `S-task` | 搜索结果、评分依据和推荐数量可追溯。 |
| `which-model` | `V-evidence`、`V-doc`、`bensz.prompt.contract-conformance` | `S-review` 子集 | 官方文档/社区证据和场景映射齐全后发布。 |
| `md-to-word` | `V-artifact`、`V-build`、`V-safe` | `S-task` | 不改 Markdown；DOCX 可打开且派生物一致。 |
| `knit-rmd-html` | `V-build`、`V-artifact`、`V-safe` | `S-build` 的 Rmd 子集 | knit 根目录、HTML 产物和错误日志可回放。 |
| `bensz-rmd-rules` | `V-build`、`V-artifact`、`V-evidence`、`bensz.analysis.rmd-interpretation` | `S-build` 的 Rmd 子集 | 图表/表格解读、矢量 PDF/JPG 和 HTML widget 检查为 required。 |
| `prompt-programming` | `bensz.prompt.contract-conformance`、`V-artifact` | `S-prompt` | 六原子结构和压缩后语义保持通过才 reviewed。 |
| `better-prompt` | `bensz.prompt.contract-conformance`、`V-evidence` | `S-prompt` | 输入意图、模型适配和输出约束结构化。 |
| `validate-md-ref` | `bensz.document.markdown-link-integrity`、`bensz.evidence.citation-truth-fit`、`V-runtime` | `bensz.workspace.ready → planned → active → checking → completed → workspace.closed`；领域 phase 另记 | 当前试点：链接规则自动判定；语义引用无引擎时保持 unchecked/manual_review。 |

### ChineseResearchLaTeX Skill

| Skill | 对接 Verifier | 对接 State | 具体挂接与 Gate |
|---|---|---|---|
| `make-latex-model` | `bensz.latex.template-build`、`V-build`、`V-safe` | `S-build` | 先锁定 projects/packages 层；公共包变更没有回归计划直接 reject。 |
| `transfer-old-latex-to-new` | `bensz.latex.migration-scope`、`V-build`、`V-safe` | `S-build` | 迁移清单和受保护文件快照在写入前检查，官方入口构建后才 delivery-ready。 |
| `complete-example` | `bensz.latex.example-contract`、`V-artifact`、`V-build` | `S-build` | 示例结构/资源引用和编译结果检查；不覆盖原示例。 |
| `nsfc-abstract` | `bensz.nsfc.abstract-contract`、`bensz.document.length-budget` | `S-task` 的 draft→reviewed→reported 子集 | 中英文长度、忠实翻译和标题候选字段先规则检查，语义质量不冒充评审结论。 |
| `nsfc-budget` | `bensz.nsfc.budget-reconciliation`、`V-build`、`V-safe` | `S-build` | 金额、预算依据、LaTeX/PDF 交叉一致；缺输入或金额不平衡 reject。 |
| `nsfc-code` | `bensz.nsfc.code-recommendation`、`V-evidence`、`V-artifact` | `S-task` | 代码库版本/候选 JSON/推荐理由可追溯；只读正文不改写。 |
| `nsfc-humanization` | `bensz.nsfc.meaning-preservation`、`V-safe`、`V-doc` | `S-task` | 改写前后主张、数字、术语和引用 diff；语义不确定 manual_review。 |
| `nsfc-justification-writer` | `bensz.nsfc.justification-contract`、`V-doc`、`V-safe`、`V-evidence` | `S-build` | 写入范围、四段论证、引用键、禁用 LaTeX 命令和写后编译共同 Gate。 |
| `nsfc-length-aligner` | `bensz.document.length-budget`、`bensz.nsfc.meaning-preservation` | `S-task` | 先确定性计数，再做最小语义保持改写；超出软预算通常 warning。 |
| `nsfc-qc` | `bensz.nsfc.qc-findings`、`V-doc`、`V-evidence`、`V-coord` | `S-coord`、`S-task` | 只读、多线程 findings 聚合；P0 未解决不得 allow。 |
| `nsfc-ref-alignment` | `bensz.nsfc.reference-alignment`、`V-doc`、`V-evidence` | `S-task` | Bib key/字段/DOI 规则先跑，正文语义支持交给 Prompt/人工。 |
| `nsfc-research-content-writer` | `bensz.nsfc.research-content-contract`、`V-doc`、`V-build` | `S-build` | 研究内容、创新和年度计划结构及术语对齐；只改声明的 extraTex。 |
| `nsfc-research-foundation-writer` | `bensz.nsfc.foundation-contract`、`V-doc`、`V-evidence` | `S-build` | 基础证据→工作条件→风险应对链齐全；不可核验成果 uncertain。 |
| `nsfc-reviewers` | `bensz.nsfc.review-findings`、`V-coord`、`V-evidence` | `S-coord`、`S-task`（`waiting + wait_reason=approval`） | 专家意见按维度聚合；模拟分数不当作官方决定。 |
| `paper-explain-figures` | `bensz.paper.figure-evidence`、`V-artifact`、`V-evidence` | `S-task`、`S-coord` | 每张图独立结果、来源/源码证据和汇总报告齐全后交付。 |
| `paper-know-journal` | `bensz.paper.journal-source-fit`、`V-evidence`、`V-doc` | `S-review` 子集 | 官网/社区来源和访问时间记录；费用/速度不可核验则 uncertain。 |
| `paper-select-journal` | `bensz.paper.journal-selection`、`V-evidence`、`V-artifact` | `S-review` | Set1/Set2/Set3 证据链和候选 JSON 完整后报告。 |
| `paper-write-sci` | `bensz.paper.manuscript-consistency`、`V-doc`、`V-build`、`V-safe` | `S-build` | autonomous 才允许 editing；collaborative 停在 awaiting-approval。 |
| `research-citation-check` | `bensz.research.citation-alignment`、`V-doc`、`V-evidence` | `S-task` | 逐条引用语义检查和 PDF/Word 回归；只在致命错误时改写句子。 |
| `research-guide-updater` | `bensz.research.guide-consistency`、`V-safe`、`V-doc` | `S-task` | 指南路径和术语 diff 受限；未指定指南进入 awaiting-input。 |
| `research-idea` | `bensz.research.idea-novelty`、`V-evidence`、`V-coord` | `S-review`、`S-coord` | 候选问题/假设逐对查新并独立审查；证据不足不得声称未被研究。 |
| `research-literature-review` | `bensz.research.review-pipeline`、`V-doc`、`V-build`、`V-evidence` | `S-review` | 去重集是后续唯一输入；评分、选文/Bib、PDF/Word 和 checkpoint 都是 Gate。 |
| `research-plan` | `bensz.research.analysis-plan`、`V-evidence`、`V-artifact` | `S-review` 子集 | 方法证据、数据假设、步骤和风险登记后才 reported。 |
| `research-topic-extractor` | `bensz.research.topic-extraction`、`V-artifact`、`V-evidence` | `S-review` intake 子集 | 输入类型、主题 JSON Schema 和来源锚点通过后交给下游。 |

### dudu 与 bensz-devtools

| Skill | 对接 Verifier | 对接 State | 具体挂接与 Gate |
|---|---|---|---|
| `dudu-optimize-prompt` | `bensz.prompt.contract-conformance`、`bensz.dudu.prompt-evaluation`、`V-coord` | `S-prompt`、`S-coord` | 只修改声明的 Prompt 面；多轮评测汇聚后 reviewed，业务代码不变。 |
| `dudu-vibe-config` | `bensz.remote.vibe-connection`、`bensz.remote.subscription-scope`、`V-remote`、`V-safe` | `S-remote` | connect/heartbeat、GET 快照、dry-run、确认、单次写入和回查；terminate/5xx 停止。 |
| `bensz-channel-vibe-config` | `bensz.remote.content-publish-safety`、`bensz.remote.vibe-connection`、`V-remote`、`V-safe` | `S-remote` | 草稿验证不允许发布；文章发布/删除是 awaiting-approval 的高风险 effect。 |
| `bensz-notes-vibe-config` | `bensz.remote.notes-sync-safety`、`bensz.remote.vibe-connection`、`V-remote`、`V-safe` | `S-remote` | manifest/revision/hash 先冻结；镜像删除需确认，409 进入 conflicted。 |

### case_analysis

| Skill | 对接 Verifier | 对接 State | 具体挂接与 Gate |
|---|---|---|---|
| `case-intake-manager` | `bensz.clinical.raw-intake-completeness`、`V-artifact`、`V-safe` | `bensz.case.raw-indexed` | raw 全读、索引完整、raw 只读；目录为空进入 awaiting-input。 |
| `case-structuring-extractor` | `bensz.clinical.fact-provenance`、`V-evidence`、`V-artifact` | `bensz.case.facts-structured` | 每个事实带来源锚点并区分缺失/冲突/推断。 |
| `timeline-medication-builder` | `bensz.clinical.timeline-medication-consistency`、`V-evidence` | `bensz.case.timeline-ready` | 日期、治疗顺序、疗效/不良反应挂接；冲突未解释 manual_review。 |
| `triage-problem-gatekeeper` | `bensz.clinical.red-flag-triage`、`bensz.clinical.missing-information` | `bensz.case.triaged`、`S-task`（`waiting + wait_reason=input`） | 红旗置顶、分流和最小检查集合是硬 Gate；不做最终诊断。 |
| `clinical-reasoning-engine` | `bensz.clinical.reasoning-uncertainty`、`V-evidence` | `bensz.case.reasoning-ready` | 支持/反对/待证据点和不确定性齐全；不直接检索或开处方。 |
| `evidence-question-planner` | `bensz.clinical.evidence-question-contract`、`V-evidence` | `bensz.case.evidence-ready` | 只把真正需循证的问题送下游；优先级和理由可追溯。 |
| `evidence-orchestrator` | `bensz.clinical.evidence-freshness`、`bensz.document.link-integrity`、`V-evidence` | `bensz.case.evidence-ready` | 优先复用证据仓库；简单检索不能标成系统综述。 |
| `mdt-panel-and-report-writer` | `bensz.clinical.report-contract`、`V-doc`、`V-evidence`、`V-safe` | `bensz.case.report-ready → bensz.case.reported` | 固定章节、红旗/缺失信息、来源链接和三类清单齐全后交付。 |
| `case-followup-qa` | `bensz.clinical.followup-safety`、`bensz.clinical.red-flag-triage`、`V-evidence` | `bensz.case.reported → bensz.case.followup-active → bensz.case.reported` | 每轮先更新红旗；停药/检查准备必须有真实来源。 |

### sub2api 运营与 sub2api 仓库

| Skill | 对接 Verifier | 对接 State | 具体挂接与 Gate |
|---|---|---|---|
| `sub2api-summary` | `bensz.sub2api.account-data-safety`、`bensz.remote.read-only-scope`、`V-safe`、`V-evidence` | `bensz.sub2api.auth-ready → snapshot-collected → analysis-ready → report-ready` | 认证/连通性/usage 核心接口失败即停止；响应递归脱敏，写操作永不执行。 |
| `sub2api-account-cost` | `bensz.sub2api.account-data-safety`、`bensz.sub2api.capacity-cost-model`、`bensz.sub2api.cost-reconciliation` | 同上 Sub2API 只读序列 | 永久失效与临时不可用分开；情景估算必须标注。 |
| `sub2api-add-users` | `bensz.sub2api.account-data-safety`、`bensz.sub2api.capacity-cost-model`、`bensz.remote.read-only-scope` | 同上 Sub2API 只读序列 | 任一容量池缺口不可由其它池抵消；核心数据缺失 reject。 |
| `sub2api-codex-available` | `bensz.sub2api.codex-route-proof`、`bensz.sub2api.account-data-safety`、`V-remote` | `auth-ready → snapshot-collected → e2e-tested → reconciled → report-ready` | 必须结合 Codex CLI 或明确标注未证明，并以 usage 的目标 `account_id` 命中作为 Gate。 |
| `sub2api-reimbursement` | `bensz.sub2api.invoice-reconciliation`、`bensz.sub2api.account-data-safety`、`V-build`、`V-safe` | `auth-ready → snapshot-collected → invoice-drafted → invoice-rendered → report-ready` | 充值/服务消费分离，净额/税额/含税合计一致；上传是单独 effect。 |
| `sub2api-batch-accounts` | `bensz.sub2api.import-schema`、`bensz.sub2api.proxy-account-binding`、`V-artifact`、`V-safe`、`V-remote`（上传时） | `phase: input-ready → dry-run-ready`；`effect: prepared → waiting + approval → applied → reconciled` | 默认 round-robin、schema/`proxy_key`/分布校验；集中分配、上传和覆盖需确认。 |
| `sub2api-ip-proxy` | `bensz.sub2api.import-schema`、`V-artifact`、`V-safe` | `S-task` | 强制 socks5h、输出不覆盖输入、accounts 为空；dry-run 后才生成 JSON。 |
| `ycy-get-acounts` | `bensz.sub2api.credential-format`、`V-artifact`、`V-safe` | `S-task` | 解析失败行可报告但不泄露凭据；源文件保持不变。 |
| `auto-draw-plot`（sub2api 仓库版） | `bensz.image.request-contract`、`V-artifact`、`V-safe` | `S-task`、`bensz.effect.prepared → applied → reconciled`（调用外部图像 API 时） | 配置来源/Base URL/Key 冲突先 reject；图片和提示词脱敏保存。 |
| `sub2api-prompts` | `bensz.sub2api.prompt-template-contract`、`V-artifact`、`V-safe` | `S-prompt` | 模板 JSON、路由字段、tags 和版本检查；发布需显式确认。 |

### 对接原则的实际含义

- 同一 Skill 只声明真正需要的子集；`md-to-word` 不需要临床或远程 State，`case-structuring-extractor` 不需要发布 effect。
- 同一 Verifier 可以被多个 Skill 复用，但输入 Adapter 必须隔离。`bensz.document.citation-traceability` 可以接 Markdown、LaTeX 和病例报告，却不把三种格式规则写进一个脚本。
- 同一核心生命周期 State 可以跨 Skill 复用，领域 phase 只描述交接点。`waiting + wait_reason=authorization` 不关心用户批准的是发票上传还是文章发布。
- 只有“稳定且重复出现的领域命题”才提升为专用 Pack；一次性文案偏好、项目路径和模型名称留在 Skill 配置或 Adapter。
- 表中 required Gate 是建议默认值，Skill 若要降为 advisory，必须在 runtime 声明中显式写出，不能由模型临时改变。

## 关键执行模式

### 只读短任务

适用于链接检查、格式转换预检、离线 Schema 和文件存在性：

`workspace.ready → planned → active → checking → completed → workspace.closed`（等待、交付和异常通过核心生命周期及正交字段表达）。

只挂接 `path-scope`、`schema`、`secret-redaction`、`artifact-existence` 等低成本规则，不创建多余领域 State。

### 长流水线与可恢复任务

适用于综述、论文、NSFC QC 和病例链：每个阶段结束时写 checkpoint、产物哈希和证据 refs；恢复时先读取旧 checkpoint，再进入对应 State，不以空 state 覆盖历史。阶段失败进入 `awaiting-dependency` 或 `failed`，而不是伪装成下一阶段已完成。

### 远程写任务

适用于 dudu/channel/notes 和 Sub2API 上传：

1. `connected`：只验证 URL、权限和 heartbeat。
2. `snapshot-ready`：GET 现状并冻结 revision/hash。
3. `dry-run-ready`：生成 payload、影响范围和幂等键。
4. `awaiting-approval`：高风险发布、删除、替换必须得到明确确认。
5. `effect-applied`：只发一次受控请求，记录 effect_id。
6. `reconciled`：只读回查目标状态；未知时进入 `effect.unknown`，不重发。
7. `disconnected`：结束连接闭环。

### 语义与确定性混合

以引用、NSFC 论证、病例适用性为例：先用规则确认 key、URL、来源元数据和证据哈希，再让 Prompt/Rubric 判断蕴含、范围和不确定性。规则 `fail` 直接 Gate `reject`；Prompt `uncertain` 只能 `manual_review`，不能被另一个模型投票成 `allow`。

## 接入方式：不重构 Skill

建议使用 Skill 已有的 `config.yaml`，在其中增加可选的 `runtime` 节，仅声明引用关系：

```yaml
runtime:
  protocol: bensz-skill-runtime-v1
  verifier_roots: [references/verifiers]
  state_roots: [references/states]
  initial_state: bensz.workspace.ready
  states:
    - bensz.workspace.ready
    - bensz.task.planned
    - bensz.task.active
    - bensz.task.waiting
    - bensz.task.checking
    - bensz.task.delivering
    - bensz.task.completed
    - bensz.task.failed
    - bensz.task.cancelled
    - bensz.workspace.closed
  phase:
    machine: skill-owned-machine
    roots: [references/phases]
  verifiers:
    - id: bensz.artifact.schema-conformance
      version: 1.0.0
      required: true
      phases: [before_input]
    - id: bensz.security.secret-redaction
      version: 1.0.0
      required: true
      phases: [before_delivery]
  hooks:
    before_write: [bensz.source.diff-scope]
    before_delivery: [bensz.runtime.task-completeness]
```

这里的字段职责与 Verifier 对称：`state_roots` 只规定从哪些目录发现 State 定义，`states` 规定当前 Skill 允许使用的 State 集合，`initial_state` 规定状态机的起点。不能只扫描并自动启用目录中的全部 State，否则无法表达初始状态，也会把未声明的状态错误暴露给当前 Skill。该结构与现有 `state-machine.json` 的 `initial_state`、`state_roots`、`states` 三个字段保持兼容；迁移时只是把声明位置收敛到 `config.yaml.runtime`。

适配器只做四件事：把 Skill 已有输入转换为 Evidence、在既有脚本前后调用 Verifier、把原有阶段映射为 State、把结果写入统一事件。禁止把原 Prompt 搬进 kernel，禁止让 Verifier 直接修改正式产物，禁止为接入而复制一套业务流程。

建议的最小挂点：

- 输入前：路径、授权、敏感边界和 Schema。
- 阶段交接：required 文件、阶段前置、证据是否冻结。
- 写入前：diff scope、危险命令、用户确认和幂等键。
- 写入后：产物存在、构建/回查、跨格式一致性。
- 交付前：Gate、报告结构、未解决不确定性、BAC/事件完整性。

## Kernel 优化与 Skill 迁移工程蓝图

本节将前面的设计转成可执行的工程边界。目标不是一次性重写所有 Skill，而是让 Kernel 先具备稳定的公共协议，再让已有 Skill 通过 Adapter 渐进接入。

### Kernel 交付包与依赖顺序

| 阶段 | Kernel 交付物 | 依赖与停止条件 |
|---|---|---|
| P0 协议冻结 | `Run/Event/Projection/Contract/Evidence/Artifact/VerificationResult/GateDecision/Effect` Schema；核心 State 白名单；Verifier/State ID 与版本规则 | 两份以上计划和现有实现对齐；发现领域特判时停在契约层，不先写代码 |
| P1 事实与投影 | 事件追加、序号/哈希链、幂等、确定性 reducer、快照重建、并发保护、`waiting + wait_reason` | 删除 `state.json` 可由事件重建；事件损坏、重复序号和非法转移有明确错误 |
| P2 原子 Verifier | 核心白名单注册/发现、JSON-stdio、超时/错误归一化、Evidence 引用、required/advisory Gate | 每个原子能力具备正例、反例、缺证据、越界和敏感输入测试 |
| P3 声明与兼容 | `config.yaml.runtime` 的 roots、允许状态/Verifier 子集、initial state、hooks；兼容旧 `state-machine.json` | 新快照只输出 canonical ID；旧目录只读，不覆盖历史报告 |
| P4 组合与副作用 | Prompt/Rule/Human 混合编排、phase DAG、子任务 join、Effect 的授权/幂等/回查/unknown | 规则硬失败不可被语义通过抵消；未知远程结果不得自动重发 |
| P5 迁移与治理 | 试点 Adapter、旁路观察、required Gate 灰度、反馈关联、校准集、版本比较和回滚 | 每个 Skill 通过“拔掉外挂”测试后才扩大迁移范围 |

推荐的代码依赖方向是：

```text
contracts → events/runtime → states
contracts → evidence → verifiers → policy/gate
contracts → adapters → events/runtime
```

`packages/bensz-skill-kernel` 的现有 `runtime.py`、`states.py`、`verifiers.py` 和 `workspace.py` 可作为增量演进入口：先抽取/冻结公共数据结构和测试，再拆分模块职责；不在同一批次中改写所有 Skill 的业务脚本。

### Skill Adapter 的统一职责

每个 Skill 只需实现一层薄 Adapter，完成以下映射：

1. 将既有输入和配置转换为最小 `Subject`、`Requirement` 和 Evidence 引用；
2. 声明 Skill 自有 `phase` DAG、required 产物、Verifier 子集和 hooks；
3. 在原脚本前后追加事件、验证结果、Gate 和产物哈希；
4. 将旧阶段导入为兼容投影，无法证实时返回 `unchecked`/`degraded`；
5. 在写回或远程调用时交给受限 Effect Adapter，保留授权、快照、幂等键、回查和恢复信息。

Adapter 不得复制领域流程、直接覆盖 `state.json`、把完整 raw/凭据交给 Verifier，或让 Verifier 取得正式产物写权限。拔掉 Adapter 后，原 Skill 的用户入口和正式产物语义必须保持可用。

### 迁移波次与验收证据

- **Wave 0：内核离线夹具。** 不接真实网络和模型，覆盖事件重放、核心 State、原子 Verifier、Gate 冲突和敏感扫描。
- **Wave 1：`validate-md-ref`。** 作为短任务样例，保留现有链接采集和状态声明，增加核心生命周期投影、Evidence 引用和 `unchecked/manual_review` 结果。
- **Wave 2：研究/LaTeX 长流程。** 选择一个有 checkpoint、编译和本地写回的 Skill，验证 phase DAG、恢复、diff scope 和渲染产物。
- **Wave 3：Sub2API 只读运营。** 验证认证边界、端点 allowlist、递归脱敏、核心数据缺失停止和报告证据；不接上传或账号补货。
- **Wave 4：高风险领域。** 逐步加入临床、远程发布、NSFC/SCI/Rmd 和 Sub2API effect Pack；先旁路，后确定性 Gate，最后才加入语义人工复核。

每一波都必须留下四类证据：事件可重放、Verifier 结果与证据引用、状态/phase 映射、拔掉外挂后的原入口回归。任一波出现核心特判、无法回放或敏感数据越界，就暂停下一波并回到协议修订。

## 分批落地路线

### 第一批：通用低风险外挂

先冻结并实现 Kernel 原子白名单：`contract.conformance`、`artifact.path-scope`、`artifact.schema-conformance`、`artifact.file-existence`、`source.diff-scope`、`security.secret-redaction`、`evidence.provenance`、`runtime.event-integrity`、`runtime.state-transition` 和 `runtime.task-completeness`。这一批只包含确定性、可重放、无领域依赖的能力；`render-success`、`prompt.contract-conformance` 等先作为组合或领域 Pack，不提前塞入核心。

### 第二批：Kernel 三类代表性试点

- `validate-md-ref`：保留现有状态图，补通用任务状态、证据/链接 Gate 和事件投影一致性。
- `research-literature-review` 或 `make-latex-model`：验证长流水线 checkpoint、渲染和恢复，不改业务脚本。
- `sub2api-summary`：只读端点 allowlist、递归脱敏、核心接口失败停止和覆盖率结果。

这三个试点分别覆盖短任务、长本地产物和真实远程只读数据，能检验外挂可拆卸性。试点顺序固定为“只读映射 → 统一事实写入 → 故障恢复 → 交付验证”，发现协议缺口时优先修改公共契约，不为试点添加核心特判。

### 第三批：高价值专用 Pack

按风险而非 Skill 数量扩展：

1. 临床 `red-flag-triage`、`fact-provenance` 和 `report-contract`；
2. Sub2API `invoice-reconciliation`、`capacity-cost-model`、`codex-route-proof`；
3. dudu/notes/channel 的连接、发布和 revision 冲突；
4. NSFC/SCI/Rmd 的章节、引用、字数、数字和渲染契约。

### 第四批：渐进迁移与版本治理

每个 Skill 先以“旁路观察”运行，只记录 verifier 结果不阻断；稳定后把确定性 required 规则接入 Gate，再逐步加入语义/人工复核。每次契约变化同步 `config.yaml`、`VERIFIER.md`/`STATE.md`、Skill 文档、测试和 `CHANGELOG.md`。ID 不重命名，使用 alias 兼容历史事件。

### 面向 Kernel 优化的工程依赖顺序

以上批次落地时，`packages/bensz-skill-kernel` 应按以下依赖顺序推进，而不是按 Skill 数量平铺开发：

1. **协议冻结：** 固定 `Run/Event/Projection/Contract/Evidence/Artifact/VerificationResult/GateDecision/Effect` 的最小 Schema，固定八个生命周期状态、canonical ID、版本和 alias 解析；输出迁移说明和兼容矩阵。
2. **事实与投影：** 先实现事件追加、序号/哈希校验、确定性 reducer、快照重建、并发保护和 `waiting + wait_reason`；删除 `state.json` 后仍能由事件恢复相同投影。
3. **原子验证：** 实现核心白名单的注册、JSON-stdio 执行、超时/错误归一化、证据引用和 required/advisory Gate；规则失败不能被语义结果覆盖。
4. **声明与 Adapter：** 支持 `config.yaml.runtime` 的 roots、允许状态/Verifier 子集和 hooks；兼容读取旧 `state-machine.json`，但新快照统一输出 canonical ID。
5. **组合与副作用：** 在原子规则稳定后加入 Prompt/规则/人工混合编排、phase DAG、子任务汇聚及 effect 的 `prepared → authorized → applied → reconciled/unknown`；未知结果只允许回查或人工恢复。
6. **Skill 迁移：** 先旁路接入 `validate-md-ref`、研究/LaTeX 长流程和 Sub2API 只读 Skill，再逐步启用 required Gate；每个 Skill 完成“拔掉外挂”测试后才能扩大范围。
7. **治理闭环：** 最后接入反馈关联、校准集、版本灰度、回滚和运行指标；没有回放与回归证据，不提升新的共享 Pack。

每一步都有停止条件：若协议无法由两个以上试点复用，或引入领域分支、敏感数据和不可控远程副作用，应停在当前层级，回退为 Skill 专用 Adapter，而不是继续扩大 Kernel。

## 验收与质量门禁

### Kernel 级

- `bsk verifier list/describe/run` 能发现、解析、超时并归一化 Rule/Prompt/Human Pack。
- `bsk state` 能合并系统/Skill 状态，拒绝未知 ID、alias 冲突、非法转移和越界 helper。
- 删除 `state.json` 后可从事件重建相同投影；重复运行不会制造重复 effect。
- `fail/error/timed_out`、`unchecked/uncertain`、缺失证据和未知远程状态有稳定 Gate 语义。

### Skill 级

- 拔掉外挂后原入口仍工作；挂回后正式产物、输入源和领域结果不改变。
- 每个 required Verifier 有正例、反例、缺证据、超时和敏感数据校准样例。
- 结果引用最小 Evidence，而不是把整个项目、完整 raw 或密钥交给模型。
- 长流程可从 checkpoint 恢复；并行流程不读取其它 thread 的工作区并能汇聚全部结果。
- 远程写流程有授权、幂等、前后快照、回查、冲突和补偿/unknown 分支。

### 报告与审计级

- 报告同时列出 verdict、Gate、未解决项、evidence refs、Verifier/State 版本和验证时间。
- 不把可达性写成真实性、不把估算写成观测、不把 HTTP 成功写成 Codex 命中、不把模型置信度写成医学确诊。
- `.bensz-api` 只存中间输入/输出/日志；正式报告留在项目约定目录；BAC 记录需求、文件变更和验证证据，绝不写入密钥或完整私有 Prompt。

## 当前差距与应避免的反模式

当前 kernel 已有 3 个 Verifier、2 个系统 State、`validate-md-ref` 状态声明和 39 个运行时测试通过；这是可用的最小骨架，但还不是全生态覆盖。主要差距是：

- Verifier 目录与 Python 注册定义仍存在双重契约，缺少自动一致性检查。
- State 是声明式发现和内存转移，尚未为所有长流程提供统一 checkpoint/恢复适配器。
- Gate 已能保守处理结果，但还需要 required/advisory、父子阶段传播和 effect unknown 的显式策略文件。
- 语义 Verifier 仍缺少真实来源摘录、校准集和模型执行记录，不能把 instruction-only 结果升级为自动通过。
- 现有试点仍使用 `state-machine.json`，而新的 Skill 约定将 Verifier/State 选择统一收敛到 `config.yaml.runtime`；不能一次性批量迁移，应先做兼容读取和旁路适配器。

必须避免：

- 为每个 Skill 创建一套重复的 `input/checking/reported` 状态，导致状态爆炸。
- 用 `quality-check`、`skill-name`、`python-checker` 或 `v1` 作为 Verifier ID，把实现或版本耦合进稳定身份。
- 把“完成”作为唯一 verdict，丢失 `unchecked`、`uncertain`、`manual_review` 和 `unknown`。
- 让 Verifier 直接写文件、发布文章、删远程数据或自动修复账号；验证和副作用必须分离。
- 用全局平均分掩盖一个 required 规则的确定性失败。
- 把完整病例 raw、账号导出包、Token、Cookie、邮箱或代理凭据作为“方便”塞入 Evidence。
- 把项目特例写进 kernel；如果只有一个领域需要，应留在专用 Pack 或 Adapter。

## 最终推荐

把这套生态的运行时想象成“可插拔的质量与交接层”：Skill 是主体，State 是路标和不变量，Verifier 是验收工位，Gate 是放行规则，事件账本是可重放凭证。先以通用低风险 Pack 建立覆盖面，再用临床、Sub2API、远程桥梁和 LaTeX/研究 Pack 处理真正的领域风险；所有接入均通过旁路观察、确定性门禁、语义人工复核三步推进。

这样既能让流程更标准、结果更透明、失败更可诊断，又不会把一个可以独立演化的 Skill 变成 Kernel 的领域承托者，符合“薄核心、可组合、即插即用”的设计目标。

## 生态索引与发行边界

下面的清单用于说明盘点不是只抽样几个 Skill。括号中的词是该 Skill 最值得挂接的外挂类型；没有必要为每个名字单独创建新的 State 或 Verifier。

### 本项目 `skills/`

- Alpha/基础工程：`auto-test-code`（测试报告/代码范围）、`auto-test-project`（项目验收）、`auto-test-skill`（Skill 契约）、`awesome-code`（计划与路由）、`parallel-vibe`（thread 完整性）、`code-reviewer`（审查 findings）、`systematic-debugging`（根因证据）、`tdd-workflow`（RED/GREEN 证据）、`writing-plans`（计划 Schema）、`multi-agent-coordinator`（子任务传播）。
- Alpha/工具与治理：`install-bensz-skills`（manifest/版本/目标路径）、`init-project`（AGENTS/BAC）、`git-commit` 与 `git-workflow`（diff/提交边界）、`git-pr-review`（只读 PR 证据）、`git-publish-release`（发布 Gate）、`bensz-collect-bugs`（隐私/上报边界）、`write-skill-readme`（文档结构）、`documentation-specialist`（文档一致性）、`frontend-specialist`（截图/构建）、`backend-specialist`、`devops-specialist`、`security-specialist`、`mirror-optimizer`（各自只需通用构建/安全外挂）。
- Beta/内容与数据：`better-prompt`、`prompt-programming`（Prompt Schema）、`find-best-skill`、`which-model`（证据与推荐完整性）、`any-picture-format`（格式/输入不覆盖）、`download-fulltext-pdf`（下载来源/文件完整性）、`md-to-word`（派生物一致）、`knit-rmd-html`、`bensz-rmd-rules`（Rmd 输出与解读）、`validate-md-ref`（现有状态/链接 Verifier）。
- `awesome-code/agents/` 下的专家 Skill 是角色插件，不应各自拥有独立生命周期；它们复用 `coordination.thread-completeness`、`source.diff-scope` 和 `runtime.task-completeness`。

### ChineseResearchLaTeX

`complete-example`（内容/模板结构）、`make-latex-model`（产品线/公共包回归）、`transfer-old-latex-to-new`（迁移范围/编译）、`nsfc-abstract`（中英文长度/忠实翻译）、`nsfc-budget`（预算公式/渲染）、`nsfc-code`（候选代码 Schema）、`nsfc-humanization`（语义保持）、`nsfc-justification-writer`（NSFC 立项依据专用 Pack）、`nsfc-length-aligner`（篇幅）、`nsfc-qc`（只读 QC findings）、`nsfc-ref-alignment`（Bib/key/DOI）、`nsfc-research-content-writer`（研究内容/年度计划）、`nsfc-research-foundation-writer`（基础-条件-风险对位）、`nsfc-reviewers`（专家评审聚合）、`paper-explain-figures`（图证据/视觉）、`paper-know-journal`（官网来源）、`paper-select-journal`（候选池/相似性）、`paper-write-sci`（章节/数字/协作模式）、`research-citation-check`（逐条引用）、`research-guide-updater`（指南增量）、`research-idea`（问题-假设-查新）、`research-literature-review`（检索流水线）、`research-plan`（分析策略）、`research-topic-extractor`（主题结构化）。

这些 Skill 共享 LaTeX/文献/Rmd 的通用基础，但 `nsfc-*`、`paper-*`、`research-*` 的语义 Pack 应保持分开；渲染与引用可由通用 Verifier 复用。

### dudu 与 bensz-devtools

- dudu：`dudu-optimize-prompt`（Prompt 版本/评测/并行结果）。
- 远程桥梁：`dudu-vibe-config`（Vibe connection、订阅字段、报告队列）、`bensz-channel-vibe-config`（草稿/发布/标签/管理员保护）、`bensz-notes-vibe-config`（revision/hash、同步、软删除）。三者共享 effect State，但 API 路径和副作用规则各自专用。

### case_analysis

`case-intake-manager`（raw 清单/缺口）、`case-structuring-extractor`（事实与来源锚点）、`timeline-medication-builder`（日期/治疗排序）、`triage-problem-gatekeeper`（红旗分流）、`clinical-reasoning-engine`（支持/反对点与不确定性）、`evidence-question-planner`（问题优先级）、`evidence-orchestrator`（证据复用/时效）、`mdt-panel-and-report-writer`（报告装配）、`case-followup-qa`（报告后高风险追问）。这是最适合使用“阶段 State + 事实/证据 Verifier”的严格链路，不应把临床推理塞进通用 kernel。

### sub2api 运营与 sub2api 仓库

- 运营：`sub2api-summary`（全量只读运营快照）、`sub2api-account-cost`（保号成本/死亡率口径）、`sub2api-add-users`（容量缺口）、`sub2api-codex-available`（Codex E2E/usage 命中）、`sub2api-reimbursement`（订单/税率/附件）、`sub2api-batch-accounts`（账号-代理导入/分配）、`sub2api-ip-proxy`（代理格式转换）、`ycy-get-acounts`（账号文本解析）。前五个需要远程只读与脱敏 Pack，批量导入/上传另加 effect Gate。
- sub2api 仓库：`auto-draw-plot`（图片请求配置/产物）、`sub2api-prompts`（Prompt JSON、路由元数据和版本）。同名 `auto-draw-plot` 与本项目版本是两个发行来源，Verifier ID 不应使用 Skill 名称来区分。

## 参考实现与盘点入口

- Kernel Verifier 协议：`packages/bensz-skill-kernel/src/bensz_skill_kernel/verifiers.py`
- Kernel State 协议：`packages/bensz-skill-kernel/src/bensz_skill_kernel/states.py`
- 事件与生命周期：`packages/bensz-skill-kernel/src/bensz_skill_kernel/runtime.py`
- Verifier ID 规范：`docs/verifier-id-naming.md`
- State ID 规范：`docs/state-id-naming.md`
- 当前 Verifier：`packages/bensz-skill-kernel/src/bensz_skill_kernel/verifiers/`
- 当前 State：`packages/bensz-skill-kernel/src/bensz_skill_kernel/states/` 与 `skills/beta/validate-md-ref/states/`
- 现有试点声明：`skills/beta/validate-md-ref/state-machine.json`
- 领域示例：`docs/events/2026-08-27-validate-md-ref状态机与验证器协作调查日记.md`
- 本次只读盘点索引：`.bensz-api/task-20260827-2215-全生态-verifier-state设计/shared/output/skill-inventory.json`
