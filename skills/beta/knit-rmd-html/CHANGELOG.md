# knit-rmd-html - 变更日志

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与语义化版本规范。

## [Unreleased]

### Fixed（修复）

- 修复 Windows Pandoc ZIP 布局并不固定为 `bin/pandoc` 的问题：解压后递归发现唯一的 `pandoc` / `pandoc.exe`，拒绝路径穿越、缺失和歧义结果，并保留 `.exe` 文件名供 Windows `PATH` 发现。
- 修复 Windows 中文 locale 下 Rscript 的 UTF-8 输出被按 GBK 解码的问题：子进程输出统一使用 UTF-8 并以 replacement 策略保留返回码和可读日志。

## [0.1.0]

### Added（新增）

- 初始化 R Markdown 到 HTML 的 Python 渲染入口，并支持缺少 Pandoc 时按固定版本安装。
