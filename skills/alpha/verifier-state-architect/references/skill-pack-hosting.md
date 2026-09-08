# Skill 专用 Verifier / State 托管规范

## 适用范围与职责

本文件是 Skill 专用 Verifier / State Contract Pack 托管规范的唯一维护入口，由 `verifier-state-architect` 随 Skill 托管、发布和安装。适用于明确采用这些组件后的新建、接入及相关资产修改；规定资产放在哪里、如何声明和发现，不替代领域架构设计、命名规范或执行协议，也不要求普通 Skill 默认接入 Verifier / State。`AGENTS.md`、教程和落地参考只引用本文件，不另存规范副本；修改托管规则时先改本文件，再同步受影响的检查脚本与引用。

本文件包含安装后执行所需的托管规则。文中 `docs/`、`packages/` 开头的代码路径均为开发仓库中的维护依据，不是相对于本文件的运行依赖；仓库外按实际安装的 Kernel 版本核对 API，不要求存在这些源码路径。

- 仅服务于目标 Skill 业务的契约及专属组件，必须随该 Skill 托管、发布和安装，不得为方便发现而塞入 `packages/bensz-skill-kernel/` 的内置目录。
- BSK 提供通用的发现、索引解析、组件执行与证据处理能力；Skill 保留自身的验证命题和状态迁移语义。跨场景复用的通用能力应另行评估，不能仅凭使用频率或 ID 前缀直接提升为 Kernel 内置 Pack。
- 本文中的“必须”是新建或修改相关资产时的仓库维护要求；“当前实现”描述现有加载行为。兼容读取旧格式不意味着新资产可以继续沿用旧布局。

## 标准目录

新建 Skill 专用 Pack 必须采用以下布局；仅创建实际使用的集合和组件，不生成空目录或占位 Pack。

```text
<skill>/
├── SKILL.md
├── config.yaml
└── references/
    ├── verifiers/
    │   ├── index.json
    │   └── <verifier-directory>/
    │       ├── VERIFIER.md
    │       └── scripts/                 # 可选的 Pack 专属执行组件
    │           └── verify.py
    └── states/
        ├── index.json
        └── <state-directory>/
            ├── STATE.md
            └── scripts/                 # 可选的 Pack 专属执行组件
                └── check.py
```

- 两个 `index.json` 分别属于 Verifier 和 State **集合根目录**，不是单个 Pack 的内部文件。每个 Pack 位于所属集合的直接子目录。
- 目录名使用能表达能力或阶段的小写 kebab-case；目录名不是公开 ID，不能用重命名目录代替 ID / alias 迁移。
- Pack 专属脚本及静态资源放在该 Pack 内；机器可读的组件入口必须指向 Pack 内实际存在的文件，不能使用 `../` 或符号链接越界。
- Skill 已有的共用业务 helper 可以继续放在 Skill 的 `scripts/` 中，由 Pack 内入口基于 `Path(__file__).resolve()` 定位并调用；不得将索引入口直接指向 Pack 外，不得复制出第二份业务实现。
- 契约和静态组件是发布资产；运行结果、状态快照、证据、日志、缓存和测试夹具不是，不得回写这些目录。

## 索引、契约与身份

新建集合必须使用索引，已有索引必须与实际 Pack 目录保持一致：不允许漏登、悬空条目、重复目录或越界契约路径。

| 文件 | 维护内容 |
| --- | --- |
| `references/verifiers/index.json` | `protocol: bensz-pack-index-v1`、`package_kind: verifier`、`entries`；每个条目声明 `directory`、`id`、`version`、`classification`、`tags`、`aliases`、`contract`、`mode`、`assurance_tier`、`components` |
| `references/states/index.json` | 同一索引协议，`package_kind: state`；条目维护对应元数据，并以 `kind: skill` 表达 Skill 领域状态 |
| `VERIFIER.md` | 验证目标、输入证据、执行含义、判定、失败及副作用边界；`contract` 使用 `VERIFIER.md` |
| `STATE.md` | 阶段说明、`entry_conditions`、`invariants`、`transitions` 及进入/退出证据；`contract` 使用 `STATE.md` |

带索引的 Pack 以索引作为身份与执行元数据的单一来源，不在契约 frontmatter 或正文中重复维护这些字段。`classification` 应按实际领域属性填写，不得把 Skill 专用 Pack 标成通用内置能力。`runtime` 中的版本要求是消费约束，不是另一个 Pack 版本定义。

两者均可采用脚本、Agent、人工或混合组件，不要求“每个 Pack 都必须有 Python 脚本”。新执行契约显式声明 `components`，组件类型为当前 Kernel 支持的 `script`、`agent`、`human`，模式按实际组件选择 `rule`、`prompt`、`human`、`hybrid`，不自行增加 Kernel 未支持的执行方式。Verifier 至少一个组件；State 的纯阶段契约可显式使用 `components: []`、`mode: none`、`assurance_tier: none`，但必须有真实阶段/迁移含义，不能冒充执行过的检查。脚本组件声明 Pack 内 `entrypoint`，明确 `required`、`assurance`、`side_effects`、超时及必要依赖顺序。

