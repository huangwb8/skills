# Verifier/State 设计计划：write-readme

## 结论摘要

- 目标 Skill 版本为 0.1.1（skills/alpha/write-readme/config.yaml），设计日期 2026-09-04；参考 Kernel 为 bensz-skill-kernel 1.0.0。
- 接入一个 Skill 专用、确定性的 bensz.document.readme-pair-alignment@1.0.0。它复用现有 check_readme_pair.py 的结构检查，通过未来 JSON-stdio Adapter 暴露标准 Result，不把语义质量硬编码进脚本。
- 默认复用 Kernel 原子 Verifier：bensz.artifact.path-scope、bensz.artifact.file-existence、bensz.document.markdown-link-integrity、bensz.security.secret-redaction、bensz.evidence.provenance；schema/contract conformance 在实现阶段用于结果/交付报告字段，runtime 三类 Verifier 由 Kernel 负责。
- 领域 State 只保留五个稳定节点：input-ready → facts-collected → bilingual-draft-ready → delivery-ready → reported。系统 planned/active/checking/delivering/completed/failed/waiting 与领域 State 分层，不复制动作状态。
- 事实充分性、模板适配、价值主张、双语语义由 AI/人工按证据判断；确定性组件只处理文件、结构、路径、哈希、协议和安全边界。语义 readme-fact-grounding 仅作为可选 advisory/human review。
- 不新增 Kernel 顶层元组件：双语对齐和 README 事实落地是 Skill 专属命题；通用路径、链接、脱敏、证据和生命周期已有 Kernel 支撑。

读取证据锚点：`skills/alpha/write-readme/SKILL.md#输入与输出`（约第 28–34 行）、`#工作流`（第 47–105 行）、`#质量门槛`（第 113–120 行）、`#安全与失败处理`（第 129–133 行）；`skills/alpha/write-readme/config.yaml`（第 1–26 行）；`skills/alpha/write-readme/scripts/check_readme_pair.py`（第 61–109 行）；`packages/bensz-skill-kernel/src/bensz_skill_kernel/verifiers/index.json`、`states/index.json`；`packages/bensz-skill-kernel/README.md#目录化-contract-pack`、`#state：阶段与迁移`、`#verifier：证据与-gate`（约第 35–78 行）；命名规范见 `docs/verifier-id-naming.md#canonical-格式` 与 `docs/state-id-naming.md#canonical-格式`。

## 业务流程与风险地图

| 阶段 | 已成立的事实/动作 | 主要风险 | 需要保留的证据 |
| --- | --- | --- | --- |
| 输入确认 | 目标项目、写作目标、受众和授权范围明确 | 越界读取/覆盖、把私有资料当公开事实 | 相对路径、授权摘要、输出名 |
| 事实清单 | 元数据、入口、能力、约束分为已证实/用户提供/待确认 | 臆造功能、版本、命令、性能或许可证 | 来源路径、哈希、claim/status |
| 模板与信息架构 | 选择一个主模板，确定首屏、Quick Start、示例和高级章节 | 空章节、模板拼接过长、受众错配 | 模板 ID、选择理由、章节树 |
| 双语草稿 | 先中文后英文，命令、路径、版本、链接和示例同步 | 标题树/围栏/token 漂移，英文改变事实 | 两个文件哈希、配对摘要 |
| 检查与复核 | 运行结构、链接、脱敏和语义复核 | 暂时不可观测被当成失效；AI 自评冒充通过 | Result、Gate、evidence_refs、uncertainties |
| 交付 | 仅写授权的 README.md 与 README_EN.md，并附摘要 | 未授权覆盖、漏写待确认项 | delivery report、artifact refs、最终哈希 |

缺输入、授权或网络观察条件时使用系统 waiting；required 检查失败进入 failed 或回到可修正领域节点；新尝试用新的 run_id/attempt_id，不覆盖历史。

## 删除影响测试（含“不接入”结论）

### State

- 删除 facts-collected 会失去“事实已盘点且可追溯”的恢复边界，无法区分重新读仓库和修订文案，保留。
- 删除 bilingual-draft-ready 会让双语成对产物和语义复核混在 active/checking 中，无法只重跑配对检查，保留。
- 删除 delivery-ready 会允许未完成 required Gate 的结果直接交付，保留。
- 不创建 drafting、link-checking、semantic-reviewing 等节点：它们是动作或 Verifier 过程，系统状态和事件已经足够，删除不会损失能力。

