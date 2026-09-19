# 类与 API 设计

## 何时需要类

当数据必须满足稳定不变量、会经过多个阶段、需要方法分派，或结果必须携带配置和审计信息时，先定义领域对象。一次性纯转换函数不需要为了“形式统一”套类。

## 选择

| 系统 | 适合 | 避免 |
|---|---|---|
| S3 | 轻量值对象、单分派、渐进式 API | 需要严格 slot 或多分派 |
| S4 | 正式 schema、严格 validity、Bioconductor、多分派 | 很小且快速变化的对象 |
| R6 | 可变状态、连接/模型服务/资源句柄 | 可用不可变值对象表达的分析结果 |

已有项目优先沿用既有类系统。若迁移会改变序列化、打印、泛型分派或下游调用，先提出兼容计划。

## 最小契约

1. 构造器只接受语义清楚的输入并创建对象。
2. 验证器集中检查跨字段不变量，错误包含字段和预期。
3. `print()`/`show()` 只输出摘要，不倾倒大对象或敏感信息。
4. 泛型表达用户动作，方法负责类特定实现。
5. 结果对象保留影响复现的参数、seed、输入摘要和产物路径；不要保存无必要的完整原始数据。
6. 内部字段视为私有契约；公开访问通过方法或稳定 accessor。

## S3 骨架

```r
new_job <- function(data, id = "job") {
  x <- structure(list(data = data, id = id, result = NULL), class = "job")
  validate_job(x)
}

validate_job <- function(x) {
  if (!is.data.frame(x$data)) {
    stop("`data` must be a data frame.", call. = FALSE)
  }
  if (!is.character(x$id) || length(x$id) != 1L || is.na(x$id) || !nzchar(x$id)) {
    stop("`id` must be one non-empty string.", call. = FALSE)
  }
  x
}

run_job <- function(x, ...) UseMethod("run_job")
```

需要子类时把最具体类放在 `class` 向量前面，并测试 fallback。不要让构造器执行昂贵计算或自动写文件。

## S4 与 R6 补充

- S4：实现 `setValidity()`，用 `new()` 构造，经 `validObject()` 校验；泛型和方法签名保持最小。
- R6：区分 public/private 字段，明确 `$clone(deep = TRUE)`、finalizer 和外部资源释放；测试多个实例不会共享意外状态。
