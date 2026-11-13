# BSK 受控润色

本页定义唯一控制入口的文件契约。State 和 Verifier 的领域含义分别见各 Pack；配置是参数、体积上限、State/action 映射及 required 清单的唯一来源。

## 运行准备

使用 Bensz 托管 Python `~/.bensz-skills/envs/benszapi/bin/python`，入口内部固定调用 `~/.bensz-skills/bin/bsk`。`init` 从当前宿主已安装的 install-bensz-skills 定位管理器，执行 `--force-runtime-update`；成功后将实际版本确认绑定本次运行。后续动作不在同一运行中切换版本；版本改变则阻塞，不能静默换成项目 Python、裸 PATH bsk 或源码包。

若托管环境不存在，先通过安装版 install-bensz-skills 的 `bootstrap_install.py --ensure-runtime` 准备环境；完整安装器/本 Skill 都要求 Python 3.11+。未确认最新运行时、无法保存授权文本或实际语义审查缺失时，保留草案并报告受阻。

复用已公开锁定的任务根。以下所有文件引用都相对于该根，原文位于 humanization/input，交付草案位于 humanization/output。不要将敏感内容复制到审计事件；不为初始化另外开任务目录。

## 请求

最小请求文件 `humanization/input/request.json`：

```json
{
  "original": "humanization/input/original.txt",
  "parameters": {},
  "outcome": "revise",
  "delivery": {"text": "humanization/output/revised.txt"}
}
```

`init` 前原文必须存在，候选可稍后生成。实际润色、优化及交付只由主 Agent 执行，子 Agent 只读审查；角色身份与实际调度沿用 parallel-vibe 记录，不增加请求字段。参数沿用现有默认值和合法值，未知字段/值拒绝；仅降低 max_self_eval_rounds 时，未显式指定的 self_eval_rounds 随之裁剪，显式冲突仍拒绝。原文、参数在 init 后不可悄悄改变。`outcome` 为 revise、keep_original 或 diagnosis。keep_original 的 text 必须与原文逐字节相同。diagnosis_only 对应 outcome=diagnosis，delivery 只有 diagnosis 文件，不需要伪候选。

text_only 的 delivery 只有 text；text_with_change_summary 增加 summary；text_with_change_summary_and_style_card 再增加 style_card。附件使用不同实际文件，全部一起冻结与审查；路径别名或硬链接不能冒充独立附件。所有路径拒绝绝对路径、`..`、重复斜杠、符号链接、非普通文件和超量输入。不要在路径或身份中写隐私内容。

reflow_plain 仅用于连续纯文本；含 TeX（包括只有数学的区域）、标题、列表、代码或表格时整份受控输入保守回退 preserve，并记录 requested/effective 与原因。若只希望重排混合文件的纯文本区域，先按授权范围拆成独立批次，不扩大格式权限。

## 唯一入口与恢复

```bash
~/.bensz-skills/envs/benszapi/bin/python <skill-root>/scripts/control.py init \
  --project-root <project-root> --task-root .bensz-api/task-YYYYMMDD-HHMM-demo \
  --request-file humanization/input/request.json --run-id run-1 --attempt-id edit-1

~/.bensz-skills/envs/benszapi/bin/python <skill-root>/scripts/control.py release \
  --project-root <project-root> --task-root .bensz-api/task-YYYYMMDD-HHMM-demo \
  --request-file humanization/input/request.json --run-id run-1 --attempt-id edit-1
```

第一次 release 返回 pending_review、handoff_ref 和 evidence_hash，退出 2，working 不变。主 Agent 通过 parallel-vibe 调度同组三个独立子 Agent 并行审查同一冻结对象的两个命题，沿用该 Skill 的计划、thread workspace、RESULT.md 和汇总记录；不新增编排脚本。required Pack 为 revision-readiness 和 defensive-framing，分别回传 semantic-review 与 defensive-review 组件结果。

