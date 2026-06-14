# parallel-vibe 智能模式协议

智能模式是 `parallel-vibe` 的默认交互路径。它依赖宿主工具的原生 subagent / 独立上下文能力，让多个 thread 独立分析同一任务，再由主 agent 汇总。智能模式和代码模式共享同一套目录契约，区别只在 thread 的底层执行机制。

## 适用边界

使用智能模式：

- 多个独立 agent 审查同一份代码、PR、文档、方案或研究假设
- 目标是方案探索、风险评估、文档优化、测试边界补充或路线对比
- 用户要求 `.parallel_vibe/`、`plan.json`、`RESULT.md`、`runner.log` 等固定目录产物，但不要求脚本 runner 或真实退出码
- 宿主工具明确支持 subagent 或等价独立上下文能力

切到代码模式：

- 用户要求脚本模式、CLI runner、`--plan-file`、`--resume`、`--dry-run`、真实退出码或可复跑批处理
- 需要跨 `codex` / `claude` / `shell` runner 批量执行
- 宿主没有可用 subagent 能力
- 多个 agent 需要实际并行修改文件，且宿主不能把 subagent 绑定到各自 `workspace/`

## 共享目录契约

智能模式必须和代码模式使用同一套目录管理：

```text
.parallel_vibe/<project_id>/
  project.json
  @main/
    plan.json
    plan.md
    summary.md
  <thread_id>/
    workspace/
      RESULT.md
    RESULT.md
    runner.log
    prompt.txt
    thread.json
    done.json
    exit_code.txt
```

执行含义：

- `@main/plan.json` / `@main/plan.md`：记录 thread 拆分、角色、输入 prompt 和执行策略。
- `<thread_id>/workspace/`：该 thread 的专属工作目录；智能模式下也要把该路径作为 subagent 的产物边界。
- `<thread_id>/workspace/RESULT.md`：thread 首选结果产物。
- `<thread_id>/RESULT.md`：供主 agent 汇总读取的规范副本；如果 subagent 不能直接落盘，由主 agent 把 subagent 返回内容写入此文件。
- `<thread_id>/runner.log`：代码模式保存 CLI stdout/stderr；智能模式保存宿主 subagent 返回内容、摘要或“宿主不暴露 transcript”的说明。
- `<thread_id>/done.json` / `exit_code.txt`：代码模式保存真实进程状态；智能模式成功用 `0`，失败或未完成用 `1`，并在 `done.json` 标明 `mode: smart`。

## Thread 规划

主 agent 先规划 `n` 个 thread。用户未指定数量时：

- 轻量审查：2-3 个 thread
- 中等方案对比：3-5 个 thread
- 高风险或多维审查：5-7 个 thread

常见角色：

- `conservative_approach`：保守、最小改动路线
- `ambitious_approach`：更彻底的重构或替代路线
- `risk_review`：bug、回归、安全、边界条件
- `test_strategy`：验证路径、测试缺口、可复现命令
- `ux_or_docs_review`：用户体验、文档、可维护性

## Subagent 输出 schema

每个 subagent 使用独立上下文，不读取其他 thread 的结果，并优先把以下 schema 写入自己的 `<thread_id>/workspace/RESULT.md`。如果宿主不允许 subagent 直接写文件，主 agent 用同一内容兜底写入 `<thread_id>/RESULT.md`：

```markdown
## Thread Result

- thread_id:
- role:
- conclusion:
- evidence:
- recommended_changes:
- risks:
- verification:
```

字段要求：

- `conclusion`：一句话结论，说明该 thread 选择或反对什么。
- `evidence`：引用本地文件、命令输出、用户材料或明确推理依据。
- `recommended_changes`：可执行建议。实现型任务默认输出 patch 建议，不直接并行写同一工作区。
- `risks`：仍未解决的不确定性、潜在回归或依赖假设。
- `verification`：最小验证命令或人工检查点。

## 主 agent 汇总 schema

主 agent 读取各 thread 的 `RESULT.md`，写入 `.parallel_vibe/<project_id>/@main/summary.md`，并在面向用户的最终输出包含：

```markdown
运行模式：智能模式
project 目录：.parallel_vibe/<project_id>/
thread 数与策略：

## Thread 摘要

- <thread_id> / <role>：<一句话结论>

## 综合结论

- 推荐路线：
- 共识：
- 主要分歧：
- 风险：

## 验证步骤

- <命令或检查点>
```

## 串行与并行策略

- 分析、审查、方案对比类任务可以并行启动 subagent。
- 依赖前一轮结论的任务应串行：先让一组 subagent 审查，再由主 agent 生成下一轮输入。
- 实现型任务先给每个 thread 分配自己的 `workspace/`。只有在宿主能把 subagent 的读写边界绑定到该 `workspace/` 时，才让多个 subagent 并行实改；否则让 subagent 输出方案或 patch 建议，再由主 agent 统一落地。

## 文件系统边界

共享目录契约不等于强安全隔离。

智能模式保证各 subagent 在上下文上独立思考，并要求它们把产物写入同一套 thread `workspace/` 结构；但是否拥有真实独立 cwd、独立 Git checkout 或安全沙箱，取决于宿主能力。需要并行写文件时，必须满足其一：

- 宿主提供独立 worktree / workspace；
- 使用代码模式复制独立 workspace；
- 改为只输出方案、diff 或 patch 建议，由主 agent 单点落地。

不要把智能模式描述成脚本级可复跑批处理系统；需要真实进程日志、失败退出码和 CLI runner 复跑时，使用代码模式。
