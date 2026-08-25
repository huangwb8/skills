# Knit Rmd HTML

当前版本：`0.1.1`。

这个 skill 用来把 `.Rmd` 文件稳定地渲染成 HTML，适合仓库里的高频 R Markdown 报告输出；如果你想生成 PDF、Word 或处理普通 Markdown，就不该直接用它。

## 用法

### 最推荐用法

```text
请使用 knit-rmd-html skill 将这个 R Markdown 文件渲染成 HTML。
输入：`/path/to/report.Rmd`
输出：对应的 `.html` 文件，默认输出到同目录
```

### 进阶用法

```text
请使用 knit-rmd-html skill 渲染这个 R Markdown 文件。
输入：`/path/to/report.Rmd`
输出：指定输出位置的 HTML 文件
另外，还有下列参数约束：
- 输出路径：`/path/to/out/report.html`
- 缺少 pandoc 时允许自动安装：是
- 日志尽量安静：是
```

## 能做什么

- 使用 Python 包装层调用 `rmarkdown::render()`，减少环境差异带来的失败。
- 缺少 `pandoc` 时可自动引导安装。
- Windows 下兼容 Pandoc ZIP 的根目录与 `bin/` 两类布局，并识别 `pandoc.exe`。
- Rscript 输出固定按 UTF-8 解码，不依赖中文控制台的 GBK locale。
- 通过正确设置 `knit_root_dir`，让 Rmd 内相对路径更稳定。
- 适合本仓库内“把 Rmd 可靠地 knit 成 HTML”的固定场景。
- 不适合替代通用报告系统或其它输出格式转换器。

## 使用示例

### 示例 1：渲染单个 Rmd

```text
请使用 knit-rmd-html skill 将这个 R Markdown 文件渲染成 HTML。
输入：`analysis/report.Rmd`
输出：`analysis/report.html`
```

### 示例 2：指定输出文件

```text
请使用 knit-rmd-html skill 渲染这个文件。
输入：`analysis/report.Rmd`
输出：`./outputs/report-final.html`
```

### 示例 3：要求失败即报错

```text
请使用 knit-rmd-html skill 渲染这个 Rmd。
输入：`report.Rmd`
输出：HTML 文件
另外，还有下列参数约束：
- 不自动安装依赖：是
- 输出日志：简洁
```

## 输出

- 默认输出：与输入 `.Rmd` 同目录下的同名 `.html`。
- 可以通过参数显式指定输出路径。
- 缺少 `pandoc` 时可自动补齐到本地用户目录。
- 需要 `Rscript` 可用；否则无法真正执行渲染。

## 配置

- 版本号由 `config.yaml:skill_info.version` 统一管理，高频设置通过命令行参数控制。
- 最常用参数：
  - `-o` / `--output`
  - `--pandoc-version`
  - `--no-install`
  - `--quiet`

## 备选用法（脚本/硬编码）

如果你已经在仓库里，直接运行脚本通常是最稳定的方式。

### 基础渲染

```bash
python3 knit-rmd-html/scripts/knit_rmd_html.py report.Rmd
```

### 指定输出文件

```bash
python3 knit-rmd-html/scripts/knit_rmd_html.py \
  report.Rmd \
  -o outputs/report.html
```

### 控制依赖安装与日志

```bash
python3 knit-rmd-html/scripts/knit_rmd_html.py \
  report.Rmd \
  --no-install \
  --quiet
```

## 常见问题

### Q：为什么这个 skill 不直接让我写 R 命令？

A：因为它的价值之一就是帮你把环境检测、`pandoc` 补齐和稳定渲染流程包装好。

### Q：会自动安装什么？

A：主要是缺失的 `pandoc`。真正的渲染仍然依赖本地 `Rscript` 和 `rmarkdown` 运行环境。

### Q：为什么输出默认在原文件旁边？

A：这是最符合直觉、也最不容易弄丢结果的默认行为。

### Q：它能生成 PDF 吗？

A：这个 skill 的职责是 `.Rmd -> HTML`。如果你要别的格式，应该走其他专门技能或工具链。
