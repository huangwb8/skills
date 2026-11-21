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

.bensz_subject_identity <- function(run_root, entries) {
  nested <- unlist(lapply(c("R", "scripts", "templates"), function(path) {
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
    c("_targets.R", "00.Environment.R", "renv.lock", "renv/activate.R", entries)
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
    grepl("^(?:/|[A-Za-z]:)", portable, perl = TRUE) ||
      any(parts %in% c("", ".", "..")) ||
      tolower(parts[[1]]) %in% c("raw", "reports", "tmp", "_targets", ".bensz-api")
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
    if (!is.na(link) && nzchar(link)) {
      stop("Formal products root cannot contain symlinks: ", part)
    }
  }
  portable
}

.bensz_test_mkdir <- function(path, exclusive = FALSE) {
  link <- Sys.readlink(path)
  if (!is.na(link) && nzchar(link)) stop("Test directory cannot be a symlink: ", path)
  expected <- paste0(normalizePath(getwd(), winslash = "/", mustWork = TRUE), "/", path)
  if (dir.exists(path)) {
    actual <- normalizePath(path, winslash = "/", mustWork = TRUE)
    if (.Platform$OS.type == "windows") {
      expected <- tolower(expected)
      actual <- tolower(actual)
    }
    if (actual != expected) stop("Test directory must not redirect: ", path)
    if (exclusive) stop("Test run root already exists: ", path)
  } else if (!dir.create(path, showWarnings = FALSE)) {
    stop("Could not create isolated test directory: ", path)
  }
  invisible(path)
}

.bensz_test_entry <- function(path) {
  if (!file.exists(path) || dir.exists(path)) stop("Missing formal entry: ", path)
  root <- paste0(normalizePath(getwd(), winslash = "/", mustWork = TRUE), "/")
  resolved <- normalizePath(path, winslash = "/", mustWork = TRUE)
  if (!startsWith(resolved, root)) stop("Formal entry must be inside the project")
  substring(resolved, nchar(root) + 1L)
}

bensz_test_begin <- function(
  project_state,
  workflow_mode,
  test_style,
  formal_entrypoint,
  observed_mechanisms = Sys.getenv("BENSZ_OBSERVED_MECHANISMS", unset = ""),
  report_entrypoint = ""
) {
  if (!project_state %in% c("new", "existing")) stop("Invalid project_state")
  if (!workflow_mode %in% c("simple", "complex")) stop("Invalid workflow_mode")
  if (!test_style %in% c("synthetic_fixture", "project_subset")) stop("Invalid test_style")
  if (identical(project_state, "existing") && !nzchar(observed_mechanisms)) {
    stop("Existing-project tests must describe observed mechanisms via BENSZ_OBSERVED_MECHANISMS")
  }
  formal_entrypoint <- .bensz_test_entry(formal_entrypoint)
  if (identical(workflow_mode, "complex") && !identical(formal_entrypoint, "_targets.R")) {
    stop("Complex smoke must use the project's _targets.R")
  }
  if (nzchar(report_entrypoint)) {
    report_entrypoint <- .bensz_test_entry(report_entrypoint)
    if (!grepl("\\.Rmd$", report_entrypoint, ignore.case = TRUE)) stop("Report entry must be an Rmd file")
  }
  run_id <- Sys.getenv(
    "BENSZ_TEST_RUN_ID",
    unset = paste0(format(Sys.time(), "%Y%m%d-%H%M%S"), "-", Sys.getpid())
  )
  if (!grepl("^[A-Za-z0-9][A-Za-z0-9._-]*$", run_id)) stop("BENSZ_TEST_RUN_ID is not portable")
  run_root <- paste0("tmp/tests/", run_id)
  formal_products_root <- .bensz_formal_products_path(
    Sys.getenv(
      "BENSZ_PRODUCTS_DIR",
      unset = getOption("bensz.products_dir", "products")
    )
  )
  formal_paths <- c("raw", formal_products_root, "reports", "_targets")
  .bensz_test_mkdir("tmp")
  .bensz_test_mkdir("tmp/tests")
  .bensz_test_mkdir(run_root, exclusive = TRUE)
  .bensz_test_mkdir(paste0(run_root, "/input"), exclusive = TRUE)
  identity_entries <- c(formal_entrypoint, report_entrypoint[nzchar(report_entrypoint)])
  context <- list(
    project_state = project_state,
    workflow_mode = workflow_mode,
    test_style = test_style,
    observed_mechanisms = if (nzchar(observed_mechanisms)) observed_mechanisms else "not-applicable-new-project",
    formal_entrypoint = formal_entrypoint,
    report_entrypoint = report_entrypoint,
    identity_entries = identity_entries,
    run_id = run_id,
    run_root = run_root,
    input_dir = file.path(run_root, "input"),
    products_dir = file.path(run_root, "products"),
    reports_dir = file.path(run_root, "reports"),
    targets_store = file.path(run_root, "_targets"),
    formal_paths = formal_paths,
    baseline = .bensz_tree_signature(formal_paths),
    previous_env = Sys.getenv(c(
      "BENSZ_PRODUCTS_DIR", "BENSZ_REPORTS_DIR", "BENSZ_TEST_RUN_ROOT",
      "BENSZ_ANALYSIS_INPUT", "BENSZ_TARGETS_STORE", "BENSZ_TEST_STYLE"
    ), unset = NA_character_)
  )
  context$subject_identity <- .bensz_subject_identity(run_root, identity_entries)
  Sys.setenv(
    BENSZ_TEST_RUN_ROOT = run_root,
    BENSZ_PRODUCTS_DIR = context$products_dir,
    BENSZ_REPORTS_DIR = context$reports_dir,
    BENSZ_TEST_STYLE = test_style
  )
  context
}

bensz_test_restore_environment <- function(context) {
  saved <- context$previous_env
  Sys.unsetenv(names(saved)[is.na(saved)])
  if (any(!is.na(saved))) {
    do.call(Sys.setenv, as.list(saved[!is.na(saved)]))
  }
  invisible(NULL)
}

bensz_test_prepare_input <- function(context) {
  fixture <- new.env(parent = parent.frame())
  sys.source(file.path("scripts", "tests", "test_data.R"), envir = fixture)
  test_input <- fixture$test_input
  if (!is.character(test_input) || length(test_input) != 1L ||
      !file.exists(test_input) || dir.exists(test_input)) stop("test_data.R must produce one test_input file")
  actual <- normalizePath(test_input, winslash = "/", mustWork = TRUE)
  input_dir <- normalizePath(context$input_dir, winslash = "/", mustWork = TRUE)
  if (!startsWith(actual, paste0(input_dir, "/"))) stop("Test input must stay under this run's input/")
  Sys.setenv(BENSZ_ANALYSIS_INPUT = actual)
  invisible(actual)
}

# Test-only process isolation, not a second analysis scheduler. The driver calls
# the same formal entry/DAG in a clean Rscript process with explicit renv load.
bensz_test_run_entry <- function(context) {
  literal <- function(x) paste(capture.output(dput(x)), collapse = "\n")
  driver <- tempfile("entry-", tmpdir = context$run_root, fileext = ".R")
  log <- sub("\\.R$", ".log", driver)
  # Override HTML placement for this smoke run only, so the production HTML
  # beside the source Rmd is never overwritten by lightweight data.
  render <- function(entry) paste0(
    "dir.create(", literal(context$reports_dir), ", recursive = TRUE, showWarnings = FALSE); ",
    "output <- rmarkdown::render(", literal(entry),
    ", output_dir = ", literal(context$reports_dir),
    ", knit_root_dir = getwd(), quiet = TRUE, envir = new.env(parent = globalenv())); ",
    "stopifnot(file.exists(output), file.info(output)$size > 0)"
  )
  command <- if (identical(context$workflow_mode, "complex")) {
    pipeline <- paste0("targets::tar_make(store = ", literal(context$targets_store), ", callr_function = NULL)")
    if (nzchar(context$report_entrypoint)) c(
      pipeline,
      paste0("Sys.setenv(BENSZ_TARGETS_STORE = ", literal(context$targets_store), ")"),
      render(context$report_entrypoint)
    ) else pipeline
  } else if (grepl("\\.Rmd$", context$formal_entrypoint, ignore.case = TRUE)) {
    render(context$formal_entrypoint)
  } else if (grepl("\\.R$", context$formal_entrypoint, ignore.case = TRUE)) {
    paste0("sys.source(", literal(context$formal_entrypoint), ", envir = new.env(parent = globalenv()))")
  } else {
    stop("Formal simple entry must be .R or .Rmd")
  }
  writeLines(c('source("renv/activate.R")', command), driver, useBytes = TRUE)
  status <- system2(
    file.path(R.home("bin"), "Rscript"),
    c("--vanilla", shQuote(driver)), stdout = log, stderr = log
  )
  if (!identical(status, 0L)) stop("Formal test entry failed; inspect relative run log: ", log)
  invisible(log)
}

# Remove only regenerated test outputs; never follow an escaping symlink or
# accept a formal path. Protected input is intentionally outside this helper.
bensz_test_remove_outputs <- function(context) {
  root <- normalizePath(context$run_root, winslash = "/", mustWork = TRUE)
  paths <- c(context$products_dir, context$reports_dir, context$targets_store)
  leaves <- c("products", "reports", "_targets")
  for (i in seq_along(paths)) {
    path <- paths[[i]]
    if (!file.exists(path) && !dir.exists(path)) next
    resolved <- normalizePath(path, winslash = "/", mustWork = TRUE)
    if (!identical(resolved, paste0(root, "/", leaves[[i]]))) {
      stop("Refusing to remove a path other than the declared isolated output")
    }
    unlink(path, recursive = TRUE)
    if (file.exists(path) || dir.exists(path)) stop("Could not remove isolated test output")
  }
  invisible(NULL)
}

bensz_test_finish <- function(
  context,
  assertions,
  attempts = character(),
  preflight = "NOT_RUN",
  lightweight_execution = "NOT_RUN",
  full_data_execution = "NOT_RUN",
  cleanup = "not recorded",
  rebuild_scenarios = c(cold_rebuild = "NOT_RUN", missing_delivery = "NOT_RUN",
                        input_content_change = "NOT_RUN", relocated_project = "NOT_RUN")
) {
  on.exit(bensz_test_restore_environment(context), add = TRUE)
  allowed_status <- c("PASS", "FAIL", "BLOCKED", "NOT_RUN")
  statuses <- c(preflight, lightweight_execution, full_data_execution)
  if (any(!statuses %in% allowed_status)) stop("Execution status must be PASS, FAIL, BLOCKED, or NOT_RUN")
  scenario_names <- c("cold_rebuild", "missing_delivery", "input_content_change", "relocated_project")
  if (!identical(sort(names(rebuild_scenarios)), sort(scenario_names)) ||
      any(!rebuild_scenarios %in% c(allowed_status, "NA"))) {
    stop("Record all four rebuild scenarios with explicit statuses")
  }
  if (!length(assertions) || any(!nzchar(assertions))) stop("At least one non-empty assertion is required")
  after <- .bensz_tree_signature(context$formal_paths)
  subject_after <- .bensz_subject_identity(context$run_root, context$identity_entries)
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
    paste0("- separate_report_entrypoint: ", if (nzchar(context$report_entrypoint)) context$report_entrypoint else "NOT_RUN"),
    paste0("- run_root: ", gsub("\\\\", "/", context$run_root)),
    paste0("- path_overrides: input/products/reports/store under run_root"),
    paste0("- environment: renv_project=.; ", R.version.string, "; renv.lock.md5=", if (file.exists("renv.lock")) unname(tools::md5sum("renv.lock")) else "missing"),
    paste0("- subject_identity: ", context$subject_identity),
    paste0("- preflight: ", preflight),
    paste0("- lightweight_execution: ", if (!mutation_ok && identical(lightweight_execution, "PASS")) "FAIL" else lightweight_execution),
    paste0("- full_data_execution: ", full_data_execution),
    paste0("- ", names(rebuild_scenarios), ": ", rebuild_scenarios),
    paste0("- mutation_check: ", if (mutation_ok) "PASS" else "FAIL"),
    paste0("- subject_check: ", if (subject_ok) "PASS" else "FAIL"),
    paste0("- cleanup: ", cleanup),
    "",
    "## Assertions",
    paste0("- ", assertions),
    "",
    "## Attempts",
    if (length(attempts)) paste0("- ", attempts) else "- not recorded"
  )
  writeLines(record, file.path(context$run_root, "run-record.md"), useBytes = TRUE)
  if (!mutation_ok) stop("Lightweight test modified raw, formal outputs/store, code, config, or lockfile")
  invisible(file.path(context$run_root, "run-record.md"))
}
