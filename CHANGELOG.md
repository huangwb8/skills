# Changelog

All notable changes to the skills repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [Unreleased]

## [4.2.6] - 2026-07-05

### Changed
- **install-bensz-skills 版本升级到 `0.5.10`**：远程 Git 源更新链路新增传输重试、Git HTTP low-speed 失败阈值、sparse checkout 失败兜底和 last-known-good 缓存复用；当远程更新失败或只能复用旧缓存时返回非零退出码，避免自动化场景误判为最新安装成功。同步更新 `SKILL.md`、README、i18n 文案与测试口径。
- **@install 标准库安装器下载稳定性优化**：GitHub zip archive 与 raw config 下载新增重试，并通过临时 `.part` 文件落盘，避免中断下载留下半成品 zip；保持无 Git、无第三方依赖的远程 bootstrap 设计。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.5` 更新为 `v4.2.6`。

## [4.2.5] - 2026-07-04

### Changed
- **install-bensz-skills 版本升级到 `0.5.8`**：新增远程仓库持久缓存——远程源 repo 缓存在 `~/.bensz-skills/installation/cache/remote-sources/`，重复远程更新时通过 `git fetch --depth 1 --no-tags` 增量更新，避免每次从零 clone；clone/fetch 均禁用 tag 拉取，缓存损坏或 Git 更新失败时自动删除并重建。同步更新 `SKILL.md`、README 与测试，进一步缩短重复远程更新等待时间。
- **@install 远程一键安装器缓存对齐评估**：经核查，v0.5.8 的持久缓存是 Git clone/fetch 专属优化；`@install` 基于 GitHub zip archive 单次下载、无 Git 依赖，天然不涉及该流程。强制对齐需引入 HTTP 条件请求（ETag/Last-Modified）或 commit-sha 失效判断，违背其「仅标准库、轻量 bootstrap」设计哲学，故按 AGENTS.md「远程拉取特有逻辑允许不同」条款保持现状。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.4` 更新为 `v4.2.5`。

## [4.2.4] - 2026-07-04

### Changed
- **install-bensz-skills 版本升级到 `0.5.7`**：远程安装在 `skills_path` 指向仓库子目录时优先使用 Git sparse checkout，只拉取目标 skills 子树；指定 `--skill` 时进一步收窄到目标 skill 目录，减少大仓库远程更新时的等待和无关内容下载。
- **远程安装对比性能优化**：同一远程源安装到 Codex 与 Claude Code 时复用远程 skill MD5 计算结果，避免重复哈希；当指定单个 skill 且某个源缺失该 skill 时，不再为了确认缺失而完整下载该源。
- **@install 标准库安装器同步优化**：保持无 Git、无第三方依赖的 bootstrap 入口，同时按 `skills_path` 和 `--skill` 选择性解压 GitHub zip archive，降低大仓库安装时的解压与扫描成本。
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.3` 更新为 `v4.2.4`。

## [4.2.3] - 2026-06-28

### Changed
- **@install legacy 清单可及性同步**：远程一键安装器优先从 `install-bensz-skills/config.yaml` 读取权威 `legacy_skill_names`，支持通过 GitHub raw 配置获取，下载源内配置作为次级兜底，内置清单仅保留为 bootstrap fallback，避免远程入口复制业务清单后漂移

### Fixed
- **@install 下载失败退出码修复**：当选定远程源下载失败或无法解析 skills 根目录时，安装器现在返回非零退出码，避免自动化场景误判为安装成功

## [4.2.2] - 2026-06-28

### Changed
- **auto-draw-plot 版本升级到 `0.2.11`**：收紧 `roadmap` / `schematic` 模式的中文标签正常字宽护栏，默认要求现代黑体/思源黑体/Noto Sans CJK 风格与自然字形比例；明确禁止窄体、长体、压缩体、condensed/narrow/compressed font、横向压缩和瘦长拉伸字体，并鼓励长标签自然换行而非压缩字形；同步更新 `SKILL.md`、README、prompt 指南、配置、脚本负面 prompt 与本地 fallback prompt
- **init-project 版本升级到 `2.3.3`**：补齐 `.gitignore` 模板与 PyYAML 缺失时脚本内置兜底规则，新增 `.systematic-literature-review/`、`.complete_example/`、`.latex-cache/`、`.make_latex_model/`、`.nsfc-budget/`、`.nsfc-code/`、`.nsfc-length-aligner/`、`.nsfc-qc/`、`*.nsfc-qc/`、`.nsfc-ref-alignment/`、`.research-idea/`、`.write-paper/` 与 `.secrets/` 等中间产物和敏感目录忽略项；`.check-review-alignment/` 继续保留在模板中
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.1` 更新为 `v4.2.2`

