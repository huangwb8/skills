# 跨平台兼容性最佳实践

## 核心规则

始终使用相对路径，避免绝对路径。

## 路径拼接

使用 `file.path()` 自动处理路径分隔符：

```r
# 推荐：file.path() 自动适配平台
input_path <- file.path("data", "raw", "expression.csv")
output_path <- file.path("tmp", "results", "figure1.png")

# 避免：手动拼接路径分隔符
# input_path <- "data/raw/expression.csv"  # 仅适用于当前系统
# input_path <- "data\\raw\\expression.csv"  # Windows 专用
```

## 文件 I/O 最佳实践

### 读取文件

```r
# 推荐：相对路径 + file.path()
data <- read.csv(file.path("data", "input.csv"))

# 推荐：使用 here/here 包（如已安装）
if (requireNamespace("here", quietly = TRUE)) {
  data <- read.csv(here::here("data", "input.csv"))
}
```

### 写入文件

```r
# 推荐：输出到临时文件夹
output_dir <- file.path("tmp", "analysis")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
output_file <- file.path(output_dir, "result.csv")
write.csv(data, output_file)
```

### 可选：安全写入/读取封装（统一分隔符与编码）

```r
# 安全写入 CSV 函数示例
.dvmut_safe_write_csv <- function(data, path, ...) {
  # 规范化路径（统一使用正斜杠）
  path <- normalizePath(path, winslash = "/", mustWork = FALSE)
  # 确保目录存在
  dir.create(dirname(path), showWarnings = FALSE, recursive = TRUE)
  # 写入数据（统一使用 UTF-8 编码）
  utils::write.csv(data, path, row.names = FALSE, fileEncoding = "UTF-8", ...)
  invisible(path)
}

# 安全读取 CSV 函数示例
.dvmut_safe_read_csv <- function(path, ...) {
  if (!file.exists(path)) return(NULL)
  tryCatch(
    utils::read.csv(path, stringsAsFactors = FALSE, ...),
    error = function(e) {
      warning("Failed to read ", path, ": ", e$message)
      NULL
    }
  )
}
```

使用示例：

```r
.dvmut_safe_write_csv(micro_data, "output/micro_continuous.csv")
data <- .dvmut_safe_read_csv("output/micro_continuous.csv")
if (is.null(data)) stop("Failed to load data")
```

### 路径存在性检查

```r
# 推荐：先检查再使用
if (file.exists("00.Environment.R")) {
  source("00.Environment.R")
} else {
  stop("Required file not found: 00.Environment.R")
}
```

## 路径验证工具（可选）

为确保跨平台兼容性，可使用路径验证脚本：

```r
# 方式 1：在 R 中运行
source("bensz-rmd-rules/scripts/validate_paths.R")
validate_project_paths(project_dir = ".")

# 方式 2：从命令行运行
Rscript bensz-rmd-rules/scripts/validate_paths.R /path/to/project
```

## 平台差异处理

### 换行符处理

```r
# 读取文件时统一换行符
data <- read.csv(file.path("data", "input.csv"),
                 fileEncoding = "UTF-8")

# 写出文件时指定换行符
write.csv(data, file.path("tmp", "output.csv"),
          fileEncoding = "UTF-8")
```

### 环境变量

```r
# 如需使用环境变量，跨平台获取路径
# Rproj_root <- Sys.getenv("R_PROJECT_ROOT")
# if (Rproj_root == "") {
#   Rproj_root <- getwd()
# }
```

## 常见陷阱

| 陷阱 | 问题 | 解决方案 |
|------|------|----------|
| 硬编码用户名 | `/Users/username/...` 不可移植 | 使用相对路径或项目根目录 |
| 混用路径分隔符 | Windows 用 `\`，Unix 用 `/` | 始终使用 `file.path()` |
| 绝对路径 | 代码无法在其他设备运行 | 从项目根目录的相对路径开始 |
| 路径大小写 | Windows 不敏感，Unix 敏感 | 统一使用小写文件名和目录 |

## 跨平台测试清单

- [ ] 所有路径是否使用相对路径？
- [ ] 路径拼接是否使用 `file.path()`？
- [ ] 文件 I/O 是否检查了路径存在性？
- [ ] 是否避免了硬编码用户名或系统路径？
- [ ] 文件名是否统一使用小写（避免大小写问题）？
