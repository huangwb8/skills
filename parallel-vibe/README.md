# parallel-vibe — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `parallel-vibe` skill。
执行规范见 `SKILL.md`；默认参数见 `config.yaml`。

## 这是什么

把同一条用户指令拆成多个独立 thread（任务视角），在多个**独立工作区**中执行，最后统一落盘并汇总结果。

**核心价值**：
- 每个 thread 启动独立 runner 进程（如 `codex exec` / `claude -p`）
- 独立工作区隔离，避免交叉污染
- 默认串行执行（省资源、减少 API 限流）
- 支持自定义 runner / 模型 / 提示词

**适用场景**：
- 多方案并行尝试，对比不同实现路径
- 同一任务用不同模型/角色独立执行
- 多工作区隔离开发

**不适用场景**：
- 只是想并行跑 shell 命令/单元测试/下载任务（应直接用并发工具或 CI）
- 没有明确"多工作区并行尝试/多方案对比"的意图
- 要求强安全隔离或处理高度敏感数据（应使用容器/沙箱方案）

## 快速开始

### 最推荐：默认 5 threads

```
用 parallel-vibe 把这个功能实现出来，并给出最小验证步骤
```

或在目标项目根目录执行：

```bash
python3 parallel-vibe/scripts/parallel_vibe.py --prompt "把这个功能实现出来，并给出最小验证步骤"
```

### 查看结果

执行后结果目录会打印到 stdout，例如：

```
.parallel_vibe/<project_id>/
```

**优先查看**：`.parallel_vibe/<project_id>/@main/summary.md`

## 使用场景

| 你的需求 | 推荐用法 | 说明 |
|---------|---------|------|
| 默认多方案尝试 | 不指定参数 | 自动拆分为规划/实现/测试/审查等 5 个 thread |
| 用户明确要求并行 | `--parallel --max-parallel 3` | 同时运行多个 thread |
| 先生成计划再调整 | `--plan-only` | 只生成 plan.json，不执行 |
| 精细控制每个 thread | 编辑 plan.json 后 `--resume` | 自定义 runner/模型/提示词 |
| 避免污染当前目录 | `--src-dir` / `--out-dir` | 指定源目录和输出根目录 |

## 推荐用法

### 默认 5 threads（推荐）

```bash
python3 parallel-vibe/scripts/parallel_vibe.py --prompt "..."
```

默认按 5 个 thread 生成"规划/实现/实现B/测试/审查"拆分计划并执行。

### 用户明确要求并行时再开启

```bash
python3 parallel-vibe/scripts/parallel_vibe.py --prompt "..." --parallel --max-parallel 3
```

说明：默认串行执行（避免资源争抢和 API 限流），只有用户明确要求时才并行。

### 先生成计划，再手动调整

```bash
python3 parallel-vibe/scripts/parallel_vibe.py --prompt "..." --plan-only
```

然后编辑：

```
.parallel_vibe/<project_id>/@main/plan.json
```

再用同一个 `project_id` 续跑（复用 project 目录；每次运行仍会重建各 thread/workspace）：

```bash
python3 parallel-vibe/scripts/parallel_vibe.py --prompt "..." --project-id <32位md5> --resume
```

### 使用外部计划文件

```bash
python3 parallel-vibe/scripts/parallel_vibe.py --plan-file /path/to/plan.json --src-dir . --out-dir .
```

### 自定义 src/out（避免污染当前目录）

```bash
python3 parallel-vibe/scripts/parallel_vibe.py \
  --prompt "..." \
  --src-dir /path/to/your/project \
  --out-dir /path/to/output/root
```

## 产物结构

`.parallel_vibe/{project_id}/` 结构：

```
.parallel_vibe/{project_id}/
├── 001/
│   ├── workspace/           # thread 001 的独立工作区（从 --src-dir 复制）
│   ├── prompt.txt           # 追加"软隔离护栏"后的完整提示词
│   ├── thread.json          # 该 thread 的计划元数据（runner/model/title 等）
│   ├── runner.log           # runner 的 stdout/stderr 合并日志
│   ├── RESULT.md            # 从 workspace/RESULT.md 提取的结果摘要
│   ├── exit_code.txt
│   └── done.json
├── 002/
│   └── ...
├── @main/
│   ├── plan.json            # 机器可读执行计划（可编辑）
│   ├── plan.md              # 人类可读计划
│   ├── summary.md           # 汇总索引（始终生成）
│   ├── synthesis_input.md   # synth 的输入（如启用 synth）
│   ├── summary_ai.md        # synth 输出（如启用 synth）
│   └── synthesis_meta.json  # synth 命令与元数据
└── project.json
```

