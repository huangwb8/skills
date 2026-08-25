---
name: knit-rmd-html
description: Knit/render R Markdown (.Rmd) to HTML reliably in this repo (auto-bootstrap pandoc, set correct knit_root_dir, and run rmarkdown::render via a Python wrapper).
metadata:
  author: Bensz Conan
  keywords:
    - knit-rmd-html
---

# Knit Rmd → HTML（项目高频场景）

版本由 `config.yaml:skill_info.version` 统一管理。

## BenszAPI 任务工作区

本 Skill 的新任务中间文件统一写入 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/{skill名}/input|output|log/`。同一任务复用一个任务根目录；多 Skill 协作才创建 `shared/`。正式交付物不写入该目录，历史隐藏目录只允许显式兼容读取、迁移或清理。

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求“report bensz skills bugs”等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

当用户说"knit 出 html / render Rmd / 生成 HTML 报告"时使用本 skill。

## 直接用法

- 在仓库根目录执行：
  - `python3 skills/knit-rmd-html/scripts/knit_rmd_html.py <input>.Rmd`
  - 输出默认写到 `<input>.Rmd` 同目录：`<input>.html`

## 常用参数

- 指定输出文件：
  - `python3 skills/knit-rmd-html/scripts/knit_rmd_html.py <input>.Rmd -o <output>.html`
- 指定 pandoc 版本（默认 `3.8.3`）：
  - `python3 skills/knit-rmd-html/scripts/knit_rmd_html.py <input>.Rmd --pandoc-version 3.8.3`
- 不自动安装依赖（只做检测；缺什么就报错）：
  - `python3 skills/knit-rmd-html/scripts/knit_rmd_html.py <input>.Rmd --no-install`
- 静默渲染输出：
  - `python3 skills/knit-rmd-html/scripts/knit_rmd_html.py <input>.Rmd --quiet`

## 设计要点（为何这样做）

- **不依赖 R 写脚本**：外层用 Python 做编排与环境自检；真正的 knit 仍由 `rmarkdown::render()` 执行。
- **自动补齐 pandoc**：若系统无 `pandoc`，自动下载安装到 `~/.local/pandoc/` 并将 `~/.local/bin` 放到子进程 `PATH` 前面。
- **兼容 Windows ZIP**：安全解压后递归寻找唯一的 `pandoc` / `pandoc.exe`，兼容根目录与 `bin/` 布局并拒绝歧义结果。
- **输出编码稳定**：Rscript 日志始终按 UTF-8 解码并保留真实退出码，不依赖 Windows 控制台 locale。
- **相对路径更稳**：用 `knit_root_dir=dirname(input)`，确保 Rmd 内 `source("xxx.R")` 等相对路径在 knit 时仍可用。

## 工作原理

1. **环境检测**：检查 `pandoc` 和 `Rscript` 是否在 PATH 中
2. **自动安装**：若缺少 pandoc，根据平台自动下载对应版本到 `~/.local/pandoc/`
3. **渲染执行**：通过 R 的 `rmarkdown::render()` 执行 knit
4. **输出定位**：默认输出到输入文件同目录，可通过 `-o` 参数指定