## [4.2.1] - 2026-06-21

### Changed
- **auto-test-project 版本升级到 `1.3.1`**：将项目级测试计划与测试会话默认目录从项目根 `plans/` / `tests/` 收敛到 `.bensz-api/skills/auto-test-project/output/plans/` 与 `.bensz-api/skills/auto-test-project/output/tests/`；同步更新 `SKILL.md`、README、references、配置与脚本帮助信息，并将 `.bensz-api/skills/auto-test-project/**` 纳入 A 轮独立评估排除范围
- **auto-test-skill 版本升级到 `2.3.1`**：将 skill 测试计划与测试会话默认目录从目标 skill 根 `plans/` / `tests/` 收敛到 `.bensz-api/skills/auto-test-skill/output/plans/` 与 `.bensz-api/skills/auto-test-skill/output/tests/`；同步更新 `SKILL.md`、README、references、配置与脚本说明，并将 `.bensz-api/skills/auto-test-skill/**` 纳入独立评估排除范围
- **parallel-vibe 版本升级到 `0.4.3`**：默认运行目录从 `.parallel-vibe/` 迁移到 `.bensz-api/skills/parallel-vibe/{yyyy-mm-dd-hh-mm}/`；默认 run id 改为分钟级时间戳，同一分钟重复运行自动追加 `-02` 等后缀；`--project-id` 改为安全 run/project id，`--resume` 现在必须显式指定 `--project-id`
- **git-pr-review 版本升级到 `0.5.4`**：同步 `parallel-vibe` 目录契约，下游并行评审产物路径从 `parallel_runs/.parallel-vibe/<project_id>/` 迁移到 `parallel_runs/.bensz-api/skills/parallel-vibe/<project_id>/`，并更新 `build_parallel_review_plan.py`、`SKILL.md`、README 与集成说明
- **awesome-code 版本升级到 `3.0.1`**：将 `cache.py`、`performance_benchmark.py` 与 `mirror_optimizer.py` 的独立运行 fallback 目录迁移到 `.bensz-api/skills/awesome-code/` 或 `.bensz-api/skills/mirror-optimizer/`；测试 watch 默认忽略 `.bensz-api/`
- **仓库忽略规则更新**：根 `.gitignore` 新增 `.bensz-api`，避免本地中间产物与 release notes 草案误入提交
- **发布提示更新**：`Prompts.md` 中的目标发布 tag 从 `v4.2.0` 更新为 `v4.2.1`

### Fixed
- **嵌套测试目录验证修复**：`auto-test-project/scripts/verify_test_session.py` 不再假设 `session_dir.parent.parent` 是项目根，可根据配置的嵌套 tests 目录推断 project root，并在缺少计划文档时输出配置化 plans 路径
- **auto-test-skill 验证配置回退修复**：`verify_test_session.py` 优先读取目标 skill 的 `config.yaml:directories`，缺失时回退到 auto-test-skill 自带配置，避免验证脚本在外部目标 skill 上丢失默认目录契约
- **嵌套镜像输出目录修复**：`awesome-code/scripts/mirror_optimizer.py` 创建输出目录时使用 `parents=True`，适配 `.bensz-api/skills/mirror-optimizer/output/` 这类多级目录

## [4.2.0] - 2026-06-21

### Added
- **auto-draw-plot 中文标签字重护栏**：`roadmap` / `schematic` 模式新增护栏——中文标签使用清晰的无衬线常规到半粗体字重、深灰或黑色，缓解“字偏瘦”观感；版本号 `0.2.9 → 0.2.10`
- **工作区目录唯一分配机制**：`auto-draw-plot`、`compact-bensz-skills`、`git-pr-review` 的工作区初始化脚本新增时间戳冲突兜底——同一分钟多次运行自动追加 `-02` / `-03` 后缀避免目录覆盖；`git-pr-review` 报告文件名与 manifest 新增 `run_id` 字段用于追溯

