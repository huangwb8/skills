<!-- Template-ID: verifier-body; Template-Version: 1; Sync-Policy: reference -->

# VERIFIER.md 轻量正文骨架

本模板是新建或修改 `VERIFIER.md` 的正文维护入口。它规定最小语义接口，不要求复制模板说明，也不要求各段等长。简单的确定性 Verifier 可以每段只写一两句；语义、混合或人工 Verifier 应把证据充分性、判断准则和不确定性写清楚。

带 `index.json` 的 Pack 以索引作为 `id`、`version`、`classification`、`tags`、`aliases`、`mode`、`assurance_tier` 和 `components` 的单一来源，正文不得重复这些机器元数据。只有没有索引的兼容 Pack 才在 `VERIFIER.md` frontmatter 中声明身份和执行元数据。

```markdown
# {Verifier title}

## Verification target

说明这个 Verifier 要确认的稳定命题、通过意味着什么，以及不负责判断什么。不要只复述 Verifier 名称。

## Inputs and evidence

说明必需与可选的 `subject`、`context`、`requirements`、`evidence` 或 `evidence_refs`。明确缺失、空集合和证据不足的含义，不得暗示未实际读取的证据。

## Execution

说明 `script`、`agent`、`human` 组件如何检查命题，是否读取文件或网络、是否有副作用，以及关键依赖或顺序。机器可读的组件清单仍留在索引中。

## Output and verdicts

说明 `pass`、`fail` 及适用的 `uncertain`、`unchecked`、`error`、`timed_out`、`skipped` 条件，并说明重要的 `findings`、`facts` 和 `evidence_refs`。未完成的执行和证据不足不得写成 `pass`。

## Failure and boundaries

说明非法输入、执行失败、不可观察状态和人工复核路径，以及路径、网络、敏感信息、副作用和非目标边界。不得声称脚本执行了源码中不存在的检查。
```

迁移现有正文时，必须先盘点原有命题、字段、参数、执行方式、结果和失败规则，再分别归入五段。禁止使用占位句、把旧正文整体移到附录，或为了通过结构检查而删除具体行为。
