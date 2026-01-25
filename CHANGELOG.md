# Changelog

All notable changes to the skills repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [Unreleased]

### Added
- **@install/**: 新增快速安装脚本目录
  - `install.sh`: macOS/Linux/WSL 一键安装脚本
  - `install.ps1`: Windows PowerShell 一键安装脚本
  - `install.bat`: Windows CMD 一键安装脚本
  - `README.md`: 安装说明文档
  - 支持通过一行命令从 GitHub 远程安装所有技能

### Changed
- **README.md**: 优化安装方法说明
  - 新增"方法一：一键快速安装"作为推荐方式
  - 将原有方法调整为"方法二：本地安装"
  - 新增"方法三：手动安装"
  - 更新项目结构，添加 @install/ 目录说明

### Fixed
- 无

## [0.1.0] - 2025-01-25

### Added
- 初始化 skills 仓库
- 添加核心技能：init-project, install-bensz-skills, git-commit, git-publish-release
- 添加测试技能：auto-test-skill, auto-test-project
- 添加项目文档：AGENTS.md, CLAUDE.md, README.md, README_EN.md
