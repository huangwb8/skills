---
name: validate-md-ref
description: 检查 Markdown 文档中的引用是否可定位、URL 或锚点是否可访问，并整理供后续判断引用真实性与适切性的结构化证据。当用户要求核查引用、检查文档链接，或确认引用是否支持正文论断时使用。
metadata:
  author: Bensz Conan
  short-description: 检查 Markdown 引用是否可定位、可访问
---

## 适用范围

- 输入：一个 Markdown 文件，可选一个 YAML 配置文件。
- 检查：Markdown 行内链接、HTML `<a href>` 链接、当前文档内的 `#anchor`，以及外部 HTTP(S) 链接的可达性。
- 输出：结构化 JSON，逐条保留引用位置、验证状态和失败或跳过原因。
- 不做：不修改原 Markdown，不把 URL 可达性解释成“来源支持正文论断”，也不替用户决定如何修复引用。

## 执行约束

每次执行都必须经过 Bensz Skill Kernel 的状态机，并调用指定版本的链接完整性 Verifier。状态机和 Verifier 是本 Skill 的运行时门禁：任一环节不可用或失败，都必须将本次任务标记为未完成并说明原因，不得退回到只运行普通脚本或手工检查。

调用 AI 应使用本 Skill 提供的执行器或已封装的运行入口；不要在对话中手工模拟状态转移、拼接事件账本或复制 Verifier 规则。状态机、Verifier 的具体命令、上下文和事件记录契约见：

- [`references/state-machine.md`](references/state-machine.md)
- [`references/verifiers.md`](references/verifiers.md)

## 业务流程

1. 确认目标 Markdown 文件存在且按只读方式处理；需要限制网络请求时加载默认或指定的 YAML 配置。
2. 提取引用并按类型检查：站内锚点在当前文档中定位，HTTP(S) 链接按安全策略检查可达性，白名单或黑名单命中的地址明确标为跳过。
3. 保留链接完整性 Verifier 的标准化结果；如需判断引用真实性或适切性，保留语义 Verifier 的 `unchecked` 或 `manual_review`，没有证据时不得猜测为通过。
4. 汇总总数、有效、无效和跳过项，逐条披露位置、状态和失败原因，并明确说明语义核验的边界。

## 执行产物与文件边界

执行需要落盘时，将本 Skill 独有的输入引用、临时结果和日志写入当前会话已声明的 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/validate-md-ref/{input,output,log}/`。多 Skill 协作的共享材料放在任务根目录的 `shared/`。正式交付物、用户指定文件和源 Markdown 保持在项目约定位置；不得写入密钥、令牌、Cookie、私有指令、隐私或不必要的大体积原始数据。纯文本答复不需要创建任务目录。

## 可用工具

- `scripts/validate_links.py`：读取 Markdown 和可选 YAML 配置，输出结构化检查结果。
- `config.yaml`：提供默认超时、域名白名单和黑名单。

调用脚本时使用 Skill 目录中的脚本路径；如果当前工作目录不同，使用绝对路径或先切换到 Skill 目录。运行入口负责完成本节所述的状态机和 Verifier 门禁，不应绕过它直接解释脚本的局部结果。

常用业务调用形式：

```bash
python3 scripts/validate_links.py DOCUMENT.md
python3 scripts/validate_links.py DOCUMENT.md CONFIG.yaml
```

输出字段和配置字段的完整说明见 [`references/formats.md`](references/formats.md) 与 [`references/tools.md`](references/tools.md)。

## 遇到疑似技能设计问题时

- **适用范围**：仅记录 Skill 设计缺陷，例如流程漏判、输入约定不完整或环境假设错误；用户数据错误、第三方波动和偶发模型输出不属于 Skill 缺陷。
- **隐私保护**：不得记录密钥、密码、身份信息、邮箱、私密路径、用户名、主机名或工作目录；公开上报前必须脱敏。
- **本地优先**：先写入 `~/.bensz-skills/bugs/`，不打断当前任务；只有用户明确要求时才用本机 `gh api` 公开上报。
- **禁止就地修 bug**：发现疑似设计缺陷时不要直接修改用户本地已安装 Skill 的源代码；先记录问题，再继续当前任务。
