# 通用 Agent Verifiers 基础设施设计与落地计划

## 通俗解释：究竟发生了什么

- **一句话说明：** Agent 可以说“任务完成了”，但目前缺少一套通用机制逐项证明它真的满足了用户要求。
- **具体场景：** 这更像包裹签收系统，而不只是文章评分器。系统既要检查包裹是否存在、地址是否正确、运输过程是否合规，也要确认收件人是否真的收到；贵重物品还可能需要人工签字。不同任务的检查方法不同，但都可以归结为“要证明什么、检查什么、证据在哪里、证据是否足以放行”。
- **对应到本项目：** 业务 Skill 负责执行任务；Verifier 负责检验某个声明；`bensz-skill-verifiers` 统一声明、证据、执行和门禁协议；`bensz-skill-kernel` 记录验证事实及任务生命周期。
- **改变前后：** 现在 Agent 可能因为命令退出码为零就宣布部署成功；改进后，它还需证明远端服务可访问、配置生效、关键副作用没有重复执行，无法确认时必须进入等待或人工复核。

## 专业判断：设计中心应该是什么

系统要覆盖的不是某一种内容评价，而是几乎所有 Agent 任务中的**可验证声明**。一个任务完成时通常同时作出多类声明：产物存在、格式正确、行为符合预期、过程没有越权、外部状态已生效、内容质量达标。通用基础设施不理解每个领域，却可以统一表达这些声明，找到适用的 Verifier，收集证据，再按照任务策略决定通过、拒绝、等待或人工复核。

参考文章《用 Verifier 提升 AI 标书写作能力：从“生成”走向“可迭代优化”》提供了专门化 Verifier、按需路由、成本分层、早停和持续校准等重要思路。这些原则适用于通用系统，但文章讨论的开放式知识工作只是其中一种场景。版本排序、Meta-Judge、`ProjectSpec` 和专家偏好数据应作为语义质量扩展，不应进入最小核心。

仓库已有的 `bensz-skill-kernel` 解决“发生了什么、任务处于什么状态、能否交付”；`bensz-skill-verifiers` 解决“一个完成声明是否有足够证据”。两者通过事件适配器协作，但 Verifiers 核心必须能够脱离 kernel 独立运行，避免把通用验证能力绑定到单一生命周期实现。

## 要达到什么目标

### 完成后的变化

- 任何 Agent、Skill 或工作流都能把完成条件拆成机器可读的 `Requirement`，把“我已满足它”登记为 `Claim`，并为每项声明找到 Verifier 或明确标记“当前不可验证”。
- 同一协议可以验证文件、文本、代码、命令、结构化数据、执行轨迹、外部服务、副作用、安全约束、语义质量和人工审批。
- 每个结论都能追溯到固定版本的验证对象、Verifier、策略和证据；输入不足、超时、外部状态未知不会被伪装成通过。
- 确定性检查优先，模型判断和人工判断按需使用；高成本检查只在其可能改变决策时运行。
- 验证结果与门禁决策分离：Verifier 只报告事实和判断，Policy/Gate 决定这些结果是否足以继续、交付或等待。
- 核心包不绑定模型供应商、业务领域或 `bensz-skill-kernel`，通过适配器接入 Python、命令、Agent Skill、外部服务和人工审核。

### 不在本次处理范围

- 不承诺让所有现实问题变成确定性验证；无法观察或存在价值判断的任务必须允许 `uncertain` 和人工复核。
- 不建立一个包办所有任务的“超级评审 prompt”，也不把所有 Verifier 常驻注入上下文。
- 不允许 Verifier 借检查之名修改正式产物或执行未经授权的远程写入；修复由原执行者或专门 remediation 流程完成。
- 首版不建设分布式调度、远程队列、训练 reward model 或通用模型网关。

## 核心设计原则

### 验证声明，而不是给整个任务打总分

任务契约先拆成要求，例如“输出文件必须存在”“所有引用必须可访问”；Agent 完成工作后再提交对应声明，例如“输出文件已经生成”“引用已经核验”。每个声明单独产生结论，最终门禁按 required/optional、严重度和授权规则组合；不使用一个平均分掩盖关键失败。

### 证据优先，结论与证据分离

Verifier 必须说明观察到了什么、据此作出什么判断、证据位于哪里。自述“我已经测试过”不是高可信证据；命令输出、文件摘要、只读 API 响应、事件记录和人工签名才是可审计证据。证据需要绑定验证对象摘要和有效时间，避免旧证据误用于新版本。

