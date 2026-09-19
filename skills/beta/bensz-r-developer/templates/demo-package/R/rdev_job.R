.rdev_cache_schema <- 1L
.rdev_output_schema <- 1L

#' Construct an R development job
#'
#' @param data A non-empty data frame with at least one numeric column.
#' @param id A safe scalar file stem used in user-facing artifact names.
#'
#' @return An object of class `rdev_job`.
#' @export
new_rdev_job <- function(data, id = "job") {
  x <- structure(
    list(
      data = data,
      id = id,
      result = NULL,
      artifacts = list(output = character(), cache.dir = NULL)
    ),
    class = "rdev_job"
  )
  validate_rdev_job(x)
}

#' Validate an R development job
#'
#' @param x An object to validate.
#'
#' @return `x`, invisibly, or an error describing the broken invariant.
#' @export
validate_rdev_job <- function(x) {
  if (!inherits(x, "rdev_job")) {
    stop("`x` must inherit from class <rdev_job>.", call. = FALSE)
  }
  if (!is.data.frame(x$data) || nrow(x$data) < 1L) {
    stop("`data` must be a non-empty data frame.", call. = FALSE)
  }
  if (!any(vapply(x$data, is.numeric, logical(1)))) {
    stop("`data` must contain at least one numeric column.", call. = FALSE)
  }
  valid_id <- is.character(x$id) &&
    length(x$id) == 1L &&
    !is.na(x$id) &&
    grepl("^[A-Za-z0-9][A-Za-z0-9._-]*$", x$id)
  if (!valid_id) {
    stop(
      paste(
        "`id` must be a safe file stem containing only letters, numbers,",
        "dots, underscores, and hyphens."
      ),
      call. = FALSE
    )
  }
  if (!is.null(x$result)) {
    required <- c("chunk", "rows", "variable", "mean")
    if (!is.data.frame(x$result) || !all(required %in% names(x$result))) {
      stop("`result` must be NULL or a summary data frame.", call. = FALSE)
    }
  }
  artifact_fields <- c("output", "cache.dir")
  has_artifact_fields <- is.list(x$artifacts) &&
    all(artifact_fields %in% names(x$artifacts))
  if (!has_artifact_fields) {
    stop(
      "`artifacts` must contain `output` and `cache.dir` fields.",
      call. = FALSE
    )
  }
  non_null_cache_dir <- is.character(x$artifacts$cache.dir) &&
    length(x$artifacts$cache.dir) == 1L &&
    !is.na(x$artifacts$cache.dir) &&
    nzchar(x$artifacts$cache.dir)
  valid_cache_dir <- is.null(x$artifacts$cache.dir) || non_null_cache_dir
  valid_artifacts <- is.character(x$artifacts$output) &&
    valid_cache_dir
  if (!valid_artifacts) {
    stop(
      paste(
        "`artifacts` must contain character `output` paths and an",
        "optional `cache.dir`."
      ),
      call. = FALSE
    )
  }
  invisible(x)
}

#' @export
print.rdev_job <- function(x, ...) {
  cat("<rdev_job>", x$id, "\n")
  cat("Rows:", nrow(x$data), " Columns:", ncol(x$data), "\n")
  cat("Completed:", !is.null(x$result), "\n")
  invisible(x)
}

#' Run a development job
#'
#' @param x An object to execute.
#' @param ... Arguments passed to a class-specific method.
#'
#' @return The updated job object.
#' @export
run_job <- function(x, ...) {
  UseMethod("run_job")
}

