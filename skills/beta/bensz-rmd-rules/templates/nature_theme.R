# ggplot2 Nature 级别主题
# 设计目标：最大程度保证人类可读性（屏幕 + 打印）。
#
# 提示：
# - base_family 默认读取 `getOption("bensz.base_family", "sans")`：
#   - 若你在 00.Environment.R 启用了 `bensz_setup_plot_font()`，这里会自动使用其选择/注册的字体
#   - 否则回退到系统 "sans"

theme_nature <- function(base_size = 10, base_family = getOption("bensz.base_family", "sans")) {
  ggplot2::theme_bw(base_size = base_size) +
    ggplot2::theme(
      # 字体
      text = ggplot2::element_text(family = base_family, colour = "black"),
      axis.text = ggplot2::element_text(size = base_size, colour = "black"),
      axis.title = ggplot2::element_text(size = base_size * 1.1, face = "bold"),
      legend.text = ggplot2::element_text(size = base_size * 0.9),
      legend.title = ggplot2::element_text(size = base_size, face = "bold"),

      # 线条与边框
      axis.line = ggplot2::element_line(colour = "black", size = 0.5),
      axis.ticks = ggplot2::element_line(colour = "black", size = 0.5),
      panel.grid.major = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      panel.border = ggplot2::element_rect(colour = "black", fill = NA, size = 0.5),
      panel.background = ggplot2::element_rect(fill = "white"),

      # 图例
      legend.position = "right",
      legend.key = ggplot2::element_rect(fill = "white", colour = NA),
      legend.box.background = ggplot2::element_rect(colour = "black", size = 0.3),

      # 标题与分面
      plot.title = ggplot2::element_text(size = base_size * 1.3, face = "bold", hjust = 0.5),
      strip.text = ggplot2::element_text(size = base_size, face = "bold"),
      strip.background = ggplot2::element_rect(fill = "grey90", colour = "black")
    )
}

# 可读性增强版：为“长标签/旋转标签/图例外置”等高频场景提供更友好的默认值。
# 说明：这里不做“基于数据自动决策”（避免过度设计）；只提供更少的手工改动点。
theme_nature_readable <- function(
  base_size = 10,
  base_family = getOption("bensz.base_family", "sans"),
  x_text_angle = 0,
  legend_position = "right"
) {
  bottom_margin <- if (is.numeric(x_text_angle) && x_text_angle != 0) 18 else 10

  theme_nature(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      legend.position = legend_position,
      axis.text.x = ggplot2::element_text(
        angle = x_text_angle,
        hjust = if (x_text_angle == 0) 0.5 else 1,
        vjust = if (x_text_angle == 0) 0.5 else 1
      ),
      plot.margin = ggplot2::margin(10, 10, bottom_margin, 10)
    )
}
