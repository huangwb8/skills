# plot_delivery_helpers.R
#
# Purpose:
# - Provide a tiny, copy-friendly helper layer for "PDF as the only formal deliverable"
#   + "auto-generate a raster preview (JPG) for visual self-check".
#
# Design:
# - KISS: prefer deterministic filesystem + system CLI tools; avoid heavy R deps.
# - Cross-platform: try multiple backends (pdftools, poppler, ImageMagick, macOS sips).

.bensz_is_writable_dir <- function(path) {
  if (!is.character(path) || length(path) != 1 || !nzchar(path)) return(FALSE)
  if (!dir.exists(path)) return(FALSE)
  # Try a cheap write probe (more reliable than file.access on some mounts).
  probe <- file.path(path, paste0(".bensz_write_probe_", Sys.getpid(), "_", as.integer(Sys.time())))
  ok <- tryCatch({
    writeLines("ok", probe, useBytes = TRUE)
    TRUE
  }, error = function(e) FALSE)
  if (file.exists(probe)) unlink(probe, force = TRUE)
  ok
}

bensz_run_dir <- function(root_dir = NULL, prefix = "bensz-rmd-rules") {
  # root_dir:
  # - NULL/"" => default to ./.bensz-api/skills
  # - non-empty => use it as the parent directory (do not hardcode /tmp in user code)
  if (!is.character(prefix) || length(prefix) != 1 || !nzchar(prefix)) {
    stop("prefix must be a non-empty string.")
  }

  if (is.null(root_dir) || (is.character(root_dir) && length(root_dir) == 1 && !nzchar(root_dir))) {
    root_dir <- file.path(getwd(), ".bensz-api", "skills")
  }
  if (!is.character(root_dir) || length(root_dir) != 1 || !nzchar(root_dir)) {
    stop("root_dir must be NULL or a non-empty string.")
  }

  base_dir <- file.path(root_dir, prefix)
  if (!dir.exists(base_dir)) dir.create(base_dir, recursive = TRUE, showWarnings = FALSE)

  ts <- format(Sys.time(), "%Y%m%d%H%M%S")
  run_dir <- file.path(base_dir, paste0("run_", ts))

  # Avoid collision in fast repeated calls.
  if (dir.exists(run_dir)) {
    run_dir <- file.path(base_dir, paste0("run_", ts, "_", Sys.getpid()))
  }

  dir.create(run_dir, recursive = TRUE, showWarnings = FALSE)
  normalizePath(run_dir, winslash = "/", mustWork = FALSE)
}

.bensz_has_cmd <- function(cmd) nzchar(Sys.which(cmd))

.bensz_system2_status <- function(cmd, args, quiet = TRUE) {
  if (isTRUE(quiet)) {
    out <- suppressWarnings(system2(cmd, args = args, stdout = TRUE, stderr = TRUE))
    st <- attr(out, "status")
    if (is.null(st)) return(0L)
    return(as.integer(st))
  }
  as.integer(suppressWarnings(system2(cmd, args = args)))
}

