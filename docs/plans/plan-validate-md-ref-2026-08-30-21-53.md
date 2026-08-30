# validate-md-ref / Kernel Verifier Gate 版本一致性优化计划

## 背景与结论

Round 2 的 `validate-md-ref` 实例已正常完成状态机闭环：`workspace.ready → input-ready → checking → reported`。链接完整性 Verifier（`bensz.document.markdown-link-integrity@1.0.0`）返回 `pass`，语义 Verifier（`bensz.evidence.citation-truth-fit@1.0.0`）按 instruction-only 契约返回 `unchecked`，Kernel Gate 保守返回 `manual_review`；事件链、快照和 rebuild 投影一致。Round 1 暴露的 required Verifier 缺失 fail-open 与非对象请求异常问题已在 Kernel 0.12.4 修复，并有回归测试覆盖。

仍确认一个可复现的 P1 契约缺陷：`apply_gate` 从 `requirements` 中只提取 Verifier ID，忽略声明的 `version`。因此，要求 `bensz.document.markdown-link-integrity@1.0.0` 时，传入同 ID 的 `@9.9.9` 且 verdict 为 `pass` 的结果会被错误判定为 `allow`。这会破坏版本化 Verifier 契约，并可能影响直接调用 Kernel 公共 API、事件重算和完成门禁路径。`normalize_requirements` 虽校验并保留版本，但 Gate 判定阶段丢弃了该信息。

## 优化范围（P1/P2）

### P1：Gate 必须校验 required Verifier 的版本

修改 `packages/bensz-skill-kernel/src/bensz_skill_kernel/verifiers.py` 的 `apply_gate`：

- 将 required requirement 规范化为 `(canonical_id, required_version)` 约束；兼容旧的仅 ID 形式（无 `version` 时按现有 ID 语义处理）。
- 对每个必需项同时检查结果的 `verifier_id` 与 `verifier_version`。结果缺失或版本不匹配时，返回稳定的 `manual_review`（reason 可区分 missing/mismatched version），并把可审计的约束标识加入 `unresolved`。
- 保持现有失败、unchecked/uncertain/timed_out、可选 Verifier 和 `result_refs` 语义不变；不得因版本检查放宽门禁。
- 确保 `EventLog` 的批量记录、`_guard_completion` 重算和 Skill CLI 使用同一 Gate 语义，避免记录时与完成时判断不一致。

### P2：Gate 不应静默接受非法 requirement 项

`apply_gate` 当前会忽略 iterable 中的 `None`、字符串或缺少 ID 的对象，并把非布尔 `required` 值按 Python truthiness 处理；在未先调用 `normalize_requirements` 的公共 API 路径上，这可能把本应拒绝的约束降为空集合并返回 `allow`。增加结构化输入校验，非法 requirement 返回稳定的 `manual_review`/`reject`（遵循现有错误语义），并补充非法项、缺少 ID、非布尔 `required` 的回归测试。该问题危害低于版本错配，列为 P2；正常 Skill 路径已由 `normalize_requirements` 提前拦截。

## 测试与验证

在 `packages/bensz-skill-kernel/tests/runtime/test_verifiers.py` 增加至少以下回归用例：

1. required 版本一致且 pass → `allow`。
2. required 版本不匹配 → `manual_review`，并列出稳定 unresolved 标识。
3. required 结果缺少版本或版本非法 → 不能 allow（结构化 manual_review/reject，按现有错误契约确定）。
4. 多个 required/optional Verifier 混合时，仅 required 的版本错配阻止 allow；optional 版本差异不改变既有 optional 失败策略（如无版本约束则保持兼容）。
5. `EventLog.record_verification_batch` 与 `_guard_completion` 对版本错配均 fail-closed；现有 43 项 Verifier 运行时测试和 CLI 批量 Gate/幂等重试测试继续通过。

完成后从仓库根目录运行定向 pytest，并执行 Pack discovery、Gate 重算及 canonical/alias 路径检查；测试产物写入任务工作区或 `tmp/`，不写入源码目录。

## 非目标与风险

- 本计划不改变 `validate-md-ref` 的网络/SSRF 策略、跳过语义、instruction-only 语义复核或状态机转移。
- 不将本轮 `valid_rate=45.8%` 解释为引用语义正确率；该指标是可验证链接比例，属于结果边界而非缺陷。
- Round 2 未发现 P0 或其它 P1/P2 缺陷；cwd 脆弱性观察属于测试调用约定改进，不纳入本次必须修复范围。

## 验收标准

- 任意 required requirement 带版本时，只有对应 ID+版本的 completed/pass 结果可使 Gate 进入 `allow`。
- 版本缺失、错配或结果缺失均不会 fail-open；Gate、事件记录和完成守卫的重算结果一致。
- 原有状态机、Verifier 结果绑定、快照/rebuild 和幂等行为无回归。
