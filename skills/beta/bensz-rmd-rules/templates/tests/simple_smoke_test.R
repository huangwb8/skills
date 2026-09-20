# Copy to scripts/tests/smoke_test.R. Keep test-only preparation in scripts/tests/.
main <- function() {
if (!file.exists(file.path("renv", "activate.R"))) stop("Missing renv/activate.R")
source(file.path("renv", "activate.R"), local = TRUE)
source(file.path("scripts", "tests", "test_harness.R"), local = TRUE)
entry <- Sys.getenv("BENSZ_ANALYSIS_ENTRY", unset = "01.00.00. 分析报告.Rmd")
if (!file.exists(entry)) stop("Set BENSZ_ANALYSIS_ENTRY to the formal R/Rmd entry: ", entry)
test_style <- Sys.getenv("BENSZ_TEST_STYLE", unset = "synthetic_fixture")
context <- bensz_test_begin("new", "simple", test_style, entry)
on.exit(bensz_test_restore_environment(context), add = TRUE)
source(file.path("scripts", "tests", "test_data.R"), local = TRUE)
on.exit(unlink(test_input), add = TRUE)

Sys.setenv(BENSZ_ANALYSIS_INPUT = normalizePath(test_input, winslash = "/", mustWork = TRUE))
if (grepl("\\.Rmd$", entry, ignore.case = TRUE)) {
  if (!requireNamespace("rmarkdown", quietly = TRUE)) stop("Package 'rmarkdown' is required.")
  dir.create(context$reports_dir, recursive = TRUE, showWarnings = FALSE)
  output <- rmarkdown::render(entry, output_dir = context$reports_dir, quiet = TRUE, envir = new.env(parent = globalenv()))
  stopifnot(file.exists(output), file.info(output)$size > 0)
} else if (grepl("\\.R$", entry, ignore.case = TRUE)) {
  sys.source(entry, envir = new.env(parent = globalenv()))
} else {
  stop("BENSZ_ANALYSIS_ENTRY must point to .R or .Rmd")
}
unlink(test_input)
bensz_test_finish(
  context,
  assertions = c("input contract and representative groups passed", "formal paths unchanged", "report/entry executed"),
  cleanup = "isolated test input removed; run record and non-sensitive outputs retained"
)
}

main()
