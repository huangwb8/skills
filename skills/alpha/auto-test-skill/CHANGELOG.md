# auto-test-skill - 变更日志

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Changed（变更）
- 版本升级：2.3.0 → 2.3.1；将计划与测试会话默认目录从目标 skill 根 `plans/` / `tests/` 收敛到 `.bensz-api/skills/auto-test-skill/output/plans/` 与 `.bensz-api/skills/auto-test-skill/output/tests/`，同步更新 `SKILL.md`、README、references 与脚本说明。

### Added（新增）
- `scripts/verify_test_session.py`：确定性验证测试会话完整性（会话结构/关联计划/占位符残留/报告状态），支持 `--require-plan` 与自动发现 skill_root
- **B 轮全覆盖修复机制**：B 轮优化与验证现在要求处理所有 P0-P2 问题（修复或说明不修复理由），确保所有发现的问题都有闭环处理
- **B 轮第八质量原则：配置集中化检查**：新增"精确端（config.yaml）与模糊端（工作文档）完全分离"检查维度，确保所有可配置参数集中在 config.yaml 作为单一真相来源，提升 skill 可维护性
- **批判性思维框架**：auto-test-skill 现在强制使用"刁钻角度"思考，确保发现系统性问题
- `references/CRITICAL_THINKING_GUIDE.md`：批判性思维指南（核心文档）
  - 框架 1: 系统视角思考（架构设计/过度设计/一致性）
  - 框架 2: 刁钻角度思考（边缘情况/恶意输入/隐式假设/自我质疑）
  - 框架 3: 问题质量标准（黄金公式 + 质量检查清单）
  - 高质量问题示例库（系统性架构问题/过度设计问题/安全性问题）
- `config.yaml`：
  - 新增 `test_rounds.min_p0_p1_ratio: 60`（A 轮 P0+P1 最小占比）
  - 新增 `test_rounds.min_systemic_issues: 3`（A 轮系统性问题最小数量）
  - 新增 `a_round_check.independent_review`（A 轮独立评估配置：审查范围 + 排除范围）

### Changed（变更）

- 版本升级：2.2.2 → 2.3.0（新增会话验证脚本、配置瘦身、脚本安全/可用性增强）
- `scripts/create_test_session.py`：
  - 新增 `--a-test-id`（B 轮记录对应 A 轮会话 id，并替换 B 轮模板的 `A_TEST_ID`）
  - 为 `TEST_PLAN_TEMPLATE.md` 的常用占位符提供默认值，避免残留 `{{...}}`
  - 会话/计划模板中不再硬编码 `tests/` 路径（通过 `SESSION_DIR_REL/TEST_PLAN_REL/TEST_REPORT_REL` 注入）
  - 路径安全：拒绝 symlink 目录，并校验 plans/tests/session 解析后仍位于 `--skill-root`
- `scripts/verify_test_session.py`：新增会话结构与一致性验证（可选但推荐）
- `config.yaml`：
  - 裁剪为“脚本读取 + 规划口径”的最小集合，并明确脚本仅解析 `directories.*` 与 `templates.*`
  - `exclude_patterns` 增加 `tests/**` 与 `plans/**`（并保留旧写法兼容）
- `templates/OPTIMIZATION_PLAN_TEMPLATE.md`：本轮轻量测试路径引用改为脚本注入，支持自定义 tests 目录
- `SKILL.md`：
  - 版本同步到 2.3.0
  - A.3/B.2 增加 `verify_test_session.py` 推荐自检命令
  - B 轮会话创建示例补充 `--a-test-id`
- `README.md`：
  - 更新 config 说明为“脚本读取范围 + 规划口径”，并补充版本更新顺序
  - 补充 `verify_test_session.py` 最小用法示例
