# Verifier/State 设计计划：Minimum Sufficient Complexity

## 结论摘要

- 建议新增一个 Kernel 内置的通用语义 Verifier，暂定 canonical ID 为 `bensz.design.minimum-sufficient-complexity`，版本 `1.0.0`。
- 不直接验证不可操作的“优雅感”，而验证一个可反驳的稳定命题：在当前目标、约束和不变量下，是否存在一个具体的、更简单的替代方案，在不损失必要能力的前提下严格降低至少一种复杂度成本，且不增加其它重要成本。
- “简单”不等于行数少、章节少或抽象少。复杂度至少包括概念实体、间接层、重复真相源、特殊分支、认知成本、运行成本和维护成本；采用 Pareto 支配判断，不设置跨领域的总分或硬阈值。
- 首版只使用一个 required `agent` 组件，不添加脚本、State、人类组件或中央 Kernel 分发逻辑。具体 Skill 决定该 Verifier 是 required 还是 advisory；建议先 advisory 校准，再在高代价设计冻结点按需设为 required。
- 本计划仅设计，不修改 `VERIFIER.md`、索引、Kernel 源码或测试。

## 业务流程与风险地图

### 服务对象

该 Verifier 面向持续时间较长、设计会积累维护成本的 Agent 工作，例如文章写作、软件开发、Agent Skill 设计和项目治理。它在稳定检查点审查当前产物或设计决策，而不是在每个生成步骤后触发。

推荐调用点：

1. 目标、必需能力、约束和不变量已经明确。
2. 已形成可比较的稳定草案、架构或变更集。
3. 在进入交付前，或在难以回滚的架构决定生效前进行一次检查。
4. 若发现可行动的更简方案，回到 `active` 修正；若证据不足或存在真实权衡，进入人工复核或保留 advisory 警告。

### 主要风险

| 风险 | 失败表现 | 设计控制 |
| --- | --- | --- |
| 审美冒充证据 | 仅说“不够优雅”便判失败 | `fail` 必须给出具体替代方案及约束等价性证据 |
| 把短小当简单 | 压缩代码或文字后更晦涩、更脆弱 | 同时比较认知、运行、维护和特殊情况成本 |
| 破坏必要复杂度 | 为简洁删除安全、兼容、审计或证据边界 | 正确性、必要能力和不变量优先；未证明保持时不得建议删除 |
| 为未来过度优化 | 用臆测的扩展需求支撑抽象 | 只接受当前需求或有证据的近程变化场景 |
| 无限重构 | 每轮都产生新的风格偏好 | 只报告 material finding；迁移成本不低于收益时不判失败 |
| 跨领域硬编码 | 把类、函数、章节数写成统一阈值 | 契约使用“设计实体”和相对成本，领域 Adapter 提供事实 |
| 自评偏差 | 生成者证明自己的方案最好 | 结果必须引用独立快照；高风险场景可由宿主安排独立 Agent 或人类复核，但不写入 Kernel 调度 |

## 删除影响测试（含“不接入”结论）

### 建议保留 Verifier

- 删除后，现有文件存在、Schema、diff、任务完整性等 Verifier 仍只能证明“产物存在且形状正确”，不能证明新增抽象、重复真相源或论证层级是否必要。
- 它会改变下一步决策：具体且占优的简化方案导致 `fail`/返工，证据不足导致 `uncertain`/人工复核，无实质问题才允许 `pass`。
- 软件、文章与 Skill 设计共享“复杂度必须由现实约束证明”的命题，因此具备 Kernel 内置基础能力的跨领域价值。

### 不新增 State

- “正在追求简洁”不是持续业务阶段；删除这个假想 State 不损失恢复、协作、Gate 或审计能力。
- 现有 `active → checking → delivering` 已能表达产出、审查和交付。简洁性检查只是 `checking` 中的一个验证命题。

### 不新增确定性脚本

- 通用脚本无法可靠判断一个章节、抽象层或配置项是否必要；用数量阈值代替语义会制造高误报。
- 文件清单、diff、Schema、路径和事件等机械事实已经有内置 Verifier，可由消费 Skill 组合使用，无需在本 Pack 重复实现。

## Verifier 设计矩阵

