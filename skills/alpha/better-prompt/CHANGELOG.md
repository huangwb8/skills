# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed（变更）
- 规范化 `SKILL.md` 正文骨架，补齐输入、输出、校验、失败恢复和公共约束摘要；better-prompt 的既有功能语义保持不变。

## [0.2.0] - 2026-02-18

### Added
- 添加 Step 0 输入验证：定义空输入、过短输入、已完善 prompt 的处理方式
- 添加"版本与兼容性"章节：说明适用的模型和最佳实践来源
- 添加"不适用场景"章节：明确何时不应使用本技能
- 添加"优化效果评估"章节：提供优化前后对比评估表
- 添加 Examples 使用规则：明确复杂任务必须提供示例
- config.yaml 添加 `validation` 配置：输入验证阈值
- config.yaml 添加 `include_evaluation` 配置：控制效果评估输出

### Changed
- 统一优先级系统：在 SKILL.md 中明确说明 P0/P1/P2 与 config.yaml 数值的对应关系
- 修复 Examples "可选"描述：改为"复杂任务必需，简单任务可省略"
- 激活 templates 配置引用：在 SKILL.md 的"特殊场景处理"章节中引用 config.yaml 的模板
- config.yaml 添加完整注释：每个配置项都有说明
- config.yaml 版本号升级：0.1.0 → 0.2.0

### Fixed
- 修复跨文件一致性问题：SKILL.md 与 config.yaml 的优先级描述现在一致
- 修复 output_format 配置与文档的矛盾：现在明确"默认全部包含"

## [0.1.0] - 2026-02-18

### Added
- 初始化 better-prompt 技能
- 实现基于 OpenAI 和 Anthropic 官方最佳实践的优化框架
- 支持五维度优化：清晰度、完整性、结构化、示例性、约束性
- 支持模型类型适配（GPT 模型 vs 推理模型）
- 支持场景专项优化（代码生成、文本分析、创意写作、多轮对话）
- 添加详细的最佳实践参考文档
