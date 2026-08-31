# Changelog

## [0.2.1] - 2026-08-31

### Changed（变更）
- 压缩 `SKILL.md` 的重复说明，保持触发语义、输入输出、Kernel 复用/元组件审查、安全边界与计划契约不变。

## [0.2.0] - 2026-08-31

### Changed（变更）
- 补充 Kernel 二层架构审查：要求先盘点并论证现有 Verifier/State 的直接、组合或适配复用，再评估跨领域元组件提炼机会。
- 强制最终设计计划设置独立章节，以分点理由同时记录 Kernel 复用结论、元 Verifier/State 提炼结论及其对人类实现决策的影响。

## [0.1.0] - 2026-08-31

### Added（新增）
- 初始化 `verifier-state-architect` beta Skill：通过业务理解、删除影响测试、AI/确定性分工和 Kernel 契约映射，生成 Verifier/State 设计计划。