| 候选 | 保留/删除 | 稳定命题或状态含义 | AI/脚本分工 | 输入与证据 | Gate/转移 | 失败与人工复核 |
| --- | --- | --- | --- | --- | --- | --- |
| `bensz.design.minimum-sufficient-complexity` | 保留 | 不存在已被证据证明、在同一约束下严格更简单的可行替代方案 | 单个 Agent 作语义比较；无专属脚本 | 目标、范围、必需能力、不变量、约束、产物快照、设计理由、候选替代 | 初期 advisory；高代价设计冻结点可由 Skill 声明 required | 有具体占优替代时 `fail`；真实权衡或证据缺失时 `uncertain`；未执行为 `unchecked` |
| “elegance score” | 删除 | 无稳定跨领域标尺 | 会退化成模型偏好评分 | 难以形成可审计证据 | 分数阈值会误阻塞 | 无法可靠校准 |
| “simplicity” State | 删除 | 是一次判断而非持续阶段 | 无必要执行逻辑 | 无独立状态证据 | 复用 `checking` | 不适用 |
| 指标统计脚本 | 暂不接入 | 行数、模块数、章节数并不等价于复杂度 | 可由领域 Adapter 日后提供辅助 facts | 需要语言/格式特定解析 | 不单独 Gate | 先收集校准数据再评估 |

### 暂定索引元数据

```json
{
  "directory": "minimum-sufficient-complexity",
  "id": "bensz.design.minimum-sufficient-complexity",
  "version": "1.0.0",
  "classification": "semantic",
  "tags": ["common", "design", "simplicity", "semantic"],
  "capabilities": [
    "design.complexity-justification",
    "design.simpler-alternative-comparison"
  ],
  "evidence_requirements": [
    "objective-and-scope",
    "current-constraints",
    "artifact-or-design-snapshot"
  ],
  "uncertainty_policy": {
    "missing_evidence": "wait",
    "unresolved_tradeoff": "manual_review",
    "engine_unavailable": "unchecked"
  },
  "contract": "VERIFIER.md",
  "entrypoint": null,
  "mode": "prompt",
  "assurance_tier": "llm_judge",
  "components": [
    {
      "id": "complexity-necessity-review",
      "type": "agent",
      "required": true,
      "assurance": "llm_judge",
      "side_effects": "none"
    }
  ]
}
```

ID 不使用 `quality-check` 或 `elegance`：前者过宽，后者不可复核；`minimum-sufficient-complexity` 直接表达“满足必要约束后的相对最小复杂度”。

## State 设计矩阵与最小状态图

| 候选 | 保留/删除 | 理由 |
| --- | --- | --- |
| 新领域 State | 删除 | 没有独立的持续阶段、恢复语义或专属不变量 |
| `bensz.runtime.checking` | 直接复用 | Verifier 在稳定产物形成后执行，并记录 result 与 Gate |
| `bensz.runtime.active` | 直接复用 | 有可行动 finding 时返回此状态修正 |
| `bensz.runtime.waiting` | 直接复用 | required 检查证据不足或需要人类裁决时使用 |
| `bensz.runtime.delivering` | 直接复用 | required Gate 允许或 advisory 检查完成后进入交付 |

```text
active → checking ── pass / advisory warning ─→ delivering
   ↑         │
   └─ fail ──┘
             └─ uncertain / missing evidence ─→ waiting
```

## AI/确定性分工与 Evidence Contract

### 确定性边界

Kernel 继续负责 Pack 发现、ID/版本、契约与组件哈希、`run_id`/`attempt_id`、handoff 绑定、输出枚举、超时、结果归一化、Gate、事件和重放。现有 artifact、diff、Schema、secret、evidence provenance 和 event integrity Verifier 可按消费方需要组合提供机械证据。

### Agent 语义判断

Agent 只回答以下问题：

1. 当前有哪些显著的“设计实体”：模块、抽象、配置、规则、章节、术语、论证步骤或流程节点？
2. 每个显著实体服务于哪个当前需求、约束、不变量或已有证据支持的变化场景？
3. 是否存在一个具体替代方案，保持同一必要能力和边界？
4. 替代方案是否在概念实体、间接层、重复、特殊分支、认知、运行和维护成本上 Pareto 支配当前方案？
5. 简化收益是否大于迁移、兼容和回归风险？

