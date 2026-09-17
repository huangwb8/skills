# 多分析单元示例

## 示例 A：一个低成本报告

| 编号 | 目的 | 上游 | 产品 | 报告 |
| --- | --- | --- | --- | --- |
| `01.00.00` | 描述样本与缺失 | `raw/sample.tsv` | 不持久缓存 | `01.00.00. 数据概览.html` |

该任务可只创建 Rmd/HTML。无需为了形式完整生成 `.R`、`_functions.R` 或 checkpoint。

## 示例 B：多阶段昂贵分析

| 编号 | 目的 | 上游 | 缓存 | 报告 |
| --- | --- | --- | --- | --- |
| `01.00.00` | 清洗并统一数据字典 | `raw/` | 完整对象 + 预览 | 无 |
| `02.00.00` | 拟合耗时模型 | `01.00.00` | 模型 + 全量预测 + 摘要 | 无 |
| `03.00.00` | 生成论文结果 | `01.00.00`, `02.00.00` | 不缓存展示层 | HTML/PDF/表格 |

修改 `03.00.00` 的 q 阈值、Top N 或配色只重渲染报告。修改 `02.00.00` 的模型参数使 02 及依赖它的 03 失效，01 仍命中缓存。

## 示例 C：从失败步骤恢复

日志仍按编号遍历：

```text
[CACHE HIT] 01.00.00. 数据整理
[CACHE HIT] 02.00.00. 特征计算
[RUN] 03.00.00. 模型拟合 - missing SUCCESS
[RUN] 04.00.00. 综合报告 - upstream identity changed
```

失败步骤没有 `SUCCESS`；前序有效产品保留。不要跳过编号遍历直接从磁盘猜测“最近文件”。

## 报告层筛选

```r
# 完整产品由上游 .R 生成；阈值只影响当前报告。
all_results <- readRDS(file.path("products", "main", "02.00.00. 模型拟合", "main.rds"))
report_results <- all_results |>
  dplyr::filter(q_value <= params$q_cutoff) |>
  dplyr::slice_head(n = params$top_n)
```

正式图写入带编号前缀的 `reports/figures/`，JPG 自检预览写入本轮 `.bensz-api` 任务目录。
