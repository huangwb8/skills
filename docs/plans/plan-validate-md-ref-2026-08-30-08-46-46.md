# validate-md-ref 与 bensz-skill-kernel 源代码优化计划

## 结论与范围

本次实例表明状态机和验证器都实际执行了，但它们之间的协作仍有契约缺口，不能把当前结果视为“完整闭环”。因此需要同时优化：

- `packages/bensz-skill-kernel`：统一外部网络不确定性、Verifier Gate 策略、状态 invariant 证据绑定和 instruction-only 证据引用保留；
- `skills/beta/validate-md-ref`：消费 runtime 中声明的 required/advisory 配置，避免适配器自行使用过宽的默认 Gate。

本计划只规划源代码、契约、测试和同步文档，不在本轮直接修改实现或原始 Markdown。

## 本次实例的可核对证据

任务工作区为 `.bensz-api/task-lsm-validate-md-ref-2026-08-30-08-46-46/`：

- `validate-md-ref/log/meta-state.json` 的最终状态为 `bensz.validate-md-ref.reported`，说明 `input-ready → checking → reported` 的状态转移命令确实生效；
- 任务级 `log/events.ndjson` 包含两个 `verification.result` 和一个 `verification.gate`，链接 Verifier 为 `fail`，语义 Verifier 为 `unchecked`，Gate 为 `reject`；
- 13 个外部 URL 的 `status_code` 均为 `null`，失败原因是 DNS 解析错误，而不是 HTTP 4xx/5xx；站内 11 个 anchor 均有效；
- 状态快照存在，但任务级事件中没有 `state.transition` 事件，状态阶段不是事件账本可重放事实，而是 Skill 独立的可覆盖快照；这属于当前分层设计的可观测性限制，本计划不把它单独升级为必须改动的 bug；
- `config.yaml` 明确声明链接完整性 Verifier `required: true`、citation Verifier `required: false`，但 `scripts/validate_links.py` 调用 `apply_gate(normalized)` 时没有传入任何 required 选择；
- `FilesystemVerifierRegistry.run()` 对 instruction-only Verifier 直接返回空的 `evidence_refs`，本次 citation 结果因此丢失了适配器已提交的证据引用。

## 缺陷清单与优先级

### 外部网络故障被误报为确定性链接失败（P1）

`markdown-link-integrity` 的 `collector._probe()` 捕获 `URLError`、DNS 失败、连接错误和超时后，只写入 `error` 并保持 `valid: false`；`verify.py` 再依据 `summary.invalid` 生成 `verdict: fail`。这会把“当前运行环境无法观察 URL”与“URL 已被 HTTP 明确证明失效”混为一谈，并在本次实例中直接触发 required Gate `reject`。

优化方向：

1. 为逐条引用增加稳定的观测分类，例如 `validation_status: valid|invalid|unresolved|skipped`，保留现有 `valid` 字段兼容旧调用方；
2. HTTP 4xx/5xx、缺失本地 anchor、越界相对文件继续作为确定性 `invalid/fail`；DNS、连接失败、超时和无 HTTP 状态码改为 `unresolved`，映射到 `unchecked` 或 `timed_out`，Gate 进入 `manual_review`/`wait`；
3. 摘要增加 `unresolved` 计数，并让 `verify.py` 只把确定性 invalid 生成 finding；
4. 保留错误文本、最终 URL 和安全跳转信息，但不把环境错误伪装成来源失效；
5. 对旧版本 Pack 提供明确版本迁移（结果语义改变按仓库版本策略视为 major 变更，建议新 Verifier 版本或兼容模式，不静默改变 `1.0.0` 语义）。

### required/advisory 声明没有进入 Gate（P1）

`skills/beta/validate-md-ref/config.yaml` 中的 `runtime.verifiers[].required` 目前只被人阅读：Kernel 的 `SkillStateDeclaration` 不解析 Verifier 选择，适配器也没有读取该列表；`apply_gate()` 只有一个全局 `required: bool` 参数。因而当 optional Verifier 将来返回 `fail` 时，当前脚本会错误地产生 `reject`，与文档所称 advisory 不一致。

优化方向：

1. 在 Kernel 增加可版本化的 Gate 输入契约，支持 `required_ids` 或 `requirements: [{verifier_id, required}]`，按 canonical ID（忽略版本后缀匹配规则需写入契约）分类 failure/unknown；
2. 扩展 runtime 声明解析或提供只读 accessor，使 Skill 能取得声明的 Verifier ID、版本和 required 标志，并拒绝重复/未知条目；
3. `validate_links.py` 从同一 `config.yaml.runtime.verifiers` 生成 Gate 参数，并把 required 集合传给 `apply_gate()` 与 `summarize_metrics(required_ids=...)`；
4. Gate 规则保持保守：required 的确定性失败为 `reject`，optional 失败为 `allow_with_warnings`，缺证据/网络未知为 `manual_review` 或 `wait`；
5. 将该配置写入运行快照/事件，确保后续回放知道当时采用的 Gate 策略。

### 状态 invariant 未绑定当前运行且不检查 Gate 语义（P1）

`check_state_invariants()` 目前只把整个事件流压成事件类型集合。只要历史上出现过一次 `verification.result` 和 `verification.gate`，就能满足 `verifier-result-recorded`；它不区分 `run_id`/`attempt_id`，不校验 Gate 的 `result_refs`、`computed_by`、结果事件关联，也不区分 `decision: reject`。实测使用带旧 `run_id` 的两个事件仍可从 checking 转到 reported；带当前 `reject` Gate 的事件也可转移。

