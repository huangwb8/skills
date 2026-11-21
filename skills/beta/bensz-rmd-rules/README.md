# bensz-rmd-rules

[English](README_EN.md) · [Skill 指令](SKILL.md)

用 R 围绕值得回答的科学问题做深度分析。`targets` 管理正式计算和增量重建，`renv` 锁定环境；Rmd 用实际代码、图表和内联数字写成完整的论文式报告。

## 快速开始

```text
用 bensz-rmd-rules 分析这份随访数据，交付 Rmd 和 HTML。
我要知道变化有多大、哪些人在比较里、结果还能说明什么。
```

想先试用可运行的合成样例？需要 Python 3.11+、R、Pandoc，以及在宿主 R 库中安装的 `renv`。从本仓库根执行：

```sh
python3 skills/beta/bensz-rmd-rules/scripts/new_project.py demo-rmd
cd demo-rmd
Rscript --vanilla run.R prepare
Rscript --vanilla run.R build
```

打开 `report.html`，看一份用合成数据写成的论文式报告：从摘要、引言和配对方法，到结果、单点影响检查、质量控制和讨论。默认用 Liquid Glass：桌面可使用浮动目录，窄屏可折叠目录，也能放大图片和复制代码。加 `--detail` 可用同一份分析数据生成可搜索的逐单位明细（兼容旧参数 `--dt`）。想换外观可用 `--theme plain` 或 `--theme flatly`。

报告先讲为什么只比较完整配对，再默认展开正式流水线使用的代码；正文用内联 R 带入本次分母、估计和区间，与 DT 汇总表共用展示值。样例 CSV 每行对应一个单位，必须含 `unit`、`before` 和 `after` 三列。区间无法估计时，报告说明原因，并保留仍可计算的平均变化。

## 何时使用

适合从 R 数据出发做分析、生成可复核的科学报告，或针对现有结果改写报告。只想把现成 Rmd 转成 HTML，用 `knit-rmd-html`；主要交付可复用的 R 函数库或包，用 `bensz-r-developer`。

## 输入与产出

说明报告给谁看、需要做什么决定、数据在哪里、有哪些分析或访问限制。Skill 用 targets 与 renv 交付 Rmd、HTML、分析代码、环境锁和复核说明。已有项目可以只改报告，按正式入口核验并复用结果。

每份新分析都写成可复核的论文式报告。主要结果会说明分析理由、展示实际代码、用内联 R 解读本次数字，并交代稳健性、质控和结论边界。参见[完整报告的写法](references/report.md#把完整研究写成论文式报告)。

一次交付多份独立报告时，从项目 README 顶部的阅读索引开始。新报告的 Rmd 与 HTML 使用同样的三级前缀（如 `01.01.01-`）：号码小的先读，相同的前缀越长，报告讨论的问题越接近。索引会标出主报告和可选阅读；只有一份报告时无需编号。参见[多报告的阅读顺序](references/delivery.md#多报告的阅读顺序)。

## 示例

### 基础用法

```text
分析基线与随访的配对测量，交付完整报告。先用日常例子讲清配对，再用公式和代码定义有效配对。
用图说明个体差异，检查少数单位是否左右平均变化，并解释缺失随访对结论的影响。
```

### 进阶用法

```text
用现有 targets 的已验证结果重写报告。先给推荐与例外，
展示决定比较口径的代码，把宽表放入可搜索的附录。只改文案时沿用现有拟合。
```

## 环境与脚本

`00.Environments/` 保存项目环境、锁文件和分析设置。先用 [骨架脚本](scripts/new_project.py) 初始化一个新目录；环境准备在 `run.R prepare`，从锁文件恢复用 `run.R restore`，有意更新依赖才使用 `run.R update-lock`。这些入口的完整用法见 [计算、环境与重建](references/workflow.md)。Skill 当前位于 beta 源，需显式选用。

想改起步示例，可以从 Skill 的[项目骨架](templates/project/)找到主报告和计算入口；[明细附录](templates/detail/)由 `--detail` 加入。[主题和绘图资源](assets/)放在一起，生成器只复制所选的 Liquid Glass 主题，绘图代码按需取用。

## 常见问题

- **能只改报告吗？** 可以。起步项目运行 `Rscript --vanilla run.R report`。若所需的 targets 结果缺失或失效，会提示运行 `Rscript --vanilla run.R build`。
- **HTML 放在哪里？** 默认与 Rmd 同目录同名。图表附件可按项目约定放在 `reports/`；供下游复用的结果可放在 `products/`。
- **报告怎么展示表格？** 正文和附录中的每张表都用 `DT::datatable()`。正文短表可以关闭交互控件；明细表按需开启。HTML 会收到所有嵌入的数据，发布前要核对授权。
- **图表默认用什么风格？** 默认采用适合出版的字号、配色和白底；图内标签用英文，把标题和解读放进图注或正文。单独交付的静态图优先用矢量 PDF。

更多：[推断与报告](references/report.md) · [主题与绘图](references/visuals.md) · [测试与交付](references/delivery.md)