三人各自完整阅读两份当前 handoff、原文、全部产物和写作参考，不读取其他人的结果、不修改正文。对每项命题分别回收三个有效判断，至少两票 pass 且所有实质异议已结案才通过。pass/pass/fail 或 pass/pass/uncertain 仅满足票数门槛；一般风格异议可保留，实质问题须修复并新 attempt 重审，或用原文/候选锚点与可复核理由驳回，未决不能多数放行。缺第三份结果或真实执行未完成不能提前通过，机械/结构/身份/哈希错误仍阻塞。无法启动三个真实子 Agent 时说明受阻，不改成主 Agent 自审。

主 Agent 根据真实审查形成两个组件的独立汇总，再次 release 加 --submission-file humanization/input/submissions.json。每份 facts 的 reviewers 和 resolutions 提供可核验的投票与异议记录，summary 解释本命题结论和少数意见；revision-readiness 继续使用 audit/comparison/rounds，defensive-framing 使用 defensive_audit。入口复算各项票数并检查两份名单一致，executor 如实记录汇总者，不能冒充某位子 Agent。结构化记录和 BSK 绑定不证明三人真实身份、实际并行或结案理由正确。

写回格式为 `{"results": [<revision-readiness ComponentResult>, <defensive-framing ComponentResult>]}`，分别从各自当前 handoff 绑定。不得只写 verdict 或把脚本组件当作外部 submission。可用公开 API 从原始 handoff 生成绑定字段：

```python
from bensz_skill_kernel import ComponentHandoff
from dataclasses import fields

# 对两份 handoff 分别执行；h 来自本次 handoffs.json，facts 来自对应命题的真实审查。
allowed = {field.name for field in fields(ComponentHandoff)}
result = ComponentHandoff(**{k: v for k, v in h.items() if k in allowed}).bind_result(
    verdict="pass", facts=facts,
    evidence_refs=[h["subject"]["ref"]],
    executor={"type": "agent", "id": "actual-main-coordinator", "model": "actual-model"},
)
results.append(result)  # results 先初始化为 []；两份绑定完成后再写回
submissions = {"results": results}
```

每个 reviewer 如实给出 pass/fail/uncertain 及依据。主 Agent 对两项命题分别按三人至少两票且实质异议结案的规则汇总；少数意见单独保留，不冒充全票一致。未达到门槛时不能回传汇总 pass；每位 reviewer 的判断不等于 BSK 顶层判定。模型名无法确认时如实写宿主未披露，不猜具体型号。绑定字段证明结果对应当前契约/证据/身份，不认证模型判断的真实性。

外部审查人数、票数和上限由 config.yaml.review_policy 声明，沿用 parallel-vibe 的计划与汇总记录，不新增事件或轮次计数器。一次对冻结稿件的三人审查算一轮，重复提交和恢复不加轮，改稿后的新审查消耗下一轮，retry 不清零。最多五轮；第五轮仍未通过时停止优化，提交最后一轮草案并说明未通过原因，不再发起第六轮或重开 run 规避上限。即使 text_only 也要保留简短未通过说明。状态保持 working，不伪造 Gate/ready；可读草案的兜底提交不等于获批交付。

准备修订前：将 action 改成 retry、attempt-id 改成新值，入口先验证当前原文/参数，再调用 BSK attempt start；然后生成或修订交付文件，以新身份重新 release。修改原文/参数时先保存新请求，再执行 retry 绑定。旧 handoff/批准不能跨 attempt。pending 同稿重复 release 可恢复且不重复写相同检查事件。

init/retry 在变更 BSK 前原子保存绑定输入、资产、运行时和身份的 pending 意图。若进程退出或会话提交失败，保持原目录和文件，以同一命令、同一 run/attempt 重试；入口核对真实事件与快照后补完，不消耗额外 attempt。未完成操作期间 release 拒绝；先恢复原动作。请求或身份不匹配时拒绝恢复，不能手写 session/ready 或删日志。该机制覆盖入口与会话提交的中断，不保证底层事件存储损坏可自动修复。

