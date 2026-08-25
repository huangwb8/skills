# auto-test-code - 变更日志

版本号以 `auto-test-code/config.yaml:skill_info.version` 为单一真相来源。

## [Unreleased]

### Added（新增）

- `references/SECURITY_TAXONOMY.md`：新增安全漏洞分类审查体系，将代码安全漏洞分类报告中的 CWE、OWASP、MITRE ATT&CK、STRIDE、七大王国、CVSS、供应链、配置、密码学、认证授权、DoS 与内存安全口径转化为可执行检查清单。

### Changed（变更）

- `config.yaml`：版本号升级为 `0.5.0`；A/B 轮新增 `security_vulnerability_analysis` 独立维度，并扩展 Dockerfile、CI/CD workflow、lockfile 等安全相关扫描模式。
- `SKILL.md` / `README.md` / `templates/` / `references/`：将安全漏洞分类审查纳入强制覆盖范围，B 轮从 8 大维度升级为 9 大维度，并同步更新优先级、刁钻角度、模板字段与参考资料说明。
- 通过 1 次 `auto-test-skill` 优化修复口径漂移：脚本默认填充 `SECURITY_COUNT`，语言检测跳过生成物/依赖目录，配置注释与 README 路径更新为真实字段，且默认排除范围不再跳过目标项目测试代码。

## [0.4.0] - 2026-04-04

### Added（新增）

- `references/DESIGN_ANTI_PATTERNS.md`：新增设计反模式识别指南，覆盖扩展性、架构、API、状态管理、领域建模、耦合/内聚、设计模式 7 类设计问题。
- `config.yaml`：A/B 轮维度新增 `design_quality`，将设计质量正式纳入审查范围。

### Changed（变更）

- `templates/B_ROUND_CODE_QUALITY_TEMPLATE.md`：B 轮质量检查升级为 8 大维度，新增“设计质量”评分与专门检查章节，并重分配评分权重保持总分 100。
- `references/CRITICAL_THINKING_FOR_CODE.md`：从三大思考框架升级为四大框架，补充设计质量视角与自问清单。
- `SKILL.md` / `README.md`：同步更新设计质量维度、B 轮 8 维度口径与参考资料说明。

## [0.3.0] - 2026-03-10

### Added（新增）

- `scripts/create_session.py`：新增 `--run-id` 与 `.auto-test-code-run.json` 运行清单，支持将一次 auto-test-code 执行的全部会话统一收口到 `tmp/run_*/tests/` 隔离工作区。

### Changed（变更）

- 默认工作区从项目根 `tests/` 调整为 `tmp/run_{timestamp}/tests/`，避免计划、报告、日志和中间产物泄露到源码项目其他位置。
- `scripts/verify_session.py`：新增对 `tmp/run_*/tests/` 布局的自动识别与隔离校验；旧布局仍可识别，但会提示不满足新的隔离规范。
- `config.yaml`：新增 `directories.tmp`，并将 `tmp/**` 加入默认排除列表，避免审查时把 skill 自身产物再次扫入。
- `SKILL.md` / `README.md` / `references/` / `templates/`：同步更新隔离工作区规则、脚本用法示例与路径口径。

## [0.2.0] - 2026-02-16

### Added（新增）

- `templates/SESSION_TEST_RUN_TEMPLATE.md`：新增“测试过程记录”模板，用于标准化沉淀测试过程（命令、关键输出摘录、关键决策与证据索引）。

### Changed（变更）

- 废弃 `reviews/` 输出目录：A/B 轮的计划/过程/结果统一沉淀到 `tests/{session}/` 会话目录（新增 `REVIEW.md` + `TEST_RUN.md` 并保留 `TEST_PLAN.md`/`TEST_REPORT.md`）。
- 会话命名规范：B 轮会话目录从 `tests/B轮-v*` 调整为 `tests/b-v*`（脚本兼容识别旧命名）。
- `scripts/create_session.py`：创建的骨架改为仅依赖 `tests/`，并在会话目录内生成 `REVIEW.md`/`TEST_RUN.md`。
- `scripts/verify_session.py`：验证逻辑调整为会话内 `REVIEW.md`；新增 `--strict`（仅在完成填写后用于占位符强校验）。
- `templates/`：将会话模板文件名从 `TEST_*_TEMPLATE.md` 重命名为 `SESSION_TEST_*_TEMPLATE.md`，避免与 `auto-test-skill` 的 `templates/TEST_PLAN_TEMPLATE.md`/`TEST_REPORT_TEMPLATE.md` 重名导致会话骨架误用与口径漂移。
- `templates/SESSION_TEST_PLAN_TEMPLATE.md` / `templates/SESSION_TEST_REPORT_TEMPLATE.md`：`**对应审查**` 字段改为引用 `REVIEW.md` 的相对路径，便于脚本一致性校验。
- `SKILL.md` / `README.md`：同步更新输出结构、命名规范与脚本用法示例（补齐 Codex/Claude Code 两种安装路径，并补充 `.auto-test-code/config.yaml` 项目级覆盖提示）。
