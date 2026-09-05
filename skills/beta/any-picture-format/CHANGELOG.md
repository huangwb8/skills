# Any Picture Format 变更记录

## [Unreleased]

### Changed（变更）
- 规范化 `SKILL.md` 正文骨架，补齐输入、输出、校验、失败恢复和公共约束摘要；any-picture-format 的既有功能语义保持不变。

## [0.2.0] - 2026-01-21

### Fixed（修复）
- **安全问题**：修复SSRF漏洞，添加URL白名单验证，拒绝内网地址访问
- **安全问题**：修复路径遍历漏洞，使用Path.resolve()规范化路径
- **错误处理**：捕获UnidentifiedImageError，返回友好的用户错误消息
- **代码质量**：修复裸except，使用具体异常类型(OSError, PermissionError)

### Changed（变更）
- **配置简化**：移除transparency_color配置项，硬编码为白色(255, 255, 255)
- **配置简化**：移除naming.batch_pattern配置项（未使用）
- **配置简化**：移除error_handling.error_report_name配置项（未使用）
- **配置简化**：移除error_handling.create_error_report配置项（未使用）
- **策略简化**：移除custom输出策略，只支持new和overwrite
- **跨平台**：临时文件目录使用系统默认(tempfile.gettempdir())，不再硬编码/tmp

### Changed（文档）
- 更新SKILL.md：移除custom策略说明
- 更新SKILL.md：明确说明GIF动画处理使用PIL默认行为
- 更新SKILL.md：移除透明背景颜色配置说明

---

## [0.1.0] - 2026-01-21

### Added（新增）
- 初始化技能，实现图片格式转换核心功能
- 支持本地文件、网络URL、剪贴板三种输入来源
- 支持PNG/JPEG/WEBP/GIF/BMP/TIFF/ICO等格式互转
- 实现单文件转换和批量文件夹转换
- 自动处理透明度（PNG→JPEG时自动替换背景）
- 可配置质量参数、输出策略、文件命名规则
- 提供Python脚本接口（scripts/convert.py）
- 添加验证功能（validate子命令）
