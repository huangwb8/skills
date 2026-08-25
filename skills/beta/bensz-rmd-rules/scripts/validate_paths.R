# bensz-rmd-rules 路径验证脚本
# 用途：检查 R 项目中是否存在硬编码路径或跨平台兼容性问题
#
# 使用方法：
#   source("bensz-rmd-rules/scripts/validate_paths.R")
#   validate_project_paths(project_dir = ".")
#
# 或从命令行运行：
#   Rscript bensz-rmd-rules/scripts/validate_paths.R /path/to/project

if (!exists("project_dir")) {
  project_dir <- "."
}

# 检查结果存储
check_results <- list(
  passed = list(),
  failed = list(),
  warnings = list()
)

# 辅助函数：记录检查结果
add_result <- function(category, item, status, message) {
  if (status == "PASS") {
    check_results$passed[[length(check_results$passed) + 1]] <<- list(
      category = category,
      item = item,
      message = message
    )
  } else if (status == "FAIL") {
    check_results$failed[[length(check_results$failed) + 1]] <<- list(
      category = category,
      item = item,
      message = message
    )
  } else if (status == "WARN") {
    check_results$warnings[[length(check_results$warnings) + 1]] <<- list(
      category = category,
      item = item,
      message = message
    )
  }
}

# 检查 1：扫描硬编码的用户名路径
check_hardcoded_username <- function(file_path) {
  lines <- readLines(file_path, warn = FALSE)
  patterns <- c(
    "/Users/[a-zA-Z0-9_]+/",
    "/home/[a-zA-Z0-9_]+/",
    "C:\\\\Users\\\\[a-zA-Z0-9_]+\\\\",
    "C:\\\\Users\\\\[a-zA-Z0-9_]+/"
  )

  for (i in seq_along(lines)) {
    # 跳过注释行（仍建议避免在注释里遗留真实用户名路径，但这里不把注释作为强制失败来源）
    if (grepl("^\\s*#", lines[i])) next
    for (p in patterns) {
      if (grepl(p, lines[i], fixed = FALSE)) {
        match <- regmatches(lines[i], regexpr(p, lines[i]))
        add_result(
          category = "硬编码用户名",
          item = file_path,
          status = "FAIL",
          message = sprintf("  第 %d 行发现硬编码用户名: %s", i, match)
        )
        return(FALSE)
      }
    }
  }
  return(TRUE)
}

# 检查 2：扫描绝对路径（排除合理的系统路径）
check_absolute_paths <- function(file_path) {
  lines <- readLines(file_path, warn = FALSE)
  # 排除合理的系统路径（如系统目录、临时目录）
  is_system_path <- function(path) {
    p <- gsub("\\\\", "/", path)
    grepl("^(/usr/|/opt/|/Library/|/tmp/|C:/Windows/)", p)
  }
  # 从一行中提取形如 "/..." 或 "C:\..." 的绝对路径字符串（仅在引号内）
  extract_abs_paths <- function(line) {
    m <- gregexpr("[\"']((/|[A-Za-z]:[\\\\/])[^\"']+)[\"']", line, perl = TRUE)
    hits <- regmatches(line, m)[[1]]
    if (length(hits) == 0) return(character(0))
    # 去掉包裹引号
    out <- gsub("^[\"']|[\"']$", "", hits)
    # 排除 URL
    out[!grepl("^https?://", out)]
  }

  for (i in seq_along(lines)) {
    line <- lines[i]
    # 跳过注释行
    if (grepl("^\\s*#", line)) next

    abs_paths <- extract_abs_paths(line)
    if (length(abs_paths) == 0) next
    for (p in abs_paths) {
      if (is_system_path(p)) next
      add_result(
        category = "绝对路径",
        item = file_path,
        status = "WARN",
        message = sprintf("  第 %d 行可能包含绝对路径: %s", i, p)
      )
    }
  }
  return(TRUE)
}

