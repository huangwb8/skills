# Copy to scripts/tests/test_data.R and replace grouping/edge rules with project facts.
source_path <- Sys.getenv("BENSZ_SOURCE_DATA", unset = file.path("raw", "input.csv"))
if (!file.exists(source_path)) stop("Authorized source data is missing: ", source_path)
full_data <- utils::read.csv(source_path, check.names = FALSE)
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

test_root <- Sys.getenv("BENSZ_TEST_RUN_ROOT", unset = file.path("tmp", "tests", "manual"))
dir.create(test_root, recursive = TRUE, showWarnings = FALSE)
test_input <- file.path(test_root, "input", "project_subset.csv")
dir.create(dirname(test_input), recursive = TRUE, showWarnings = FALSE)
utils::write.csv(subset_data, test_input, row.names = FALSE, na = "")
