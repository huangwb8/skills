# parallel-vibe - 变更日志

本文档记录 `parallel-vibe` skill 的重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added（新增）

- `parallel-vibe/references/smart-mode-protocol.md`：新增智能模式协议，沉淀 thread 输出 schema、主 agent 汇总 schema、串行/并行策略和“独立上下文不等于文件系统隔离”的边界说明
- `parallel-vibe/tests/智能模式-v202606141850/`：新增双模式改造的兼容性测试记录，用于验证代码模式脚本仍能生成 `plan.json` 和独立 workspace

### Changed（变更）

- `parallel-vibe/scripts/parallel_vibe.py`：默认中间工作区目录从 `.parallel_vibe/` 改为 `.parallel-vibe/`；同步更新 `SKILL.md`、README、配置、智能模式协议、工作区隔离文档和下游 `git-pr-review` 路径契约；版本号 `0.4.1 → 0.4.2`
- `parallel-vibe/SKILL.md` / `parallel-vibe/README.md` / `references/smart-mode-protocol.md` / `docs/工作区隔离机制.md`：将智能模式和代码模式的目录管理收敛为完全一致的 `.parallel_vibe/<project_id>/` 契约；固定目录、`plan.json`、`RESULT.md`、`runner.log` 不再作为切换代码模式的条件，模式差异仅保留为宿主 subagent 独立上下文 vs CLI runner 执行机制
- `parallel-vibe/config.yaml`：版本号 `0.4.0 → 0.4.1`；同步更新 skill 描述和 `modes.*.description`，明确两种模式共享目录契约
- `parallel-vibe/SKILL.md`：改造为“智能模式默认、代码模式保留”的双模式路由；默认用宿主原生 subagent 独立分析并汇总，只有脚本 runner、`plan-file`、`resume`、真实退出码或跨 CLI runner 自动化场景才进入代码模式
- `parallel-vibe/README.md`：重写为双模式用户指南，首屏推荐智能模式，同时说明两种模式共享 `.parallel_vibe/` 产物查看方式
- `parallel-vibe/config.yaml`：版本号 `0.3.1 → 0.4.0`；新增 `defaults.mode: smart` 以及 `modes.smart` / `modes.code` 语义说明，不改变现有脚本参数契约
- `parallel-vibe/plans/智能模式-v202606141850.md`：新增“智能模式默认、代码模式保留”的双模式改造计划，明确用宿主原生 subagent 能力替代普通多 agent 编排，同时保留现有脚本作为可追溯批处理接口
- `parallel-vibe/README.md`：按 `write-skill-readme` 风格重构为面向使用者的指南，突出 Prompt 触发路径；新增 `thread` 数、`runner` 进程数、`max_parallel` 与 `synthesize` 的关系说明，明确“总调用次数”与“同时运行中的独立进程数”的区别，并移除对普通使用者无价值的硬编码使用细节
- `parallel-vibe/README.md`：进一步收敛为以 `thread` 为中心的用户表述，弱化 `runner` 这一底层实现概念；把用户决策重点统一到 `thread` 数、`max_parallel` 与 `synthesize`

## [0.3.1] - 2026-02-27

### Fixed（修复）

- `parallel-vibe/scripts/parallel_vibe.py` / `config.yaml`：修复 claude runner 在 `-p` 模式下因缺少权限绕过标志而可能阻塞 thread 的问题；`global_args` 新增 `--dangerously-skip-permissions`（对应 codex 的 `--ask-for-approval never`）和 `--no-session-persistence`（避免 thread 运行污染会话历史）

## [0.3.0]

### Added（新增）

- `parallel-vibe/references/cli_prompt_usage.md`：补齐 Codex / Claude “一条命令一次执行”的 CLI prompt 用法速查（用于 thread 规划落到可执行命令）
- `parallel-vibe/@main/plan.json`（运行产物）：新增机器可读的 thread 计划落盘（每个 thread 的 runner/model/prompt 可追溯、可改写）

