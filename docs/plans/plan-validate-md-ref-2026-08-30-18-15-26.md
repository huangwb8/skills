# validate-md-ref 多验证器事件编排优化计划

## 通俗解释：究竟发生了什么

- **一句话说明：** 这次检查确实找到了两个验证结果，但系统只把最后一个结果写进“总审核单”，所以审核单看起来不完整，流程被安全门禁挡在报告阶段。
- **生活类比或具体场景：** 可以把一次运行想成寄出一箱需要两张检验单的包裹。两张检验单都已生成（链接完整性检查通过，语义引用检查未自动执行），但装箱员逐张登记时只在最后一张上填写“整箱审核单”。仓库发现审核单没有覆盖第一张检验单，于是拒绝出库。
- **对应到本问题：** 两张检验单对应两个 `verification.result` 事件；整箱审核单对应 `verification.gate` 的 `result_refs`；仓库出库规则对应 `checking` 状态的 `verifier-result-recorded` 不变量。状态机是在防止不完整证据被当成完成，并非误报。
- **改变前后：** 目前 `bsk verification` 逐条写入结果，Gate 只引用最后一个 Verifier，`checking → reported` 稳定失败。修复后，同一 `run_id/attempt_id` 的所有结果一次登记，Gate 引用集合覆盖全部结果；即使 Gate 仍是 `manual_review`，状态也能按契约进入 `reported`。

## 专业判断：问题在哪里

- **当前现象：** `validate-md-ref` 运行产生一个链接完整性 `pass`、一个 instruction-only 语义 Verifier `unchecked`，但事件账本中的 Gate 只包含语义 Verifier 的引用。重试时状态 reducer 正确返回 `gate result_refs do not cover current run results`。
- **影响范围：** 任何通过 Kernel CLI `verification` 命令一次提交多个 Verifier 结果的 Skill，都可能出现“结果已记录、Gate 不完整、生命周期无法收尾”的阻塞；审计和下游状态监控也会看到不一致的结果数与 Gate 覆盖范围。
- **已知原因：** `packages/bensz-skill-kernel/src/bensz_skill_kernel/cli.py` 的 `verification` 分支循环调用单结果 `record_verification`，仅在最后一项传入 Gate。公开的 `record_verification_batch` 已能正确生成全量 `result_refs`，因此不应放宽状态不变量来掩盖编排错误。`skills/beta/validate-md-ref/scripts/validate_links.py::record_runtime_events` 正是该 CLI 的调用封装。
- **次要观察（需先确认契约）：** 外部 HTTPS 链接被统一解释为“本地、回环或内部域名”；`valid_rate` 缺少可观测分母；instruction-only Verifier 的 assurance/metrics 可能被当作自动验证。它们影响可解释性和指标使用，但不是本次状态阻塞的根因。

## 要达到什么目标

- **完成后的变化：**
  - 多 Verifier CLI 调用产生全部 `verification.result` 事件和一个绑定完整结果集合的 Kernel Gate。
  - Gate 的 `result_refs` 严格限定在当前 `run_id/attempt_id`，保持身份隔离、幂等和现有安全门禁。
  - `validate-md-ref` 能在两个结果（`pass` + `unchecked`）场景下完成 `checking → reported`，并继续把 `manual_review` 明确为人工复核而非语义通过。
  - 若契约确认纳入第二阶段，摘要和 metrics 能区分“未观测/策略跳过/人工保障”，避免读者误解覆盖率。
- **不在本次处理范围：** 不放宽 `verifier-result-recorded`、不把 `unchecked` 改成 `pass`、不绕过 SSRF/DNS 私网阻断、不修改用户 Markdown、不重写现有批量 API 的核心语义，也不顺带重构无关 Kernel 模块。

## 改进方向

### 统一 CLI 的批量持久化路径（首要修复）

把 `cli.py` 的 `verification` 列表输入改为一次调用 `EventLog.record_verification_batch`，将结果列表、Gate 候选、`run_id`、`attempt_id`、scope/actor 和幂等键作为同一批次处理。保留单对象输入的兼容行为（内部仍可归一化为单元素批次），并让输出继续返回每条结果事件及一个 Gate 事件，避免调用方协议突然变化。Kernel 继续重算 Gate，不信任调用方的 decision/reason。

这相当于一次把整箱检验单交给仓库登记，仓库可以看到完整清单，而不是依赖最后一张单据推测整箱内容。

受影响组件：

- `packages/bensz-skill-kernel/src/bensz_skill_kernel/cli.py`：verification 命令分支及其事件输出组装。
- `packages/bensz-skill-kernel/src/bensz_skill_kernel/runtime.py`：仅核对并保持 `record_verification_batch` 的幂等、证据去重和最后结果事件绑定语义；除非测试证明存在问题，不扩大修改。
- `skills/beta/validate-md-ref/scripts/validate_links.py`：确认 `record_runtime_events` 传入批量结果后无需二次拼接；若需要调整，仅做兼容封装和错误回执改进。

