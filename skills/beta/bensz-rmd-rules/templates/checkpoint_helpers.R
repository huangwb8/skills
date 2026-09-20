# 通用 checkpoint helper：只处理路径、身份、完整性和安全落盘。
# 领域统计逻辑必须留在具体分析单元中。

if (TRUE) {
  .bensz_require_yaml <- function() {
    if (!requireNamespace("yaml", quietly = TRUE)) {
      stop("Package 'yaml' is required for checkpoint metadata.")
    }
  }

  .bensz_is_symlink <- function(path) {
    link <- Sys.readlink(path)
    !is.na(link) && nzchar(link)
  }

  .bensz_assert_portable_name <- function(name, label = "name") {
    if (!nzchar(name) || grepl('[<>:"/\\\\|?*[:cntrl:]]', name) || grepl("[. ]$", name)) {
      stop(label, " contains characters that are not portable to Windows.")
    }
    base <- toupper(strsplit(name, ".", fixed = TRUE)[[1]][[1]])
    if (base %in% c("CON", "PRN", "AUX", "NUL", paste0("COM", 1:9), paste0("LPT", 1:9))) {
      stop(label, " uses a Windows reserved device name.")
    }
    invisible(name)
  }

  .bensz_products_root <- function(
    root = getwd(),
    products_dir = getOption(
      "bensz.products_dir",
      Sys.getenv("BENSZ_PRODUCTS_DIR", unset = "products")
    )
  ) {
    project_root <- normalizePath(root, winslash = "/", mustWork = TRUE)
    if (!is.character(products_dir) || length(products_dir) != 1L || !nzchar(products_dir)) {
      stop("products_dir must be one non-empty project-relative path.")
    }
    portable <- gsub("\\\\", "/", products_dir)
    parts <- strsplit(portable, "/", fixed = TRUE)[[1]]
    test_root <- gsub("\\\\", "/", Sys.getenv("BENSZ_TEST_RUN_ROOT", unset = ""))
    test_parts <- strsplit(test_root, "/", fixed = TRUE)[[1]]
    is_test_products <- nzchar(test_root) &&
      length(test_parts) >= 3L &&
      identical(test_parts[1:2], c("tmp", "tests")) &&
      !any(test_parts %in% c("", ".", "..")) &&
      identical(portable, paste0(test_root, "/products"))
    if (
      grepl("^(?:/|[A-Za-z]:[/\\\\]|\\\\\\\\)", products_dir, perl = TRUE) ||
        any(parts %in% c("", ".", "..")) ||
        (!is_test_products && parts[[1]] %in% c("raw", "reports", "tmp", "_targets", ".bensz-api"))
    ) {
      stop("products_dir must be a safe project-relative product directory.")
    }
    candidate <- normalizePath(file.path(project_root, portable), winslash = "/", mustWork = FALSE)
    if (!startsWith(candidate, paste0(project_root, "/"))) {
      stop("products_dir must stay inside the project root.")
    }
    current <- project_root
    for (part in parts) {
      current <- file.path(current, part)
      if (file.exists(current) && .bensz_is_symlink(current)) {
        stop("Product root cannot contain symlinks: ", part)
      }
    }
    candidate
  }

  .bensz_normalize_relative <- function(paths, root = getwd()) {
    root <- normalizePath(root, winslash = "/", mustWork = TRUE)
    normalized <- normalizePath(paths, winslash = "/", mustWork = TRUE)
    prefix <- paste0(root, "/")
    if (any(normalized != root & !startsWith(normalized, prefix))) {
      stop("Checkpoint input/code paths must stay inside the project root.")
    }
    ifelse(normalized == root, ".", substring(normalized, nchar(prefix) + 1L))
  }

  .bensz_assert_product_dir <- function(product_dir, root = getwd()) {
    products_root <- .bensz_products_root(root = root)
    raw_candidate <- gsub("\\\\", "/", path.expand(product_dir))
    raw_parts <- strsplit(raw_candidate, "/", fixed = TRUE)[[1]]
    if (any(raw_parts %in% c(".", ".."))) {
      stop("product_dir cannot contain dot or parent path segments.")
    }
    candidate <- normalizePath(product_dir, winslash = "/", mustWork = FALSE)
    if (!startsWith(candidate, paste0(products_root, "/"))) {
      stop("product_dir must stay inside the configured project products directory.")
    }
    relative_parts <- strsplit(substring(candidate, nchar(products_root) + 2L), "/", fixed = TRUE)[[1]]
    current <- products_root
    for (part in relative_parts) {
      current <- file.path(current, part)
      if (file.exists(current) && .bensz_is_symlink(current)) {
        stop("Checkpoint paths cannot contain symlinks: ", part)
      }
    }
    candidate
  }

  bensz_hash_value <- function(value) {
    tmp <- tempfile("bensz-hash-", fileext = ".rds")
    on.exit(unlink(tmp), add = TRUE)
    saveRDS(value, tmp, version = 3)
    unname(tools::md5sum(tmp))
  }

  bensz_object_structure <- function(object) {
    dimensions <- dim(object)
    list(
      class = class(object),
      dimensions = if (is.null(dimensions)) NULL else as.integer(dimensions),
      length = length(object),
      names = utils::head(names(object), 100L),
      column_types = if (is.data.frame(object)) {
        vapply(object, function(column) paste(class(column), collapse = "/"), character(1))
      } else NULL,
      missing_by_column = if (is.data.frame(object)) {
        vapply(object, function(column) sum(is.na(column)), integer(1))
      } else NULL
    )
  }

  bensz_summary_lines <- function(object, unit_stem, purpose, downstream_notes = "None recorded.") {
    structure <- bensz_object_structure(object)
    dimensions <- if (is.null(structure$dimensions)) "not tabular" else paste(structure$dimensions, collapse = " x ")
    missing_total <- if (is.null(structure$missing_by_column)) {
      sum(is.na(object))
    } else {
      sum(structure$missing_by_column)
    }
    c(
      paste0("# ", unit_stem),
      "",
      paste0("- Purpose: ", purpose),
      paste0("- Class: ", paste(structure$class, collapse = ", ")),
      paste0("- Dimensions: ", dimensions),
      paste0("- Missing values: ", missing_total),
      paste0("- Object size (bytes): ", as.numeric(object.size(object))),
      paste0("- Downstream notes: ", downstream_notes)
    )
  }

  bensz_file_signatures <- function(paths, root = getwd()) {
    if (length(paths) == 0L) return(list())
    if (any(!file.exists(paths))) {
      stop("Missing identity input: ", paste(paths[!file.exists(paths)], collapse = ", "))
    }
    rel <- .bensz_normalize_relative(paths, root = root)
    info <- file.info(paths)
    stats::setNames(
      lapply(seq_along(paths), function(i) {
        list(path = rel[[i]], size = unname(info$size[[i]]), md5 = unname(tools::md5sum(paths[[i]])))
      }),
      rel
    )
  }

  bensz_cache_identity <- function(
    input_files = character(), parameters = list(), code_files = character(),
    upstream_identities = character(), output_contract_version = 1L,
    runtime_versions = NULL, root = getwd()
  ) {
    payload <- list(
      inputs = bensz_file_signatures(input_files, root),
      parameters = parameters,
      code = bensz_file_signatures(code_files, root),
      upstream_products = sort(as.character(upstream_identities)),
      output_contract_version = as.integer(output_contract_version)
    )
    if (!is.null(runtime_versions)) payload$runtime_versions <- runtime_versions
    bensz_hash_value(payload)
  }

  bensz_product_dir <- function(workflow, unit_stem, root = getwd()) {
    if (!grepl("^[A-Za-z0-9][A-Za-z0-9._-]*$", workflow)) {
      stop("workflow must start with a letter or digit and contain only letters, digits, dot, underscore and hyphen.")
    }
    if (!grepl("^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\. [^/\\\\]+$", unit_stem)) {
      stop("unit_stem must use 'AA.BB.CC. name'.")
    }
    .bensz_assert_portable_name(sub("^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\. ", "", unit_stem), "unit name")
    product_dir <- file.path(.bensz_products_root(root = root), workflow, unit_stem)
    .bensz_assert_product_dir(product_dir, root = root)
  }

  .bensz_replace_file <- function(tmp, destination) {
    if (!file.exists(tmp)) stop("Temporary checkpoint file is missing: ", tmp)
    if (file.exists(destination) && unlink(destination) != 0L) {
      stop("Cannot replace checkpoint file: ", destination)
    }
    if (!file.rename(tmp, destination)) {
      stop("Cannot commit checkpoint file: ", destination)
    }
  }

  bensz_checkpoint_status <- function(product_dir, expected_identity = NULL) {
    product_dir <- .bensz_assert_product_dir(product_dir)
    success <- file.path(product_dir, "SUCCESS")
    metadata_path <- file.path(product_dir, "metadata.yaml")
    if (.bensz_is_symlink(success) || .bensz_is_symlink(metadata_path)) {
      return(list(valid = FALSE, reason = "checkpoint metadata/marker symlink is not allowed"))
    }
    if (!file.exists(success)) return(list(valid = FALSE, reason = "missing SUCCESS"))
    if (!file.exists(metadata_path)) return(list(valid = FALSE, reason = "missing metadata.yaml"))
    .bensz_require_yaml()
    metadata <- tryCatch(yaml::read_yaml(metadata_path), error = function(e) NULL)
    if (!is.list(metadata)) return(list(valid = FALSE, reason = "invalid metadata.yaml"))
    if (!is.character(metadata$product_identity) || length(metadata$product_identity) != 1L ||
        !nzchar(metadata$product_identity)) {
      return(list(valid = FALSE, reason = "missing product identity", metadata = metadata))
    }
    if (!is.null(expected_identity) && !identical(metadata$cache_identity, expected_identity)) {
      return(list(valid = FALSE, reason = "cache identity mismatch", metadata = metadata))
    }
    outputs <- metadata$outputs
    if (!is.list(outputs) || length(outputs) == 0L) {
      return(list(valid = FALSE, reason = "metadata has no outputs", metadata = metadata))
    }
    for (item in outputs) {
      if (!is.list(item) || !is.character(item$path) || length(item$path) != 1L ||
          grepl("^(?:/|[A-Za-z]:[/\\\\]|\\\\\\\\)", item$path, perl = TRUE) ||
          any(strsplit(item$path, "[/\\\\]")[[1]] == "..")) {
        return(list(valid = FALSE, reason = "unsafe output path", metadata = metadata))
      }
      path <- file.path(product_dir, item$path)
      if (.bensz_is_symlink(path)) {
        return(list(valid = FALSE, reason = "checkpoint output symlink is not allowed", metadata = metadata))
      }
      if (!file.exists(path)) return(list(valid = FALSE, reason = paste("missing output", item$path), metadata = metadata))
      if (!identical(unname(tools::md5sum(path)), item$md5)) {
        return(list(valid = FALSE, reason = paste("damaged output", item$path), metadata = metadata))
      }
    }
    marker <- trimws(paste(readLines(success, warn = FALSE, encoding = "UTF-8"), collapse = ""))
    if (!identical(marker, metadata$cache_identity)) {
      return(list(valid = FALSE, reason = "SUCCESS identity mismatch", metadata = metadata))
    }
    list(valid = TRUE, reason = "cache hit", metadata = metadata)
  }

  bensz_product_identity <- function(product_dir, expected_identity = NULL) {
    status <- bensz_checkpoint_status(product_dir, expected_identity = expected_identity)
    if (!isTRUE(status$valid)) stop("Invalid upstream product: ", status$reason)
    status$metadata$product_identity
  }

  bensz_run_decision <- function(unit_id, status) {
    force_step <- Sys.getenv("BENSZ_FORCE_STEP", unset = "")
    resume_from <- Sys.getenv("BENSZ_RESUME_FROM", unset = "")
    id_pattern <- "^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}$"
    if (!grepl(id_pattern, unit_id)) stop("unit_id must use AA.BB.CC.")
    if (nzchar(force_step) && !grepl(id_pattern, force_step)) stop("BENSZ_FORCE_STEP must use AA.BB.CC.")
    if (nzchar(resume_from) && !grepl(id_pattern, resume_from)) stop("BENSZ_RESUME_FROM must use AA.BB.CC.")
    if (nzchar(force_step) && identical(force_step, unit_id)) return("run")
    if (nzchar(resume_from) && unit_id < resume_from && !isTRUE(status$valid)) {
      stop("Cannot resume from ", resume_from, ": earlier unit ", unit_id, " is invalid.")
    }
    if (isTRUE(status$valid)) "hit" else "run"
  }

  bensz_write_checkpoint <- function(
    object, product_dir, unit_id, cache_identity, summary_lines,
    preview = NULL, extra_metadata = list(), elapsed_seconds = NA_real_,
    output_contract_version = 1L
  ) {
    .bensz_require_yaml()
    version_is_valid <- is.numeric(output_contract_version) && length(output_contract_version) == 1L &&
      !is.na(output_contract_version) && is.finite(output_contract_version) &&
      output_contract_version == as.integer(output_contract_version) && output_contract_version >= 1L
    if (!isTRUE(version_is_valid)) {
      stop("output_contract_version must be one positive integer.")
    }
    output_contract_version <- as.integer(output_contract_version)
    product_dir <- .bensz_assert_product_dir(product_dir)
    dir.create(product_dir, recursive = TRUE, showWarnings = FALSE)
    success <- file.path(product_dir, "SUCCESS")
    if (file.exists(success) && unlink(success) != 0L) {
      stop("Cannot invalidate existing SUCCESS marker: ", success)
    }
    stale_preview <- file.path(product_dir, "preview.tsv")
    if (is.null(preview) && file.exists(stale_preview) && unlink(stale_preview) != 0L) {
      stop("Cannot remove stale preview: ", stale_preview)
    }

    token <- paste0(Sys.getpid(), "-", format(Sys.time(), "%Y%m%d%H%M%OS6"))
    main_tmp <- file.path(product_dir, paste0(".main.rds.", token))
    summary_tmp <- file.path(product_dir, paste0(".summary.md.", token))
    metadata_tmp <- file.path(product_dir, paste0(".metadata.yaml.", token))
    preview_tmp <- file.path(product_dir, paste0(".preview.tsv.", token))
    success_tmp <- file.path(product_dir, paste0(".SUCCESS.", token))
    temp_paths <- c(main_tmp, summary_tmp, metadata_tmp, preview_tmp, success_tmp)
    on.exit(unlink(temp_paths[file.exists(temp_paths)]), add = TRUE)

    saveRDS(object, main_tmp, version = 3)
    invisible(readRDS(main_tmp))
    writeLines(as.character(summary_lines), summary_tmp, useBytes = TRUE)

    output_paths <- c("main.rds", "summary.md")
    if (!is.null(preview)) {
      utils::write.table(preview, preview_tmp, sep = "\t", row.names = FALSE, quote = TRUE, na = "")
      invisible(utils::read.delim(preview_tmp, nrows = 5L, check.names = FALSE))
      output_paths <- c(output_paths, "preview.tsv")
    }

    pending <- c(main_tmp, summary_tmp)
    if (!is.null(preview)) pending <- c(pending, preview_tmp)
    outputs <- lapply(seq_along(output_paths), function(i) {
      list(path = output_paths[[i]], md5 = unname(tools::md5sum(pending[[i]])))
    })
    product_identity <- bensz_hash_value(list(cache_identity = cache_identity, outputs = outputs))
    metadata <- c(
      list(
        unit_id = unit_id,
        cache_identity = cache_identity,
        product_identity = product_identity,
        output_contract_version = output_contract_version,
        elapsed_seconds = as.numeric(elapsed_seconds),
        output_structure = bensz_object_structure(object),
        outputs = outputs
      ),
      extra_metadata
    )
    yaml::write_yaml(metadata, metadata_tmp)
    invisible(yaml::read_yaml(metadata_tmp))

    .bensz_replace_file(main_tmp, file.path(product_dir, "main.rds"))
    .bensz_replace_file(summary_tmp, file.path(product_dir, "summary.md"))
    if (!is.null(preview)) .bensz_replace_file(preview_tmp, file.path(product_dir, "preview.tsv"))
    .bensz_replace_file(metadata_tmp, file.path(product_dir, "metadata.yaml"))
    writeLines(cache_identity, success_tmp, useBytes = TRUE)
    .bensz_replace_file(success_tmp, success)

    final_status <- bensz_checkpoint_status(product_dir, expected_identity = cache_identity)
    if (!isTRUE(final_status$valid)) stop("Committed checkpoint failed validation: ", final_status$reason)
    invisible(final_status)
  }
}