.bensz_ensure_parent_dir <- function(path) {
  d <- dirname(path)
  if (!dir.exists(d)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
  invisible(TRUE)
}

.bensz_without_ext <- function(path) sub("\\.[^.]*$", "", path)

bensz_pdf_to_jpg <- function(pdf_path, jpg_path, dpi = 200, page = 1, quiet = TRUE) {
  if (!is.character(pdf_path) || length(pdf_path) != 1 || !nzchar(pdf_path)) {
    stop("pdf_path must be a non-empty string.")
  }
  if (!file.exists(pdf_path)) stop("PDF not found: ", pdf_path)

  if (!is.character(jpg_path) || length(jpg_path) != 1 || !nzchar(jpg_path)) {
    stop("jpg_path must be a non-empty string.")
  }
  .bensz_ensure_parent_dir(jpg_path)

  dpi <- as.integer(dpi)
  page <- as.integer(page)
  if (is.na(dpi) || dpi <= 0) stop("dpi must be a positive integer.")
  if (is.na(page) || page <= 0) stop("page must be a positive integer (1-based).")

  # Ensure we don't leave stale output around.
  if (file.exists(jpg_path)) unlink(jpg_path, force = TRUE)

  # 1) pdftools (if available): try direct conversion first.
  if (requireNamespace("pdftools", quietly = TRUE)) {
    ok <- tryCatch({
      # pdf_convert writes image files; some builds support jpeg output.
      pdftools::pdf_convert(
        pdf = pdf_path,
        pages = page,
        dpi = dpi,
        filenames = jpg_path,
        format = "jpeg"
      )
      file.exists(jpg_path)
    }, error = function(e) FALSE)
    if (isTRUE(ok)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
  }

  # 2) Poppler (preferred CLI): pdftocairo/pdftoppm
  out_prefix <- .bensz_without_ext(jpg_path)
  candidates <- c(paste0(out_prefix, ".jpg"), paste0(out_prefix, ".jpeg"))
  for (p in candidates) if (file.exists(p)) unlink(p, force = TRUE)

  if (.bensz_has_cmd("pdftocairo")) {
    args <- c("-jpeg", "-r", as.character(dpi), "-f", as.character(page), "-l", as.character(page),
              "-singlefile", pdf_path, out_prefix)
    rc <- .bensz_system2_status("pdftocairo", args = args, quiet = quiet)
    if (identical(rc, 0L)) {
      if (file.exists(paste0(out_prefix, ".jpg"))) file.rename(paste0(out_prefix, ".jpg"), jpg_path)
      if (!file.exists(jpg_path) && file.exists(paste0(out_prefix, ".jpeg"))) file.rename(paste0(out_prefix, ".jpeg"), jpg_path)
      if (file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
    }
  }

  if (.bensz_has_cmd("pdftoppm")) {
    args <- c("-jpeg", "-r", as.character(dpi), "-f", as.character(page), "-singlefile", pdf_path, out_prefix)
    rc <- .bensz_system2_status("pdftoppm", args = args, quiet = quiet)
    if (identical(rc, 0L)) {
      if (file.exists(paste0(out_prefix, ".jpg"))) file.rename(paste0(out_prefix, ".jpg"), jpg_path)
      if (!file.exists(jpg_path) && file.exists(paste0(out_prefix, ".jpeg"))) file.rename(paste0(out_prefix, ".jpeg"), jpg_path)
      if (file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
    }
  }

  # 3) ImageMagick CLI (works well when available)
  page0 <- page - 1L
  if (.bensz_has_cmd("magick")) {
    # Flatten to avoid transparent background turning black in some viewers.
    args <- c("-density", as.character(dpi), sprintf("%s[%d]", pdf_path, page0),
              "-background", "white", "-alpha", "remove", "-alpha", "off", "-flatten",
              "-quality", "92", jpg_path)
    rc <- .bensz_system2_status("magick", args = args, quiet = quiet)
    if (identical(rc, 0L) && file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
  }

  if (.bensz_has_cmd("convert")) {
    args <- c("-density", as.character(dpi), sprintf("%s[%d]", pdf_path, page0),
              "-background", "white", "-alpha", "remove", "-alpha", "off", "-flatten",
              "-quality", "92", jpg_path)
    rc <- .bensz_system2_status("convert", args = args, quiet = quiet)
    if (identical(rc, 0L) && file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
  }

  # 4) macOS fallback: sips (best-effort)
  if (.bensz_has_cmd("sips")) {
    # sips rasterizes PDFs via Quartz in most macOS setups.
    rc <- .bensz_system2_status("sips", args = c("-s", "format", "jpeg", pdf_path, "--out", jpg_path), quiet = quiet)
    if (identical(rc, 0L) && file.exists(jpg_path)) return(normalizePath(jpg_path, winslash = "/", mustWork = FALSE))
  }

  stop(
    "Failed to render JPG preview from PDF.\n",
    "- Tried: pdftools (jpeg), pdftocairo/pdftoppm, ImageMagick (magick/convert), sips.\n",
    "- PDF: ", pdf_path, "\n",
    "- JPG: ", jpg_path, "\n",
    "Suggestion: install one of poppler (pdftocairo/pdftoppm) or ImageMagick, or install R package pdftools."
  )
}