身份规范的仓库维护入口为 `docs/verifier-id-naming.md` 与 `docs/state-id-naming.md`：Verifier 使用 `owner.domain.capability`，State 使用 `owner.machine.state`；canonical ID 为全小写 kebab-case 三段式，版本独立维护且不嵌入 ID，发布后重命名保留唯一 `aliases`，历史事件不改写。`bensz` 前缀不代表一定属于 Kernel 内置注册表。

### VERIFIER.md 正文

正文按顺序包含以下五个二级章节，每节写该组件的真实契约，不使用模板占位或附录托管旧正文；通用正文骨架的仓库维护入口为 `docs/templates/verifier-body.md`。

1. `## Verification target`：稳定命题、通过意味着什么、非目标。
2. `## Inputs and evidence`：subject/context/requirements/evidence、缺失/空证据及来源锚点。
3. `## Execution`：实际组件的检查语义、宿主/脚本依赖、网络/文件与副作用边界。
4. `## Output and verdicts`：适用的 pass/fail/uncertain/unchecked/error/timed_out/skipped 条件与 findings/facts/evidence_refs。
5. `## Failure and boundaries`：非法输入、超时、不可观测、人工复核、路径和敏感信息边界。

### STATE.md 领域契约

阶段语义、进入/退出证据、`entry_conditions`、`invariants`、`transitions` 必须清楚。当前 Kernel 从 YAML frontmatter 读取图字段，不能只写在正文中期待机器解析。`entry_conditions` 与 `transitions` 使用 canonical State ID 列表；自然语言进入条件写在正文；`invariants` 按实际 Kernel 支持的规则/宿主解释边界声明，不假定任意文字都会被引擎强制执行。空数组可以表达无前置、无机器 invariant 或终止态，但应解释证据和结束含义。

frontmatter 只维护这些领域契约字段及说明，不重复索引身份/执行元数据。不得把 Verifier 的 verdict 列表当作状态图；所有转移目标必须可解析且属于选定流程，失败与恢复路径需实际核对。

## Skill 声明与加载接入

### 配置与 AI 执行契约

- 使用领域 State 时，必须在 `config.yaml.runtime.state_roots` 显式声明 `references/states`，并通过 `initial_state`、`states` 使用 canonical State ID；入口条件和迁移边也使用 canonical ID。
- 使用 Verifier 要求时，在 `config.yaml.runtime.verifiers` 声明 `id`、`version` 和布尔 `required`。通用 Verifier 引用 Kernel 中的能力，专用 Verifier 引用本 Skill 集合，不把内置契约复制进 Skill。
- 接入 Kernel 时核对 `runtime.kernel` 中的包名、版本与实际运行版本；当前声明加载器精确匹配版本，不接受版本区间。不能盲抄示例中的历史版本，不能以“文件存在”代替版本和解析检查。
- `SKILL.md` 的控制章节必须说明调用时机、证据来源、通过条件、失败恢复和人工介入，并引用本 Skill 内的配置或契约。领域规则归对应契约维护，不在 `SKILL.md` 再维护平行副本。

### 当前实现边界

| 入口或能力 | 当前行为与使用要求 |
| --- | --- |
| Skill State 声明加载 | `SkillStateDeclaration.from_skill_root()` 读取 `runtime.state_roots`；路径相对于 Skill 根目录解析，且必须留在 Skill 内。省略该字段时当前默认是 `states`，因此标准布局必须显式声明 `references/states` |
| Skill Verifier 要求解析 | 上述声明加载路径在存在 `runtime.verifiers` 时合并内置注册表和 `<skill>/references/verifiers`；这不是任意目录自动扫描，也不提供可照搬 `state_roots` 的 `verifier_roots` 配置 |
| State CLI | 支持通过 `--skill-root` 读取 Skill 声明，或通过 `--root` 提供附加状态目录；两者不能混用 |
| 普通 Verifier CLI | 当前注册表只加载内置 Verifier；仅安装 Skill 或填写 `runtime.verifiers`，不会使专用 Verifier 自动进入该 CLI 的注册表 |

**声明可解析不等于组件已执行。** 接入方必须明确使用哪个宿主或 Python API 加载本地 Verifier 注册表并交给执行器；不能因 State 声明能解析专用 Verifier，就声称通用 Verifier CLI 已支持它。没有可用执行入口时，应报告接入缺口，不得将未执行或证据不足记录为通过。Agent / 人工组件仍需要宿主执行和绑定结果回传，不能把自然语言契约当成已运行的脚本。

只有 Verifier 时，用 `CombinedVerifierRegistry(FilesystemVerifierRegistry(builtin_verifier_root()), FilesystemVerifierRegistry(local_root))` 和 `normalize_requirements()` 解析，不为通过 State 声明加载器而创建无意义状态。本地索引用 `FilesystemVerifierRegistry` / `FilesystemStateRegistry` 验证；组件计划用 `definition.contract_pack()` 或 `ContractPack.from_directory()` 检查。

