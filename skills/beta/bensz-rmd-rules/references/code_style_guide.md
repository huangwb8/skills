# R 代码风格指南

本文档规范 R Markdown 分析脚本中的代码风格，确保代码简洁、易读、易维护。

## 核心原则

| 原则 | 说明 |
|------|------|
| **管道优先** | 使用 `%>%` 或 `|>` 构建可读的数据处理流程 |
| **向量化思维** | 优先使用向量化操作，避免遍历 + if 判断 |
| **函数式编程** | 使用 `purrr::map()` 等函数式工具替代循环 |
| **数据驱动** | 用查找表、join 等数据驱动方式替代硬编码逻辑 |

## 基础代码风格

### 管道操作

```r
# 好的风格：简洁、直观
result <- data %>%
  filter(condition) %>%
  group_by(category) %>%
  summarise(mean_value = mean(value))

# 避免的风格：过度嵌套、难以理解
result <- summarise(group_by(filter(data, condition), category), mean_value = mean(value))
```

### 命名规范

- **变量名**：小写字母 + 下划线，描述性强（如 `survival_data`, `gene_expression`）
- **函数名**：动词开头，清晰表达功能（如 `calculate_survival()`, `plot_heatmap()`）
- **中间函数**：以 `.` 开头，个性化命名（如 `.cf01_prepare_data()`）

## 减少 if 语句使用

**核心思想**：if 语句增加代码复杂度，优先使用向量化操作、内置函数和数据驱动方式替代。

### 场景对照表

| 场景 | 推荐做法 | 避免 |
|------|----------|------|
| 条件赋值 | `dplyr::case_when()` / `ifelse()` / `dplyr::coalesce()` | 嵌套 `if-else` |
| 分类映射 | `purrr::map()` / `dplyr::left_join()` | 手动 `if` 判断 |
| 数值替换 | `dplyr::recode()` / `dplyr::na_if()` | `if (x == "a") x <- "b"` |
| 存在性检查 | `any()` / `all()` / `%in%` | 遍历 + `if` 判断 |
| 多分支逻辑 | 向量化函数 / 查找表 | 多层 `if-else if-else` |

### 条件赋值示例

```r
# 好的做法：向量化 + 数据驱动
data$category <- case_when(
  data$value > 90 ~ "high",
  data$value > 50 ~ "medium",
  TRUE ~ "low"
)

# 避免：命令式 if 判断
data$category <- NA
for (i in seq_len(nrow(data))) {
  if (data$value[i] > 90) {
    data$category[i] <- "high"
  } else if (data$value[i] > 50) {
    data$category[i] <- "medium"
  } else {
    data$category[i] <- "low"
  }
}
```

### 数值替换示例

```r
# 好的做法：向量化替换
data$status <- dplyr::recode(data$old_status,
  "a" = "active",
  "i" = "inactive",
  "u" = "unknown"
)

# 避免：逐个 if 判断
data$status <- NA
for (i in seq_len(nrow(data))) {
  if (data$old_status[i] == "a") {
    data$status[i] <- "active"
  } else if (data$old_status[i] == "i") {
    data$status[i] <- "inactive"
  } else if (data$old_status[i] == "u") {
    data$status[i] <- "unknown"
  }
}
```

### 分类映射示例

```r
# 好的做法：数据驱动（查找表）
lookup <- tibble(
  code = c("A", "B", "C"),
  label = c("Type A", "Type B", "Type C")
)
data <- left_join(data, lookup, by = c("category_code" = "code"))

# 避免：手动 if 判断
data$category_label <- NA
data$category_label[data$category_code == "A"] <- "Type A"
data$category_label[data$category_code == "B"] <- "Type B"
data$category_label[data$category_code == "C"] <- "Type C"
```

## 边界规则

### if 语句使用边界

**允许**：
- 控制流程（如提前返回、参数验证）
- 无法向量化的场景
- 函数内部的逻辑判断（非数据操作）

**禁止**：
- 遍历数据行做简单判断
- 用 if 做可用向量化替代的操作

### 禁止防御性文件存在性检查

不要为"文件是否存在"写大量 if 语句。让代码在文件缺失时自然报错，由调用方处理。

```r
# 好的做法：直接读取，缺失时报错
data <- readRDS(file.path("tmp", "analysis_results.rds"))

# 避免：防御性 if 检查
if (file.exists(file.path("tmp", "analysis_results.rds"))) {
  data <- readRDS(file.path("tmp", "analysis_results.rds"))
} else {
  stop("文件不存在")  # 与不写 if 效果相同，但更冗长
}
```

**理由**：
- 文件缺失是异常情况，应通过报错暴露，而非静默吞掉
- 过多 if 检查增加维护负担，且容易掩盖真实问题
- R 的 `stop()` 本身就是处理异常的标准机制

## 代码注释规范

### 代码块头部

必须说明目的/输入/参数/输出，帮助人类快速理解上下文：

```r
# 目的：一句话概括代码块目的
# 输入：关键输入来源或变量
# 参数：来自 YAML params / 全局变量的关键参数
# 输出：关键变量或输出文件
```

### 分步注释

用 `Step` 注释拆分流程：

```r
# Step 1: 数据加载
# Step 2: 数据清洗
# Step 3: 统计分析
```

### 业务逻辑注释

说明筛选或判断的业务含义：

```r
# 规则：说明筛选或判断的业务含义
# 回退策略：说明缺失数据时的处理方式
```

### 注释原则

- 代码块头部必须说明目的/输入/参数/输出
- 关键步骤用 `Step` 注释拆分流程
- 复杂逻辑、正则、魔法数、关键中间函数要补一句"为何如此"
- 注释保持简洁，建议不超过代码行数的 20%

## 常见反模式

### 反模式 1：遍历 + if

```r
# 避免
for (i in seq_len(nrow(data))) {
  if (data$value[i] > threshold) {
    data$flag[i] <- "high"
  } else {
    data$flag[i] <- "low"
  }
}

# 推荐
data$flag <- ifelse(data$value > threshold, "high", "low")
```

### 反模式 2：嵌套 if-else

```r
# 避免
if (condition1) {
  if (condition2) {
    result <- "A"
  } else {
    result <- "B"
  }
} else {
  if (condition3) {
    result <- "C"
  } else {
    result <- "D"
  }
}

# 推荐
result <- case_when(
  condition1 & condition2 ~ "A",
  condition1 & !condition2 ~ "B",
  !condition1 & condition3 ~ "C",
  TRUE ~ "D"
)
```

### 反模式 3：防御性文件检查

```r
# 避免
if (file.exists(path)) {
  data <- readRDS(path)
} else {
  stop("File not found")
}

# 推荐
data <- readRDS(path)  # 缺失时自动报错
```
