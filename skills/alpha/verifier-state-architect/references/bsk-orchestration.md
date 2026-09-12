# Skill 自有 BSK 编排入口

## 何时强制采用

目标 Skill 明确同时使用 BSK 领域 State 和至少一个 `required: true` Verifier 时，必须实现一个 Skill 自有的单一编排入口。它是 Agent 执行受控 action 的正常入口；不得只生成 Pack、`runtime` 声明或一组供 Agent 自由拼接的 BSK 命令。

仅使用 State、仅使用 Verifier、没有 required Verifier，或删除影响测试结论为不接入时不强制创建，避免占位脚本。BSK 不会阻止完全绕过它的宿主，因此目标 `SKILL.md` 的 `## 控制` 必须明确：直接调用底层 BSK 子步骤只用于入口内部、诊断或恢复，不能作为正常业务路径。

## 声明与入口

在目标 `config.yaml.runtime` 声明 Skill 自有元数据；BSK 不解释 `orchestration`，由目标入口和 `verifier-state-architect` 的检查器使用：

```yaml
runtime:
  orchestration:
    entrypoint: scripts/control.py
    actions:
      publish-report:
        current_state: org.example.report.checking
        target_state: org.example.report.delivering
```

- `entrypoint` 必须是 Skill 内 `scripts/` 下真实存在的相对路径，不能含绝对路径、`..`、反斜杠或符号链接逃逸。
- `actions` 必须非空；每个 action 映射到 `runtime.states` 中声明的 canonical `current_state` 和 `target_state`。领域映射留在目标 Skill，不写入 BSK。
- required Verifier 必须在运行时从 `runtime.verifiers` 的 `required: true` 项解析，不在 `orchestration` 或脚本中维护第二份清单。
- 入口对 Agent 暴露一条简单命令，至少接收 action、任务根、请求/证据引用及 `run_id`/`attempt_id`。敏感或大体积输入使用受限文件/stdin，不放入命令行或日志。
- `runtime.orchestration` 只用于这个组合场景；不适用时不保留孤立声明或占位入口。

命令名可按技术栈调整，但每个目标 Skill 只公开一种正常形态，例如：

```bash
python3 scripts/control.py publish-report \
  --task-root .bensz-api/task-YYYYMMDD-HHMM-demo \
  --request-file request.json --run-id run-1 --attempt-id attempt-1
```

正常回执至少提供稳定的 `protocol`、`action`、`run_id`、`attempt_id`、`previous_state`、`target_state`、`current_state`、`required_results`、`gate`、`transition` 与 `status` 字段；失败回执提供稳定 `reason_code` 和 `recovery`。具体协议名由目标 Skill 版本化，不能把自由文本当机器契约。

## 不可省略的执行顺序

入口必须完成并测试以下闭环；不能把任一步交给 Agent 临时补做：

1. 解析 action → current/target State 映射；未知 action 立即拒绝。
2. 用目标 `runtime.kernel` 精确版本的 BSK 公共 CLI/Python API 读取当前 Skill State、版本和运行绑定；不直接猜测或信任调用方自报状态。调用 CLI 时使用参数数组和结构化 stdin/文件，禁止 `shell=True`、shell 字符串拼接或把未验证输入插入命令。
3. 核对当前 State 等于 action 声明的 `current_state`，再统一构造 Verifier 请求；请求绑定同一 subject/context/evidence、`run_id`、`attempt_id` 和必要证据引用。
4. 从 Skill 声明解析并调用全部 required Verifier；advisory 可按目标策略运行，但不能掩盖 required 缺失、失败或未完成。
5. 由 BSK 对本次完整结果生成并记录 Gate；入口不得自行伪造 Gate、把模型自评当 `pass`，或复用旧 State/旧 attempt 的结果。
6. 仅当 Gate 明确允许继续、全部 required 结果通过且身份/结果引用绑定完整时，调用 BSK transition 到 `target_state`；其它已知或未知结果全部 fail-closed。
7. 严格校验每次 BSK 返回的协议、操作、状态/判定枚举、canonical ID/version、run/attempt、结果集合、Gate `result_refs`、transition 回执和新快照。只看退出码、文件存在或自然语言消息不得放行。

入口最后返回一个稳定、最小的结构化回执，明确 action、原/目标/当前 State、required 结果、Gate、transition、运行身份和恢复原因；不要回显原始私密上下文。

## 失败与恢复

- 缺声明/证据、版本不匹配、非法路径、超时、`uncertain`、`unchecked`、错绑、未知枚举、Gate 非放行或 transition 回执不一致时，不执行后续阶段或正式交付。
- 依据 BSK 稳定字段和原因码选择重试、补证据、人工复核或新 attempt；不解析异常文本作为调用契约。
- 幂等键、事件与快照必须绑定当前 action/run/attempt；恢复后不能复用旧 Gate。若目标 action 还需阶段内单次授权，再按实际 BSK 版本接入 action preflight/consume。
- 未实际执行入口行为测试时，只能报告结构已接入、执行 `unchecked`。

## 最小验收

除 `check_integration.py` 的声明/路径检查外，至少验证：成功路径；未知 action；当前 State 不匹配；required 缺失、失败、未完成或错版本；Gate 非放行或错绑；transition 拒绝；返回目标 State/版本/快照不一致；重试不复用旧 run/attempt。测试应证明业务入口无法在这些失败下继续，而不只是断言某函数被调用。
