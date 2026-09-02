# bensz-skill-kernel

无第三方运行时依赖的 Agent Skill 状态、工作区与 verifier 生命周期内核。

## Python 支持

- 最低支持版本：Python 3.11。
- 已验证测试矩阵：Python 3.11、3.12、3.13。
- 推荐运行版本：Python 3.12。

内核运行时仅依赖 Python 标准库；新 Python 版本会在测试矩阵验证后纳入官方支持范围。

State 与 Verifier 都采用目录化 Contract Pack：一个 Markdown 契约、索引元数据和零个或多个执行组件。`contract_packs.py` 在 `packs.py` 的发现与 JSON-stdio 边界之上统一描述并编排 `script`、`agent`、`human` 组件，绑定契约/计划/组件哈希、证据、依赖顺序、run/attempt 和执行者。State 仍由状态图/迁移适配器解释组件结果，Verifier 仍由 verdict/Gate 适配器解释组件结果，二者不会因共享执行层而混淆语义。

Verifier ID 的 canonical 命名、版本和 alias 迁移规则见仓库级 [`docs/verifier-id-naming.md`](../../docs/verifier-id-naming.md)；State ID 对应规则见 [`docs/state-id-naming.md`](../../docs/state-id-naming.md)。

状态定义采用目录化协议：`states/index.json` 是 State 包目录清单和属性索引，每个元状态目录包含一个 `STATE.md`，可选附带 JSON-stdio
检查或演示脚本。内置状态可以通过统一命令发现；`--root` 会在内置状态之外叠加 Skill
状态包，而非替换它：

```bash
bsk state list
bsk state describe bensz.workspace.ready
bsk state list --root path/to/skill/states
```

Kernel 自己的八个生命周期状态均直接位于 `states/<state>/STATE.md`：`planned`、
`active`、`waiting`、`checking`、`delivering`、`completed`、`failed`、`cancelled`。
目录契约用于发现与人工审核，`runtime.py` 的事件 reducer 是可执行转移语义；测试会阻止两者漂移。
`states/workspace-ready/` 与 `states/workspace-closed/` 保存工作区系统状态。领域 Skill 的业务阶段仍在自身 `references/states/`，
不进入 kernel 生命周期目录。

一个 Skill 现在在根目录 `config.yaml` 的 `runtime` 节声明它采用哪些状态包、初始状态、可用状态
和 Verifier 子集；旧版 `state-machine.json` 仍可只读兼容。kernel 只校验该格式，不理解领域动作。
Agent 先读取状态契约，再用同一命令检查或持久化转移。旧 Pack 的单一 `entrypoint` 继续按原 JSON-stdio 协议执行；新 Pack 可在索引中声明组件计划。required 组件只有全部完成并通过时才允许对应阶段条件成立：

```bash
bsk state list --skill-root path/to/skill
bsk state describe bensz.workspace.ready --skill-root path/to/skill
bsk state check bensz.workspace.ready org.example.skill.collecting --skill-root path/to/skill
bsk state transition .bensz-api/task-YYYYMMDD-HHMM-demo skill-name org.example.skill.collecting \
  --skill-root path/to/skill --context-json '{"input":"report.md"}'
```

状态操作统一返回 `bensz-meta-state-v1` JSON，包含操作、状态、结果、可选脚本回执和
持久化快照。每个 Skill 的当前元状态写入自身 `log/meta-state.json`；它与任务级
`events.ndjson` / `state.json` 分层，后者仍只记录生命周期、验证与交付事实。
成功的 Skill 状态转移同时以 `state.transition`（`state_domain: skill`）追加到任务事件账本，
`bsk rebuild` 会将其投影到 `skill_states`/`skill_state_transitions`，并核验最新元状态快照的稳定字段哈希；快照缺失时仍可据事件账本恢复，漂移则返回 `integrity_error`。

状态 `invariants` 默认是面向领域的说明；Kernel 只执行有明确协议的通用 invariant。
当前支持 `verifier-result-recorded`：离开声明该 invariant 的状态前，任务事件账本必须
同时包含 `verification.result` 和 `verification.gate`。未满足时 CLI 返回结构化
`rejected`，不会写入新的状态快照；领域专属 invariant 仍由 Skill helper 或人工复核负责。
事件带有运行身份时，`run_id` 与 `attempt_id` 必须成对传入，避免重试之间串用验证证据。

内置 State 的 ID、版本、kind、aliases、classification、tags、`mode`、`assurance_tier` 和 `components` 由 `states/index.json` 单独管理；
`STATE.md` 只保留 `description`、`entry_conditions`、`invariants`、`transitions` 等状态工作契约及正文说明。
没有 `index.json` 的外部兼容目录仍可在 `STATE.md` frontmatter 声明完整属性。可选 `entrypoint` 是相对于该 `STATE.md` 目录的脚本：stdin 接收
`{"protocol":"bensz-meta-state-v1","state":...,"request":...}`，stdout 只能输出一个
JSON 对象，其中 `verdict` 是 `pass`、`fail`、`uncertain`、`unchecked`、`error`、
`timed_out` 或 `skipped`，并可带 `summary`、`facts`、`evidence_refs`。只有成功执行且
`verdict=pass` 的 helper 会允许持久化转移。显式 `agent`/`human` 组件会先返回带契约、组件、计划和运行身份的 handoff；外部执行者按 handoff 回传标准组件结果后，`StateContractAdapter` 才会把公共结果解释为阶段是否满足。没有新组件声明的旧 instruction-only 状态仍保持兼容行为。

