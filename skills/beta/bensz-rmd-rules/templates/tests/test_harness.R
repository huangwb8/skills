# Minimal base-R harness for isolated lightweight analysis runs.
.bensz_tree_signature <- function(paths) {
  out <- character()
  for (path in unique(paths)) {
    normalized <- gsub("\\\\", "/", path)
    if (!file.exists(path) && !dir.exists(path)) {
      out[paste0(normalized, "::<absent>")] <- ""
      next
    }
    files <- if (dir.exists(path)) {
      list.files(path, recursive = TRUE, all.files = TRUE, full.names = TRUE, no.. = TRUE)
    } else {
      path
    }
    files <- files[file.exists(files) & !dir.exists(files)]
    if (!length(files)) {
      out[paste0(normalized, "::<empty>")] <- ""
      next
    }
    keys <- gsub("\\\\", "/", files)
    out[keys] <- unname(tools::md5sum(files))
  }
  out[order(names(out))]
}

.bensz_subject_identity <- function(run_root) {
  nested <- unlist(lapply(c("scripts", "templates"), function(path) {
    if (!dir.exists(path)) return(character())
    list.files(
      path,
      pattern = "\\.(R|Rmd|ya?ml|json|css|html)$",
      recursive = TRUE,
      full.names = TRUE
    )
  }), use.names = FALSE)
  files <- unique(c(
    list.files(".", pattern = "\\.(R|Rmd|ya?ml|json)$", full.names = TRUE),
    nested,
    c("_targets.R", "00.Environment.R", "renv.lock")
  ))
  files <- files[file.exists(files) & !dir.exists(files)]
  manifest <- paste(gsub("\\\\", "/", files), unname(tools::md5sum(files)), sep = "=")
  manifest_path <- file.path(run_root, ".subject-manifest")
  writeLines(sort(manifest), manifest_path, useBytes = TRUE)
  identity <- unname(tools::md5sum(manifest_path))
  unlink(manifest_path)
  identity
}

.bensz_formal_products_path <- function(value) {
  if (!is.character(value) || length(value) != 1L || !nzchar(value)) {
    stop("Formal products root must be one non-empty project-relative path")
  }
  portable <- gsub("\\\\", "/", value)
  parts <- strsplit(portable, "/", fixed = TRUE)[[1]]
  if (
    grepl("^(?:/|[A-Za-z]:[/\\\\]|\\\\\\\\)", value, perl = TRUE) ||
      any(parts %in% c("", ".", "..")) ||
      parts[[1]] %in% c("raw", "reports", "tmp", "_targets", ".bensz-api")
  ) {
    stop("Formal products root must stay in a non-reserved project directory")
  }
  root <- normalizePath(getwd(), winslash = "/", mustWork = TRUE)
  candidate <- normalizePath(file.path(root, portable), winslash = "/", mustWork = FALSE)
  if (!startsWith(candidate, paste0(root, "/"))) stop("Formal products root escapes the project")
  current <- root
  for (part in parts) {
    current <- file.path(current, part)
    link <- Sys.readlink(current)
    if (file.exists(current) && !is.na(link) && nzchar(link)) {
      stop("Formal products root cannot contain symlinks: ", part)
    }
  }
  portable
}

