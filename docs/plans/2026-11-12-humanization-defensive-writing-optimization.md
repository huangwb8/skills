# humanization：防御性／法务式写作约束与 BSK Verifier 优化计划

> **日期：** 2026-11-12\
> **对象：** `huangwb8/skills/skills/alpha/humanization`\
> **基线：** 仓库 `main` 分支当前 `config.yaml:skill_info.version = 2.1.0`（本计划读取时）\
> **交付性质：** 设计与实施计划；尚未修改仓库源码、安装副本或 BSK Kernel，也未执行新的写作质量实验。\
> **用语：** 本计划中的“法律性写作”主要指对话中所说的**法务式、防御性、过度免责的表达**，不指为了法律效力所必需的正式法律文本；后者必须单独保护。

## 通俗解释：究竟要改善什么

**一句话说明：** 现有 Skill 擅长防止 AI 在润色时改错意思，却不能稳定阻止 AI 把本来直接的判断包装成一连串“我不主张……”“这并不意味着……”“还需指出……”的自我防御；要为这种残留增加可复核的质量门禁。

**具体场景：** 一位研究者写：“我们的结果提示不同中心之间存在稳定的分子关联。”AI 改成：“需要强调的是，尽管结果具有一定参考意义，但这并不意味着我们已经证明其普遍适用性，也不能排除其他因素，仍然需要谨慎看待。”文字看似稳妥，却把原稿真正表达的发现压到了后面，并添加了原文未规定的限制。

**改进后：** 先完整保留原稿的证据强度与研究对象，再由审查者逐条回答：这项限定是否改变结论的解释？是否有原文依据？是否只是反驳作者没提出的主张？与附近文字是否重复？无信息的防御性包装删掉；真正必要的范围、阈值、分母、风险和临床外推限制继续保留。

可把它理解成两名不同职责的校对员：**语义保真员**防止删掉实质条件，**防御性表达审查员**防止把无效免责和假想反驳留在最终稿。只有二者都认可，BSK 才批准当前冻结版本。

## 专业判断：现状与真正的缺口

### 已确认的仓库事实

- `humanization` 当前为 **2.1.0**，服务于**已有文本润色**，不负责从零写作、事实检索、补证据或改变全局聊天风格；这一边界应保留。
- 主 Agent 写作，`parallel-vibe` 的 **3 个独立子 Agent**审查同一冻结产物；**至少 2 票 pass**，外部最多 **5 轮**；第 5 轮仍未通过时，交付**明确注明未获批的最后草案**，状态仍为 `working`。
- BSK 已有 `bensz.revision.working → bensz.revision.ready` 两个领域 State、`bensz.prose.revision-readiness@1.1.0` 一个 required 混合 Verifier、`scripts/control.py` 唯一编排入口。当前 `VERIFIER.md` 已要求审查独立限定、净改善、文本/附件哈希、语义安全。
- `references/machine-patterns.md` 已包含“边界声明压缩”“元评论和伪对立”等规则；所以**不应再堆一份同义禁词清单**。
- `scripts/revision_evidence.py::validate_review()` 验证的是审查记录结构、锚点与若干关联，不验证语义结论是否正确。`control.py` 的提交处理目前对**每个** verdict=`pass` 的回传调用同一个 `validate_review()`；新增第二种 Verifier 需要按身份分派各自 schema。
- 已有社区调查 `docs/events/2026-11-04-humanization-community-survey.md` 曾分析 11 个项目，明确警告“每个主张最多保留一项限定”“强制主动语态”“句长配额”等规则可能误伤科学内容。不能把这次计划写成此前从未考虑过防御性写作。

### 缺口是判定与执行，不是再写几句提醒

1. **缺专项判定：** 没有将“残余的无效免责、假想反驳、结论后置、重复否认、审稿人预答辩”作为独立验收命题。现有八维比较可能认为文章有净改善，却对这些问题没有明确否决理由。
2. **缺证据化的处置：** 防御性片段目前可出现在边界处置表中，但没有统一区分“必要限定、重复限定、纯姿态、虚构反方、证据不足”，也不要求记录“删后哪处仍承担原有功能”。
3. **缺相互制衡的 Gate：** 单个复合审查把语义安全和文风揉在一起，可能出现“很安全但仍然满篇免责”或“更干脆但增强了结论”的假通过。
4. **缺真实效果证据：** 既有 BSK 协议、短文回归与同宿主审查只能证明门禁链能跑，不能证明它降低了实际 GPT 产出的防御性写作。

