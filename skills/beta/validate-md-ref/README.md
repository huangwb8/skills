# validate-md-ref

当前版本：`0.4.2`。这个 skill 对 Markdown 引用做只读检查：站内 `#anchor` 在当前文档本地校验，外部 HTTP(S) 链接检查可达性，并报告行号、状态和跳过原因。它不判断网页内容是否支持正文论断，也不自动修改文档。

它适合文档质检、交付前巡检和失效引用定位。底层运行时是实现手段，不是触发条件；结果中的验证缺口会明确标为 `unchecked` 或 `manual_review`。

执行细节按需阅读：

- [工具包与命令](references/tools.md)
- [输入与输出](references/formats.md)

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
- 重定向由 kernel 以固定上限逐跳处理，并在每一跳发起请求前重新执行安全检查。
- 支持域名白名单和黑名单。
- 关键配置节：
  - `validation`
  - `domain_whitelist`
  - `domain_blacklist`

Verifier 契约由 `bensz-skill-kernel` 内置 registry 统一维护；本 Skill 只声明调用方式和验证边界。

直接调用 `bsk` 时，配置文件不会自动加载。请通过 `--timeout`、重复的 `--blacklist` / `--whitelist` 显式传入策略，或使用下方脚本封装读取 YAML 配置。运行前可执行 `bsk verifier describe markdown.references.v1`；若失败，说明 kernel runtime 或该 verifier 尚不可用。

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
  --input docs/review.md --timeout 10 \
  --blacklist localhost --blacklist '*.internal' \
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
