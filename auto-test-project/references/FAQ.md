# auto-test-project FAQ（常见问题）

本文件用于存放容易反复出现的问答与细节规则，避免 `SKILL.md` 过长。

## Q: 如何检测“假计划、空报告”？

优先使用验证脚本（推荐），并在需要时启用严格模式。

```bash
# 1) 快速检查：是否残留模板占位符（双大括号）
grep -r "{{" .bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/tests/vYYYYMMDDHHMM/

# 2) 验证脚本（推荐）
python3 auto-test-project/scripts/verify_test_session.py .bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/tests/vYYYYMMDDHHMM

# 3) 严格模式（推荐在收尾/回归阶段使用）
# - 要求 .bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/plans/vYYYYMMDDHHMM.md 存在
# - 要求 plan 内包含形如 "#### P0-1:" 的编号，才能做计划-报告一致性检查
python3 auto-test-project/scripts/verify_test_session.py --require-plan .bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/tests/vYYYYMMDDHHMM
```

## Q: 如果发现计划与执行脱节怎么办？

建议按以下顺序修复（从“可追溯性”到“可复现证据”）：

1. 重新阅读 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/plans/vYYYYMMDDHHMM.md` 的问题清单（确认每个问题都有编号，如 `P0-1`）。
2. 检查 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/tests/vYYYYMMDDHHMM/TEST_REPORT.md` 是否包含相同编号的修复记录。
3. 对缺失项补齐“修复前 → 修复措施 → 修复后 → 验证命令/输出”。
4. 重新运行验证脚本，直到通过。

## Q: TEST_REPORT.md 应该包含哪些证据？

证据优先级从高到低：

| 证据类型 | 示例 | 优先级 |
|---------|------|--------|
| 命令输出 | `git diff`、`pytest`、构建日志 | ⭐⭐⭐⭐⭐ |
| 文件引用 | `src/file.py:123`、截图路径 | ⭐⭐⭐⭐ |
| 对比结果 | 修复前后对比、通过率对比 | ⭐⭐⭐⭐ |
| 量化指标 | 覆盖率、耗时、规模变化 | ⭐⭐⭐ |
| 文字描述 | “已修复并验证正常” | ⭐⭐ |

## Q: 如何避免运行示例命令时污染项目根目录？

- 确认自己在“目标项目根目录”执行 `create_test_session.py`，不要在仓库根目录随手运行。
- 脚本会在 `--project-root` 下创建 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/plans/` 与 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/tests/`；默认拒绝将系统根目录或用户主目录作为 project-root，如需覆盖请显式使用 `--allow-unsafe-root`。
- 中间产物统一放进 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/tests/<session>/_artifacts/` 与 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-test-project/output/tests/<session>/_scripts/`，避免在项目根散落临时文件。

## Q: 项目类型识别失败怎么办？

- 手动在计划文档里声明项目类型与测试边界（例如“这是一个 Agent Skill/工作流项目/脚本工具集”）。
- 确保项目根目录存在至少一个项目指令文件（如 `CLAUDE.md`、`AGENTS.md`、`README.md`）。
- 如需更系统的识别规则，可参考 `config.yaml:project_detection` 的启发式配置。

## Q: 测试会话太多怎么办？

- 测试会话目录主要是文档与少量证据文件，通常建议保留以便追溯与复盘。
- 如果确需清理，推荐归档而不是删除：例如将早期会话移动到 `tests_archive/`（保留关键里程碑会话）。

## Q: 如何处理跨模块问题？

- 在计划文档中明确：受影响模块列表、依赖关系、预期连锁反应。
- 在 TEST_PLAN 中增加集成验证点（例如“修改 A 后，验证 B 的调用仍正常”）。
- 在 TEST_REPORT 中记录跨模块验证的命令与输出，避免只做描述性结论。

## Q: 项目级质量检查与 skill 级别有什么区别？

项目级质量检查更强调：

- 跨模块一致性（接口、命名、配置、文档）
- 架构层面的过度设计（模块边界、抽象层次、配置复杂度）
- 项目级安全风险（外部接口、依赖、路径与权限）
- 全局冗余与残留（重复逻辑、僵尸文件/引用）