### 社区经验如何取舍

| 来源 | 值得借鉴 | 不采用的部分 |
| --- | --- | --- |
| OpenAI 开发者社区 2026-10-29 的重复 caveats 抱怨 | 针对**未被用户提出的极端结论**和“同一免责声明反复出现”做测试 | 用户抱怨不能直接当作模型缺陷的定量证据 |
| `blader/humanizer` | 优先捕捉句段功能、假对立、开场铺垫、无信息收束，而非只按高频词替换 | 强制所有命中都改、为制造个性加入原文不存在的事实 |
| `conorbronsdon/avoid-ai-writing` | `detect`/`edit`/`rewrite` 分离、分级严重性、低误报与保留原文、受控二次修订 | 直接复用仅校准英文的词典来判中文科研文本 |
| `Worigin0314/academic-defensive-writing-auditor` | 先问“删掉是否会误导”，再判断是否只是在预先回应假想审稿人；区分必要 caveat 和 defense | “每项主张最多一个限定”“统一移到 Limitations”会丢失独立边界 |
| UK AISI《Ask Don't Tell》 | 当输入本身是带有立场的陈述时，先转化成待检验的命题可降低迎合；启发评审的**独立判断问题** | 该研究测的是迎合，不是论文润色；不应让 Skill 私自补新论点或改变用户立场 |

## 要达到什么目标

**正常文本效果：** 原稿里本就存在的明确判断更早、更直接出现；没有信息贡献的“首先免责再回答”“未提出观点先反驳”“重复强调自身有限性”被压缩；句段推进自然，但不制造新的自信和断言。

**技术效果：** 每个批准的冻结版本都拥有两个**可区分**的 required 审查结果：**语义/格式/证据边界保持**和**防御性写作残留审查**；任一结果缺失、失败或未执行都不能得到 `ready`。两者独立提供失败原因，而非用单一平均评分掩盖问题。

**不在范围内：** 解除模型安全策略、绕过合规限制、自动改写所有 ChatGPT 回复、让原稿没有的观点凭空出现、替代医学/法律/论文事实核验、增加新 State/Kernel 功能、改动系统级已安装 Skill 或直接向 GitHub 提交。若将来需要全局回答风格控制，应由**明确选用的上层路由/宿主输出环节**单独集成，不把这个仅做润色的 Skill 伪装成拦截器。

## 改进方向

### 用五个问题判定一句话是否真的在防御

在 `references/machine-patterns.md` 引入一份简短的 `references/defensive-writing.md` 专题契约，专供诊断和 Verifier 引用。每个被标记的句段须回答：

1. **必要性：** 删除这项限定，会不会改变事实、证据强度、适用范围、责任、行动阈值、风险理解或下一步决策？
2. **来源：** 这项限定对应原稿的哪一句、哪项实际条件？若候选新添了谨慎措辞，是否只是模型对风险的想象？
3. **对象：** 它是在回应作者真实陈述/文档真实问题，还是在反驳从未提出的极端解释或假想审稿人？
4. **重复与位置：** 相同的语义边界是否已经在本阅读单元中清楚给出？若合并/移动，是否仍能独立理解？
5. **替代性：** 是否能以“有依据的主张 → 关键事实/证据 → 必要边界”的形式表达**同一含义**，而非只删“不”“可能”等字？

只对**具体、可定位、能解释危害**的残留给失败；单独出现“可能”“但”“并不意味着”或科学术语，不是失败理由。针对每项归入：`necessary`（必须保留）、`redundant`（可合并）、`anticipatory`（假想反驳）、`performative`（姿态式免责）、`mixed`（含有真正信息和多余包装）、`unresolved`（尚不能判断）。对应操作为 `keep / compress / rewrite / delete / human_review`。

“删除”仅用于原文/候选中已可证明无独立信息的包装；`mixed` 优先将技术条件写进主句；`unresolved` 保留而不是强行变得自信。禁止新增原稿没有的范围、否定、承诺或事实。

