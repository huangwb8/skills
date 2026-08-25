# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- 同步 `parallel-vibe` 默认工作区目录变更：并行评审产物路径从 `parallel_runs/.parallel-vibe/<project_id>/` 迁移到 `parallel_runs/.bensz-api/skills/parallel-vibe/<project_id>/`，更新 `build_parallel_review_plan.py`、`SKILL.md`、README、集成说明与版本号 `0.5.3 → 0.5.4`。
- 同步 `parallel-vibe` 默认工作区目录变更：并行评审产物路径从 `.parallel_vibe/<project_id>/` 改为 `.parallel-vibe/<project_id>/`，更新 `build_parallel_review_plan.py`、`SKILL.md`、README 与集成说明。

## [0.5.3] - 2026-03-24

### Changed
- `build_parallel_review_plan.py` 改为从 `config.yaml` 解析 `parallel-vibe` 依赖脚本路径与 thread 结果 schema，并把绝对脚本路径、输入快照指纹与固定 `project_id` 写入 `parallel_review_job.json`，避免系统级安装后相对路径失效与 prompt/schema 漂移
- `build_parallel_review_plan.py` 的 `recommended_command` 现在显式带上 `--project-id`，并将 `project_id` 与输入快照一起绑定，避免证据更新后误复用旧的并行评审目录
- `parallel_plan.md` 现在会回显可直接执行的 `recommended_command`，降低二次排障时在 JSON 与 Markdown 之间来回跳转的成本
- `aggregate_parallel_reviews.py` 开始按 `config.yaml` 校验 `RESULT.md` 的必需章节、Recommendation、Risk Level、Confidence，避免把无效 thread 输出聚合成误导性共识
- `validate_review_artifacts.py` 为损坏的 `manifest.json` 补充 fail-fast 错误处理，不再抛出原始 Python traceback
- `SKILL.md`、`README.md` 与 `references/parallel-vibe-integration.md` 同步更新并行依赖调用方式，明确优先使用 `parallel_review_job.json` 里的 `recommended_command`，并要求证据变化后重新生成 plan

## [0.5.2] - 2026-03-24

### Changed
- `prepare_review_job.py` 收紧输入契约：仓库输入只接受仓库根 URL 或 `owner/repo`，PR 输入只接受 PR URL、`#123`、`123` 或 `pr-123`，避免把 issue/tree 等错误链接误当成合法输入
- `build_parallel_review_plan.py` 新增 manifest 结构校验，改为从 manifest/config 读取快照目录，并对推荐命令中的路径做 shell quoting，降低配置漂移与含空格路径失败的风险
- `aggregate_parallel_reviews.py` 对缺失 project root、缺失 thread 目录、缺失 `RESULT.md` 改为明确报错，避免静默生成不完整或误导性的独立评审摘要
- `SKILL.md` / `README.md` 统一“默认优先使用内置 good-PR 标准、必要时再联网补充”的口径，并补齐 `review_count -> --n` 的参数映射说明
- `config.yaml` 版本升级为 `0.5.2`，并将 `review_count` 纳入可选输入

## [0.5.1] - 2026-03-24

### Changed
- `SKILL.md` 不再内嵌整段最终报告模板，改为只保留必需章节清单，并统一引用 `references/report-template.md`，降低主规范噪音与重复维护成本
- `config.yaml` 的版本升级为 `0.5.1`

## [0.5.0] - 2026-03-24

### Added
- 新增 `references/good-pr-standards.md`，将“什么是好 PR”的调研结果固化为 skill 内置参考

### Changed
- `SKILL.md` 将“好 PR 标准”从“每次运行强制联网查询”调整为“默认优先使用内置参考，仅在用户明确要求或参考不足时再联网补充”
- `prepare_review_job.py` 现在会把内置好 PR 标准预填充到 `notes/community_good_pr.md`

## [0.4.0] - 2026-03-24

### Added
- 新增 `references/license-checklist.md`，系统化检查依赖、vendored 代码、资源资产与许可证冲突风险
- 工作区脚手架新增 `notes/license_review.md`

### Changed
- `SKILL.md` / `README.md` 将 license / 合规审查升级为标准工作流的一部分
- 最终报告模板新增 `## License / 合规审查`
- 并行独立评审 thread 模板新增 `## License Review`
- `config.yaml` 将 `## License / 合规审查` 加入最终报告必需章节，并将 license 风险加入独立评审关注焦点
- 版本号升级为 `0.4.0`

## [0.3.0] - 2026-03-24

### Added
- 新增基于 `parallel-vibe` 的独立并行评审能力：默认进行 5 次独立 PR review，并在最终报告中综合各线程结论
- 新增 `scripts/build_parallel_review_plan.py`：生成 `parallel-vibe` 可执行计划、输入快照与 job manifest
- 新增 `scripts/aggregate_parallel_reviews.py`：聚合各 thread 的 `RESULT.md`，输出 recommendation/risk 分布与共识摘要
- 新增参考文档 `references/parallel-review-result-template.md` 与 `references/parallel-vibe-integration.md`

### Changed
- `config.yaml` 新增 `parallel_review.*` 配置段，并将 `## 独立评审综合结果` 加入最终报告必需章节
- `SKILL.md` / `README.md` 升级为“默认使用 parallel-vibe 做 5 次独立评审”的工作流口径
- 版本号升级为 `0.3.0`

## [0.2.0] - 2026-03-24

### Changed
- 脚本现在从 `config.yaml` 读取目录、文件名与报告章节要求，减少配置漂移
- `prepare_review_job.py` 新增 repo/PR 一致性校验、时间戳校验与工作区占位文件创建
- `validate_review_artifacts.py` 强化默认隐藏工作区检查、脚手架文件检查与报告结构检查
- `README.md` 补齐 fail-fast 行为说明、工作区说明与 WHICHMODEL 章节

### Added
- `scripts/common_config.py`：共享配置读取逻辑
- `prepare_review_job.py` 生成的 manifest 现在记录 `skill_version`
- 参考文档新增供应链、来源日期与“证据不足”口径

## [0.1.0] - 2026-03-24

### Added
- 初始化 `git-pr-review` skill
- 新增只读 PR 审查工作流，覆盖问题理解、方案分析、恶意/安全风险识别与 merge 建议
- 新增 `.git-pr-review/` 隐藏工作区约束与最终 Markdown 报告命名规则
- 新增 `prepare_review_job.py` 与 `validate_review_artifacts.py` 两个确定性脚本
- 新增报告模板、社区检索指引和安全检查清单
