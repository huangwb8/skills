# bensz-skill-kernel

轻量的 Agent Skill 状态、工作区与 Verifier 生命周期内核。

当前发布版本：`2.1.4`

[English](README_EN.md)

## 适合谁

- **Skill 使用者**：用 `bsk` 发现状态、Verifier 和工作区边界。
- **Skill/Pack 作者**：声明 `config.yaml.runtime`、State/Verifier Contract Pack 与 JSON-stdio 组件。
- **内核开发者**：维护可重放事件账本、Gate、证据和安全边界。

## 快速开始

需要 Python 3.11+。在仓库根目录执行：

```bash
# 建议在隔离环境安装当前包
python3 -m venv .bensz-api/.venv
.bensz-api/.venv/bin/python -m pip install -e packages/bensz-skill-kernel

# 确认 CLI 与内置 Pack 已可发现
.bensz-api/.venv/bin/bsk --version
.bensz-api/.venv/bin/bsk verifier list
```

预期：第一条命令输出当前包版本，第二条列出内置 Verifier。只想安装已发布版本时，可改用 `python3 -m pip install bensz-skill-kernel`；版本与依赖以 `pyproject.toml` 为准。

## 声明式 State/Verifier 子 Agent 协作

Kernel 只负责 State、Verifier、证据和 Gate；它不实现跨 Harness 的 Agent 创建、并行、等待或回收。需要协作的 Skill 应引用[条件性协作模板](../../docs/templates/state-verifier-agent-coordination.md)，在 `SKILL.md` 中说明触发阶段、子 Agent 输入、独立性、输出格式和 fallback。

- `config.yaml` 可以声明 `mode`、`count`、`rounds` 等协作意图，供 LLM 与 Harness 理解和报告；这些字段不是 Kernel 调度 API。
- 默认的 Verifier 协作建议是两个独立子 Agent 并行检查同一快照；串行复核只在 Skill 明确需要时声明。
- Codex、Claude Code 或其他 Harness 自主决定如何创建和隔离子 Agent；Skill 不得假设平台 API、host ID 或沙箱参数。
- 子 Agent 结果仍须回到既有 Verifier/Gate 契约，缺失、不确定或失败不得被伪装为通过。

## Python 支持与依赖

- 最低支持 Python 3.11；已验证 3.11、3.12、3.13，推荐 3.12。
- 运行时仅依赖 PyYAML（读取 Skill 的 `config.yaml`）和 Python 标准库。
- 新 Python 版本通过测试矩阵后才进入支持范围。

新建或修改的 Skill 只声明依赖 BSK；实际版本由 Bensz 托管运行时在执行前更新到最新生产版，不由各 Skill 分别选择最低版本、精确版本或 capability 门禁：

```yaml
runtime:
  kernel:
    name: bensz-skill-kernel
```

Kernel 仍可读取历史 Skill 的 `runtime.kernel.version` 与 `required_capabilities`，但这只是迁移兼容，不是新声明模板。生产 CLI 统一使用 `~/.bensz-skills/bin/bsk`；最新版本的检查和更新由 `install-bensz-skills --force-runtime-update` 完成。

## 目录化 Contract Pack

State 与 Verifier 都采用“Markdown 契约 + 索引元数据 + 零个或多个组件”的目录化 Pack。`contract_packs.py` 在 `packs.py` 的发现与 JSON-stdio 边界上编排 `script`、`agent`、`human` 组件，并绑定契约/计划/组件哈希、证据、依赖顺序、`run_id`/`state_visit_id`/`attempt_id` 和执行者。共享执行层不混淆 State 的迁移语义与 Verifier 的 verdict/Gate 语义。

canonical ID、版本和 alias 迁移规则见 [`docs/verifier-id-naming.md`](../../docs/verifier-id-naming.md) 与 [`docs/state-id-naming.md`](../../docs/state-id-naming.md)。

## State：阶段与迁移

`states/index.json` 是 State 目录清单；每个状态目录包含 `STATE.md`，可选 JSON-stdio helper。内置生命周期状态为 `planned`、`active`、`waiting`、`checking`、`delivering`、`completed`、`failed`、`cancelled`；`workspace-ready` 与 `workspace-closed` 是工作区系统状态。领域 Skill 阶段仍放在自身 `references/states/`。

State Pack 的模块化边界是单个状态目录本身：`states/<state>/` 或 Skill 自有 `references/states/<state>/` 承载该状态的语义契约、脚本 helper、Agent/人工组件和证据要求。内置 `states/` 目录故意保持扁平；`runtime`、`workspace`、领域状态等差异通过 canonical ID、`kind`、`classification` 和 `tags` 表达，而不是通过额外子目录表达。

