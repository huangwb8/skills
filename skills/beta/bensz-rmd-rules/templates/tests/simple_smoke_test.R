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
assert_outputs <- function() {
  # A script can exit successfully without writing anything. Require actual
  # project-specific file/science assertions for .R entries before PASS.
  assertion_script <- file.path("scripts", "tests", "assert_results.R")
  if (file.exists(assertion_script)) {
    sys.source(assertion_script, envir = environment())
  } else if (grepl("\\.R$", entry, ignore.case = TRUE)) {
    stop("Add scripts/tests/assert_results.R to verify the .R entry's actual products and scientific invariants.")
  }
}
bensz_test_run_entry(context)
assert_outputs()
# Discard only generated outputs of this isolated run, then rebuild in a second
# clean process. For .R entries add assertions for actual files and science;
# for Rmd the driver verifies that a non-empty HTML is rendered.
bensz_test_remove_outputs(context)
bensz_test_run_entry(context)
assert_outputs()
# Add project-specific result assertions here, and input-change/relocation cases
# from references/rebuild_contract.md. Do not promote NOT_RUN to PASS by editing
# a label without executing those cases.
unlink(test_input)
bensz_test_finish(
  context,
  assertions = c("fixture preparation assertions passed", "formal entry executed twice in clean processes", "isolated outputs regenerated", "formal paths unchanged"),
  rebuild_scenarios = c(cold_rebuild = "PASS", missing_delivery = "NOT_RUN",
                        input_content_change = "NOT_RUN", relocated_project = "NOT_RUN"),
  cleanup = "isolated test input removed; run record and non-sensitive outputs retained"
)
}

main()
