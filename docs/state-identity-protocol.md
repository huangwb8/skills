# BSK State visit / attempt 身份协议

## 决策

BSK 将一次业务运行、一次 State 访问和访问内的一次验证尝试分为三层不透明身份：

- `run_id`：整次业务运行，在同一条 State 流程中保持稳定。
- `state_visit_id`：一次进入 State 的访问；每次 transition 都创建新值，即使回到同一 State 也不能复用。
- `attempt_id`：当前访问内的一次证据/验证尝试；可被新 attempt 显式替代，但同一 visit 内不能复用旧值。

新身份使用 `bensz-state-identity-v2`，新事件信封使用 `bensz-event-v2`，State 响应与快照使用 `bensz-meta-state-v2`。旧 `bensz-event-v1` 和 `bensz-meta-state-v1` 保持只读可重放；缺少 `state_visit_id` 的旧记录会标记 `legacy_identity=true`，不会被推断为具备 v2 完成资格。

Skill 可在 `config.yaml.runtime.identity_policy` 声明 `state-identity-v2`。声明后实际模式为 `strict-v2`：新写入必须显式提供非空 `run_id` 和非 `default` 的目标 attempt，且不能请求 legacy 降级。未声明策略的旧 Skill 暂时保留兼容写入，但响应明确返回 `identity_mode=legacy`、`downgrade_policy=warn` 和 `legacy_state_write` 警告。

## 状态图

```text
run-1
  ├─ visit-A / attempt-A1 ── attempt.start ──> visit-A / attempt-A2
  │                                              │
  │                         source_identity ─────┘
  │                                              │ transition
  └──────────────────────────────────────────────v
                                             visit-B / attempt-B1
```

transition 的源侧按当前 active identity 检查 invariant；目标侧在同一事件与快照提交中创建新的 visit 和 initial attempt。事件信封绑定目标身份，`payload.source_identity` 与 `payload.target_identity` 明确表达两侧，消费方不得再把信封的一组 attempt 同时解释为源和目标。

## 事件与投影

`state.transition` 的 v2 payload 至少包含：

```json
{
  "state_domain": "skill",
  "identity_protocol": "bensz-state-identity-v2",
  "source_identity": {
    "run_id": "run-1",
    "state_visit_id": "visit-a",
    "attempt_id": "attempt-a2"
  },
  "target_identity": {
    "run_id": "run-1",
    "state_visit_id": "visit-b",
    "attempt_id": "attempt-b1"
  }
}
```

受 Gate 保护的 strict-v2 前向迁移还包含：

```json
{
  "gate_event_id": "gate-event-id",
  "evidence_hash": "sha256:<64-hex>",
  "evidence_refs": ["completion-index"]
}
```

Gate 属于 source identity，而 transition 事件信封属于 target identity。Kernel 必须以
`payload.source_identity` 对账 Gate 的 `run_id/state_visit_id/attempt_id`，并要求 Gate decision、
证据哈希和引用完全一致；不得把 transition 信封身份误当成 Gate 身份。

首次从 legacy/工作区初始状态进入 v2 State 时，`source_identity` 可以为 `null`。从 v2 State 离开时必须与当前投影完全一致，`run_id` 不得在 transition 中改变。

`state.attempt.started` 只允许在当前 visit 内追加，记录 `supersedes_attempt_id` 和原因。reducer 随即更新 `active_attempt_id`，并使旧 attempt 的未消费 action authorization 过期。Verifier、Gate、handoff 和 action authorization 都按 `run_id + state_visit_id + attempt_id` 过滤；旧窗口证据仍保留审计价值，但不能满足当前 invariant。

## CLI

先查询能力，不需要创建临时业务工作区：

```bash
bsk capabilities
bsk diagnostics
```

进入目标 State 时分别提供源身份与目标 attempt；目标 visit 可显式提供，也可由 Kernel 确定性生成：

