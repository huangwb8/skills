# validate-md-ref 第 1 轮 Kernel 缺陷优化计划

## 目标

修复本轮验证暴露的两个当前可复现问题，同时保持已有状态机、Verifier 证据边界、
批量事务和 SSRF 防护行为不变：

1. `apply_gate` 在声明的必需 Verifier 缺失时不得返回 `allow`（P1）。
2. `FilesystemVerifierRegistry.run` 对非 JSON object 请求返回稳定、结构化的错误
   结果，而不是抛出 `AttributeError`（P2）。

## 背景与证据

本轮运行账本 `task-lsm-validate-md-ref-2026-08-30-05-09` 已完成
`input-ready → checking → reported`；链接 Verifier 为 `pass`，语义
instruction-only Verifier 为 `unchecked`，Gate 为 `manual_review`。历史“逐结果
写入导致 Gate 只覆盖最后结果”的问题已通过批量登记修复，不得回退或放宽
`verifier-result-recorded` 不变量。

当前 P1 复现：

```python
result = VerificationResult(
    "bensz.document.markdown-link-integrity", "1.0.0", "completed", "pass"
)
apply_gate([result], requirements=[
    {"id": "bensz.evidence.citation-truth-fit", "required": True}
])
# 当前错误结果：decision == "allow"
```

当前 P2 复现：`FilesystemVerifierRegistry.run(verifier_id, [])` 或以 `None` 作为
request 时，在访问 `.get` 处抛出未结构化异常。

## 实施阶段

### P1：Gate 缺失项 fail-closed

- 在 `packages/bensz-skill-kernel/src/bensz_skill_kernel/verifiers.py` 统一解析
  `requirements`/`required_ids`，建立 canonical required 集合和实际结果 ID 集合。
- 在计算 failures/unknown 前检测 `missing_required`；返回稳定
  `manual_review`（reason 可固定为 `required verifier result missing`），
  `unresolved` 按确定顺序列出缺失 canonical IDs，`result_refs` 仍仅绑定实际结果。
- 确认 `record_verification`、`record_verification_batch`、`_guard_completion` 和
  CLI 均使用同一语义；不得以额外状态检查掩盖 Gate 的错误 allow。
- 对 alias 输入先 canonicalize，再参与缺失检测；保留 optional-only、无
  requirements、空结果等现有语义。

### P2：非法 request 结构化处理

- 在 `FilesystemVerifierRegistry.run` 解析 request 前检查是否为
  `Mapping` 或 `VerificationRequest`；其他类型返回现有协议允许的
  `execution_status="error"`、`verdict="error"` 及脱敏 `uncertainty_reason`，或
  按既有 CLI 错误协议抛出统一 `ValueError`，二者择一并保持全 API 一致。
- 增加 list、`None`、标量和非法 JSON 的回归断言，确保 stderr/异常不泄露输入内容。

### 回归、文档与记录

- 在 `packages/bensz-skill-kernel/tests/runtime/test_verifiers.py` 及相关 CLI/
  runtime 测试中覆盖：缺失单个 required、全部 required、optional-only、alias→
  canonical、批量 pass+unchecked、非法 request，以及现有历史批量 Gate 全覆盖。
- 使用 source-tree Kernel 重放 `validate-md-ref`，核验结果集合、Gate
  `result_refs`、`manual_review` 和 `reported` 状态均未退化。
- 按仓库治理要求同步受影响的 README/docs、版本和 `CHANGELOG.md`，并在
  `docs/contribution.bac` 记录需求、修改和验证证据；测试产物写入 `tmp/` 或本轮
  `.bensz-api` 工作区。

## 验收标准

- 任一 required Verifier 缺失时，`apply_gate`、单结果和批量登记都不会产生
  `allow`；Gate 的 unresolved 明确包含缺失 canonical ID。
- 现有两个结果（link pass + citation unchecked）仍得到 `manual_review`，完整
  `result_refs`，状态可到 `reported`。
- 非对象 request 不再出现 `AttributeError`；调用方得到稳定 error 结果/错误类别。
- 现有 canonical/alias、幂等、run/attempt 隔离、SSRF/DNS 跳过和安全日志测试全部
  通过；不修改输入 Markdown。

## 风险与回滚

变更集中在 Gate 计算和输入校验，可能使依赖错误 `allow` 的调用方显式进入
`manual_review`，这是预期的安全行为。若发现兼容性问题，应回滚本次提交并保留
失败测试证据；不得通过放宽状态门禁或删除缺失检查来恢复旧行为。
