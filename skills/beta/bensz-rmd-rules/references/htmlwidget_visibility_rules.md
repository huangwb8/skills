# HTML 可见性硬规则（htmlwidget/DT/plotly）

当 `.Rmd` 渲染为 HTML 时，`DT::datatable()` 等 **htmlwidget 必须作为 code chunk 的“可见结果”返回**，否则经常会出现“代码块在，但 HTML 不出表/不出图”的情况（尤其当 widget 被 `print()` / `invisible()` 包裹，或在 chunk 中间输出后又继续执行其它表达式）。

## 硬规则

- 任何“需要在 HTML 中展示”的 htmlwidget（含 DT/plotly/leaflet 等），必须满足以下任意一种写法：
  - 方式 A（最推荐）：让 widget 调用成为该 chunk 的最后一个表达式
  - 方式 B（推荐）：先赋值给变量，chunk 最后一行单独写该变量名（返回该对象）
  - 方式 C（多组件）：用 `htmltools::tagList(...)` 作为 chunk 最后表达式，返回多个 widget
- 禁止对“需要展示”的 htmlwidget 使用 `print()` / `invisible()` / `suppressMessages(print(...))` 等包裹写法。
- 如果一个 chunk 里要展示多个 widget，必须用 `htmltools::tagList(...)`（否则通常只会渲染最后一个）。

## 常见错误示例

```r
print(DT::datatable(head(data, 100)))  # 禁止：print() 包裹 widget
```

```r
DT::datatable(head(data, 100))
NULL  # 禁止：widget 不是最后表达式
```

## 正确示例

```r
# 方式 A：最后表达式
DT::datatable(head(data, 100), options = list(scrollX = TRUE, pageLength = 10))
```

```r
# 方式 B：先赋值，最后返回变量
tbl <- DT::datatable(head(data, 100), options = list(scrollX = TRUE, pageLength = 10))
tbl
```

```r
# 方式 C：多个 widget 一次性返回
tbl <- DT::datatable(head(data, 50))
fig <- plotly::ggplotly(ggplot2::qplot(1:10, 1:10))
htmltools::tagList(tbl, fig)
```

## 标准化调用（推荐）

建议使用本 skill 的辅助函数统一渲染交互式表格（并确保“可见性规则”成立）：

```r
# 方式 1：直接使用 DT（推荐用于简单表格）
DT::datatable(head(data, 100), options = list(scrollX = TRUE, pageLength = 10))

# 方式 2：使用辅助函数（推荐用于复杂场景）
source(file.path("templates", "datatables_helper.R"))
render_dt(data, n = 100)  # 注意：必须作为 chunk 最后表达式（或先赋值，最后返回变量）

# 如果你需要在同一 chunk 里继续写其它代码，但仍要确保表格可见，
# 推荐改用 render_dt_output(...) 并把它放在 chunk 末尾（或用于 tagList 组合）。
render_dt_output(data, n = 100)
```

