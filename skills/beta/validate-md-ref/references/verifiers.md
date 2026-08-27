# Verifier 契约与边界

本 Skill 只负责 Markdown 输入适配和链接事实采集；目录化 Verifier 负责按统一协议执行规则或语义判断。每次执行必须运行链接完整性 Verifier 并保留语义 Verifier 状态；不要在 Skill 侧复制 Verifier 注册表、规则或 Gate 逻辑。

## 可用 Verifier

- `bensz.document.markdown-link-integrity@1.0.0`：检查 Markdown 链接、HTML `href` 和站内锚点的完整性与可达性；旧 ID `markdown.link-integrity`、`markdown.references` 作为 alias。
- `bensz.evidence.citation-truth-fit@1.0.0`：格式无关的引用真实性与适切性 Verifier。它接收适配器提交的论断上下文、来源元数据和来源摘录，不直接解析 Markdown、LaTeX 或 Word；旧 ID `citation.truth-and-fit` 作为 alias。

Markdown 解析、URL 请求和锚点检查产生的是输入事实，不能直接被解释为“来源支持正文论断”的语义结论。

## 强制调用

查看目录与契约：

```bash
bsk verifier describe bensz.document.markdown-link-integrity --version 1.0.0
bsk verifier describe bensz.evidence.citation-truth-fit --version 1.0.0
```

每次运行均须执行链接完整性 Verifier，并向任务事件账本写入标准化结果：

```bash
bsk verifier run bensz.document.markdown-link-integrity --version 1.0.0 --input DOCUMENT.md \
  --events TASK_ROOT/log/events.ndjson --run-id RUN_ID
```

再运行 `scripts/validate_links.py`，传入同一个 `--events` 与 `--run-id`，以保留 `bensz.evidence.citation-truth-fit@1.0.0` 的结果。直接调用链接完整性 Verifier时不会自动读取 Skill 的 `config.yaml`；超时、白名单和黑名单必须通过 CLI 参数显式传入。任何 Verifier、Gate 或事件写入失败都必须终止本次检查，不得降级为仅脚本或手工检查。

## 结果解释

保留 Verifier 返回的 `verification.results` 与 `verification.gate`。链接事实通常用 `allow` 或 `reject` 表达；缺少语义证据、来源不可获取、判断引擎不可用或证据冲突时，应保留 `unchecked`、`uncertain` 或 `manual_review`，不得为了通过门禁而猜测。

`bensz.evidence.citation-truth-fit` 的证据字段和语义判断详见 [`citation-truth-and-fit.md`](citation-truth-and-fit.md)。