BSK 只托管跨状态复用的基础设施：Pack 发现、ID/alias 校验、契约加载与哈希、组件执行边界、通用转移合法性、事件与快照、资源限制、错误归一化和敏感信息脱敏。新增普通 State 应优先通过新增状态目录、更新 `index.json` 或目标 Skill 的 `config.yaml.runtime` 声明完成；只有确属跨多个 State/Skill 复用的基础能力，才进入 Kernel 系统代码。`runtime.py` 的生命周期 reducer 是稳定投影例外，修改其状态或转移时必须与内置 State Pack 契约保持一致。

```bash
bsk state list
bsk state describe bensz.workspace.ready
bsk state list --root path/to/skill/states
```

`--root` 会叠加 Skill 状态，不替换内置状态。Skill 在根目录 `config.yaml.runtime` 声明初始状态、可用状态、状态根和 Verifier 子集；旧 `state-machine.json` 只读兼容。required 组件必须全部完成并通过，状态条件才成立。

需要强身份的新 Skill 在同一 runtime 声明中加入 `identity_policy: state-identity-v2`。该策略只收紧新写入：首次 transition 缺少 `run_id`、显式 initial attempt，或使用 legacy `default` attempt 时，会在首条事件前以稳定 `reason_code` 拒绝；旧 v1 日志仍可读取和重放，但不能在 strict Skill 中原地升级。

先初始化任务工作区和 Skill 状态声明，再检查/持久化迁移：

```bash
bsk workspace init . --description citation-review
bsk state check bensz.workspace.ready org.example.skill.collecting --skill-root path/to/skill
bsk state transition .bensz-api/task-YYYYMMDD-HHMM-citation-review skill-name org.example.skill.collecting \
  --skill-root path/to/skill --run-id run-1 --target-attempt-id collecting-1 \
  --context-json '{"input":"report.md"}'
```

新身份协议把 `run_id`（整次运行）、`state_visit_id`（一次进入 State）和 `attempt_id`（该访问内的一次验证尝试）分层。transition 用 `source_identity` 验收当前 State，同时原子创建 `target_identity`；CLI 返回目标身份供下一阶段直接使用。同一 State 内重试使用 `bsk attempt start`，新 attempt 启用后旧 Gate、handoff 与 authorization 均不能满足当前窗口。完整协议、状态图、稳定错误码和 legacy 规则见[身份协议说明](../../docs/state-identity-protocol.md)。

```bash
bsk capabilities
bsk diagnostics
bsk attempt start .bensz-api/task-YYYYMMDD-HHMM-citation-review skill-name \
  --run-id run-1 --state-visit-id STATE_VISIT_ID --attempt-id collecting-2 \
  --reason retry --idempotency-key collecting-2
```

新状态操作返回 `bensz-meta-state-v2` JSON；旧 `bensz-meta-state-v1`/`bensz-event-v1` 日志保持只读可重放并标为 legacy，不会被推断为具备 v2 完成资格。Skill 元状态写入自身 `log/meta-state.json`；任务 `events.ndjson`/`state.json` 仍是独立的生命周期与证据层。成功迁移追加 `state.transition`（`state_domain: skill`）事件，`bsk rebuild` 投影 State、visit、active attempt 并核验稳定字段哈希。

Kernel 只执行有明确协议的 invariant。当前 `verifier-result-recorded` 要求离开该状态前同时存在 `verification.result` 与 `verification.gate`；v2 事件必须属于当前 `run_id/state_visit_id/attempt_id`，并发生在当前 attempt 窗口开始之后，较早阶段或已替代 attempt 的通过结果不能复用。不满足时返回 `rejected`，不写入新快照。领域 invariant 仍由 Skill helper 或人工复核负责。

## Action：阶段内动作授权

State transition 只能约束主动提交的迁移，不能自动拦截宿主绕过 Kernel 的文件写入或业务调用。需要保护阶段内动作时，Skill host 应在动作前调用通用 preflight，取得与当前 State 快照、State 版本、`run_id/attempt_id`、handoff 和证据窗口绑定的单次 capability，并在实际动作前原子消费：

```bash
bsk action preflight .bensz-api/task-YYYYMMDD-HHMM-demo/log/events.ndjson \
  demo-skill publish-report --state org.example.workflow.ready --state-version 1.0.0 \
  --run-id run-1 --state-visit-id visit-1 --attempt-id attempt-1 --idempotency-key authorize-publish

bsk action consume .bensz-api/task-YYYYMMDD-HHMM-demo/log/events.ndjson \
  action-auth-... demo-skill publish-report --run-id run-1 --state-visit-id visit-1 --attempt-id attempt-1 \
  --idempotency-key consume-publish
```