不得仅凭“更短”“更少文件”“我更喜欢”判定更简单。不得奖励牺牲正确性、安全性、可读性、证据链或必要扩展点的表面压缩。

### 请求契约

`subject` 建议包含：

- `artifact_kind`：如 `software`、`article`、`skill`、`plan`；只用于解释，不改变判定枚举。
- `scope`：本次审查的明确边界。
- `snapshot` 或可读取的受限快照引用；大产物应由 Adapter 提供必要摘录和结构摘要。
- `design_decisions`：可选，列出关键实体及其理由；缺失时不得臆造作者意图。

`context` 建议包含：

- `objective`、`required_capabilities`、`invariants`、`constraints`。
- `accepted_tradeoffs`：已经明确接受且有证据的权衡。
- `change_scenarios`：仅包含已有需求或可引用证据支持的近程变化，不接受“未来也许需要”。
- `materiality`：由消费 Skill 描述什么会显著影响理解、维护、运行或演化；首版不设 Kernel 数值阈值。

`evidence` 至少应锚定目标与范围、当前约束、产物或设计快照，并提供 `ref`、`source_type`、`content_hash`、`collected_at` 或协议允许的等价审计信息。完整内容不写入事件账本；handoff 使用受限摘要或 subject/context 中的最小必要快照。

### 结果契约

- `pass`：在给定证据和范围内，未发现 material 的占优替代方案；这不是“全局最优”证明。
- `fail`：至少一个 finding 给出当前实体、它声称服务的约束、具体替代方案、约束保持证据、成本降低及迁移风险；缺任一关键项不得 fail。
- `uncertain`：存在合理简化候选，但约束保持、收益或风险无法从当前证据确定，或不同复杂度维度存在不可消解权衡。
- `unchecked`：没有绑定的 Agent 结果、必要快照不可用或执行引擎不可用。
- `error`/`timed_out`：协议、执行或资源失败，不能转写为 pass。

建议 `facts` 包含 `essential_complexity`、`incidental_complexity`、`tradeoffs`、`simpler_alternatives` 和 `scope_reviewed`。建议 finding 使用少量稳定类别：`unjustified-entity`、`dominated-design`、`duplicate-source-of-truth`、`premature-generality`、`avoidable-indirection`。类别只是解释标签，`fail` 仍由完整反例证据决定。

## Kernel 对接、Gate、重放与资源边界

- 新 Pack 放在 `packages/bensz-skill-kernel/src/bensz_skill_kernel/verifiers/minimum-sufficient-complexity/`，只含 `VERIFIER.md`；元数据只写入相邻集合的 `index.json`。
- 复用 `ContractPackExecutor` 的 Agent handoff，不新增中央 dispatcher。未收到绑定 submission 时保持 `unchecked`，required Gate 为 `wait`。
- `run_id`、`attempt_id`、contract/component/plan hash 和 evidence refs 必须随结果绑定；错绑、漏绑或旧轮次结果不能支持当前 Gate。
- Pack 不声明全局 required。消费 Skill 在 `config.yaml.runtime.verifiers` 中决定 required/advisory。
- 推荐发布策略：第一阶段只 advisory；收集跨文章、软件、Skill 的校准案例并复核误报。只有在具体 Skill 能稳定提供目标、约束和快照时，才把它设为 required。
- required `fail` 应返回 `active` 修正或在不可恢复时 `failed`；required `uncertain` 进入 `manual_review`/`waiting`；advisory 非 pass 只产生警告。
- Agent 组件无文件、网络或写入副作用。宿主若需要加载大文件，应先做范围限制、大小上限和脱敏摘要，不能把整个仓库或完整私有材料写入 handoff/账本。
- 同一稳定检查点最多执行一次；只有目标、约束或产物快照哈希变化后才重新执行，防止风格循环。

## Kernel 复用与元 Verifier/State 提炼决策

### 现有 Kernel 能力盘点

已核对 Kernel `1.1.0` 的 `verifiers/index.json`、`states/index.json`、README、语义引用 Verifier、Gate 与 Contract Pack 执行协议。相关候选如下：

