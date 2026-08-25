# download-fulltext-pdf

这个 skill 用来尽可能把目标论文的全文 PDF 下载到本地，适合 DOI、标题或 BibTeX 驱动的全文获取；如果你已经有 PDF，只是想解析、提取或处理它，就不该用它。

## 用法

### 最推荐用法

```text
请使用 download-fulltext-pdf skill 下载这篇论文的全文 PDF。
输入：DOI、标题或 BibTeX，以及输出目录
输出：下载到本地的 PDF 文件；若失败，给出各数据源的失败原因
```

### 进阶用法

```text
请使用 download-fulltext-pdf skill 获取这篇论文的全文。
输入：DOI `10.1038/nature09492`，输出目录 `./papers`
输出：本地 PDF 文件
另外，还有下列参数约束：
- 优先尝试开放获取来源
- 若失败，保留每个数据源的失败原因
- 不覆盖已存在文件
```

## 能做什么

- 根据 DOI、标题或 BibTeX 识别目标论文。
- 按多源策略尝试下载 PDF。
- 对下载结果做基本验证，避免把 HTML 错页当成 PDF。
- 失败时给出来源级错误信息，便于你继续排查。
- 不适合处理已有 PDF，也不负责论文内容分析。

## 使用示例

### 示例 1：按 DOI 下载

```text
请使用 download-fulltext-pdf skill 下载这篇论文的全文 PDF。
输入：DOI `10.1038/nature09492`，输出目录 `./papers`
输出：下载好的 PDF 文件
```

### 示例 2：按 BibTeX 下载

```text
请使用 download-fulltext-pdf skill 下载这篇文献。
输入：BibTeX 条目，以及输出目录 `./downloads`
输出：本地 PDF 文件或失败原因报告
```

### 示例 3：要求明确失败报告

```text
请使用 download-fulltext-pdf skill 获取这篇论文的全文。
输入：论文标题和输出目录
输出：PDF 文件
另外，还有下列参数约束：
- 如果全部失败，列出每个数据源的失败原因
```

## 输出

- 成功时：输出一个本地 `.pdf` 文件。
- 默认文件名：`paper.pdf`
- 默认不会覆盖已有输出。
- 验证失败时，会继续尝试下一个数据源。
- 所有来源都失败时，会返回详细失败说明。

## 配置

- 配置文件：`download-fulltext-pdf/config.yaml`
- 常见数据源顺序：
  - `arXiv`
  - `Sci-Hub`
  - `Unpaywall`
  - 期刊官网兜底
- 默认输出覆盖：`false`
- 常见关键配置：
  - `download.scihub`
  - `download.arxiv`
  - `download.unpaywall`
  - `verification`
  - `output`

## 备选用法（脚本/硬编码）

如果你已经明确知道 DOI 和目标输出路径，脚本方式最直接。

### 输入校验

```bash
python3 download-fulltext-pdf/scripts/validate_input.py \
  10.1038/nature09492 \
  ./papers
```

### 执行下载

```bash
python3 download-fulltext-pdf/scripts/download_pdf.py \
  10.1038/nature09492 \
  ./papers
```

### 校验 PDF

```bash
python3 download-fulltext-pdf/scripts/verify_pdf.py \
  ./papers/paper.pdf
```

## 常见问题

### Q：为什么失败报告里会出现多个来源？

A：因为这个 skill 会按顺序尝试多个来源，只要前一个失败，就继续尝试下一个。

### Q：下载到了文件，但打不开怎么办？

A：这通常意味着拿到的是 HTML 页面或损坏文件。技能会尽量做 PDF 头和可解析性检查，但你仍可以再运行 `verify_pdf.py` 复核。

### Q：会覆盖我已经下载好的 PDF 吗？

A：默认不会。配置里的 `output.overwrite` 默认为 `false`。

### Q：它能帮我总结论文吗？

A：不能。它的职责是“拿到 PDF”，不是“阅读或分析 PDF”。
