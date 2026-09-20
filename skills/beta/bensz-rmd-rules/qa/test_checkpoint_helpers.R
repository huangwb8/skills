args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) != 1L) stop("Run this test with Rscript.")
script_path <- normalizePath(sub("^--file=", "", file_arg), winslash = "/", mustWork = TRUE)
skill_root <- dirname(dirname(script_path))
helper <- file.path(skill_root, "templates", "checkpoint_helpers.R")

repo_root <- normalizePath(file.path(skill_root, "..", "..", ".."), winslash = "/", mustWork = TRUE)
test_parent <- Sys.getenv("BENSZ_TEST_TMP", unset = file.path(repo_root, "tmp"))
dir.create(test_parent, recursive = TRUE, showWarnings = FALSE)
test_root <- tempfile("bensz-rmd-checkpoint-", tmpdir = test_parent)
dir.create(test_root)
test_root <- normalizePath(test_root, winslash = "/", mustWork = TRUE)
on.exit(unlink(test_root, recursive = TRUE, force = TRUE), add = TRUE)

old_wd <- setwd(test_root)
on.exit(setwd(old_wd), add = TRUE)
dir.create("raw")
writeLines(c("x", "1"), file.path("raw", "input.tsv"))
writeLines("x <- 1", "01.00.00. 数据整理.R")
source(helper)

# 不存在路径中的 .. 不能绕过 products/ 边界，workflow 也不能退化为路径段。
traversal_error <- tryCatch({
  .bensz_assert_product_dir(file.path(test_root, "products", "x", "..", "..", "raw", "evil"))
  FALSE
}, error = function(e) TRUE)
stopifnot(traversal_error)
workflow_error <- tryCatch({
  bensz_product_dir("..", "01.00.00. escape")
  FALSE
}, error = function(e) TRUE)
stopifnot(workflow_error)
for (bad_stem in c("01.00.00. CON", "01.00.00. trailing.", "01.00.00. bad:name")) {
  portable_name_error <- tryCatch({
    bensz_product_dir("main", bad_stem)
    FALSE
  }, error = function(e) TRUE)
  stopifnot(portable_name_error)
}
stopifnot(!file.exists(file.path(test_root, "raw", "evil")))

# 产品目录只通过一个项目设置覆盖，且仍受项目边界与保留目录保护。
options(bensz.products_dir = file.path("derived", "products"))
custom_product_dir <- bensz_product_dir("main", "01.00.00. 数据整理")
stopifnot(identical(
  custom_product_dir,
  normalizePath(file.path(test_root, "derived", "products", "main", "01.00.00. 数据整理"), winslash = "/", mustWork = FALSE)
))
for (unsafe_products_dir in c("../outside", "raw/products", "tmp/products", "/outside")) {
  options(bensz.products_dir = unsafe_products_dir)
  unsafe_error <- tryCatch({
    bensz_product_dir("main", "01.00.00. 数据整理")
    FALSE
  }, error = function(e) TRUE)
  stopifnot(unsafe_error)
}
options(bensz.products_dir = "products")

# 测试期 products 覆盖只能精确绑定到声明的唯一 run root。
Sys.setenv(BENSZ_TEST_RUN_ROOT = file.path("tmp", "tests", "checkpoint-test"))
options(bensz.products_dir = file.path("tmp", "tests", "checkpoint-test", "products"))
isolated_product_dir <- bensz_product_dir("main", "01.00.00. 数据整理")
stopifnot(grepl("/tmp/tests/checkpoint-test/products/main/", isolated_product_dir, fixed = TRUE))
options(bensz.products_dir = file.path("tmp", "tests", "other-run", "products"))
mismatched_test_root_error <- tryCatch({
  bensz_product_dir("main", "01.00.00. 数据整理")
  FALSE
}, error = function(e) TRUE)
stopifnot(mismatched_test_root_error)
Sys.unsetenv("BENSZ_TEST_RUN_ROOT")
options(bensz.products_dir = "products")

identity <- bensz_cache_identity(
  input_files = file.path("raw", "input.tsv"),
  parameters = list(alpha = 1),
  code_files = "01.00.00. 数据整理.R",
  upstream_identities = "upstream-a"
)
stopifnot(identity != bensz_cache_identity(
  input_files = file.path("raw", "input.tsv"),
  parameters = list(alpha = 2),
  code_files = "01.00.00. 数据整理.R",
  upstream_identities = "upstream-a"
))
stopifnot(identity != bensz_cache_identity(
  input_files = file.path("raw", "input.tsv"),
  parameters = list(alpha = 1),
  code_files = "01.00.00. 数据整理.R",
  upstream_identities = "upstream-b"
))
writeLines("x <- 2", "01.00.00. 数据整理.R")
stopifnot(identity != bensz_cache_identity(
  input_files = file.path("raw", "input.tsv"),
  parameters = list(alpha = 1),
  code_files = "01.00.00. 数据整理.R",
  upstream_identities = "upstream-a"
))
writeLines("x <- 1", "01.00.00. 数据整理.R")

