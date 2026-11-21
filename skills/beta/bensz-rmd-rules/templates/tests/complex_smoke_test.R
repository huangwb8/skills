# Copy to scripts/tests/smoke_test.R. The formal _targets.R reads the normal
# BENSZ_ANALYSIS_INPUT/BENSZ_PRODUCTS_DIR configuration; it has no test-mode branch.
main <- function() {
  if (!file.exists(file.path("renv", "activate.R"))) stop("Missing renv/activate.R")
  source(file.path("renv", "activate.R"), local = TRUE)
  source(file.path("scripts", "tests", "test_harness.R"), local = TRUE)
  if (!requireNamespace("targets", quietly = TRUE)) stop("Package 'targets' is required.")
  test_style <- Sys.getenv("BENSZ_TEST_STYLE", unset = "synthetic_fixture")
  context <- bensz_test_begin(
    "new", "complex", test_style, "_targets.R",
    report_entrypoint = Sys.getenv("BENSZ_REPORT_ENTRY", unset = "")
  )
  on.exit(bensz_test_restore_environment(context), add = TRUE)
  on.exit(unlink(context$input_dir, recursive = TRUE), add = TRUE)
  test_input <- bensz_test_prepare_input(context)

  first_log <- bensz_test_run_entry(context)
  manifest <- targets::tar_meta(store = context$targets_store, fields = c(name, error))
  stopifnot(nrow(manifest) > 0L, !any(!is.na(manifest$error) & nzchar(manifest$error)))
  # Adapt these target names and scientific assertions to the actual project.
  baseline <- targets::tar_read(analysis_results, store = context$targets_store)
  product <- targets::tar_read(scientific_product, store = context$targets_store)
  stopifnot(identical(readRDS(product), baseline))
  times <- targets::tar_meta(store = context$targets_store, fields = c(name, time))
  reuse_log <- bensz_test_run_entry(context)
  times_after <- targets::tar_meta(store = context$targets_store, fields = c(name, time))
  stopifnot(identical(times[order(times$name), ], times_after[order(times_after$name), ]))

  # Missing file with valid compute cache: restore the file without recomputing
  # analysis_results. Never remove a path returned by an unverified user target.
  expected_product <- file.path(context$products_dir, "analysis_results.rds")
  stopifnot(identical(normalizePath(product), normalizePath(expected_product)))
  unlink(expected_product)
  repair_log <- bensz_test_run_entry(context)
  stopifnot(identical(readRDS(expected_product), baseline))
  new_times <- targets::tar_meta(store = context$targets_store, fields = c(name, time))
  stopifnot(identical(times$time[times$name == "analysis_results"],
                      new_times$time[new_times$name == "analysis_results"]))

  # No previous store or products: rebuild the same graph in a fresh process.
  bensz_test_remove_outputs(context)
  rebuild_log <- bensz_test_run_entry(context)
  stopifnot(isTRUE(all.equal(baseline, targets::tar_read(analysis_results, store = context$targets_store))))
  stopifnot(isTRUE(all.equal(baseline, readRDS(expected_product))))
  # Still add real downstream interruption, input-content-change and relocation
  # cases plus scientific assertions. An unchanged rerun alone is not interruption
  # evidence; these unexecuted cases are not silently marked PASS.
  stopifnot(unlink(context$input_dir, recursive = TRUE) == 0L, !dir.exists(context$input_dir))
  bensz_test_finish(
    context,
    assertions = c("target graph executed in clean processes", "unchanged graph reused targets", "missing product regenerated without recomputing analysis_results", "cold rebuild reproduced result",
                   if (nzchar(context$report_entrypoint)) "configured report rendered from isolated store"),
    lightweight_execution = "PASS",
    attempts = paste0("Rscript --vanilla ", sub("\\.log$", ".R", c(first_log, reuse_log, repair_log, rebuild_log)),
                      "; exit_status=0; failure_category=none; fix=none; see assertions"),
    rebuild_scenarios = c(cold_rebuild = "PASS", missing_delivery = "PASS",
                          input_content_change = "NOT_RUN", relocated_project = "NOT_RUN"),
    cleanup = "isolated test input removed; run record and non-sensitive outputs retained"
  )
}

main()