### 两个 required Verifier，各守一道门

**建议增加一个专用领域 Verifier，而不再增加 State：**

| 组件 | 职责 | 如何判定 | Gate 角色 |
| --- | --- | --- | --- |
| 保留 `bensz.prose.revision-readiness` | 原始语义、数字、LaTeX、条件、证据级别、输出结构及净改善保护 | 原有机械 `revision-facts` + 人工/Agent `semantic-review`；必要时补充功能保全检查 | `required`；语义/格式有已证实严重缺陷则拒绝 |
| 新增 `bensz.prose.defensive-framing`（建议 v1.0.0） | 冻结候选是否仍有**可确认且重要的**无效防御性表达；删除是否造成新风险 | `defensive-facts`（脚本仅定位线索、去重、生成证据指针）+ `defensive-review`（Agent 语义裁决） | `required`；重大残留或误删必要限定则拒绝 |

新 Pack 放在 `skills/alpha/humanization/references/verifiers/defensive-framing/`，登记至现有 `references/verifiers/index.json`，在 `config.yaml.runtime.verifiers` 增加同一 required 依赖；继续使用已有 `control.py` 做全部 required → Gate → 状态迁移。**不新增 BSK Kernel Verifier，不复刻第二套编排器。**

“独立 Verifier”不是要求多召集三名 Agent：继续由当前 `parallel-vibe` 并行启动**同一组三名审查者**，各自看同一冻结原稿和候选、对两项审查命题分别给出 verdict。主 Agent 将结果汇总为**两个**独立绑定的 BSK ComponentResult；这样新增成本主要是审查任务内容，而不是将外部模型调用数简单翻倍。

**审查投票策略：** 保持现有 3 人、2 票、5 轮默认值；但将 `pass/pass/fail` 的异议区分为普通文风分歧与**实质性红线指控**。后一种（新增承诺、丢失阈值、改了分母、删掉必要法律条款等）不得仅靠多数票直接覆盖；需要主 Agent **核对原文/候选锚点，修复或提交可复审的驳回理由**，如仍有实质不确定性则不批准。这不是“任何一票拥有无限否决权”，而是严重问题必须结案，不能丢在少数意见里。

**判断严格度：** 新 Verifier 只针对可确认的**重大**残留设失败；对弱、孤立、有合理用途的表达给 `pass`（附建议）或 `uncertain`（必要时人工确认），防止为了追求满分而无限修改。`keep_original` 如原文已经很好可照常通过；如原文确有大量无效防御内容，不能仅凭 `keep_original` 豁免文风目标；`diagnosis_only` 则检查诊断是否正确识别问题，不要求实际改写。

### 把 Verifier 的“自我声称”变成可审计证据

每次语义审查保留 BSK 当前 `run_id/attempt_id`、handoff、文件哈希和 evidence_refs；专项审查增补下面的证据字段（**内部记录，默认不出现在 `text_only`**）：

```json
{
  "defensive_audit": {
    "scope": "text",
    "items": [
      {
        "source_anchors": [{"artifact":"original","start":0,"end":12}],
        "candidate_anchors": [{"artifact":"text","start":0,"end":18}],
        "pattern": "anticipatory_rebuttal",
        "necessity": "performative",
        "disposition": "rewrite",
        "materiality_reason": "该句仅反驳原文未提出的夸张解释",
        "preserved_function": "原文主张在候选相邻句中完整保留"
      }
    ],
    "unresolved_material_findings": []
  },
  "reviewers": [
    {"result_ref":"parallel-vibe/.../RESULT.md","verdict":"pass","artifact_hash":"sha256:..."}
  ]
}
```

上述 JSON 是**示意性契约**，`start/end` 延续当前 Python Unicode 字符区间 `[start,end)`；具体字段和类型必须以生产 BSK 标准 ComponentResult 为外壳，不自造新顶层结果协议。涉及隐私的正文留在授权任务文件，事件/汇总仅保存相对路径、哈希、类别、锚点和短理由，避免复制大段原文。

确定性脚本只检查字段类型、锚点范围、证据哈希、文件/参数绑定、重复的 reviewer 路径、票数计算以及已标记 issue 的“处置去向”。它**不能**因为包含“不能”“可能”“值得注意的是”就自动判失败，也不能凭 JSON 字段齐全宣称事实真实。子 Agent 的语义解释和最终结案必须是真实宿主执行。