- 初始化 `parallel-vibe` skill：目录隔离 + 进程并行 + Prompt 约束的最小可用版本
- 新增确定性编排脚本 `parallel-vibe/scripts/parallel_vibe.py`：创建 project 目录、复制 workspace、并行运行 runner，并生成 `@main/summary.md`
- 新增技能文档与配置：`parallel-vibe/SKILL.md`、`parallel-vibe/README.md`、`parallel-vibe/config.yaml`
- 新增轻量测试会话：`parallel-vibe/tests/v202602031043/PLAN.md`、`parallel-vibe/tests/v202602031043/REPORT.md`

### Changed（变更）

- `parallel-vibe/scripts/parallel_vibe.py`：runner 参数升级为“全局参数 + 子命令参数”两段式拼接（`runner.args` / `runner.sub_args`），并引入 `config.yaml:cli.*.global_args/profile_args/subcommand_args`（把 `codex -c reasoning_effort=...`、`claude --effort ...` 等 `--help` 口径稳定落到一条命令）；增加 runner 可用性预检（缺少 CLI 时早返回）；线程未落盘 `workspace/RESULT.md` 时自动用 `runner.log` 生成兜底 `RESULT.md`，确保每个 thread 都可被汇总与 synth 消费
- `parallel-vibe/scripts/parallel_vibe.py`：彻底重构为“按计划拆分 threads + 每个 thread 一条 CLI 命令”；默认串行执行，支持 `--parallel/--max-parallel`；新增 `--src-dir/--out-dir` 与 `--plan-only/--plan-file`；汇总增强为 `@main/plan.json/plan.md/summary.md`，并可选 synth 汇总
- `parallel-vibe/config.yaml`：新增 `cli.*.global_args/profile_args/subcommand_args` 并对齐 `runner.args/sub_args` 语义；版本号 `0.2.1 → 0.3.0`（Single Source of Truth）
- `parallel-vibe/SKILL.md` / `parallel-vibe/README.md`：更新为“规划 thread → 单命令执行 → 汇总落盘”的新工作流，并强调默认串行策略
- `parallel-vibe/SKILL.md` / `parallel-vibe/README.md`：统一口径为“工程隔离 + 软护栏（操作规范）”，补齐 symlink/shell runner 风险提示，并澄清 `--resume` 会重建各 thread/workspace
- `parallel-vibe/docs/工作区隔离机制.md`：同步更新软护栏口径、symlink 策略与 `copy_exclude` 实践建议

- `parallel-vibe/scripts/parallel_vibe.py`：`--resume` 保留 `created_at`，并记录 `last_run_at/last_run_prompt`；summary 增强可读性（包含 `last_run_at` 与失败 thread 的 error 摘要）
- `parallel-vibe/SKILL.md` / `parallel-vibe/README.md`：补齐“系统安装后任意目录可用”的脚本路径示例（`~/.codex/skills/...` / `~/.claude/skills/...`）
- `parallel-vibe/config.yaml`：版本号更新（Single Source of Truth）

### Fixed（修复）

- runner 启动失败时不再导致整体崩溃：每个 thread 仍会落盘 `runner.log/exit_code.txt/done.json`
- `--workdir` 校验更明确：非目录/不存在时早返回并输出清晰错误
- workspace 复制不再跟随 symlink 复制其目标内容；默认拒绝 `src_dir` 中的 symlink，并新增 `--symlink-policy error|skip|keep`（避免击穿工作区边界假设）
- `runner.type=shell` 模板仍强制包含 `{prompt}` 占位符，但不再要求 `{prompt}` 必须是独立 token（支持 `--x={prompt}`）
- 清理残留 `.DS_Store` 文件，减少噪声与误提交风险

### Added（新增）

- 新增 auto-test-skill 优化会话：`parallel-vibe/plans/v202602031103.md`、`parallel-vibe/tests/v202602031103/`
- 新增 B 轮质量检查与验证会话：`parallel-vibe/plans/B轮-v202602031103.md`、`parallel-vibe/tests/B轮-v202602031103/`
- 新增 B 轮落地验证（symlink 策略 / shell 模板 / resume 语义）：`parallel-vibe/tests/B轮-v202602142014/PLAN.md`、`parallel-vibe/tests/B轮-v202602142014/REPORT.md`、`parallel-vibe/tests/B轮-v202602142014/_scripts/run_light_tests.sh`
