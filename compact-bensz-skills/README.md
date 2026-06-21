# compact-bensz-skills

`compact-bensz-skills` 用来压缩某个 Agent Skill 里的工作型 Markdown 文档，目标是在**不改变原有功能**的前提下，显著降低上下文体积。

## 最推荐用法

```text
请使用 compact-bensz-skills skill 压缩这个 Agent Skill 的工作型 Markdown 文档。
输入：/path/to/target-skill
输出：更新后的 skill 源文件；所有中间文件保存在目标目录下的 .bensz-api/skills/compact-bensz-skills/
```

## 适用场景

- 目标 skill 的 `SKILL.md`、`references/*.md` 明显冗长
- 你希望节省上下文，但不想动脚本逻辑
- 你需要先理解 skill，再做保守压缩

## 默认行为

- 工作区根：`<skill_root>/.bensz-api/skills/compact-bensz-skills/`
- 每次运行目录：`<skill_root>/.bensz-api/skills/compact-bensz-skills/{yyyy-mm-dd-hh-mm}/`
- 最近一次运行指针：`<skill_root>/.bensz-api/skills/compact-bensz-skills/latest-run.txt`
- 测试区：`<skill_root>/tests/compact-bensz-skills/`
- 自动忽略：`tests/`、`plans/`、目标 skill 根目录下的 `README.md`、`CHANGELOG.md`
- 优先保留：frontmatter、输入输出契约、安全边界、命令与路径
- 如果你显式指定外部 `workspace_dir`，脚本会接受，但验证报告会提示“中间文件已离开 skill 根目录”

## 常用示例

### 示例 1：压缩单个 skill

```text
请使用 compact-bensz-skills skill 压缩 `git-pr-review` 这个 skill 的工作型 Markdown 文档。
输入：/workspace/skills/git-pr-review
输出：原 skill 目录内更新后的 Markdown；中间文件放到 `.bensz-api/skills/compact-bensz-skills/`
```

### 示例 2：指定额外约束

```text
请使用 compact-bensz-skills skill 压缩这个 skill 的工作型 Markdown。
输入：/workspace/skills/my-skill
输出：更新后的 skill 源文件
另外，还有下列参数约束：
- 只压缩 Markdown，不改 Python/Bash 脚本
- 默认不要动 README.md / CHANGELOG.md
- 不要改变 SKILL.md frontmatter 的 name
- 压缩完成后要输出压缩前后统计
```

## 运行时会生成什么

- `.bensz-api/skills/compact-bensz-skills/latest-run.txt`
- `.bensz-api/skills/compact-bensz-skills/{yyyy-mm-dd-hh-mm}/analysis/file-inventory.json`
- `.bensz-api/skills/compact-bensz-skills/{yyyy-mm-dd-hh-mm}/analysis/compaction-plan.md`
- `.bensz-api/skills/compact-bensz-skills/{yyyy-mm-dd-hh-mm}/reports/size-before.json`
- `.bensz-api/skills/compact-bensz-skills/{yyyy-mm-dd-hh-mm}/reports/size-after.json`
- `.bensz-api/skills/compact-bensz-skills/{yyyy-mm-dd-hh-mm}/reports/size-delta.md`
- `.bensz-api/skills/compact-bensz-skills/{yyyy-mm-dd-hh-mm}/reports/validation.json`

## 备选用法（脚本）

```bash
python3 compact-bensz-skills/scripts/init_workspace.py --skill-root /path/to/target-skill
python3 compact-bensz-skills/scripts/measure_markdown.py --skill-root /path/to/target-skill --phase after
python3 compact-bensz-skills/scripts/validate_compaction.py --skill-root /path/to/target-skill
```

如果你想显式锁定某一轮：

```bash
python3 compact-bensz-skills/scripts/init_workspace.py --skill-root /path/to/target-skill
# 记下输出里的 run_id
python3 compact-bensz-skills/scripts/measure_markdown.py --skill-root /path/to/target-skill --run-id 2026-03-28-15-52 --phase after
python3 compact-bensz-skills/scripts/validate_compaction.py --skill-root /path/to/target-skill --run-id 2026-03-28-15-52
```

## WHICHMODEL

最后核对：2026-03-28。

- OpenAI 路线：
  - 复杂 skill 压缩、跨多份 `references/` 去重、需要保守保留约束时，优先 `gpt-5.4`；OpenAI 官方把它列为复杂推理、coding 和 agentic workflows 的起点。
  - 如果你主要在 Codex 里工作，且任务是“读文档 + 改文档 + 跑脚本验证”的 agentic coding 流程，可优先 `gpt-5-codex`；官方说明它是面向 Codex 一类环境优化的 agentic coding 模型。
  - 只做轻量统计、跑 helper scripts、整理测试记录时，可降到 `gpt-5.4-mini` 或同级快模型。
- Anthropic 路线：
  - 最复杂的压缩任务优先 `Opus`；Anthropic 官方建议复杂任务先从 Opus 开始。
  - 日常 skill 压缩、文档改写和一般验证优先 `Sonnet`；官方将其定位为速度与智能的最佳平衡，并在 Claude Code 中作为日常 coding 默认推荐档位。
  - 只做简单检查或批量轻任务时可用 `Haiku`。
- 长上下文优先级：
  - 如果目标 skill 很大，优先选支持更长上下文的模型。OpenAI 当前前沿模型页给 `gpt-5.4` 标注了 1M context；Anthropic 也为 Sonnet/Opus 提供了 1M context 选项或长会话模式。

参考：
- OpenAI Models: https://developers.openai.com/api/docs/models
- OpenAI GPT-5-Codex: https://developers.openai.com/api/docs/models/gpt-5-codex
- Anthropic Models Overview: https://platform.claude.com/docs/en/about-claude/models/overview

## FAQ

### 它会改 `tests/` 和 `plans/` 吗？

不会。这个 skill 默认忽略目标 skill 里的 `tests/` 和 `plans/`。

### 它会处理 `README.md` 或 `CHANGELOG.md` 吗？

默认不会。这个 skill 只把工作型 Markdown 视为主要目标；目标 skill 根目录下的 `README.md`、`CHANGELOG.md` 一般属于面向人类的说明或发布记录，不纳入默认压缩范围。

### 它会自动改脚本代码吗？

默认不会。它的核心目标是压缩 Markdown 文档；只有当文档与脚本明显不一致时，才应先指出风险，再做最小修正。

### 它怎么保证不破坏功能？

它要求先理解 `SKILL.md`、`config.yaml`、`scripts/`，然后再压缩文档，并在最后运行统计和校验脚本。

### 为什么现在要用 `{yyyy-mm-dd-hh-mm}`？

因为这个 skill 可能会反复执行。按分钟级 run 目录隔离后，每一轮的快照、统计和验证结果都能独立追溯，不会被下一轮覆盖；同一分钟重复运行时脚本会自动追加后缀。

### 它会检查相对链接是否越界吗？

会。`validate_compaction.py` 现在不仅检查链接是否存在，也会拒绝链接跳出目标 skill 根目录。