- 版本升级：2.2.1 → 2.2.2（配置/文档一致性修复）
- **核心定位升级**：从"自动化测试驱动优化技能"升级为"批判性思维驱动的测试优化技能"
- **A 轮独立评估机制**：A 轮评估默认不查看 `plans/` 与 `tests/`，并强制声明审查范围（required_files/required_dirs）与排除范围（exclude_patterns），降低确认偏差、提升多轮价值
- **create_test_session.py**：
  - 对任意目标 skill 可用：优先使用目标 skill 的 `templates/`，否则回退到 auto-test-skill 自带模板
  - 严格校验 `--id` 为 `vYYYYMMDDHHMM`（省略 `--id` 时自动生成），避免不规范会话目录
  - `--kind` 支持 `A轮/B轮`（中文环境更自然）
  - 会话元数据时间字段在同一时刻生成，避免边界条件不一致
- **SKILL.md**：
  - 版本升级：2.2.0 → 2.2.1
  - 版本升级：2.1.0 → 2.2.0
  - description：新增"批判性思维驱动"和"系统性问题"关键词
  - A.2 章节：从"问题分析与计划生成"重构为"批判性分析与计划生成"
  - A.2 章节：新增"批判性思维是核心要求"警告（不是可选项）
  - A.2 章节：新增"质量要求"（P0+P1 占比 ≥ 60%，系统性问题 ≥ 3 个）
  - A.2 章节：新增"独立评估原则"与"审查范围"强制要求（不看 `plans/` 与 `tests/`）
  - A.2 章节：新增"批判性聚焦"和"刁钻角度"核心要求
  - A.2 章节：新增"批判性思维框架"必读文档列表（CRITICAL_THINKING_GUIDE.md 放在首位）
  - A.4 章节：进入下一轮条件改为“本轮问题闭环 + 用户轮次数未完成”，并明确“每轮独立评估，不因问题已解决提前终止”
  - 完成条件：新增"P0+P1 占比 ≥ 60%"和"系统性问题 ≥ 3 个"验收标准
  - 可复用资源：突出 CRITICAL_THINKING_GUIDE.md 为核心文档
- **references/A_ROUND_PLAN_TEMPLATE.md**：大幅简化（从 200+ 行简化为核心结构）
  - 第一部分：独立评估与审查范围（不看 plans/tests + required_files/required_dirs）
  - 第二部分：批判性思维分析（刁钻角度 + 系统性问题）⚠️ 新增
  - 第三部分：问题清单（P0-P2，明确质量要求）
  - 第四部分：问题质量检查（9 条强制检查）⚠️ 新增
- **templates/OPTIMIZATION_PLAN_TEMPLATE.md**：补齐 A 轮独立评估与审查范围章节，避免仅列问题而遗漏“范围覆盖/排除范围”声明
- **README.md**：补齐 A 轮独立评估说明与配置项索引，统一 B 轮为“七大质量原则”，并补充脚本模板回退说明
- **config.yaml**：
  - skill_info.version: 2.1.0 → 2.2.0
  - skill_info.version: 2.2.0 → 2.2.1
  - skill_info.description: 更新为"批判性思维驱动的测试优化技能"
  - test_rounds: 新增质量门槛配置（min_p0_p1_ratio, min_systemic_issues）
  - skill_info.description: 补充 A 轮“独立评估”口径

- **测试会话**：
  - A 轮验证会话：`tests/v202601162213/`
  - B 轮验证会话：`tests/B轮-v202601162227/`

### Fixed（修复）

- 修复 A 轮计划模板对 tests 目录的硬编码：现在会正确引用自定义 `directories.tests`
- 修复 B 轮计划模板关键字段 `A_TEST_ID` 无法自动替换的问题（新增 `--a-test-id`）
- 修复 B 轮“七大/八大”口径漂移：统一为“质量原则检查”，并明确以 `config.yaml:b_round_check.dimensions` 为准
- 修复 B 轮 P1 修复率阈值规则冲突：将 `config.yaml:b_round_check.p1_fix_rate_required` 统一为 100%，并同步更新 `auto-test-skill/SKILL.md` 验收口径
- 修复 `scripts/create_test_session.py` 的“伪配置”风险：脚本现在会读取 `config.yaml` 中的 `directories.*` 与 `templates.*`（缺失/解析失败时回退默认值），并统一使用正斜杠展示路径
- 修复"问题挖掘技巧"未强调的问题（现在通过 CRITICAL_THINKING_GUIDE.md 强制使用）
- 修复 A 轮模板过于复杂导致 AI 选择性忽略的问题（大幅简化，突出核心要求）
- 修复缺乏"系统性问题"挖掘引导的问题（现在强制要求 ≥ 3 个系统性问题）

