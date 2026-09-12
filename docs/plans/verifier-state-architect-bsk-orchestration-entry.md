# Verifier/State 设计计划：verifier-state-architect 的 BSK 编排入口约束

## 结论摘要

当目标 Agent Skill 明确同时使用 BSK 管理领域 State 与 required Verifier 时，`verifier-state-architect` 必须把“Skill 自有的单一编排入口”作为 P0 交付，而不是只生成 Pack、配置和说明。入口统一完成 action → State 映射、当前 State 读取、Verifier 请求准备、全部 required Verifier 执行与 Gate、Gate 放行后的 State transition，以及 BSK 返回结构与绑定的严格校验；任一步不确定或失败均 fail-closed。

本次不为 `verifier-state-architect` 自身新增 State/Verifier Pack，也不修改 BSK。领域 action 映射和命令入口属于目标 Skill，BSK 继续只提供通用加载、执行、Gate、事件与迁移 API。

## 业务流程与风险地图

当前流程能要求 Pack、`runtime` 声明和业务调用点，却没有把多次 BSK 调用收敛成唯一入口。Agent 可能绕过 State 读取、漏跑 required Verifier、自己拼 Gate、在非放行结果下迁移，或只凭退出码/文件存在就继续交付。

目标流程为：解析 action → 从目标 Skill 配置取得 from/to State 映射与 required Verifier → 通过固定版本 BSK 公共 API 读取当前 State → 规范化一次请求和运行身份 → 执行并记录全部 required Verifier → 使用 BSK 生成/记录 Gate → 仅在明确放行且绑定完整时调用 BSK transition → 校验 transition 回执与新快照 → 返回稳定结果。`SKILL.md` 必须把该命令声明为 Agent 正常执行受控 action 的唯一入口。

## 删除影响测试（含“不接入”结论）

- 删除单一编排入口后，Agent 可以分别调用业务命令和 BSK 子步骤，无法机械保证 required Verifier 完整性、Gate 绑定和 transition 顺序；因此在 State + required Verifier 场景不可删除。
- 删除 action → State 映射后，Kernel 必须理解领域 action 或 Agent 临时推断 State，都会破坏领域/Kernel 边界；因此映射必须由目标 Skill 托管。
- 目标只使用 State、只使用 advisory Verifier、只使用 Verifier或删除影响为零时，本约束不适用；不得为满足检查器创建虚假编排入口。

## Verifier 设计矩阵

| 候选 | 保留/删除 | 稳定命题或状态含义 | AI/脚本分工 | 输入与证据 | Gate/转移 | 失败与人工复核 |
| --- | --- | --- | --- | --- | --- | --- |
| required Verifier 调度 | 保留 | 当前 action 所需的全部 required Verifier 均已执行并绑定到本次 run/attempt | 入口机械枚举声明、准备请求、调用和校验；语义组件仍按契约执行 | subject/context/evidence、run/attempt、结果引用 | 只接受 BSK 对完整 required 集合的放行 Gate | 缺失、未完成、错版本、错绑定或不确定均不迁移 |
| 编排入口自检 | 不提升为 Verifier | 这是接入结构与执行路径约束，不是独立领域验证命题 | `check_integration.py` 检查声明与入口文件；行为测试检查调用顺序和 fail-closed | 目标配置、入口、测试回执 | 不产生业务 Gate | 结构通过仍标记执行未验证 |

## State 设计矩阵与最小状态图

| 候选 | 保留/删除 | 稳定命题或状态含义 | AI/脚本分工 | 输入与证据 | Gate/转移 | 失败与人工复核 |
| --- | --- | --- | --- | --- | --- | --- |
| action → from/to State 映射 | 保留 | 每个受控 action 只在声明的当前 State 进入声明的目标 State | 目标 Skill 配置维护映射；入口机械解析并核对当前快照 | action、当前 State/版本、目标 State | Gate 放行后才提交 BSK transition | 未知 action、State 不匹配、非法边均拒绝 |
| Architect 自身运行 State | 删除 | 本次只是强化设计/实施流程，无持久恢复收益 | 普通任务工作区和计划对账足够 | 不适用 | 不适用 | 不生成占位 Pack |