Python 调用方使用 `EventLog.preflight_action()` 和 `EventLog.consume_action_authorization()`。v2 preflight 只接受当前 State 快照绑定的 active run/visit/attempt；可选 `handoff_id` 必须来自当前 attempt 窗口。State 再次进入或 attempt 被替代后旧授权自动过期，授权只能消费一次；`expected_last_seq` 可用于拒绝并发观察漂移。拒绝同样追加 `action.authorization.denied`，包含稳定原因码和恢复建议。`status/rebuild` 只投影已有授权事件，不会补写授权或业务动作。

协议标识为 `bensz-action-authorization-v1`（公开常量 `ACTION_AUTHORIZATION_PROTOCOL`）。preflight 拒绝码覆盖 `concurrent_event_conflict`、`skill_state_unavailable`、`state_mismatch`、`state_version_mismatch`、`state_snapshot_unbound`、`state_identity_mismatch`、`handoff_outside_state_window`、`handoff_outside_attempt_window` 和 `evidence_outside_handoff`；消费拒绝码覆盖 `authorization_not_found`、`authorization_already_consumed`、`authorization_expired`、`authorization_binding_mismatch` 及并发冲突。调用方应依据原因码执行 `recovery`，不要解析自然语言消息。

动作名称及“哪些动作必须保护”仍由 Skill/host 契约定义，Kernel 不认识领域字段，也不扫描项目文件。完全不调用 preflight 的宿主无法被 Kernel 自身阻止；该 capability 是可审计的协议门禁，不是操作系统权限沙箱。幂等键绑定首次结果；修复拒绝原因后应使用新的动作尝试/幂等键。

## Verifier：证据与 Gate

`verifiers/index.json` 是 Verifier 包目录和执行计划的单一来源；每个 Pack 有 `VERIFIER.md` 和可选组件。脚本组件 stdin 接收一个 JSON 请求、stdout 输出一个结果 JSON；`verdict` 支持 `pass`、`fail`、`uncertain`、`unchecked`、`error`、`timed_out`、`skipped`。Kernel 负责超时、异常、非法 JSON 和结果字段归一化。

Verifier Pack 与 State Pack 使用相同的模块化边界：内置 `verifiers/<verifier>/` 或 Skill 自有 `references/verifiers/<verifier>/` 承载契约、脚本和专属证据解释。BSK 从索引发现 Pack，不在中央 Registry 重复维护 ID 或目录清单；新增普通 Verifier 不需要修改 Kernel 分发逻辑。

新建或修改 `VERIFIER.md` 时，正文按 [`docs/templates/verifier-body.md`](../../docs/templates/verifier-body.md) 的轻量骨架依次说明判断目标、输入与证据、执行、输出与判定、失败与边界。带索引的 Pack 不在正文重复机器元数据；包内测试会校验所有内置契约的章节顺序和非空内容。

```bash
bsk verifier list --tag citation
bsk verifier describe bensz.evidence.citation-truth-fit --version 1.0.0
bsk verifier run bensz.document.markdown-link-integrity --input README.md
bsk verifier list --skill-root path/to/skill
bsk verifier run org.example.contract.check --skill-root path/to/skill \
  --request-json '{"subject":{"data":{"id":1}},"context":{"schema":{"required":["id"]}}}'
```

`--root` 显式叠加一个或多个 Verifier 集合；`--skill-root` 从 `config.yaml.runtime.verifier_roots`（默认 `references/verifiers`）加载 Pack，并只暴露 `runtime.verifiers` 已声明的 ID/版本。两者互斥且都不会扫描全局目录。`run` 保留 `--input` 文件兼容入口，也支持完整的 `--request-json` 或 `--request-file`；非文件型 Verifier 应使用完整请求，避免遗漏其 subject/context/evidence 契约。JSON 请求中的 `run_id`/`attempt_id` 会被保留，显式 CLI 参数优先。

内置示例包括文件存在、Markdown 链接完整性、引用真实性/适切性，以及 `bensz.design.minimum-sufficient-complexity`（审查复杂度是否有当前目标、约束或风险依据）；旧 ID alias 仍可解析。引用和设计复杂度 Verifier 显式声明为 `agent` 组件，未收到绑定结果时保持 `unchecked`/`wait`。旧单入口 Pack、无 `index.json` 的兼容目录和 instruction-only 状态仍可发现，但会给出缺少显式组件元数据的诊断。原子 Pack 还覆盖合同一致性、路径范围、Schema、diff、敏感信息脱敏、证据来源、事件完整性、状态转移和任务完整性；领域规则不写入 Kernel。

