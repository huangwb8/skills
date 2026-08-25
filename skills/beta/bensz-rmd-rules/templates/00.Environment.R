# 00.Environment.R
# 用途：作为项目级“单一入口”，集中完成：
# - luckyBase 强制加载（本 skill 的硬前提）
# - 统一的包加载策略（luckyBase::Plus.library）
# - 可选：candidate_r 加载（仅当用户显式提供路径）
#
# 注意：
# - 这里允许做最小的依赖边界检查；主脚本/主 Rmd 不要重复检查或写降级分支。
# - 只做增量添加，不覆盖用户已有内容。

options(stringsAsFactors = FALSE)

# --- luckyBase（硬前提）---
if (!requireNamespace("luckyBase", quietly = TRUE)) {
  stop(
    "bensz-rmd-rules requires luckyBase (hard prerequisite). ",
    "Please install luckyBase first, then re-run."
  )
}
suppressPackageStartupMessages(library(luckyBase))

# --- fonts (CJK-safe defaults for plots) ---
# Purpose:
# - Make Chinese text in plots (base/ggplot2) render correctly (no "tofu"/garbled glyphs).
# - Keep behavior safe: if optional packages are missing, fall back to a reasonable system font.
#
# Notes:
# - This only affects plot rendering; it does not force any language policy (see config.yaml:plot_language).
# - If showtext/sysfonts/systemfonts are available, we register a font by file path for stable cross-device output.
if (TRUE) {
  .bensz_pick_cjk_family <- function() {
    candidates <- c(
      # macOS
      "PingFang SC", "PingFang TC", "Hiragino Sans GB",
      # Windows
      "Microsoft YaHei", "SimHei", "SimSun",
      # Linux common
      "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Source Han Sans SC",
      # Legacy
      "Arial Unicode MS"
    )

    if (requireNamespace("systemfonts", quietly = TRUE)) {
      fams <- unique(systemfonts::system_fonts()$family)
      for (f in candidates) {
        if (f %in% fams) return(f)
      }
    }
    "sans"
  }

  #' Setup a CJK-capable base font for plots
  #'
  #' @param prefer Optional preferred font family name.
  #' @param enable_showtext Whether to enable showtext::showtext_auto(TRUE).
  #'   Default is FALSE to avoid implicit global side effects. You can also set
  #'   env var BENSZ_ENABLE_SHOWTEXT=1 to enable it for the current session.
  #' @return The font family actually used (string).
  bensz_setup_plot_font <- function(prefer = NULL, enable_showtext = FALSE) {
    base_family <- if (is.character(prefer) && nzchar(prefer)) prefer else .bensz_pick_cjk_family()
    options(bensz.base_family = base_family)
    try(graphics::par(family = base_family), silent = TRUE)

    # Prefer showtext path-based registration for consistent rendering across devices.
    enable_showtext <- isTRUE(enable_showtext) || identical(Sys.getenv("BENSZ_ENABLE_SHOWTEXT"), "1")
    if (enable_showtext &&
        requireNamespace("showtext", quietly = TRUE) &&
        requireNamespace("sysfonts", quietly = TRUE) &&
        requireNamespace("systemfonts", quietly = TRUE)) {
      mf <- systemfonts::match_font(base_family)
      if (is.list(mf) && !is.null(mf$path) && is.character(mf$path) && nzchar(mf$path) && file.exists(mf$path)) {
        sysfonts::font_add("bensz_base", regular = mf$path)
        showtext::showtext_auto(enable = TRUE)
        options(bensz.base_family = "bensz_base")
        try(graphics::par(family = "bensz_base"), silent = TRUE)
        return(getOption("bensz.base_family"))
      }
    }

    getOption("bensz.base_family")
  }

  # Default behavior: pick a reasonable font family, but do NOT enable showtext
  # automatically (it affects the whole session's rendering pipeline).
  #
  # If you need stable cross-device font rendering, call:
  #   bensz_setup_plot_font(enable_showtext = TRUE)
  # or set:
  #   Sys.setenv(BENSZ_ENABLE_SHOWTEXT = "1")
  invisible(bensz_setup_plot_font(enable_showtext = FALSE))
}

# --- 常用包（按需增量添加）---
# 按你的分析需要把依赖都集中写在这里：主脚本中只用 pkg::fn() 调用即可。
# luckyBase::Plus.library("ggplot2")
# luckyBase::Plus.library("dplyr")
# luckyBase::Plus.library("DT")
#
# 图表（Nature 级别）常见依赖（按需开启）：
# luckyBase::Plus.library("ggplot2")
# luckyBase::Plus.library("circlize")
# luckyBase::Plus.library("ComplexHeatmap")
# luckyBase::Plus.library("plotly")
# luckyBase::Plus.library("htmlwidgets")

# --- candidate_r（可选）---
# 只有当用户显式提供 candidate_r_path 时，才按该路径 source()（不猜路径、不扫描磁盘）。
if (exists("candidate_r_path") && is.character(candidate_r_path) && nzchar(candidate_r_path)) {
  # 示例：按需加载单个脚本
  # f <- file.path(candidate_r_path, "feature_selection.R")
  # if (!file.exists(f)) stop("candidate_r script not found: ", f)
  # source(f)
}

# --- 你的分析专用 helper 函数可以写在这里（避免污染全局）---
if (TRUE) {
  # Example:
  # .my_prepare_data <- function(raw_data, ...) raw_data
}