### Removed（移除）

- 移除 A_ROUND_PLAN_TEMPLATE.md 中冗余的"修改步骤"和"轻量测试计划"章节（聚焦核心批判性思维）
- `config.yaml`：移除未被引用的过度设计段落（test_session/priority/testing/reporting/quality/acceptance），降低误用

---

## [2.1.0] - 2026-01-14

### Added（新增）

- **"非常挑剔"升级**：auto-test-skill 现在强制每轮提出 10-20 个建设性建议
- `references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md`：建设性建议标准文档（可执行、有证据、有价值、可验证）
- `references/ISSUE_DISCOVERY_TECHNIQUES.md`：问题挖掘技巧文档（10 大类技巧，系统化发现 10+ 问题）
- `references/ANTI_PATTERNS_LIBRARY.md`：反例库文档（七大原则的常见反例，快速识别问题）
- `templates/B_ROUND_CHECK_TEMPLATE.md`：
  - 新增"🚨 挑衅性检查"（仅在第一个维度，其他维度待补充）
  - 新增"全局挑衅性检查"（6 大类挑战性问题）
  - 新增"技能评分系统"（百分制，7 个维度评分）
- `config.yaml`：
  - 新增 `test_rounds.min_suggestions_per_round: 10`（A 轮最小建议数量）
  - 新增 `test_rounds.target_suggestions_range: [15, 20]`（A 轮目标范围）
  - 新增 `b_round_check.min_suggestions: 10`（B 轮最小建议数量）
  - 新增 `b_round_check.constructive_suggestion_required: true`（强制建设性建议）
  - 新增 `b_round_check.p0_fix_rate_required: 100`（P0 修复率要求）
  - 新增 `b_round_check.p1_fix_rate_required: 80`（P1 修复率要求）

### Changed（变更）

- `SKILL.md`：
  - A.2 章节：新增"数量要求"（强制每轮至少 10 个问题，鼓励 15-20 个）
  - A.2 章节：新增"建设性"要求（引用 `references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md`）
  - A.4 章节：重构为"强制检查" + "进入下一轮条件"（数量门槛前置）
  - B.2 章节：新增"强制修复要求"（P0 必须修复，P1 高比例修复）
  - 完成条件：新增"每轮 A 轮平均问题数量 ≥ 10"和"B 轮 P0/P1 修复率"要求
  - 可复用资源：补充新增的 3 个 references/ 文件和 3 个 templates/ 文件
- `references/A_ROUND_PLAN_TEMPLATE.md`：
  - 新增"全局意识检查清单"（必填）
  - 新增"本轮的刁钻角度"（至少选择一个）

### Fixed（修复）

- 修复 SKILL.md 中"可复用资源"章节未列出新增 references 文件的问题
- 修复 A.4 节逻辑不一致的问题（强制检查现在前置）
- 修复"问题挖掘技巧"未强调的问题（现在标记为⚠️强烈建议）

---

## [2.0.4] - 2026-01-14

### Added（新增）

- B 轮质量检查新增第 7 个维度：**SKILL.md 瘦身检查**
  - 检查 SKILL.md 是否超过 300 行（建议阈值）
  - 检查是否存在可独立到 `references/` 的详细内容
  - 检查是否存在冗余的配置说明（应移至 `config.yaml` 注释）
  - 提供渐进披露原则的瘦身策略表（核心工作流→SKILL.md，详细模板→references/，技术细节→scripts/）
- `references/A_ROUND_PLAN_TEMPLATE.md`：A 轮优化计划结构模板（全局视图、与上轮关联、优先级定义、问题清单）
- `SKILL.md`：
  - A.2 章节新增"全局意识"、"上下文连贯"、"优先级依据"三大核心要求
  - 明确 P0/P1/P2 优先级判定标准（P0: 阻塞/安全/核心；P1: 重要优化；P2: 锦上添花）
  - 引用 `references/A_ROUND_PLAN_TEMPLATE.md` 作为详细结构模板
  - 更新"可复用资源"章节，新增模板与参考文档的分类列表
