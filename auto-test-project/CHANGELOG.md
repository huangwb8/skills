# Changelog

本文件记录 `auto-test-project` 技能的变更历史。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added（新增）

- **模板自动替换机制**：从技术上消除"占位符未替换"问题
  - `scripts/create_test_session.py`：新增 `_render_template()` 函数，自动替换 `{{KEY}}` 格式的占位符
  - 支持模板变量：`TEST_ID`、`PROJECT_ROOT`、`SESSION_NAME`、`TEST_TIME`、`ROUND_KIND` 等
  - 新增 `--create-plan` 参数：自动创建计划文档骨架
  - TEST_REPORT_TEMPLATE.md：重构为详细的结构化模板

- **强制数量要求**：迫使 AI 深入挖掘问题
  - A.2 节新增"数量要求"（强制）：每轮至少 10 个问题（P0 + P1 + P2 总和）
  - 鼓励达到 15-20 个问题，项目级测试建议 15-25 个
  - A.4 节新增"数量验证"（强制检查）：进入下一轮前必须确认问题数量 ≥ 10

- **计划-执行一致性检查**：确保计划中的问题在报告中有对应记录
  - `scripts/verify_test_session.py`：新增 `check_plan_report_consistency()` 函数
  - 检查计划中的问题编号（P0-1, P1-2）是否在报告中有对应记录
  - 检查问题数量是否达到最低要求（≥ 10 个）
  - 新增配置常量 `MIN_ISSUE_COUNT = 10`

- **新增参考文档**：
  - `references/PROJECT_ISSUE_DISCOVERY_TECHNIQUES.md`：项目级问题挖掘技巧（8 大技巧）
    - 跨模块一致性检查、依赖关系分析、配置管理审查
    - 文档同步检查、边缘情况压力测试、代码"模式匹配"
    - 安全性扫描、性能分析
  - `references/EXAMPLE_TEST_REPORT.md`：完整的测试报告示例（12 个问题）
    - 展示期望的输出质量
    - 每个问题都有：位置、影响、修复建议、验证方法
    - 使用多种问题挖掘技巧

- `SKILL.md`：
  - 新增关键词：`template rendering`、`issue discovery techniques`
  - 引用 `references/PROJECT_ISSUE_DISCOVERY_TECHNIQUES.md`
  - 引用 `references/EXAMPLE_TEST_REPORT.md`

### Changed（变更）

- `scripts/create_test_session.py`：**重大重构**
  - 新增 `_render_template()` 函数
  - `_copy_or_template()` 函数新增 `template_values` 参数，支持模板变量替换
  - 新增 `--create-plan` 命令行参数
  - 内联模板改为使用 `{{ROUND_KIND}}` 等变量

- `scripts/verify_test_session.py`：增强验证能力
  - 新增 `check_plan_report_consistency()` 函数
  - 新增配置常量 `MIN_ISSUE_COUNT`
  - 验证项从 4 项增加到 5 项

- `templates/TEST_REPORT_TEMPLATE.md`：**完全重写**
  - 从简单的 115 行模板重构为详细的 137 行结构化模板
  - 包含：执行摘要、验证点执行情况、问题修复记录、问题修复统计、遗留问题、证据文件、下一步建议
  - 在模板末尾添加验证命令提示

- 版本号升级为 `1.2.0`（`config.yaml: skill_info.version` 同步到 `SKILL.md` YAML frontmatter）

### Technical Details（技术细节）

- 项目识别支持多种指令文件（CLAUDE.md、AGENTS.md、PROJECT.md 等）
- 测试边界配置支持核心模块识别和排除路径设置
- 优先级配置扩展为项目级示例（跨模块问题、架构问题等）
- B轮质量检查增加 `project_level` 和 `scope` 字段

### Fixed（修复）

- **模板占位符未替换问题**：通过 `_render_template()` 函数从技术上解决
- **计划与执行脱节问题**：通过 `check_plan_report_consistency()` 检测
- **报告内容过短问题**：通过 `MIN_ISSUE_COUNT` 和 `MIN_REPORT_LENGTH` 双重门槛

