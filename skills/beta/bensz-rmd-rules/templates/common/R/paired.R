read_pairs <- function(file) {
  # Reject inconsistent widths before read.csv can interpret an extra field as row names.
  fields <- utils::count.fields(file, sep = ",", quote = '"', comment.char = "")
  fields <- fields[!is.na(fields)]
  if (!length(fields) || any(fields != fields[[1L]])) {
    stop("Expected every CSV record to have the same number of fields as the header.", call. = FALSE)
  }
  values <- read.csv(file, colClasses = "character", check.names = FALSE, fill = FALSE)
  required <- c("unit", "before", "after")
  if (!all(required %in% names(values)) || anyDuplicated(names(values))) {
    stop("Expected unique CSV columns including unit, before and after.", call. = FALSE)
  }
  unit <- trimws(values$unit)
  if (anyNA(unit) || any(!nzchar(unit)) || anyDuplicated(unit)) {
    stop("Expected one row per nonempty, unique unit ID.", call. = FALSE)
  }
  measurement <- function(column) {
    input <- trimws(values[[column]])
    number <- suppressWarnings(as.numeric(input))
    if (any(is.na(number) & !is.nan(number) & !is.na(input) & nzchar(input))) {
      stop("Expected numeric measurements or missing values in ", column, ".", call. = FALSE)
    }
    number
  }
  data.frame(unit = unit, change = measurement("after") - measurement("before"))
}

read_confidence <- function(parameter_file) {
  settings <- new.env(parent = baseenv())
  sys.source(parameter_file, envir = settings)
  level <- settings$confidence
  if (!is.numeric(level) || length(level) != 1L || !is.finite(level) || level <= 0 || level >= 1) {
    stop("Set confidence in 00.Environments/analysis.R to a number between 0 and 1.", call. = FALSE)
  }
  level
}

paired_sample <- function(data) {
  changes <- data$change[is.finite(data$change)]
  directions <- c(up = sum(changes > 0), level = sum(changes == 0), down = sum(changes < 0))
  list(changes = changes, n = length(changes), n_total = nrow(data), directions = directions)
}

estimate_change <- function(sample, confidence) {
  observed <- sample$changes
  n <- sample$n
  estimate <- if (n) mean(observed) else NA_real_
  bounds <- c(NA_real_, NA_real_)
  interval_status <- if (!n) "no_pairs" else if (n == 1L) "one_pair" else "ok"
  if (interval_status == "ok") {
    if (all(observed == observed[[1L]])) {
      interval_status <- "no_variation"
    } else {
      spread <- stats::sd(observed)
      half_width <- stats::qt((1 - confidence) / 2, df = n - 1L, lower.tail = FALSE) *
        (spread / sqrt(n))
      interval <- estimate + c(-half_width, half_width)
      if (all(is.finite(interval)) && interval[[1L]] < interval[[2L]]) {
        bounds <- interval
      } else {
        interval_status <- "numeric_limit"
      }
    }
  }
  list(n_total = sample$n_total, n = n, estimate = estimate, lower = bounds[[1L]],
       upper = bounds[[2L]], confidence = confidence, interval_status = interval_status)
}

summarize_leave_one_out <- function(sample) {
  observed <- sample$changes
  limits <- c(NA_real_, NA_real_)
  if (length(observed) < 2L) {
    return(list(n_checks = 0L, limits = limits, status = "too_few"))
  }
  omitted_means <- vapply(seq_along(observed), function(i) mean(observed[-i]), numeric(1))
  if (!all(is.finite(omitted_means))) {
    return(list(n_checks = length(omitted_means), limits = limits, status = "numeric_limit"))
  }
  list(n_checks = length(omitted_means), limits = range(omitted_means), status = "ok")
}
