# 混合架构示例（.R 计算层 / .Rmd 解读层）

本文件存放从 `SKILL.md` 下沉的“可参考示例”，用于说明：

- `.R` 负责生成**全量结果**（不做业务阈值筛选）
- `.Rmd` 负责根据 YAML `params` 做**阈值筛选 + 可视化 + 解读**

## 示例：.R（数据处理层，不做阈值筛选）

```r
# .R 只负责生成全量表，不做任何阈值筛选
micro_pan <- res_pan_cont$Data$micro
micro_pan2 <- .pp_add_symbol_column(micro_pan, "marker")

# 保存全量表（包含所有基因，不筛选 p/q 值）
.dvmut_safe_write_csv(micro_pan2, file.path(out_cont_all_data, "micro_continuous.csv"))
```

## 示例：.Rmd（分析解读层，按 params 动态筛选）

```r
# .Rmd 根据业务需求动态应用阈值筛选
micro_pan <- .dvmut_read_micro(micro_pan_path)

# 在 Rmd 中应用筛选（可随时调整参数）
top_genes_heatmap <- as.integer(params$gene_top_n_heatmap)
gene_q_cutoff <- as.numeric(params$gene_q_cutoff)

# 阈值变更无需重跑 .R，只需重新 knit .Rmd
```

## YAML params 示例（阈值只在 .Rmd 定义）

```yaml
params:
  # micro（基因层面）筛选/展示
  min_tissue_n: 60
  gene_top_n_heatmap: 25
  gene_q_cutoff: 0.10
  gene_p_cutoff: 0.05
  # GSEA（通路层面）显著性阈值
  gsea_q_cutoff: 0.10
  gsea_p_cutoff: 0.05
```

## 图表示例：Nature 级别（在 .Rmd 侧生成与保存）

```r
# 建议：把“图表配色/主题”作为可复用代码放到项目内 templates/ 或 _functions.R，
# 然后在 .Rmd 中 source()，保证全项目统一风格。

source(file.path("templates", "nature_colors.R"))
source(file.path("templates", "nature_theme.R"))

p <- ggplot2::ggplot(df, ggplot2::aes(x = x, y = y, color = group)) +
  ggplot2::geom_line(size = 0.9) +
  theme_nature(base_size = 10) +
  ggplot2::scale_color_manual(values = nature_colors) +
  ggplot2::labs(x = "X", y = "Y", color = "Group")

ggplot2::ggsave(
  filename = file.path("tmp", "{主脚本名}", "figure_line.pdf"),
  plot = p,
  width = 6,
  height = 4,
  device = "pdf"
)
```
