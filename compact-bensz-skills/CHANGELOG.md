# compact-bensz-skills - 变更日志

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与语义化版本规范。

## [Unreleased]

### Added（新增）
- 新增 `workspace_inside_skill_root` 诊断字段到初始化清单与校验结果，便于识别用户显式指定的外部工作区
- 新增 `latest-run.txt` 与 `--run-id` 机制，支持 `measure_markdown.py` / `validate_compaction.py` 复用指定 run

### Changed（变更）
- 默认待压缩范围收紧为工作型 Markdown：目标 skill 根目录下的 `README.md`、`CHANGELOG.md` 不再纳入 `file-inventory.json`、快照和体积统计；`SKILL.md`、README、参考清单与测试夹具已同步改为这一口径
- `validate_compaction.py` 现在会在缺少 `size-after.json` 时自动补算当前统计，降低验证顺序对结果的影响
- `README.md`、`SKILL.md`、`references/validation-checklist.md` 同步补充“外部工作区会被警告”和“本地链接不得越出 skill 根目录”的口径
- 默认工作区从单一 `.compact-bensz-skills/` 切换为按运行隔离的 `.compact-bensz-skills/run-{timestamp}/`
- `init_workspace.py` 会输出 `workspace_base` / `run_id` 并刷新 `latest-run.txt`，后续脚本默认复用最近一次运行
- `config.yaml` 版本号 `0.2.0 -> 0.3.0`

### Fixed（修复）
- 修复本地 Markdown 链接校验只检查“是否存在”而不检查“是否越出目标 skill 根目录”的缺口
- 修复压缩后 `SKILL.md` frontmatter.name 可能与压缩前快照悄然漂移而未被校验的问题
- 修复多次连续运行时中间文件可能被同一隐藏目录相互覆盖、导致不同会话互相污染的问题

## [0.1.0] - 2026-03-28

### Added（新增）
- 初始化 `compact-bensz-skills` skill，用于压缩 Agent Skill 的 Markdown 文档，同时保留触发语义、输入输出契约与安全边界
- 新增 `scripts/init_workspace.py`：创建目标 skill 的 `.compact-bensz-skills/` 隐藏工作区，生成 Markdown 清单、快照与压缩计划骨架
- 新增 `scripts/measure_markdown.py`：统计压缩前后字数/字符数/标题数/代码块数，并输出对比报告
- 新增 `scripts/validate_compaction.py`：校验 `SKILL.md` frontmatter、相对 Markdown 链接、忽略目录约束与压缩收益
- 新增 `references/compaction-playbook.md`、`references/preservation-checklist.md`、`references/validation-checklist.md` 三份参考文档
- 新增 `tests/compact-bensz-skills/fixture-skill/` 轻量夹具，用于验证文件发现、工作区隔离与压缩校验流程
