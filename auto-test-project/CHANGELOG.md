# Changelog

本文件记录 `auto-test-project` 技能的变更历史。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [1.1.0] - 2026-01-14

### Added（新增）

- **强制数量要求**：
  - 每轮 A 轮至少 10 个问题（P0 + P1 + P2 总和），鼓励 15-20 个
  - B 轮至少 10-20 个建设性建议
  - A.4 章节新增"强制检查"：必须满足至少 10 个问题才能进入下一轮
- `references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md`：建设性建议标准（项目级版本）
  - 定义建设性建议的四大特征：可执行、有证据、有价值、可验证
  - 提供"黄金公式"：位置 + 问题现象 + 影响分析 + 涉及模块 + 修复方案 + 验证方法
  - 包含项目级特有注意事项（跨模块依赖、项目级一致性、测试覆盖）
- `references/ISSUE_DISCOVERY_TECHNIQUES.md`：问题挖掘技巧（项目级版本）
  - 10 大类问题挖掘技巧，适配项目级测试场景
  - 技巧 1 扩展为"跨模块交叉验证"
  - 新增"项目级专项清单"和"跨模块测试场景"
  - 提供单轮检查策略和数量达标策略
- `references/ANTI_PATTERNS_LIBRARY.md`：反例库（项目级版本）
  - 七大质量原则的常见反例，扩展为项目级场景
  - 每个反例包含"涉及模块"字段，强调跨模块影响
  - 新增项目级特有反例（如跨模块接口不一致、跨模块配置重复定义等）
- `SKILL.md`：
  - A.2 章节新增"建设性"要求，引用 `CONSTRUCTIVE_SUGGESTION_GUIDELINES.md`
  - A.2 章节新增"问题挖掘技巧"引用，推荐每轮使用 3-5 个技巧组合
  - B.1 章节新增 B 轮数量要求（至少 10-20 个建议）
  - B.2 章节新增"强制修复要求"：P0 100%、P1 ≥ 80% 修复率
  - 完成条件新增"每轮 A 轮平均问题数量 ≥ 10 个"和"B 轮建议数量 ≥ 10 个"
- `config.yaml`：
  - 新增 `test_rounds.min_suggestions_per_round: 10`（A 轮最小建议数量）
  - 新增 `test_rounds.target_suggestions_range: [15, 20]`（A 轮目标范围）
  - 新增 `b_round_check.min_suggestions: 10`（B 轮最小建议数量）
  - 新增 `b_round_check.target_suggestions_range: [15, 20]`（B 轮目标范围）
  - 新增 `b_round_check.constructive_suggestion_required: true`（建设性建议要求）
  - 新增 `b_round_check.p0_fix_rate_required: 100`（P0 修复率要求）
  - 新增 `b_round_check.p1_fix_rate_required: 80`（P1 修复率要求）

### Changed（变更）

- 版本号从 `1.0.2` 升级为 `1.1.0`（新增功能，向下兼容）
- `skill_info.description` 更新为强调"强制每轮提出10-20个建设性建议"
- YAML frontmatter 同步版本号为 `1.1.0`，新增核心能力说明

### Fixed（修复）

- 修复 A 轮无明确数量要求导致测试深度不足的问题
- 修复 B 轮修复要求不够明确导致验收标准模糊的问题

---

## [Unreleased]

### Added（新增）

- `references/A_ROUND_PLAN_TEMPLATE.md`：A 轮优化计划结构模板（项目级版本，包含跨模块分析和依赖关系）
- B 轮质量检查新增第 7 个维度：**项目指令文件瘦身检查**
  - 检查 CLAUDE.md/AGENTS.md 等项目指令文件是否超过 400 行（建议阈值）
  - 检查是否存在可独立到模块级 `references/` 或 `docs/` 的详细内容
  - 提供渐进披露原则的瘦身策略表（项目级核心原则→CLAUDE.md，模块详细文档→模块内 references/）
- `SKILL.md`：
  - A.2 章节新增"全局意识"、"上下文连贯"、"项目视野"、"优先级依据"四大核心要求
  - 明确 P0/P1/P2 优先级判定标准（P0: 阻塞/安全/核心缺陷；P1: 重要优化/模块间接口；P2: 锦上添花）
  - 引用 `references/A_ROUND_PLAN_TEMPLATE.md` 作为详细结构模板
  - B 轮章节标注新增的项目指令文件瘦身检查维度
- `config.yaml`：
  - 新增 `b_round_check.mandatory: true` 配置项，明确 B 轮为强制环节（除非用户明确要求跳过）
  - A.4 章节增加强制提示："A 轮结束后（无论多少轮），必须进入 B 轮质量检查，不得跳过"
  - B 轮章节开头增加 ⚠️ 警告："B 轮质量检查是项目级自动测试流程的强制性环节，除非用户明确要求跳过，否则不得省略"
  - 完成条件引用 `config.yaml` 的 `mandatory` 配置，形成配置-文档联动

### Changed（变更）

- B 轮质量检查从"六大原则"扩展为"七大原则"，新增项目指令文件瘦身检查维度
- `templates/B_ROUND_CHECK_TEMPLATE.md`：**重大重构** - 所有七大原则的检查说明更加详细和可操作
  - 每个原则新增"核心原则"一句话总结
  - 每个原则新增三级判断标准（✅ 良好 / ⚠️ 改进信号 / ❌ 严重问题）
  - 每个原则新增"典型反例（项目级）"章节，包含具体代码/配置示例
  - 每个原则新增"改进方向（项目级）"操作指南
  - 目标：让模型在执行 B 轮检查时更清晰理解每个原则的定义、判断标准和改进方向，避免歧义
- `SKILL.md` A.2 章节：从简略的"问题清单"要求，重构为结构化的"全局视图 + 上下文 + 项目视野 + 优先级 + 可追溯性"框架
- 版本号升级为 `1.0.2`（`config.yaml: skill_info.version` 同步到 `SKILL.md` YAML frontmatter）

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
