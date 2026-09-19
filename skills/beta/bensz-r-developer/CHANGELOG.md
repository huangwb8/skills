# Changelog

## Unreleased

### Added

- 新增面向 R 函数与 Package 的类驱动开发工作流。
- 新增输出/缓存、并行性能、类与 API、Package 工具链参考。
- 新增可运行的 `benszRdemo` Package 示例与触发测试用例。

### Changed

- 经一轮 `auto-test-skill` 优化 demo：限制安全文件名，补齐对象与数值参数验证，并拒绝输出/缓存目录嵌套。
- 缓存加入 schema 身份、损坏条目隔离与 `filelock` 并发锁；多文件输出改为预检、暂存和可回滚提交，并增加 manifest。
- 测试覆盖恶意 ID、损坏缓存、部分输出防护与真实 multisession 串并行等价。
- B 轮复核将格式版本收敛为单一常量，并显式捕获缓存 schema 供 future worker 使用，避免跨进程隐式全局依赖。
