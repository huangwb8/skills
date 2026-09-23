# targets-first pipeline entrypoint for bensz-rmd-rules.
# _targets.R is the only execution graph. Functions live in R/ and reports
# consume target values; do not add SUCCESS, identity hashes, or a second runner.
# Human readability: keep targets grouped under stage comment blocks, give
# every target a semantic name, and attach a tar_manifest() snapshot to the
# delivery summary as the human-readable pipeline map.

source("renv/activate.R")
if (!requireNamespace("targets", quietly = TRUE)) {
  stop("This pipeline requires the targets package from renv.lock.")
}

targets::tar_source("R")

targets::tar_option_set(
  packages = character(),
  format = "rds"
)

list(
  # ---- Stage: inputs (read-only raw data tracked as file targets) ----
  targets::tar_target(
    analysis_input,
    file.path("raw", "input.tsv"),
    format = "file"
  ),
  # ---- Stage: computation (functions in R/, semantic target names) ----
  targets::tar_target(
    prepared_data,
    prepare_data(analysis_input)
  ),
  targets::tar_target(
    analysis_results,
    analyze_data(prepared_data)
  ),
  # ---- Stage: delivery (documentation only) ----
  # Export only a scientific object that downstream users must review/reuse:
  # targets::tar_target(scientific_product, write_product(analysis_results), format = "file"),
  # Render outside the graph with an Rmd that calls tar_read("analysis_results"),
  # or use tarchetypes::tar_render() only when it is locked in renv.lock.
  targets::tar_target(
    pipeline_contract,
    list(
      state = "targets-managed",
      report_consumer = "Rmd uses tar_read/tar_load",
      store_contract = "caller supplies _targets or isolated tmp/tests/<run-id>/_targets"
    )
  )
)
