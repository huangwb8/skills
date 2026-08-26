---
name: validate-md-ref
description: 当用户要求检查 Markdown 文档中的外部 URL、站内锚点或引用链接、生成链接核验结果、排查失效引用，或在文档交付前做链接巡检时使用。
metadata:
  author: Bensz Conan
  short-description: 检查 Markdown 引用是否可定位、可访问
---

## 工具包

- `scripts/validate_links.py`：读取 Markdown 和可选 YAML 配置，输出结构化检查结果。
- `bsk verifier run markdown.references --version 1.0.0`：直接运行仓库提供的 Markdown 引用检查工具。
- `config.yaml`：默认超时、域名白名单和黑名单配置。

## 完成工作时使用的命令

| 工作 | 命令 |
| --- | --- |
| 使用默认配置检查 Markdown | `python3 scripts/validate_links.py DOCUMENT.md` |
| 使用自定义配置检查 Markdown | `python3 scripts/validate_links.py DOCUMENT.md CONFIG.yaml` |
| 直接调用运行时工具 | `bsk verifier run markdown.references --version 1.0.0 --input DOCUMENT.md` |
| 记录审计事件 | 在上述脚本或命令后追加 `--events EVENTS.ndjson --run-id RUN_ID` |

## 参考资料

- [`references/tools.md`](references/tools.md)：工具包、命令参数和配置字段的简要说明。
- [`references/formats.md`](references/formats.md)：支持的引用形式和输出字段的简要说明。

Skill 只检查引用的提取、站内锚点和 HTTP(S) 可达性；不判断网页内容是否支持正文论断，不自动修改 Markdown。

## bensz-collect-bugs 约束

- **适用范围**：仅记录 Skill 设计缺陷；用户数据错误、第三方波动和偶发模型输出不属于 Skill 缺陷。
- **隐私保护**：不得记录密钥、密码、身份信息、邮箱、私密路径、用户名、主机名或工作目录；公开上报前必须脱敏。
- **本地优先**：先写入 `~/.bensz-skills/bugs/`，不打断当前任务；只有用户明确要求时才用本机 `gh api` 公开上报。
- **禁止就地修 bug**：不得直接修改用户本地已安装 Skill 的源代码来顺手修复。
