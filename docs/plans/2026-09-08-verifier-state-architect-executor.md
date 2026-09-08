# verifier-state-architect 设计与执行一体化

## 结论摘要

把目标 Skill 的默认交付从建议升级为经过验证的本地源码变更。计划仍在实施前形成，供 AI 连续执行和人类事后审查，不引入人工计划审批关卡。用户明确要求仅计划或只读审查时保留只读行为。

## 业务流程与风险地图

现有流程已覆盖业务理解、删除影响、AI/确定性分工及 Kernel 复用，但拒绝生成 Pack。新增源目录确认、托管规范核验、连续实现、实际执行验证与交付对账。不得修改系统级安装副本或自动扩大到 Kernel/远程变更；保留工作树中已有改动。

## 删除影响测试（含“不接入”结论）

保留零组件结论，不为设计者自身新增 State 或 Verifier。此次需要的是执行契约和只读机械验收工具，而非再建一层治理 Pack。

## Verifier 设计矩阵

目标 Skill 的专用命题仍由 AI 依据业务设计；新验收 helper 仅检查托管结构、加载与引用一致性，不冒充业务 Verifier，不给出语义通过结论。

## State 设计矩阵与最小状态图

本 Skill 使用普通顺序流程：读取 → 最小设计 → 保存计划 → 本地实现 → 验证 → 交付。没有新增持久状态恢复需求，不声明运行时 State。

## AI/确定性分工与 Evidence Contract

AI 判断删除影响、领域语义、复用与控制调用点；helper 复用 BSK 加载器核验索引、契约、声明及路径，并区分结构通过和未执行。证据保留相对来源、变更摘要、命令与结果，不归档原始私有输入。

## Kernel 对接、Gate、重放与资源边界

依据 `skills/alpha/verifier-state-architect/references/skill-pack-hosting.md` 与当前 Kernel 源码约束设计。托管在目标 Skill 的 `references/verifiers`、`references/states`，不虚构 `verifier_roots` 或专用 Verifier 的通用 CLI 自动发现能力。业务执行、Gate 与重放仍需目标 Skill 的真实执行证据。

## Kernel 复用与元 Verifier/State 提炼决策

### Kernel 复用结论

- 复用共享 Pack 加载器、ContractPack、Verifier/State 注册表和 Skill 声明加载器；不复制组件执行框架。
- 新 helper 只补托管规范严格检查，不改变运行时对历史格式的兼容行为。

### Kernel 元组件提炼结论

- 不新增 Kernel 元组件：该需求是 Skill 开发流程升级，没有跨领域运行时能力缺口的独立证据。
- 保持领域设计和项目规范在 Skill 层，避免将仓库治理规则强制加到所有 Kernel 消费者。

## 实施顺序（P0/P1/P2）

- P0：修改 `SKILL.md` 与 `config.yaml` 的模式、授权、连续实施、失败和完成边界；同步 `AGENTS.md` 的旧只规划条款。
- P1：增加安装后可读的执行参考和只读检查脚本；核验布局、元数据、真实加载接口；同步双语使用指南与变更记录。
- P2：用临时微型 Skill 覆盖正反例、复制后发现及失败路径，完成定向 Diff 审查并记录 BAC。不得为此安装覆盖系统副本。

## 验收与回归测试

目标 Skill strict 结构检查、双语指南一致性、helper 正反例、从异地工作目录运行复制后的 helper、源码缓存污染检查。AI 语义流程用行为用例逐条复核；没有运行完整模型评测时明确说明。

## 已知不确定性、回退方案和不在范围内的事项

通用脚本不能保证任意业务语义正确。没有宿主、Kernel 或授权源目录时报告受影响阻塞，不伪造完成；只回退本轮自身修改，不重置用户改动。当前未提交的托管规范是本次依据，保留不覆盖。本次不改 Kernel、不自动接入其它 Skill，也不发布或系统安装。

## 实施与验收对账

- P0 完成：目标 SKILL.md/config.yaml 已默认连续设计和执行，保留显式只读；AGENTS.md 只同步必要调用条款。
- P1 完成：references/implementation.md、scripts/check_integration.py、双语 README 与变更记录已交付；参考不依赖开发仓库绝对路径。
- P2 完成：31 个定向用例通过，包含复制发现、声明/路径拒绝、真实脚本正反例、Agent 待回传与依赖受阻。strict、双语指南、Ruff 和 Diff 检查通过；审查无遗留范围内问题。
- 环境偏差：已安装 Kernel 为 0.12.4，缺 ContractPack API；验证固定使用仓库 1.0.2 源码和 Python 3.12，不升级安装副本。用例脚本位于 `tmp/verifier-state-executor-20260908/test_integration.py`，通过 PYTHONPATH 选择仓库包。
- 证据入口：`.bensz-api/task-20260908-2307-verifier-state-executor/README.md`。未运行完整模型端到端评测，不宣称对任意领域的生成结果已获得实证保证。
