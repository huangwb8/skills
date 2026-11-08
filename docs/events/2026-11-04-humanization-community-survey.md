# humanization 社区调查：哪些做法值得融入

## 结论

`humanization` 的主要短板已经不是识别不到“赋能、闭环、重要意义”。当前版本具备语义保护、段落推进、语域适配、原稿比较和免改规则，基础比许多热门同类 Skill 更稳。下一轮更值得投入的是：**给改写提供可信的作者风格依据，按基金申请的任务判断表达，并用真实长文确认这些规则是否有效。**

社区值得吸收的是判断方法，直接搬入规则清单可能适得其反。尤其不能采用句长配额、限定数量上限、强制主动语态、制造随机性或虚构研究经历来增加“人味”。“科学家普遍觉得 Codex + GPT 写作有 AI 味”是本次需求的出发点；本调查没有测量其普遍程度，也不据此归因于某一模型。

调查日期：2026-11-04。范围为本仓库现状、社区 Skill 原始契约及重点参考文件；本轮没有执行新版写作实验。

**另有一个直接影响评估的发现：仓库源码为 1.5.0，本会话可发现的本机 Codex 安装副本为 1.3.0。** 后者默认 `aggressive`、一轮自评，仓库则为 `moderate`、两轮，并已增加正向自然写作指导。不能把某次使用旧安装副本的体验归到仓库现版，也不能据此认定其他科学家遇到同样的问题。本轮仅只读核对，没有更新安装副本；后续比较必须记录实际加载路径、版本和正文哈希。

## 调查方法与证据边界

先读取本地 `SKILL.md`、配置、三个参考文件、保护检查脚本、中文指南、变更记录、既有优化计划及相关测试。再通过 GitHub 仓库搜索，以 humanizer、中文学术润色、scientific writing 等关键词发现候选，读取 11 个项目的 Skill 入口，并对最相关的学术、基金、作者声音和误改边界深入阅读。公开源码按 commit 固定，下载文件记录 SHA-256，没有执行第三方代码或安装其 Skill。

本地发现缓存不存在。SkillsMP 搜索页可以访问，但取得页面不等于验证了独立用户评价；Reddit 请求返回 403。GitHub 后续触发限流，因此只使用此前取得的仓库指标、Issue/PR 列表与源码；未取得的讨论正文没有被当作证据。这里的“系统调查”指有明确范围、比较维度和来源记录的工程调查，不是穷尽搜索或系统性文献综述。

Stars、Forks 和更新时间只说明传播与维护信号。热门仓库未必适合标书，小仓库也可能提供更好的编辑机制。多个候选共享 blader、Humanizer-zh 或 Wikipedia 的来源，不能把相似规则算成多份独立效果证据。

## 社区方案比较

下表按对本任务的启发归类。指标是本轮 GitHub API 返回的仓库级快照；“最近推送”不等于本 Skill 的最后实质修改，集合仓库的 Stars 也不属于单个 Skill。全部候选均未归档，并实际包含 `SKILL.md`。