# 检查 3：检查是否使用 file.path() 进行路径拼接
check_file_path_usage <- function(file_path) {
  lines <- readLines(file_path, warn = FALSE)
  # 检测常见的“手动拼接路径”反模式：用 paste/paste0/sprintf/glue 等拼出 "a/b"，
  # 而不是用 file.path(a, b)。（注意：单纯出现字符串 "/a/b" 不应触发该检查）
  bad_patterns <- c(
    "paste0\\([^#\\n]*['\\\"]\\/['\\\"]",
    "paste\\([^#\\n]*sep\\s*=\\s*['\\\"]\\/['\\\"]",
    "sprintf\\([^#\\n]*%s\\/%s",
    "glue::glue\\([^#\\n]*\\{[^}]+\\}\\/\\{[^}]+\\}",
    "stringr::str_c\\([^#\\n]*['\\\"]\\/['\\\"]"
  )

  for (i in seq_along(lines)) {
    line <- lines[i]
    # 跳过注释行
    if (grepl("^\\s*#", line)) next
    # 跳过已使用 file.path() 的行
    if (grepl("file.path\\(", line)) next
    # 跳过 URL
    if (grepl("https?://", line)) next

    for (p in bad_patterns) {
      if (!grepl(p, line, perl = TRUE)) next
      add_result(
        category = "路径拼接",
        item = file_path,
        status = "WARN",
        message = sprintf("  第 %d 行可能手动拼接路径: %s", i, trimws(line))
      )
      break
    }
  }
  return(TRUE)
}

# 检查 4：检查文件 I/O 是否有路径存在性检查
check_path_validation <- function(file_path) {
  lines <- readLines(file_path, warn = FALSE)
  io_patterns <- c(
    "readCSV\\(", "read\\.csv\\(", "readRDS\\(", "read\\.table\\(",
    "load\\(", "source\\("
  )

  has_io <- FALSE
  has_check <- FALSE

  for (i in seq_along(lines)) {
    line <- lines[i]
    if (grepl("^\\s*#", line)) next
    for (p in io_patterns) {
      if (grepl(p, line)) {
        has_io <- TRUE
        break
      }
    }
    if (grepl("file\\.exists\\(", line) || grepl("dir\\.exists\\(", line)) {
      has_check <- TRUE
    }
  }

  if (has_io && !has_check) {
    add_result(
      category = "路径验证",
      item = file_path,
      status = "WARN",
      message = "  发现文件 I/O 操作但未检测到路径存在性检查"
    )
  }
  return(TRUE)
}

# 主函数：验证项目路径
validate_project_paths <- function(project_dir = ".") {
  cat(sprintf("=== bensz-rmd-rules 路径验证 ===\n"))
  cat(sprintf("项目目录: %s\n\n", normalizePath(project_dir)))

  # Ensure repeated calls in the same R session do not accumulate stale findings.
  check_results$passed <<- list()
  check_results$failed <<- list()
  check_results$warnings <<- list()

  # 查找所有 .R/.r 与 .Rmd/.rmd 文件
  r_files <- list.files(project_dir, pattern = "\\.(R|r|Rmd|rmd)$", recursive = TRUE, full.names = TRUE)

  if (length(r_files) == 0) {
    cat("未找到任何 .R 或 .Rmd 文件\n")
    return(invisible(NULL))
  }

  cat(sprintf("找到 %d 个文件需要检查\n\n", length(r_files)))

  # 逐文件检查
  for (f in r_files) {
    check_hardcoded_username(f)
    check_absolute_paths(f)
    check_file_path_usage(f)
    check_path_validation(f)
  }

  # 输出结果
  cat("\n=== 检查结果 ===\n\n")

  if (length(check_results$failed) > 0) {
    cat(sprintf("[FAIL] 失败 (%d 项):\n", length(check_results$failed)))
    for (r in check_results$failed) {
      cat(sprintf("\n[%s] %s\n%s\n", r$category, r$item, r$message))
    }
    cat("\n")
  }

  if (length(check_results$warnings) > 0) {
    cat(sprintf("[WARN] 警告 (%d 项):\n", length(check_results$warnings)))
    for (r in check_results$warnings) {
      cat(sprintf("\n[%s] %s\n%s\n", r$category, r$item, r$message))
    }
    cat("\n")
  }

  if (length(check_results$passed) > 0) {
    cat(sprintf("[PASS] 通过 (%d 项)\n", length(check_results$passed)))
  }

  # 总结
  total_issues <- length(check_results$failed) + length(check_results$warnings)
  if (total_issues == 0) {
    cat("\n🎉 所有检查通过！项目路径符合跨平台兼容性要求。\n")
  } else {
    cat(sprintf("\n[WARN] 发现 %d 个问题，请修复后重新检查。\n", total_issues))
  }

  invisible(check_results)
}

# 如果直接运行此脚本
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) > 0) {
    validate_project_paths(args[1])
  } else {
    validate_project_paths(".")
  }
}