### Verifier

- 删除 readme-pair-alignment 会失去标题树、围栏、相对图片和命令/env/version token 的跨语言配对命题，通用文件或链接 Verifier 无法替代，保留。
- 删除 path-scope 或 secret-redaction 会放松越界写入和凭据泄露边界，required 保留。
- 删除 markdown-link-integrity 会让局部锚点、相对目标和外部观察缺口只能人工发现，保留；不可观测转 unchecked/manual_review。
- 删除 readme-fact-grounding 不影响确定性结构能力，故默认 advisory；严格事实场景再提升为 required。

## Verifier 设计矩阵

| 候选 | 保留/删除 | 稳定命题或状态含义 | AI/脚本分工 | 输入与证据 | Gate/转移 | 失败与人工复核 |
| --- | --- | --- | --- | --- | --- | --- |
| bensz.document.readme-pair-alignment@1.0.0（Skill Pack） | 保留，required | 中文/英文结构、围栏、相对目标和机器 token 对齐 | 脚本复用 checker，Adapter 仅做 JSON 归一化 | zh_path、en_path、语言契约、两文件哈希 | pass 才允许 delivery-ready | 缺文件/结构漂移 fail；warning 不自动升级为 pass |
| bensz.artifact.path-scope@1.0.0 | 保留，required | 读写处于授权项目范围 | Kernel rule | allowed_paths、相对路径快照 | 失败拒绝读写/交付 | ..、绝对路径、symlink 逃逸 fail-closed；授权变化 waiting |
| bensz.artifact.file-existence@1.0.0 | 保留，required（交付前） | 两份最终 README 是普通文件 | Kernel rule | 两个 artifact refs、大小/哈希 | 缺任一文件不得交付 | 修正后新 attempt；不覆盖既有文件 |
| bensz.document.markdown-link-integrity@1.0.0 | 保留，required；网络不可观测时等待 | 局部锚点/相对文件可解析，HTTP 结果如实记录 | Kernel collector | 每份 README 的 path、timeout/黑白名单 | invalid reject；unchecked/timed_out manual_review/wait | DNS/超时不自动 pass；报告披露未观测项 |
| bensz.security.secret-redaction@1.0.0 | 保留，required | 输出、日志和摘要无 Key/Token/Cookie/密码/隐私值 | Kernel rule | 脱敏后的 artifact/event 摘要 | 命中即拒绝交付 | findings 不含秘密原文；清理后新 attempt |
| bensz.evidence.provenance@1.0.0 | 保留，required | 关键事实可追溯到仓库、用户或待确认来源 | Kernel rule 校验字段；AI 归类状态 | source_ref、hash、origin、claim_ids、status | 缺 provenance 阻止 facts-collected/交付 | 缺来源 waiting 或 unresolved，不猜测 |
| bensz.document.readme-fact-grounding@0.1.0（本地 semantic/human Pack） | 条件保留，默认 advisory | 功能、命令、版本、限制与来源证据相符 | AI/人工判断，脚本只汇总 claim/evidence | subject/context/evidence、anchors、confidence、uncertainties | advisory 不阻塞；strict 时 required | uncertain/unchecked 转人工；模型自评不能覆盖规则失败 |

语义 Result 至少包含 subject、context、evidence、Kernel verdict、summary、evidence_refs、confidence、uncertainties；error/timed_out/缺证据不得转 pass。

## State 设计矩阵与最小状态图

| State | 稳定含义 | 进入条件/不变量 | Agent 操作与证据 | 离开条件与失败路径 |
| --- | --- | --- | --- | --- |
| bensz.write-readme.input-ready@1.0.0 | 目标、受众、授权和输出名已解析，尚未写 README | bensz.workspace.ready；只读输入、无私密资料 | 建立输入引用，记录 input.read-only | 来源可读到 facts-collected；依赖/授权缺失到 system waiting |
| bensz.write-readme.facts-collected@1.0.0 | 事实清单已分层，关键 claim 有 provenance | 输入可读；provenance 通过 | 读取公开配置/入口/文档，生成 claim inventory、模板候选和不确定项 | 足够到 bilingual-draft-ready；冲突/缺口回 input-ready 或 waiting |
| bensz.write-readme.bilingual-draft-ready@1.0.0 | 两份 README 已生成，结构配对但未声明可交付 | 两个 artifact refs 存在；源项目未被改写 | 先中文后英文，保留命令、路径、版本、URL 和示例 | Gate 允许到 delivery-ready；失败留在本状态修订，事实错误回 facts-collected，不确定到 waiting |
| bensz.write-readme.delivery-ready@1.0.0 | required 检查、证据和不确定性披露齐全，可准备交付 | required Result/Gate 已记录；无 secret/path/link invalid | 组装 delivery report，复核文件名、授权和待确认项 | 报告完成到 reported；新漂移回 bilingual-draft-ready |
| bensz.write-readme.reported@1.0.0 | README 对及其报告已交付，领域运行终止 | report、artifact refs、验证证据完整 | 呈现路径和限制，不重写完成证据 | 终态；修订必须新 run/attempt，随后 workspace-closed |