bensz_test_begin <- function(
  project_state,
  workflow_mode,
  test_style,
  formal_entrypoint,
  observed_mechanisms = Sys.getenv("BENSZ_OBSERVED_MECHANISMS", unset = "")
) {
  if (!project_state %in% c("new", "existing")) stop("Invalid project_state")
  if (!workflow_mode %in% c("simple", "complex", "preserved-existing")) stop("Invalid workflow_mode")
  if (identical(project_state, "new") && identical(workflow_mode, "preserved-existing")) {
    stop("New projects cannot use preserved-existing")
  }
  if (identical(project_state, "existing") && !identical(workflow_mode, "preserved-existing")) {
    stop("Existing projects must use preserved-existing")
  }
  if (!test_style %in% c("synthetic_fixture", "project_subset")) stop("Invalid test_style")
  if (identical(project_state, "existing") && !nzchar(observed_mechanisms)) {
    stop("Existing-project tests must describe observed mechanisms via BENSZ_OBSERVED_MECHANISMS")
  }
  run_id <- Sys.getenv(
    "BENSZ_TEST_RUN_ID",
    unset = paste0(format(Sys.time(), "%Y%m%d-%H%M%S"), "-", Sys.getpid())
  )
  if (!grepl("^[A-Za-z0-9][A-Za-z0-9._-]*$", run_id)) stop("BENSZ_TEST_RUN_ID is not portable")
  run_root <- file.path("tmp", "tests", run_id)
  if (file.exists(run_root) || dir.exists(run_root)) stop("Test run root already exists: ", run_root)
  dir.create(run_root, recursive = TRUE, showWarnings = FALSE)
  formal_products_root <- .bensz_formal_products_path(
    Sys.getenv(
      "BENSZ_PRODUCTS_DIR",
      unset = getOption("bensz.products_dir", "products")
    )
  )
  formal_paths <- c("raw", formal_products_root, "reports", "_targets")
  context <- list(
    project_state = project_state,
    workflow_mode = workflow_mode,
    test_style = test_style,
    observed_mechanisms = if (nzchar(observed_mechanisms)) observed_mechanisms else "not-applicable-new-project",
    formal_entrypoint = formal_entrypoint,
    run_id = run_id,
    run_root = run_root,
    input_dir = file.path(run_root, "input"),
    products_dir = file.path(run_root, "products"),
    reports_dir = file.path(run_root, "reports"),
    targets_store = file.path(run_root, "_targets"),
    formal_paths = formal_paths,
    baseline = .bensz_tree_signature(formal_paths),
    previous_products_dir = Sys.getenv("BENSZ_PRODUCTS_DIR", unset = ""),
    previous_reports_dir = Sys.getenv("BENSZ_REPORTS_DIR", unset = ""),
    previous_test_run_root = Sys.getenv("BENSZ_TEST_RUN_ROOT", unset = "")
  )
  dir.create(context$input_dir, recursive = TRUE, showWarnings = FALSE)
  Sys.setenv(
    BENSZ_TEST_RUN_ROOT = run_root,
    BENSZ_PRODUCTS_DIR = context$products_dir,
    BENSZ_REPORTS_DIR = context$reports_dir
  )
  context$subject_identity <- .bensz_subject_identity(run_root)
  context
}

bensz_test_restore_environment <- function(context) {
  restore_one <- function(name, value) {
    if (nzchar(value)) {
      do.call(Sys.setenv, stats::setNames(list(value), name))
    } else {
      Sys.unsetenv(name)
    }
  }
  restore_one("BENSZ_PRODUCTS_DIR", context$previous_products_dir)
  restore_one("BENSZ_REPORTS_DIR", context$previous_reports_dir)
  restore_one("BENSZ_TEST_RUN_ROOT", context$previous_test_run_root)
  invisible(NULL)
}

bensz_test_finish <- function(
  context,
  assertions,
  attempts = "attempt 1: exit_status=0; PASS; failure_category=none; no correction required",
  preflight = "PASS",
  lightweight_execution = "PASS",
  full_data_execution = "NOT_RUN",
  cleanup = "isolated input removed; non-sensitive run evidence retained"
) {
  on.exit(bensz_test_restore_environment(context), add = TRUE)
  allowed_status <- c("PASS", "FAIL", "BLOCKED", "NOT_RUN")
  statuses <- c(preflight, lightweight_execution, full_data_execution)
  if (any(!statuses %in% allowed_status)) stop("Execution status must be PASS, FAIL, BLOCKED, or NOT_RUN")
  if (!length(assertions) || any(!nzchar(assertions))) stop("At least one non-empty assertion is required")
  after <- .bensz_tree_signature(context$formal_paths)
  subject_after <- .bensz_subject_identity(context$run_root)
  subject_ok <- identical(context$subject_identity, subject_after)
  mutation_ok <- identical(context$baseline, after) && subject_ok
  record <- c(
    "# Lightweight test run",
    "",
    paste0("- project_state: ", context$project_state),
    paste0("- workflow_mode: ", context$workflow_mode),
    paste0("- test_style: ", context$test_style),
    paste0("- observed_mechanisms: ", context$observed_mechanisms),
    paste0("- formal_entrypoint: ", context$formal_entrypoint),
    paste0("- run_root: ", gsub("\\\\", "/", context$run_root)),
    paste0("- path_overrides: input/products/reports/store under run_root"),
    paste0("- environment: renv_project=.; ", R.version.string, "; renv.lock.md5=", if (file.exists("renv.lock")) unname(tools::md5sum("renv.lock")) else "missing"),
    paste0("- subject_identity: ", context$subject_identity),
    paste0("- preflight: ", preflight),
    paste0("- lightweight_execution: ", lightweight_execution),
    paste0("- full_data_execution: ", full_data_execution),
    paste0("- mutation_check: ", if (mutation_ok) "PASS" else "FAIL"),
    paste0("- subject_check: ", if (subject_ok) "PASS" else "FAIL"),
    paste0("- cleanup: ", cleanup),
    "",
    "## Assertions",
    paste0("- ", assertions),
    "",
    "## Attempts",
    paste0("- ", attempts)
  )
  writeLines(record, file.path(context$run_root, "run-record.md"), useBytes = TRUE)
  if (!mutation_ok) stop("Lightweight test modified raw, formal outputs/store, code, config, or lockfile")
  invisible(file.path(context$run_root, "run-record.md"))
}