product_dir <- bensz_product_dir("main", "01.00.00. 数据整理")
fresh_status <- bensz_checkpoint_status(product_dir, identity)
stopifnot(!isTRUE(fresh_status$valid), identical(fresh_status$reason, "missing SUCCESS"))
bensz_write_checkpoint(
  object = data.frame(x = 1:3),
  product_dir = product_dir,
  unit_id = "01.00.00",
  cache_identity = identity,
  summary_lines = c("# Summary", "- rows: 3"),
  preview = data.frame(x = 1:2)
)
stopifnot(isTRUE(bensz_checkpoint_status(product_dir, identity)$valid))
product_identity_1 <- bensz_product_identity(product_dir, identity)

versioned_dir <- bensz_product_dir("main", "01.50.00. 版本契约")
versioned_identity <- bensz_cache_identity(
  parameters = list(version = 2L),
  code_files = "01.00.00. 数据整理.R",
  output_contract_version = 2L
)
versioned_status <- bensz_write_checkpoint(
  object = data.frame(x = 1),
  product_dir = versioned_dir,
  unit_id = "01.50.00",
  cache_identity = versioned_identity,
  summary_lines = c("# Summary", "- rows: 1"),
  output_contract_version = 2L
)
stopifnot(identical(versioned_status$metadata$output_contract_version, 2L))

# 相同静态 cache identity 下强制重算出不同内容时，实际 product identity 必须变化，
# 以便下游自动失效。
bensz_write_checkpoint(
  object = data.frame(x = 4:6),
  product_dir = product_dir,
  unit_id = "01.00.00",
  cache_identity = identity,
  summary_lines = c("# Summary", "- rows: 3")
)
product_identity_2 <- bensz_product_identity(product_dir, identity)
stopifnot(product_identity_1 != product_identity_2)

unlink(file.path(product_dir, "main.rds"))
missing_output_status <- bensz_checkpoint_status(product_dir, identity)
stopifnot(
  !isTRUE(missing_output_status$valid),
  identical(missing_output_status$reason, "missing output main.rds")
)
bensz_write_checkpoint(
  object = data.frame(x = 4:6),
  product_dir = product_dir,
  unit_id = "01.00.00",
  cache_identity = identity,
  summary_lines = c("# Summary", "- rows: 3")
)

unlink(file.path(product_dir, "SUCCESS"))
stopifnot(!isTRUE(bensz_checkpoint_status(product_dir, identity)$valid))
bensz_write_checkpoint(
  object = data.frame(x = 1:3),
  product_dir = product_dir,
  unit_id = "01.00.00",
  cache_identity = identity,
  summary_lines = c("# Summary", "- rows: 3")
)
writeLines("damaged", file.path(product_dir, "main.rds"))
stopifnot(!isTRUE(bensz_checkpoint_status(product_dir, identity)$valid))

# 标记内容与 symlink 都不能被直接执行的 R helper 误判为命中。
bensz_write_checkpoint(
  object = data.frame(x = 1:3),
  product_dir = product_dir,
  unit_id = "01.00.00",
  cache_identity = identity,
  summary_lines = c("# Summary", "- rows: 3")
)
writeLines("wrong", file.path(product_dir, "SUCCESS"))
stopifnot(!isTRUE(bensz_checkpoint_status(product_dir, identity)$valid))
bensz_write_checkpoint(
  object = data.frame(x = 1:3),
  product_dir = product_dir,
  unit_id = "01.00.00",
  cache_identity = identity,
  summary_lines = c("# Summary", "- rows: 3")
)
outside_object <- file.path(test_root, "outside.rds")
saveRDS(data.frame(x = 9), outside_object)
unlink(file.path(product_dir, "main.rds"))
if (isTRUE(file.symlink(outside_object, file.path(product_dir, "main.rds")))) {
  stopifnot(!isTRUE(bensz_checkpoint_status(product_dir, identity)$valid))
}

valid_status <- list(valid = TRUE)
invalid_status <- list(valid = FALSE)
Sys.setenv(BENSZ_FORCE_STEP = "01.00.00", BENSZ_RESUME_FROM = "")
stopifnot(identical(bensz_run_decision("01.00.00", valid_status), "run"))
Sys.setenv(BENSZ_FORCE_STEP = "", BENSZ_RESUME_FROM = "02.00.00")
resume_error <- tryCatch({
  bensz_run_decision("01.00.00", invalid_status)
  FALSE
}, error = function(e) TRUE)
stopifnot(resume_error)
Sys.unsetenv(c("BENSZ_FORCE_STEP", "BENSZ_RESUME_FROM"))

cat("[PASS] checkpoint identity, completion, damage, force and resume tests\n")
