# datatables_helper.R
# 标准化 DT::datatable() 调用的辅助函数
#
# 使用方式：
#   source(file.path("templates", "datatables_helper.R"))
#   render_dt(data, n = 100)
#
# 注意：此函数假设 DT 包已通过 00.Environment.R 中的 luckyBase::Plus.library("DT") 加载
# 注意：在 Rmd 中要“显示”表格，render_dt(...) 必须作为 chunk 的最后表达式（或先赋值，最后返回变量）。

if (TRUE) {
  #' 标准化渲染交互式表格
  #'
  #' @param data 数据框或 tibble
  #' @param n 显示的行数（默认 100）
  #' @param scrollX 是否启用横向滚动（默认 TRUE）
  #' @param pageLength 每页显示行数（默认 10）
  #' @return DT::datatable 对象
  #' @examples
  #'   render_dt(head(iris, 50))
  #'   render_dt(mtcars, n = 200, pageLength = 20)
  render_dt <- function(data, n = 100, scrollX = TRUE, pageLength = 10) {
    DT::datatable(
      head(data, n),
      options = list(
        scrollX = scrollX,
        pageLength = pageLength
      )
    )
  }

  #' 以“可见结果”方式输出交互式表格（用于避免 HTML 不出表）
  #'
  #' 用法：让 render_dt_output(...) 成为 chunk 的最后表达式；
  #' 或者用于组合多个 widget：htmltools::tagList(render_dt_output(...), other_widget)
  render_dt_output <- function(data, n = 100, scrollX = TRUE, pageLength = 10) {
    htmltools::tagList(
      render_dt(data = data, n = n, scrollX = scrollX, pageLength = pageLength)
    )
  }
}
