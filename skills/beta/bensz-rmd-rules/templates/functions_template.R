# {主脚本名}_functions.R
# 用途：[简要说明函数集合的用途]
#
# 本文件包含 {主脚本名}.R 和 {主脚本名}.Rmd 专用的辅助函数
# 使用 `if (TRUE) { ... }` 包裹，避免污染全局环境

if (TRUE) {

  # ==== 数据处理函数 ====

  # .{主脚本名缩写}_prepare_data
  # 用途：[简要说明]
  # 参数：
  #   - data: 输入数据
  #   - ...: 其他参数
  # 返回：处理后的数据
  .{主脚本名缩写}_prepare_data <- function(data, ...) {
    # 具体实现
    # ...

    return(result)
  }

  # ==== 可视化函数 ====

  # .{主脚本名缩写}_plot_xxx
  # 用途：[简要说明]
  # 参数：
  #   - data: 输入数据
  #   - ...: 其他参数
  # 返回：ggplot 对象
  .{主脚本名缩写}_plot_xxx <- function(data, ...) {
    # 具体实现
    # plot <- ggplot(data, ...) + ...

    return(plot)
  }

  # ==== 统计检验函数 ====

  # .{主脚本名缩写}_test_xxx
  # 用途：[简要说明]
  # 参数：
  #   - data: 输入数据
  #   - ...: 其他参数
  # 返回：检验结果
  .{主脚本名缩写}_test_xxx <- function(data, ...) {
    # 具体实现
    # result <- test_func(...)

    return(result)
  }

}
