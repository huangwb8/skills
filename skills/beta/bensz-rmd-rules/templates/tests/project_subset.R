# Copy to scripts/tests/test_data.R and replace grouping/edge rules with project facts.
if (!identical(Sys.getenv("BENSZ_TEST_STYLE"), "project_subset")) {
  stop("This test_data.R requires an explicitly authorized project_subset run")
}
source_path <- Sys.getenv("BENSZ_SOURCE_DATA")
test_root <- Sys.getenv("BENSZ_TEST_RUN_ROOT")
if (!nzchar(test_root)) stop("Run the smoke entry to create an isolated test root")
if (!nzchar(source_path) || !file.exists(source_path) || dir.exists(source_path)) {
  stop("Set BENSZ_SOURCE_DATA to an authorized project file")
}
root <- paste0(normalizePath(getwd(), winslash = "/", mustWork = TRUE), "/")
source_path <- normalizePath(source_path, winslash = "/", mustWork = TRUE)
if (!startsWith(source_path, root)) stop("Authorized source data must be inside the project")
full_data <- utils::read.delim(source_path, check.names = FALSE, fileEncoding = "UTF-8")
required <- c("sample_id", "group", "value")
if (!all(required %in% names(full_data))) stop("Project subset template requires: ", paste(required, collapse = ", "))

# Deterministic representative rule: smallest stable ID per group, plus rows with
# missing values and the largest finite value. Adapt when these are not the real boundaries.
ordered <- full_data[order(full_data$group, full_data$sample_id), , drop = FALSE]
by_group <- !duplicated(ordered$group)
edge <- is.na(ordered$value)
finite <- which(is.finite(ordered$value))
if (length(finite)) edge[finite[[which.max(ordered$value[finite])]]] <- TRUE
subset_data <- ordered[by_group | edge, , drop = FALSE]
stopifnot(length(unique(subset_data$group)) == length(unique(full_data$group)))

test_input <- file.path(test_root, "input", "project_subset.tsv")
utils::write.table(subset_data, test_input, sep = "\t", row.names = FALSE, quote = TRUE, na = "", fileEncoding = "UTF-8")
