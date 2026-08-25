#!/usr/bin/env Rscript
#
# 图片可读性自动检查脚本（基础版）
#
# 使用方式：
#   Rscript scripts/check_plot_readability.R path/to/plot.pdf
#   Rscript scripts/check_plot_readability.R path/to/plot.pdf --render-jpg --out-dir path/to/run_dir --dpi 200
#
# 说明：
# - 本脚本只做“确定性、轻依赖”的基础检查；不尝试基于图像做复杂检测（避免过度设计）。
# - 若系统已安装 pdftools，将额外尝试提取文本用于快速发现“空白/无法提取”的异常情况。
#

args <- commandArgs(trailingOnly = TRUE)

.has_cmd <- function(cmd) nzchar(Sys.which(cmd))

.system2_status <- function(cmd, args, quiet = TRUE) {
  if (isTRUE(quiet)) {
    out <- suppressWarnings(system2(cmd, args = args, stdout = TRUE, stderr = TRUE))
    st <- attr(out, "status")
    if (is.null(st)) return(0L)
    return(as.integer(st))
  }
  as.integer(suppressWarnings(system2(cmd, args = args)))
}

.is_writable_dir <- function(path) {
  if (!is.character(path) || length(path) != 1 || !nzchar(path)) return(FALSE)
  if (!dir.exists(path)) return(FALSE)
  probe <- file.path(path, paste0(".bensz_write_probe_", Sys.getpid(), "_", as.integer(Sys.time())))
  ok <- tryCatch({
    writeLines("ok", probe, useBytes = TRUE)
    TRUE
  }, error = function(e) FALSE)
  if (file.exists(probe)) unlink(probe, force = TRUE)
  ok
}

.default_run_dir <- function(prefix = "bensz-rmd-rules") {
  root <- file.path(getwd(), ".bensz-api", "skills")
  base <- file.path(root, prefix)
  if (!dir.exists(base)) dir.create(base, recursive = TRUE, showWarnings = FALSE)
  run_dir <- file.path(base, paste0("run_", format(Sys.time(), "%Y%m%d%H%M%S")))
  dir.create(run_dir, recursive = TRUE, showWarnings = FALSE)
  normalizePath(run_dir, winslash = "/", mustWork = FALSE)
}