- `config.yaml`：新增 `b_round_check.mandatory: true` 配置项，明确 B 轮为强制环节（除非用户明确要求跳过）
  - A.4 章节增加强制提示："A 轮结束后（无论多少轮），必须进入 B 轮质量检查，不得跳过"
  - B 轮章节开头增加 ⚠️ 警告："B 轮质量检查是自动测试流程的强制性环节，除非用户明确要求跳过，否则不得省略"
  - 完成条件引用 `config.yaml` 的 `mandatory` 配置，形成配置-文档联动

### Changed（变更）

- B 轮质量检查从"六大原则"扩展为"七大原则"，新增 SKILL.md 瘦身检查维度
- `templates/B_ROUND_CHECK_TEMPLATE.md`：**重大重构** - 所有七大原则的检查说明更加详细和可操作
  - 每个原则新增"核心原则"一句话总结
  - 每个原则新增三级判断标准（✅ 良好 / ⚠️ 改进信号 / ❌ 严重问题）
  - 每个原则新增"典型反例"章节，包含具体代码/配置示例
  - 每个原则新增"改进方向"操作指南
  - 目标：让模型在执行 B 轮检查时更清晰理解每个原则的定义、判断标准和改进方向，避免歧义
- `SKILL.md` A.2 章节：从简略的"问题清单"要求，重构为结构化的"全局视图 + 上下文 + 优先级 + 可追溯性"框架，解决 A 轮计划可读性差、缺少全局意识的问题
- 版本号升级为 `2.0.4`（`config.yaml: skill_info.version` 同步到 `SKILL.md` YAML frontmatter）

## [2.0.1] - 2026-01-12

### Added（新增）

- `scripts/create_test_session.py`：
  - 新增 `--create-plan`（可选生成 `plans/` 计划文档骨架，默认不覆盖）
  - 新增 `--seed-test-plan-from-plan`（可选用计划文档初始化 `TEST_PLAN.md`）
- `templates/`：
  - 轻量化 `templates/TEST_REPORT_TEMPLATE.md`（结论/变更/证据/验证点/新问题）
  - 轻量化 `templates/OPTIMIZATION_PLAN_TEMPLATE.md`（位置/影响/修复/验证 + 执行步骤 + 测试引用）

### Changed（变更）

- 版本号升级为 `2.0.1`（`config.yaml: skill_info.version` 同步到 `SKILL.md` YAML frontmatter）。
- `templates/TEST_PLAN_TEMPLATE.md`：新增 `{{ROUND_KIND}}`，由脚本自动替换 A/B 轮。
- `scripts/create_test_session.py`：
  - CLI 错误输出改为 usage + 单行 `error:`（无 traceback）
  - `PLAN_DOC_PATH` 使用 `plans/...` 相对路径（更可移植）
- `auto-test-skill/SKILL.md`、`auto-test-skill/README.md`：补充脚本两种调用方式与 `--create-plan` 推荐用法；README 触发说明改为平台中立。

### Fixed（修复）

- B 轮报告模板中的 `{{A_TEST_ID}}` 不再被脚本默认替换为当前 B 轮 ID（避免产生“看似填写但实际错误”的追溯信息）。

## [2.0.0] - 2026-01-12

### Added（新增）

- 新增 `plans/` 与 `tests/` 的目录规范与多轮 A 轮 × N + B 轮工作流（六大质量原则）。
- 新增 B 轮质量检查模板：`templates/B_ROUND_CHECK_TEMPLATE.md`。
- 新增缺失模板：`templates/TEST_PLAN_TEMPLATE.md`、`templates/FINAL_SUMMARY_TEMPLATE.md`。
- 新增确定性辅助脚本：`scripts/create_test_session.py`（创建测试会话骨架）。
- 新增参考文档：`references/TESTING_BEST_PRACTICES.md`。

### Changed（变更）

- 更新 `auto-test-skill/config.yaml`：补充轮次、目录、B 轮检查维度与模板配置。
- 重构 `auto-test-skill/SKILL.md` 与 `auto-test-skill/README.md`：统一输出交付与目录命名为 `plans/` + `tests/`，并改为 A/B 轮工作流描述。
