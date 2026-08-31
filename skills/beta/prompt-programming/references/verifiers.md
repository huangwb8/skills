# Verifier 契约与边界

本 Skill 使用两个互补的目录化 Verifier：

- `bensz.prompt.contract-conformance@1.0.0`：确定性的结构门禁。
- `bensz.prompt.semantic-equivalence@1.0.0`：由当前 AI 按 `semantic-equivalence/PROMPT.md`
  执行的语义等价性评审，assurance tier 为 `llm_judge`。

结构检查不判断原始 prompt 的意图等价性；语义评审也不负责文件解析。两者必须同时通过。

## 调用（每次执行必做）

```bash
python SKILL_ROOT/references/verifiers/program-conformance/scripts/verify.py \
  < VERIFIER_REQUEST_JSON > VERIFIER_RESULT_JSON
bsk verification EVENTS_NDJSON \
  --result-file VERIFIER_RESULTS_JSON \
  --gate-json '{"decision":"pending","reason":"kernel must recompute"}' \
  --run-id RUN_ID --attempt-id ATTEMPT_ID --scope skill
```

结构请求的 `subject.program` 必须是非空字符串；可选 `context.required_blocks` 覆盖最小块集合，
`context.control_required=true` 时还要求流程包含条件或迭代标记。语义请求必须同时提供
`subject.source_prompt`、`subject.program` 和 `context.rubric_version=1.0`。两个验证器都返回标准
`pass`/`fail`/`uncertain`/`error` 结果及结构化 findings；超大、非法 JSON、缺失证据或模型不可用
不得由调用方猜测为通过。将两个结果组成 JSON 数组传给 `bsk verification`；`--gate-json` 只是
候选值，Kernel 会依据整批原始结果重算并写入最终 Gate。验证结果或 Gate 缺失时，状态机不得离开
`schema-valid`。

结果和 Gate 应写入任务事件账本。`unchecked`、`uncertain` 或执行错误均不能被翻译成
`reviewed`，而应保留原始结果并走人工复核或失败路径。