## Runner 与模型配置

`parallel-vibe/config.yaml` 提供：

- 默认线程数、串行/并行默认值
- `codex` / `claude` CLI 命令与 `model_flag`
- `models.*`（可选）：填入你本机可用的 `model_id`

**plan.json 中每个 thread 的 runner 支持**：

| 字段 | 说明 |
|------|------|
| `type` | `codex` / `claude` / `shell` / `local` |
| `profile` | `fast` / `deep` / `default`（用于从 config.yaml 解析真实 model_id） |
| `model` | 显式 model_id（如填写，会覆盖 profile 解析结果） |

**推荐路由**（默认策略）：

| Runner | 适用任务 |
|--------|---------|
| `claude` | 规划/审查/风险与边界（强推理、强约束） |
| `codex` | 实现/修改/测试与验证（代码落地） |

注意：不同机器/账号可用的模型与 CLI 参数可能不同；建议先保持 `models.*` 为空，确认 CLI 可用后再填写。

## 常见问题

### Q：什么时候用 parallel-vibe？

当你需要"多方案并行尝试"或"多工作区隔离开发"时使用。例如：
- 同一功能用不同技术栈实现，对比效果
- 同一任务让不同角色（规划/实现/测试/审查）独立完成

### Q：默认为什么是串行？

串行执行可以省资源、减少 API 限流风险。只有当你明确要求"并行"时才开启并行模式。

### Q：大仓库复制很慢怎么办？

`parallel-vibe` 会为每个 thread 复制一份 `workspace/`，因此大仓库会有明显的磁盘/IO 成本。建议：

- 把 `--src-dir` 指向“最小必要子目录”（而不是整个 monorepo）
- 视情况扩展 `--copy-exclude`（默认值见 `config.yaml:defaults.copy_exclude`）
- 先用默认串行与较少 threads 验证思路，再按需加并发/加 thread

### Q：如何查看每个 thread 的结果？

查看 `.parallel_vibe/{project_id}/{thread_id}/RESULT.md`，或直接进入 `workspace/` 目录查看产物。

### Q：如何清理生成的目录？

在触发目录执行：

```bash
rm -rf .parallel_vibe
```

### Q：thread 执行失败怎么办？

查看 `runner.log` 和 `exit_code.txt` 了解失败原因。可以修改 `plan.json` 后用 `--resume` 续跑。

## 工作区隔离护栏（操作规范；非强安全边界）

当你在某个 thread 的 `workspace/` 内工作时：

- 只允许读写当前 `workspace/` 及其子目录
- 禁止访问父目录（`..`）与任何绝对路径写入
- 禁止读取/写入其他 thread 目录
- 产物必须落盘到当前 `workspace/`

说明：这是一种“工程隔离”（减少文件互相覆盖与相对路径污染），不是容器/沙箱级强安全隔离。默认拒绝 `--src-dir` 中的 symlink（可用 `--symlink-policy skip|keep` 覆盖，但存在越界风险）；不要把包含敏感文件（如 `.env`、SSH key）的目录作为 `--src-dir`。如计划使用 `runner.type=shell`，它会执行任意命令模板，仅对受信任 plan 使用。

## 清理

在触发目录执行：

```bash
rm -rf .parallel_vibe
```

## 配置说明

配置文件位于 `config.yaml`：

- `defaults.n_threads`：默认线程数
- `defaults.execution`：串行/并行默认值
- `defaults.symlink_policy`：`--src-dir` 下遇到 symlink 的处理策略（默认拒绝）
- `defaults.copy_exclude`：复制到各 thread/workspace 时的默认排除项（减少缓存/构建产物带来的成本与噪声）
- `cli`：codex/claude CLI 命令配置
- `models`：模型 ID 映射（可选）

---

版本信息见 `config.yaml:skill_info.version`。