### Changed
- **统一中间产物目录到 `.bensz-api/` 命名空间**：将分散在各 skill 下的隐藏工作区收敛到 `.bensz-api/skills/<skill-name>/`，并结构化为 `input` / `output` / `log` 子目录，降低多 skill 并存时的目录污染与命名冲突：
  - `auto-draw-plot`：`.draw-plot/` → `.bensz-api/skills/auto-draw-plot/`
  - `compact-bensz-skills`：`.compact-bensz-skills/` → `.bensz-api/skills/compact-bensz-skills/`
  - `git-pr-review`：`.git-pr-review/` → `.bensz-api/skills/git-pr-review/`
  - `awesome-code`：`.awesome-code/{reports,benchmarks,logs,cache}` → `.bensz-api/skills/awesome-code/{output/reports,output/benchmarks,log,cache}`；镜像优化产物 `.mirror/` → `.bensz-api/skills/mirror-optimizer/output/`
  - `auto-test-code`：`tmp/` + `tests/` → `.bensz-api/skills/auto-test-code/{yyyy-mm-dd-hh-mm}/output/tests/`
  - `auto-test-project` / `auto-test-skill`：`tests/` → `.bensz-api/skills/<skill>/output/tests/`
  - 各 skill 的 `SKILL.md`、`README.md` 与初始化脚本同步更新路径契约
- **统一时间戳与 run_id 格式**：时间戳从 `%Y%m%d%H%M%S%f`（密集无分隔）改为 `%Y-%m-%d-%H-%M`（可读分隔）；`run_prefix` 由 `run-` / `run_` 收敛为空；`auto-test-code` 的 `create_session.py` 兼容新旧两种 run_id 格式
- **parallel-vibe 工作区更名**：默认目录 `.parallel_vibe/` → `.parallel-vibe/`（下划线改连字符），`copy_exclude` 同步更新；下游 `git-pr-review` 的并行评审产物路径与集成文档同步；版本号 `0.4.1 → 0.4.2`
- **git-pr-review 校验逻辑适配**：`validate_review_artifacts.py` 隐藏目录校验放宽为“路径含 `.bensz-api` 或目录名以 `.` 开头”；报告名正则适配新时间戳格式（含可选 `-NN` 后缀）
- **init-project .gitignore 模板**：新增 `.bensz-api/`、`/.bensz-api/`、`.parallel-vibe/` 忽略规则（保留 `.parallel_vibe/` 兼容旧产物）；版本号 `2.3.1 → 2.3.2`
- **install-bensz-skills legacy 清理**：将已弃用的 `nsfc-roadmap`、`nsfc-schematic` 加入 `legacy_skill_names`，安装时自动清理系统级残留目录；版本号 `0.5.4 → 0.5.5`
- **awesome-code 文档规范化**：`SKILL.md` 移除序号化标题前缀（如“代理团队（14 个子代理）”→“代理团队”），符合“层级标题不使用序号前缀”规范；`code-reviewer` 输入说明泛化计划文档来源（`PLAN.md` / `docs/plans/*.md` 等）
- **awesome-code frontend-specialist 增强**：补充表单与输入控件整齐度策略，覆盖输入框高度阶梯、宽度栅格、label/help/error 文案规则、行内基线对齐、状态样式与移动端表单分组
- **AGENTS.md 双安装器同步约束**：新增“双安装器与业务逻辑同步”章节，明确 `install-bensz-skills/scripts/install.py`（本地开发版，单一真理来源）与 `@install/install.py`（远程一键版）必须保持业务逻辑对齐，安装器业务变更时强制联动检查

## [4.1.3] - 2026-06-14

### Added
- **新增技能**：
  - `awesome-code`: 多代理协作开发技能，支持并行协调开发
  - `better-prompt`: Prompt 优化技能，基于 OpenAI 和 Anthropic 最佳实践
  - `parallel-vibe`: 并行 Vibe Coding 技能，支持多工作区并行尝试
  - `write-skill-readme`: 技能文档生成器，自动生成用户友好的 README.md
- **PR 审查归档**：
  - `docs/pr-reviews/Git-PR-Review_huangwb8_skills_pr-1_20260330184127.md`：新增对 `huangwb8/skills#1` 的评估报告，记录对外部 Tessl 评分优化 PR 的审查结论与证据
