# 状态机契约

状态机是本 Skill 的强制运行治理层，不替代 Markdown 检查流程。每次执行都必须通过 kernel 命令读取契约、执行合法转移并保存元状态快照；不得自行猜测状态含义、伪造快照或跳过状态机。

## 状态包

Skill 根目录的 [`state-machine.json`](../state-machine.json) 声明状态根和状态列表。`bensz.workspace.ready` 是强制初始状态，Skill 阶段按顺序为：

`bensz.validate-md-ref.input-ready` → `bensz.validate-md-ref.checking` → `bensz.validate-md-ref.reported`

各状态的入口条件、不变量和允许转移分别记录在 [`input-ready`](../states/input-ready/STATE.md)、[`checking`](../states/checking/STATE.md) 和 [`reported`](../states/reported/STATE.md) 的 `STATE.md` 中。`input-ready` 只接受现有且可读的 Markdown 文件；`checking` 要求保留规范化验证结果；`reported` 要求向用户披露不确定性并保持原文档不变。

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
