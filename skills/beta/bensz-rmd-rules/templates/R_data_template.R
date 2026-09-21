# R/analysis_functions.R - target 调用的计算函数
# 复制到项目 R/；_targets.R 通过 tar_source("R") 自动发现本目录。
# 函数返回完整结果，不写 SUCCESS、identity hash 或自定义 checkpoint。

prepare_data <- function(input_file) {
  stopifnot(length(input_file) == 1L, file.exists(input_file))
  data <- utils::read.delim(input_file, check.names = FALSE)
  # 在这里写真实的数据整理；保留完整、未按报告阈值截断的结果。
  data
}

analyze_data <- function(prepared_data) {
  stopifnot(is.data.frame(prepared_data))
  # 在这里写模型/统计计算；报告层 Top N、阈值和配色不要放在这里。
  prepared_data
}

write_scientific_product <- function(result, path) {
  # 仅当结果需要人工审阅、下游复用或正式交付时导出 products/。
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  saveRDS(result, path)
  path
}