每个逻辑任务先初始化一个不可变的 BenszAPI 工作区；Skill 不应自行拼接路径，而应通过
工作区命令取得自己的 `input`、`output` 和 `log` 边界：

```bash
bsk workspace init . --description citation-review
bsk workspace path .bensz-api/task-YYYYMMDD-HHMM-citation-review validate-md-ref input
bsk workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

初始化结果中的 `bensz.workspace.ready` 是所有 Skill 状态的系统级前置状态，旧 ID `workspace.ready` 作为 alias 保留。工作区还会创建
共享 `shared/input|output|log` 边界；工作区清单保存协议版本和初始状态，事件账本仍由
下方的生命周期命令追加和重放；两者保持分层，避免把 Skill 领域状态硬编码进核心 reducer。

安装后，Skill 通过 `bsk` 发现和调用包内 `bensz_skill_kernel/verifiers/` 目录中的 verifier。`verifiers/index.json` 是 Verifier 包目录清单和执行计划的单一来源；每个 verifier 由一个 `VERIFIER.md` 契约和 `components` 组成。脚本组件通过 stdin/stdout 交换 JSON，Agent/人工组件由 Kernel 准备 handoff、由外部宿主执行并回传绑定结果：

```bash
bsk verifier list --tag citation
bsk verifier describe bensz.evidence.citation-truth-fit --version 1.0.0
bsk verifier run bensz.document.markdown-link-integrity --input README.md
```

内置 Verifier 的 ID、版本、aliases、classification、tags、契约路径、mode、assurance 和组件由
`verifiers/index.json` 单独管理；`VERIFIER.md` 专注判断目标、证据边界与执行说明。
没有 `index.json` 的外部兼容目录仍可使用原 YAML frontmatter；旧单入口 Pack 会兼容解释为一个脚本组件，旧 instruction-only Pack 会给出缺少显式组件元数据的诊断。脚本入口遵循：stdin 一个请求 JSON，stdout
一个结果 JSON（`verdict` 为 `pass`、`fail`、`uncertain`、`unchecked`、`error`、
`timed_out` 或 `skipped`）。kernel 负责超时、异常、非法 JSON 和结果字段归一化。

当前内置示例：

- `bensz.artifact.file-existence`：确认本地产物是现有普通文件；旧 ID `artifact.file-exists` 作为 alias 保留。
- `bensz.document.markdown-link-integrity`：Markdown 链接和锚点完整性检查，标签 `common`、`markdown`、`links`、`deterministic`；旧 ID `markdown.link-integrity`、`markdown.references` 作为 alias 保留。
- `bensz.evidence.citation-truth-fit`：格式无关的引用真实性与适切性契约；索引将它显式声明为 `agent` 组件，Kernel 不捆绑模型，未回传绑定结果时保持 `unchecked`/`wait`；旧 ID `citation.truth-and-fit` 作为 alias 保留。

首批通用原子 Pack 还包括合同一致性、路径范围、Schema、diff 范围、敏感信息脱敏、证据来源、事件完整性、状态转移和任务完整性。每个 Pack 都位于 `verifiers/<slug>/`，包含可审查的 `VERIFIER.md` 与可选 `scripts/verify.py`；共享实现位于 kernel 模块层的 `atomic_verifiers.py`，不占用 Verifier 清单目录，也不再把规则主体塞进 `builtins.py`。它们只接受通用事实，不包含领域规则。`index.json` 是属性的单一来源；注册表会校验其目录、契约和入口真实存在，且没有漏列或陈旧条目。

代码只定义发现、调用、超时、结果归一化和事件记录协议，不内置领域判断流程。Markdown、LaTeX、Word 等格式适配器可各自选择适用 verifier。

需要审计时，为 `run` 增加 `--events EVENTS --run-id RUN_ID`；命令会输出统一 `results`、`gate` 和兼容的 `verification` 字段。Agent/人工组件未执行时还会在顶层输出完整 handoff，但 handoff 不进入持久化 `results`，避免把契约正文或原始上下文写入事件账本。Python Adapter 使用 `FilesystemVerifierRegistry.run_contract()` 接收外部组件提交。生命周期底层命令仍可通过 `bsk status/rebuild/append/transition/artifact/validation/delivery` 使用。

# 运行边界与审计

Pack helper 默认以受信本地进程运行，但内核会限制输入、stdout/stderr 体积、环境变量和执行时长，并在超时后终止整个进程组；调用不可信 Pack 时应显式传入 `trusted=False`，此时会 fail-closed。该边界是进程级资源与路径约束，不等同于容器或操作系统沙箱。

事件账本除状态投影外还保留可选的运行契约快照、授权链和执行审计轨迹；`reduce_events()` 仅用于离线状态投影重放，不会重新调用模型或工具。`verification-v2` 结果会在记录和完成门禁处复核组件唯一性、哈希、证据引用、run/attempt、执行者/模型及人工确认，调用方自报的 aggregate pass 不能覆盖 required 失败或漏跑。`summarize_metrics()` 额外汇总组件绑定率和执行者身份覆盖率。
