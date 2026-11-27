# BSK 受控润色

配置统一定义参数、体积上限、State/action 映射和 required 清单。入口和文件约定见本页，State 与 Verifier 的具体规则见各 Pack。

## 运行准备

使用安装器管理的原生平台路径：

| 平台 | 托管 Python | BSK 托管启动器 |
| --- | --- | --- |
| macOS / Linux（POSIX） | `~/.bensz-skills/envs/benszapi/bin/python` | `~/.bensz-skills/bin/bsk` |
| Windows | `~/.bensz-skills/envs/benszapi/python.exe` | `~/.bensz-skills/bin/bsk.cmd` |

入口检查当前解释器确实为上述托管 Python，且启动器存在。Windows 内部使用托管 Python 以隔离导入、禁写字节码和 UTF-8 模式调用 `bensz_skill_kernel.runtime:main`，保持 BSK CLI 参数和 JSON 协议，避免通过 `.cmd` 的 shell 展开路径及误加载项目同名模块；子进程 JSON 通信使用 UTF-8。`init` 从当前宿主已安装的 install-bensz-skills 定位管理器，执行 `--force-runtime-update`；成功后将实际版本确认绑定本次运行。后续动作不在同一运行中切换版本；版本改变则阻塞，不能静默换成项目 Python、裸 PATH bsk 或源码包。

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

POSIX：

```bash
~/.bensz-skills/envs/benszapi/bin/python <skill-root>/scripts/control.py init \
  --project-root <project-root> --task-root .bensz-api/task-YYYYMMDD-HHMM-demo \
  --request-file humanization/input/request.json --run-id run-1 --attempt-id edit-1

~/.bensz-skills/envs/benszapi/bin/python <skill-root>/scripts/control.py release \
  --project-root <project-root> --task-root .bensz-api/task-YYYYMMDD-HHMM-demo \
  --request-file humanization/input/request.json --run-id run-1 --attempt-id edit-1
```

Windows PowerShell（`release`、`retry`、`status` 使用同一解释器和参数）：

```powershell
& "$HOME/.bensz-skills/envs/benszapi/python.exe" "<skill-root>/scripts/control.py" init `
  --project-root "<project-root>" --task-root .bensz-api/task-YYYYMMDD-HHMM-demo `
  --request-file humanization/input/request.json --run-id run-1 --attempt-id edit-1
```

第一次 release 返回 pending_review、handoff_ref、evidence_hash，退出 2，状态仍为 working。主 Agent 用 parallel-vibe 的计划、thread workspace、RESULT.md 和汇总记录执行三人并审。required Pack revision-readiness 与 defensive-framing 分别回传 semantic-review 和 defensive-review。

三人各自读完两份当前 handoff、原文、全部产物和写作参考，独立审查两项命题。每项都须三份真实判断、至少两票 pass 和实质异议结案。pass/pass/fail 或 pass/pass/uncertain 仅满足票数要求。一般风格异议可保留，实质问题须修后新 attempt 重审，或以原文/候选锚点和可复核理由驳回。机械、结构、身份或哈希错误仍阻塞。无法真实并审时说明受阻。

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

reviewer 如实给出 pass/fail/uncertain 及依据。汇总保留少数意见，未达门槛不得回传 pass。个人判断需由 BSK 汇总判定，绑定只证明契约、证据和身份对应。模型名无法确认时写“宿主未披露”。

按 config.yaml.review_policy 执行，计轮沿用 parallel-vibe 记录。对同一冻结稿的三人审查算一轮，重复提交和恢复不加轮，改稿重审消耗下一轮，retry 不清零。第五轮未过时提交最后草案和原因，即使 text_only 也须说明。状态留在 working，禁止伪造 Gate/ready 或另开 run 规避上限。

准备修订前：将 action 改成 retry、attempt-id 改成新值，入口先验证当前原文/参数，再调用 BSK attempt start；然后生成或修订交付文件，以新身份重新 release。修改原文/参数时先保存新请求，再执行 retry 绑定。旧 handoff/批准不能跨 attempt。pending 同稿重复 release 可恢复且不重复写相同检查事件。

init/retry 在变更 BSK 前原子保存绑定输入、资产、运行时和身份的 pending 意图。若进程退出或会话提交失败，保持原目录和文件，以同一命令、同一 run/attempt 重试；入口核对真实事件与快照后补完，不消耗额外 attempt。未完成操作期间 release 拒绝；先恢复原动作。请求或身份不匹配时拒绝恢复，不能手写 session/ready 或删日志。该机制覆盖入口与会话提交的中断，不保证底层事件存储损坏可自动修复。

线索采样上限由 control_policy.max_defensive_clues 控制，facts 记录 clue_count 与 clues_truncated；截断后仍须完整语义审查，不以采样代表全文无问题。

