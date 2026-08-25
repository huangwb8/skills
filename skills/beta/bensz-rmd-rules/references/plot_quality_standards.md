# 图表质量规范（Nature 级别）

本文件定义“默认即出版级别”的图表质量标准，用于指导 AI 在生成绘图代码时自动应用统一规范。

唯一目标：最大程度保证人类可读性（屏幕阅读 + 打印均清晰）。

说明：当前仅强制 Nature 级别默认规范；不提供多期刊风格切换（保持 KISS）。

## AI 自主规划原则（必须）

- 可读性优先：任何参数调整都以“读者能否清晰阅读”为第一准则。
- 场景自适应：根据数据量/图表类型/展示载体（论文/幻灯/交互）动态调整字体、线宽、点大小、图例位置等。
- 默认值 + 允许偏离：下方提供推荐默认值；若偏离需有明确理由（例如“点数>1e4，避免遮挡需减小点大小”）。
- 避免视觉缺陷：主动检查并修复标签重叠、过密、字体过小、对比不足、中文乱码、图例遮挡等问题。

## 可读性自检清单（生成代码时必须自检）

- [ ] 字体大小：轴标签/刻度/图例/标题是否清晰？是否存在过大/过小？
- [ ] 线条与点：线宽/点大小是否与图密度匹配？是否过粗/过细？
- [ ] 标签重叠：轴刻度/注释/数据标签是否重叠？是否需要旋转/缩写/分面？
- [ ] 字符编码：中文/希腊字母/上下标是否正常？必要时指定字体或使用表达式。
- [ ] 图例布局：图例是否遮挡数据？是否应改到底部/右侧/外置？
- [ ] 配色对比：颜色是否足够区分？是否色盲友好？避免彩虹色。
- [ ] 尺寸比例：宽高比是否与内容匹配？是否过扁或过窄导致信息拥挤？

## 通用技术规范（跨包）

| 维度 | 推荐默认值 | 说明 |
|------|------------|------|
| 输出格式（静态） | PDF（矢量，优先） | 矢量优先；位图仅在特殊场景使用并说明原因 |
| 字体 | Arial / Helvetica（无衬线） | 系统缺失时回退到 `sans`，不要为了字体引入复杂依赖 |
| 背景与网格 | 白底 + 减少网格 | 避免灰底；网格默认去除或弱化，强调数据本身 |
| 配色 | Nature 调色板 / viridis | 必须色盲友好；避免彩虹色、低对比度组合 |

## ggplot2 推荐默认值

| 维度 | 推荐默认值 | 说明 |
|------|------------|------|
| 字体大小 | 轴刻度 10pt，图例 9pt，标题 12pt | 图密度高时可整体下调 2–4pt |
| 线宽 | 数据线 0.8–1.0，边框/轴线 0.5 | 复杂图可降至 0.5；强调可升至 1.5 |
| 图例位置 | 右侧或底部 | 避免遮挡数据；优先外置 |
| 保存 | `ggsave(..., device = "pdf")` | PDF 无需 dpi；若输出位图需指定 dpi 并说明 |

推荐实现（详见模板）：
- `templates/nature_colors.R`：`nature_colors`
- `templates/nature_theme.R`：`theme_nature()` / `theme_nature_readable()`

## ComplexHeatmap 推荐默认值

| 维度 | 推荐默认值 | 说明 |
|------|------------|------|
| 字体 | 行/列名 8–10pt，图例标题 9pt | 大矩阵需动态减小字体并可隐藏部分行/列名 |
| 配色 | Nature / viridis | 使用 `circlize::colorRamp2()` 构造连续色带 |
| 尺寸 | 随矩阵维度动态调整 | 避免挤压导致文字不可读 |

参考模板：`templates/complexheatmap_template.R`（含 `make_heatmap_nature_safe()` 等可读性安全入口）。

## plotly 推荐默认值

| 维度 | 推荐默认值 | 说明 |
|------|------------|------|
| 字体 | 轴标题 14px，刻度 12px，图例 11px | 随图大小调整 ±2–3px |
| 线宽 | 2–3px | 点多时可减小点大小与透明度 |
| 配色 | Nature / viridis | 保证色盲友好与高对比度 |
| 输出 | 交互优先 HTML | 静态图优先 ggplot2/ComplexHeatmap 的 PDF |

