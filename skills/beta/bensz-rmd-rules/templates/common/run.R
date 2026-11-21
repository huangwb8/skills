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
  if (tolower(strsplit(relative, "/", fixed = TRUE)[[1L]][[1L]]) %in%
      c("raw", "_targets", "00.environments")) stop("Report cannot be in a protected directory.")
  # A previously linked HTML could direct the renderer outside the project.
  output <- file.path(dirname(input), paste0(tools::file_path_sans_ext(basename(input)), ".html"))
  link <- Sys.readlink(output)
  if (!is.na(link) && nzchar(link)) stop("The output HTML must not be a symbolic link.")
  use_environment()
  if (!rmarkdown::pandoc_available()) stop("Pandoc is required to produce the HTML report.")
  if (command == "build" && file.exists("_targets.R")) {
    targets::tar_make(script = "_targets.R", store = "_targets", callr_function = NULL)
  }
  rmarkdown::render(input, output_format = "html_document", output_file = basename(output),
                    output_dir = dirname(output), knit_root_dir = project_root,
                    envir = new.env(parent = globalenv()))
}
main(commandArgs(trailingOnly = TRUE))
