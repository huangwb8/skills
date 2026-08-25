# 图表/表格解读覆盖判定标准（硬编码）

本文件定义 `scripts/check_figure_table_interpretation.py` 的“覆盖检验”口径：**每个可见输出（图/表）都必须有对应的解读文本**。

## 检验目标

- 解决“有图/表、无解读”的漏项（Coverage）。
- 不替代“解读质量检查”（Quality），后者由 `scripts/check_interpretation_quality.py` 提供启发式提示。

## 什么算作“需要解读的输出”

脚本通过静态模式识别以下 R 代码块为“输出块”（可在 `config.yaml:figure_interpretation_check.check_patterns` 调整）：

- 图：`ggplot(...)` / `plot(...)` / `Heatmap(...)` / `pheatmap(...)` / `ggsave(...)` / `pdf(...)` / `png(...)` 等
- 表：`knitr::kable(...)` / `DT::datatable(...)` / `gt::gt(...)` / `flextable::flextable(...)` 等

以下情况默认**不纳入覆盖检验**（视作“不可见/不需要解读”）：

- chunk 设置了 `eval=FALSE` 或 `include=FALSE`
- chunk 设置了 `results='hide'`（通常隐藏打印输出）
- chunk 设置了 `interp_check=FALSE`（手动豁免：用于“命中输出模式但确实不产生可见输出”的少数情况）

## 什么算作“有解读”

对每个“输出块”，其后（默认 50 行内，见 `config.yaml:figure_interpretation_check.max_distance_lines`）必须出现 Markdown 正文（非代码块），并满足：

1. **长度门槛**（避免一句话套话）  
   - 含中文：至少 100 个中文字符（默认，可用 CLI 参数覆盖）  
   - 纯英文：至少 50 个英文单词（默认，可用 CLI 参数覆盖）

2. **解释性证据元素**（默认至少 2 个）  
   典型元素：展示/差异/显著性（p/FDR/q）/提示与推论等。

3. **四层解读标记（推荐）**  
   默认要求正文出现“数据描述/统计见解/领域见解/局限”等关键词之一（可在 `config.yaml:figure_interpretation_check.check_patterns.interpretation_markers` 调整）。

可选更严格模式：强制要求正文显式引用 “Figure/图/Table/表 N”（见脚本 `--require-reference` 或 `config.yaml:figure_interpretation_check.require_reference`）。

## 运行方式（交付前强制）

```bash
python3 bensz-rmd-rules/scripts/check_figure_table_interpretation.py your_report.Rmd --strict
python3 bensz-rmd-rules/scripts/check_interpretation_quality.py your_report.Rmd
```
