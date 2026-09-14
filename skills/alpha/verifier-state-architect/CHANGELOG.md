# Changelog

## [Unreleased]

### Fixed（修复）
- 升级至 `0.4.1`，集成检查按 BSK 统一的最低版本/capability 契约验证目标 Skill，不再要求声明版本与当前 Kernel 精确相等。
- 同步 verifier-only 集成测试到当前 orchestration 报告契约，避免旧 scope/缺字段断言造成假失败。

### Added（新增）
- 当目标 Skill 同时采用 BSK State 与 required Verifier 时，强制交付 Skill 自有的单一编排命令，统一 action → State、状态读取、请求准备、required Verifier、Gate、放行后 transition 与严格返回校验；失败默认关闭。
- 新增 `runtime.orchestration` 的最小声明与静态检查，缺入口、越界路径、空 action 或未声明 State 映射会拒绝；静态通过仍明确标记执行未验证。

### Changed（变更）
- 当前托管与检查契约已用 BSK 2.1.0 验证：Skill 专用 Verifier 可通过 `runtime.verifier_roots` 声明，并由 CLI 的显式 `--skill-root`/`--root` 与完整 JSON 请求入口发现和执行；仍禁止任意全局扫描和把“已发现”冒充“已执行”。

### Added（新增）
- 新增随 Skill 安装的落地参考与只读 `scripts/check_integration.py`，核验专用 Pack 托管、索引/契约分工和真实 Kernel 加载；结构通过不冒充组件已执行。
- 补齐中英文对齐的使用指南，说明默认落地、显式只读、事后审查和执行证据边界。

### Changed（变更）
- 托管规范集中到 `references/skill-pack-hosting.md` 唯一维护，合并落地参考中的重复规则；项目治理、教程和 Skill 入口统一引用，安装后的规范不依赖开发仓库外部文档路径。
- 默认从只规划升级为“设计 → 保存计划 → 本地实现 → 验证”，不等待人工审批计划；保留显式 `plan-only` / `review-only`，计划持久保存在 `docs/plans/`。
- 专用组件按目标 Skill 标准目录托管，明确 Verifier-only、宿主回传、版本/alias、失败恢复及复制后验证；不默认修改 Kernel 或安装副本。
- 保留已规范化的正文骨架、公共约束和既有删除影响/Kernel 两层审查规则，在原有设计能力之上增加执行闭环。

### Validation（验证）
- 本轮 `auto-test-skill` 完成 1 个 A 轮（10 项问题）及强制 B 轮（10 项建议），12 个编排声明正反例、strict 结构、Ruff、相对链接和复制后检查通过；`compact-bensz-skills` 在保持 BSK 七步强制闭环的前提下减少 1,123 个工作型 Markdown 词（约 9.4%）。
- Python 3.12 与仓库 Kernel 源码环境通过 31 个定向用例，覆盖零组件、单类/双类组件、标准布局、索引/声明拒绝、alias、越界、复制后发现、脚本成功/失败与 Agent 待回传；未进行完整模型端到端评测。
- Skill strict 结构检查、双语指南检查、Ruff 与 Diff 空白检查通过；旧版已安装 Kernel 缺 API 时返回受阻，不自动改动系统环境。

## [0.2.1] - 2026-08-31

### Changed（变更）
- 压缩 `SKILL.md` 的重复说明，保持触发语义、输入输出、Kernel 复用/元组件审查、安全边界与计划契约不变。

## [0.2.0] - 2026-08-31

### Changed（变更）
- 补充 Kernel 二层架构审查：要求先盘点并论证现有 Verifier/State 的直接、组合或适配复用，再评估跨领域元组件提炼机会。
- 强制最终设计计划设置独立章节，以分点理由同时记录 Kernel 复用结论、元 Verifier/State 提炼结论及其对人类实现决策的影响。

## [0.1.0] - 2026-08-31

### Added（新增）
- 初始化 `verifier-state-architect` beta Skill：通过业务理解、删除影响测试、AI/确定性分工和 Kernel 契约映射，生成 Verifier/State 设计计划。