最小状态图由每个目标 Skill 的领域流程决定；本次只固定每条受控 action 的 `current_state → [required Verifier + Gate] → target_state` 原子顺序，不增加通用领域节点。

## AI/确定性分工与 Evidence Contract

- AI：判断哪些 action 需要控制、action 的领域 from/to State、证据语义、人工复核路径和业务恢复建议。
- 确定性入口：从配置读取 action 映射与 required Verifier；调用 BSK 公共 API；核对 protocol、操作、canonical ID/version、run/attempt、结果集合、Gate decision/result refs、transition 结果与新快照；禁止根据自然语言消息或进程退出码推断放行。
- Evidence Contract：每次编排至少绑定 action、Skill、current/target State、State 版本、request/run/attempt、required Verifier ID/version、结果引用、Gate 和 transition 回执。原始私密上下文不进入日志。

## Kernel 对接、Gate、重放与资源边界

- 使用目标 `runtime.kernel` 精确版本的 BSK CLI 或 Python API；不得混用仓库源码、PATH 旧命令或未核对版本。
- required 集合从 `runtime.verifiers` 的 `required: true` 声明得出，不在入口复制第二份清单。请求统一携带本次 run/attempt 和证据锚点。
- Gate 必须由 BSK 基于本次完整结果生成并记录。只有明确允许继续、required 全部通过且结果引用/身份绑定一致时才迁移；`reject/wait/manual_review`、错误、超时、`uncertain/unchecked` 或未知值均 fail-closed。
- transition 仍由 BSK 校验状态图与 invariant；入口还要核对回执的新 State/版本/快照确为目标。事件和快照按 BSK 协议重放，不能复用较早阶段或其它 attempt 的 Gate。
- 入口限制路径、输入体积、超时、环境与日志；使用结构化稳定字段和原因码，不解析自然语言错误文本。若目标 action 还需阶段内单次授权，按实际 BSK 版本评估 action preflight/consume，但不把它误写为本次七项基础契约的替代品。

## BSK 单一编排入口（适用时）

- 目标 `runtime.orchestration` 只声明一个 Skill 内 `scripts/` 入口和 action 的 current/target 领域 State；required Verifier 继续从 `runtime.verifiers` 解析。
- 目标 `## 控制` 把该命令设为正常唯一路径，入口按“读 State → 准备请求 → required Verifier → BSK Gate → allow 后 transition → 严格回执检查”执行。结构检查之外还必须保留成功与 fail-closed 行为证据。

## Kernel 复用与元 Verifier/State 提炼决策

### Kernel 复用结论

- 直接复用 BSK 2.1.0 的 Skill 声明加载、Verifier 执行与 Gate、State transition、事件/快照和稳定协议字段；这些能力与所需顺序契合，目标 Skill 不应复制 reducer 或 Gate 算法。
- 通过 Skill 自有适配入口组合这些 API；组合成本是维护 action 映射和请求适配，但能保留领域边界，并把 Agent 的多步自由调用收敛为一条命令。

### Kernel 元组件提炼结论

- 明确不把 action → State 映射或目标命令入口提升到 Kernel：删除具体目标 Skill 后它们失去主要含义，并需要知道领域 action 与证据。
- 暂不新增通用 Kernel orchestrator：现有 API 已覆盖底层能力，目前证据只证明 Architect 应强制目标 Skill 组合调用，尚无两个不相邻领域共享同一 action/request 适配契约的证据。

### 对人类决策的影响

- 采纳后会修改 `verifier-state-architect` 的工作契约、托管/落地参考、检查器、配置、双语 README 和 CHANGELOG；以后相关目标 Skill 需增加一个实际可运行的入口和机器可读 action 映射。
- 不采纳则 Pack 可加载仍无法证明 Agent 不绕过控制链；人类必须逐次审查调用日志，漏跑 State/Verifier 的风险保持不变。

| 候选能力 | 现有 Kernel ID/版本 | 复用方式 | 契约差异 | 是否跨领域 | 提炼建议 | 主要理由 | 验证动作 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 声明、Verifier、Gate、transition | `bensz-skill-kernel@2.1.0` 公共 API | 组合复用 | 需要目标 Skill 补 action/request 适配 | 是（底层） | 不新增 Kernel 能力 | Kernel 已提供领域无关原语 | 对照 CLI/Python API、运行正反例 |
| action → State 编排入口 | 无通用 ID | Skill 适配 | 依赖领域 action、State 与证据 | 否（上层） | 留在目标 Skill | 删除目标 Skill 后失去语义 | 静态声明检查 + 行为测试 |

