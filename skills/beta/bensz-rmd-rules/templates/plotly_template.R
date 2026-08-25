# plotly Nature 级别模板（交互式图表）
#
# 使用方式：
# - 依赖请集中写在 00.Environment.R（luckyBase::Plus.library）
# - 在 .Rmd 中 source("templates/nature_colors.R") 后再 source 本文件

make_plotly_nature <- function(data, x, y, color = NULL, title = NULL,
                               x_title = "X", y_title = "Y", family = "Arial") {
  if (!exists("nature_colors")) stop("Missing nature_colors. Please source templates/nature_colors.R first.")

  fig <- plotly::plot_ly(
    data = data,
    x = x,
    y = y,
    color = color,
    colors = nature_colors,
    type = "scatter",
    mode = "lines+markers",
    line = list(width = 2),
    marker = list(size = 6, opacity = 0.8),
    hoverinfo = "x+y+name"
  )

  # Default: no plot title in-figure. Use filename + Rmd headings/captions for semantics.
  layout_args <- list(
    xaxis = list(
      title = list(text = x_title, font = list(size = 14, family = family)),
      tickfont = list(size = 12, family = family)
    ),
    yaxis = list(
      title = list(text = y_title, font = list(size = 14, family = family)),
      tickfont = list(size = 12, family = family)
    ),
    legend = list(
      orientation = "v",
      x = 1.02,
      y = 1,
      font = list(size = 11, family = family)
    ),
    plot_bgcolor = "white",
    paper_bgcolor = "white"
  )

  if (!is.null(title) && nzchar(title)) {
    layout_args$title <- list(text = title, font = list(size = 16, family = family))
  }

  fig <- do.call(plotly::layout, c(list(fig), layout_args))

  fig
}

save_plotly_html <- function(fig, filename) {
  dir.create(dirname(filename), recursive = TRUE, showWarnings = FALSE)
  htmlwidgets::saveWidget(fig, filename)
  invisible(filename)
}
