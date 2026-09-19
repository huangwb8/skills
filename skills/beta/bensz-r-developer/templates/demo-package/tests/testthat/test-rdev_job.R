test_that("constructor enforces useful invariants", {
  expect_s3_class(new_rdev_job(iris, "iris"), "rdev_job")
  expect_error(new_rdev_job(data.frame(label = "x")), "numeric column")
  expect_error(new_rdev_job(iris, ""), "safe file stem")
  expect_error(new_rdev_job(iris, "../escape"), "safe file stem")

  broken <- new_rdev_job(iris, "iris")
  broken$artifacts <- NULL
  expect_error(validate_rdev_job(broken), "artifacts")
})

test_that("memory, output, and cache contracts are distinct", {
  output_dir <- file.path(tempdir(), paste0("output-", sample.int(1e7, 1L)))
  cache_dir <- file.path(tempdir(), paste0("cache-", sample.int(1e7, 1L)))
  job <- run_job(
    new_rdev_job(iris, "iris"),
    output.dir = output_dir,
    cache.dir = cache_dir,
    chunk.size = 40L
  )

  expect_s3_class(job, "rdev_job")
  expect_true(all(file.exists(job$artifacts$output)))
  expect_length(job$artifacts$output, 3L)
  expect_gt(length(list.files(cache_dir, pattern = "^chunk-.*\\.rds$")), 0L)
  expect_false(identical(normalizePath(output_dir), normalizePath(cache_dir)))
  expect_error(
    run_job(new_rdev_job(iris, "iris"), output.dir = output_dir),
    "Refusing to overwrite"
  )
})

test_that("arguments and directory boundaries fail clearly", {
  job <- new_rdev_job(iris, "iris")
  expect_error(run_job(job, chunk.size = Inf), "positive integer")
  expect_error(run_job(job, seed = NA_real_), "finite integer")

  parent <- tempfile("rdev-nested-")
  child <- file.path(parent, "cache")
  expect_error(
    run_job(job, output.dir = parent, cache.dir = child),
    "non-nested"
  )
})

test_that("a damaged cache entry is quarantined and rebuilt", {
  cache_dir <- tempfile("rdev-cache-")
  job <- new_rdev_job(iris, "iris")
  first <- run_job(job, cache.dir = cache_dir, chunk.size = 40L)
  cache_file <- list.files(
    cache_dir,
    pattern = "^chunk-.*\\.rds$",
    full.names = TRUE
  )[[1L]]
  writeLines("not an RDS file", cache_file)

  second <- run_job(job, cache.dir = cache_dir, chunk.size = 40L)
  expect_equal(second$result, first$result)
  expect_true(any(grepl("\\.corrupt-", list.files(cache_dir))))
})

test_that("preflight prevents partial user-facing output", {
  output_dir <- tempfile("rdev-output-")
  dir.create(output_dir)
  existing_job <- file.path(output_dir, "iris-job.rds")
  saveRDS("keep", existing_job)

  expect_error(
    run_job(new_rdev_job(iris, "iris"), output.dir = output_dir),
    "Refusing to overwrite"
  )
  expect_false(file.exists(file.path(output_dir, "iris-summary.csv")))
  expect_identical(readRDS(existing_job), "keep")
})

test_that("sequential and multisession execution agree", {
  skip_if_not_installed("future")
  old_plan <- future::plan()
  on.exit(future::plan(old_plan), add = TRUE)
  future::plan(future::multisession, workers = 2L)

  job <- new_rdev_job(iris, "iris")
  sequential <- run_job(job, parallel = FALSE, seed = 11L, chunk.size = 30L)
  future_result <- run_job(job, parallel = TRUE, seed = 11L, chunk.size = 30L)

  expect_equal(future_result$result, sequential$result)
})
