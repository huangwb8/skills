# md-to-word - 变更日志

本文档记录 `md-to-word` 技能的重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Changed（变更）
- 规范化 `SKILL.md` 正文骨架，补齐输入、输出、校验、失败恢复和公共约束摘要；md-to-word 的既有功能语义保持不变。

## [0.4.0] - 2026-01-13

### Added（新增）

- 新增 `scripts/fix_template_namespace.py` 工具脚本，用于检测和修复自定义 Word 模板的命名空间问题
- 在 `scripts/md_to_word.py` 中自动添加 `--markdown-headings=atx` 参数，提高 Pandoc 兼容性
- 更新 SKILL.md 文档，新增"Word 兼容性问题与解决方案"章节，详细说明两个主要问题和解决方案

### Fixed（修复）

- **修复 Word 警告问题**：彻底解决 Word 打开文档时提示"无法读取的内容"的问题
  - 根本原因：内置模板（cn-modern、compact）使用非标准的 `ns0:` 命名空间前缀，而不是标准的 `w:` 前缀
  - 解决方案：使用 Pandoc 重新生成所有内置模板，确保使用标准 OOXML 命名空间
  - 验证结果：所有模板和生成的 Word 文件 `ns0:` 使用次数为 0，`w:` 使用次数正常

### Changed（变更）

- 更新版本号至 0.4.0，同步更新 config.yaml 和 SKILL.md 的 metadata.version
- 更新 description 描述，强调内置模板已修复命名空间兼容性问题

---

## [0.3.0] - 2026-01-12

### Added（新增）

- 重构图片处理工作流，使用 `.md-to-word/` 隐藏目录统一管理中间产物
- 支持所有图片格式（PNG/JPG/GIF/BMP/WebP）智能转换
- 智能转换非 RGB 模式图片（RGBA/P/PA/LA → RGB）
- 默认保留工作目录便于增量转换
- 新增 `--clean` 选项主动清理工作目录

---

## [0.2.0] - 2026-01-12

### Fixed（修复）

- 修复图片嵌入问题：优化 `_resource_path_for()` 函数，确保 Pandoc 能正确找到相对路径的本地图片
- 资源路径现包含：Markdown 文件所在目录、父目录、当前工作目录，支持 `raw/` 等子目录结构

### Changed（变更）

- 简化代码架构：删除不必要的远程图片处理模块（image_downloader.py、md_preprocessor.py、docx_validator.py）
- 专注于 Pandoc 原生能力，通过正确配置 `--resource-path` 解决图片嵌入问题

---

## [0.1.0] - 2026-01-12

### Added（新增）

- 初始化 `md-to-word` 技能：基于 Pandoc 将 Markdown 批量转换为 Word（.docx）。
- 内置 3 个 reference.docx 模板（`default` / `cn-modern` / `compact`），并支持 `--reference-doc` 自定义模板。
- 提供确定性脚本 `scripts/md_to_word.py`：默认不覆写输出、支持输出目录与 dry-run。
- 脚本增强：`--list-templates`、`--output-suffix`（多模板输出不覆盖）、`--output`（单文件显式输出路径）。
- 脚本支持 `--config` 读取 `config.yaml` 的关键约束与默认参数（max_inputs、扩展名白名单、pandoc 默认参数、templates）。
