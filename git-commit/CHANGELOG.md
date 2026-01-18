# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