现有 `control.py` 需要按 Verifier ID 调用各自校验逻辑；不能沿用“任何 pass 都跑 `validate_review()`”的写法。两个 Pack 的 result/handoff、`required` 和 Gate 应在同一 attempt 中统一冻结、逐一校验和回读；新 Pack 的 `facts` schema 与旧 Pack 分离，旧版历史回执仍可在对应契约下读回。

### 把“结论优先”做成按需编辑策略，而不是全文格式命令

新增“直接表达”检查：如果原稿已有明确结论，但候选在开头先用两三句话否认用户从未提出的解释，先将**原有结论**放回叙述核心，随后仅留下必要条件。默认不强制“第一句一定是结论”，因为叙事文本、Discussion 的论证铺垫、复杂科学论证和承接前段内容可能确有必要。**不是固定句序，而是优先让重要信息早于无信息的免责。**

针对带有明显立场的输入，可以在内部把“作者究竟主张什么、证据在哪里、允许的推断范围是什么”重写成中性审查问题，要求审查者独立核查；这借鉴 AISI 的“Ask Don't Tell”，但不能悄悄替换作者观点或在润色时补出新事实。

### 为论文、基金与医学文本设保留反例

分语域评判是否真正需要限定。法律条款中的权利义务、告知义务和责任范围不能被当成“法务腔”删除；科学文本中的抽样范围、相关与因果、探索性/验证性定位和外推边界不能因读起来不果断而升级；医学文本中的危险信号、适应证、禁忌证和关键决策条件不能删。**即使多个限定相邻，若分别改变解释，全部保留，不设置数量上限。**

下面四种情况应有清楚的正反例：

| 场景 | 应修的防御性 | 必须保留的真实边界 |
| --- | --- | --- |
| 一般讨论 | 在回答“X 是否有效”前解释“这不代表 X 能解决一切问题” | 用户真实提出的反例或直接影响结论的条件 |
| 论文结果 | “我们并不声称已解决全部肿瘤分型问题” | “该关联仅在内部队列验证，未做外部验证” |
| 国自然标书 | “需要说明本项目并不是要证明所有平台完全一致”反复出现 | 明确研究所检验的跨队列关系及其不等同于临床获益 |
| 医学与法律 | 把同一泛化免责声明重复三次 | 会改变临床决策或法律责任的具体、必要条件 |

### 优化循环仍然有界，不用五轮“磨出另一种机器味”

保留两个内部表达/安全复核预算和五轮外部审查上限。每轮主 Agent **只修复带明确证据锚点的实质问题**，优先最小修改；错误风险比风格建议优先。连续一轮没有可证明净改善时，优先 `keep_original` 或保留当前最优草案，而不是为了消除全部标记继续制造改写。第 5 轮仍不通过，按 v2.1.0 原合同明确标注未获批并提交草案，`working` 不伪造 `ready`。

## 实施范围与顺序

| 优先级 | 要做的事 | 最小影响范围 | 完成定义 |
| --- | --- | --- | --- |
| P0 | 固定 2.1.0 基线与测试稿；明确防御性/必要限定判别契约和保留反例 | `references/defensive-writing.md`、`machine-patterns.md`、`regression-cases.md` | 每个正反例都能说明删改理由，不依赖禁词频率 |
| P0 | 新增 `defensive-framing` required 混合 Pack；接入现有 runtime 索引和唯一入口 | `references/verifiers/index.json`、新 Pack、`config.yaml`、`control.py` | 两个结果齐全且均通过才迁移 `ready`，失败和缺失都保持 `working` |
| P0 | 按 Pack ID 拆分 `facts` schema 校验；审查者证据和严重异议可追溯 | `scripts/revision_evidence.py`、`references/runtime-control.md`、相关回归 | 不允许用空审查项、假锚点、旧稿票据或“多数票”掩盖严重问题 |
| P1 | 调整主 Agent 编辑/子 Agent 审查分工：同三人分别审两命题、对已证实问题做最小复写 | `SKILL.md`、原 `revision-readiness/VERIFIER.md`、新 Pack `VERIFIER.md` | 无新增编排器；真正的语义审查结果与各自 handoff 绑定 |
| P1 | 增加中文/英文、论文/基金/医学/法律、优秀原文免改和 `diagnosis_only` 回归 | `references/regression-cases.md` 与根级测试 | 无安全回归、无强制词禁、原格式保护有效 |
| P2 | 在真实授权长文上对照旧版/新版，按盲评决定是否启用为默认 | 工作区评测材料，报告；必要时微调规则 | 有作者/领域评审支持，而不只是“Gate 能跑” |

