# Verifier 契约与边界

本 Skill 使用目录化的 `bensz.prompt.contract-conformance@1.0.0`。它是确定性的结构检查，
不判断原始 prompt 的事实真实性、意图等价性或风格偏好。

## 调用（每次执行必做）

```bash
python SKILL_ROOT/references/verifiers/program-conformance/scripts/verify.py \
  < VERIFIER_REQUEST_JSON > VERIFIER_RESULT_JSON
bsk verification EVENTS_NDJSON \
  --result-file VERIFIER_RESULT_JSON \
  --gate-json '{"decision":"pending","reason":"kernel must recompute"}' \
  --run-id RUN_ID --attempt-id ATTEMPT_ID --scope skill
```

请求的 `subject.program` 必须是非空字符串；可选 `context.required_blocks` 覆盖最小块集合，
`context.control_required=true` 时还要求流程包含条件或迭代标记。验证器返回标准
`pass`/`fail`/`error` 结果及结构化 findings；超大、非法 JSON 或缺失字段必须保持 error，
不得由调用方猜测为通过。`--gate-json` 只是触发 Gate 事件的候选值，Kernel 会依据原始结果
重算并写入最终 Gate；不得手写允许结论。验证结果或 Gate 缺失时，状态机不得离开
`schema-valid`。

结果和 Gate 应写入任务事件账本。`unchecked`、`uncertain` 或执行错误均不能被翻译成
`reviewed`，而应保留原始结果并走人工复核或失败路径。
