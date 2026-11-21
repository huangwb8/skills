# bensz-rmd-rules

[English](README_EN.md) · [Skill 指令](SKILL.md)

用 Rmd 围绕值得回答的科学问题展开论证：日常例子给读者直觉，公式和代码明确比较口径，图表和文字解释证据支持什么。小分析直接用 Rmd；昂贵计算用 targets，修改报告时复用仍有效的结果。

## 快速开始

```text
用 bensz-rmd-rules 分析这份随访数据，交付 Rmd 和 HTML。
我要知道变化有多大、哪些人在比较里、结果还能说明什么。
```

想先试用可运行的合成样例？需要 Python 3.11+、R、Pandoc，以及在宿主 R 库中安装的 `renv`。从本仓库根执行：

```sh
python3 skills/beta/bensz-rmd-rules/scripts/new_project.py simple demo-rmd
cd demo-rmd
Rscript --vanilla run.R prepare
Rscript --vanilla run.R build
```

打开 `report.html`，看一个通勤例子如何引出配对差的公式，再用变化分布和汇总表解释合成数据。把 `simple` 改成 `complex` 可体验 targets；加 `--dt --theme flatly` 可看到带搜索和横向滚动的长表及可选主题。

## 何时使用

适合从 R 数据出发做分析、生成可复核的科学报告，或针对现有结果改写报告。只想把现成 Rmd 转成 HTML，用 `knit-rmd-html`；主要交付可复用的 R 函数库或包，用 `bensz-r-developer`。

## 输入与产出

说明报告给谁看、需要做什么决定、数据在哪里、有哪些分析或访问限制。Skill 会选择符合计算成本的入口，给出 Rmd、HTML、必要的分析代码、环境锁和复核说明。已有项目可以只重写报告，按已有正式入口核验其结果。

## 示例

### 基础用法

```text
给组会做一页配对分析。先用日常例子讲清配对，再用公式和代码定义有效配对。
用图说明平均变化背后的个体差异，并解释缺失随访对结论的影响。
```

### 进阶用法

```text
用现有 targets 的已验证结果重写报告。先给推荐与例外，
展示决定比较口径的代码，把宽表放入可搜索的附录。只改文案时沿用现有拟合。
```

## 环境与脚本

`00.Environments/` 保存项目环境、锁文件和分析设置。先用 [骨架脚本](scripts/new_project.py) 初始化一个新目录；环境准备在 `run.R prepare`，从锁文件恢复用 `run.R restore`，有意更新依赖才使用 `run.R update-lock`。这些入口的完整用法见 [计算、环境与重建](references/workflow.md)。Skill 当前位于 beta 源，需显式选用。

## 常见问题

- **能只改报告吗？** 可以。起步项目运行 `Rscript --vanilla run.R report`。complex 若缺结果或结果失效，会提示运行 `Rscript --vanilla run.R build`。
- **HTML 放在哪里？** 默认与 Rmd 同目录同名。图表附件可按项目约定放在 `reports/`；供下游复用的结果可放在 `products/`。
- **每份报告都要用 DT 吗？** 静态小表更适合正文。需要查明细时再启用 DT；HTML 会收到所有嵌入的数据，发布前要核对授权。

更多：[推断与报告](references/report.md) · [测试与交付](references/delivery.md)
