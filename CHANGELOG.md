# Changelog

All notable changes to the skills repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [Unreleased]

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
