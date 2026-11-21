read_pairs <- function(file) {
  values <- read.csv(file)
  stopifnot(all(c("unit", "before", "after") %in% names(values)), !anyNA(values$unit),
            !anyDuplicated(values$unit), is.numeric(values$before), is.numeric(values$after))
  data.frame(unit = values$unit, change = values$after - values$before)
}

estimate_change <- function(data, parameter_file, environment_lock) {
  stopifnot(file.exists(environment_lock))
  settings <- new.env(parent = baseenv())
  sys.source(parameter_file, envir = settings)
  observed <- data$change[is.finite(data$change)]
  if (length(observed) < 2L) stop("At least two complete pairs are required.")
  fit <- stats::t.test(observed, conf.level = settings$confidence)
  list(n_total = nrow(data), n = length(observed), estimate = unname(fit$estimate),
       lower = fit$conf.int[[1L]], upper = fit$conf.int[[2L]], confidence = settings$confidence)
}
