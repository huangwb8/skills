# benszRdemo

这是 `bensz-r-developer` 的最小 Package 示例，不是可发布业务包。它演示：

- S3 构造器、验证器、打印方法和执行泛型；
- `output.dir` 最终交付与 `cache.dir` 可重建缓存分离；
- 默认拒绝覆盖，最终产物先暂存、成组提交，失败时回滚；
- 生成 manifest，并用 `filelock` 保护并发缓存写入；
- 函数顶部 `if (FALSE)` 手测块；
- 尊重调用方 future plan 的可复现并行；
- testthat 对不变量、文件副作用和串并行等价的验证。

运行：

```r
devtools::document(".")
devtools::test(".")
devtools::check(".", cran = FALSE)
```

实际使用前请更换包名、作者、许可证、领域对象和统计逻辑。
