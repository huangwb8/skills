# Copy to scripts/tests/test_data.R and adapt the schema to the formal input.
if (!identical(Sys.getenv("BENSZ_TEST_STYLE"), "synthetic_fixture")) {
  stop("This test_data.R requires test style synthetic_fixture")
}
set.seed(20260920L)
test_root <- Sys.getenv("BENSZ_TEST_RUN_ROOT")
if (!nzchar(test_root)) stop("Run the smoke entry to create an isolated test root")

fixture <- data.frame(
  sample_id = sprintf("S%02d", 1:8),
  group = rep(c("control", "treated"), each = 4L),
  value = c(1.0, 1.3, NA, 1.8, 2.0, 2.4, 8.0, 2.8),
  stringsAsFactors = FALSE
)
stopifnot(!anyDuplicated(fixture$sample_id))
stopifnot(setequal(unique(fixture$group), c("control", "treated")))
stopifnot(anyNA(fixture$value), max(fixture$value, na.rm = TRUE) >= 8)

test_input <- file.path(test_root, "input", "synthetic_fixture.tsv")
utils::write.table(fixture, test_input, sep = "\t", row.names = FALSE, quote = TRUE, na = "", fileEncoding = "UTF-8")
