# AA.BB.CC. 名称.R - 单个分析单元的计算脚本
# 目的：[本单元解决的问题]
# 上游：[更早编号的单元；没有则写 raw 输入]
# 输入：[raw/ 或 products/ 中的相对路径]
# 参数：[只列影响本单元科学结果的参数]
# 输出：products/<流程>/AA.BB.CC. 名称/

source("00.Environment.R")
source(file.path("templates", "checkpoint_helpers.R"))

unit_id <- "01.00.00"
unit_stem <- "01.00.00. 数据整理"
workflow <- "main"
product_dir <- bensz_product_dir(workflow, unit_stem)
unit_functions <- paste0(unit_stem, "_functions.R")
if (file.exists(unit_functions)) source(unit_functions)

# 只把会改变本单元结果的参数纳入缓存身份；报告阈值与配色属于 Rmd。
unit_parameters <- list(example_parameter = "replace-me")
input_files <- c(file.path("raw", "input.tsv"))
code_files <- c(paste0(unit_stem, ".R"), unit_functions, file.path("templates", "checkpoint_helpers.R"))
code_files <- code_files[file.exists(code_files)]
# 下游单元应使用实际产品身份，而非上游静态 cache identity：
# upstream_dir <- bensz_product_dir("main", "00.50.00. 上游单元")
# upstream_identities <- c(bensz_product_identity(upstream_dir))
upstream_identities <- character()
output_contract_version <- 1L

cache_identity <- bensz_cache_identity(
  input_files = input_files,
  parameters = unit_parameters,
  code_files = code_files,
  upstream_identities = upstream_identities,
  output_contract_version = output_contract_version
)
status <- bensz_checkpoint_status(product_dir, expected_identity = cache_identity)
decision <- bensz_run_decision(unit_id, status)

if (identical(decision, "hit")) {
  message("[CACHE HIT] ", unit_stem)
  result <- readRDS(file.path(product_dir, "main.rds"))
} else {
  message("[RUN] ", unit_stem, " - ", status$reason)
  started_at <- proc.time()[["elapsed"]]

  # ==== 数据加载（raw/ 只读）====
  # raw_data <- utils::read.delim(input_files[[1]], check.names = FALSE)

  # ==== 本单元计算 ====
  # result <- .unit_prepare_data(raw_data, unit_parameters)
  stop("Replace the template computation with a real implementation before running.")

  # 重要矩形数据提供受控预览；复杂对象至少提供结构与统计摘要。
  preview <- if (is.data.frame(result)) utils::head(result, 100L) else NULL
  summary_lines <- bensz_summary_lines(
    object = result,
    unit_stem = unit_stem,
    purpose = "Replace with the real analysis purpose.",
    downstream_notes = "Record exclusions, assumptions, anomalies and constraints for downstream units."
  )

  bensz_write_checkpoint(
    object = result,
    product_dir = product_dir,
    unit_id = unit_id,
    cache_identity = cache_identity,
    summary_lines = summary_lines,
    preview = preview,
    elapsed_seconds = proc.time()[["elapsed"]] - started_at,
    output_contract_version = output_contract_version,
    extra_metadata = list(
      inputs = bensz_file_signatures(input_files),
      parameters = unit_parameters,
      code = bensz_file_signatures(code_files),
      upstream_products = upstream_identities
    )
  )
  message("[PASS] checkpoint committed: ", file.path("products", workflow, unit_stem))
}
