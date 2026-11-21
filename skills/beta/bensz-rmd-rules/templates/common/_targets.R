targets::tar_source("R")
list(
  targets::tar_target(input_file, "raw/measurements.csv", format = "file"),
  targets::tar_target(parameter_file, "00.Environments/analysis.R", format = "file"),
  targets::tar_target(environment_lock, "00.Environments/renv.lock", format = "file"),
  targets::tar_target(paired_changes, read_pairs(input_file)),
  targets::tar_target(analysis_sample, paired_sample(paired_changes)),
  targets::tar_target(paired_estimate, {
    stopifnot(file.exists(environment_lock))
    estimate_change(analysis_sample, read_confidence(parameter_file))
  }),
  targets::tar_target(paired_robustness, {
    stopifnot(file.exists(environment_lock))
    summarize_leave_one_out(analysis_sample)
  })
)