.render_pdf_to_jpg <- function(pdf_path, out_dir, dpi = 200, page = 1, quiet = TRUE) {
  if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  stem <- sub("\\.[^.]*$", "", basename(pdf_path))
  jpg_path <- file.path(out_dir, paste0(stem, ".jpg"))
  if (file.exists(jpg_path)) unlink(jpg_path, force = TRUE)

  dpi <- as.integer(dpi)
  page <- as.integer(page)
  if (is.na(dpi) || dpi <= 0) stop("Invalid dpi: ", dpi)
  if (is.na(page) || page <= 0) stop("Invalid page: ", page)

  out_prefix <- file.path(out_dir, stem)
  for (p in c(paste0(out_prefix, ".jpg"), paste0(out_prefix, ".jpeg"))) {
    if (file.exists(p)) unlink(p, force = TRUE)
  }

  if (.has_cmd("pdftocairo")) {
    rc <- .system2_status(
      "pdftocairo",
      args = c("-jpeg", "-r", as.character(dpi), "-f", as.character(page), "-l", as.character(page),
               "-singlefile", pdf_path, out_prefix),
      quiet = quiet
    )
    if (identical(rc, 0L)) {
      if (file.exists(paste0(out_prefix, ".jpg"))) file.rename(paste0(out_prefix, ".jpg"), jpg_path)
      if (!file.exists(jpg_path) && file.exists(paste0(out_prefix, ".jpeg"))) file.rename(paste0(out_prefix, ".jpeg"), jpg_path)
      if (file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
    }
  }

  if (.has_cmd("pdftoppm")) {
    rc <- .system2_status(
      "pdftoppm",
      args = c("-jpeg", "-r", as.character(dpi), "-f", as.character(page), "-singlefile", pdf_path, out_prefix),
      quiet = quiet
    )
    if (identical(rc, 0L)) {
      if (file.exists(paste0(out_prefix, ".jpg"))) file.rename(paste0(out_prefix, ".jpg"), jpg_path)
      if (!file.exists(jpg_path) && file.exists(paste0(out_prefix, ".jpeg"))) file.rename(paste0(out_prefix, ".jpeg"), jpg_path)
      if (file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
    }
  }

  page0 <- page - 1L
  if (.has_cmd("magick")) {
    rc <- .system2_status(
      "magick",
      args = c("-density", as.character(dpi), sprintf("%s[%d]", pdf_path, page0),
               "-background", "white", "-alpha", "remove", "-alpha", "off", "-flatten",
               "-quality", "92", jpg_path),
      quiet = quiet
    )
    if (identical(rc, 0L) && file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
  }

  if (.has_cmd("convert")) {
    rc <- .system2_status(
      "convert",
      args = c("-density", as.character(dpi), sprintf("%s[%d]", pdf_path, page0),
               "-background", "white", "-alpha", "remove", "-alpha", "off", "-flatten",
               "-quality", "92", jpg_path),
      quiet = quiet
    )
    if (identical(rc, 0L) && file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
  }

  if (.has_cmd("sips")) {
    rc <- .system2_status(
      "sips",
      args = c("-s", "format", "jpeg", pdf_path, "--out", jpg_path),
      quiet = quiet
    )
    if (identical(rc, 0L) && file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
  }

  stop("Failed to render JPG preview. Install poppler (pdftocairo/pdftoppm) or ImageMagick (magick/convert).")
}

.image_dims <- function(img_path) {
  if (.has_cmd("magick")) {
    out <- tryCatch(system2("magick", args = c("identify", "-format", "%w %h", img_path), stdout = TRUE, stderr = TRUE), error = function(e) NULL)
    if (is.character(out) && length(out) >= 1) {
      parts <- strsplit(trimws(out[1]), "\\s+")[[1]]
      if (length(parts) >= 2) return(list(w = as.integer(parts[1]), h = as.integer(parts[2])))
    }
  }
  if (.has_cmd("sips")) {
    out <- tryCatch(system2("sips", args = c("-g", "pixelWidth", "-g", "pixelHeight", img_path), stdout = TRUE, stderr = TRUE), error = function(e) NULL)
    if (is.character(out)) {
      w <- suppressWarnings(as.integer(sub(".*pixelWidth:\\s*", "", out[grepl("pixelWidth", out)][1])))
      h <- suppressWarnings(as.integer(sub(".*pixelHeight:\\s*", "", out[grepl("pixelHeight", out)][1])))
      if (!is.na(w) && !is.na(h)) return(list(w = w, h = h))
    }
  }
  NULL
}

.trim_margins_px <- function(img_path) {
  if (!.has_cmd("magick")) return(NULL)
  # Use -trim bbox as a deterministic proxy for "content touches border / risk of clipping".
  w_h <- .image_dims(img_path)
  if (is.null(w_h) || is.na(w_h$w) || is.na(w_h$h)) return(NULL)

  geom <- tryCatch(system2("magick", args = c(img_path, "-trim", "-format", "%@", "info:"), stdout = TRUE, stderr = TRUE), error = function(e) NULL)
  if (!is.character(geom) || length(geom) < 1) return(NULL)
  g <- trimws(geom[1])
  # Format: WxH+X+Y
  m <- regexec("^([0-9]+)x([0-9]+)\\+([0-9]+)\\+([0-9]+)$", g)
  mm <- regmatches(g, m)[[1]]
  if (length(mm) != 5) return(NULL)
  tw <- as.integer(mm[2]); th <- as.integer(mm[3]); x <- as.integer(mm[4]); y <- as.integer(mm[5])
  if (any(is.na(c(tw, th, x, y)))) return(NULL)
  list(
    left = x,
    top = y,
    right = max(0L, w_h$w - (x + tw)),
    bottom = max(0L, w_h$h - (y + th)),
    w = w_h$w,
    h = w_h$h
  )
}

.usage <- function() {
  paste(
    "Usage:",
    "  Rscript scripts/check_plot_readability.R <path_to_pdf> [--render-jpg] [--out-dir DIR] [--dpi 200] [--page 1]",
    "",
    "Notes:",
    "  - This checker is intentionally lightweight and deterministic.",
    "  - When --render-jpg is enabled, it renders page 1 into a JPG preview in --out-dir (or a temp run dir).",
    sep = "\n"
  )
}

if (length(args) == 0) {
  stop(.usage())
}

opts <- list(render_jpg = FALSE, out_dir = NULL, dpi = 200L, page = 1L)
pos <- character()
i <- 1L
while (i <= length(args)) {
  a <- args[i]
  if (identical(a, "--render-jpg")) {
    opts$render_jpg <- TRUE
    i <- i + 1L
    next
  }
  if (identical(a, "--out-dir")) {
    if (i + 1L > length(args)) stop("--out-dir requires a value.\n", .usage())
    opts$out_dir <- args[i + 1L]
    i <- i + 2L
    next
  }
  if (identical(a, "--dpi")) {
    if (i + 1L > length(args)) stop("--dpi requires a value.\n", .usage())
    opts$dpi <- suppressWarnings(as.integer(args[i + 1L]))
    i <- i + 2L
    next
  }
  if (identical(a, "--page")) {
    if (i + 1L > length(args)) stop("--page requires a value.\n", .usage())
    opts$page <- suppressWarnings(as.integer(args[i + 1L]))
    i <- i + 2L
    next
  }
  if (startsWith(a, "-")) {
    stop("Unknown option: ", a, "\n", .usage())
  }
  pos <- c(pos, a)
  i <- i + 1L
}

if (length(pos) != 1) {
  stop("Expected exactly one PDF path.\n", .usage())
}

plot_path <- pos[1]
if (!file.exists(plot_path)) {
  stop(sprintf("File not found: %s", plot_path))
}

info <- file.info(plot_path)
file_size <- info$size
if (is.na(file_size) || file_size <= 0) {
  stop(sprintf("File is empty or unreadable: %s", plot_path))
}

# 经验阈值：过小通常意味着渲染失败或内容缺失（如空白页）
if (file_size < 1000) {
  warning(sprintf("File size suspiciously small (%d bytes): %s", file_size, plot_path))
}

is_pdf <- (tolower(tools::file_ext(plot_path)) == "pdf")
if (!is_pdf) {
  warning(sprintf("Not a PDF (ext=%s). This checker is PDF-oriented: %s", tools::file_ext(plot_path), plot_path))
}

if (is_pdf && requireNamespace("pdftools", quietly = TRUE)) {
  txt <- tryCatch(
    pdftools::pdf_text(plot_path),
    error = function(e) NULL
  )
  if (is.null(txt)) {
    warning("pdftools failed to extract text (file may be corrupted, encrypted, or missing text layer).")
  } else {
    all_txt <- paste(txt, collapse = "\n")
    if (nchar(gsub("\\s+", "", all_txt)) == 0) {
      warning("No extractable text found (could be image-only PDF, or render/text embedding issue).")
    }
  }
} else if (is_pdf) {
  message("Note: pdftools not installed; skipping text extraction checks.")
}

jpg_path <- NULL
if (isTRUE(opts$render_jpg) || (is.character(opts$out_dir) && nzchar(opts$out_dir))) {
  out_dir <- if (is.character(opts$out_dir) && nzchar(opts$out_dir)) opts$out_dir else .default_run_dir()
  jpg_path <- .render_pdf_to_jpg(plot_path, out_dir = out_dir, dpi = opts$dpi, page = opts$page)

  dims <- .image_dims(jpg_path)
  if (!is.null(dims)) {
    message(sprintf("Preview JPG: %s (%dx%d px)", jpg_path, dims$w, dims$h))
    if (!is.na(dims$w) && dims$w < 1000) warning("Preview width < 1000px; readability risk (try higher dpi or larger plot size).")
    if (!is.na(dims$h) && dims$h < 800) warning("Preview height < 800px; readability risk (try higher dpi or larger plot size).")
  } else {
    message("Preview JPG: ", jpg_path)
  }

  margins <- .trim_margins_px(jpg_path)
  if (!is.null(margins)) {
    message(sprintf("Trim margins (px) L/T/R/B = %d/%d/%d/%d", margins$left, margins$top, margins$right, margins$bottom))
    if (min(c(margins$left, margins$top, margins$right, margins$bottom)) <= 4) {
      warning("Very small margins detected (<=4px). Possible clipping/too-tight layout; consider increasing plot.margin or figure size.")
    }
  }
}

cat(sprintf("[PASS] Basic checks passed for: %s\n", plot_path))
