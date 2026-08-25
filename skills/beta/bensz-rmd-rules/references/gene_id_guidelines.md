# 基因 ID 优先级与可读性指南

## 适用场景

生物信息学、医学统计、临床数据分析等涉及基因标识符的 R Markdown 分析项目。

## 核心原则

在解读、做表、画图时，**优先使用 SYMBOL 类的基因 ID**，而非 ENSEMBL ID 或 ENTREZID。

## 原因

| ID 类型 | 可读性 | 典型读者认知 |
|---------|--------|-------------|
| **SYMBOL**（如 `TP53`、`EGFR`） | 高 | 大部分读者熟悉，直观易懂 |
| ENSEMBL ID（如 `ENSG00000141510`） | 低 | 仅生信专业人员熟悉 |
| ENTREZID（如 `7157`） | 低 | 仅生信专业人员熟悉 |

**核心目标**：增强可读性，让更多读者（临床医生、生物学家、学生等）能够理解分析结果。

## 实践规范

### 1. 可视化与展示（SYMBOL 优先）

在热图、火山图、箱线图、网络图等可视化中：

```r
# 推荐：使用 SYMBOL 作为标签，轴标题使用英文
ggplot(data, aes(x = SYMBOL, y = expression)) +
  geom_point() +
  labs(x = "Gene Symbol", y = "Expression Level")

# 避免：使用 ENSEMBL ID 或 ENTREZID
ggplot(data, aes(x = ensembl_id, y = expression)) +
  geom_point()

# 也避免：使用中文轴标题
ggplot(data, aes(x = SYMBOL, y = expression)) +
  geom_point() +
  labs(x = "基因", y = "表达量")
```

### 2. 表格展示（SYMBOL 为主）

在 DT::datatable、kable 等表格渲染中：

```r
# 推荐：SYMBOL 作为主列，其他 ID 作为辅助列
DT::datatable(data[, .(SYMBOL, ensembl_id, entrezid, p_value, log2FC)],
              options = list(scrollX = TRUE))

# 列顺序：SYMBOL 在前，便于读者快速识别
```

### 3. 文本解读（使用 SYMBOL）

在 Rmd 的文本解读中：

````markdown
```r
# 推荐：使用 SYMBOL 基因名
TP53 在肺癌中显著高表达（log2FC = 2.3, p < 0.001）

# 避免：使用 ENSEMBL ID
ENSG00000141510 在肺癌中显著高表达（log2FC = 2.3, p < 0.001）
```
````

### 4. 数据保存（多 ID 并存）

**关键原则**：虽然展示时优先使用 SYMBOL，但**保存的数据中应包含多种 ID**，以确保数据准确性和可追溯性。

```r
# 推荐：保存包含所有 ID 类型的完整数据
final_data <- data[, .(
  SYMBOL,
  ensembl_id,
  entrezid,
  expression,
  p_value,
  log2FC
)]

# 保存为 CSV/RDS
write.csv(final_data, "results/gene_expression.csv", row.names = FALSE)
out_dir <- file.path("tmp", "analysis")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
saveRDS(final_data, file.path(out_dir, "gene_expression.rds"))
```

**好处**：
- **准确性**：ENSEMBL ID 和 ENTREZID 是稳定的数据库标识符，避免 SYMBOL 歧义
- **可追溯性**：后续可通过其他 ID 类型回溯到原始数据库
- **灵活性**：可根据需要切换展示的 ID 类型

## 基因 ID 转换

### 常用转换函数

```r
# 强制：使用 luckyBase::convert()（本 skill 的统一接口）

# ENSEMBL -> SYMBOL
gene_symbols <- luckyBase::convert(
  ids = gene_ensembl_ids,
  from_type = "ENSEMBL",
  to_type = "SYMBOL",
  organism = "human"
)

# ENTREZID -> SYMBOL
gene_symbols2 <- luckyBase::convert(
  ids = gene_entrez_ids,
  from_type = "ENTREZID",
  to_type = "SYMBOL",
  organism = "human"
)
```

### 在数据处理流程中添加 SYMBOL

```r
# 在 .R 脚本的数据处理阶段，确保添加 SYMBOL 列（示例）
.pp_add_symbol_column <- function(data, id_col = "ensembl_id",
                                 from_type = "ENSEMBL", organism = "human") {
  ids <- data[[id_col]]
  data$SYMBOL <- luckyBase::convert(
    ids = ids,
    from_type = from_type,
    to_type = "SYMBOL",
    organism = organism
  )
  data
}
```

## 检查清单

在生成涉及基因的 R Markdown 分析时：

- [ ] **可视化**：图表的轴标签、图例是否使用 SYMBOL？
- [ ] **表格**：DT::datatable 的主列是否为 SYMBOL？
- [ ] **文本解读**：解读中提到的基因名是否使用 SYMBOL？
- [ ] **数据保存**：保存的数据是否包含 SYMBOL、ENSEMBL、ENTREZID 三列？
- [ ] **ID 转换**：是否在数据处理阶段添加了 SYMBOL 列？
- [ ] **可读性**：非生信专业背景的读者能否理解基因标识符？

## 常见问题

### Q1：SYMBOL 有歧义怎么办？

**A**：在数据保存时保留 ENSEMBL/ENTREZID 作为权威标识符，但在展示时使用 SYMBOL 并注明可能的歧义。

### Q2：某些基因没有 SYMBOL 怎么办？

**A**：使用 ENSEMBL ID 或 ENTREZID 作为备选，并在注释中说明。

### Q3：需要展示大量基因时，SYMBOL 太长怎么办？

**A**：
- 使用缩写（如 `TP53` 而非 `tumor protein p53`）
- 在图表中使用基因编号，在表格中提供完整 SYMBOL
- 使用交互式表格（DT），支持搜索和滚动

## 参考资源

- [HGNC 基因命名规范](https://www.genenames.org/)
- [ENSEMBL 基因 ID](https://www.ensembl.org/info/genome/stable/index.html)
- [NCBI Gene 数据库](https://www.ncbi.nlm.nih.gov/gene)
