# Awesome Code

这个 skill 是复杂开发任务的协调器：它会先分析任务，再把专业代理分成 `required / preferred / optional` 三层，再决定用单任务、顺序还是并行策略推进；如果命中了 required 路由但 agent 缺失，它会先阻塞而不是假装能继续开工。如果只是一个很小的改动，通常不需要动用它。

## 用法

### 最推荐用法

```text
请使用 awesome-code skill 辅助规划、优化。所有问题都要解决。如果工作时有疑问，或者有更好的方案，自己选个最优方案优化，不要问我。不要破坏其它功能。要保证最终成品能正常、稳定、高效地工作。
输入：当前项目与任务目标
输出：分层代理分工、`dispatch_gate` 门禁、执行策略，以及落地后的改进结果
```

### 进阶用法

```text
请使用 awesome-code skill 协调处理这个复杂开发任务。
输入：当前项目、目标需求和重点风险
输出：任务拆解、`required_agents` / `preferred_agents` / `optional_agents`、执行顺序和最终验证结果
另外，还有下列参数约束：
- 优先级：先修阻塞问题，再补测试和文档
- 协作方式：能并行的任务尽量并行
- 沟通方式：默认自主推进，只有明显高风险破坏性决策再停下来确认
```

## 能做什么

- 先分析任务，再匹配合适的子代理，而不是一上来盲目开工。
- 会把子代理分成 `required / preferred / optional`，避免“看起来推荐了，但真正需要时没人兜底”。
- 命中安全、系统化调试、TDD/test-first、明确 UI 重设计等高专长路线时，会强制调对应 agent。
- 若 required agent 缺失、禁用或不可调度，会通过 `dispatch_gate` 阻塞并说明原因。
- 根据任务依赖关系自动选择 `single`、`sequential` 或 `parallel` 协调策略。
- 适合复杂 bug 修复、大规模重构、多模块改造、前后端协作和多步骤验证。
- 对 UI/前端任务会优先考虑设计方向、信息层级和实现策略。
- 不适合非常简单的单文件小改或纯概念问答。

## 使用示例

### 示例 1：复杂重构

```text
请使用 awesome-code skill 协调重构这个项目。
输入：当前代码库，目标是减少重复逻辑并补齐验证
输出：任务拆解、代理分层和最终改动结果
```

### 示例 2：系统化调试

```text
请使用 awesome-code skill 处理这个 bug。
输入：当前项目与 bug 描述
输出：根因分析、修复步骤、验证结果
另外，还有下列参数约束：
- 优先使用系统化调试
- 修复后补测试
```

### 示例 3：多代理并行推进

```text
请使用 awesome-code skill 处理这个复杂任务。
输入：当前项目，目标是同时优化文档、测试和脚本稳定性
输出：代理分工、并行策略和整合后的结果
```

### 示例 4：前端或体验优化

```text
请使用 awesome-code skill 优化这个前端任务。
输入：当前项目，目标是重做 SaaS 仪表盘体验
输出：设计方向、实现策略和最终代码改进
```

## 输出

- `required_agents`：必须实际调用的 agent；缺失时不得继续执行。
- `preferred_agents`：强烈建议调用；缺失时可以降级，但应说明影响。
- `optional_agents`：补充覆盖面或效率，不构成门禁。
- `dispatch_gate`：说明当前是否可继续、为什么阻塞、缺哪些 agent。
- `dispatch_manifest`：本轮应调度哪些 agent 的清单；执行后可补 `dispatch_receipts` 做留痕。
- 协调策略说明：单任务、顺序执行、并行推进，或 `blocked`。

## 配置

- 配置文件：`awesome-code/config.yaml`
- 默认启用 14 个专业代理。
- 最大并行任务数：`5`
- 任务优先级策略：`priority`
- 关键配置节：
  - `multi_agent.enabled_agents`
  - `multi_agent.agent_priorities`
  - `multi_agent.frontend_design_keywords`
  - `multi_agent.dispatch_policy`
  - `tdd`
  - `code_review`
  - `git`

## 备选用法（脚本/硬编码）

如果你想先走确定性分析，再由 AI 决定具体代理协作方式，脚本入口是最稳的。

### 第一步：动态发现安装路径

```bash
python3 awesome-code/scripts/get_path.py
```

### 第二步：分析任务并读取门禁结果

```bash
AGENT_COORDINATOR=$(python3 awesome-code/scripts/get_path.py | python3 -c 'import json,sys; print(json.load(sys.stdin)["executable_scripts"]["agent_coordinator"])')
python3 "$AGENT_COORDINATOR" \
  "fix login bug and add regression tests"
```

重点看这些字段：

- `required_agents`
- `preferred_agents`
- `optional_agents`
- `dispatch_gate`
- `dispatch_manifest`

如果 `dispatch_gate.can_proceed` 是 `false`，先补齐 required agent，再继续实现。

### 常用辅助脚本

```bash
python3 awesome-code/scripts/test_runner.py
python3 awesome-code/scripts/code_analyzer.py --path .
python3 awesome-code/scripts/create_test_session.py --skill-root .
```

## 常见问题

### Q：是不是所有任务都该用 `awesome-code`？

A：不是。它更适合复杂任务、跨模块任务和需要明确协作策略的任务。简单任务直接做通常更快。

### Q：为什么有些任务会强制调 agent？

A：因为这类任务一旦不走专长代理，错误率会明显升高。比如安全漏洞、根因排查、TDD/test-first、明确 UI 重设计，都属于“少了对应 agent 就容易做错”的路线，所以会进入 `required_agents`。

### Q：为什么有时会被阻塞？

A：因为 `dispatch_gate` 检测到 required agent 当前不可用。阻塞不是失败，而是防止系统在缺少关键专长时继续硬做，最后产出看似完整、实则没过质量门禁的结果。

### Q：README 里为什么不先展开 14 个代理的细节？

A：因为真正的上手路径不是“背代理清单”，而是“知道怎么触发、怎么让它分工、怎么收尾”。代理列表是支撑，不是入口。

### Q：你这里说“不要问我”，是不是永远不确认？

A：不是。更稳妥的理解是“默认自主推进，不让常规疑问阻塞任务”；但遇到明显高风险、破坏性或不可逆决策时，仍应停下来确认。

### Q：为什么脚本方式必须先跑 `get_path.py`？

A：因为安装位置可能不同，先动态拿到真实路径，能避免把 `~/.claude/skills/` 或 `~/.codex/skills/` 写死。