### 补齐多结果回归与运行隔离验证

新增/更新 Kernel CLI 测试，覆盖两个合法 canonical Verifier（一个 `pass`、一个 `unchecked`）及 `manual_review` Gate：断言账本有两条结果和一个 Gate，Gate 引用集合包含两个 `verifier_id@version`，`result_event_id` 指向批次最后一条结果，且带齐 `run_id/attempt_id` 时状态不变量允许转移。另测空列表、非法身份/版本、缺失运行身份、历史运行结果混入、重复幂等调用和单结果旧调用。

在 `validate-md-ref` 侧增加最小集成回归（可调用 source-tree Kernel），确认真实封装路径与 CLI 行为一致，并验证失败时 `recorded: false` 与 stderr 不泄露原始 Markdown。

### 分阶段改善可解释性与指标（次要、需契约确认）

先核对 Verifier Pack/Kernel 对 `assurance_tier`、`verifier_count` 和 `valid_rate` 的正式定义，再决定是否纳入同一版本：

- instruction-only 结果标记为 human/manual assurance，或在输出中显式声明没有自动执行器；required Verifier 数与实际结果数分开统计。
- 将外链跳过原因拆分为策略拒绝、主机名本地判定、DNS 解析到私有/保留地址等，并增加 observable/分类分母说明。
- 对上述字段补充向后兼容的可选字段或文档，不改变既有 SSRF 阻断和 `manual_review` 语义。

若契约尚未确定，则本阶段只形成议题和测试样例，不修改公开字段，避免指标语义漂移。

## 实施范围与顺序

1. 先在 Kernel CLI 接入 `record_verification_batch`，保持现有参数、事件类型和单结果兼容；同步针对多 Verifier Gate 覆盖的单元/CLI 回归测试。
2. 用 source-tree Kernel 重放本次最小复现，并从 `validate-md-ref` 封装入口运行集成测试；确认 `checking → reported` 成功且 Gate 仍为 `manual_review`。
3. 核对并更新受影响的 Kernel/Skill 文档、版本和变更记录（由实施者按仓库治理要求完成；本计划阶段不修改这些文件）。
4. 在 assurance、metrics 和外链跳过原因的契约得到确认后，再实施可选的解释性字段与对应测试；若未确认，保留现状并记录不纳入理由。

## 如何确认完成

- CLI 多结果调用的事件账本恰好包含 N 条 `verification.result` 和一个 Gate；Gate `result_refs` 与当前运行的 N 个 canonical Verifier 集合完全相等，不引用历史运行。
- `manual_review`、`unchecked`、instruction-only 的语义保持不变；没有通过降低状态门禁强度来“修复”流程。
- 为同一 `run_id/attempt_id` 重复提交不会产生不一致或重复 Gate；缺失身份、非法 JSON、非法 Verifier ID/version 仍以稳定错误拒绝。
- `validate-md-ref` 端到端运行能写入完整事件并从 `checking` 转移到 `reported`；输出中的结果、Gate、metrics 与账本一致。
- 建议执行的验证：
  - `python -m pytest packages/bensz-skill-kernel/tests/runtime/test_cli.py packages/bensz-skill-kernel/tests/runtime/test_kernel.py`
  - `python -m pytest packages/bensz-skill-kernel/tests`（环境具备 pytest 时）
  - 使用 `validate_links.py --events <临时账本> --run-id <测试ID>` 重放双 Verifier 场景，并检查 `events.ndjson` 和状态转移回执。
  - 安装后再次运行 CLI/package-data 发现检查，确保修改未破坏系统级入口。

## 风险与待确认事项

- **兼容性风险：** CLI 当前输出按每条结果返回事件对象；批量实现必须保留该形状或提供明确兼容映射，不能让现有 Skill 解析器失效。
- **幂等风险：** 批次幂等键需与现有 `:<index>` 结果键及 `:gate` 键保持稳定，避免重试时只写入部分结果。
- **身份隔离风险：** Gate 覆盖检查必须继续按 `run_id/attempt_id` 过滤，不能复用上一轮运行的结果来满足当前 Gate。
- **协议不确定性：** assurance/metrics 字段的正式语义尚需确认；在确认前不应擅自改变计数含义或新增强制字段。
- **网络安全边界：** 外链解释性改进只能细化阻断原因，不能放宽 DNS、重定向、私网和回环地址检查。
- **环境前提：** 当前评估环境缺少 pytest；实施前需准备可运行的测试环境，否则只能保留 CLI 最小复现和人工账本检查证据。

