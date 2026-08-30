# validate-md-ref 状态机、Verifier 与运行时一致性优化计划

## 调查结论

本实例中状态机和 Verifier 都有运行证据，但“执行过”不等于“闭环可重放”或“始终使用仓库源码”：

- `validate-md-ref/log/meta-state.json` 的 `last_operation` 从
  `bensz.validate-md-ref.reported` 进入 `bensz.workspace.closed`，说明状态执行器至少成功走过
  `input-ready → checking → reported`，并执行了终态关闭。
- 任务级和 Skill 级 `events.ndjson` 均记录了两个 `verification.result` 和一个
  `verification.gate`。链接完整性结果为 `unchecked`（13 个 URL 因 DNS 不可观测），语义引用
  Verifier 为 instruction-only/`unchecked`，Gate 为 `manual_review`。这表明 checking 阶段的
  “结果已记录”门禁与不确定性披露能够协作。
- 状态快照只保存当前状态，事件账本没有 `state.transition` 事件；删除或覆盖快照后不能从任务
  事件流重建 Skill 元状态。因此状态机是有效的运行时门禁，但不是完整的可重放审计事实。
- 仓库源码测试通过（Kernel 与 Skill QA 共 89 项），但当前 shell 中的 `bsk` 来自已安装的
  `bensz-skill-kernel 0.11.0`，而仓库 `pyproject.toml` 声明 0.12.0。用该 `bsk` 复跑同一探针
  时，`summary.unresolved` 不出现，网络不可观测会按旧 Gate 语义导致 `reject`；这与仓库源码
  预期不一致。

## 状态机与 Verifier 的协作方式

1. `input-ready` 的 helper 检查 `context.document` 是存在且可读的 Markdown；通过后 Kernel
   写入 Skill 元状态快照。
2. 进入 `checking` 后，Skill 适配器调用
   `bensz.document.markdown-link-integrity` 收集链接事实，再调用
   `bensz.evidence.citation-truth-fit`。后者当前是 instruction-only，只产生
   `unchecked`，不冒充语义判断。
3. 适配器把两个结果交给 Kernel Gate，并将 `verification.result`/`verification.gate` 写入任务
   事件账本。离开 `checking` 时，`verifier-result-recorded` invariant 检查所需事件是否存在；
   `reported` 负责向用户报告事实与不确定性，随后工作区可进入 `closed`。
4. 该协作只在调用方传入正确的 `run_id`/`attempt_id` 时具备运行级隔离；未传入时 Kernel 会
   使用整个历史事件流判断 invariant，存在陈旧结果满足当前运行的风险。

## 已确认的源码缺陷

### P0：事件记录命令无版本校验，可能使用旧 bsk

`validate_links.py` 的 `_load_verifier_runtime()` 当前能够把仓库 `src` 放到 `sys.path`，但
`record_runtime_events()` 通过 `_kernel_command()` 优先选择 PATH 中任意可用的 `bsk`，只检查
`--help` 是否包含 `verification`，不检查 Kernel 版本、Pack 版本或来源。当前环境的 `bsk` 是
0.11.0，而仓库源码/构建元数据为 0.12.0；直接用该命令复跑会丢失新 `unresolved` 字段并采用旧
Gate 语义。虽然事件记录只是追加适配器已经计算好的结果，但协议/审计能力仍可能发生漂移。

**优化方向**：通过 `Path(__file__).resolve()` 校验源码和 Pack 的存在性；事件记录优先调用与
适配器同一源码版本的 `python -m bensz_skill_kernel.cli`，或严格校验 `bsk` 的版本与能力清单。
不匹配时结构化失败并给出升级提示，不得静默使用旧可执行文件；增加从任意工作目录、旧 bsk、无
bsk 和 wheel 安装环境调用的回归测试。

### P1：Kernel 版本单一真相破裂

`packages/bensz-skill-kernel/pyproject.toml` 为 0.12.0，`src/bensz_skill_kernel/__init__.py`
仍暴露 `__version__ = 0.11.0`，环境安装包也确为 0.11.0。调用方无法可靠判断 API、Gate 和 Pack
语义是否与源码一致。

**优化方向**：移除硬编码或在构建时从唯一版本来源生成 `__version__`；加入打包后
`import bensz_skill_kernel; importlib.metadata.version(...)` 一致性测试，并在 Skill 启动时校验
Kernel 版本与 runtime 声明。

### P1：状态元状态没有事件化，无法重放

`state transition` 只覆盖 `log/meta-state.json`，而任务 `events.ndjson` 只包含 Verifier 事件。
`bensz-skill-kernel` 的事件投影因此无法证明状态转移顺序，也无法在快照损坏后恢复。

**优化方向**：为 Skill 状态转移追加规范化 `state.transition` 事件（包含 canonical state、版本、
前后状态、运行身份、快照哈希和结果），快照仅作为缓存；`rebuild`/审计读取事件重放并检测快照
漂移。保持系统生命周期状态与 Skill 领域状态分层，避免把领域规则硬编码进 Kernel。

### P1：invariant 默认允许跨运行历史污染

