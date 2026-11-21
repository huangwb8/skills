# Keep the generated theme available when the Rmd moves into a subdirectory.
report_theme_options <- function(input, project_root) {
  report_dir <- dirname(input)
  if (identical(report_dir, project_root)) return(list())
  formats <- rmarkdown::yaml_front_matter(input)$output
  if (!is.list(formats) || !is.list(formats$html_document)) return(list())
  html <- formats$html_document
  theme_dir <- "templates/liquid-glass"
  rebase <- function(paths, filename) {
    if (is.null(paths)) return(paths)
    paths <- unlist(paths, use.names = FALSE)
    theme_path <- paste0(theme_dir, "/", filename)
    project_path <- file.path(project_root, theme_path)
    if (!file.exists(file.path(report_dir, theme_path)) && file.exists(project_path)) {
      paths[paths == theme_path] <- project_path
    }
    paths
  }
  options <- list()
  css <- rebase(html$css, "liquid_glass_theme.css")
  if (!is.null(css) && !identical(css, unlist(html$css, use.names = FALSE))) options$css <- css
  includes <- html$includes
  if (is.list(includes)) {
    after <- rebase(includes$after_body, "liquid_glass_lightbox.html")
    if (!is.null(after) && !identical(after, unlist(includes$after_body, use.names = FALSE))) {
      includes$after_body <- after
      options$includes <- includes
    }
  }
  options
}

# Start in the project root with Rscript --vanilla run.R COMMAND [REPORT.Rmd].
main <- function(args) {
  commands <- c("prepare", "restore", "update-lock", "build", "report")
  if (!length(args) || length(args) > 2L || !args[[1L]] %in% commands ||
      (length(args) == 2L && !args[[1L]] %in% c("build", "report"))) {
    stop("Usage: Rscript --vanilla run.R {prepare|restore|update-lock|build|report} [REPORT.Rmd]",
         call. = FALSE)
  }
  if (!file.exists("00.Environments/environment.R")) {
    stop("Start Rscript from the project root.", call. = FALSE)
  }
  command <- args[[1L]]
  sys.source("00.Environments/environment.R", envir = environment())
  if (command %in% c("prepare", "restore", "update-lock")) {
    prepare_environment(command)
    return(invisible(NULL))
  }
  input <- if (length(args) == 2L) args[[2L]] else "report.Rmd"
  if (!file.exists(input) || dir.exists(input) || !grepl("\\.[Rr][Mm][Dd]$", input)) {
    stop("Provide the path of an existing Rmd, relative to the project root.")
  }
  input <- normalizePath(input, winslash = "/", mustWork = TRUE)
  if (!startsWith(input, paste0(project_root, "/"))) stop("Report must be inside the project.")
  relative <- substring(input, nchar(project_root) + 2L)
  components <- strsplit(relative, "/", fixed = TRUE)[[1L]]
  if (tolower(components[[1L]]) %in%
      c("raw", "_targets", "00.environments")) stop("Report cannot be in a protected directory.")
  # A previously linked HTML could direct the renderer outside the project.
  output <- file.path(dirname(input), paste0(tools::file_path_sans_ext(basename(input)), ".html"))
  link <- Sys.readlink(output)
  if (!is.na(link) && nzchar(link)) stop("The output HTML must not be a symbolic link.")
  if (dir.exists(output)) stop("The output HTML path is already a directory.", call. = FALSE)
  use_environment()
  if (!rmarkdown::pandoc_available()) stop("Pandoc is required to produce the HTML report.")
  theme_options <- report_theme_options(input, project_root)
  if (command == "build" && file.exists("_targets.R")) {
    targets::tar_make(script = "_targets.R", store = "_targets", callr_function = NULL)
  }
  rmarkdown::render(input, output_format = "html_document", output_file = basename(output),
                    output_dir = dirname(output), intermediates_dir = dirname(input),
                    knit_root_dir = project_root,
                    output_options = theme_options,
                    envir = list2env(list(report_root_prefix = strrep("../", length(components) - 1L)),
                                     parent = globalenv()))
}
main(commandArgs(trailingOnly = TRUE))
