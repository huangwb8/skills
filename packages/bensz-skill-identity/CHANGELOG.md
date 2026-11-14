# Changelog

## [Unreleased]

## [1.0.0] - 2026-11-14

### Added

- README 原理流程图：展示稳定身份、签名发行、显式信任与有限撤销检查及严格安装；图片经 PicGo 上传，文档仅保留图床链接。已完成视觉复核、远程原图摘要及 Markdown 链接检查。

### Changed

- 按用户指定版本将 Python 发行元数据对齐至 1.0.0；协议继续使用 v1，不改变 API、签名域、信任或安装判定。
- 双语 README 对齐公开 API/CLI，补充 PyPI 安装、能力输出、包版本查询与开发测试入口；发行包包含 MIT 许可证及项目链接。
- 统一展示名为 Bensz Skill Identity（BSI），使用 `bsi` CLI，与同作者的 Bensz Skill Kernel（BSK）/ `bsk` 对应；Python 发行名为 `bensz-skill-identity`。

## [0.1.0] - 2026-11-14

### Added

- 独立身份声明、受签发行、显式信任与有限撤销、精确依赖锁定 API/CLI。
- 完整文件集合、字节和执行属性核对，路径/文件类型与输入限额。
- 持久安全修订、统一状态锁、可恢复严格安装与实际安装重验。
- 公共固定签名向量、库测试、公开安装入口与隔离 wheel 验证。

当前最高保证为 `files_verified`；无宿主加载或工具执行绑定。验收范围见仓库正式验证记录。
