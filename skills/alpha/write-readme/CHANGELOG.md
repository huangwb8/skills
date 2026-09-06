# write-readme 变更记录

## [Unreleased]

### Changed（变更）
- 规范化 `SKILL.md` 正文骨架，补齐输入、输出、校验、失败恢复和公共约束摘要；write-readme 的既有功能语义保持不变。
- 默认首屏升级为完整 GitHub Hero（居中标题/标识、事实徽章、导航、价值主张、解释段和证据/Quick Start），新增 `references/github-hero-patterns.md`，沉淀产品展示型、开发者工具型、库/SDK 型和资源/集合型四种可复用套路及其可访问性门槛。

## [0.2.0] - 2026-09-04

### Added（新增）

- 新增可选 Kernel runtime 声明、五个领域 State 和 `readme-pair-alignment` JSON-stdio Verifier Pack；结构检查仍复用原 CLI，语义与不确定性保留给 AI/人工复核。
- 新增 Evidence Contract、required Gate 和运行身份说明，明确路径、脱敏、来源追溯与 fail-closed 边界。

## [0.1.1] - 2026-09-03

### Added（新增）

- 初始化通用 README Skill：项目类型识别、事实清单、双语对齐、Agent Skill legacy 模板和确定性结构检查脚本；检查器同时验证相对图片目标，避免视觉资源失效却被判定为通过。