#' Run an `rdev_job`
#'
#' Each chunk produces a cacheable numeric summary. The final summary, job, and
#' manifest are committed as one user-facing output set; chunk files are
#' rebuildable cache entries. Parallel execution respects the caller's active
#' future plan and does not change it.
#'
#' @param x An `rdev_job` object.
#' @param output.dir Optional directory for final artifacts. `NULL` keeps the
#'   result in memory only.
#' @param cache.dir Optional directory for rebuildable chunk caches.
#' @param overwrite Whether known final artifacts may be replaced.
#' @param parallel Whether to use `future.apply::future_lapply()`.
#' @param seed Integer seed used by future's reproducible RNG stream.
#' @param chunk.size Positive number of rows per chunk.
#' @param ... Reserved for future method extensions.
#'
#' @return The updated `rdev_job` with `result` and `artifacts` fields.
#' @export
run_job.rdev_job <- function(
    x,
    output.dir = NULL,
    cache.dir = NULL,
    overwrite = FALSE,
    parallel = FALSE,
    seed = 2026L,
    chunk.size = 500L,
    ...) {
  # Test
  if (FALSE) {
    job <- new_rdev_job(datasets::iris, id = "iris")
    output.dir <- tempfile("r-output-")
    cache.dir <- tempfile("r-cache-")
    parallel <- FALSE
    seed <- 2026L
    chunk.size <- 40L
    result <- run_job(
      job,
      output.dir = output.dir,
      cache.dir = cache.dir,
      parallel = parallel,
      seed = seed,
      chunk.size = chunk.size
    )
    print(result)

    parallel_result <- local({
      old_plan <- future::plan()
      on.exit(future::plan(old_plan), add = TRUE)
      workers <- max(1L, parallelly::availableCores(omit = 1L))
      future::plan(future::multisession, workers = workers)
      run_job(job, parallel = TRUE, seed = seed, chunk.size = chunk.size)
    })
    print(parallel_result)
  }

  validate_rdev_job(x)
  valid_chunk_size <- is.numeric(chunk.size) &&
    length(chunk.size) == 1L &&
    !is.na(chunk.size) &&
    is.finite(chunk.size) &&
    chunk.size >= 1 &&
    chunk.size <= .Machine$integer.max &&
    chunk.size == as.integer(chunk.size)
  if (!valid_chunk_size) {
    stop("`chunk.size` must be one positive integer.", call. = FALSE)
  }
  valid_seed <- is.numeric(seed) &&
    length(seed) == 1L &&
    !is.na(seed) &&
    is.finite(seed) &&
    seed >= -.Machine$integer.max &&
    seed <= .Machine$integer.max &&
    seed == as.integer(seed)
  if (!valid_seed) {
    stop("`seed` must be one finite integer.", call. = FALSE)
  }
  if (!is.logical(parallel) || length(parallel) != 1L || is.na(parallel)) {
    stop("`parallel` must be TRUE or FALSE.", call. = FALSE)
  }
  if (!is.logical(overwrite) || length(overwrite) != 1L || is.na(overwrite)) {
    stop("`overwrite` must be TRUE or FALSE.", call. = FALSE)
  }

  output.dir <- prepare_dir(output.dir, "output.dir")
  cache.dir <- prepare_dir(cache.dir, "cache.dir")
  output_in_cache <- path_is_within(output.dir, cache.dir)
  cache_in_output <- path_is_within(cache.dir, output.dir)
  nested_dirs <- !is.null(output.dir) &&
    !is.null(cache.dir) &&
    (output_in_cache || cache_in_output)
  if (nested_dirs) {
    stop(
      "`output.dir` and `cache.dir` must be separate, non-nested directories.",
      call. = FALSE
    )
  }

  rows <- seq_len(nrow(x$data))
  groups <- split(rows, ceiling(seq_along(rows) / as.integer(chunk.size)))
  numeric_names <- names(x$data)[vapply(x$data, is.numeric, logical(1))]
  cache_schema <- .rdev_cache_schema

  summarize_chunk <- function(group_id) {
    index <- groups[[group_id]]
    key <- digest::digest(
      list(
        cache_schema = cache_schema,
        group_id = group_id,
        data = x$data[index, , drop = FALSE],
        numeric_names = numeric_names
      ),
      algo = "xxhash64"
    )
    cache_path <- if (is.null(cache.dir)) {
      NULL
    } else {
      file.path(cache.dir, paste0("chunk-", key, ".rds"))
    }
    lock <- NULL
    if (!is.null(cache_path)) {
      lock <- filelock::lock(paste0(cache_path, ".lock"), timeout = 10000)
      if (is.null(lock)) {
        stop("Timed out while waiting for the cache lock.", call. = FALSE)
      }
      on.exit(filelock::unlock(lock), add = TRUE)
      cached <- read_cache_entry(
        cache_path,
        expected_key = key,
        schema_version = cache_schema
      )
      if (!is.null(cached)) {
        return(cached)
      }
    }

    values <- vapply(
      x$data[index, numeric_names, drop = FALSE],
      mean,
      numeric(1),
      na.rm = TRUE
    )
    result <- data.frame(
      chunk = key,
      rows = length(index),
      variable = names(values),
      mean = unname(values),
      row.names = NULL
    )
    if (!is.null(cache_path)) {
      entry <- list(
        schema_version = cache_schema,
        key = key,
        value = result
      )
      atomic_save_rds(entry, cache_path, overwrite = FALSE)
    }
    result
  }

  group_ids <- seq_along(groups)
  pieces <- if (parallel) {
    future.apply::future_lapply(
      group_ids,
      summarize_chunk,
      future.seed = as.integer(seed)
    )
  } else {
    lapply(group_ids, summarize_chunk)
  }
  summary <- do.call(rbind, pieces)
  rownames(summary) <- NULL

  artifacts <- list(output = character(), cache.dir = cache.dir)
  if (!is.null(output.dir)) {
    targets <- c(
      summary = file.path(output.dir, paste0(x$id, "-summary.csv")),
      job = file.path(output.dir, paste0(x$id, "-job.rds")),
      manifest = file.path(output.dir, paste0(x$id, "-manifest.csv"))
    )
    assert_output_targets(targets, overwrite = overwrite)
    completed <- x
    completed$result <- summary
    completed$artifacts <- list(output = unname(targets), cache.dir = cache.dir)
    manifest <- data.frame(
      path = basename(unname(targets)),
      type = c("summary", "job", "manifest"),
      input_hash = digest::digest(x$data, algo = "xxhash64"),
      seed = as.integer(seed),
      format_version = .rdev_output_schema,
      generated_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
      stringsAsFactors = FALSE
    )
    staged <- c(
      summary = stage_csv(summary, output.dir),
      job = stage_rds(completed, output.dir),
      manifest = stage_csv(manifest, output.dir)
    )
    commit_staged_files(staged, targets, overwrite = overwrite)
    artifacts$output <- unname(targets)
  }

  x$result <- summary
  x$artifacts <- artifacts
  validate_rdev_job(x)
  x
}