最小图：

~~~text
bensz.workspace.ready ⋮
input-ready → facts-collected → bilingual-draft-ready → delivery-ready → reported
      ↑             ↑                    │   │                 │
      └──缺事实──────┘                    │   └─required fail───┘（回草稿）
                                           └─uncertain/error→ runtime.waiting/failed
~~~

系统 planned → active → checking → delivering → completed 与领域节点正交；runtime.state-transition 和 runtime.task-completeness 负责生命周期合法性，领域状态不写入 Kernel reducer。

## AI/确定性分工与 Evidence Contract

### 确定性边界

- 解析 output 文件名、模板路径和检查开关；拒绝绝对路径、..、越界 symlink 和未授权文件。
- 运行双语检查：文件存在、标题层级、围栏、相对链接/图片、命令/env/version token；把 CLI 输出归一化为 JSON Result。
- 计算 artifact/source/contract 哈希，校验 JSON 字段、超时、输出上限、事件完整性和 required 结果唯一性。
- 调用内置链接、脱敏、文件存在、路径和 provenance Pack；机械失败 fail-closed。

### AI/人工边界

- 选择主模板、判断读者任务、解释事实冲突、评估 Quick Start、价值主张和章节取舍。
- 判断陈述是否由 evidence 支持、双语是否语义等价、哪些命令实际运行过；提供 claim anchor、理由、置信度和不确定性。
- 网络不可观测、事实冲突、覆盖既有 README 或高风险声明时由人工确认；不以换模型或自评掩盖缺证据。

### Evidence Contract

~~~yaml
subject:
  project_ref: <authorized repo-relative reference>
  zh_path: README.md
  en_path: README_EN.md
context:
  goal: <user writing goal>
  audience: <optional audience>
  template_id: <general|library|cli-service|web-app|data-ml|agent-skill>
  language_contract: aligned-structure
evidence:
  - source_ref: <repo-relative or sanitized user reference>
    content_hash: <sha256>
    origin: repo|user|external
    claim_ids: [claim-001]
    status: verified|user-provided|inferred|unresolved
artifacts:
  - path_ref: README.md
    content_hash: <sha256>
    role: chinese-readme
~~~

事件只保存相对引用、哈希、状态和摘要；不保存凭据、完整 Prompt、原始上下文、个人信息或不必要绝对路径。

## Kernel 对接、Gate、重放与资源边界

实现阶段在 skills/alpha/write-readme/config.yaml 增加 runtime，并新增：

- skills/alpha/write-readme/references/states/<state>/STATE.md：五个领域状态，frontmatter 使用 canonical ID、独立 version、唯一 alias 和 transitions。
- skills/alpha/write-readme/references/verifiers/readme-pair-alignment/{VERIFIER.md,index.json,scripts/verify.py}：Pack 契约、元数据和 JSON-stdio Adapter；复用现有 checker，不改 CLI 兼容行为。
- 可选 readme-fact-grounding Pack：仅在用户要求严格事实审查或出现高风险外部声明时启用。

建议 runtime 语义（字段名以实现时 Kernel schema 为准）：

~~~yaml
runtime:
  kernel: {name: bensz-skill-kernel, version: '1.0.0'}
  state_roots: [references/states]
  initial_state: bensz.workspace.ready
  states: [bensz.write-readme.input-ready, bensz.write-readme.facts-collected,
           bensz.write-readme.bilingual-draft-ready, bensz.write-readme.delivery-ready,
           bensz.write-readme.reported]
  verifiers:
    - {id: bensz.document.readme-pair-alignment, version: 1.0.0, required: true}
    - {id: bensz.artifact.path-scope, version: 1.0.0, required: true}
    - {id: bensz.artifact.file-existence, version: 1.0.0, required: true}
    - {id: bensz.document.markdown-link-integrity, version: 1.0.0, required: true}
    - {id: bensz.security.secret-redaction, version: 1.0.0, required: true}
    - {id: bensz.evidence.provenance, version: 1.0.0, required: true}
