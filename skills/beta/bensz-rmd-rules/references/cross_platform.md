# 跨平台路径与文件 I/O

## 新项目边界

从项目根目录构造相对路径，并用 `file.path()` 适配 Windows、macOS 与 Linux：

```r
input_path <- file.path("raw", "expression.tsv")
product_path <- file.path(products_dir, "analysis_results.rds")
figure_path <- file.path("reports", "figures", "02.00.00. 主要结果.pdf")
```

- `raw/` 只读；不得把清洗结果或缓存写回。
- 完整可恢复数据写 `products/`，正式图表/表格写 `reports/`。
- Rmd 与同名 HTML 位于项目根目录。
- AI 日志、预览和检查结果写当前 `.bensz-api/task-*`，由宿主传入任务根目录。

R/ 函数名、target 名称和报告文件名必须兼容 Windows：不得包含 `< > : " / \\ | ? *` 或控制字符，不得以点/空格结尾，也不得使用 `CON`、`PRN`、`AUX`、`NUL`、`COM1`–`COM9`、`LPT1`–`LPT9` 等设备保留名。

不要手写 `/` 或 `\\` 拼接路径，也不要硬编码用户名、盘符、`/tmp` 或本机绝对路径。

## 读取与写入

```r
if (!file.exists(input_path)) stop("Missing raw input: ", input_path)
data <- utils::read.delim(input_path, check.names = FALSE, fileEncoding = "UTF-8")

output_dir <- file.path("reports", "tables")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
utils::write.table(
  data,
  file.path(output_dir, "02.00.00. 主要结果.tsv"),
  sep = "\t",
  row.names = FALSE,
  quote = TRUE,
  fileEncoding = "UTF-8"
)
```

新 pipeline 不自行实现通用缓存/完成标记；由 targets 管理 `_targets/` 状态。旧项目若已有 checkpoint helper，保持原位置并标记 legacy。

## 项目根与 Skill 根

用户分析代码以项目根为当前目录。Skill 自带脚本和资产必须从 Skill 文件自身位置解析，文档命令用 `<skill-root>/scripts/...` 表示，不假设用户当前目录是 Skill 根。

验证项目路径：

```bash
Rscript <skill-root>/scripts/validate_paths.R /path/to/project
```

## 旧 `tmp/` 项目

只有检测到现有脚本/Rmd 实际引用 `tmp/{主脚本名}/`，或用户显式声明 legacy 模式时，才继续使用旧路径。此时只做非破坏维护，不把下面写法复制到新项目：

```r
# Legacy only
legacy_output <- file.path("tmp", "existing-analysis", "result.rds")
```

## 检查清单

- [ ] 路径由 `file.path()` 构造，且从项目根或已解析的 Skill 根开始。
- [ ] `raw/` 只有读取，没有写入、移动、覆盖或删除。
- [ ] `products/`、`reports/`、`.bensz-api/task-*` 职责没有混用。
- [ ] 文件名大小写一致，不依赖 Windows 的大小写不敏感行为。
- [ ] 文本显式使用 UTF-8；Windows 控制台状态前缀使用 ASCII。
- [ ] 元数据和日志只记录相对路径，不泄露用户名、盘符或绝对私有路径。
- [ ] 旧 `tmp/` 用法被明确标为兼容路径，而非新项目默认。
