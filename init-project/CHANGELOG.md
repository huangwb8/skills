# Changelog

**重要**：本文件是 init-project 技能变更的**唯一正式记录**。凡是本技能的更新，都要统一在本文件里记录。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Changed（变更）

- `init-project/SKILL.md` 按社区推荐格式瘦身：移除大段内嵌模板示例，改为引用 `init-project/templates/*.template`，确保 `SKILL.md` ≤ 500 行

## [2.0.1] - 2026-01-18

### Fixed（修复）

- **版本号一致性**：从 SKILL.md 中移除硬编码的 `version` 字段，改为注释引用 config.yaml（P0-1）
- **路径验证**：在 `generate_auto()` 和 `main()` 中添加输出目录验证，防止在不存在的目录中创建文件（P0-2）
- **必需章节同步**：更新 config.yaml 中的 `agents_required_sections`，与 AGENTS.md.template 保持一致（P0-3）
- **智能合并提示**：在智能合并时输出警告，提示用户如果结果不符合预期可使用 `--overwrite` 参数（B3-1）
- **占位符检测**：在 `replace_placeholders()` 中添加未替换占位符警告（P1-7）

### Removed（移除）

- **未使用配置**：删除 `max_questions_rush`、`min_required_info_rush`、`backup_before_overwrite`、`backup_suffix`、`static_validation_checks` 等未实现的配置项（P1-2/P1-3/P1-4）
- **脚本版本号**：移除 generate.py 中的硬编码版本号，改为注释引用 config.yaml（P2-1）

### 说明（Notes）

本次更新基于 auto-test-skill 的批判性分析，修复了 8 个问题（3 个 P0、4 个 P1、1 个 P2）。

---

## [2.0.0] - 2025-01-18

### Added（新增）

- **架构重构**：采用 AGENTS.md 作为 Single Source of Truth 的新架构
- **自动引用**：CLAUDE.md 通过 `@./AGENTS.md` 语法自动引用 AGENTS.md
- **零维护成本**：修改 AGENTS.md 后，CLAUDE.md 自动生效，无需运行同步命令
- **符合社区标准**：遵循 [AGENTS.md 官方规范](https://agents.md/)（60k+ 开源项目采用）
- **版本管理**：在 config.yaml 中添加 skill_info 版本信息

### Changed（变更）

- **生成顺序**：先生成 AGENTS.md（跨平台通用），再生成 CLAUDE.md（Claude Code 特定）
- **SKILL.md**：
  - 更新描述，强调 AGENTS.md 的 Single Source of Truth 地位
  - 移除所有同步相关的工作流说明
  - 添加 Claude Code @ 引用语法的说明
- **generate.py**：
  - 移除 `--sync-from` 参数和相关逻辑
  - 移除 `--check-consistency` 参数和相关逻辑
  - 移除 `sync_from_source()`、`check_consistency()` 方法
  - 更新 `check_consistency_reminder()` 为新的工作流提醒
  - 调整生成顺序，先生成 AGENTS.md，再生成 CLAUDE.md
- **CLAUDE.md.template**：
  - 完全重写为简洁的引用模板
  - 使用 `@./AGENTS.md` 语法
  - 添加"与 AGENTS.md 的关系"章节
- **config.yaml**：
  - 添加 skill_info 版本信息
  - 更新目录结构模板的注释
  - 简化 claude_required_sections 和 agents_required_sections

### Removed（移除）

- **双向同步功能**：移除 AGENTS.md ↔ CLAUDE.md 的双向同步逻辑
- **一致性检查**：移除两个文件的一致性检查功能
- **同步命令**：移除 `--sync-from` 和 `--check-consistency` 命令行参数

### Fixed（修复）

- 修正了 CLAUDE.md 和 AGENTS.md 的关系描述，明确 AGENTS.md 是跨平台通用文件

### 说明（Notes）

**为何进行此次大版本更新？**

1. **符合社区标准**：AGENTS.md 是跨平台通用格式，应作为主文件，而非特定平台的附属文件
2. **降低维护成本**：通过 Claude Code 的 `@` 引用语法，实现真正的零维护成本
3. **简化工作流**：用户只需维护 AGENTS.md 一个文件，CLAUDE.md 自动生效
4. **更好的架构**：AGENTS.md（通用）+ CLAUDE.md（特定）的分离架构更清晰

**升级指南**：

如果你已经在使用 v1.x 版本：

1. 运行 `python3 init-project/scripts/generate.py --auto --overwrite` 重新生成文件
2. 之后只需维护 AGENTS.md，CLAUDE.md 会自动引用 AGENTS.md 的内容
3. 不再需要运行任何同步命令

**参考文档**：

- [AGENTS.md 官方网站](https://agents.md/)
- [Claude Code Issue #990：@ 引用语法](https://github.com/anthropics/claude-code/issues/990)

---

## [1.0.0] - 2025-01-XX

### Added（新增）

- 初始化 init-project 技能
- 支持自动生成 CLAUDE.md 和 AGENTS.md
- 支持双向同步功能
- 支持一致性检查
