# 状态机契约

状态机是本 Skill 的运行治理层，不替代 Prompt Program 的翻译规则。每次执行都**必须**按
`config.yaml:runtime` 声明，通过 Kernel 读取状态契约、执行合法转移并保存元状态快照；不允许
以“任务简单”或“只需输出文本”为由跳过。

状态顺序为：

`bensz.workspace.ready` → `bensz.prompt-programming.draft` →
`bensz.prompt-programming.schema-valid` → `bensz.prompt-programming.reviewed` →
`bensz.prompt-programming.published` →
`bensz.workspace.closed`

翻译失败可从 `draft` 进入 `bensz.runtime.failed`；验证 Gate 不允许时，从
`schema-valid` 进入 `bensz.runtime.failed`，不得把失败结果推进到 `reviewed`。

## Kernel 操作

```bash
bsk state list --root SKILL_ROOT/references/states
bsk state describe bensz.prompt-programming.draft --root SKILL_ROOT/references/states
bsk state transition TASK_ROOT prompt-programming bensz.prompt-programming.draft \
  --root SKILL_ROOT/references/states --run-id RUN_ID --attempt-id ATTEMPT_ID \
  --context-json '{"prompt":"..."}'
```

后续转移按清单顺序执行。每次成功转移都**必须**检查标准 `bensz-meta-state-v1` 回执，并将
快照保存在任务工作区 Skill 的 `log/meta-state.json`。`schema-valid` 离开前，事件账本必须
包含同一 `run_id/attempt_id` 下的 `verification.result` 与 `verification.gate`；
`reviewed` 离开前还必须有 allowing Gate。任何命令失败、回执缺失或身份不一致都走
`bensz.runtime.failed`，不得直接返回翻译结果。