实际接入复用 `ContractPackExecutor` 的脚本执行、Agent/人工 handoff 与绑定结果回传，以及对应 Verifier/State 适配器；调用参数以实际版本 API 为准。handoff 只是待办，不是判定。State 与 Verifier 共用执行/证据底层，不能混淆两者的领域结果对象。

仓库实现核对入口位于 `packages/bensz-skill-kernel/src/bensz_skill_kernel/`：`states.py` 负责 Skill 声明加载，`packs.py` 负责共享 Pack 加载，`cli.py` 维护 CLI 注册表，`contract_packs.py` 定义共享组件执行协议。这些入口变化时同步本节，不能将本文误当成尚未实现功能的承诺。

## 发布资产与运行产物

- Skill 拥有专用 Pack 的源码维护责任；发布和复制安装必须保留其索引、契约和组件的相对结构，不依赖开发仓库绝对路径或工作目录。
- 安装后的 Skill 副本按只读发布资产使用，不因执行失败就地改源码、索引或版本。
- AI 任务的输入引用、证据、状态快照和日志保存在唯一的 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/` 下，按 `shared/` 和各 Skill 的 `input|output|log/` 分界；工作区规范的仓库维护入口为 `docs/bensz-api-workspace.md`。测试运行产物按仓库约定进入 `tmp/`，Python 等缓存进入 `.bensz-api/`。
- 正式业务交付物仍按用户项目约定保存，不得放进 Pack 目录或混同任务临时证据。不得把凭据、隐私或私有 Prompt 作为 Pack 资产或审计附件归档。

## 旧格式兼容与修改范围

当前加载器仍兼容部分无索引目录、契约 frontmatter 身份元数据及旧式单入口 `entrypoint`。这是运行时兼容能力，不是新建资产的推荐方式。

- 历史 Skill 不因本规范发布而自动批量迁移；只改无关业务文档时，也不得顺带重构 Pack。
- 修改相关托管布局、索引或契约时，按受影响集合核对本规范，清理机器元数据双写并验证原有语义；若兼容约束阻止迁移，明确记录差异和后续处理，不宣称已符合新规范。
- 迁移保留 ID、版本兼容关系、aliases、输入输出、执行方式和失败边界；发生契约变化时按版本规则处理。不得修改历史事件或靠复制旧正文到附录完成迁移。
- `write-readme` 的现有目录可作为布局参考，但旧 frontmatter 和历史 Kernel 版本不是规范模板。

## 最小验收清单

本清单指导变更验收，不表示仓库结构检查器已经自动覆盖全部要求。

1. 核对领域职责与可选性，只新增确有需要的专用 Pack，不修改内置注册表来绕过接入问题。
2. 用目标版本的加载器验证索引、契约、canonical / alias 解析和目录边界；确认 State 声明及 Verifier 要求能解析到预期定义。
3. 验证实际调用入口，而不只做目录检查；脚本组件检查成功、失败与非法输入，Agent / 人工组件检查待处理与结果回传路径。未执行项明确留痕。
4. 核对迁移规则与证据判定，保证缺失或不可观察证据不会被默认为通过，状态不会因“有结果文件”就自动放行。
5. 从仓库约定的临时目录验证复制后的资产仍可发现，组件不依赖开发路径，不产生源码目录缓存；无需为验证而覆盖系统级安装副本。
6. 更新受影响的 Skill 使用说明、版本和变更记录，按 BAC 要求记录验证证据；正式交付与运行产物分别归档。

按实际变更收集以下执行证据，不适用的项目说明原因：

| 场景 | 最小证据 |
| --- | --- |
| 脚本组件 | 成功、失败、非法/缺失证据、超时（适用时）；JSON-stdio 及副作用边界；脚本成功退出不等于语义通过 |
| Agent/人工组件 | 待处理 handoff、与当前 run/attempt/契约/组件绑定的回传、拒绝错绑/缺证据；实际模型/人类未执行时保留 unchecked |
| Gate / State | required 缺失或 uncertain 不放行，advisory 不误阻塞；合法/非法转移、恢复及适用事件重放 |
| ID / 布局 | canonical/alias 同一解析、旧身份兼容、未知/重复/悬空引用、越界路径拒绝 |
| 发布资产 | 在临时目录复制目标 Skill，从无关工作目录加载；无需覆盖系统安装；无源码缓存污染 |
| 文档/行为 | 目标普通业务仍工作，版本与文档一致；计划每项对应文件、命令、证据、完成/偏差/阻塞状态 |

托管检查不能判断组件设计是否合适，也不能检测所有正文中的元数据双写；仍须进行人类可复核的 AI 语义自检。验证能力受限时明确范围，不宣称“完全符合”或“已生效”。