```bash
bsk state transition TASK_ROOT SKILL TARGET_STATE \
  --skill-root SKILL_ROOT \
  --run-id run-1 \
  --state-visit-id visit-a \
  --attempt-id attempt-a2 \
  --target-state-visit-id visit-b \
  --target-attempt-id attempt-b1 \
  --gate-event-id GATE_EVENT_ID \
  --evidence-hash sha256:... \
  --evidence-ref completion-index \
  --idempotency-key transition-a-b
```

strict-v2 State 只要声明了 Kernel 已定义的 Gate invariant，离开时就必须同时提供
`--gate-event-id`、`--evidence-hash` 和至少一个 `--evidence-ref`；重复引用参数可表达多条引用。
首次进入 v2 State 时省略源 `--state-visit-id`，但仍提供 `--run-id` 与 `--target-attempt-id`；
该原子初始化没有 source identity，因此不要求 Gate binding。是否受保护由 State 声明决定，
不按领域名称或边名称硬编码。

新任务可通过一个命令原子建立 workspace、运行契约快照与首个 v2 State：

```bash
bsk workspace initialize PROJECT_ROOT SKILL TARGET_STATE \
  --skill-root SKILL_ROOT --run-id run-1 --attempt-id attempt-a1
```

该入口拒绝复用既有任务根：显式路径以排他目录创建，自动命名冲突时原子选择短后缀；初始化异常时仅在 ownership token 仍匹配时回滚本次新建的任务根。运行快照包含 Skill/Kernel 版本、identity policy、State 契约、Verifier Markdown 契约/组件计划/helper 资产哈希和最小 Python 指纹，并以 `run_snapshot_id`/`run_snapshot_hash` 绑定 State 事件、投影和 action authorization。快照只允许相同内容的幂等写入，读取时重算 payload hash 和派生 ID；运行中的声明或契约发生漂移时返回 `runtime_contract_drift`，不得继续复用旧 Gate 或授权，而应创建新的 workspace/task root。

同一 State 内重试：

```bash
bsk attempt start TASK_ROOT SKILL \
  --run-id run-1 \
  --state-visit-id visit-b \
  --attempt-id attempt-b2 \
  --reason retry \
  --idempotency-key attempt-b2
```

Verifier 与 action 命令在 v2 State 中必须携带同一个 `--state-visit-id`。transition 拒绝响应提供稳定 `reason_code`；attempt API 的结构化错误前缀包括 `concurrent_event_conflict`、`state_identity_unavailable`、`state_binding_mismatch`、`state_visit_identity_mismatch`、`attempt_already_active` 和 `attempt_identity_reused`。Gate binding 写入前的稳定失败码包括 `gate_event_not_found`、`gate_identity_mismatch`、`gate_not_allowing`、`gate_evidence_hash_mismatch` 与 `gate_evidence_refs_mismatch`；同一幂等键改变 binding 时返回 idempotency conflict。

## 原子性、恢复与边界

CLI 在暂存快照前先只读验证 Gate binding，再在事件锁内复核并追加哈希链事件，最后原子替换正式快照。事件追加前会用 reducer 校验 source/target identity；追加或提交中断会留下可检测的临时快照，后续操作 fail-closed。`status`/`rebuild` 只重放事件，不生成新 visit、attempt、Gate 或授权。`query_transition_bindings()` 与 `inspect_transition_binding()` 将无绑定历史迁移显式报告为 `legacy_unbound`，将无 source identity 的初始化报告为 `not_applicable`，不会把可读取的历史事件提升为严格认证。

Kernel 不理解领域阶段含义，不扫描业务产物，也不自动升级 Python、安装副本或 Skill。环境预检可使用 `bsk capabilities` 判断协议与 identity mode 契约，使用 `bsk diagnostics` 获取实际解释器、Python 和 Kernel 版本；报告 schema、控制完成度与科学证据资格仍由调用方分别诊断。