### 结果与门禁分离

Verifier 返回 `pass`、`fail`、`uncertain`、`not_applicable` 或 `error`；是否阻断由 Policy 决定。同一个可访问性失败，在草稿阶段可以告警，在正式发布阶段可以阻断。`error` 表示检查没有成功执行，绝不能等价为被检查对象失败或通过。

### 默认只读，副作用显式授权

Verifier 默认只能读取和探测。需要编译、运行测试或生成临时文件时，只能在声明的隔离边界内产生可清理副作用；外部写入、删除、发布和补偿不属于验证动作。远端结果未知时先 reconciliation（重新探测真实状态），不能盲目重试。

### 小核心、可插拔能力

核心只管理协议、注册、规划、执行、证据和门禁。具体检查通过 Python callable、命令适配器、Agent Skill、模型 provider、只读外部探针或人工审核插件提供。Registry 初始只暴露轻量能力索引，选中后才加载完整实现和说明。

## 通用验证对象与 Verifier 类型

### 验证对象 `SubjectRef`

统一引用以下对象，而不是假设输入总是一篇文稿：

- `artifact`：文件、目录、图片、PDF、数据集或结构化输出；
- `response`：Agent 给用户的回答、决策或计划；
- `execution`：命令、测试、构建、工具调用及其退出状态；
- `trace`：阶段、事件、授权、来源和执行轨迹；
- `external_state`：远端 API、数据库记录、部署、消息或第三方资源的可观察状态；
- `effect`：写入、发布、删除、扣费等副作用及其后置条件；
- `environment`：依赖、版本、权限、配置和运行平台；
- `candidate_set`：多个候选结果，仅供比较或排序场景使用。

每个引用至少包含 `subject_id`、`kind`、`locator`、`digest/version`、`snapshot_time`、`sensitivity` 和允许的读取方式。易变外部状态必须额外记录观察窗口和新鲜度要求。

### Verifier 能力分类

| 类型 | 主要回答的问题 | 常见实现 |
|---|---|---|
| 结构与静态检查 | 产物是否存在、格式/schema/引用是否正确 | 文件检查、解析器、schema、AST、规则 |
| 行为与可执行检查 | 代码或流程实际运行是否符合预期 | 测试、构建、沙箱命令、仿真 |
| 过程与来源检查 | 必需步骤、授权、来源和审计链是否完整 | 事件/trace 校验、签名、策略规则 |
| 外部状态与副作用检查 | 远端操作是否真的生效、是否重复或处于未知状态 | 只读 API probe、reconciliation、幂等记录 |
| 安全与合规检查 | 是否越权、泄密、越界或违反政策 | 密钥扫描、路径/权限检查、策略引擎 |
| 事实与语义检查 | 内容中的主张是否有依据、是否一致 | 检索、引用核查、模型或专家判断 |
| 质量与偏好检查 | 结果是否清晰、有用，哪个候选更好 | rubric、pairwise、panel、Meta-Judge |
| 人工门禁 | 机器证据不足或风险需要谁确认 | 明确身份、范围和有效期的审批 |

一个 Verifier 应尽量只负责一个能力；需要组合多个能力时由 Verification Plan 编排，而不是在插件内部隐藏不可观察的子流程。

## 公开协议（首版必须先冻结）

### `Requirement`

表示一项完成条件，至少包含：`requirement_id`、自然语言声明、`subject_refs`、`capability`、`required`、`severity`、`evidence_policy`、`gate_policy`、`depends_on` 和 `applicability`。无法映射到能力时必须报告 `unverifiable`，不能静默省略。

### `Claim`

表示执行者声称某项要求已经满足，至少包含：`claim_id`、`requirement_id`、`subject_refs`、可验证谓词或预期后置条件、`asserted_by`、`asserted_at`、`attempt_id` 和执行者提供的初始 evidence refs。Claim 不是事实；它只有在 Verifier 独立观察后才可能获得 `pass`。如果执行者没有显式提交 Claim，runner 可以在交付检查时为 required Requirement 生成“待验证但尚未声明”的缺口，不能替执行者假定成功。

### `VerifierSpec`

Registry 条目至少包含：`verifier_id`、`version`、`capabilities`、可接受的 `subject_kinds`、输入/输出 schema、`execution_mode`、`determinism`、`side_effect_profile`、`network_policy`、`sensitivity_limit`、`cost_class`、`trust_level`、超时/重试语义和适用条件。

