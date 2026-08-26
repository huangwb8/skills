# 状态机契约

状态机是本 Skill 的可选运行治理层，不替代 Markdown 检查流程。只有需要记录阶段、转移或元状态快照时才启用；启用后必须通过 kernel 命令读取契约并执行合法转移，不要自行猜测状态含义或伪造快照。

## 状态包

Skill 根目录的 [`state-machine.json`](../state-machine.json) 声明状态根和状态列表。`workspace.ready` 是强制初始状态，Skill 阶段按顺序为：

`validate-md-ref.input-ready` → `validate-md-ref.checking` → `validate-md-ref.reported`

各状态的入口条件、不变量和允许转移分别记录在 [`input-ready`](../states/input-ready/STATE.md)、[`checking`](../states/checking/STATE.md) 和 [`reported`](../states/reported/STATE.md) 的 `STATE.md` 中。`input-ready` 只接受现有且可读的 Markdown 文件；`checking` 要求保留规范化验证结果；`reported` 要求向用户披露不确定性并保持原文档不变。

## Kernel 操作

```bash
bsk state list --skill-root .
bsk state describe validate-md-ref.input-ready --skill-root .
bsk state transition TASK_ROOT validate-md-ref validate-md-ref.input-ready \
  --skill-root . --context-json '{"document":"DOCUMENT.md"}'
```

命令返回标准 `bensz-meta-state-v1` JSON。状态快照写入任务工作区中 Skill 的 `log/meta-state.json`；不得把源 Markdown 复制进工作区，也不得在状态转移中写回原文档。