- `scripts/create_test_session.py`：
  - 修复 B 轮创建会话时潜在的未定义变量问题（`--kind b` 可用）
  - 修复 plan 文件存在时误把 plan 复制到 `TEST_PLAN.md` 的行为；新增 `--seed-test-plan-from-plan`（默认关闭）
  - 统一 `--create-plan` 生成/引用的 plan 路径，避免 B 轮漏掉 `.md`
  - 补齐模板变量（`PLAN_ID/PLAN_TIME/PROJECT_TYPE/PLAN_DOC_PATH` 等）用于头字段自动填充

- `scripts/verify_test_session.py`：
  - 放宽“文件:行号”证据正则，支持常见小写路径与 Windows 路径，减少误判

- 文档与模板一致性：
  - 将“B 轮质量检查”口径统一为项目级七大质量原则（与 `config.yaml:b_round_check.dimensions` 对齐）
  - 重写 `templates/OPTIMIZATION_PLAN_TEMPLATE.md` 为 `P0-1/P1-1/P2-1` 编号结构，确保计划-报告一致性检查可落地
  - `templates/TEST_PLAN_TEMPLATE.md` 标题改为按轮次变量渲染，并统一使用 `PLAN_DOC_PATH`

- CLI 可用性与严格模式：
  - `scripts/create_test_session.py` 增加 `--id` 格式校验（强制 `vYYYYMMDDHHMM`），并将常见错误统一为 argparse 报错（无堆栈）
  - `scripts/verify_test_session.py` 改为 argparse CLI，新增 `--require-plan`（严格模式）以及 `--min-report-length`/`--min-issue-count`（阈值可配置）

- `config.yaml` 口径精简与对齐：
  - 明确标注 scripts 不解析 config（避免误导为“配置可改变脚本行为”）
  - 去除重复字段与通用但未被本 skill 使用的段落（testing/reporting/quality/acceptance）
  - 补齐结构化门槛字段：A 轮最少问题数/目标范围、B 轮建议数与修复率门槛、verify 默认阈值
  - 同步更新 `README.md` 与 `SKILL.md` 对配置字段的引用口径

- 文档有机瘦身与模块化：
  - `SKILL.md` 增加 Quick Start，并将 FAQ/最佳实践正文下沉到 `references/`
  - 新增 `references/FAQ.md`，集中维护常见问题、证据标准与严格模式用法
  - `README.md` 增加 Quick Start，移除重复的长篇最佳实践/FAQ，改为引用 references

- 模板与示例对齐严格模式：
  - 重写 `templates/B_ROUND_CHECK_TEMPLATE.md` 为可填写骨架，并使用 `P0-1` 编号以支持一致性检查
  - `templates/TEST_PLAN_TEMPLATE.md` 与 `templates/TEST_REPORT_TEMPLATE.md` 补充严格模式验证入口
  - 新增 `references/EXAMPLE_STRICT_MINIMAL.md`，用于演示编号对齐与严格验证
  - `references/A_ROUND_PLAN_TEMPLATE.md` 统一使用 `P0-1/P1-1/P2-1` 编号口径

- 确定性自检与批量验证：
  - 新增 `scripts/verify_skill.py`：一键自检本 skill（必需文件、脚本可用性、模板关键占位符自动填充回归）
  - 新增 `scripts/verify_all_sessions.py`：批量验证 `tests/` 下会话（支持 `--require-plan` 与 `--skip-missing-plan`）
  - 清理误生成的 `plans/B轮-v202601152999.md`，避免严格模式批量验证被历史残留阻塞

- 安全性与跨平台鲁棒性：
  - `scripts/create_test_session.py` 默认拒绝系统根目录/用户主目录作为 project-root（需显式 `--allow-unsafe-root` 才可覆盖）
  - 将缺少指令文件的 warning 输出到 stderr，避免污染 stdout 的“会话路径输出”
  - `scripts/verify_test_session.py` 与 `scripts/verify_skill.py` 采用容错读取，避免非 UTF-8 文件导致验证崩溃
  - Quick Start/FAQ 补充安全提示，降低误用风险

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