### `VerificationRequest`

至少包含：`verification_id`、`requirements[]`、`claims[]`、`subjects[]`、`policy_ref/version`、可用 Verifier 约束、预算、权限、环境快照、证据新鲜度和幂等键。请求可以只验证一个 Claim，也可以编译成带依赖关系的 Verification Plan。

### `Evidence`

至少包含：`evidence_id`、`kind`、`producer`、`subject_digest`、`locator` 或内联摘要、`observed_at`、`valid_until`、`integrity`、`sensitivity` 和 `collection_method`。默认保存最小必要证据；密钥、Cookie、完整私密文档和无关原始响应不得进入日志。

### `VerificationResult`

执行状态与业务结论必须分开：

- `execution_status`：`completed`、`skipped`、`cancelled`、`timed_out`、`error`；
- `verdict`：`pass`、`fail`、`uncertain`、`not_applicable` 或 `unchecked`；
- 关联字段：`requirement_id`、`claim_id`、Verifier id/version、subject/evidence refs、观察事实、finding、严重度、置信或不确定原因、repair hint、耗时/成本、输入与策略摘要。

只有 `execution_status=completed` 时才能给出 `pass`、`fail`、`uncertain` 或 `not_applicable`；其余状态一律为 `unchecked`。`skipped` 说明规划器没有运行检查，`not_applicable` 说明检查成功判断该要求不适用，两者不可混用。`timed_out` 或 `error` 不能聚合为 `pass`。

### `GateDecision`

门禁输出固定为 `allow`、`allow_with_warnings`、`reject`、`wait` 或 `manual_review`，并列出导致决定的 requirement/result、授权级别、未解决的不确定性和恢复条件。它是策略计算结果，不是 Verifier 自己的意见。

### 可选扩展

- `ComparisonResult`：用于候选 pairwise/ranking，不是所有任务必需；
- `RubricResult` 与 `MetaJudgement`：用于开放式语义质量和冲突意见；
- `ReconciliationResult`：用于副作用结果未知后的外部状态探测；
- 领域投影（如 `ProjectSpec`）：减少重复读取，但必须带来源锚点且可重建。

## 一次通用验证如何运行

1. **编译完成契约**：把用户要求、Skill 契约和运行时约束转换为 Requirements；无法验证的要求显式进入缺口清单。
2. **登记完成声明**：执行者把本轮声称满足的 Requirement 登记为 Claim；未声明的 required Requirement 直接形成覆盖缺口。
3. **冻结验证对象**：为本地产物计算摘要，为执行/trace 固定事件范围，为外部状态记录观察窗口，防止验证期间对象被偷换。
4. **规划检查 DAG**：先按 required 和依赖关系选择 mandatory Verifier，再运行规则触发项；adaptive 选择只处理长尾，不得跳过必检项。
5. **收集或复用证据**：优先复用对象摘要、版本、策略和新鲜度均匹配的证据；不匹配时重新检查。
6. **执行检查**：按执行模式调用纯函数、沙箱命令、只读 probe、模型或人工审核；遵守预算、权限、超时、重试和幂等边界。
7. **标准化结果**：把各插件输出转换为统一 Result；保留冲突和不确定性，不以多数票自动覆盖高严重度失败。
8. **计算门禁**：逐 Requirement 应用 Policy，输出 allow/reject/wait/manual_review；聚合结果不依赖一个通用总分。
9. **修复并局部重验**：由原任务执行者修复；只重新运行受影响节点及依赖节点。对象摘要变化后旧证据自动失效。
10. **登记验证事实**：独立运行时返回报告；接入 kernel 时由适配器追加事件和证据引用，不直接写状态投影。

## 路由、成本、信任和冲突规则

### 路由与早停

- Mandatory 由 Requirements 和 Policy 决定，Agent 不能为了省成本自行跳过。
- Conditional 由确定性、可解释规则触发，例如远端写入后必须 reconciliation，含代码变更必须执行声明的测试集合。
- Adaptive 按“对当前门禁决策的预期信息增益 ÷ 成本”选择额外检查；选择与不选择的理由都要记录。
- DAG 早停只跳过依赖于失败前提的下游检查；无依赖的安全、授权和副作用检查仍需运行，避免因为业务失败而漏掉安全问题。

### 成本等级