参考模板：`templates/plotly_template.R`。

## 可读性问题诊断流程

当图表出现可读性问题时，按以下流程诊断与修复（优先用“最小改动”解决核心问题）：

1. **识别问题类型**
   - 文字溢出：长标签超出画布边界（常见于分类轴）
   - 文字遮挡：标签/注释与数据点、图例、标题重叠
   - 字体过小：打印或投影不可读
   - 标签过密：刻度过多、点太多、注释太多
   - 中文/特殊字符异常：乱码、方块、缺字

2. **选择处理策略（按优先级）**
   - 调整布局：增大画布尺寸、增加边距、调整宽高比、移动图例
   - 调整内容：旋转/换行/缩写、减少 breaks、仅标注关键点
   - 调整展示方式：分面（facet）、拆成多图；必要时改用交互（plotly）

3. **验证修复效果**
   - 文字是否完全可见、无裁剪
   - 文字是否清晰可读（屏幕 + 打印）
   - 修复是否引入新问题（如旋转后边距不足、图例挤压数据）

## 常见场景处理示例（最小可复用）

说明：以下 ggplot2 示例默认已 `source("templates/nature_theme.R")`（提供 `theme_nature()` / `theme_nature_readable()`）。

### 场景 1：长分类名（基因名/样本名/分组名很长）

推荐：旋转 + 增加边距（或换行/缩写）。

```r
p <- ggplot2::ggplot(df, ggplot2::aes(x = category, y = value)) +
  ggplot2::geom_col(width = 0.8) +
  theme_nature_readable(base_size = 10, x_text_angle = 45) +
  ggplot2::theme(
    axis.text.x = ggplot2::element_text(hjust = 1, vjust = 1),
    plot.margin = ggplot2::margin(10, 10, 18, 10)
  )
```

### 场景 2：数据点很多导致标签过密（散点/火山图/条形图 topN）

推荐：只标注关键点（极值/topN）；其余用交互（plotly）或表格补充。

```r
# 不引入额外依赖的最小做法：仅保留 topN，再用 geom_text(check_overlap=TRUE)
df_label <- df[order(df$score, decreasing = TRUE), ][seq_len(min(10, nrow(df))), , drop = FALSE]

p <- ggplot2::ggplot(df, ggplot2::aes(x = x, y = y)) +
  ggplot2::geom_point(size = 1, alpha = 0.7) +
  ggplot2::geom_text(
    data = df_label,
    ggplot2::aes(label = label),
    size = 3,
    check_overlap = TRUE
  ) +
  theme_nature_readable(base_size = 10)
```

### 场景 3：图例遮挡数据（尤其面板小、分组多）

推荐：优先外置到底部，并横向排布（降低遮挡概率）。

```r
p <- p +
  ggplot2::theme(legend.position = "bottom") +
  ggplot2::guides(color = ggplot2::guide_legend(nrow = 1))
```

### 场景 4：中文显示问题（方块/乱码/缺字）

推荐：按“是否包含中文字符”选择字体族，并允许用户在 `.Rmd` 的 `params` 中覆盖。

```r
has_han <- grepl("\\p{Han}", paste(df$label, collapse = ""), perl = TRUE)
base_family <- if (has_han) "sans" else "Arial"

p <- p + theme_nature_readable(base_size = 10, base_family = base_family)
```

## 常见反模式

| 反模式 | 问题 | 更好的做法 |
|--------|------|------------|
| 硬编码图例位置 | 不同数据分布下可能遮挡 | 默认外置（底部/侧边），必要时再微调 |
| 固定字体大小 | 图尺寸变化时不可读 | 基于输出场景调整 `base_size` 与图尺寸 |
| 显示所有标签 | 数据多时重叠、不可读 | 采样/减少 breaks/只标注关键点 |
| 忽略中文字体 | 方块/乱码/缺字 | 显式指定支持中文的字体族（跨平台候选） |
