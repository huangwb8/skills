# R Package 工作流

## 建立与理解结构

新包用 `usethis::create_package()`，已有包先读 `DESCRIPTION`、`NAMESPACE`、`R/`、`tests/testthat/`、`src/`、vignettes 和 CI。包名、导出 API、最低 R 版本和许可证属于公共契约，不随意更改。

## 开发闭环

```r
usethis::use_r("feature")
usethis::use_testthat()
usethis::use_test("feature")
devtools::document()
devtools::load_all()
devtools::test()
devtools::check(cran = FALSE)
```

- roxygen2 是函数文档与 `NAMESPACE` 的源；不要同时手改生成段。
- `Imports` 只放运行时依赖，代码用 `pkg::fun()` 或精确 `@importFrom`。
- `Suggests` 中的可选能力用 `requireNamespace()` 与测试 skip 管理。
- `testthat` 覆盖构造/验证、公开方法、错误、文件副作用、缓存、RNG、串并行等价。
- 用 `withr` 隔离 options、环境变量、工作目录和临时文件；测试不写用户目录。
- `renv` 可锁定开发/应用环境，但不能替代 `DESCRIPTION` 声明包依赖。

## 文档与示例

公开函数说明参数单位、维度、缺失值、返回类、副作用和错误。`@examples` 必须轻量、离线、确定；昂贵流程用 `\dontrun{}`，核心行为仍由测试覆盖。函数内 `if (FALSE)` 块用于维护者手测，可比 `@examples` 更贴近调试，但不得含私人路径。

## 检查结果

交付前运行 `devtools::check()`；错误必须清零。warning 通常必须清零，note 逐条判断并记录。涉及 compiled code 时在目标 OS/R 版本矩阵验证，检查注册、符号可见性、线程安全和 sanitizer/valgrind 条件。

## 版本与兼容

公开签名、类布局、序列化格式或默认副作用变化时，更新测试、README、NEWS/CHANGELOG 和迁移说明。优先用 deprecation 周期替代突然删除；读取旧对象时明确 schema/version 升级路径。