线索采样上限由 control_policy.max_defensive_clues 控制，facts 记录 clue_count 与 clues_truncated；截断后仍须完整语义审查，不以采样代表全文无问题。

成功回执 status=ready，带目标 attempt（通常原值加 `-ready`）及交付文件哈希。只返回这些已经批准的字节，不临时再写摘要或改词。再次取回时以回执的目标 attempt 调 release，结果为 already_ready；回执缺失时可从 status 取得当前 attempt，再用 release 重建。入口从真实 transition、绑定 Gate/结果和冻结字节重建回执，不信任可修改的 release.json；哈希变化会拒绝。status 只观察当前身份，不证明文字仍有效。回读还会重验 RESULT.md 的文件哈希、运行身份和异议记录；BSK 事件中已脱敏的 audit 字段不被当作原始审查文件重新解析，原审查是否完成以绑定的 completed/pass 事件为依据。

## RESULT.md 与两项汇总

每位子 Agent 在独立 thread 的 RESULT.md 中写一段且仅一段 fenced `json`，其余 Markdown 可写解释。以下为字段示意，身份、哈希、判断与理由必须替换为本轮真实值；不能用示例生成虚构审查。

```json
{
  "protocol": "humanization-review-v1",
  "reviewer_id": "reviewer-1",
  "run_id": "run-1",
  "state_visit_id": "current-visit",
  "attempt_id": "edit-1",
  "evidence_hash": "sha256:CURRENT_EVIDENCE_HASH",
  "reviews": {
    "bensz.prose.revision-readiness": {
      "verdict": "pass",
      "summary": "本命题的实际判断和依据",
      "material_findings": []
    },
    "bensz.prose.defensive-framing": {
      "verdict": "pass",
      "summary": "本命题的实际判断和依据",
      "material_findings": []
    }
  }
}
```

每项 verdict 为 pass/fail/uncertain；material_findings 总是存在，每条含唯一 id、具体 reason 和非空 anchors。锚点格式见下文；只有实质问题写入该列表，普通风格偏好写在 summary 或说明文字中。三份文件必须来自真实独立审查，不能复制同一文件、硬链接或只改声明身份冒充独立执行。

每份组件 facts 都附以下字段，revision-readiness 与 defensive-framing 引用同三人、同路径和同文件哈希，但 verdict 取各自命题：

| 字段 | 契约 |
| --- | --- |
| reviewers | 恰好三项；每项含 reviewer_id、result_ref、result_hash、artifact_hash、verdict |
| result_ref | 任务根相对路径，形如 `parallel-vibe/<批次>/<线程>/RESULT.md` |
| result_hash / artifact_hash | 前者为 RESULT.md 字节的 sha256，后者为当前冻结 evidence_hash；采用入口输出的 `sha256:` 前缀格式 |
| resolutions | 无实质异议时为 []；否则逐项引用 reviewer_id、finding_id，disposition 只能为 dismissed，并附 reason 与覆盖 original 及 text/diagnosis 的 anchors |

修复问题不能在旧结果中标记 fixed：先 retry、改稿并发起新一轮真实审查。dismissed 只记录有依据的驳回，脚本检查其结构和锚点，不替代语义裁决。缺票、重复记录、哈希漂移、错绑当前身份、两项名单不一致或未结案实质异议均不能形成批准。

## 语义 facts

revision-readiness 的 pass facts 除上述 reviewers/resolutions 外必须包含（这是主 Agent 根据实际三人审查形成的汇总记录，rounds 指表达/安全复核预算，与最多五轮的外部优化轮次不同）：

| 字段 | 含义 |
| --- | --- |
| evidence_hash | 当前冻结索引的 sha256（与 handoff 文件同值） |
| summary / confidence / uncertainties | 具体判断、0–1 置信度、未决项；pass 不允许未决项 |
| audit | 配置中启用的 require_* 键去掉前缀后的五个部分 |
| comparison | outcome、具体 reason；revise 另需 net_improvement=true |
| rounds | 数量等于 self_eval_rounds；逐轮 focus 和 summary，合计覆盖 expression、safety |
| lexical_explanation | 字面结果 fail/unchecked 时，具体解释差异及替代复核，不能只写“忽略” |