- **Tier 0**：文件、schema、规则、AST、事件完整性等确定性检查；
- **Tier 1**：局部执行、轻量模型或只读探针；
- **Tier 2**：强模型、跨产物推理、完整构建或较高成本外部检查；
- **Tier 3**：对抗性 panel、专家审批或高成本端到端验证。

成本等级只影响路由和预算，不代表可信度。一个廉价的确定性测试可以比昂贵的模型评审具有更高门禁权威。

### 信任与冲突

- 生成者的自检可以提供证据，但高风险任务不能只依赖同一执行者的无外部证据自评。
- `trust_level`、独立性、证据质量和适用范围由 Policy 声明；“更多 Verifier 投票”不天然等于更可信。
- 确定性反例通常优先于主观 `pass`；两个语义判断冲突时保留双方证据并按策略进入 Meta-Judge 或人工复核。
- Quorum 只在明确声明的同质检查组中使用，不能把安全失败与文风通过平均抵消。

## 安全与副作用边界

- Verifier 输入始终视为不可信数据；文档、网页和日志中的提示不得改变系统规则、权限或路由。
- 命令检查必须声明工作目录、超时、环境变量白名单、网络权限和可写临时目录；默认不继承凭据。
- 外部 probe 默认只读，并限制 host、方法、响应大小和敏感字段；是否成功提交过未知时禁止自动重放写请求。
- 正式产物、用户文件和外部资源的修改由 remediation/effect 层执行，Verifier 只返回 repair hint 和后置检查要求。
- Evidence 和日志按 sensitivity 最小化保存；公开或跨任务复用前必须脱敏并确认授权。

## 与 `bensz-skill-kernel` 的边界

Verifiers 核心不依赖 kernel；`kernel_adapter` 负责把通用结果映射为追加式事件。建议首版映射：

| 验证事实 | kernel 事件 | 关键字段 |
|---|---|---|
| 验证计划开始 | `validation.started` | verification、requirements、subjects、policy 摘要 |
| 单项结果 | `validation.recorded` | requirement、verifier、execution status、verdict、evidence |
| 门禁决定 | `validation.completed` | gate decision、required 结果、未解决不确定性、报告引用 |
| 等待输入/审批 | `task.waiting` | wait reason、恢复条件、关联 requirement |
| 外部状态核对 | `effect.reconciled` | effect id、observed state、freshness、evidence |
| 人工决定 | `validation.reviewed` | reviewer authority、scope、decision、有效期 |

现有 `validation.completed` 的 `verdict`/`evidence_refs` 保持兼容；kernel 只保存和检查通用交付条件，不解释领域 finding。删除投影后，仍应能从事件与证据重建验证事实。

## 首版包和插件边界

建立 `packages/bensz-skill-verifiers/`，发布包 `bensz-skill-verifiers`，导入名 `bensz_skill_verifiers`，Python 3.10+，核心无第三方运行时依赖。最小模块职责：

- `contracts`：Subject、Requirement、Claim、Spec、Request、Evidence、Result、Gate；
- `registry`：能力索引、版本、适用性和按需加载；
- `planner`：Requirement 编译、Verifier 选择、DAG 与预算；
- `executors`：pure、command、probe、provider、human 适配接口；
- `evidence`：摘要、新鲜度、完整性、最小化和缓存；
- `policy`：门禁、信任、冲突、重试和证据要求；
- `runner`：执行、超时、取消、幂等和局部重验；
- `reporting`：结构化报告和人类可读摘要；
- `adapters/kernel`：可选 kernel 事件桥接；
- `cli`：计划预览、运行、报告和离线重放。

首批 reference Verifier 只用于证明协议通用性：文件存在/摘要、JSON/schema、命令退出与输出、事件链完整性、敏感信息扫描、只读 HTTP 状态（fake probe）和人工审批占位器。语义模型先用 fake provider 验证适配协议，不内置领域 prompt。

Verifier 插件可位于 Python 包、可执行脚本或独立 Agent Skill 中。Agent Skill 仍以自身 `SKILL.md` 为边界，Registry 只索引公开 metadata；选中后再加载完整指令。插件不能自行修改全局 Policy 或绕过 runner 写 kernel。

## 代表性任务覆盖矩阵

首版不以标书作为唯一试点，而用四类任务证明抽象没有偏科：

