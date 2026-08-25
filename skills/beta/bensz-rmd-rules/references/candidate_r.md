# candidate_r 函数库使用指南

## 概述

`candidate_r` 是一个可选的独立分析脚本集合，包含特征选择、聚类、生存分析等函数。

## 可选性说明

- `candidate_r` **不是必需的**，只是用户可能拥有的"自定义函数目录"的一种
- 如果用户没有 candidate_r，AI 应使用 lucky 系列、CRAN/Bioconductor 包或实现最小辅助函数
- candidate_r 典型场景：用户有一些常用的独立 R 脚本（如 `feature_selection.R`、`clustering.R`），但不方便打包成正式 R 包

## 使用模式

### 模式 1：已通过 00.Environment.R 加载（默认）

当用户已在 `00.Environment.R` 中加载 candidate_r 后，AI 可以直接使用这些函数：

```r
# 先加载环境
source("00.Environment.R")

# 轻量检查：函数是否已存在
fs <- get0("feature_selection", ifnotfound = NULL)
if (is.function(fs)) {
  # 使用 candidate_r 中的函数
  res <- fs(x, y, method = "lasso")
} else {
  # 回退：使用 lucky/CRAN/or 实现最小 helper
  res <- glmnet::cv.glmnet(x, y, alpha = 1)
}
```

**优点**：
- 用户一次性配置（在 00.Environment.R），AI 无需猜测路径
- 轻量检查，不扫描磁盘，不假设文件结构

### 模式 2：用户指定路径（可选）

用户可在环境设置代码块中定义 `candidate_r_path`，AI 按该路径加载：

```r
# 在 00.Environment.R 或 Rmd 环境设置中
if (exists("candidate_r_path") && nzchar(candidate_r_path)) {
  f <- file.path(candidate_r_path, "feature_selection.R")
  if (!file.exists(f)) {
    stop("candidate_r script not found: ", f)
  }
  source(f)
}
```

## 安全提示

`source()` 只应指向**信任的本地代码**，不要对未知来源/下载来的脚本直接 `source()`。

## 实践原则

1. **不猜路径**：AI 不应假设 candidate_r 的标准位置
2. **不扫描磁盘**：避免使用 `list.files()` 搜索 candidate_r
3. **优先现有资源**：lucky 系列不满足时，才考虑 candidate_r
4. **提供回退方案**：当 candidate_r 不可用时，使用 CRAN 包或最小实现

## 资源使用优先级

1. **已安装的 R 包**（直接 `library()`）
2. **candidate_r 函数库**（已由 `00.Environment.R` 加载；或用户通过 `candidate_r_path` 指定路径后再 `source()`）
3. **CRAN/Bioconductor 包**（如确实需要新包）
4. **自定义函数**（最后选择，写入 `00.Environment.R`）