审计运行增加 `--events EVENTS --run-id RUN_ID`，返回统一 `results`、`gate` 和兼容 `verification` 字段。Skill 声明中的 required Verifier 失败会拒绝，未完成会等待或进入人工复核；advisory Verifier 的非通过结果只产生警告。Verifier 级和组件级 Gate 按严重度保守合并，advisory 只影响它自己的组件，不会掩盖其它 required Verifier 的绑定错误或缺失结果。Agent/人工 handoff 会在顶层返回，但不把契约正文或原始上下文写入账本。Python API 的 `trusted=False` 是不可信 Pack 的进程级 fail-closed 选项，不是 `bsk verifier run` 的 CLI 参数；CLI 只执行用户显式选择的内置、`--root` 或 `--skill-root` Pack。

## Workspace：不可变任务边界

每个逻辑任务先初始化一个不可变 BenszAPI 工作区；Skill 不应自行拼接路径：

```bash
bsk workspace init . --description citation-review
bsk workspace path .bensz-api/task-YYYYMMDD-HHMM-citation-review validate-md-ref input
bsk workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

初始化会创建 `bensz.workspace.ready`（旧 alias：`workspace.ready`）和 `shared/input|output|log` 边界。工作区 manifest、生命周期事件账本和 Skill 元状态快照分层保存且可重放。

strict-v2 Skill 可用单入口完成工作区、运行契约快照和首个 State identity 初始化；该命令只接受新的任务根。显式任务根采用排他创建；自动命名并发冲突会原子选择 `-a`、`-b` 等后缀。任一步失败都只会在 ownership token 匹配时回滚本次新建的任务目录：

```bash
bsk workspace initialize . skill-name org.example.skill.collecting \
  --skill-root path/to/skill --run-id run-1 --attempt-id collecting-1 \
  --description citation-review
```

运行快照保存 Skill/Kernel 版本、identity policy、State 契约、Verifier Markdown 契约/组件计划/helper 资产哈希，以及不含解释器绝对路径的最小 Python 指纹。快照写入后不可覆盖，读取时会重新校验 payload、hash 与派生 ID。State 事件、投影和 action authorization 引用同一个 snapshot ID/hash；契约漂移或 run 不匹配时必须创建新的 workspace/task root。`bsk diagnostics` 单独报告当前 CLI 的实际解释器路径、Python 与 Kernel 版本，便于识别双 Python 环境。

## 运行边界与审计

Pack helper 默认以受信本地进程运行；Kernel 限制输入、stdout/stderr 体积、环境变量和执行时长，超时终止整个进程组。对不可信 Pack 传入 `trusted=False` 会 fail-closed；这是进程级资源边界，不等同于容器或操作系统沙箱。stdio 子进程默认设置 `PYTHONDONTWRITEBYTECODE=1`，不会向 Pack 目录写入 `__pycache__`；显式提供的 `PYTHONPYCACHEPREFIX` 仍会透传，便于把缓存归档到指定目录。

追加式账本保留可选契约快照、授权链和执行审计。`reduce_events()` 只做离线投影重放，不重新调用模型或工具。`verification-v2` 在记录和完成门禁处复核组件唯一性、哈希、证据引用、运行身份、执行者/模型及人工确认；调用方自报的 aggregate pass 不能覆盖 required 失败或漏跑。`summarize_metrics()` 额外汇总组件绑定率和执行者身份覆盖率。

Gate 还可以绑定一次业务证据索引的内容哈希。向 `record_verification()` 或
`record_verification_batch()` 的结果加入 `evidence_hash`（`sha256:<64 位十六进制>`）后，
Kernel 会把它固化到 Kernel 计算的 Gate；`transition(..., gate_event_id=..., evidence_hash=...,
evidence_refs=...)` 只接受同一 run/State visit/attempt、允许放行且证据绑定完全一致的 Gate。
Skill 可用 `EventLog.query_verifications()` 与 `EventLog.query_gates()` 从事件账本读取原始回执，
避免依赖可被后来改写的摘要投影。旧结果不含该字段时保持只读兼容，但不会获得新的证据哈希绑定。

## 开发、测试与发布

```bash
# 包内单元测试（需要已安装 pytest）
python3 -m pytest packages/bensz-skill-kernel/tests

# 构建并检查发布包；默认不上传
python3 tests/publish_bsk_pypi.py
# 只有明确授权时才上传到 PyPI
python3 tests/publish_bsk_pypi.py --upload
```

发布助手把构建产物写入 `tmp/bsk-pypi/`，不读取、复制或记录 PyPI 凭据。完整 API、State/Verifier 契约和变更记录见仓库 `docs/`、源码与 `CHANGELOG.md`。

## 许可证

本包使用 MIT License，详见 [`LICENSE`](LICENSE)。