prepare_dir <- function(path, arg) {
  if (is.null(path)) {
    return(NULL)
  }
  valid_path <- is.character(path) &&
    length(path) == 1L &&
    !is.na(path) &&
    nzchar(path)
  if (!valid_path) {
    stop("`", arg, "` must be NULL or one non-empty path.", call. = FALSE)
  }
  dir.create(path, recursive = TRUE, showWarnings = FALSE)
  normalizePath(path, winslash = "/", mustWork = TRUE)
}

path_is_within <- function(path, root) {
  if (is.null(path) || is.null(root)) {
    return(FALSE)
  }
  path <- sub("/+$", "", path)
  root <- sub("/+$", "", root)
  identical(path, root) || startsWith(path, paste0(root, "/"))
}

read_cache_entry <- function(path, expected_key, schema_version) {
  if (!file.exists(path)) {
    return(NULL)
  }
  tryCatch(
    {
      entry <- readRDS(path)
      valid <- is.list(entry) &&
        identical(entry$schema_version, schema_version) &&
        identical(entry$key, expected_key) &&
        is.data.frame(entry$value) &&
        all(c("chunk", "rows", "variable", "mean") %in% names(entry$value))
      if (!valid) {
        stop("Cache schema mismatch.")
      }
      entry$value
    },
    error = function(error) {
      quarantine <- paste0(
        path,
        ".corrupt-",
        format(Sys.time(), "%Y%m%d%H%M%S"),
        "-",
        Sys.getpid()
      )
      if (!file.rename(path, quarantine)) {
        stop("Could not quarantine an unreadable cache entry.", call. = FALSE)
      }
      NULL
    }
  )
}

atomic_save_rds <- function(object, path, overwrite) {
  if (file.exists(path) && !overwrite) {
    stop("Refusing to overwrite existing file: ", path, call. = FALSE)
  }
  temp <- tempfile(pattern = ".tmp-", tmpdir = dirname(path))
  on.exit(unlink(temp, force = TRUE), add = TRUE)
  saveRDS(object, temp)
  replace_file(temp, path, overwrite)
}

stage_csv <- function(object, directory) {
  path <- tempfile(pattern = ".stage-", tmpdir = directory, fileext = ".csv")
  utils::write.csv(object, path, row.names = FALSE)
  path
}

stage_rds <- function(object, directory) {
  path <- tempfile(pattern = ".stage-", tmpdir = directory, fileext = ".rds")
  saveRDS(object, path)
  path
}

assert_output_targets <- function(paths, overwrite) {
  existing <- paths[file.exists(paths)]
  if (length(existing) > 0L && !overwrite) {
    stop(
      "Refusing to overwrite existing file(s): ",
      paste(existing, collapse = ", "),
      call. = FALSE
    )
  }
  invisible(paths)
}

commit_staged_files <- function(staged, targets, overwrite) {
  if (!identical(names(staged), names(targets)) || length(staged) == 0L) {
    stop(
      "Staged files and targets must have the same non-empty names.",
      call. = FALSE
    )
  }
  assert_output_targets(targets, overwrite = overwrite)
  backups <- rep(NA_character_, length(targets))
  committed <- rep(FALSE, length(targets))
  on.exit(unlink(staged[file.exists(staged)], force = TRUE), add = TRUE)

  tryCatch(
    {
      for (i in seq_along(targets)) {
        if (file.exists(targets[[i]])) {
          backups[[i]] <- tempfile(
            pattern = ".backup-",
            tmpdir = dirname(targets[[i]])
          )
          if (!file.rename(targets[[i]], backups[[i]])) {
            stop("Could not stage an existing output for replacement.")
          }
        }
      }
      for (i in seq_along(targets)) {
        if (!file.rename(staged[[i]], targets[[i]])) {
          stop("Could not commit staged output: ", targets[[i]])
        }
        committed[[i]] <- TRUE
      }
    },
    error = function(error) {
      unlink(targets[committed], force = TRUE)
      for (i in seq_along(backups)) {
        if (!is.na(backups[[i]]) && file.exists(backups[[i]])) {
          file.rename(backups[[i]], targets[[i]])
        }
      }
      stop(conditionMessage(error), call. = FALSE)
    }
  )
  unlink(backups[!is.na(backups)], force = TRUE)
  invisible(unname(targets))
}

replace_file <- function(from, to, overwrite) {
  if (file.exists(to) && overwrite && unlink(to) != 0L) {
    stop("Could not replace existing file: ", to, call. = FALSE)
  }
  if (!file.rename(from, to)) {
    stop("Could not atomically move temporary file to: ", to, call. = FALSE)
  }
  invisible(to)
}