| 项目与来源 | Stars / Forks；最近推送 | 值得吸收的做法 | 不宜照搬的部分 |
| --- | --- | --- | --- |
| scientific-manuscript-editor [S1] | 73 / 3；10-08 | 区分内容依据与表达依据；作者认可的周边正文优先；删除前确认其论证功能在何处保留 | 整套稿件管理、会话交接和证据审阅超出普通润色；不能全部引入 |
| humanizer-zh-next [S2] | 240 / 8；10-25 | 通用入口加按需基金参考；区分研究结果、计划与可行性；无样本也能继续编辑 | 入口本身较长；无需复制完整模式库和全部体裁分支 |
| academic-humanizer [S3] | 3,327 / 252；07-03 | 论文按证据约束主张，申请书还需保留研究愿景、明确其可行性依据；参考作者既往作品 | NSF/NIH 的栏目不能套到 NSFC；一律删破折号、按词数拆句不合理；部分示例新增数字或证据位置，不能作为保真示范 |
| Humanizer-zh [S4] | 21,963 / 1,384；09-23 | 中文特有的定语链、弱动词、无主句与标点判断；每类模式配“保留”反例；明确样本不能提供目标稿事实 | 很多原则本地已有；继续整份叠加只会重复 |
| humanizer [S5] | 64,667 / 5,101；10-28 | 关注段落级的重复收尾、虚假对立、无信息铺垫；先看读者和文章功能；作者样本优先 | 部分模式采用单次命中即改；破折号硬禁；某些示例删掉独立信息；博客允许添加反应的规则不适合标书 |
| academic-defensive-writing-auditor [S6] | 125 / 4；08-30 | 用“删后是否误导、是否有依据、是否只在回应假想批评”区分必要限定与防御姿态 | “每项主张最多一条实质限定”、统一移入局限章节会丢科学含义；不能为了果断而改强结论 |
| doc-coauthoring [S7] | 187,286 / 22,098；10-28，集合仓库 | 用没有参与写作的读者检查理解，寻找作者自认为显然、读者却无法恢复的关系 | 高交互、多轮问答与全面协作流程不宜作为每次润色的默认步骤 |
| stop-slop [S8] | 18,601 / 1,373；03-17 | 识别假行动主体、空泛结构、金句式收尾；尊重读者已有知识 | 禁所有副词/被动句、每句必须有人类主语、两项优于三项，均会误伤科研表达 |
| humanizer-lite [S9] | 1 / 0；09-28 | 入口与按需模式参考分离；单列误报与免改边界 | 自动“始终应用”的触发过宽；破折号禁令和技术英语句长上限不适合通用学术润色 |
| research-writing-skill [S10] | 5,651 / 302；05-14，集合仓库 | 区分原文、作者确认、推断与扩展；检查每段对章节目的的贡献 | 同时覆盖新写、审稿回复等；部分章节顺序只是领域偏好，不能成为标书统一模板 |
| humanizer-zh-academic [S11] | 355 / 23；02-24 | 观察到理论式起笔、重复总结、段落等重等中文问题 | 以检测率为目标；设词频/加粗/段落配额和“噪声预算”；示例加入未提供的观察、来源或推论，整体不建议作为执行规则来源 |

各项仓库指标以本轮保存的 API 快照为准；后续在线元数据更新不改变本次固定源码的比较结论。

### 哪些是增量，哪些本地已经有

本地已经明确反对禁词式编辑、刻意交替长短句、删除真实三项、泛化口语、添加主观判断和统一段首主张；也已有两轮内部复核、八维比较与原稿免改。因此，“增加二次审查”“先组织再润色”“保留科学限定”都不能包装成这次的新发现。

真正有增量的是三件事。第一，把“风格卡”从模型总结自己的输出，扩展为可追溯到作者认可样本的偏好。第二，把已有章节职责提示展开为可操作的基金编辑判断，同时保留通用入口。第三，在删句时追踪该句承担的论证与引用功能，并在删后重读，而不仅检查事实词和引用 key 是否仍在。

## 对当前 humanization 的判断

### 作者风格依据不够明确：已确认的契约缺口

当前输入接受用途、读者、语气，输出可生成风格卡；但没有明确说明作者样本如何使用、样本和待改草稿冲突时谁优先，以及如何防止借用样本中的事实。若输入本身就是作者不满意的 AI 草稿，沿用其语气并不能可靠恢复作者声音。

建议采用 S1/S2/S4 的来源区分：本轮明确偏好优先，其次是作者认可的同一文档周边正文，再是指定风格样本；均没有时使用适合任务的中性中文。待改草稿提供内容和立场，不自动成为作者认可的风格标准。样本只提供可迁移的表达倾向，不能移植论点、结果和标志性措辞。

