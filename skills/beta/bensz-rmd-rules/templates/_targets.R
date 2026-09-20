# targets entrypoint for a new complex bensz-rmd-rules project.
# Keep dependency orchestration here; product writing and SUCCESS verification stay
# in the target functions/helpers so every product follows one contract.

if (!requireNamespace("targets", quietly = TRUE)) {
  stop("This complex project requires the targets package from renv.lock.")
}
source("renv/activate.R")
source("00.Environment.R")

library(targets)

tar_option_set(
  packages = character(),
  format = "rds",
  store = "_targets"
)

list(
  # Replace this placeholder with the smallest real analysis unit. If a new
  # project does not need dependency/invalidation/recovery semantics, use simple
  # mode and do not create this file.
  tar_target(
    analysis_product,
    stop("Define analysis_product in _targets.R before running tar_make().")
  )
)
