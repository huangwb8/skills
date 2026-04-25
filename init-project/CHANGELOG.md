# Changelog

**重要**：本文件是 init-project 技能变更的**唯一正式记录**。凡是本技能的更新，都要统一在本文件里记录。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added（新增）

- **安全性声明章节**：在 SKILL.md 中新增"安全性声明"章节，明确技能的工作边界
  - 允许的操作：在当前工作目录内创建/修改文件，只读访问当前目录
  - 禁止的操作：修改当前目录之外的任何文件或文件夹
  - 风险说明：违反边界可能导致用户不知情的文件修改、其它项目崩溃、数据丢失
  - 执行保障：脚本使用相对路径，所有文件写入前验证目标路径
- **README.md 安全性保障章节**：在用户指南中添加"安全性保障"章节，说明安全机制和操作边界
- **docs 目录初始化**：完整初始化项目时，脚本会自动创建 `docs/` 与 `docs/plans/`；如果目录已经存在则直接复用，避免重复创建或报错
- **计划文档固定位置**：在生成的 `AGENTS.md` 中明确计划文档统一放在 `./docs/plans/`

### Changed（变更）

- **增强路径验证**：改进 `validate_output_dir()` 方法，新增"当前工作目录边界检查"
  - 使用 `Path.relative_to()` 验证输出目录必须在当前工作目录内
  - 如果尝试访问当前目录之外的路径，立即终止并显示详细警告信息
  - 保留原有的系统敏感目录检查作为额外安全层
- **docs 非计划文档同步约束**：更新 `AGENTS.md` 模板与说明文档，要求当代码变化导致 `docs/` 中非 `plans/` 文档过时时，必须实时更新这些用户文档、教程等内容，使其与项目实际业务逻辑保持一致
- **AGENTS.md 模板压缩**：合并 Codex CLI 输出、编辑边界、变更记录、版本管理与有机更新说明，保留核心约束并减少生成文档冗余
- **必需章节同步**：更新 `agents_required_sections` 与智能合并白名单，兼容旧版 `## 变更边界` 内容迁移到新版编辑原则
- **CHANGELOG.md 模板压缩**：将教程式记录规范改为最小维护规则，保留初始记录、Keep a Changelog 和 SemVer 约束
- **CLAUDE.md 模板压缩**：将 Claude Code 专属说明进一步合并为 4 条短规则，保留 `@./AGENTS.md` 引用和必要适配

## [2.1.0] - 2026-03-02

### Added（新增）

- **智能 .gitignore 生成**：自动生成适合项目类型的 Git 忽略规则，确保向 GitHub 提交时安全
  - 共性设置：操作系统生成文件、IDE 配置、环境变量和敏感信息（.env、*.pem、*.key）、日志和临时文件
  - 个性化设置：根据项目类型（Python/Web/Rust/Go/Java/数据科学/文档）添加特定忽略规则
  - 安全优先原则：宁可多忽略，不可漏掉敏感文件
  - 智能合并策略：保留用户自定义规则，更新标准化部分
- 新增 `--skip-gitignore` 命令行参数，可跳过 .gitignore 生成
- 在 config.yaml 中添加 `gitignore_common` 和 `gitignore_by_type` 配置项
- **配置加载优雅降级**：config.yaml 不存在或损坏时使用默认配置，而非崩溃
- **输出目录安全验证**：阻止在系统敏感目录（/etc、/root 等）中创建文件

### Fixed（修复）

- 移除 Python gitignore 规则中的 `.gitignore` 条目（该规则会导致 .gitignore 文件忽略自己）
- 修复 docs 项目类型检测过于宽泛的问题（移除 `*.md` 指标，避免误判）
- 修复 YAML frontmatter 与 SKILL.md 正文对生成文件描述不一致的问题
- 消除目录验证逻辑重复代码（提取为 `validate_output_dir` 公共方法）

### Removed（移除）

- 移除未使用的目录模板配置（default_directory_template、python_directory_template、web_directory_template）
- 移除未使用的 template_placeholders 配置

### Changed（变更）

- `init-project/SKILL.md` 按社区推荐格式瘦身：移除大段内嵌模板示例，改为引用 `init-project/templates/*.template`，确保 `SKILL.md` ≤ 500 行
- **AGENTS.md 输出精简**：`init-project/templates/AGENTS.md.template` 不再生成 `## 目录结构` 章节；智能合并时会自动丢弃旧的该章节，避免被当作自定义内容回填
- **.gitignore 配置迁移**：将 gitignore 规则从 config.yaml 迁移到 templates/gitignore.yaml，减少 config.yaml 篇幅约 230 行

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