| 任务原型 | 主要验证对象 | 必须覆盖的能力 |
|---|---|---|
| 文件/文档转换 | artifact、execution | 文件存在、格式、结构、摘要、可打开性 |
| 代码修改 | artifact、execution、trace | diff 范围、测试/构建、安全扫描、变更要求 |
| 外部系统操作 | external_state、effect、trace | 授权、幂等、只读 reconciliation、未知状态 |
| 开放式知识输出 | response、candidate_set | 事实证据、rubric、uncertain、pairwise、人工复核 |

只有四类原型都能使用同一 Requirement/Claim/Request/Result/Gate 协议，才能宣称核心具有通用性。标书写作可以作为第四类的后续领域插件试点，但不决定核心数据模型。

## 实施范围与顺序

1. **冻结通用词汇和协议**：定义 Subject、Requirement、Claim、Evidence、Result、Gate、执行状态与 verdict 的差异，并提供四类任务的 JSON 示例。
2. **实现最小本地核心**：完成 contracts、registry、planner、policy、runner 和 Tier 0 reference Verifier；不接模型、网络和 kernel 也能端到端运行。
3. **实现隔离执行与证据层**：加入 command sandbox 契约、fake probe、证据摘要/新鲜度/失效和局部重验；验证检查本身不会越权改动正式对象。
4. **接入 kernel 适配器**：映射开始、单项结果、门禁、等待、reconciliation 和人工审核事件，保持现有验证字段向后兼容。
5. **完成四类原型测试**：先用人工构造的无敏感夹具覆盖确定性、外部状态未知、语义不确定和人工门禁，不为单个场景增加核心特判。
6. **开放插件生态**：稳定 Registry metadata 和 Agent Skill 适配接口后，再建设代码、科研、文档、部署等领域 Verifier；按真实使用数据校准误报、漏报、成本和信任策略。

## 如何确认完成

### 协议通用性

- 四类任务使用相同的 Subject/Requirement/Claim/Evidence/Result/Gate 协议，没有为“文稿”或“代码”增加核心特例。
- 新增一个 Verifier 只需注册能力和适配器，不需要修改 runner、Gate 或 kernel reducer。
- 每项 required Requirement 都有结果或明确的 unverifiable/manual-review 状态，不存在静默漏检。

### 正确性与可重放

- 相同对象摘要、Verifier/policy 版本和环境快照能重放出相同结构；非确定性判断明确记录 provider、参数和不确定性。
- 对象内容变化、证据过期或外部观察窗口失效后，旧证据不会继续放行。
- 超时、取消、检查器崩溃、网络未知和不适用被准确区分，不会折叠成 pass/fail。

### 门禁与安全

- required 确定性失败能够阻断；optional 失败可按 Policy 告警；人工门禁能记录权限范围和有效期。
- 命令、probe、模型和人工适配器不能绕过权限及 sensitivity 限制；提示注入不能改变 Verification Plan。
- 外部写入结果未知时进入 wait/reconciliation，不自动重复副作用。

### 集成与扩展

- 核心包可独立运行；安装 kernel adapter 后能追加兼容事件并从账本重建验证事实。
- capability index 无需加载所有 Verifier 的完整说明；实际运行只加载选中的插件。
- 报告能回答“验证了什么、没有验证什么、用了什么证据、为什么放行、还剩什么风险”。

## 风险与待确认事项

- **“通用”边界：** 系统可以统一表达和编排验证，但不能凭空创造领域真值；无法观察的要求必须暴露为 verification gap。
- **Requirement 编译质量：** 如果遗漏用户真实要求，后续检查再准确也无效；需要把“需求覆盖率”本身作为可检查对象，并允许用户确认关键完成条件。
- **Verifier 可信度：** 自检、模型评审和外部专家的权威不同；首版必须先冻结 trust/evidence 规则，不能只靠投票数。
- **环境可复现性：** 执行检查受平台、依赖和外部状态影响；结果需要环境摘要和新鲜度，不能宣传绝对可复现。
- **kernel 兼容性：** 当前完成守卫只查看最后一条 passing validation，后续若接入多 Requirement Gate，需要向后兼容地扩展，不能让 advisory pass 覆盖 required fail。
- **生态复杂度：** 不在首版创建大量领域 Skill；先证明核心协议对四类任务成立，再按真实需求增加插件。

本计划的核心结论是：`bensz-skill-verifiers` 不应被设计成开放式写作评审器，而应成为 Agent 完成声明的通用“证据与门禁层”。确定性测试、外部状态核对、安全检查、语义评价和人工审批都只是可插拔 Verifier；核心只负责把要求、对象、证据、结果和放行决策可靠地连接起来。
