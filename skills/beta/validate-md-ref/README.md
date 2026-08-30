# validate-md-ref

当前版本：`0.13.2`。这个 skill 将 Markdown 作为输入适配层，提取引用并采集 URL/锚点事实，再交由目录化 verifier 协议判断引用完整性与引用真实性。每次运行都会强制经过使用 canonical State ID 的 kernel 状态机并执行 canonical Verifier；它不把链接可达性冒充语义结论，也不自动修改原文档。

它适合跨格式引用核验；Markdown 只是当前可用的输入适配器。语义引擎缺口会明确标为 `unchecked` 或 `manual_review`。调用脚本时请使用能够导入 `bensz_skill_kernel`、且与 `bsk` 同一环境的 Python 解释器。

执行细节按需阅读：

- [工具包与命令](references/tools.md)
- [输入与输出](references/formats.md)
- [Verifier 契约与边界](references/verifiers.md)
- [状态机契约](references/state-machine.md)

## 用法

### 最推荐用法

```text
请使用 validate-md-ref skill 验证这个 Markdown 文档中的 URL 引用是否可访问。
输入：`/path/to/file.md`
输出：JSON 格式的结构化验证结果，包含有效、无效和跳过的链接统计
```

### 进阶用法

```text
请使用 validate-md-ref skill 检查这个 Markdown 文档的 URL 引用。
输入：`/path/to/file.md`
输出：验证结果
另外，还有下列参数约束：
- 使用自定义配置文件：`custom-config.yaml`
- 结果里按引用类型分类
- 保留失败原因
```

## 能做什么

- 提取 Markdown 里的多种 URL 引用形式。
- 对每个 URL 做可达性检查和安全校验。
- 输出结构化结果，方便后续人工或 AI 进一步处理。
- 适合文档质检、交付前巡检、链接清单复核。
- 不负责自动改写正文内容，也不直接替你决定如何处理无效链接。

## 使用示例

### 示例 1：检查单个 Markdown

```text
请使用 validate-md-ref skill 验证这个 Markdown 文档中的 URL 引用。
输入：`README.md`
输出：JSON 结构化验证结果
```

### 示例 2：按自定义规则检查

```text
请使用 validate-md-ref skill 检查这个 Markdown 文件。
输入：`docs/review.md`
输出：验证结果
另外，还有下列参数约束：
- 使用自定义配置文件：`validate-md-ref/config.yaml`
```

### 示例 3：为交付做最后巡检

```text
请使用 validate-md-ref skill 检查这份 Markdown 交付文档的引用质量。
输入：`deliverable.md`
输出：有效、无效和跳过链接的结构化结果
```

## 输出

- 核心输出是结构化验证结果，可继续转成 Markdown 报告。
- 常见结果字段包括：
  - `summary.total`
  - `summary.valid`
  - `summary.invalid`
  - `summary.skipped`
  - `references[*].validation`
- 当前脚本直接把 JSON 结果输出到标准输出，不会自动生成独立 Markdown 报告文件。
- 使用状态机执行器时产生 `log/meta-state.json` 状态快照；传入 `--events` 时产生 `log/events.ndjson` Verifier 事件账本。直接脚本调用不会隐式创建任务工作区，若任务要求审计必须显式提供这些入口。
- `verification.results` 保存原子规则结果与证据引用；本 Skill 的 `verification.gate` 用 `allow` 或 `reject` 表达链接完整性结果。格式无关的语义 Pack 才用 `manual_review` 表达验证缺口。
- `verification.metrics` 保存 Kernel 计算的 Verifier 覆盖率、未知/不确定比例、Gate 放行率、assurance tier 与耗时指标。

## 配置

- 配置文件：`validate-md-ref/config.yaml`
- 默认超时：`10` 秒
- 重定向由 kernel 以固定上限逐跳处理，并在每一跳发起请求前重新执行安全检查。
- 支持域名白名单和黑名单。
- 关键配置节：
  - `validation`
  - `domain_whitelist`
  - `domain_blacklist`
  - `runtime`：声明 `references/states` 状态包及链接/语义 Verifier 版本；状态包使用 `references/states/index.json` 的 `bensz-pack-index-v1` 清单

Verifier 契约由 `bensz-skill-kernel` 内置 registry 统一维护；本 Skill 只声明调用方式和验证边界。

`bensz.evidence.citation-truth-fit` 是唯一的引用 Verifier，不受文档类型限制；本 Skill 负责将 Markdown 转成它所需的标准证据。旧 ID `citation.truth-and-fit` 仅作为兼容 alias。详见 [引用真实性与适切性契约](references/citation-truth-and-fit.md)。

直接调用 `bsk` 时，配置文件不会自动加载。请通过格式适配器提交结构化证据，再调用 `bensz.evidence.citation-truth-fit@1.0.0`；不能把文档路径直接当作通用语义输入。

## 备选用法（脚本/硬编码）

如果你已经知道要检查哪个 Markdown 文件，直接调用脚本就可以得到结构化结果。

### 使用默认配置

```bash
python3 validate-md-ref/scripts/validate_links.py README.md
```

### 指定自定义配置

```bash
python3 validate-md-ref/scripts/validate_links.py \
  docs/review.md \
  validate-md-ref/config.yaml
```

### 调用 kernel 内置 Verifier

这个 Skill 通过 runtime 声明链接完整性为 required、引用语义为 advisory，并保留两个 Verifier 的独立结果：

```bash
bsk verifier list --tag common
bsk verifier describe bensz.document.markdown-link-integrity --version 1.0.0
bsk verifier describe bensz.evidence.citation-truth-fit --version 1.0.0
```

所需 verifier：`bensz.evidence.citation-truth-fit`，版本 `1.0.0`。它带有 `common`、`citation`、`semantic`、`evidence` 标签；格式适配器负责提供标准证据，Verifier 输出统一的 `verification.results` 与 `verification.gate`。

## 常见问题

### Q：它会自动把无效链接从 Markdown 中删掉吗？

A：不会。它负责“检查并报告”，后续是否删除、替换或标注，需要你或 AI 继续判断。

### Q：为什么结果里会出现 `skipped`？

A：因为脚本会根据白名单和黑名单跳过某些域名验证，例如本地地址、内网地址，或不在白名单范围内的域名。

### Q：为什么有些本地或内网地址会被跳过？

A：默认黑名单会排除 `localhost`、`127.0.0.1`、`*.local`、`*.internal` 等域名，避免把本地开发环境误当成公开可访问链接。

### Q：它能检查 Markdown 以外的格式吗？

A：Markdown 只是当前 Skill 的输入适配器。Verifier `bensz.evidence.citation-truth-fit` 本身不限制 Markdown，LaTeX、Word 或其它格式适配器都可以提交同样的标准证据。
