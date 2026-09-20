# Copy to scripts/tests/smoke_test.R. The formal _targets.R reads the normal
# BENSZ_ANALYSIS_INPUT/BENSZ_PRODUCTS_DIR configuration; it has no test-mode branch.
main <- function() {
if (!file.exists(file.path("renv", "activate.R"))) stop("Missing renv/activate.R")
source(file.path("renv", "activate.R"), local = TRUE)
source(file.path("scripts", "tests", "test_harness.R"), local = TRUE)
if (!requireNamespace("targets", quietly = TRUE)) stop("Package 'targets' is required.")
test_style <- Sys.getenv("BENSZ_TEST_STYLE", unset = "project_subset")
context <- bensz_test_begin("new", "complex", test_style, "_targets.R")
on.exit(bensz_test_restore_environment(context), add = TRUE)
source(file.path("scripts", "tests", "test_data.R"), local = TRUE)
on.exit(unlink(test_input), add = TRUE)

Sys.setenv(
  BENSZ_ANALYSIS_INPUT = normalizePath(test_input, winslash = "/", mustWork = TRUE)
)
targets::tar_make(store = context$targets_store)
manifest <- targets::tar_meta(store = context$targets_store, fields = c(name, error))
stopifnot(nrow(manifest) > 0L, !any(!is.na(manifest$error) & nzchar(manifest$error)))
unlink(test_input)
bensz_test_finish(
  context,
  assertions = c("target graph executed", "isolated store contains successful metadata", "formal paths unchanged"),
  cleanup = "isolated project subset removed; run record and non-sensitive outputs retained"
)
}

main()