| 候选能力 | 现有 Kernel ID/版本 | 复用方式 | 契约差异 | 是否跨领域 | 提炼建议 | 主要理由 | 验证动作 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 语义 Agent handoff | `bensz.evidence.citation-truth-fit@1.0.0` 的执行形态 | 组合复用底层，不复用其命题 | 引用身份/蕴含不等于复杂度必要性 | 是 | 复用 Contract Pack 协议 | 已覆盖 agent、unchecked、证据绑定 | 仿照语义 Pack 做 pending/回传/错绑测试 |
| diff 范围 | `bensz.source.diff-scope@1.0.0` | 组合复用 | 只能证明改动路径在范围内 | 是 | 不扩展 | 可提供审查范围，不能判断设计是否必要 | 组合测试但保持独立 verdict |
| 契约/Schema | `bensz.contract.conformance@1.0.0`、`bensz.artifact.schema-conformance@1.0.0` | 组合复用 | 只检查字段存在 | 是 | 不扩展 | 可保证输入形状，不能判断语义 | 缺字段和空要求测试 |
| 任务完整性 | `bensz.runtime.task-completeness@1.0.0` | 不适用作替代 | 完整不等于简洁 | 是 | 不扩展 | 目标命题正交 | 验证两者可独立 pass/fail |
| 最小充分复杂度 | 无 | 新增基础语义 Pack | 新的稳定比较命题 | 是：文章、软件、Skill/项目治理 | 推荐提炼 | 多领域共享，且现有 Pack 无法表达 | 跨领域校准集与 Gate 测试 |

### Kernel 复用结论

- 直接复用内置生命周期状态和 Gate：契约完全覆盖“检查—修正—等待—交付”，新增 State 只会增加标签和迁移成本。
- 复用 Contract Pack 的单 Agent handoff、哈希和运行身份绑定：执行协议一致，新增执行器没有收益，反而会产生双重结果模型。
- 不复用 `task-completeness`、`contract-conformance` 或 `schema-conformance` 作为本 Verifier 的替代：它们只验证存在性/形状，无法给出“复杂度有无必要”的反例。
- 可与 `diff-scope`、`evidence-provenance` 等组合，但不把它们塞进本 Pack：保持 verdict 正交，避免一个语义 Pack重复执行现有机械检查。

### Kernel 元组件提炼结论

- 推荐将 `minimum-sufficient-complexity` 提炼为 Kernel 内置基础 Verifier：用户明确要求覆盖文章与软件，仓库现有 `init-project` 又将 KISS、YAGNI、DRY、奥卡姆剃刀和“正确性 > 简洁性 > 清晰性 > 扩展性”作为通用项目原则，已有至少三个不相邻使用域。
- 命题可独立版本化：它比较当前约束下的复杂度必要性，不依赖具体 Skill 名、模型、文件格式或固定阈值；不同领域只需提供 Adapter/证据。
- 不把具体反模式列表、行数/章节数阈值或语言规则提升进 Kernel：这些内容领域耦合、易变且会制造误报，应留在领域 Skill、Adapter 或校准案例中。
- 首版仍有模型一致性风险，因此采用 semantic/LLM judge、保留 `uncertain` 和人工复核，并先 advisory 校准；不能把“Kernel 内置”误解为“全局强制”。

### 对人类决策的影响

- 采纳后需要新增一个 Pack 目录、一个索引条目、对应 Kernel 单元测试，并更新包 README/CHANGELOG/BAC；不修改公共 Python API、CLI 参数或 reducer。
- 消费 Skill 若设为 advisory，只增加检查结果和警告，不改变完成兼容性；设为 required 会新增 `wait`、`manual_review` 或 `reject` 路径，必须同步说明证据输入和人工介入责任。
- 不采纳则保留现状，由各 Skill 在自然语言审查中自行执行 KISS/YAGNI；代价是结果无法统一绑定证据、Gate 和事件重放，跨任务口径更易漂移。
- 维护责任由 Kernel 维护者承担通用契约和校准集；领域团队只维护输入 Adapter 与领域证据，不应向 Kernel 追加特定语言或文体规则。

## 实施顺序（P0/P1/P2）

### P0：建立不会误判的语义契约

- 文件：`packages/bensz-skill-kernel/src/bensz_skill_kernel/verifiers/minimum-sufficient-complexity/VERIFIER.md`
- 内容：按五段骨架定义稳定命题、证据、Pareto 比较、判定、反例格式和非目标。
- 完成条件：没有“更优雅”“分数低于阈值”等不可审计规则；`fail` 必须包含具体占优替代及约束保持证据。