- **@install/**: 新增快速安装脚本目录
  - `install.py`: 基于 Python 标准库的单文件跨平台安装器
  - `README.md`: 安装说明文档
  - 支持通过一行 Python 命令从 GitHub 远程安装所有技能

### Changed
- **项目指令新增"双安装器业务逻辑同步"约束**：
  - 在 AGENTS.md「本机可发现性（系统级安装）」章节新增子节，明确 `install-bensz-skills/scripts/install.py`（本地开发版，安装逻辑单一真理来源）与 `@install/install.py`（远程一键版）必须保持业务逻辑对齐
  - 强制联动：当 `install-bensz-skills` 发生业务逻辑变更时，必须检查 `@install/install.py` 是否需要同步对齐；仅远程拉取特有逻辑（下载、解压、远程源发现）允许差异
- **项目指令文档重构**：
  - 重构 AGENTS.md，优化工程原则和工作流说明
  - 精简 CLAUDE.md，通过 `@./AGENTS.md` 引用核心指令
  - 统一文档格式规范：层级标题不使用序号前缀
- **README.md 首页重构**：
  - 按当前仓库状态重写首页结构，突出“技能库 + 技能开发流水线”的双重定位
  - 刷新核心技能清单，补充 `bensz-collect-bugs`、`git-pr-review` 等新增能力
  - 同步 `init-project` 与 `awesome-code` 的最新能力口径：补充标准 `docs/` 目录初始化、三层代理分派与 required agent 门禁说明
  - 优化快速开始、安装方式、项目结构和维护流程说明，降低新读者理解成本
  - 保留演示视频与 AI 算力视频入口，维持首页导览信息完整性
  - 同步对齐 `README_EN.md`，使中英文首页结构与信息范围保持一致
  - 为中英文首页标题补充克制风格的 emoji，提高辨识度与视觉质感
- **README 安装说明同步**：
  - 将首页快速开始口径更新为以 `@install/install.py` 标准库远程安装器为推荐入口
  - 明确一键安装默认会安装 `general`、`research`、`anthropic-docs` 三个远程源
  - 补充 `--source`、`--codex`、`--claude`、`--check`、`--lang zh` 等常用参数示例
  - 同步更新 `README_EN.md`，保持中英文安装说明一致
- **git-commit 技能增强**：
  - 实现动态语言检测，自动识别项目主要语言
  - 新增 `--lang` 参数，支持手动指定提交信息语言
- **install-bensz-skills 技能优化**：
  - 实现脚本路径感知机制
  - 新增配置化管理，支持自定义安装源
  - 配合 `@install/install.py` 形成远程快速安装与本地开发安装两类入口
- **@install 安装器重构**：
  - 将跨平台快速安装入口收敛为单文件 Python 脚本，降低 shell/PowerShell/CMD 多入口维护成本
  - 安装流程改为仅依赖 Python 标准库，不再要求 Git 或 PyYAML 作为启动期依赖
  - 默认安装语言调整为英文，保留中文输出选项
- **@install 安装器策略对齐**：
  - 为标准库远程安装器补齐 `--skill` 单技能过滤能力，支持重复传入和逗号分隔
  - 多远程源安装时只处理匹配的 production skill，并对缺失或非生产 skill 给出明确提示
  - 同步更新 `@install/README.md` 参数说明
- **文档规范化**：
  - 统一所有技能的 `description` 为单行格式
  - 统一 `metadata.author` 为 "Bensz Conan"
  - 新增 WHICHMODEL 模型选择指南
- **README.md**: 优化安装方法说明
  - 将推荐安装方式调整为一行远程安装
  - 将克隆仓库后的脚本安装定位为本地开发安装
  - 保留 AI 调用 `install-bensz-skills` 的自然语言安装方式
  - 更新项目结构，添加新增技能说明

### Fixed
- 修复 init-project 技能配置与脚本兼容性问题
- 修复 `install-bensz-skills` 远程安装对“仓库根目录即 skills 根目录”布局的兼容性问题
  - 安装器现在会在 `skills_path` 缺失时自动回退并识别仓库根目录
  - 修正 `general` 远程源配置为 `skills_path: "."`，恢复 `@install` 默认远程安装链路

## [0.1.0] - 2025-01-25

### Added
- 初始化 skills 仓库
- 添加核心技能：init-project, install-bensz-skills, git-commit, git-publish-release
- 添加测试技能：auto-test-skill, auto-test-project
- 添加项目文档：AGENTS.md, CLAUDE.md, README.md, README_EN.md
