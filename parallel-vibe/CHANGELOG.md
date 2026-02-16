# parallel-vibe - 变更日志

本文档记录 `parallel-vibe` skill 的重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added（新增）

- `parallel-vibe/references/cli_prompt_usage.md`：补齐 Codex / Claude “一条命令一次执行”的 CLI prompt 用法速查（用于 thread 规划落到可执行命令）
- `parallel-vibe/@main/plan.json`（运行产物）：新增机器可读的 thread 计划落盘（每个 thread 的 runner/model/prompt 可追溯、可改写）

- 初始化 `parallel-vibe` skill：目录隔离 + 进程并行 + Prompt 约束的最小可用版本
- 新增确定性编排脚本 `parallel-vibe/scripts/parallel_vibe.py`：创建 project 目录、复制 workspace、并行运行 runner，并生成 `@main/summary.md`
- 新增技能文档与配置：`parallel-vibe/SKILL.md`、`parallel-vibe/README.md`、`parallel-vibe/config.yaml`
- 新增轻量测试会话：`parallel-vibe/tests/v202602031043/PLAN.md`、`parallel-vibe/tests/v202602031043/REPORT.md`

### Changed（变更）

- `parallel-vibe/scripts/parallel_vibe.py`：彻底重构为“按计划拆分 threads + 每个 thread 一条 CLI 命令”；默认串行执行，支持 `--parallel/--max-parallel`；新增 `--src-dir/--out-dir` 与 `--plan-only/--plan-file`；汇总增强为 `@main/plan.json/plan.md/summary.md`，并可选 synth 汇总
- `parallel-vibe/config.yaml`：移除“看似可配置但实际固定”的 `work_dir_name`；新增 `symlink_policy`；补齐更通用的 `copy_exclude`；版本号 `0.2.0 → 0.2.1`（Single Source of Truth）
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
