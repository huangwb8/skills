# Copy to scripts/tests/test_data.R and adapt the schema to the formal input.
set.seed(20260920L)
test_root <- Sys.getenv("BENSZ_TEST_RUN_ROOT", unset = file.path("tmp", "tests", "manual"))
dir.create(test_root, recursive = TRUE, showWarnings = FALSE)

fixture <- data.frame(
  sample_id = sprintf("S%02d", 1:8),
  group = rep(c("control", "treated"), each = 4L),
  value = c(1.0, 1.3, NA, 1.8, 2.0, 2.4, 8.0, 2.8),
  stringsAsFactors = FALSE
)
stopifnot(!anyDuplicated(fixture$sample_id))
stopifnot(setequal(unique(fixture$group), c("control", "treated")))
stopifnot(anyNA(fixture$value), max(fixture$value, na.rm = TRUE) >= 8)

test_input <- file.path(test_root, "input", "synthetic_fixture.csv")
dir.create(dirname(test_input), recursive = TRUE, showWarnings = FALSE)
utils::write.csv(fixture, test_input, row.names = FALSE, na = "")
