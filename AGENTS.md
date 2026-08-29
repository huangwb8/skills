# skills - 项目指令

本项目是 **Agent Skills 开发流水线**：用于创建、优化和维护高质量、可复用的 AI Agent Skills。所有技能遵循 [Agent Skills 开放标准](https://agentskills.io)，确保在 Claude Code、OpenAI Codex、Cursor 等多个平台间"编写一次，随处使用"。

**核心价值**：
- 提供标准化的技能开发框架和工作流
- 确保技能质量（安全性、可靠性、通用性）
- 支持有机迭代和持续优化

**兼容平台**：Claude Code、OpenAI Codex、Cursor、GitHub、VS Code、Amp、Letta、Goose（详见 [Agent Skills 官方网站](https://agentskills.io)）。

## 目录结构与边界

- `skills/alpha/<skill-name>/`：可发布、默认安装的成熟 Skill；以自身 `SKILL.md` 为识别边界，可包含专属的 `scripts/`、`references/`、`templates/` 和资源文件。
- `skills/beta/<skill-name>/`：尚未成熟的候选 Skill；不进入默认安装源，仅当用户显式指定 beta 源目录时才处理。
- `packages/<project>/`：独立运行时包边界，拥有自己的项目配置、版本、依赖和测试；不得在包内放置领域 Skill 流程。
- `docs/plans/`：正式计划、迁移说明和治理文档；不得在 Skill 目录内新建 `plans/`。
- `tests/`：面向 `packages/` Python 包核心公开 API 及仓库级公开入口（如安装器）的可执行 smoke/integration 测试脚本；不承载测试计划、报告、artifacts、fixture 或运行缓存。
- `tmp/`：测试脚本运行过程的临时承载目录，可包含测试计划、报告、artifacts、fixture、日志和缓存；这些内容不得回写到 `tests/`。
- `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/`：本轮任务的输入、过程产物、日志和验证证据；正式交付物不写入其中。

**目录职责规则**：
- 包内单元测试放在对应 `packages/<project>/tests/`；跨包或仓库公开入口测试脚本放在根级 `tests/`；测试运行产物统一写入根级 `tmp/`。
- Skill 目录内不得新建历史计划、测试夹具或运行缓存目录。
- AI 任务级中间材料遵循下方 `.bensz-api` 工作区协议。

## AI 任务中间文件与 Skill 协作工作区

本节定义仓库统一的 `.bensz-api` 任务工作区协议，为需要落盘的 AI 任务提供统一、可审查且不污染项目交付物的中间文件管理。协议只依赖本文件及当前仓库的目录约定，不要求读取其它仓库、绝对路径或外部说明文档；它也不替代具体业务 Skill 的专业流程。

### 任务根目录与生命周期

- 将"本轮"解释为用户发起的一个逻辑任务，而不是一次 HTTP 请求、模型采样或工具 continuation。
- 开始任务时先检查会话历史：若该逻辑任务已公开声明任务根目录，必须无条件复用并恢复该工作区锁，不得重新计算时间戳、描述或冲突后缀。
- 若尚未声明且确实需要落盘，而准确时间、项目根目录或候选目录冲突状态未知，只允许先做一次不改变项目状态的最小只读引导，确认时间、项目根目录、目录冲突和必要 Skill 可用性；不得读取业务数据、调用 Skill、写文件或开始实现。
- 在正式工作、调用任何 Skill 或写入任何中间文件前，只公开声明一次最终目录：`./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/`（同一分钟内冲突时用后缀 `-a`、`-b` 区分）。
- 任务根目录一经公开即锁定为该逻辑任务会话内不可变状态；后续 continuation、重复模板注入、智能路由或 Skill 变化都不得更换、重命名或迁移。新增、移除 Skill 或调整用途只能在原根目录下增删对应子目录，并在下一次相关调用前更新用户。
- 一个逻辑任务只能使用一个任务根目录。小型纯文本回答不产生中间文件时，不创建任务目录。

### Skill 透明度与目录边界

- 首次调用任何 Skill 前，必须通过用户可见进度消息逐项报告准确的 Skill 名称及其具体工作，并说明多个 Skill 的调用顺序或协作关系。
- 没有适用 Skill 时，必须明确告知用户本次不调用 Skill 及原因；不能在交付时追溯性补报或把未调用伪装成已调用。
- 为需要落盘的任务建立 `shared/`，并为每个实际调用的 Skill 建立独立边界；任务共享且与任何 Skill 无关的材料放在 `shared/`，Skill 专属材料只放入对应 Skill 子目录。默认目录树：

  ```text
  ./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/
  ├── README.md
  ├── shared/{input,output,log}/
  └── {skill名}/{input,output,log}/
  ```

- 只为实际参与的 Skill 创建子目录；单阶段任务不为未调用的 Skill 预建目录。多阶段任务按依赖顺序在同一根目录下增加 Skill 子目录，并在消费者的 `input/` 中用 Markdown 记录相对来源。

### 输入、输出与归档要求

- `input/` 保存输入、参数快照、来源说明和跨 Skill 引用；`output/` 保存草案、临时输出和供后续阶段消费的中间结果；`log/` 保存命令、验证、错误和决策摘要。
- 任务根目录的 `README.md` 默认汇总任务目标、参与 Skill 与顺序、跨 Skill 来源、关键临时产物、正式交付路径和验证摘要，便于人工审查。
- 只有需要完整审计链路的全流程任务才保留完整输入、输出和日志链；其它任务按需求规模采用最小必要落盘方式。
- 正式交付物、用户明确要求保存的文件、计划文档、项目文档和源代码变更不得默认写入 `.bensz-api`；实施、审查、排查等计划类 Markdown 默认保存到 `./docs/plans/`。
- 交付时列出关键输出路径和必要验证证据，不粘贴大文件全文。

### 失败兜底与安全边界

- 若宿主不支持独立的中间进度消息，使用最早可见消息报告 Skill 使用说明；若全程无法发送，最终交付开头补充实际使用的 Skill、具体工作及宿主限制。
- 若原路径或 `.bensz-api` 创建失败，报告已锁定路径、失败原因和应创建的目录树；不得在同一逻辑任务内切换到第二个任务根目录，应停止写入并请求处理。
- 外部工具或远程站点不可用时，保留本地草案和失败摘要，不上传、不覆盖远程状态。固定目录要求须在对应 Skill 子目录的 `README.md` 中记录映射关系。
- 不得把中间文件散落到项目根目录或覆盖已有文件；远程写入、上传、删除、迁移和覆盖必须获得明确授权。敏感信息禁令见"隐私与敏感信息"一节。
- `bensz-collect-bugs` 仅用于记录 Bensz Skill 或基础设施模板的设计缺陷（最小复现、影响范围、workaround），不得污染用户项目交付物。

### 工作区质量门禁

- 检查首次 Skill 调用前是否已逐项播报"Skill 名称 → 具体工作"，无适用 Skill 时是否说明原因；计划变化时是否在下一次相关调用前更新。
- 确认一个逻辑任务至多使用一个不可变任务根目录，且 `shared` 与各 Skill 的 `input`、`output`、`log` 边界清楚、跨 Skill 来源可追溯、敏感信息已排除。
- 检查流程长度、Skill 数量和落盘规模是否与需求匹配，避免过度执行；验证正式交付物未误写入 `.bensz-api`，必要命令与验证证据已留痕。

## 通用协作规范

### 默认语言

除非用户明确要求其他语言，始终使用简体中文与用户对话及撰写文档/说明。

### 联网与搜索

默认优先使用项目内文件与本地上下文；确需联网获取信息时，优先使用本地搜索工具。仅当本地工具不足以满足需求时再使用其它联网手段，并说明原因与保留关键链接。

### 隐私与敏感信息

不得在任何记录、归档或公开上报内容中保留：API Key、访问令牌、密码、Cookie、本地环境文件、凭据文件、完整私有 Prompt、用户隐私（身份信息、邮箱、私密路径等）或不必要的大体积原始数据。默认不收集本地用户名、主机名、工作目录；公开上报前必须脱敏。

### 贡献记录（BAC）

本项目默认且强制启用 [bensz-auto-contribution](https://github.com/huangwb8/bensz-auto-contribution) 的 `bac` 贡献记录，默认托管文件为 `docs/contribution.bac`。项目协作应使用 `bac` 客观记录需求来源、AI 生成内容、工具执行结果、人工确认、文件改动与验证证据。

- 初始化或维护项目时，必须检查 Python 环境、确认 `bac` 可用，并初始化或验证账本；环境未配置好时按 `init-project` 流程补齐依赖。
- 除非项目负责人明确要求暂时关闭，否则不得跳过 BAC 依赖检查、安装、账本初始化或贡献记录。
- BAC 仅用于过程记录和辅助审计，不替代最终署名、责任或合规判断；敏感信息禁令遵循"隐私与敏感信息"一节。

### 修改规范与边界

- 先读取足够上下文，明确输入、输出、兼容性和安全边界，再进行最小范围修改。
- 按需使用专门 Skill 或多代理协作；协作结果必须回收、复核并由主流程统一验证。
- 不得遗留已知缺陷，不得以无关重构扩大变更范围，不得破坏既有功能。
- 修改代码后运行与风险匹配的构建、静态检查或测试，并把验证证据写入变更记录。
- 默认只修改 `skills/alpha/`、`skills/beta/` 与其配套的 `packages/`、`docs/`、`tests/`；`AGENTS.md`、`CLAUDE.md`、`CHANGELOG.md` 和 `docs/contribution.bac` 属于项目治理文件，可在遵守本文件变更记录与 BAC 规则的前提下修改；扩展到其它范围需用户明确授权。
- 修改技能时，优先优化而非重写，保留用户自定义内容。

## 核心工作流

当用户提出 Skills 开发相关需求时：

- **任务理解**：理解用户的真实需求和意图，确认任务范围和预期输出，识别可能的依赖和约束。
- **执行流程**：需求确认 → 内容规划 → 撰写/实现 → 校审与测试 → 发布/安装。
- **输出规范**：代码变更遵循项目现有风格，文档更新保持一致性，测试覆盖符合项目标准。

### 对象化最小流程

- **Skill**：读取现有 `SKILL.md`、`config.yaml`、脚本和必要 references → 确认触发边界与输入输出 → 最小修改 → 静态一致性检查 → 轻量测试 → README、CHANGELOG 和 BAC 同步；影响安装发现时再运行安装器回归。
- **Verifier**：确定稳定判断命题与 Evidence Contract → 判断是否应成为顶层 Verifier → 编写 `VERIFIER.md` 和入口 → 更新 `verifiers/index.json` → 测试 canonical/alias、非法输入、超时和安全边界 → 同步 kernel 文档与 CHANGELOG。
- **State**：确定状态语义和所属 machine → 编写 `STATE.md` → 更新 `states/index.json` → 检查 entry conditions、invariants、transitions 与 Runtime reducer → 测试非法迁移、alias、helper 和 terminal state → 同步 Skill runtime 声明、文档与 CHANGELOG。

详细字段表和长示例应下沉到 `docs/`（建议维护 `docs/skill-development.md`、`docs/verifier-development.md`、`docs/state-development.md` 和 `docs/verification-matrix.md`）；`AGENTS.md` 只保留不可违反的边界、门禁和入口，避免规范与实现长期双写漂移。

## Kernel 包开发

`packages/bensz-skill-kernel/` 是独立 Python 包。包的公开 API、CLI 和目录化 Pack 资产必须同时保持可发现、可重放和向后兼容。

- Python 版本、包版本、依赖和入口以 `packages/bensz-skill-kernel/pyproject.toml` 为准；运行时继续保持零第三方依赖，测试依赖不得进入运行时依赖。
- 修改公开 API、CLI 参数、JSON 协议、事件字段、错误类型或退出码时，先判断兼容性，再同步 README、`docs/`、示例和 CHANGELOG；不得只修改实现而留下过时契约。
- `states/**`、`verifiers/**` 等包内 Markdown、JSON 和脚本资产必须纳入 `pyproject.toml` 的 package data，并用安装后环境验证仍可发现。
- 事件和状态投影必须可重放；时间、哈希和 JSON 序列化保持确定性。错误处理应提供稳定的错误类别或状态，不以异常文本作为调用方契约。
- 包内单元测试放在 `packages/bensz-skill-kernel/tests/`；根级 `tests/` 仅用于仓库公开入口或跨包集成测试。测试运行产物统一写入 `tmp/`，不得写入源码或测试目录。

## Skill 开发

### 高质量技能开发原则

基于实战经验总结，开发高质量 Agent Skills 需遵循以下六项原则：

**硬编码/AI 功能规划**——合理划分确定性与灵活性的边界：
- 确定性操作（文件解析、数据验证、格式转换）硬编码到 `scripts/`，避免 AI 反复编写相同逻辑
- 启发式判断（需求理解、方案设计、内容生成）交给 AI 动态处理
- 可配置参数（阈值、路径、模板、选项）集中到 `config.yaml`，避免硬编码会变化的业务逻辑

**Skill 脚本路径感知**：skill 安装到 `~/.claude/skills/` 或 `~/.codex/skills/` 后，脚本须基于 `Path(__file__).resolve()` 计算自身根目录（如 `parents[1]`）来访问 `config.yaml`、`assets/`、`references/`；禁止使用 `Path.cwd()`（返回用户工作目录而非 skill 目录）和硬编码绝对路径；跨平台使用 `Path` 对象并显式 `encoding="utf-8"`。

**多轮 AI 自检 + 人类监督 + 轻量测试**：建立可重复的优化循环——AI 自检（静态分析、代码-文档一致性、逻辑推演）→ 人类审查关键决策和变更范围 → 轻量测试验证核心功能（非全面测试，产物按目录约定写入 `tmp/`）→ 在 CHANGELOG.md 记录结果 → 根据测试结果迭代。

**冗余残留错误检查**：每次更新主动清理——合并重复逻辑或相似代码；删除功能后全局搜索并彻底清理引用；保持 YAML frontmatter、SKILL.md、config.yaml 三者一致；版本号只记录在 config.yaml，不在 SKILL.md、README.md 冗余记录；移除未被引用的文件或定义，定期清理 `references/` 中过时的参考文档。

**安全性检查**：检查输入验证（注入攻击、路径遍历）、路径处理规范化（文件路径使用正斜杠，用户提供的路径验证在项目范围内）、敏感信息不泄露到日志或错误消息、文件操作权限合理、网络/系统调用安全（SSRF、命令注入）；脚本错误处理要明确，不推诿给 AI 猜测。

**过度设计与通用性检查**：用 YAGNI/KISS/奥卡姆剃刀审视每个设计决策——只实现当前明确需要的功能，优先最直观的方案，提供合理默认值，不为"未来可能用到"预留扩展点；避免硬编码会过时的时间（用"当前版本"而非具体年份）、场景、平台或语言假设，如需限定场景写入 YAML `description` 而非工作流，提供扩展机制而非写死配置。

### 技能开发流程

**需求确认**：
- 阅读 Prompts.md，确认是否属于"创建/优化 skill"
- 获取 `skill_name`（用户指定或自取 1-3 个候选）

**创建结构**：
- 创建 `{skill_name}/` 目录
- 生成 `SKILL.md`（包含 YAML frontmatter；必须包含 `metadata.author: Bensz Conan`）
- SKILL.md 中必须包含 `bensz-collect-bugs` 约束章节：
  - **适用范围**：仅处理 skill 设计缺陷（流程漏判、输入契约不完整、环境假设错误等），排除用户数据有误、第三方服务抖动、用户主动改源码、模型偶发波动
  - **隐私保护**：遵循"隐私与敏感信息"一节；默认不收集本地用户名、主机名、工作目录，公开上报前必须脱敏
  - **本地优先**：bug 先记录到 `~/.bensz-skills/bugs/`，当前任务不中断；仅在用户明确要求时才通过本机 `gh` 公开上报（不 clone 仓库，用 `gh api` 按文件路径创建）
  - **禁止就地修 bug**：严禁直接修改用户本地已安装 skills 的源代码来"顺手修 bug"
- 按需添加 `config.yaml`、`scripts/`、`references/`、`assets/`

**质量检查**：通过"六项质量原则"验证，运行静态自检清单。

**生成用户文档**：
- 使用 write-skill-readme skill 生成用户友好的 README.md：README.md 面向使用者说明如何触发和使用技能，SKILL.md 面向 AI 定义执行规范和工作流
- 首次生成时，使用 which-model skill 为 README.md 添加 WHICHMODEL 章节，记录模型选择最佳实践

**测试验证**：按"目录职责规则"在对应 `packages/<project>/tests/` 编写或运行包内测试；仅仓库公开入口和跨包集成测试放在根级 `tests/`。

**系统安装**：运行 `python3 skills/alpha/install-bensz-skills/scripts/install.py`，验证技能在任意项目中可被发现。

### SKILL.md 标准结构

每个 skill 必须包含 `SKILL.md` 文件，格式如下：

```yaml
---
name: skill-name
description: Brief description of what this Skill does and when to use it
metadata:
  author: Bensz Conan
---

# Skill Title（Markdown body）

[技能说明、工作流程、使用指南等]
```

`SKILL.md` 的 description 负责触发边界，正文负责执行契约；详细参数以 `config.yaml` 为单一真相来源，不在文档中复制易变默认值。脚本必须基于 `Path(__file__).resolve()` 定位自身资产，不能依赖用户当前工作目录。

### 系统级安装

本仓库的 skills 默认只在"当前 workdir 位于本仓库"时更容易被发现；要确保它们在**任意项目/对话**里都可用，需要将 skills **复制安装**到系统级目录（不使用软链接）。

系统级安装通过两个安装入口实现，二者必须保持业务逻辑对齐：

- **本地开发版**：`skills/alpha/install-bensz-skills/scripts/install.py`，从 `skills/alpha/` 复制安装，功能完整（i18n、配置化、`--skill` 过滤等），是安装逻辑的**单一真理来源**。
- **标准库 bootstrap 版**：`skills/alpha/install-bensz-skills/scripts/bootstrap_install.py`，从 GitHub 拉取 zip 远程安装，仅依赖 Python 标准库，作为本地安装器的远程引导入口。

⚠️ **强制联动**：当 `install-bensz-skills` 发生业务逻辑变更（安装流程、版本控制策略、命令行参数、目标目录约定、manifest 格式等）时，必须检查 `bootstrap_install.py` 是否需要同步对齐，保证两者对 alpha 默认源、manifest 和安装目标的可观测行为一致；仅 Git 缓存与远程拉取实现允许不同。

### Verifier ID 命名规范

仓库内所有新 Verifier 必须遵循 [`docs/verifier-id-naming.md`](docs/verifier-id-naming.md)：canonical ID 使用 `owner.domain.capability` 格式，官方内置 owner 为 `bensz`，全小写 kebab-case，版本独立记录在 `version` 字段。不得把 Skill 名称、输入格式（除非判断契约确实格式专属）、实现方式、模型、Gate 策略或版本写入 ID。已发布 ID 不重命名；迁移时使用 `aliases` 保留兼容入口，历史事件记录不得改写。

Verifier Pack、内部 Rule/Prompt、输入 Adapter 和运行实例必须使用不同层级的标识；只有独立注册、版本化和复用的组件才提升为顶层 Verifier。修改 verifier 命名或契约时，必须同步 `packages/bensz-skill-kernel`、相关 Skill、文档、测试和 `CHANGELOG.md`，并验证 canonical/alias 两条解析路径。

### State ID 命名规范

仓库内所有新状态必须遵循 [`docs/state-id-naming.md`](docs/state-id-naming.md)：canonical ID 使用 `owner.machine.state` 格式，官方内置 owner 为 `bensz`，全小写 kebab-case，版本独立记录在 `version`。State ID 描述稳定状态节点，不表示 transition 动作、事件、helper、Verifier 或运行实例；状态 `kind` 也不得写入 ID。

`initial_state`、`states`、`entry_conditions` 和 `transitions` 应引用 canonical ID。已发布 ID 不直接重命名；迁移时使用 `aliases` 保留兼容入口，新清单、CLI 回执和快照必须输出 canonical ID，历史事件与旧快照不得改写。修改状态命名或契约时，必须同步 kernel、相关 Skill 声明与 `STATE.md`、文档、测试和 `CHANGELOG.md`，并验证 canonical/alias 两条路径。

## Skill、Verifier、State 的 Pack 开发契约

以下规则是新增或修改 Pack 的最低要求；详细理论说明可放在 `docs/`，但不得与本节的强制契约冲突。

### Verifier Pack

- 目录使用 `verifiers/<directory>/`；至少包含 `VERIFIER.md`，可选 `scripts/verify.py` 或其它入口脚本。
- 新增、删除或重命名目录时，必须同步 `verifiers/index.json`。索引协议为 `bensz-pack-index-v1`，其中 `directory`、canonical `id`、`version`、`classification`、`tags`、`contract` 和可选 `entrypoint` 必须与实际文件一致；索引是元数据单一真相来源。
- `VERIFIER.md` 必须说明判断目标、Subject/Context/Evidence 输入、必需字段、证据边界、不判断范围和结果解释。没有入口脚本的 Verifier 必须明确标为 instruction-only。
- 可执行入口通过 stdin 接收一个 JSON 请求，stdout 只输出一个 JSON 对象；stderr 只用于脱敏诊断。`verdict` 与执行状态分开，结果只能使用 `pass`、`fail`、`uncertain`、`unchecked`、`error`、`timed_out` 或 `skipped`。
- 入口默认只读；确需副作用时必须在契约、请求和审计事件中显式声明，并提供失败恢复和幂等策略。超时、异常、非法 JSON、非零退出码不得由调用方猜测，必须由 kernel 归一化。
- Verifier 只负责稳定的可复核判断；格式适配器负责把 Markdown、LaTeX 等输入转换为通用证据。只有需要独立注册、版本化和复用的能力才提升为顶层 Verifier。

### State Pack

- 目录使用 `states/<directory>/`；至少包含 `STATE.md`，可选附带 JSON-stdio helper。
- 使用 `states/index.json` 时，索引负责 `directory`、canonical `id`、`version`、`kind`、`classification`、`tags`、`aliases`、`contract` 和可选 `entrypoint`；`STATE.md` 负责 description、entry conditions、invariants 和 transitions。索引优先时不得在 Markdown 中复制易漂移的元数据。
- `initial_state`、允许状态集合、`entry_conditions` 和 `transitions` 必须引用 canonical State ID；`state_roots` 只声明发现根，不能代替允许集合。`*` 只表示明确受支持的迁移策略，不是状态 ID。
- State ID 描述已经成立或持续中的稳定状态；动作、事件、helper、Verifier 和运行实例必须使用不同标识。terminal 状态不得定义后继迁移；`kind: system|skill` 不得编码进 ID。
- helper 通过 stdin 接收标准 JSON 请求、stdout 返回一个结果对象；只有执行成功且 `verdict=pass` 才能持久化转移。instruction-only 状态必须在正文中写明由 Agent 执行的检查。
- Kernel 只提供发现、解析、转移校验、执行边界和持久化协议；领域 Skill 的业务状态、规则和判断不得硬编码进 kernel reducer。

### 索引与安全门禁

提交前必须检查：

- Pack 索引无漏列、陈旧条目、重复目录、重复 canonical ID 或 alias 冲突；canonical 与 alias 两条解析路径均能通过 CLI 验证。
- contract 和 entrypoint 文件真实存在，解析后的路径仍在 Pack 自身目录内；拒绝 `..`、绝对路径和 symlink 逃逸。
- JSON 请求和结果均经过结构校验；日志、错误和证据引用不得包含密钥、令牌、密码、Cookie、完整私有 Prompt 或不必要的原始输入。
- 网络、子进程和文件访问遵循最小权限、超时、资源上限和 SSRF/命令注入防护；不因“验证方便”扩大访问范围。

## 变更类型、版本与验证矩阵

| 变更类型 | 版本策略 | 最低验证 |
|---|---|---|
| 文案或实现修复，判断/协议不变 | patch | 原有测试、契约和索引检查 |
| 新增可选字段、证据、标签或迁移能力 | minor | 新旧输入兼容、CLI 和索引测试 |
| 修改输入契约、结果语义、Gate 或迁移边 | major | 迁移说明、回放、兼容和全量测试 |
| canonical ID 重命名 | 新 ID + alias | canonical/alias 双路径，历史事件不改写 |
| 删除字段、State 或 Verifier | major | deprecation、迁移和失败路径测试 |

版本来源必须保持分层：Kernel 包版本来自 `packages/bensz-skill-kernel/pyproject.toml`，Skill 版本来自各自 `config.yaml:skill_info.version`，Pack 版本来自对应 `index.json` 或兼容 frontmatter，仓库版本来自 Git tag。

涉及 Kernel、CLI、协议或 Pack 资产的变更，至少运行包内 pytest、Pack discovery/index 一致性、canonical/alias、非法 JSON/超时/越界路径和安装后 package-data 检查；涉及 Skill 安装发现时，再运行安装器回归测试。验证产物写入 `tmp/` 或当前任务工作区，不写入 `tests/` 和 Skill 源目录。

## 变更记录与版本号

**强制规则**：凡是项目更新，必须统一在 `CHANGELOG.md` 记录。记录范围：
- 项目指令文件（CLAUDE.md、AGENTS.md）的任何修改
- 项目结构变更（新增/删除/重命名目录或关键文件）
- 核心工作流程调整
- 工程原则变更
- 影响项目行为的重要配置变更

**记录时机**：修改前先在 `[Unreleased]` 部分草拟，修改后完善变更描述与影响范围，发布时将 `[Unreleased]` 内容移至具体版本号下。

**记录格式**：遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)：

```markdown
## [版本号] - YYYY-MM-DD

### Added（新增）
- 新增了 XXX 功能/章节：用途是 YYY

### Changed（变更）
- 修改了 XXX 章节：原因是 YYY，具体变更内容是 ZZZ

### Fixed（修复）
- 修复了 XXX 问题：表现是 YYY，修复方式是 ZZZ
```

**版本号 Single Source of Truth**：
- 本仓库不维护根级 `config.yaml`：仓库发布版本以 Git tag 为准；项目级 `project_info` 配置仅供需要项目级版本治理的下游仓库参考。
- 各 Skill 版本唯一记录在自身 `config.yaml:skill_info.version`，不在 SKILL.md、README.md 中冗余记录；遵循 [语义化版本](https://semver.org/lang/zh-CN/)：主版本号为不兼容 API 修改，次版本号为向下兼容功能新增，修订号为向下兼容问题修正。
- 版本号同步顺序：`config.yaml`（唯一来源）→ README.md 等文档引用 → `CHANGELOG.md` 版本条目。
- 技能初始化模板：`config.yaml` 声明 `skill_info.version: 0.1.0`，`CHANGELOG.md` 记录 `[0.1.0] - YYYY-MM-DD` 与 `Added（新增）- 初始化技能，实现核心功能`。

检查技能版本号：`rg -l "^skill_info:" skills/alpha skills/beta -g config.yaml | xargs -I{} sh -c 'grep -A 3 "skill_info:" "{}" | grep version'`

## Codex CLI 特定说明

**文件引用**：使用内联代码使文件路径可点击（如 `src/main.py`、`src/main.py:42`）；每个引用独立成路径，包含起始行号；不要输出刚写的大文件内容，只引用路径。

**代码编辑**：在"修改规范与边界"的基础上，保持类型安全（变更通过构建检查），无效输入早返回（遵循仓库的日志/通知模式）。

**输出格式**：简单确认跳过繁重格式；提供简短的逻辑后续步骤（测试、提交、构建）。

## 工程原则

| 原则 | 核心思想 | 在本项目中的体现 |
|------|----------|------------------|
| **KISS** | Keep It Simple, Stupid | 追求极致简洁，避免过度设计 |
| **YAGNI** | You Aren't Gonna Need It | 只实现当前需要的功能 |
| **DRY** | Don't Repeat Yourself | 相似逻辑应抽象复用 |
| **SOLID** | 面向对象设计五大原则 | 单一职责、开闭原则等 |
| **关注点分离** | Separation of Concerns | 不同层次逻辑应分离 |
| **奥卡姆剃刀** | 如无必要，勿增实体 | 优先选择最简单的解决方案 |
| **最小惊讶原则** | Principle of Least Astonishment | API 行为应符合用户直觉 |
| **早期返回原则** | Early Return | 尽早返回，减少嵌套 |

**原则冲突时的决策优先级**：正确性 > 一切；简洁性 > 灵活性；清晰性 > 性能；扩展性 > 紧凑性。

## 有机更新原则

当需要更新本文档时：

- **理解意图**：理解用户需求背后的意图和在工作流中的本质作用。
- **定位生态位**：每条规则/要求都应找到其在整个文档结构中的"生态位"——它与其他内容的关系、它服务的目标、它影响的其他部分。
- **协调生长**：更新一个部分时，检查并同步更新相关部分——更新工作流步骤时同步更新示例和验证清单；更新输出规范时同步更新引用该规范的其他章节；更新术语定义时全局统一替换；更新本文档后记录 `CHANGELOG.md` 并确保 `CLAUDE.md` 核心内容保持一致。
- **源代码—说明文档同步**：`docs/` 下不属于 `plans/` 或 `events/` 的文档是当前源代码、配置和公开运行协议的说明性视图。发生重要源代码、配置、CLI、协议、目录或公开 API 变更时，AI 必须在同一任务中按需检查这些文档，并同步更新受影响的设置、示例、字段、ID、路径和行为说明；`plans/` 与 `events/` 保留其计划/历史记录属性，不将其当作现行规范强制改写。同步后运行与变更范围匹配的定向一致性检查，并在 `CHANGELOG.md` 记录影响范围。
- **保持呼吸感**：章节之间应有逻辑流动，而非割裂的清单。
- **定期修剪整合**：当某个章节变得过于臃肿时，主动重构。
- **格式规范**：层级标题不使用序号前缀（用 `##` 而非 `## 1)`），Markdown 本身有层级结构，序号是冗余的形式化标记。
