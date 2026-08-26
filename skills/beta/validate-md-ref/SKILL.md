---
name: validate-md-ref
description: 检查 Markdown 文档中外部 HTTP(S) URL、站内锚点和引用链接的可定位性与可达性，并输出结构化核验结果；当用户要求检查 Markdown 链接、排查失效引用、生成链接核验结果或进行交付前链接巡检时使用。若用户要判断引用是否真实支持正文论断或引用是否恰当，应转入格式无关的 citation.truth-and-fit 能力，而不是把链接可达性当作语义核验。
metadata:
  author: Bensz Conan
  short-description: 检查 Markdown 引用是否可定位、可访问
---

## 适用范围

- 输入：一个 Markdown 文件，可选一个 YAML 配置文件。
- 检查：引用提取、当前文档内的 `#anchor`、外部 HTTP(S) 链接可达性，以及白名单/黑名单等安全策略。
- 输出：结构化 JSON；确定性链接结果使用 `allow` 或 `reject`，无法完成的语义核验使用 `unchecked` 或 `manual_review` 表达。
- 不做：不判断网页内容是否支持正文论断，不自动修改原 Markdown，也不替用户决定如何修复无效链接。

## 能力分层

- `markdown.link-integrity` 是格式适配器：提取 Markdown 链接，检查站内锚点和 HTTP(S) 可达性。
- `citation.truth-and-fit` 是格式无关的语义能力契约：判断来源身份是否可信、来源证据是否支持目标论断，以及引用位置和强度是否恰当。它至少需要论断上下文、来源元数据和来源摘录，不能只凭 URL 可达性得出 `pass`。
- 本 Skill 当前只提供前一层。用户要求后一层时，按 [`references/citation-truth-and-fit.md`](references/citation-truth-and-fit.md) 准备证据并调用实现该契约的领域 Pack；若环境没有该 Pack，明确返回 `unchecked` 或 `manual_review`。

## BenszAPI 任务工作区

新任务的输入、报告和日志写入已声明的 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/validate-md-ref/input|output|log/`；同一逻辑任务复用已锁定的任务根目录，多 Skill 协作时共享材料放在任务根目录的 `shared/`。正式交付物、用户指定文件和源 Markdown 不写入该目录；不得归档密钥、令牌、Cookie、私有指令、隐私或不必要的大体积原始数据。历史 `.bensz-api/skills/` 等目录仅按需显式兼容读取、迁移或清理，新任务不得创建这些目录。

## 执行流程

1. 先确认目标 Markdown 文件存在且按只读方式处理；缺少输入时先报告缺口，不要猜测文件路径。
2. 默认使用 `scripts/validate_links.py`，因为它会自动读取 Skill 根目录的 `config.yaml`；需要更细的参数或字段说明时，再按需读取 `references/tools.md` 和 `references/formats.md`。
3. 只有在需要直接调用运行时 verifier，或需要显式覆盖超时、白名单、黑名单时，才使用 `bsk verifier run`。直接调用不会自动加载 YAML 配置。
4. 汇总 `summary`、逐条 `references[*].validation` 和 `verification.gate`，区分有效、无效、跳过与验证缺口，并保留失败原因。

命令中的 `scripts/validate_links.py` 指 Skill 根目录下的脚本；从其他工作目录调用时，请先切换到 Skill 根目录，或改用该脚本的绝对路径。

## 工具包

- `scripts/validate_links.py`：读取 Markdown 和可选 YAML 配置，输出结构化检查结果。
- `bsk verifier run markdown.link-integrity --version 1.0.0`：直接运行仓库提供的 Markdown 链接完整性检查工具。
- `config.yaml`：默认超时、域名白名单和黑名单配置。

## 命令映射

| 工作 | 命令 |
| --- | --- |
| 使用默认配置检查 Markdown | `python3 scripts/validate_links.py DOCUMENT.md` |
| 使用自定义配置检查 Markdown | `python3 scripts/validate_links.py DOCUMENT.md CONFIG.yaml` |
| 直接调用运行时工具 | `bsk verifier run markdown.link-integrity --version 1.0.0 --input DOCUMENT.md` |
| 记录审计事件 | 在脚本或 `bsk verifier run` 后追加 `--events EVENTS.ndjson --run-id RUN_ID` |

## 参考资料

- [`references/tools.md`](references/tools.md)：工具包、命令参数和配置字段的简要说明。
- [`references/formats.md`](references/formats.md)：支持的引用形式和输出字段的简要说明。
- [`references/citation-truth-and-fit.md`](references/citation-truth-and-fit.md)：格式无关的引用真实性与适切性证据契约。

## bensz-collect-bugs 约束

- **适用范围**：仅记录 Skill 设计缺陷；用户数据错误、第三方波动和偶发模型输出不属于 Skill 缺陷。
- **隐私保护**：不得记录密钥、密码、身份信息、邮箱、私密路径、用户名、主机名或工作目录；公开上报前必须脱敏。
- **本地优先**：先写入 `~/.bensz-skills/bugs/`，不打断当前任务；只有用户明确要求时才用本机 `gh api` 公开上报。
- **禁止就地修 bug**：不得直接修改用户本地已安装 Skill 的源代码来顺手修复。
