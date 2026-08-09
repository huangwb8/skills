# Awesome Code

这个 skill 是复杂开发任务的协调器：脚本先收集可用 Agent 摘要、配置约束与 required route 门禁，再由 AI 自主决定是否使用子代理、使用哪些子代理，以及采用单任务、顺序还是并行策略推进。如果配置中的 required route agent 缺失，它会先阻塞而不是假装能继续开工。

## 用法

### 最推荐用法

```text
请使用 awesome-code skill 辅助规划、优化。所有问题都要解决。如果工作时有疑问，或者有更好的方案，自己选个最优方案优化，不要问我。不要破坏其它功能。要保证最终成品能正常、稳定、高效地工作。
输入：当前项目与任务目标
输出：Agent 选择依据、`dispatch_gate` 门禁、执行策略，以及落地后的改进结果
```

### 进阶用法

```text
请使用 awesome-code skill 协调处理这个复杂开发任务。
输入：当前项目、目标需求和重点风险
输出：任务拆解、自主选择的 Agent 分工、执行顺序和最终验证结果
另外，还有下列参数约束：
- 优先级：先修阻塞问题，再补测试和文档
- 协作方式：能并行的任务尽量并行
- 沟通方式：默认自主推进，只有明显高风险破坏性决策再停下来确认
```

## 能做什么

- 先收集可用 Agent 摘要和配置约束，再由 AI 自主规划，而不是用硬编码关键词替 AI 做语义判断。
- 小任务可直接 `single-pass`，避免把简单修改升级成多代理编排。
- 对宽泛且缺少验收标准的高风险任务，AI 先澄清目标、边界和成功标准，或记录保守假设。
- 执行前确定最小变更范围、成功标准和验证计划，让改动范围与验证方式可追溯。
- 若配置中的 required route agent 缺失、禁用或不可调度，会通过 `dispatch_gate` 阻塞并说明原因。
- 根据任务依赖关系自主选择 `focused-agent`、`sequential` 或 `parallel` 协调策略。
- 适合复杂 bug 修复、大规模重构、多模块改造、前后端协作和多步骤验证。
- 对 UI/前端任务会优先考虑设计方向、信息层级和实现策略。
- 不适合非常简单的单文件小改或纯概念问答。

## 使用示例

### 示例 1：复杂重构

```text
请使用 awesome-code skill 协调重构这个项目。
输入：当前代码库，目标是减少重复逻辑并补齐验证
输出：任务拆解、Agent 选择依据和最终改动结果
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

- `planning_mode`：当前为 `autonomous`。
- `available_agents`：从 `agents/*/SKILL.md` 读取的可用 Agent 摘要。
- `config_constraints`：启用 Agent、required routes、TDD 与代码审查阈值等配置约束。
- `dispatch_gate`：说明当前是否可继续、为什么阻塞、缺哪些 agent。
- `dispatch_guidance`：AI 自主规划时应遵守的最小变更边界与调度留痕规则。

## 配置

- 配置文件：`awesome-code/config.yaml`
- 默认启用 14 个专业代理。
- 最大并行任务数：`5`
- 任务优先级策略：`priority`
- 关键配置节：
  - `multi_agent.enabled_agents`
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

### 第二步：收集规划上下文并读取门禁结果

```bash
AGENT_COORDINATOR=$(python3 awesome-code/scripts/get_path.py | python3 -c 'import json,sys; print(json.load(sys.stdin)["executable_scripts"]["agent_coordinator"])')
python3 "$AGENT_COORDINATOR" \
  "fix login bug and add regression tests"
```

重点看这些字段：

- `planning_mode`
- `available_agents`
- `config_constraints`
- `dispatch_gate`
- `dispatch_guidance`

如果 `dispatch_gate.can_proceed` 是 `false`，先补齐 required route agent，再继续实现；如果门禁通过，由 AI 根据 Agent 摘要和任务描述自主决定分工。

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

A：脚本不再用关键词直接强制当前任务分派；它会暴露配置中的 required routes 和可用 Agent，AI 判断 route 是否适用。若适用，该 route 的 Agent 就是 required。

### Q：为什么有时会被阻塞？

A：因为 `dispatch_gate` 检测到 required agent 当前不可用。阻塞不是失败，而是防止系统在缺少关键专长时继续硬做，最后产出看似完整、实则没过质量门禁的结果。

### Q：README 里为什么不先展开 14 个代理的细节？

A：因为真正的上手路径不是“背代理清单”，而是“知道怎么触发、怎么让它分工、怎么收尾”。代理列表是支撑，不是入口。

### Q：你这里说“不要问我”，是不是永远不确认？

A：不是。更稳妥的理解是“默认自主推进，不让常规疑问阻塞任务”；但遇到明显高风险、破坏性或不可逆决策时，仍应停下来确认。

### Q：为什么脚本方式必须先跑 `get_path.py`？

A：因为安装位置可能不同，先动态拿到真实路径，能避免把 `~/.claude/skills/` 或 `~/.codex/skills/` 写死。