成功回执 status=ready，带目标 attempt（通常原值加 `-ready`）及交付文件哈希。再次取回时以回执的目标 attempt 调 release，结果为 already_ready；回执缺失时可从 status 取得当前 attempt，再用 release 重建。入口从真实 transition、绑定 Gate/结果和冻结字节重建回执，不信任可修改的 release.json；哈希变化会拒绝。status 只观察当前身份，不证明文字仍有效。回读还会重验 RESULT.md 的文件哈希、运行身份和异议记录；BSK 事件中已脱敏的 audit 字段不被当作原始审查文件重新解析，原审查是否完成以绑定的 completed/pass 事件为依据。

### 交付前终润色

仅对 `ready` 或 `already_ready` 的 `outcome=revise` 执行，先重验冻结稿哈希。本地处理或限制外发时直接交付获批稿。脚本接收冻结 `t0` 路径与预设 profile，逐稿要求在 T0 写作、审查及 T1 核验中落实。请求正文为原样 T0，禁止添加编辑备忘、审查意见、指令或其他上下文。旧调用须删去 `--requirements-file` 及其值。

```bash
python3 <skill-root>/scripts/finalize_prose.py <approved-t0> \
  --prompt-profile academic --request-id

python3 <skill-root>/scripts/finalize_prose.py <approved-t0> \
  --prompt-profile academic --expect-request-id <request-sha256>
```

主 Agent 根据用户要求和 T0 已完成的文体判断选择提示词。用户显式指定 T1 profile 时直接采用，显式指定文体时按文体所承担的表达职责选择。脚本接受以下 T0 `style_profile` 值作为 CLI 别名：

| T0 风格 | T1 profile |
| --- | --- |
| `general_prose`、`natural_explanation` | `general` |
| `academic_general`、`nsfc_academic` | `academic` |
| `technical_prose` | `technical` |
| `professional_communication` | `professional` |
| `auto` | 主 Agent 按原文与原任务判断，直接传给 CLI 时使用 `general` |

按表达职责本地选择。论文用 `academic`，科普用 `general`，软件文档用 `technical`，正式工作报告用 `professional`，文学叙事用 `creative`。创意稿的 T0 若用 `general_prose`，T1 仍可按其用途选 `creative`。混合文体用途不明或省略 `--prompt-profile` 时用 `general`。无需用户选模板或另发分类请求。

用 Python 3.11+ 执行。脚本从 `CODEX_HOME/config.toml`（默认 `~/.codex/config.toml`）解析选中的 `model_provider`，用 `[model_providers.<id>].base_url` 请求 `/responses`。仅接受 `benszresearch.com` 及其子域的 HTTPS URL，不跟随重定向。鉴权复用 provider 的 `env_key` 或 `experimental_bearer_token`，需要 OpenAI 鉴权时也支持 `OPENAI_API_KEY` 或 Codex `auth.json` 中的 API Key。请求使用 Codex 客户端标识和 SSE，五种提示词均使用 `gpt-6.2-sol`、`medium`，设置 `store=false`。

Responses 请求的 `system` 是所选 profile 的内置提示词，`developer` 是内置的公共保护要求。同一版本、同一 profile 的两条指令消息逐字一致。唯一的 `user` 消息是 `t0` 正文原文，其中的指令式文字也作为正文处理。

`--request-id` 在本地计算实际请求体的 SHA-256，覆盖冻结 `t0`、两条固定指令及模型参数。恢复时重算指纹，只复用 `humanization/output/` 中同时绑定当前 attempt 和该指纹的完整返回稿。旧返回稿没有匹配指纹时，重新执行。生成时带上 `--expect-request-id`，请求体变化会在发送前报错。将标准输出按 UTF-8 原样捕获到独立的临时文件，等待进程退出。仅在退出 `0` 且文件非空时，将该文件保存为绑定当前 attempt 和请求指纹的候选稿。终润色脚本跳过（退出 `3`）、执行失败或返稿明显截断时，交付获批的 `t0` 并简述原因。

以冻结的 `t0`、用户要求和已有保护信息为依据核验 `t1`。可用 [`check_revision.py`](../scripts/check_revision.py) 按有效的 `structure_mode` 辅助核对两稿。对差异定位复核语义、事实、独立限定、术语、结构与受保护元素。普通英文词语的预期变化或检查器无法可靠解析的内容应逐项人工比对。

- `t1` 满足关键要求时，用它作正式稿。普通措辞差异、节奏变化或主 Agent 的个人文风偏好不构成退回依据。若唯一需要修复的格式差异是最后一个正文行末尾缺少或多出一个换行，按冻结稿约定补上或移除该换行，核对写入副本的结构与回读结果。原始 `t1` 文件保持原样并向用户提供。此规则只处理文件末尾的单个行结束符，段落、空行、缩进及正文内换行仍按有效 `structure_mode` 核验。
- `t1` 有实质回归，或逐项核查后仍有具体的关键要求无法确认时，用获批 `t0` 作正式稿，同时提供原样的完整 `t1` 正文或可访问文件。指出哪里发生了变化、触犯哪项要求或还需确认什么。比如完整返稿把“拟验证”写成“已验证”，应将这一处说明放在正文外，即使是 `text_only` 也提供 T1 供对照。

摘要和风格卡随正式稿校准。保留冻结稿与对应的 BSK 回执。

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
