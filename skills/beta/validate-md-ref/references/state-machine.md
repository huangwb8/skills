# 状态机契约

状态机是本 Skill 的强制运行治理层，不替代 Markdown 检查流程。每次执行都必须通过 kernel 命令读取契约、执行合法转移并保存元状态快照；不得自行猜测状态含义、伪造快照或跳过状态机。

## 状态包

Skill 根目录的 [`config.yaml`](../config.yaml) 的 `runtime` 节声明状态根和状态列表。旧版
[`state-machine.json`](../state-machine.json) 仅作为兼容读取入口。`bensz.workspace.ready` 是强制初始状态，Skill 阶段按顺序为：

`references/states/index.json` 是当前状态包的目录清单，采用 kernel 的
`bensz-pack-index-v1` 协议；它集中声明 canonical ID、版本、alias 和入口脚本，
`STATE.md` 保留状态契约正文。没有索引的旧目录仍由 kernel 兼容读取。

`bensz.validate-md-ref.input-ready` → `bensz.validate-md-ref.checking` → `bensz.validate-md-ref.reported`

各状态的入口条件、不变量和允许转移分别记录在 [`input-ready`](states/input-ready/STATE.md)、[`checking`](states/checking/STATE.md) 和 [`reported`](states/reported/STATE.md) 的 `STATE.md` 中。`input-ready` 只接受现有且可读的 Markdown 文件；`checking` 要求保留规范化验证结果；`reported` 要求向用户披露不确定性并保持原文档不变。

其中 `checking` 的 `verifier-result-recorded` 是 Kernel 可执行的不变量：离开该状态前，任务级 `events.ndjson` 必须同时存在 `verification.result` 和 `verification.gate`。其余自然语言不变量仍由本 Skill 的 helper 或人工复核负责。

## 必经 Kernel 操作

```bash
bsk workspace status TASK_ROOT
bsk state list --skill-root SKILL_ROOT
bsk state describe bensz.validate-md-ref.input-ready --skill-root SKILL_ROOT
bsk state transition TASK_ROOT validate-md-ref bensz.validate-md-ref.input-ready \
  --skill-root SKILL_ROOT --context-json '{"document":"DOCUMENT.md"}'
bsk state transition TASK_ROOT validate-md-ref bensz.validate-md-ref.checking \
  --skill-root SKILL_ROOT --context-json '{"document":"DOCUMENT.md"}'
bsk state transition TASK_ROOT validate-md-ref bensz.validate-md-ref.reported \
  --skill-root SKILL_ROOT --context-json '{"document":"DOCUMENT.md"}'
```

按 `input-ready`、`checking`、`reported` 顺序执行。每次转移成功后检查返回的标准 `bensz-meta-state-v1` JSON；状态快照写入任务工作区中 Skill 的 `log/meta-state.json`。任一转移失败即停止，不得把源 Markdown 复制进工作区，也不得在状态转移中写回原文档。
