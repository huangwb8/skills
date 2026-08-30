# 输入与输出

## 输入

目标是一个 Markdown 文件。工具会识别常见 Markdown 行内链接、HTML `<a href>` 链接和 `#anchor` 站内锚点。

站内锚点在当前文档中检查；HTTP(S) 链接进行网络可达性检查。输入文件按只读处理。

## 输出

结果为 JSON，常用字段：

- `summary.total`、`summary.valid`、`summary.invalid`、`summary.unresolved`、`summary.skipped`
- `references[*].validation.validation_status`：`valid`、`invalid`、`unresolved`、`timed_out` 或 `skipped`；网络不可观测不等同于链接失效。
- `references[*].url`、`references[*].line_number`、`references[*].validation`
- `verification`（直接命令也提供顶层 `results` 和 `gate`）
- `verification.metrics`：Kernel 汇总的 Verifier 覆盖率、未知/不确定比例、Gate 放行率、assurance tier 与耗时指标。
- `verification.requirements`：运行时声明的 required/advisory Verifier 及版本；Gate 仅对 required 的确定性失败拒绝。
- `verification.runtime`：本次运行使用的 Kernel 名称/版本/来源与规范化 Pack 版本；同一元数据会随事件结果记录，便于审计环境漂移。

可达性通过不代表网页内容支持正文论断；被安全策略跳过的地址也不等于链接失效。

本 Skill 将 Markdown 事实适配到格式无关的 `bensz.evidence.citation-truth-fit` 契约；不要从 URL `valid: true` 推导语义结论。
