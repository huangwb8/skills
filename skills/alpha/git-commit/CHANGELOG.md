# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-02-13

### Changed
- **动态语言检测**：移除 `config.yaml` 中硬编码的 `default_language`，改为运行时动态检测
  - 优先级：用户指定（`--lang`） > 最近 5 次 commit 主体语言 > 设备默认语言
  - 最近 5 次 commit 以多数语言为准（如 3 中文 + 2 英文 → 中文）
  - 平局时使用设备默认语言
  - 无 commit 时使用设备默认语言（检测 `$LANG` 环境变量）

### Added
- 新增 `--lang <zh|en>` 参数，支持用户临时指定提交信息语言

## [2.1.0] - 2026-02-13

### Added
- **自动推送**：提交成功后默认自动执行 `git push`
  - 自动模式：直接推送，无需确认
  - 审核模式：询问是否推送
  - 自动检测并设置上游分支（`git push -u origin <branch>`）
- 新增 `--no-push` 参数，跳过自动推送（仅本地提交）

### Changed
- 工作流程增加"自动推送"步骤（步骤 6），原"安全回滚"调整为步骤 7
- 更新重要约束，明确"默认推送"行为

## [2.0.1] - 2026-02-11

### Fixed
- Auto stage now includes untracked files by default (even when the staging area is not empty), preventing “new files missing from commit”.

### Added
- `--no-untracked` option to disable automatic handling of untracked files.

## [2.0.0] - 2026-01-19

### Added
- **工作模式**：新增自动模式和审核模式，默认使用自动模式
  - 自动模式：AI 自主决策暂存、拆分、提交，无需用户确认
  - 审核模式：在关键决策点暂停，等待用户确认
- 新增 `--review` 参数启用审核模式
- 新增 `--no-all` 参数在自动模式下跳过自动暂存
- 在 config.yaml 中新增 `modes` 配置段，定义两种模式的行为

### Changed
- **破坏性变更**：默认行为从"审核模式"改为"自动模式"
  - 暂存区为空时，自动模式默认执行 `git add -A`（而非提示用户选择）
  - 达到拆分阈值时，自动模式自动拆分提交（而非仅给出建议）
  - 提交前，自动模式直接提交（而非显示 commit message 等待确认）
  - 如需原有交互行为，请使用 `--review` 参数启用审核模式

## [1.0.0] - 2026-01-18

### Added
- 初始化 git-commit skill
- 从 zcf:git-commit 迁移到项目级技能管理
- 支持 Conventional Commits 规范
- 支持可选 emoji 前缀
- 智能拆分提交建议
- 根据仓库历史自动选择语言
- 默认运行本地 Git 钩子（可 --no-verify 跳过）
- 在 README.md 中添加致谢章节，说明参考了 UfoMiao/zcf 项目
