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
  - `install.sh`: macOS/Linux/WSL 一键安装脚本
  - `install.ps1`: Windows PowerShell 一键安装脚本
  - `install.bat`: Windows CMD 一键安装脚本
  - `README.md`: 安装说明文档
  - 支持通过一行命令从 GitHub 远程安装所有技能

### Changed
- **项目指令文档重构**：
  - 重构 AGENTS.md，优化工程原则和工作流说明
  - 精简 CLAUDE.md，通过 `@./AGENTS.md` 引用核心指令
  - 统一文档格式规范：层级标题不使用序号前缀
- **README.md 首页重构**：
  - 按当前仓库状态重写首页结构，突出“技能库 + 技能开发流水线”的双重定位
  - 刷新核心技能清单，补充 `bensz-collect-bugs`、`git-pr-review` 等新增能力
  - 优化快速开始、安装方式、项目结构和维护流程说明，降低新读者理解成本
  - 保留演示视频与 AI 算力视频入口，维持首页导览信息完整性
  - 同步对齐 `README_EN.md`，使中英文首页结构与信息范围保持一致
  - 为中英文首页标题补充克制风格的 emoji，提高辨识度与视觉质感
- **git-commit 技能增强**：
  - 实现动态语言检测，自动识别项目主要语言
  - 新增 `--lang` 参数，支持手动指定提交信息语言
- **install-bensz-skills 技能优化**：
  - 实现脚本路径感知机制
  - 新增配置化管理，支持自定义安装源
  - 新增 Windows 安装脚本支持
- **文档规范化**：
  - 统一所有技能的 `description` 为单行格式
  - 统一 `metadata.author` 为 "Bensz Conan"
  - 新增 WHICHMODEL 模型选择指南
- **README.md**: 优化安装方法说明
  - 新增"方法一：一键快速安装"作为推荐方式
  - 将原有方法调整为"方法二：本地安装"
  - 新增"方法三：手动安装"
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