~~~

Gate：required 缺失、版本不符、组件重复/漏跑、fail、error、非法路径或敏感信息命中均不允许交付；uncertain/unchecked/timed_out 进入 manual_review/waiting，除非用户明确接受并在报告披露。advisory 不覆盖 required 失败。

每次运行绑定 run_id/attempt_id；事件包含 Pack/契约/组件哈希、canonical ID@version、evidence refs、执行状态和 Gate。bsk rebuild 只重放事件与快照，不重新调用模型/网络；哈希漂移、缺 Gate 或快照不完整返回结构化错误并 fail-closed。路径、网络、子进程和大输入使用 Kernel 默认最小权限、超时、输入输出上限和进程组终止；Skill 不自行放宽默认值。

## Kernel 复用与元 Verifier/State 提炼决策

### 现有 Kernel 能力盘点

实际读取了 verifiers/index.json、states/index.json、相关 VERIFIER.md 与 Kernel README。相关条目：

| Kernel 能力 | 版本/类型 | 用途 |
| --- | --- | --- |
| artifact.file-existence | 1.0.0 / atomic rule | 交付前确认双语文件存在 |
| artifact.path-scope | 1.0.0 / atomic rule | 授权范围和 symlink 越界 |
| artifact.schema-conformance | 1.0.0 / atomic rule | Result/报告字段（实现阶段按需） |
| contract.conformance | 1.0.0 / atomic rule | 交付/组件契约字段（实现阶段按需） |
| document.markdown-link-integrity | 1.0.0 / composite rule | Markdown anchor、相对目标和 HTTP 观察 |
| security.secret-redaction | 1.0.0 / atomic rule | 防止 README、日志、事件泄露秘密 |
| evidence.provenance | 1.0.0 / atomic rule | 事实来源、哈希和 claim 绑定 |
| runtime.state-transition/task-completeness/event-integrity | 1.0.0 / atomic rule | 生命周期、完成 Gate 和回放 |
| evidence.citation-truth-fit | 1.0.0 / semantic prompt | README 非论文引用语义，默认不适用 |

### Kernel 复用结论

- 直接复用 file-existence、path-scope、secret-redaction、evidence-provenance：字段和失败语义匹配文件/安全/证据边界，继承 Kernel 的 fail-closed、版本和事件绑定，避免重复脚本和维护面。
- 组合/适配复用 markdown-link-integrity：它覆盖链接和 anchor 但不理解双语配对；两个文件分别调用并由 Pair Adapter 汇总，避免把 URL 可达误称为事实正确，网络不可观测保持 unchecked/timed_out。
- schema-conformance、contract-conformance 在实现阶段按需复用：机械校验标准 Result 和 delivery report，claim 判断留在 Adapter/AI，若 Kernel 默认字段足够则不重复声明。
- 系统层直接复用 state-transition、task-completeness、event-integrity：这些能力决定状态边、完成门禁和重放，不能由 Skill 专用 Verifier 替换；领域状态只提供 entry/exit/invariant。

### 元组件提炼结论

- 明确不提炼 readme-pair-alignment：标题/围栏/token 同步和双语文件对是本 Skill 的专属命题，当前没有第二个不相邻领域共享同一契约；提升到 Kernel 会增加术语、误报规则和版本维护成本。
- 明确不提炼 readme-fact-grounding：虽有跨领域潜力，但目前耦合模板、受众、README 首屏和双语语义，且 AI/人工判断不可由 Kernel 复现；先做本地 advisory/human Pack，收集两个领域的同构证据后再评估。
- 保持通用底层在 Kernel：路径、文件、链接、脱敏、provenance、事件和 Gate 已跨场景复用；write-readme 只提供薄 Adapter，不复制执行器。

### 对人类决策的影响

- 采纳会新增 config.yaml.runtime、5 个 STATE.md、一个 Pair Verifier Pack、Adapter 测试和版本/CHANGELOG 记录，不改 README 生成逻辑或 Kernel reducer。
- 默认 required 链接检查可能因网络不可观测进入人工等待；若运营场景不能接受，应把本地 anchor/相对路径设为 required、HTTP reachability 设为 advisory，并同步 Gate/测试。
- 不采纳 semantic Verifier 可降低成本，但严格事实场景需人工审阅；不能把 advisory 缺失伪装成自动保证。