`check_state_invariants()` 只有在调用方提供 `context.run_id` 或 `attempt_id` 时才过滤事件；而
文档中的状态转移示例没有传入运行身份。这样，历史上任意一次 `verification.result` 与
`verification.gate` 就可能满足当前 `checking` 的 `verifier-result-recorded`。

**优化方向**：对声明了该 invariant 的状态，要求显式运行身份，或从最近一次 `run.started` 推导并
拒绝歧义；校验结果/Gate 的同一 `run_id`、`attempt_id`、`result_event_id` 和 `result_refs`，并
增加陈旧运行、错配 Gate、重复运行和缺少身份的测试。明确 `reported` 是“已报告”而非“验证通过”，
如需通过才能结束则使用独立的 `verifier-gate-allow` invariant。

### P1：runtime Verifier 声明仍缺少严格契约校验

`validate_links.py` 会从配置读取 `runtime.verifiers`，但对重复 ID、未知 ID、缺失必需的链接
Verifier、版本格式和 alias 没有统一早期校验；适配器可能把未声明的结果追加为 optional，改变
Gate 语义。

**优化方向**：由 `SkillStateDeclaration` 或共享 accessor 解析并校验 Verifier 清单；要求 canonical
ID、版本和 `required` 类型合法，拒绝重复/未知条目及关键 Verifier 缺失；Gate、metrics、运行快照
和事件使用同一份规范化 requirements。

### P2：instruction-only 证据与运行环境状态需保持可审计

仓库源码已修复 instruction-only 结果保留 evidence refs，但旧安装包仍会丢失或表现不同。环境
版本漂移时，报告无法仅凭结果判断使用了哪一份实现。

**优化方向**：在结果、事件和任务 manifest 中记录 Kernel/Pack 版本、源码或安装来源哈希；保留
证据 ref/哈希而不写入证据正文；发现版本不匹配时返回结构化 `error`，不继续生成看似正常的报告。

## 实施顺序

### 阶段 A：冻结兼容契约

- 定义 Kernel 版本、源码/安装来源、Pack 版本和 Skill runtime requirements 的 JSON 字段。
- 决定 0.12.0 的迁移策略；旧 `valid`/`invalid` 字段继续兼容，新 `unresolved`/运行来源字段
  通过版本化协议发布。
- 为状态转移事件定义 canonical ID、前后状态、运行身份和快照哈希字段。

### 阶段 B：修复发现与版本一致性

- 保留已验证正确的源码路径定位；删除“只要 PATH 中有 bsk 就使用”的无版本探测，改为同版本
  Kernel/CLI 选择与能力校验。
- 增加源码优先/安装包校验策略、最小版本约束和结构化失败信息。
- 统一 `__version__` 与构建元数据，补充 wheel 安装后发现测试。

### 阶段 C：强化 State/Verifier 运行契约

- 将 requirements 解析、canonical/alias 解析、重复和未知项检查集中到 Kernel accessor。
- 让 Gate、metrics、事件和 manifest 复用规范化 requirements。
- 强制 invariant 使用当前运行身份并校验结果/Gate 绑定；补充 reject、manual_review、旧 run
  和错配引用的边界测试。

### 阶段 D：事件化与回放

- 状态转移成功后追加 `state.transition`，失败只记录结构化拒绝事件（不改变状态）。
- `rebuild` 从事件重放 Skill 状态并验证快照哈希；保留旧快照的读取兼容和迁移说明。
- 让 `reported`/`closed` 的审计语义与生命周期 `completed`/`failed` 清楚分离。

### 阶段 E：Skill 适配、文档与回归

- 更新 `SKILL.md`、README、state-machine/verifiers references、Kernel README、Pack 索引和
  CHANGELOG。
- 测试从任意 cwd 调用、无 bsk、旧 bsk、版本不匹配、DNS/连接/超时、HTTP 4xx、anchor 缺失、
  SSRF 重定向、instruction-only evidence refs、非法 JSON、超时、事件重放及安装后 package data。
- 用 BAC 记录实现、验证命令、版本迁移和环境限制；不得记录密钥、完整原始文档或私密路径。

## 验收标准

- Skill 只能使用与声明匹配的 Kernel/Pack；版本不匹配时明确失败，不静默降级。
- 同一输入在源码运行和 wheel 安装运行下结果协议一致；DNS/连接不可观测为
  `unresolved`/`timed_out`，不会被误判为确定性 invalid。
- required/advisory Gate、metrics、事件和报告一致；optional failure 不会被当作 required reject。
- 没有当前 run 的结果/Gate、结果引用不完整或 Gate 来自旧 run 时，checking 不能进入 reported。
- 删除快照后可由事件重放出相同状态；快照哈希漂移会被报告。
- 现有 Kernel/Skill 测试保持通过，新增反例测试覆盖上述缺陷；原始 Markdown 始终只读。

## 非目标

- 不在 Kernel 中实现 citation 真实性或适切性判断；instruction-only Verifier 仍需人工/领域引擎。
- 不把 `validate-md-ref` 的领域规则硬编码进通用 Kernel。
- 不在本计划阶段安装、上传、发布或远程修改任何环境，也不修改用户原始 Markdown。
