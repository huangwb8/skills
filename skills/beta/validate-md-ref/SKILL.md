---
name: validate-md-ref
description: 检查 Markdown 文档中的引用是否可定位、URL 或锚点是否可访问，并整理供后续判断引用真实性与适切性的结构化证据。当用户要求核查引用、检查文档链接，或确认引用是否支持正文论断时使用。
metadata:
  author: Bensz Conan
  short-description: 检查 Markdown 引用是否可定位、可访问
---

## 适用范围

- 输入：一个 Markdown 文件，可选一个 YAML 配置文件。
- 检查：引用提取、当前文档内的 `#anchor`、外部 HTTP(S) 链接可达性，以及白名单/黑名单等安全策略。
- 输出：结构化 JSON、Verifier 结果与状态机快照；确定性链接结果使用 `allow` 或 `reject`，无法完成的语义核验使用 `unchecked` 或 `manual_review` 表达。
- 不做：不判断网页内容是否支持正文论断，不自动修改原 Markdown，也不替用户决定如何修复无效链接。

## 执行产物与文件边界

执行需要落盘时，将输入引用、临时报告和日志分别写入当前会话已声明的 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/validate-md-ref/{input,output,log}/`。多 Skill 协作产生的共享材料放在任务根目录的 `shared/`。正式交付物、用户指定文件和源 Markdown 保持在项目约定位置；不要把密钥、令牌、Cookie、私有指令、隐私或不必要的大体积原始数据写入任务目录。纯文本答复不需要创建任务目录。

## 执行流程

1. 先运行 `bsk workspace status TASK_ROOT`、`bsk state list --skill-root SKILL_ROOT` 与 `bsk verifier describe markdown.link-integrity --version 1.0.0`，确认 kernel、任务工作区、状态声明和 Verifier 可用。缺少任一项即停止，并在 `log/` 保留诊断；不得改用无状态机或无 Verifier 的检查流程。
2. 确认目标 Markdown 文件存在并以只读方式处理。以 `workspace.ready` 为起点，执行 `validate-md-ref.input-ready` 状态转移，向 `context.document` 传入该文件路径；仅在转移成功后继续。
3. 执行 `validate-md-ref.checking` 状态转移，并强制运行 `markdown.link-integrity@1.0.0`。为 Verifier 指定 `--events TASK_ROOT/log/events.ndjson`、稳定的 `--run-id` 和适用的超时/域名策略；将标准化 Verifier 结果写入 `output/`。未取得 Verifier 结果或 Gate 时，本次检查失败，不能只输出脚本结果。
4. 再运行 `scripts/validate_links.py`，使其加载本 Skill 的 YAML 配置并生成兼容的引用明细；同时传入相同的 `--events` 与 `--run-id`，保留其 `citation.truth-and-fit` 的语义核验状态。链接完整性和语义真实性是不同结论，不能相互替代。
5. 汇总 `summary`、逐条 `references[*].validation`、`verification.results` 与 `verification.gate`。明确区分有效、无效、跳过和待人工核验，保留失败原因后才执行 `validate-md-ref.reported` 状态转移，并将状态快照保存在 `log/meta-state.json`。

调用脚本时，`scripts/validate_links.py` 指 Skill 目录中的脚本。若当前工作目录不是该目录，应使用脚本的绝对路径，或先切换到 Skill 目录。运行脚本的 Python 解释器必须能导入 `bensz_skill_kernel`，并与 `bsk` 使用同一已安装环境；否则将无法满足强制运行时要求。

## 强制运行时要求

- 每次执行都必须使用已安装的 `bensz-skill-kernel`，并完成 `validate-md-ref.input-ready` → `validate-md-ref.checking` → `validate-md-ref.reported` 三次状态转移。
- 每次执行都必须运行 `markdown.link-integrity@1.0.0`；不能以 `validate_links.py`、手工检查或已有旧报告替代。
- `citation.truth-and-fit@1.0.0` 的结果也必须保留。其为 instruction-only Verifier 时，`manual_review` 或 `unchecked` 是诚实的语义结论，不得伪造 `allow`。
- 任一状态转移、Verifier 或事件记录失败时，交付必须标记为失败/未完成，说明原因与可复现命令；不得静默降级。

执行前完整阅读 [`references/state-machine.md`](references/state-machine.md) 与 [`references/verifiers.md`](references/verifiers.md)，其中定义了状态上下文、事件账本与 Verifier 契约。

## 可用工具

- `scripts/validate_links.py`：读取 Markdown 和可选 YAML 配置，输出结构化检查结果。
- `config.yaml`：提供脚本未指定自定义配置时使用的默认超时、域名白名单和黑名单。

## 命令映射

| 工作 | 命令 |
| --- | --- |
| 使用 Skill 默认配置检查 Markdown | `python3 scripts/validate_links.py DOCUMENT.md` |
| 使用自定义配置检查 Markdown | `python3 scripts/validate_links.py DOCUMENT.md CONFIG.yaml` |
| 强制链接完整性验证 | `bsk verifier run markdown.link-integrity --version 1.0.0 --input DOCUMENT.md --events TASK_ROOT/log/events.ndjson --run-id RUN_ID` |
| 强制状态转移 | `bsk state transition TASK_ROOT validate-md-ref TARGET_STATE --skill-root SKILL_ROOT --context-json JSON` |

## 参考资料

- [`references/tools.md`](references/tools.md)：可用命令、参数和配置字段的简要说明。
- [`references/formats.md`](references/formats.md)：支持的引用形式和输出字段的简要说明。
- [`references/verifiers.md`](references/verifiers.md)：必读，定义 Verifier 职责边界、版本和调用方式。
- [`references/state-machine.md`](references/state-machine.md)：必读，定义强制状态转移和结果记录方式。
- [`references/citation-truth-and-fit.md`](references/citation-truth-and-fit.md)：需要判断引用真实性与适切性时，查阅证据要求和不确定性边界。

## 遇到疑似技能设计问题时

- **适用范围**：仅记录 Skill 设计缺陷，例如流程漏判、输入约定不完整或环境假设错误；用户数据错误、第三方波动和偶发模型输出不属于 Skill 缺陷。
- **隐私保护**：不得记录密钥、密码、身份信息、邮箱、私密路径、用户名、主机名或工作目录；公开上报前必须脱敏。
- **本地优先**：先写入 `~/.bensz-skills/bugs/`，不打断当前任务；只有用户明确要求时才用本机 `gh api` 公开上报。
- **禁止就地修 bug**：发现疑似设计缺陷时不要直接修改用户本地已安装 Skill 的源代码；先记录问题，再继续当前任务。
