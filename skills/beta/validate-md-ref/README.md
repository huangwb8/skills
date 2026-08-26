# validate-md-ref

当前版本：`0.4.0`。站内 `#anchor` 在当前文档本地校验；外部链接 HEAD 返回 403/405 时会做一次有限 GET 回退。运行时记录通过 `bensz-skill-kernel` 提供的 `bsk` 命令完成。

这个 skill 用来验证 Markdown 文档中的 URL 引用是否可访问，并输出结构化结果供后续处理。它现在也会给出版本化的 Verifier 结果和 Gate；这能明确区分“链接不可达”与“链接虽然可达、但不能据此证明正文论断”。

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
- `verification.results` 保存原子规则结果与证据引用；`verification.gate` 用 `reject` 或 `manual_review` 表达确定性失败和验证缺口。

## 配置

- 配置文件：`validate-md-ref/config.yaml`
- 默认超时：`10` 秒
- 默认跟随重定向：`true`
- 支持域名白名单和黑名单。
- 关键配置节：
  - `validation`
  - `domain_whitelist`
  - `domain_blacklist`
- `output` 相关字段目前更偏预留配置，不是当前 CLI 的核心生效入口。

Pack 契约见 `verifier-pack.yaml`，脱敏边界样例见 `calibration.json`。

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

这个 Skill 只声明一个命令和一个 verifier：

```bash
bsk verifier list --tag markdown
bsk verifier describe markdown.references.v1
bsk verifier run markdown.references.v1 \
  --input docs/review.md \
  --events "$EVENTS" --run-id "review-20260826-01"
```

所需 verifier：`markdown.references.v1`。它带有 `vertical`、`markdown`、`references`、`network-read` 标签；命令输出兼容 `summary`、`references`、`verification` 字段，并可选地把标准化结果写入 `events.ndjson`。Skill 不需要知道事件 payload 的具体格式。

## 常见问题

### Q：它会自动把无效链接从 Markdown 中删掉吗？

A：不会。它负责“检查并报告”，后续是否删除、替换或标注，需要你或 AI 继续判断。

### Q：为什么结果里会出现 `skipped`？

A：因为脚本会根据白名单和黑名单跳过某些域名验证，例如本地地址、内网地址，或不在白名单范围内的域名。

### Q：为什么有些本地或内网地址会被跳过？

A：默认黑名单会排除 `localhost`、`127.0.0.1`、`*.local`、`*.internal` 等域名，避免把本地开发环境误当成公开可访问链接。

### Q：它能检查 Markdown 以外的格式吗？

A：这个 skill 的目标对象就是 Markdown 文档及其 URL 引用。
