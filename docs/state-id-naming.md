# State ID 命名规范

## 目的

State ID 是状态机中一个稳定状态节点的公开标识，不是动作、事件、命令、页面标题或一次运行名称。它会出现在 `STATE.md`、状态声明、迁移边、工作区快照、CLI 回执和审计记录中，因此发布后应视为状态图的外键。

## Canonical 格式

```text
<owner>.<machine>.<state>
```

规则如下：

- 全部使用小写 ASCII。
- 每个词使用 kebab-case；允许字母、数字和连字符，必须以字母开头。
- `owner` 可以由一个或多个点分段组成，以支持组织或发行方命名空间。
- `machine` 是拥有该状态的稳定状态机或生命周期名称。
- `state` 描述已经成立或正在持续的状态，不描述触发该状态的命令。
- 版本、实现脚本、执行引擎、状态 kind 和运行实例不得写入 ID。
- canonical ID 不得以 `v1`、`v2` 等版本后缀结尾。

Kernel 官方内置状态使用 `bensz` owner，例如：

```text
bensz.workspace.ready
bensz.workspace.closed
bensz.runtime.planned
bensz.runtime.active
bensz.runtime.checking
bensz.runtime.delivering
bensz.runtime.completed
```

Skill 自有状态也应使用 `bensz` 或组织命名空间，例如
`bensz.validate-md-ref.input-ready`、`bensz.validate-md-ref.checking` 和
`bensz.validate-md-ref.reported`；它们不属于 kernel 内置状态目录。

第三方可使用组织前缀，例如 `org.example.deploy.awaiting-approval`。

## 各段含义

`owner` 表示维护者或发行方；`machine` 表示状态所属的生命周期边界；`state` 表示该边界内可观察、可进入、可离开的稳定阶段。

状态名优先使用状态性名词、形容词或清晰的持续阶段，例如 `ready`、`checking`、`awaiting-approval`、`reported`、`closed`。不要使用命令式动作，例如 `run-check`、`create-report`、`close-workspace`；动作属于 transition、helper 或事件。

状态 ID、transition/event ID、Contract Pack 组件 ID、Verifier ID 和单次运行 ID 必须分开。`kind: system|skill` 是状态元数据，不进入 ID；目录名也不决定公开身份。

## 状态图引用

`initial_state`、`states`、`entry_conditions` 和 `transitions` 应写 canonical ID。Skill 的 `config.yaml.runtime.state_roots` 只负责声明 State 定义的发现根，不能代替 `states` 的允许集合。通配符 `*` 只允许作为迁移策略，不是 State ID。

Registry 可以接受 legacy alias，但完成解析后：

- `state list/describe` 输出 canonical ID；
- 新工作区 manifest 和元状态快照保存 canonical ID；
- helper 请求中的当前状态和目标状态使用 canonical ID；
- Gate、事件或历史快照中的旧 ID 不被覆盖改写。

## 版本与兼容

版本独立记录在 `version` 字段，并以 `id@version` 展示，例如 `bensz.workspace.ready@1.0.0`。

- patch：说明或 helper 实现修复，不改变状态含义和迁移契约；
- minor：增加向后兼容的元数据、可选入口条件或迁移能力；
- major：改变状态语义、必需入口条件、不变量或迁移边。

发布后的 ID 不直接重命名。迁移时把新 ID 设为 canonical，并通过 alias 保留旧 ID：带 `index.json` 的 State Pack 在索引条目的 `aliases` 中声明；没有索引的外部兼容目录才在 `STATE.md` frontmatter 中声明。Alias 必须唯一，不得与任何 canonical ID 冲突。

Kernel 内置 State Pack 使用 `bensz-pack-index-v1` 的 `states/index.json` 作为属性单一来源；索引条目同时记录 `directory`、canonical `id`、`version`、`kind`、`classification`、`tags`、`aliases`、契约文件、`mode`、`assurance_tier` 和 `components`。内置通用生命周期状态以 `mode: none` 明确表示阶段语义由 reducer/invariant 管理；领域 State 可声明 `script`、`agent` 或 `human` 组件。`STATE.md` 保留 `description`、入口条件、不变量、迁移边和正文说明。

## 禁止模式

不要使用无 owner 的 `workspace.ready`、带版本的 `workspace.ready.v1`、命令式 `deploy.run-check`、实现相关的 `python.collecting`、运行实例 `review.attempt-2` 或含义宽泛的 `task.active` 作为新 State ID。

## 契约示例

```yaml
id: bensz.validate-md-ref.checking
version: 1.0.0
kind: skill
aliases: validate-md-ref.checking
entry_conditions: bensz.validate-md-ref.input-ready
transitions: bensz.validate-md-ref.reported
```

Kernel 必须校验 canonical ID，维护 alias 到 canonical ID 的解析，并确保状态定义、声明、状态图、CLI 与新快照使用同一身份。
