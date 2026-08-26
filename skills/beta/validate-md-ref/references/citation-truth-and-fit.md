# 引用真实性与适切性契约

`citation.truth-and-fit` 是格式无关的语义验证能力，不负责解析 Markdown、LaTeX、Word 或其它载体。各格式适配器先把引用归一化，再提交以下证据：

- `subject_context`：被引用支持的目标论断、必要上下文和引用位置。
- `source_metadata`：来源标题、作者、发布日期、标识符及可追溯位置。
- `source_excerpt`：与目标论断直接相关的来源摘录；只有 URL 或书目信息不够。

验证结果分别回答：

- `evidence.identity`：来源身份与元数据能否被可靠确认。
- `semantic.entailment`：来源证据是否支持目标论断，还是仅与主题相关。
- `semantic.appropriateness`：引用位置、表述强度、时效性和来源类型是否恰当。

缺少必需证据、来源无法获取、判断引擎不可用或证据存在冲突时，返回 `unchecked`、`uncertain` 或 `manual_review`，不得因为链接可访问就判定通过。

当前 `validate-md-ref` 提供 Markdown 输入适配，并调用该通用 Pack。其它格式适配器也应提交同样的三类证据；kernel 只负责版本、证据引用、结果格式和 Gate 语义。