**不新增领域 State。** `working` 已涵盖编辑、冻结、待审查、重试；`ready` 已表示两个 required 审查全部获批。新增 `defensive_ready`、`under_review` 等只是状态膨胀。**不提炼 Kernel 元 Verifier。** 这个判定高度依赖具体写作语境，还没有跨两个独立领域可复用且语义稳定的证据；部署在 `humanization` 自有 Pack 成本更低。复用 Kernel 的 Pack 发现、绑定、Gate、transition、事件与重放能力，而不让 Kernel 关心“AI 腔”。

## 如何确认完成

### 工程门禁：必须跑的反例

1. 旧 Pack `pass`、新 Pack `fail/uncertain/unchecked` → Gate 不放行，仍 `working`；反向同理。
2. 旧/新结果均 `pass`，但冻结文本或参数哈希改变 → 不放行；新 attempt 重新审查。
3. 未返回三名有效 reviewer、同一结果冒充三票、缺少锚点/处置/证据、引用了另一轮 `RESULT.md` → 阻塞或报告未审查，不能伪装成通过。
4. `pass/pass/fail` 存在有锚点的阈值、分母、承诺等严重问题 → 不得仅计票通过；必须处理该问题并留下结案证据。
5. 机械扫描命中“可能”“但”“不意味着”，但其是真正科学或法律限定 → 不自动拒绝；只由真实语义审查判断。
6. 只改普通英文；保留 LaTeX/数学/注释/引用；原文已优秀；只做诊断；第 5 轮兜底；中断恢复/重放 → 维持既有行为。
7. 受控 `ready` 回执只批准原字节；禁止 `ready` 之后再补一句“但不构成……”使审核失效。

运行现有 `tests/test_humanization_protection.py` 及相关 BSK 控制测试，执行 `verifier-state-architect` 的 Pack 集成检查，核对公共约束块、README 中英文、CHANGELOG 与 BAC 审计。必须使用**按安装器确认的生产 BSK**和托管 Python 做真实成功/失败路径验证，不把仓库中测试协议或合成回传写成真实独立审查。

### 写作质量：如何判断不是形式主义

使用 12 个开发单元调规则，另保留至少 24 个**未见过**的评测单元（短对话、长段落、论文/标书、医学/法律、优秀原文、独立限定密集文本；中英均覆盖）。同一模型和设置对照：`v2.1.0` 基线、仅新增编辑规则、规则+新 Verifier 三个条件；另将原文作为允许胜出的对照。每单元至少两次生成，随机匿名呈现，最好由两位熟悉相应文体的评审者先检查语义红线，再成对判断文风与有效信息密度。

建议把以下门槛定义为**预设工程目标，而非未经测试的效果声明**：

- **安全硬门槛：** 不允许已确认的严重语义、科学、医学或法律含义回归被标记为获批；任何此类回归须修复并重新测试。
- **主要收益：** 在原本确有防御性问题的保留样本中，至少 2/3 的样本获评为新版更直接、更少无效防御且没有损失信息；不追求“所有文字更短”。
- **误伤控制：** 必要限定密集的负例中，独立边界不得因“反防御”误删。发现误删就是规则失败，不用平均分抵消。
- **复杂度消融：** 如果“仅新增编辑规则”和“加 Verifier”效果基本一样，而后者成本明显增加，则降级新 Pack 为 advisory 或撤回，保留更简单方案。**只有增量收益能支撑强制门禁，才维持 required。**

报告真实样本数、模型与配置、生成次数、失败率、平均轮数、各 Pack 的拒绝原因、延迟/调用成本、原文胜出和平局比例。不要把同一模型的三个审查者视为完全独立的人工评审，也不能凭脚本通过宣称整体文风改善。

