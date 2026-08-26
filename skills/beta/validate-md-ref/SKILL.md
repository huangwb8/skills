---
name: validate-md-ref
description: 当用户要求验证 Markdown 文档中的 URL、站内锚点或引用链接是否可访问、生成链接核验报告，或在文档交付前检查 Markdown 引用时使用。它执行只读的 URL/anchor 验证，并以 bensz-skill-kernel Verifier Pack 输出可追溯结论；不用于核实网页正文是否支持某个论断。
metadata:
  author: Bensz Conan
  short-description: 基于证据与门禁协议的 Markdown 引用可达性核验
  keywords: [Markdown, URL, 锚点, 引用验证, verifier]
---

# Markdown 引用可达性 Verifier

版本由 `config.yaml:skill_info.version` 管理。此 Skill 是只读检查器：它提取 Markdown 引用、验证站内 anchor 与可声明的 HTTP(S) 可达性，并报告验证边界；绝不改写文档、删除链接或替用户判断网页内容的学术/事实支持关系。

## BenszAPI 任务工作区

新任务的输入、报告和日志写入已声明的 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/validate-md-ref/input|output|log/`；正式交付文件按用户指定的位置保存。复用同一逻辑任务既有工作区，不保存密钥、Cookie、私人正文或不必要的完整网页内容。

## 与 bensz-collect-bugs 的协作约定

- 仅当发现本 Skill 的设计契约、环境假设或流程存在缺陷时，使用 `bensz-collect-bugs` 记录脱敏的最小复现；不把用户数据错误、第三方波动或模型偶发输出当作 Skill bug。
- 先记录到 `~/.bensz-skills/bugs/`，不打断当前工作；只有用户明确要求时才用 `gh api` 公开上报。
- 不直接修改用户本地已安装 Skill 来“顺手修复”。

## 验证契约

Pack：`markdown.references.v1@1.0.0`，模式：`hybrid`。

- Subject：目标 Markdown 快照与内容哈希。
- Evidence：`markdown.snapshot`、`reference.results`；每项带来源、采集时间、哈希和脱敏标记。
- Rule：链接提取、站内 anchor、协议/域名策略和 HTTP(S) 可达性。
- Prompt/Rubric：本 Pack 不尝试由 URL 可达性推断“引用是否支持论断”，因此明确输出 `unchecked` 的语义缺口。
- Gate：有不可达引用时 `reject`；只有可达性规则通过但语义无法观察时为 `manual_review`。这是验证范围的诚实表达，不代表文档不可交付。

## 执行步骤

1. 读取目标 Markdown，确认只读范围和域名策略。
2. 运行 `scripts/validate_links.py <markdown_file> [config_file]`；外部 URL 仅允许 `http/https`，HEAD 得到 403/405 时有限 GET 回退，`#anchor` 在当前文件本地检查。
3. 保存或呈现 JSON 中的原始 `summary`、`references` 和 `verification` 三部分；不要把 `manual_review` 解释成 `pass`。
4. 如需处理失败链接，先给出定位与原因；只有用户另行授权才修改正文。

## 输出与解释

脚本兼容既有 `summary` 和 `references` 字段，并新增：

```json
{"verification":{"results":[{"verdict":"pass|fail|unchecked","evidence_refs":["..."]}],"gate":{"decision":"allow|reject|manual_review","reason":"..."}}}
```

- `pass`：该原子可达性规则有充分证据通过。
- `fail`：可定位的确定性反例，例如 HTTP 404 或缺失 anchor。
- `unchecked`：本 Pack 没有足够、或不具备合适能力来验证的事项，例如 URL 对正文主张的蕴含。
- `manual_review`：存在未闭合验证缺口，需要人或另一专用 Pack 复核。

## 安全与限制

- 不访问 `localhost`、回环地址、`.local` 或 `.internal`；配置白名单时只验证列出的域名。
- 传给 `curl` 的 URL 使用参数数组和协议校验，避免命令注入；超时按配置限制。
- URL 可访问不等于来源真实、内容相关、引用准确或许可合规；这些事项必须由具备正文证据的独立 Pack 验证。