audit 的每一部分包含 applicability（applicable/not_applicable）、reason、items。applicable 的 items 非空，not_applicable 的 items 为空且理由充分；invariant_audit 始终适用。每个 item 包含 disposition（preserved/rewritten/merged/reviewed）、reason 和 anchors。anchor 使用 artifact（original/text/diagnosis/summary/style_card）、start/end：Python Unicode 字符区间 `[start,end)`，不是字节偏移。区间必须真实存在，避免在日志重复源文。一次多对一改写可以引用多个 source 区间和一个 text 区间。

记录存在与区间合法由脚本验证；覆盖充分、处置理由真实、候选中每个主张均来自原文，由真实语义组件判断。它必须阅读配置中 diagnostic_layers 和自然写作、模式、回归、防御性表达四份参考，不能以五个非空对象代替通读。附件也须核对并给锚点。词法差异保留原结果，不改写成“自动已通过”。

## 防御性表达 facts

defensive-framing 的 pass facts 包含 evidence_hash、summary、confidence（0–1）、空 uncertainties，以及 reviewers、resolutions 和 defensive_audit。依据 [防御性表达参考](defensive-writing.md) 的五问和六类功能判断，扫描线索仅帮助定位。

| defensive_audit 字段 | 契约 |
| --- | --- |
| scope | 普通/免改稿为 text；diagnosis_only 为 diagnosis |
| coverage | reason 解释通读结论；anchors 覆盖 original 与全部交付物 |
| items | 问题/限定处置列表；干净文本可为空，但仍须 coverage |
| unresolved_material_findings | pass 时必须为 [] |

每个 item 含 pattern、necessity、disposition、material、materiality_reason、preserved_function、source_anchors、candidate_anchors、preserved_anchors。source/candidate 至少一项非空；前者只指 original，后者只指交付物。preserved_anchors 必须包含 text（诊断时为 diagnosis），解释相关信息功能在交付中的去向。material=false 表示当前稿没有未决实质问题，不表示原文问题无关紧要。

necessity 为 necessary/redundant/anticipatory/performative/mixed/unresolved。necessary、mixed 只能 keep/compress/rewrite；redundant、anticipatory、performative 另允许 delete；unresolved 只能 human_review，不能获得 pass。任何改动仍不得删除真实范围、责任、阈值、风险或证据强度；必要功能只写在摘要中不算保全。keep_original 仍审查原文本身；diagnosis 检查问题识别与建议是否准确，不伪造改稿。

## 回执、失败与审计

稳定回执协议为 bensz-revision-control-v1，含 action/run_id/attempt_id、previous/target/current_state、required_results、gate、transition、status。退出 0 对应初始化、重试、观察或 ready；退出 2 对应待审查/阻塞。消费者仍须检查 status，不能仅看退出码。

BSK 生成 Gate 并记录完整 verification-v2 组件绑定。入口核对协议、ID/version、结果集合、源身份、Gate result_refs、evidence、transition 和新快照，任何未知或不一致均停止。失败用稳定 reason_code/recovery，不回显原文、异常内容或私密路径。

事件位于任务根 log，Skill 证据位于 humanization/log；不得写回 Skill 源码。可用 BSK rebuild/query 接口重放或核对事件，不重新调用模型。不清空日志、不手写 ready、不跳 required。契约或运行时发生漂移时保留已有工作区，报告不能在当前运行继续；同一逻辑任务不擅自换根。

新增 required 命题和结构化审查记录改变批准合同，版本以 config.yaml 为准。旧工作区、事件和回执不改写；旧批准只能在原契约快照下读回。新源码拒绝旧运行的资产漂移，不把历史 pass 升格为双命题批准；恢复仍复用原任务根。

控制只覆盖经过入口的执行。宿主直接发送正文或写正式文件的能力仍在宿主侧；本 Skill 不声称通用沙箱或跨平台强制拦截。
