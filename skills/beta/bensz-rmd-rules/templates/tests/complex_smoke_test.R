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
bensz_test_run_entry(context) # internally tar_make(store = context$targets_store)
manifest <- targets::tar_meta(store = context$targets_store, fields = c(name, error))
stopifnot(nrow(manifest) > 0L, !any(!is.na(manifest$error) & nzchar(manifest$error)))
# Adapt these target names and scientific assertions to the actual project.
baseline <- targets::tar_read(analysis_results, store = context$targets_store)
product <- targets::tar_read(scientific_product, store = context$targets_store)
stopifnot(identical(readRDS(product), baseline))
times <- targets::tar_meta(store = context$targets_store, fields = c(name, time))
bensz_test_run_entry(context)
times_after <- targets::tar_meta(store = context$targets_store, fields = c(name, time))
stopifnot(identical(times[order(times$name), ], times_after[order(times_after$name), ]))

# Missing file with valid compute cache: restore the file without recomputing
# analysis_results. Never remove a path returned by an unverified user target.
expected_product <- file.path(context$products_dir, "analysis_results.rds")
stopifnot(identical(normalizePath(product), normalizePath(expected_product)))
unlink(expected_product)
bensz_test_run_entry(context)
stopifnot(identical(readRDS(expected_product), baseline))
new_times <- targets::tar_meta(store = context$targets_store, fields = c(name, time))
stopifnot(identical(times$time[times$name == "analysis_results"],
                    new_times$time[new_times$name == "analysis_results"]))

# No previous store or products: rebuild the same graph in a fresh process.
bensz_test_remove_outputs(context)
bensz_test_run_entry(context)
stopifnot(isTRUE(all.equal(baseline, targets::tar_read(analysis_results, store = context$targets_store))))
stopifnot(isTRUE(all.equal(baseline, readRDS(expected_product))))
# Still add real downstream interruption, input-content-change and relocation
# cases plus scientific assertions. An unchanged rerun alone is not interruption
# evidence; these unexecuted cases are not silently marked PASS.
unlink(test_input)
bensz_test_finish(
  context,
  assertions = c("target graph executed in clean processes", "unchanged graph reused targets", "missing product regenerated without recomputing analysis_results", "cold rebuild reproduced result", "formal paths unchanged"),
  rebuild_scenarios = c(cold_rebuild = "PASS", missing_delivery = "PASS",
                        input_content_change = "NOT_RUN", relocated_project = "NOT_RUN"),
  cleanup = "isolated project subset removed; run record and non-sensitive outputs retained"
)
}

main()