## 实施顺序（P0/P1/P2）

本轮不实施，仅给后续交接顺序。

### P0：安全与完整性

1. 在 config.yaml 增加 Kernel 1.0.0 runtime，建立 references/states 与 Pair Pack；完成条件：Pack/index、State frontmatter、canonical/alias 一致。
2. 为 check_readme_pair.py 增加不改变 CLI 的 JSON-stdio Adapter；完成条件：缺文件、标题/围栏/相对目标/token 漂移返回稳定结果，异常返回 error。
3. 接入 path-scope、file-existence、secret-redaction 和 runtime 完成门禁；完成条件：越界、symlink、秘密和 required 缺失 fail-closed。

### P1：契约与可观测性

1. 实现五节点 State 和事件记录；完成条件：入口/出口、不变量、waiting/失败/新 attempt 可重放。
2. 接入 markdown-link-integrity、evidence-provenance、schema/contract conformance；完成条件：Result 绑定版本、组件、证据 refs、run/attempt，网络不可观测不自动通过。
3. 编写事实清单和 delivery report Schema；完成条件：报告列模板、运行命令、未运行命令、待确认项和文件哈希。

### P2：可选改进

1. 增加 readme-fact-grounding semantic/human Pack，仅在 strict 或高风险外部声明时启用；完成条件：不确定性、人工身份和确认时间可审计。
2. 用真实样本决定 HTTP reachability 的 required/advisory 分流；本地链接失效仍阻塞，外部不可观测有人工路径。
3. 收集两个不相邻文档/生成领域的同构证据后，再评估 Kernel 元 Verifier；未满足前不改 Kernel。

## 验收与回归测试

实现阶段至少覆盖：

- Pack/index、Pair Verifier canonical 与 alias 双路径解析，版本不符拒绝。
- 缺少一份 README、非普通/不可读文件、绝对路径、..、symlink 逃逸和越界输入。
- 标题树、围栏、相对文件/图片目标、命令/env/version 漂移；checker warning 不得误算 required pass。
- 本地 anchor/相对链接失效、HTTP 4xx、DNS/超时、重定向内部地址；验证 fail、unchecked、timed_out 和 waiting。
- secret-redaction 命中（findings 不含原文）、provenance/schema/contract 缺字段、required 缺失。
- State 允许/禁止转移、facts-collected 回退、草稿修订新 attempt、waiting 恢复、failed 终态、reported 后禁止原地重写。
- 事件/快照重放、哈希漂移、组件重复/漏跑、run/attempt 串台、Gate 缺失和伪造 aggregate pass。
- 语义 Verifier 的 pass/fail/uncertain/unchecked/error、人工身份及 advisory 不阻塞。

建议命令（实现后）：

~~~bash
python3.12 skills/alpha/write-readme/scripts/check_readme_pair.py \
  skills/alpha/write-readme/README.md skills/alpha/write-readme/README_EN.md
python3.12 -m pytest packages/bensz-skill-kernel/tests
bsk verifier list --root skills/alpha/write-readme/references/verifiers
bsk state list --root skills/alpha/write-readme/references/states
git diff --check
bac verify --json
~~~

本轮已实际运行双语 checker、bac verify 和 git diff --check；未运行实现后的 Pack/State discovery 或 Kernel 全量测试，因为没有实现组件。

## 已知不确定性、回退方案和不在范围内的事项

- runtime 声明字段和本地 Pack discovery 的最终 CLI 形态需在实现时以 Kernel 1.0.0 实际 API 校对；本计划不扩展协议。
- 当前 checker 把 token 漂移作为 warning；是否升级为 fail 要用真实 README 样本校准，默认结构/链接错误阻塞，token 漂移由语义复核决定。
- HTTP 可达性受网络、robots、速率和站点变化影响；unchecked/timed_out 不能当失效或通过，必要时降为 advisory 并披露。
- 语义事实审查仍由 AI/人工完成，Kernel 不能证明模型遵守写作契约；不得保存完整 Prompt 或敏感原文。
- 不实现 Kernel 源码、模型网关、远程发布、自动提交、批量迁移其它 Skill、README 内容本身或正式 VERIFIER.md/STATE.md。
- 若发现 Skill/Kernel 设计缺陷，按 bensz-collect-bugs 脱敏记录到 ~/.bensz-skills/bugs/，不修改系统级已安装 Skill。
