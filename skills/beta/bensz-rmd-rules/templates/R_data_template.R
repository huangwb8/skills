# {主脚本名}.R - 数据处理与计算脚本
# 用途：[简要说明数据处理目的]
# 目的：[一句话概括代码块目的]
# 输入：[关键输入数据或路径]
# 参数：[来自 YAML params / 全局变量的关键参数]
# 输出：[关键变量或输出文件]
#
# 核心功能：
# - 数据加载与预处理
# - 耗时计算（统计检验、模型训练等）
# - 结果保存（供 .Rmd 使用）
#
# 使用方法：
#   source("{主脚本名}.R")
#
# 输出位置：
#   tmp/{主脚本名}/

# ==== 环境初始化 ====
source("00.Environment.R")
source("{主脚本名}_functions.R")

# 创建输出目录
output_dir <- file.path("tmp", "{主脚本名}")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# ==== 1. 数据加载 ====
# Step 1: 数据加载
cat("=== 步骤 1/4: 加载数据 ===\n")

# 示例：加载数据
# raw_data <- read.csv(file.path("data", "input.csv"))
# str(raw_data)

# ==== 2. 数据预处理 ====
# Step 2: 数据预处理
cat("=== 步骤 2/4: 数据预处理 ===\n")

# 示例：数据清洗
# processed_data <- raw_data %>%
#   filter(!is.na(key_column)) %>%
#   mutate(new_column = ...)

# ==== 3. 核心计算 ====
# Step 3: 核心计算
cat("=== 步骤 3/4: 核心计算 ===\n")

# 示例：统计检验
# computation_results <- list(
#   test1 = t.test(...),
#   test2 = wilcox.test(...),
#   model1 = lm(...)
# )

# ==== 4. 结果保存 ====
# Step 4: 结果保存
cat("=== 步骤 4/4: 保存结果 ===\n")

# 保存处理后的数据（供 .Rmd 使用）
saveRDS(processed_data, file.path(output_dir, "processed_data.rds"))

# 保存计算结果（供 .Rmd 可视化）
saveRDS(computation_results, file.path(output_dir, "computation_results.rds"))

# （可选）保存原始数据备份
# saveRDS(raw_data, file.path(output_dir, "raw_data.rds"))

cat("\n")
cat("[PASS] 数据处理完成！\n")
cat("📁 结果已保存到:", output_dir, "\n")
cat("- processed_data.rds: 处理后的数据\n")
cat("- computation_results.rds: 计算结果\n")
cat("\n")
cat("下一步：在 RStudio 中打开 {主脚本名}.Rmd 进行可视化分析\n")
