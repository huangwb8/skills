# parallel-vibe

本 README 面向使用者：告诉你什么时候用默认智能模式，什么时候切到脚本 runner 的代码模式。执行规范在 `SKILL.md`，默认配置在 `config.yaml`。

## 这是什么

`parallel-vibe` 用来让多个独立 thread 围绕同一条 Vibe Coding 指令给出不同视角，再由主 agent 汇总共识、分歧和推荐路线。

默认推荐 **智能模式**：直接使用宿主工具的原生 subagent / 独立上下文能力。两种模式都使用同一套 `.parallel_vibe/<project_id>/` 目录、`@main/plan.json`、thread `workspace/`、`RESULT.md` 和 `runner.log`；区别只在 thread 的底层执行机制。

只有当你需要脚本 runner、`plan-file`、`resume`、真实退出码、跨 `codex` / `claude` / `shell` runner，或下游脚本可复跑批处理时，才切到 **代码模式**。

## 推荐用法：智能模式

普通多 agent 探索、审查、优化和方案对比，直接用 Prompt 触发：

```text
请使用 parallel-vibe 的智能模式，让 4 个独立 subagent 分别审查这个方案。
每个 thread 都要给出结论、依据、建议、风险和验证步骤。
最后请综合共识、主要分歧和推荐路线。
```

实现型任务建议这样说，避免多个 subagent 同时改同一份 checkout：

```text
请使用 parallel-vibe 的智能模式，让 3 个独立 subagent 给出不同实现方案和 patch 建议。
暂时不要让多个 subagent 并行写同一个工作区。
最后由主 agent 选择最小可行路线并给出验证命令。
```

智能模式适合：

- 多个独立 agent 审查同一份代码、PR、文档或方案
- 让不同角色给出保守方案、激进方案、测试边界、风险审查
- 研究假设、产品方案、重构方向的多视角打磨
- 需要固定 `.parallel_vibe/` 目录，但希望由宿主原生 subagent 完成独立思考的交互式任务

## 什么时候用代码模式

代码模式保留脚本 runner 能力，适合可复跑批处理编排：

- 你要用 `--plan-file`、`--project-id`、`--resume`、`--dry-run`
- 你需要跨 `codex` / `claude` / `shell` runner 批量执行
- 下游 skill 或脚本要读取机器可读产物
- 你需要真实进程退出码和 runner 失败日志来驱动自动化

代码模式命令：

```bash
python3 parallel-vibe/scripts/parallel_vibe.py \
  --prompt "<用户指令原文>" \
  --n 5
```

只生成计划，不执行 threads：

```bash
python3 parallel-vibe/scripts/parallel_vibe.py \
  --prompt "<用户指令原文>" \
  --n 3 \
  --plan-only \
  --no-synthesize
```

使用自定义计划：

```bash
python3 parallel-vibe/scripts/parallel_vibe.py \
  --plan-file /path/to/plan.json \
  --src-dir . \
  --out-dir .
```

系统级安装时可用：

```bash
python3 ~/.codex/skills/parallel-vibe/scripts/parallel_vibe.py --prompt "<用户指令原文>"
# 或
python3 ~/.claude/skills/parallel-vibe/scripts/parallel_vibe.py --prompt "<用户指令原文>"
```

## 两种模式的区别

| 维度 | 智能模式（默认） | 代码模式 |
|------|------------------|----------|
| 默认用途 | 多 agent 独立思考、审查、对比方案 | 可追溯批处理和脚本集成 |
| 执行方式 | 宿主原生 subagent / 独立上下文 | `scripts/parallel_vibe.py` |
| 落盘契约 | 固定 `.parallel_vibe/` | 固定 `.parallel_vibe/` |
| 关键产物 | `plan.json`、`RESULT.md`、`runner.log`、`summary.md` | `plan.json`、`RESULT.md`、`runner.log`、`summary.md` |
| 文件隔离 | 使用相同 thread `workspace/`；是否能绑定 cwd 取决于宿主 subagent 能力 | 每个 thread 复制独立 workspace，并以 `cwd=workspace/` 启动 runner |
| 适合下游自动化 | 一般不适合 | 适合 |

最容易误解的一点：目录一致不等于底层隔离机制一致。智能模式的独立性来自宿主 subagent / 独立上下文；代码模式的独立性来自脚本复制 workspace 并启动 CLI runner。需要并行实改文件时，确保每个执行单元只写自己的 `workspace/`；如果宿主不能绑定 subagent 的工作目录，使用代码模式或让智能模式只输出 patch 建议。

## 代码模式参数语义

| 名称 | 你可以怎样理解 | 直接影响什么 |
|------|----------------|-------------|
| `thread` 数 | 你要拆成多少条独立尝试路径 | 独立工作区数量、thread 级结果数量 |
| `max_parallel` | 允许同时推进多少个 `thread` | 同一时刻的并发执行数量 |
| `synthesize` | threads 结束后是否再做一次统一汇总 | 是否自动生成最终结论 |

核心关系：

- 1 个 `thread` = 1 份独立工作区
- `thread` 数决定总共要尝试多少条路径
- `max_parallel` 决定这些路径会同时推进几条
- `synthesize` 在全部 thread 结束后额外生成统一汇总，不会提高 thread 阶段并发峰值

## 输出怎么看

执行后先看：

- `.parallel_vibe/<project_id>/@main/summary.md`

某个独立尝试路径：

- `.parallel_vibe/<project_id>/<thread_id>/RESULT.md`
- `.parallel_vibe/<project_id>/<thread_id>/workspace/`

排查失败：

- `.parallel_vibe/<project_id>/<thread_id>/runner.log`

## FAQ

### Q：默认会创建 `.parallel_vibe/` 吗？

会。智能模式和代码模式都应该使用 `.parallel_vibe/<project_id>/`。固定目录和日志不再是代码模式专属；只有需要脚本 runner、`plan-file`、`resume` 或真实退出码时才切到代码模式。

### Q：我设了 8 个 thread，是不是就会同时跑 8 个进程？

不一定。代码模式默认串行；只有开启并行并设置 `max_parallel` 后，才会同时推进多条 thread，峰值为 `min(thread 数, max_parallel)`。

### Q：什么时候应该少开几个 thread？

仓库很大、复制工作区成本高、模型调用成本敏感、等待时间敏感时，先减少 thread 数，必要时保持串行。

---

版本信息见 `config.yaml` 中的 `skill_info.version`。