### P1：注册与协议验证

- 文件：`packages/bensz-skill-kernel/src/bensz_skill_kernel/verifiers/index.json`
- 内容：加入上述 semantic/agent 条目，不修改中央 Registry 或 reducer。
- 测试：扩展 `packages/bensz-skill-kernel/tests/runtime/test_verifiers.py`，覆盖发现、describe、pending handoff、绑定回传、缺证据、错 run/attempt/contract/component hash、各 verdict 的 Gate。
- 完成条件：安装前后均可发现；未执行/缺证据不 pass；required 与 advisory 行为符合 Kernel 现有语义。

### P1：跨领域校准

- 位置：包内测试 fixture 或项目约定的 `tmp/` 测试输入，不把运行产物放入 Pack。
- 最少案例：单实现却预建多层工厂的软件设计、必要的安全/兼容层、文章重复论证、文章必要的方法细节、重复真相源、证据不足的真实权衡。
- 完成条件：明确反例稳定 fail；必要复杂度 pass；有权衡或缺约束 uncertain；两名人类复核者对 material findings 的方向性结论达到可接受一致度。

### P2：消费方接入

- 先在一个软件 Skill 和一个写作 Skill 中以 advisory 使用，记录误报、漏报和人工改判原因。
- 稳定后才考虑在难回滚、高维护成本的设计冻结点设为 required；普通局部任务不默认执行。
- 不在首版加入指标脚本、多 Agent 调度、复杂度分数或新 State。

建议验证命令（实现阶段使用 Python 3.11+ 环境）：

```bash
PYTHONPYCACHEPREFIX=.bensz-api/pycache \
python3.11 -m pytest packages/bensz-skill-kernel/tests/runtime/test_verifiers.py \
  -o cache_dir=.bensz-api/.pytest_cache

PYTHONPYCACHEPREFIX=.bensz-api/pycache \
python3.11 -m pytest packages/bensz-skill-kernel/tests/runtime/test_contract_packs.py \
  -o cache_dir=.bensz-api/.pytest_cache
```

## 验收与回归测试

- 索引协议、canonical ID、版本、目录和五段式 `VERIFIER.md` 结构通过现有测试。
- `bsk verifier list/describe` 返回新 Pack；从构建后的 wheel 安装环境仍能发现契约资产。
- 无 submission 时返回绑定 handoff 与 `unchecked`；不能因 Agent 未执行而 pass。
- `pass` 案例包含必要复杂度，例如安全边界、明确兼容要求或防止重复真相源的单一抽象。
- `fail` 案例必须包含一个保持全部声明约束的具体更简单方案，且迁移风险不抵消收益。
- 缺少目标、约束、不变量或产物快照时为 `uncertain`/`unchecked`，required Gate 不允许完成。
- advisory fail 只产生 `allow_with_warnings`；required fail 为 `reject`；required uncertain 为 `manual_review`；required unchecked 为 `wait`。
- 错误的 run/attempt、证据引用、contract/component/plan hash 被拒绝；历史结果不能满足当前运行。
- 运行前后源码目录不产生 `__pycache__`、pytest/Ruff 缓存或测试产物。

## 已知不确定性、回退方案和不在范围内的事项

- “不存在全局更简单方案”通常不可证明，因此 pass 只表示在声明范围和证据中未发现 material 的占优替代，不宣称数学全局最优。
- 不同复杂度维度经常冲突；没有 Pareto 支配关系时应记录 tradeoff 并返回 `uncertain` 或 pass-with-observation，而不是强行加权评分。
- 首版 Agent 一致性尚未校准，默认 advisory。若误报偏高，回退为各 Skill 的非 Gate 审查清单，不影响其它内置 Verifier。
- 不负责验证业务正确性、事实真实性、安全性、性能、文体偏好或任务完整性；这些由其它 Verifier、测试或人工审查承担。
- 不实现自动重构，不修改产物，不决定子 Agent 数量，不把完整文章、仓库或私有 Prompt写入事件账本。
- 设计日期：2026-09-11。Kernel 依据版本：`bensz-skill-kernel 1.1.0`。参考输入：`init-project 2.4.0` 的工程原则、当前 Kernel 索引/契约、Verifier ID 与 Pack 托管规范。
