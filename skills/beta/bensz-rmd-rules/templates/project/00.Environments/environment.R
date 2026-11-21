# Sourced by run.R from the project root. renv itself is the only host R package.
if (!requireNamespace("renv", quietly = TRUE)) {
  stop("Install renv in the host R library before preparing or running this project.", call. = FALSE)
}
project_root <- normalizePath(".", winslash = "/", mustWork = TRUE)
lockfile <- "00.Environments/renv.lock"
Sys.setenv(RENV_PATHS_RENV = "00.Environments/renv", RENV_PATHS_LOCKFILE = lockfile,
           RENV_PROFILE = "default")
project_library <- renv::paths$library(project = project_root)
project_packages <- scan("00.Environments/packages.txt", what = character(), quiet = TRUE)

activate_environment <- function() {
  options(renv.config.sandbox.enabled = TRUE, renv.config.synchronized.check = FALSE,
          renv.config.auto.snapshot = FALSE, renv.config.updates.check = FALSE,
          renv.config.user.profile = FALSE, renv.config.user.environ = FALSE)
  renv::load(project = project_root, quiet = TRUE)
}

check_lock_r <- function(lock) {
  version <- lock$R$Version
  if (!is.character(version) || length(version) != 1L || is.na(version) || !nzchar(version)) {
    stop("No R version recorded in 00.Environments/renv.lock.", call. = FALSE)
  }
  if (as.character(getRversion()) != version) {
    stop("Use the R version recorded in 00.Environments/renv.lock: R ", version, ".", call. = FALSE)
  }
}

prepare_environment <- function(action) {
  if (action == "prepare" && file.exists(lockfile)) {
    stop("A lockfile already exists. Use restore or explicitly use update-lock.")
  }
  if (action != "prepare" && !file.exists(lockfile)) {
    stop("Missing lockfile. Use prepare only to initialize a new environment.")
  }
  if (action == "restore") check_lock_r(renv::lockfile_read(lockfile))
  dir.create(project_library, recursive = TRUE, showWarnings = FALSE)
  activate_environment()
  if (action == "restore") {
    renv::restore(project = project_root, library = project_library, lockfile = lockfile,
                  prompt = FALSE, clean = FALSE)
    return(invisible(NULL))
  }
  if (identical(unname(getOption("repos")["CRAN"]), "@CRAN@")) {
    options(repos = c(CRAN = "https://cloud.r-project.org"))
  }
  renv::install(project_packages, project = project_root, library = project_library, prompt = FALSE)
  renv::snapshot(project = project_root, library = c(project_library, .Library), lockfile = lockfile,
                 packages = project_packages, prompt = FALSE)
}

use_environment <- function() {
  if (!file.exists(lockfile)) {
    stop("Missing 00.Environments/renv.lock. Use Rscript --vanilla run.R prepare for a new project.")
  }
  lock <- renv::lockfile_read(lockfile)
  check_lock_r(lock)
  records <- lock$Packages
  if (!all(project_packages %in% names(records))) {
    stop("Dependencies changed. Review packages.txt and run Rscript --vanilla run.R update-lock.")
  }
  if (!dir.exists(project_library)) {
    stop("Project library missing. Run Rscript --vanilla run.R restore.")
  }
  activate_environment()
  local_versions <- utils::installed.packages(lib.loc = project_library, noCache = TRUE)
  r_versions <- utils::installed.packages(lib.loc = .Library, priority = c("base", "recommended"),
                                         noCache = TRUE)
  versions <- rbind(local_versions, r_versions)
  actual <- setNames(versions[, "Version"], versions[, "Package"])
  expected <- vapply(records, function(record) record$Version, character(1))
  mismatched <- is.na(actual[names(expected)]) | actual[names(expected)] != expected
  if (any(mismatched)) {
    stop("Packages absent or different from the lock: ", paste(names(expected)[mismatched], collapse = ", "),
         ". Run Rscript --vanilla run.R restore.")
  }
  invisible(NULL)
}
