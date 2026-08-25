# 图表语言规范（plot_language）

## 英文优先原则

**核心规则**：所有可视化图表（ggplot2、survminer、lattice 等）的文本元素默认必须使用英文。

适用范围：

| 文本元素 | 要求 | 示例 |
|---------|------|------|
| **轴标题** | 必须英文 | `x = "Gene Expression"` （非 `x = "基因表达"`） |
| **图例标签** | 必须英文 | `color = "Cancer Type"` （非 `color = "癌种"`） |
| **图表标题** | 默认不使用；如使用必须英文 | `title = "Survival Analysis"` （非 `title = "生存分析"`） |
| **副标题/注释** | 默认不使用；如使用必须英文 | `subtitle = "Log-rank test"` （非 `subtitle = "Log-rank 检验"`） |
| **刻度标签** | 推荐英文 | 分类变量使用英文标签（如 "LUAD"、"BRCA"） |

实践示例：

```r
# 正确做法（默认；强制）：不在图内使用 title/subtitle，把语义放在文件名与 .Rmd 正文结构里
ggplot(data, aes(x = SYMBOL, y = expression, color = cancer_type)) +
  geom_point() +
  labs(
    x = "Gene Symbol",
    y = "Expression Level (log2 TPM)",
    color = "Cancer Type"
  ) +
  theme_minimal()

# 错误做法（禁止）
ggplot(data, aes(x = SYMBOL, y = expression, color = cancer_type)) +
  geom_point() +
  labs(
    title = "不同癌种的基因表达",  # 禁止中文标题
    x = "基因",                     # 禁止中文轴标签
    y = "表达量",                   # 禁止中文轴标签
    color = "癌种"                  # 禁止中文图例
  )
```

## 例外场景

| 场景 | 处理方式 | 示例 |
|------|----------|------|
| **中文期刊投稿** | 在 YAML params 中添加 `plot_language: "zh"`，由 AI 根据参数动态调整 | `params$plot_language == "zh"` 时使用中文 |
| **特定临床术语** | 优先使用国际通用英文术语 | 使用 "Overall Survival" 而非"总生存期" |
| **基因/蛋白名称** | 始终使用国际标准符号（如 TP53、EGFR） | 无需翻译 |

实现建议：

```r
# 方式 1：在 00.Environment.R 中定义全局标签函数
.set_plot_labels <- function(language = "en") {
  if (language == "en") {
    list(
      x_title = "Gene Expression",
      y_title = "Expression Level",
      legend_title = "Cancer Type"
    )
  } else if (language == "zh") {
    list(
      x_title = "基因表达",
      y_title = "表达水平",
      legend_title = "癌种"
    )
  }
}

# 方式 2：在 .Rmd 的 YAML params 中配置
params:
  plot_language: "en"  # 或 "zh"
```

检查清单：

- [ ] 图表轴标题是否使用英文？
- [ ] 图例标签是否使用英文？
- [ ] 若显式使用了图表标题/副标题（默认不建议），是否使用英文？
- [ ] 是否避免了中文字符在图表中出现（除非有特殊例外）？
