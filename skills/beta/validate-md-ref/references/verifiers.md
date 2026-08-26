# Verifier 契约与边界

本 Skill 只负责 Markdown 输入适配和链接事实采集；目录化 Verifier 负责按统一协议执行规则或语义判断。不要在 Skill 侧复制 Verifier 注册表、规则或 Gate 逻辑。

## 可用 Verifier

- `markdown.link-integrity@1.0.0`：检查 Markdown 链接、HTML `href` 和站内锚点的完整性与可达性。
- `citation.truth-and-fit@1.0.0`：格式无关的引用真实性与适切性 Verifier。它接收适配器提交的论断上下文、来源元数据和来源摘录，不直接解析 Markdown、LaTeX 或 Word。

Markdown 解析、URL 请求和锚点检查产生的是输入事实，不能直接被解释为“来源支持正文论断”的语义结论。

## 调用

查看目录与契约：

```bash
bsk verifier list --tag citation
bsk verifier describe citation.truth-and-fit --version 1.0.0
```

直接运行链接完整性 Verifier：

```bash
bsk verifier run markdown.link-integrity --input DOCUMENT.md
```

直接调用时不会自动读取 Skill 的 `config.yaml`；超时、白名单和黑名单必须通过 CLI 参数显式传入。需要审计时，在脚本或 `bsk verifier run` 后追加 `--events EVENTS.ndjson --run-id RUN_ID`。

## 结果解释

保留 Verifier 返回的 `verification.results` 与 `verification.gate`。链接事实通常用 `allow` 或 `reject` 表达；缺少语义证据、来源不可获取、判断引擎不可用或证据冲突时，应保留 `unchecked`、`uncertain` 或 `manual_review`，不得为了通过门禁而猜测。

`citation.truth-and-fit` 的证据字段和语义判断详见 [`citation-truth-and-fit.md`](citation-truth-and-fit.md)。