### 基金语境目前偏薄：已确认的设计事实，效果尚待验证

配置保留立项依据、研究内容、研究基础、工作条件和风险应对等职责，但 `nsfc_academic` 当前只是 `academic_general` 的兼容映射，不加载基金参考。通用化保留了使用范围，却没有为本次最关心的申请书提供足够细的判断依据。

这里不需要恢复 NSFC 为全局默认。更合适的是识别到申请书后按需加载参考，检查已有的“问题—目标—研究动作—基础”关系是否表达清楚。保留有依据的研究愿景；区分“拟检验”“预期获得”和“已观察到”，不把计划修成既成成果，也不把有根据的明确判断统一改成“初步提示”。

### 删改后的功能复核可以更具体：增量改进

现有规则保护引用与主张的对应，且要求逐项语义对照；但尚未把删除后的指代悬空、唯一问题陈述消失、图表首次引入丢失等情况具体纳入检查。S1 的“删除前说明作用、删除后确认作用仍在”比再加一批禁句更有价值。

这是一条紧凑的编辑规则，不需要每句生成审计表。没有跨段依赖时局部复核；确有引用或图表依赖时才读取相关上下文。

### 保守规则是否压制改善：合理假设，尚未证实

当前默认保留行段，LaTeX 命令紧随参数全部保护；内部要求多张对照表，并使用“不能证明零损失则保留原句”。这些设计有安全收益，也可能使模型把主要注意力放在免责和冻结表达上。不能仅凭规则多就断言它是 AI 味的根因。

本轮对现有检查器作了四个小型范围探针：普通中文措辞调整通过；数字不变但分母和阈值含义被改坏仍通过；普通英文润色报字面差异；同义润色放入命令参数后报差异。相关边界已在现有文档承认。这些结果说明字面检查不能衡量写作质量，也不能单独证明科学保真，不构成新发现的全面程序缺陷。

应先比较完整规则与精简规则的实际产出。默认格式保护继续保留；只有证据证明其阻碍授权编辑，再单独设计明确的可编辑区域，不能为了提高改动量放宽保护。

### 效果证据仍不足：最值得优先补齐

既有计划记录了五段合成 NSFC 文本的一次匿名比较：新版相对旧版 1 胜、4 平、0 负，唯一胜例的原文也与新版平局。这支持部分安全表达改进，尚未显示自然度的稳定增益。当前已有八维量表和盲评流程，下一步应真正执行真实长文评估，补直接普通润色基线、重复生成、作者样本隔离和领域人员评审，而不是再新建一套评分体系。

## 融入建议

优先吸收 S1 的风格来源与功能保护、S2/S3 的基金语境、S4 的中文保留反例。S5/S6/S8 仅提炼少量诊断问题，先与现有条目合并；S7 的新读者检查进入评估方案或按需长文审阅，不成为每次改稿的固定成本。S9 用于检视入口是否能更短；S10 仅作内容来源区分的补充；S11 主要作为反例。

实际改写规则应由本项目重新表述，并逐条标注来源及取舍。后续若复制第三方文字、示例或代码，须另核对具体文件许可并保留要求的署名；本次引用不等于已完成后续代码复用的许可审查。

实施顺序与验收见 [优化计划](../plans/2026-11-04-humanization-community-informed-optimization.md)。

## 来源与复核入口

以下链接由本轮实际获取的 commit 固定，避免后续主分支变化。公开源码快照、来源哈希、检索结果与网络失败摘要保存在本轮任务工作区 `find-best-skill/`，不作为 Skill 的运行依赖。Issue/PR 列表可提示问题，例如 Humanizer-zh #37、#47 和 humanizer PR #318；本轮未取得讨论正文，故不推断维护者已认可问题或修复已生效。

