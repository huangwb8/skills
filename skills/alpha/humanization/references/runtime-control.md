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

第一次 release 返回 pending_review、handoff_ref 和 evidence_hash，退出 2，working 不变。主 Agent 直接通过 parallel-vibe 调度三个独立子 Agent 并行审查同一冻结对象，沿用该 Skill 的计划、thread workspace、RESULT.md 和汇总记录；不新增编排脚本或额外 Pack。

三人各自完整阅读当前 handoff、原文、全部产物和写作参考，不读取其他人的结果、不修改正文。主 Agent 回收三个有效判断，至少两票 pass 才通过；pass/pass/fail 或 pass/pass/uncertain 允许通过并保留异议，缺第三份结果或真实执行未完成不能提前通过。机械/结构/身份/哈希错误仍阻塞。无法启动三个真实子 Agent 时说明受阻，不改成主 Agent 自审。

主 Agent 根据真实审查结果形成原有 semantic-review 组件的一份汇总回传，再次 release 加 --submission-file humanization/input/submissions.json。facts.summary 记录审查轮数、三人票数、三个 RESULT.md 的任务内相对路径及少数意见；其余 audit/comparison/rounds 沿用原 schema。executor 如实记录汇总者，不能冒充某位子 Agent；BSK 绑定证明汇总对应当前稿件，不证明三人身份或实际并行。

写回格式为 `{"results": [<BSK ComponentResult>]}`。不得只写 verdict 或把脚本组件当作外部 submission。可用公开 API 从原始 handoff 生成绑定字段：

```python
from bensz_skill_kernel import ComponentHandoff
from dataclasses import fields

# h 来自本次 handoffs.json；facts、executor 来自实际完成的审查。
allowed = {field.name for field in fields(ComponentHandoff)}
result = ComponentHandoff(**{k: v for k, v in h.items() if k in allowed}).bind_result(
    verdict="pass", facts=facts,
    evidence_refs=[h["subject"]["ref"]],
    executor={"type": "agent", "id": "actual-main-coordinator", "model": "actual-model"},
)
submissions = {"results": [result]}
```

每个 reviewer 如实给出 pass/fail/uncertain 及依据。主 Agent 按三人至少两票的规则汇总；少数意见单独保留，不冒充全票一致。未达到门槛时不能回传汇总 pass；每位 reviewer 的判断不等于 BSK 顶层判定。模型名无法确认时如实写宿主未披露，不猜具体型号。绑定字段证明结果对应当前契约/证据/身份，不认证模型判断的真实性。

外部审查人数、票数和上限由 config.yaml.review_policy 声明，沿用 parallel-vibe 的计划与汇总记录，不新增事件或轮次计数器。一次对冻结稿件的三人审查算一轮，重复提交和恢复不加轮，改稿后的新审查消耗下一轮，retry 不清零。最多五轮；第五轮仍未通过时停止优化，提交最后一轮草案并说明未通过原因，不再发起第六轮或重开 run 规避上限。即使 text_only 也要保留简短未通过说明。状态保持 working，不伪造 Gate/ready；可读草案的兜底提交不等于获批交付。

准备修订前：将 action 改成 retry、attempt-id 改成新值，入口先验证当前原文/参数，再调用 BSK attempt start；然后生成或修订交付文件，以新身份重新 release。修改原文/参数时先保存新请求，再执行 retry 绑定。旧 handoff/批准不能跨 attempt。pending 同稿重复 release 可恢复且不重复写相同检查事件。

init/retry 在变更 BSK 前原子保存绑定输入、资产、运行时和身份的 pending 意图。若进程退出或会话提交失败，保持原目录和文件，以同一命令、同一 run/attempt 重试；入口核对真实事件与快照后补完，不消耗额外 attempt。未完成操作期间 release 拒绝；先恢复原动作。请求或身份不匹配时拒绝恢复，不能手写 session/ready 或删日志。该机制覆盖入口与会话提交的中断，不保证底层事件存储损坏可自动修复。

成功回执 status=ready，带目标 attempt（通常原值加 `-ready`）及交付文件哈希。只返回这些已经批准的字节，不临时再写摘要或改词。再次取回时以回执的目标 attempt 调 release，结果为 already_ready；回执缺失时可从 status 取得当前 attempt，再用 release 重建。入口从真实 transition、绑定 Gate/结果和冻结字节重建回执，不信任可修改的 release.json；哈希变化会拒绝。status 只观察当前身份，不证明文字仍有效。

## 语义 facts

pass 的 facts 必须包含（这是主 Agent 根据实际三人审查形成的汇总记录，rounds 指表达/安全复核预算，与最多五轮的外部优化轮次不同）：

| 字段 | 含义 |
| --- | --- |
| evidence_hash | 当前冻结索引的 sha256（与 handoff 文件同值） |
| summary / confidence / uncertainties | 具体判断、0–1 置信度、未决项；pass 不允许未决项 |
| audit | 配置中启用的 require_* 键去掉前缀后的五个部分 |
| comparison | outcome、具体 reason；revise 另需 net_improvement=true |
| rounds | 数量等于 self_eval_rounds；逐轮 focus 和 summary，合计覆盖 expression、safety |
| lexical_explanation | 字面结果 fail/unchecked 时，具体解释差异及替代复核，不能只写“忽略” |

audit 的每一部分包含 applicability（applicable/not_applicable）、reason、items。applicable 的 items 非空，not_applicable 的 items 为空且理由充分；invariant_audit 始终适用。每个 item 包含 disposition（preserved/rewritten/merged/reviewed）、reason 和 anchors。anchor 使用 artifact（original/text/diagnosis/summary/style_card）、start/end：Python Unicode 字符区间 `[start,end)`，不是字节偏移。区间必须真实存在，避免在日志重复源文。一次多对一改写可以引用多个 source 区间和一个 text 区间。

记录存在与区间合法由脚本验证；覆盖充分、处置理由真实、候选中每个主张均来自原文，由真实语义组件判断。它必须阅读配置中 diagnostic_layers 和三个写作参考，不能以五个非空对象代替通读。附件也须核对并给锚点。词法差异保留原结果，不改写成“自动已通过”。

## 回执、失败与审计

稳定回执协议为 bensz-revision-control-v1，含 action/run_id/attempt_id、previous/target/current_state、required_results、gate、transition、status。退出 0 对应初始化、重试、观察或 ready；退出 2 对应待审查/阻塞。消费者仍须检查 status，不能仅看退出码。

BSK 生成 Gate 并记录完整 verification-v2 组件绑定。入口核对协议、ID/version、结果集合、源身份、Gate result_refs、evidence、transition 和新快照，任何未知或不一致均停止。失败用稳定 reason_code/recovery，不回显原文、异常内容或私密路径。

事件位于任务根 log，Skill 证据位于 humanization/log；不得写回 Skill 源码。可用 BSK rebuild/query 接口重放或核对事件，不重新调用模型。不清空日志、不手写 ready、不跳 required。契约或运行时发生漂移时保留已有工作区，报告不能在当前运行继续；同一逻辑任务不擅自换根。

控制只覆盖经过入口的执行。宿主直接发送正文或写正式文件的能力仍在宿主侧；本 Skill 不声称通用沙箱或跨平台强制拦截。