优化方向：

1. 将 invariant 检查上下文扩展为当前 `run_id`、`attempt_id`、Verifier 选择和所需 Gate 策略；
2. 只接受同一运行且顺序正确的结果/Gate 对，要求 Gate 的 `result_refs` 覆盖该运行结果并由 Kernel 计算；
3. 为需要成功才能离开的状态新增明确的通用 invariant（例如 `verifier-gate-allow`），不把领域语义硬编码到 Kernel；`verifier-result-recorded` 继续仅表达“已记录”；
4. CLI 状态转移命令传入并持久化运行身份，拒绝跨 run 的陈旧事件满足当前 invariant；
5. 明确 `reported` 是否允许报告 reject：若允许，应在文档中把它定义为“结果已报告而非验证通过”；若要求验证成功，应增加 `failed`/`waiting` 分支并由新 invariant 控制，避免调用方误把 `reported` 当作成功完成。

### instruction-only Verifier 丢失证据引用（P2）

`FilesystemVerifierRegistry.run()` 在无 entrypoint 时直接构造 `unchecked` 结果，未从 `VerificationRequest.evidence` 或请求中的证据列表提取 `evidence_refs`。这削弱了 citation 语义复核的可审计性；本次事件中的 citation 结果 `evidence_refs` 为空，尽管适配器已提供 `subject_context`、`source_metadata` 和 `source_excerpt`。

优化方向：

- instruction-only 返回 `unchecked` 时保留请求中的证据 ref，并在结果中声明缺少执行引擎而非缺少证据；
- 对 Mapping 与 `VerificationRequest` 两种输入统一归一化证据读取；
- 增加不会泄露证据正文的回归断言，只检查 ref、哈希和状态字段。

## 实施顺序

### 阶段 A：冻结兼容契约

- 为 `validation_status/unresolved`、Gate requirements、运行身份和证据引用写 JSON Schema/字段说明；
- 决定 Verifier/Kernel/Skill 版本升级与 alias 策略。由于网络结果和 Gate 语义变化，按项目变更矩阵走 major 迁移；
- 补充迁移说明：旧消费者仍可读取 `valid`、`invalid`、`skipped`，新消费者使用 `unresolved` 和版本化 Gate。

### 阶段 B：修复 Kernel Verifier 结果语义

- 修改 Markdown collector、Pack verify 入口和指标汇总；
- 修改 `apply_gate` 以支持逐 Verifier required 策略；
- 修复 instruction-only evidence refs；
- 保持 SSRF、重定向逐跳检查、超时和进程边界不回退。

### 阶段 C：修复 Skill 适配与运行快照

- 让 `validate_links.py` 从 runtime 声明读取 Verifier 版本/required 配置；
- 将 Gate、required 集合、unresolved 计数和运行身份写入结果与事件；
- 保持 Kernel facts 为唯一链接事实来源，不再恢复旧本地探测结果合并。

### 阶段 D：加强 State 证据绑定

- 扩展 invariant 检查 API 和 CLI 上下文；
- 增加当前 run、陈旧 run、reject Gate、错配 result_refs、伪造 Gate 和重复事件测试；
- 同步 `validate-md-ref` 状态契约，明确 reported 的“报告完成”与验证 Gate 的“通过/拒绝”不是同一语义。

### 阶段 E：文档、版本与回归

- 同步 `SKILL.md`、`README.md`、`references/state-machine.md`、`references/verifiers.md`、Kernel README 和 CHANGELOG；
- 更新 `verifiers/index.json`、Pack 版本和 package data；
- 运行包测试、Skill QA、Pack/index 一致性、canonical/alias、非法输入、超时/DNS、重定向 SSRF、事件重放和安装后发现检查；
- 通过 BAC 记录变更、测试命令、版本迁移和未解决的环境限制。

## 验收标准

- 对同一 Markdown：HTTP 404 与缺失 anchor 仍为 `fail`；DNS/连接/超时无 HTTP 状态时为 `unchecked`/`timed_out`，摘要含 `unresolved`，Gate 不再误报 `reject`；
- runtime 声明的 required/advisory 组合与 Gate 决策、metrics 和事件完全一致；optional failure 只能产生 warning，required failure 才 reject；
- 旧运行事件不能满足新运行 invariant；reject Gate 不能满足 `verifier-gate-allow`；result/Gate 引用和 run/attempt 不匹配时结构化拒绝；
- instruction-only 结果保留 evidence refs，且不保存证据正文、密钥或隐私；
- `reduce_events()` 和状态快照在重放/迁移后给出一致的可解释状态；
- 所有现有 Kernel（80 项）与 Skill 回归测试保持通过，新增边界测试覆盖上述反例；
- 原始 Markdown 不被修改，正式报告仍只引用事实、Gate 和不确定性，不把可达性解释成引用真实性。

## 非目标

- 本计划不在 Kernel 内实现 citation 语义判断引擎；`citation-truth-fit` 仍可保持 instruction-only/`unchecked`；
- 不把领域业务状态硬编码进 Kernel，不强制所有 Skill 采用同一 Gate 到生命周期的映射；
- 不恢复 Skill 侧独立网络探测或双重事实源；
- 不进行无关重构、远程发布或自动修改用户的 Markdown。