- [S1] [deathcats4/scientific-manuscript-editor：SKILL.md](https://github.com/deathcats4/scientific-manuscript-editor/blob/9371352cf7153076065421e8686bf1139f61ddc6/SKILL.md)，commit `9371352cf715`。
  - [references/style-source-contract.md](https://github.com/deathcats4/scientific-manuscript-editor/blob/9371352cf7153076065421e8686bf1139f61ddc6/references/style-source-contract.md)。
  - [references/academic-naturalness.md](https://github.com/deathcats4/scientific-manuscript-editor/blob/9371352cf7153076065421e8686bf1139f61ddc6/references/academic-naturalness.md)。
  - [references/academic-protection.md](https://github.com/deathcats4/scientific-manuscript-editor/blob/9371352cf7153076065421e8686bf1139f61ddc6/references/academic-protection.md)。
- [S2] [Hyacehila/humanizer-zh-next：SKILL.md](https://github.com/Hyacehila/humanizer-zh-next/blob/0c3ee9cbba7a54b8ae180554c95a0ff906a7b8fd/SKILL.md)，commit `0c3ee9cbba7a`。
  - [references/grant-proposals.md](https://github.com/Hyacehila/humanizer-zh-next/blob/0c3ee9cbba7a54b8ae180554c95a0ff906a7b8fd/references/grant-proposals.md)。
  - [references/academic-writing.md](https://github.com/Hyacehila/humanizer-zh-next/blob/0c3ee9cbba7a54b8ae180554c95a0ff906a7b8fd/references/academic-writing.md)。
- [S3] [AIScientists-Dev/academic-humanizer：SKILL.md](https://github.com/AIScientists-Dev/academic-humanizer/blob/94b88b23703bed7df507acae7d6d5876209a0cdf/SKILL.md)，commit `94b88b23703b`。
- [S4] [op7418/Humanizer-zh：SKILL.md](https://github.com/op7418/Humanizer-zh/blob/f4518a8eab97b8bfebc66a89d34320a89bef6930/SKILL.md)，commit `f4518a8eab97`。
- [S5] [blader/humanizer：SKILL.md](https://github.com/blader/humanizer/blob/0ef9fe5bc3572734fd3ae6c448fe00a30cd5dcf0/SKILL.md)，commit `0ef9fe5bc357`。
- [S6] [Worigin0314/academic-defensive-writing-auditor：SKILL.md](https://github.com/Worigin0314/academic-defensive-writing-auditor/blob/89f26b8a7f8149e6458f657010d354587d42cfe9/SKILL.md)，commit `89f26b8a7f81`。
- [S7] [anthropics/skills：skills/doc-coauthoring/SKILL.md](https://github.com/anthropics/skills/blob/ca45fc496a3436251f191354091d557da31c15b5/skills/doc-coauthoring/SKILL.md)，commit `ca45fc496a34`。
- [S8] [hardikpandya/stop-slop：SKILL.md](https://github.com/hardikpandya/stop-slop/blob/8da1f030185bdfe8471220585162991eaeb970e9/SKILL.md)，commit `8da1f030185b`。
- [S9] [F-DK/humanizer-lite：SKILL.md](https://github.com/F-DK/humanizer-lite/blob/c3418228c1591babf366b677ac1a839d02d44c84/SKILL.md)，commit `c3418228c159`。
  - [references/false-positives.md](https://github.com/F-DK/humanizer-lite/blob/c3418228c1591babf366b677ac1a839d02d44c84/references/false-positives.md)。
- [S10] [zLanqing/codex-claude-academic-skills：research-writing-skill/SKILL.md](https://github.com/zLanqing/codex-claude-academic-skills/blob/7ed6377f0efb6a38951b48ef03b19d996e454b1f/research-writing-skill/SKILL.md)，commit `7ed6377f0efb`。
- [S11] [redbaronyyyyy-eng/humanizer-zh-academic：SKILL.md](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic/blob/50e11af64eb4817f75b8be7d609b99d7cd80d801/SKILL.md)，commit `50e11af64eb4`。
