# Changelog

本文件记录 download-fulltext-pdf skill 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added
- 自动安装缺失依赖机制（scihub 库）
- 路径遍历安全检查（防止恶意输入访问系统文件）
- `create_missing_dirs` 配置项支持
- Unpaywall `emails` + `email_strategy` + `state_file` 配置，支持多邮箱负载均衡

### Fixed
- arXiv ID 提取 bug（返回类型从列表改为字符串）
- 路径验证安全漏洞（增加工作目录边界检查）
- Unpaywall 仅使用 `best_oa_location.url_for_pdf` 导致“有 OA 但无 PDF”误判的问题（改为遍历 `oa_locations` 候选链接）

### Changed
- 更新 README.md 说明开箱即用性
- 更新 SKILL.md 说明自动安装机制
- Unpaywall 请求逻辑支持按状态码（如 429/5xx）自动切换邮箱重试
- 版本号 `0.1.0 → 0.1.1`
- 版本号 `0.1.1 → 0.1.2`；Unpaywall round_robin 状态文件从 `.download-fulltext-pdf/` 迁移到 `.bensz-api/skills/download-fulltext-pdf/state/`

## [0.1.0] - 2026-01-24

### Added
- 初始版本发布
- 通过 DOI 号下载学术论文全文 PDF
- 支持 Sci-Hub、arXiv、Unpaywall、期刊官网等多源策略
- 智能 arXiv ID 检测
- 下载后 PDF 验证
- 详细的错误处理和报告