## 实施顺序（P0/P1/P2）

- P0：在 `SKILL.md` 和 `references/skill-pack-hosting.md` 写入不可绕过的单一编排入口、七项职责、唯一正常调用路径和 fail-closed 完成条件；在 `references/implementation.md` 给出精简实施与测试清单。
- P1：在 `config.yaml:planning.required_plan_sections` 增加编排入口章节并升级版本；增强 `scripts/check_integration.py`，当目标同时声明领域 State 与 required Verifier 时检查 `runtime.orchestration.entrypoint/actions`、入口路径和 State 映射，报告静态通过但执行未验证。
- P1：同步中英文 README 与 CHANGELOG；建立任务对账和 BAC 记录。
- P2：用临时目标 Skill 覆盖适用/不适用、缺入口、越界入口、未知 State、合格声明；执行 strict 结构检查、Ruff、链接/双语一致性和缓存污染检查。
- P2：按用户要求运行一次 `auto-test-skill` A 轮及强制 B 轮，闭环问题后再运行 `compact-bensz-skills` 压缩工作型 Markdown，最后重复所有关键验证。

## 验收与回归测试

- 静态检查：适用场景缺 `runtime.orchestration`、缺/越界入口、空 action、from/to State 非法时失败；仅 State、仅 Verifier、无 required Verifier 时不强制生成入口。
- 行为契约：至少覆盖未知 action、当前 State 不匹配、required 缺失/失败/未完成、Gate 非放行、Gate 错 run/attempt/result refs、transition 拒绝、回执目标不一致和成功路径。
- 文档：固定正文骨架、公共约束哈希、README/README_EN 语义一致、链接有效；版本只在 `config.yaml`。
- 环境：Python 3.12、BSK 2.1.0；`PYTHONPATH` 显式固定仓库源码进行源态测试，不覆盖系统安装副本；缓存写入 `.bensz-api/`。
- Auto-test：A 轮至少 10 个问题、P0+P1 ≥ 60%、系统性问题 ≥ 3，并完成 B 轮；所有问题有修复或不修复理由与证据。
- 压缩：工作型 Markdown 总量下降，七项职责、适用条件、唯一入口和 fail-closed 语义逐项保留。

## 已知不确定性、回退方案和不在范围内的事项

- BSK 不会拦截完全绕过入口的宿主；本 Skill 通过目标 `SKILL.md` 唯一入口约束、机器可读声明和执行证据降低误用，不能冒充 OS 沙箱。
- 静态检查不能证明入口真实调用顺序或业务语义；必须保留行为测试证据，未运行时标记 `unchecked`。
- 本次不修改 BSK、其它业务 Skill、系统安装副本或远程状态；工作树中已有 Kernel 改动全部保留。
- 若压缩造成语义丢失或未形成净缩减，恢复压缩前快照并交付未压缩的已验证版本；不撤销用户既存改动。

## 实施与验收对账

- P0 契约：`SKILL.md`、`references/bsk-orchestration.md` 和托管规范已把七项职责、唯一正常入口与 fail-closed 设为组合场景强制条件。
- P1 静态门禁：`scripts/check_integration.py` 检查 `runtime.orchestration`、Skill 内入口、真实 `## 控制`、action 映射、领域 State 与合法静态边；结果仍标记执行 `unchecked`。
- 文档与版本：`config.yaml` 升级至 0.4.0；中英文 README、CHANGELOG 和实现参考已同步。
- Auto-test：A 轮 10 项、B 轮 10 项均闭环；12 个正反例覆盖缺/孤立声明、路径、action、State、Control fence 与不适用场景。
- 压缩：5 个工作型 Markdown 的统计词数从 11,975 降至 10,852（-1,123，约 9.4%），0 个校验错误；外置工作区警告源于仓库统一任务目录策略。
- 不在范围：未修改 BSK 或其它业务 Skill，未覆盖系统安装副本，未运行任意真实业务 Skill 的模型端到端编排。
