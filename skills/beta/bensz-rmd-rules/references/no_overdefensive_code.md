# 不过度保护原则（避免“防御性过载”）

核心理念：信任 `00.Environment.R` 的环境配置，避免对已加载的包和函数进行冗余检查；让错误显式暴露，避免静默失败。

## 绝对禁止的反模式

```r
# 包加载检查（绝对禁止）
if (!requireNamespace("DT", quietly = TRUE)) {
  # 降级方案
} else {
  DT::datatable(data)
}
# 正确做法：直接使用 DT::datatable(data)，因为 00.Environment.R 已加载

# 包加载多重检查（绝对禁止）
if (requireNamespace("luckyBase", quietly = TRUE)) {
  luckyBase::Plus.library("DT")
} else {
  suppressPackageStartupMessages(library(DT))
}
# 正确做法：00.Environment.R 已执行加载，主脚本无需重复

# 数据多重验证（绝对禁止）
if(!is.null(data) && nrow(data) > 0 && !all(is.na(data$value))) {
  if(class(data$value) %in% c("numeric", "integer")) {
    result <- mean(data$value, na.rm = TRUE)
  } else {
    result <- NA
    warning("数据类型不正确")
  }
} else {
  result <- NA
  warning("数据为空或无效")
}

# 简洁直接（推荐）
result <- mean(data$value, na.rm = TRUE)

# 表格渲染过度检查（绝对禁止）
if (!is.null(data) && requireNamespace("DT", quietly = TRUE)) {
  DT::datatable(utils::head(data, n), options = list(scrollX = TRUE, pageLength = 10))
} else if (!is.null(data)) {
  utils::head(data, n)
}
# 正确做法：DT::datatable(utils::head(data, n), options = list(scrollX = TRUE, pageLength = 10))
```

## 检查边界规则

必须检查的场景（白名单）：

- 文件 I/O 前检查路径有效性
- 用户输入的关键参数（如分组变量是否存在于数据中）
- 外部数据源连接（如数据库、API）
- **00.Environment.R 存在性检查**：作为整个分析的硬性前提，显式 `if (!file.exists("00.Environment.R")) stop(...)` 提供比自然报错更清晰的错误信息，属于合理异常（见 `templates/Rmd_template.Rmd` 示例）

不应检查的场景（黑名单）：

- R 包是否已加载（`00.Environment.R` 已通过 `luckyBase::Plus.library()` 统一管理）
- 函数是否存在（对于通过 `00.Environment.R` 加载的函数）
- 内部中间变量的类型检查
- 标准 R 包函数的返回值验证
- 已由用户代码处理过的数据

硬性规定：

- 主脚本中禁止使用 `requireNamespace()` 检查包可用性
- 主脚本中禁止使用 `if (!is.null(...) && requireNamespace(...))` 模式
- 主脚本中禁止出现包加载的“降级方案”或“回退逻辑”

## 禁止占位性代码（Fail Loud）

核心问题：在科研分析场景中，用占位性代码保证“不报错”会隐藏功能失败，导致分析结果不完整且难以察觉。

占位性代码定义：使用 `try()` 捕获错误后，将结果赋值为 `NULL`、`NA`、空数据框，或直接跳过/打印警告继续，从而保证代码表面运行成功的模式。

绝对禁止的占位性模式：

| 模式类型 | 示例代码 | 危害 |
|---------|---------|------|
| try-catch 后赋值 NULL | `if (inherits(fit, "try-error")) { fit <- NULL }` | 静默失败，后续代码可能崩溃或产生误导性结果 |
| try-catch 后打印警告继续 | `if (inherits(fit, "try-error")) { cat("Failed, skipping...\n"); next }` | 用户不易察觉，分析结果不完整 |
| 降级到占位符 | `if (!requireNamespace("pkg")) { result <- data.frame() }` | 空结果导致误导性输出 |
| 条件分支后无有效逻辑 | `if (error) { return(NA) } else { ... }` | 功能形同虚设，分析目标未达成 |

切实落地要求：

- 必须确保功能在正常流程中切实落地，不得使用占位符保证“不报错”
- 如功能失败，应 `stop()` 报错而非静默处理
- 如需容错，必须提供有效降级方案（替代算法/简化模型），且降级方案也要切实落地

正确示例对比：

```r
# ❌ 危险：占位性代码
fit_lda <- try(MASS::lda(f_main, data = train), silent = TRUE)
if (inherits(fit_lda, "try-error")) {
  cat("LDA model fitting failed, skipping...\n")
  fit_lda <- NULL
}

# ✅ 正确：切实落地或报错
fit_lda <- MASS::lda(f_main, data = train)

# ✅ 正确：需要容错时，提供有效降级方案
fit_lda <- try(MASS::lda(f_main, data = train), silent = TRUE)
if (inherits(fit_lda, "try-error")) {
  message("LDA failed, falling back to QDA...")
  fit_lda <- MASS::qda(f_main, data = train)
}
if (inherits(fit_lda, "try-error")) {
  stop("Both LDA and QDA failed. Please check data or use other methods.")
}
```

权衡原则：

- 科研分析 > 代码美观（宁可报错，也要结果可信）
- 显式失败 > 静默成功（失败要暴露）
- 有效降级 > 占位符（降级也要实现目标）

