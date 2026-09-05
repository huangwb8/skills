# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed（变更）
- 规范化 `SKILL.md` 正文骨架，补齐输入、输出、校验、失败恢复和公共约束摘要；prompt-programming 的既有功能语义保持不变。

## [0.2.1] - 2026-04-11

### Changed
- 保守压缩 `SKILL.md`、`references/primitives.md`、`references/examples.md` 与 `references/translation-rules.md`，删除重复说明并收紧措辞
- 保留 6 个语义原子、块顺序、输入验证、控制流推断、输出保真、冲突处理与质量标准等硬约束

## [0.2.0] - 2026-04-11

### Added
- 初始化 `prompt-programming` 技能
- 定义 6 个最小语义原子：Entity、Intent、Operation、Constraint、Control、Check
- 定义统一的 Prompt Program 方言与固定块顺序
- 添加 prompt 到 Prompt Program 的翻译工作流
- 添加 README 用户指南与基础 WHICHMODEL 小节
- 添加 `references/primitives.md`、`references/examples.md` 与 `references/translation-rules.md`

### Changed
- 明确 `输出` 与 `返回` 的语义边界：前者定义目标产物，后者只定义交付动作
- 将块语义、句式模板、可选块与冲突处理顺序收敛到 `config.yaml`
- 将控制流推断策略从“强制补最小控制逻辑”改为“仅在显式或强隐含时补出”
- 为复杂任务改用软句子预算，避免压缩过度导致信息丢失
- README 补充可选块省略、输入要求、顺序保真与官方模型来源说明

### Fixed
- 修复示例 2 将“生成脚本”错误弱化为“输出脚本说明”的等价性问题
- 修复缺少输入验证与显式格式保真规则的问题
