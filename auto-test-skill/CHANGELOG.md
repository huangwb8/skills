# auto-test-skill - 变更日志

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added（新增）

- `config.yaml`：新增 `b_round_check.mandatory: true` 配置项，明确 B 轮为强制环节（除非用户明确要求跳过）
- `SKILL.md`：
  - A.4 章节增加强制提示："A 轮结束后（无论多少轮），必须进入 B 轮质量检查，不得跳过"
  - B 轮章节开头增加 ⚠️ 警告："B 轮质量检查是自动测试流程的强制性环节，除非用户明确要求跳过，否则不得省略"
  - 完成条件引用 `config.yaml` 的 `mandatory` 配置，形成配置-文档联动

### Changed（变更）

- 版本号升级为 `2.0.2`（`config.yaml: skill_info.version` 同步到 `SKILL.md` YAML frontmatter）

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

