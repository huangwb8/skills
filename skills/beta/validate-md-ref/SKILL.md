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
- 输出：结构化 JSON；确定性链接结果使用 `allow` 或 `reject`，无法完成的语义核验使用 `unchecked` 或 `manual_review` 表达。
- 不做：不判断网页内容是否支持正文论断，不自动修改原 Markdown，也不替用户决定如何修复无效链接。

## 执行产物与文件边界

执行需要落盘时，将输入引用、临时报告和日志分别写入当前会话已声明的 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/validate-md-ref/{input,output,log}/`。多 Skill 协作产生的共享材料放在任务根目录的 `shared/`。正式交付物、用户指定文件和源 Markdown 保持在项目约定位置；不要把密钥、令牌、Cookie、私有指令、隐私或不必要的大体积原始数据写入任务目录。纯文本答复不需要创建任务目录。

## 执行流程

1. 确认目标 Markdown 文件存在，并以只读方式处理；缺少输入时报告缺口，不猜测文件路径。
2. 通常运行 `scripts/validate_links.py`。未提供自定义配置时，它会加载随 Skill 提供的默认 `config.yaml`；需要项目专用策略时，将 YAML 配置作为第二个参数传入。参数和字段含义按需查阅 `references/tools.md` 与 `references/formats.md`。
3. 如果任务还需要 Verifier 或状态机，先按需阅读 `references/verifiers.md` 或 `references/state-machine.md`，再使用其中列出的命令和结果状态。这样可以复用统一的输出边界，避免把链接可达性误报成引用语义结论。
4. 汇总 `summary`、逐条 `references[*].validation` 以及（执行 Verifier 时）`verification.gate`，明确区分有效、无效、跳过和待人工核验，并保留失败原因。

调用脚本时，`scripts/validate_links.py` 指 Skill 目录中的脚本。若当前工作目录不是该目录，应使用脚本的绝对路径，或先切换到 Skill 目录。

## 可用工具

- `scripts/validate_links.py`：读取 Markdown 和可选 YAML 配置，输出结构化检查结果。
- `config.yaml`：提供脚本未指定自定义配置时使用的默认超时、域名白名单和黑名单。

## 命令映射

| 工作 | 命令 |
| --- | --- |
| 使用 Skill 默认配置检查 Markdown | `python3 scripts/validate_links.py DOCUMENT.md` |
| 使用自定义配置检查 Markdown | `python3 scripts/validate_links.py DOCUMENT.md CONFIG.yaml` |
| 查看 Verifier 调用方式 | 参见 [`references/verifiers.md`](references/verifiers.md) |
| 查看状态机调用方式 | 参见 [`references/state-machine.md`](references/state-machine.md) |

## 按需参考

- [`references/tools.md`](references/tools.md)：可用命令、参数和配置字段的简要说明。
- [`references/formats.md`](references/formats.md)：支持的引用形式和输出字段的简要说明。
- [`references/verifiers.md`](references/verifiers.md)：需要运行 Verifier 时，查阅其职责边界、版本和调用方式。
- [`references/state-machine.md`](references/state-machine.md)：需要管理状态时，查阅状态转移和结果记录方式。
- [`references/citation-truth-and-fit.md`](references/citation-truth-and-fit.md)：需要判断引用真实性与适切性时，查阅证据要求和不确定性边界。

## 遇到疑似技能设计问题时

- **适用范围**：仅记录 Skill 设计缺陷，例如流程漏判、输入约定不完整或环境假设错误；用户数据错误、第三方波动和偶发模型输出不属于 Skill 缺陷。
- **隐私保护**：不得记录密钥、密码、身份信息、邮箱、私密路径、用户名、主机名或工作目录；公开上报前必须脱敏。
- **本地优先**：先写入 `~/.bensz-skills/bugs/`，不打断当前任务；只有用户明确要求时才用本机 `gh api` 公开上报。
- **禁止就地修 bug**：发现疑似设计缺陷时不要直接修改用户本地已安装 Skill 的源代码；先记录问题，再继续当前任务。