## 风险与回退

- **防御过矫正：** 为求直接而删去必要的“可能”、适用条件或重要风险。通过原稿–候选双向追踪、保留反例和语义 required 门禁防止；必要时原文免改。
- **自证循环：** 主模型写稿，三个同源模型按相似规则给 pass。至少要求分离角色、冻结稿件、独立结果与可审计锚点；若条件允许，用不同模型或人工做离线盲评，但不宣称身份字段能证明认知独立。
- **过度工程：** 多一个 Pack 可能增加 schema、回归、调用与发布负担。先测删除影响：若独立 Gate 无法带来可测改善，就回归一个 required Verifier + 明确的防御性审查段落。
- **兼容变化：** 新增 required Pack 改变了审批合同，尽管不一定改变用户输入/输出，仍必须维护独立 Pack 版本、更新 Skill 版本及文档，并保留旧版本的历史读取。建议先以开发副本试验，最终版本号按实际兼容范围决定，不提前声称 2.2.0 已发布。
- **边界限制：** 本 Skill 不控制普通聊天，也不能绕开模型/宿主安全策略。模型原本未写出独立观点时，忠实润色只能清除包装，不能凭空找回缺失的分析；这种问题要另用“问题重构/独立批判”的上游工作流处理。

## 仓库落地与参考来源

建议正式实施计划存为仓库 `docs/plans/2026-11-12-humanization-defensive-writing-verifier-optimization.md`，先固定当前 `main` 提交 SHA 与未提交改动，再在**开发源码副本**实施，不覆盖安装目录；本文件只是可直接放入该位置的计划草稿。

**已检查的仓库依据：**

- [`humanization/SKILL.md`](https://github.com/huangwb8/skills/blob/main/skills/alpha/humanization/SKILL.md)
- [`humanization/config.yaml`](https://github.com/huangwb8/skills/blob/main/skills/alpha/humanization/config.yaml)
- [`humanization/references/verifiers/index.json`](https://github.com/huangwb8/skills/blob/main/skills/alpha/humanization/references/verifiers/index.json)
- [`revision-readiness/VERIFIER.md`](https://github.com/huangwb8/skills/blob/main/skills/alpha/humanization/references/verifiers/revision-readiness/VERIFIER.md)
- [`scripts/control.py`](https://github.com/huangwb8/skills/blob/main/skills/alpha/humanization/scripts/control.py)
- [`scripts/revision_evidence.py`](https://github.com/huangwb8/skills/blob/main/skills/alpha/humanization/scripts/revision_evidence.py)
- [`runtime-control.md`](https://github.com/huangwb8/skills/blob/main/skills/alpha/humanization/references/runtime-control.md)
- [`2026-11-04 社区调查`](https://github.com/huangwb8/skills/blob/main/docs/events/2026-11-04-humanization-community-survey.md)
- [`2026-11-08 BSK 设计`](https://github.com/huangwb8/skills/blob/main/docs/plans/2026-11-08-humanization-verifier-state-design.md)
- [`writing-plans/SKILL.md`](https://github.com/huangwb8/skills/blob/main/skills/alpha/awesome-code/agents/writing-plans/SKILL.md)
- [`verifier-state-architect/SKILL.md`](https://github.com/huangwb8/skills/blob/main/skills/alpha/verifier-state-architect/SKILL.md)

**社区方法依据：**

- [OpenAI Developer Community：Excessive caveats and repetitive disclaimers](https://community.openai.com/t/excessive-caveats-and-repetitive-disclaimers-make-chatgpt-conversations-exhausting/1410602)
- [blader/humanizer](https://github.com/blader/humanizer)
- [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing)
- [Worigin0314/academic-defensive-writing-auditor](https://github.com/Worigin0314/academic-defensive-writing-auditor)
- [UK AI Security Institute：Ask Don't Tell](https://www.aisi.gov.uk/research/ask-dont-tell-reducing-sycophancy-in-large-language-models)

**结论：** 实施优先级是**专项防御性判定 → 独立 required BSK Gate → 证据与异议可追溯 → 盲评消融**。保留已有安全保真、三人审查和工作流，不将“多写规则”误认为“提高写作质量”。
