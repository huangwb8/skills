# Verifier/State 设计计划：BSK 内置 Verifier 正文规范化

## 结论摘要

- 在 `docs/templates/verifier-body.md` 维护完整轻量骨架，避免把长模板重复写入 `AGENTS.md`。
- 在 `AGENTS.md` 保留不可违反的五段顺序、索引与正文的职责分工、模板入口和语义迁移门禁。
- 将 BSK 全部内置 `VERIFIER.md` 迁移为五段正文，并增加包内测试，防止后续退化。
- 不改变 Verifier ID、版本、组件、脚本、请求/结果协议或 Gate 行为，因此不提升 Kernel 包版本。

## 业务流程与风险地图

当前 `verifiers/index.json` 已是机器元数据单一来源，但内置 `VERIFIER.md` 多数只有一句描述，不能稳定回答输入证据、执行边界、输出语义和失败路径。主要风险是 Agent 只凭名称猜测、把证据缺失误写为通过，或让正文与脚本实际行为漂移。

本次只规范契约文档与结构门禁，不修改运行时逻辑。迁移依据为 `verifiers/index.json`、各 `scripts/verify.py`、`atomic_verifiers.py` 和 Markdown 链接采集器。

## 删除影响测试（含“不接入”结论）

- 若不增加模板：新 Verifier 仍会重复出现一句话契约，输入、输出和失败边界不可审查，因此保留模板。
- 若不在 `AGENTS.md` 保留硬门禁：模板只是可选参考，无法形成仓库约束，因此保留简短入口和固定顺序。
- 若不增加测试：内置 Pack 可在后续修改中重新退化，且人工审查难以覆盖全部目录，因此保留一个轻量结构测试。
- 不增加 State、不增加新 Verifier、不修改 Gate；这些能力对本次正文格式治理没有删除影响收益。

## Verifier 设计矩阵

| 候选 | 保留/删除 | 稳定命题或状态含义 | AI/脚本分工 | 输入与证据 | Gate/转移 | 失败与人工复核 |
| --- | --- | --- | --- | --- | --- | --- |
| `VERIFIER.md` 五段骨架 | 保留 | 每份契约明确目标、证据、执行、判定和边界 | 脚本行为按源码陈述；语义边界由正文说明 | `subject/context/evidence` | 不改变现有 Gate | 不确定与不可观察不能伪装为 `pass` |
| 内置结构测试 | 保留 | 所有内置正文具有同一最小接口 | 脚本机械检查 H1 与 H2 顺序 | Pack 文件 | 不参与运行 Gate | 失败阻止测试通过，由维护者修正文档 |
| 新运行时 Verifier | 删除 | 本次没有新的业务命题 | 不适用 | 不适用 | 不适用 | 不适用 |

## State 设计矩阵与最小状态图

本次不新增或修改 State。文档规范化不会改变 `planned → active → checking → delivering → completed` 等既有图，也不新增状态转移证据。

## AI/确定性分工与 Evidence Contract

- 确定性部分：检查一级标题、五个二级标题及其顺序；核对正文中提到的字段和枚举是否与脚本、索引一致。
- AI/自然语言部分：为每个 Verifier 解释稳定命题、非目标、证据充分性和不确定性边界。
- 混合边界：测试只检查结构，不判断正文质量；语义复核必须逐文件对照实现，不能用空模板占位通过测试。

正文骨架固定为：`Verification target`、`Inputs and evidence`、`Execution`、`Output and verdicts`、`Failure and boundaries`。正文不复制索引中的 ID、版本、mode、assurance 或组件清单；无索引兼容 Pack 才在 frontmatter 声明身份。

## Kernel 对接、Gate、重放与资源边界

- 保持 `owner.domain.capability` ID、版本、alias 和组件哈希不变。
- 保持 JSON-stdio、`run_id`/`attempt_id`、结果枚举和 Gate 行为不变。
- `VERIFIER.md` 只描述实际证据与行为；不得声称脚本执行了源码中不存在的检查。
- 结构测试放入 `packages/bensz-skill-kernel/tests/`；pytest 与字节码缓存继续写入 `.bensz-api/`。
- Pack 资产已被 `pyproject.toml` 的 `verifiers/**/*` 纳入 package data；安装后发现测试需继续通过。

## Kernel 复用与元 Verifier/State 提炼决策

### 现有 Kernel 能力盘点

- 复用 `bensz-pack-index-v1` 的索引职责，不把机器元数据复制到 Markdown 正文。
- 复用现有 Verifier 请求、结果、组件和 Gate 协议，仅补充人类/Agent 可读契约。

### Kernel 复用结论

- 直接复用现有 Pack 发现和 Markdown `instructions` 加载；格式变化不需要新解析器，维护成本最低。
- 直接复用现有包内测试布局；结构门禁属于资产测试，不应进入运行时或通用 reducer。

### Kernel 元组件提炼结论

- 明确不提炼新的元 Verifier：标题顺序是仓库发布治理，不是跨领域运行命题，提升为运行时 Pack 会形成自举和维护负担。
- 明确不提炼新的 State：正文迁移没有持续阶段、恢复点或跨 Skill 生命周期语义，普通实施流程足够承载。

### 对人类决策的影响

- 采纳后，新建或修改 `VERIFIER.md` 必须按模板编排；机器元数据仍只改索引。
- 不采纳测试则规则只能依靠人工记忆；采纳测试会让不完整的内置正文直接在包测试中暴露，但不影响 legacy 外部 Pack 的运行兼容。

| 候选能力 | 现有 Kernel ID/版本 | 复用方式 | 契约差异 | 是否跨领域 | 提炼建议 | 主要理由 | 验证动作 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pack 索引与契约加载 | `bensz-pack-index-v1` | 直接复用 | 无运行时差异 | 是 | 不新增 | 已能加载任意 Markdown 正文 | registry/pack 测试 |
| 正文结构门禁 | 无 | 仓库测试 | 只约束内置资产 | 否 | 不提炼 | 发布治理不属于运行命题 | 新增结构测试 |

## 实施顺序（P0/P1/P2）

- P0：无安全或不可恢复运行时缺陷。
- P1：新增模板与 `AGENTS.md` 门禁；迁移全部内置 `VERIFIER.md`；新增结构测试。完成条件是结构测试、Registry/Contract Pack 测试通过，逐文件 diff 与脚本一致。
- P2：同步 Kernel README、根 `CHANGELOG.md` 和 BAC；验证构建资产仍包含全部 Verifier 契约。

## 验收与回归测试

1. 包内测试检查全部内置 `VERIFIER.md` 具有唯一 H1 和五个有序 H2。
2. 运行 Verifier、Contract Pack 与打包相关测试，确认文档哈希变化不破坏发现和执行。
3. 构建 wheel 到 `tmp/`，检查所有 `VERIFIER.md` 均被打包。
4. 检查仓库源码目录没有新增 `__pycache__`、`.pytest_cache` 等缓存。
5. 运行 `bac verify`，记录变更和测试证据。

## 已知不确定性、回退方案和不在范围内的事项

- 当前 Kernel 不解析正文标题；结构门禁由测试承担，这是有意的发布期约束，而非运行时兼容性要求。
- 回退时可单独撤销模板、治理条款、正文和测试；不存在数据或事件迁移。
- 不修改 Verifier 脚本、ID、版本、索引、Gate、State、外部 Skill Pack 或已安装副本。
