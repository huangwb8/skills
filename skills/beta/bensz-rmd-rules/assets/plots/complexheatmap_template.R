# ComplexHeatmap Nature 级别模板（可读性优先）
#
# 使用方式：
# - 声明 ComplexHeatmap 和 circlize。
# - 根据矩阵规模动态调整 show_row_names / show_column_names / 字体 / 尺寸

make_heatmap_nature <- function(mat, name = "Value") {
  if (!is.matrix(mat)) mat <- as.matrix(mat)
  if (!is.numeric(mat)) stop("mat must be a numeric matrix.")

  finite_vals <- mat[is.finite(mat)]
  if (length(finite_vals) == 0) stop("mat contains no finite values (all NA/Inf).")

  min_val <- min(finite_vals)
  max_val <- max(finite_vals)
  constant <- min_val == max_val
  palette <- if (constant) {
    breaks <- if (min_val == 0) c(0, 1) else sort(c(0, min_val))
    circlize::colorRamp2(breaks, rep("#31688E", 2))
  } else {
    circlize::colorRamp2(c(min_val, max_val), c("#440154", "#FDE725"))
  }

  n_rows <- nrow(mat)
  n_cols <- ncol(mat)

  row_name_size <- max(8, 10 - n_rows / 50)
  col_name_size <- max(8, 10 - n_cols / 50)

  ComplexHeatmap::Heatmap(
    mat,
    name = name,
    col = palette,
    show_row_names = n_rows <= 100,
    show_column_names = n_cols <= 50,
    row_names_gp = grid::gpar(fontsize = row_name_size),
    column_names_gp = grid::gpar(fontsize = col_name_size),
    heatmap_legend_param = c(list(
      title_gp = grid::gpar(fontsize = 9, fontface = "bold"),
      labels_gp = grid::gpar(fontsize = 8)
    ), if (constant) list(at = min_val, color_bar = "discrete")),
    width = grid::unit(4 + n_cols / 20, "cm"),
    height = grid::unit(4 + n_rows / 20, "cm")
  )
}

truncate_labels <- function(x, max_chars = 15, suffix = "...") {
  if (is.null(x)) return(x)
  if (!is.character(x)) x <- as.character(x)
  if (!is.numeric(max_chars) || max_chars < 1) stop("max_chars must be a positive number.")
  ifelse(nchar(x) > max_chars, paste0(substr(x, 1, max_chars), suffix), x)
}

# 安全版：在 make_heatmap_nature 的基础上，先处理“行/列名过长”的高频可读性问题。
make_heatmap_nature_safe <- function(mat, name = "Value", max_label_length = 15) {
  if (!is.matrix(mat)) mat <- as.matrix(mat)
  rownames(mat) <- truncate_labels(rownames(mat), max_chars = max_label_length)
  colnames(mat) <- truncate_labels(colnames(mat), max_chars = max_label_length)
  make_heatmap_nature(mat = mat, name = name)
}

save_heatmap_pdf <- function(ht, filename, width = 6, height = 6, legend_side = "right") {
  if (!is.numeric(width) || width <= 0) stop("width must be a positive number.")
  if (!is.numeric(height) || height <= 0) stop("height must be a positive number.")
  dir.create(dirname(filename), recursive = TRUE, showWarnings = FALSE)
  grDevices::pdf(filename, width = width, height = height)
  on.exit(grDevices::dev.off(), add = TRUE)
  ComplexHeatmap::draw(ht, heatmap_legend_side = legend_side)
  invisible(filename)
}
