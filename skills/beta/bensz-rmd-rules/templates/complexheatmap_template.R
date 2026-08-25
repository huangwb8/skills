# ComplexHeatmap Nature 级别模板（可读性优先）
#
# 使用方式：
# - 依赖请集中写在 00.Environment.R（luckyBase::Plus.library）
# - 在 .Rmd 中 source("templates/nature_colors.R") 后再 source 本文件
# - 根据矩阵规模动态调整 show_row_names / show_column_names / 字体 / 尺寸

make_heatmap_nature <- function(mat, name = "Value") {
  if (!exists("nature_colors")) stop("Missing nature_colors. Please source templates/nature_colors.R first.")

  if (!is.matrix(mat)) mat <- as.matrix(mat)
  if (!is.numeric(mat)) stop("mat must be a numeric matrix.")

  finite_vals <- mat[is.finite(mat)]
  if (length(finite_vals) == 0) stop("mat contains no finite values (all NA/Inf).")

  min_val <- min(finite_vals)
  max_val <- max(finite_vals)
  if (min_val == max_val) max_val <- min_val + 1e-9

  n_rows <- nrow(mat)
  n_cols <- ncol(mat)

  row_name_size <- max(6, 10 - n_rows / 50)
  col_name_size <- max(6, 10 - n_cols / 50)

  ComplexHeatmap::Heatmap(
    mat,
    name = name,
    col = circlize::colorRamp2(c(min_val, max_val), nature_colors[c(1, 3)]),
    show_row_names = n_rows <= 100,
    show_column_names = n_cols <= 50,
    row_names_gp = grid::gpar(fontsize = row_name_size),
    column_names_gp = grid::gpar(fontsize = col_name_size),
    heatmap_legend_param = list(
      title_gp = grid::gpar(fontsize = 9, fontface = "bold"),
      labels_gp = grid::gpar(fontsize = 8)
    ),
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
# 建议 max_label_length 与 skill 的 config.yaml:plot_readability.heatmap_max_label_chars 保持一致。
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
