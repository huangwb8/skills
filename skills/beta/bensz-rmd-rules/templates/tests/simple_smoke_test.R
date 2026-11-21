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
  on.exit(unlink(context$input_dir, recursive = TRUE), add = TRUE)
  assertion_script <- file.path("scripts", "tests", "assert_results.R")
  if (!file.exists(assertion_script) || dir.exists(assertion_script)) {
    stop("Add scripts/tests/assert_results.R to verify actual deliverables and scientific invariants.")
  }
  test_input <- bensz_test_prepare_input(context)
  assert_outputs <- function() {
    sys.source(assertion_script, envir = environment())
  }
  first_log <- bensz_test_run_entry(context)
  assert_outputs()
  # Discard only generated outputs of this isolated run, then rebuild in a second
  # clean process. Both R and Rmd require actual file and science assertions.
  bensz_test_remove_outputs(context)
  second_log <- bensz_test_run_entry(context)
  assert_outputs()
  # Add project-specific result assertions here, and input-change/relocation cases
  # from references/rebuild_contract.md. Do not promote NOT_RUN to PASS by editing
  # a label without executing those cases.
  stopifnot(unlink(context$input_dir, recursive = TRUE) == 0L, !dir.exists(context$input_dir))
  bensz_test_finish(
    context,
    assertions = c("test input prepared", "formal entry executed twice in clean processes", "project assertions passed for both runs", "isolated outputs regenerated"),
    lightweight_execution = "PASS",
    attempts = paste0("Rscript --vanilla ", sub("\\.log$", ".R", c(first_log, second_log)),
                      "; exit_status=0; failure_category=none; fix=none; project assertions passed"),
    rebuild_scenarios = c(cold_rebuild = "PASS", missing_delivery = "NOT_RUN",
                          input_content_change = "NOT_RUN", relocated_project = "NOT_RUN"),
    cleanup = "isolated test input removed; run record and non-sensitive outputs retained"
  )
}

main()
