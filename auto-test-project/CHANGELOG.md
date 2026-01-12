# Changelog

本文件记录 `auto-test-project` 技能的变更历史。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added（新增）

- `config.yaml`：新增 `b_round_check.mandatory: true` 配置项，明确 B 轮为强制环节（除非用户明确要求跳过）
- `SKILL.md`：
  - A.4 章节增加强制提示："A 轮结束后（无论多少轮），必须进入 B 轮质量检查，不得跳过"
  - B 轮章节开头增加 ⚠️ 警告："B 轮质量检查是项目级自动测试流程的强制性环节，除非用户明确要求跳过，否则不得省略"
  - 完成条件引用 `config.yaml` 的 `mandatory` 配置，形成配置-文档联动

### Changed（变更）

- 版本号升级为 `1.0.1`（`config.yaml: skill_info.version` 同步到 `SKILL.md` YAML frontmatter）

## [1.0.0] - 2026-01-12

### Added（新增）
- 新增 `auto-test-project` 技能：项目级自动化测试驱动优化
- 从 `auto-test-skill` 迁移核心能力并扩展为项目级支持
- 新增项目类型识别功能：自动识别 Agent Skill、工作流项目等
- 新增项目初始化流程：验证项目结构、识别测试边界
- 新增跨模块问题分析和处理能力
- 新增项目级六大质量原则检查（扩展自 skill 级别）
- 新增项目级测试模板：
  - `B_ROUND_CHECK_TEMPLATE.md`：B轮质量检查模板（项目级扩展）
  - `TEST_PLAN_TEMPLATE.md`：测试计划模板
  - `PROJECT_TYPE_ANALYSIS_TEMPLATE.md`：项目类型分析模板
  - `BUG_REPORT_TEMPLATE.md`：Bug 报告模板（支持跨模块问题）
  - `OPTIMIZATION_PLAN_TEMPLATE.md`：优化计划模板
  - `TEST_REPORT_TEMPLATE.md`：测试报告模板
  - `FINAL_SUMMARY_TEMPLATE.md`：最终总结模板
- 新增辅助脚本：`scripts/create_test_session.py`（适配项目级）
- 新增配置文件：`config.yaml`（项目级配置，包含项目识别、测试边界等）
- 新增参考文档：`references/PROJECT_TESTING_BEST_PRACTICES.md`

### Changed（变更）
- 将测试对象从"单个 skill"扩展为"完整项目"
- 将质量检查维度从 skill 级别扩展为项目级别
- 将输出目录从 skill 内部扩展为项目根目录
- 将问题分析从单文件扩展为跨模块、跨文件
- 将 CHANGELOG 更新目标从 skill 级别扩展为项目级别

### Technical Details（技术细节）
- 项目识别支持多种指令文件（CLAUDE.md、AGENTS.md、PROJECT.md 等）
- 测试边界配置支持核心模块识别和排除路径设置
- 优先级配置扩展为项目级示例（跨模块问题、架构问题等）
- B轮质量检查增加 `project_level` 和 `scope` 字段
