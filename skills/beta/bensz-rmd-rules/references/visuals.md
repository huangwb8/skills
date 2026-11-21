# HTML 主题与图表规范

## HTML 章节编号

新写或修订完整报告时在原入口核对节号。三种示例主题共享 `html_document` 的 `number_sections: true`。用 `## 数据与方法`、`### 研究设计` 等标题层级让 Pandoc 自动编号，标题省去手写数字。YAML 题名单独显示。

已有项目保留主题和入口，按实际输出格式补齐设置。用户或投稿模板要求关闭时，在 `output.html_document` 下设 `number_sections: false`，或用等效选项。[成品验收](delivery.md#先核对结果再读-html)

## Liquid Glass HTML

骨架默认 Liquid Glass，含半透明卡片、系统深色模式、桌面动态/常驻目录、窄屏折叠目录、居中可放大的图、代码复制和视图状态恢复。禁用字体连字以原样显示 R 的 `<-`。可选 `--theme plain` 或 `--theme flatly`，已有项目保留用户选择。

要为已有报告启用，复制 [Liquid Glass 资源](../assets/liquid-glass/)到 `templates/liquid-glass/`，合并配置并保留原有公式、代码选项。

```yaml
output:
  html_document:
    theme: default
    toc: true
    toc_float: true
    toc_depth: 3
    highlight: tango
    code_folding: show
    css: templates/liquid-glass/liquid_glass_theme.css
    includes:
      after_body: templates/liquid-glass/liquid_glass_lightbox.html
```

CSS 用 `css`，交互用 `includes.after_body`。独立 knit 时路径相对 Rmd，例如 `../templates/liquid-glass/…`。骨架 `run.R` 也可从项目根定位。实际打开 HTML 检查桌面悬停目录、窄屏折叠、放大图片、复制代码、DT 可读性及启用的搜索和局部横向滚动。自定义主题再查深色和减少动态效果的系统偏好。

## 图表语言

报告内外的图表默认英文，涵盖轴、图例、分面、注释、图注、表题、表头、行标签、状态和表注。类别优先用惯用英文，基因和蛋白保留标准符号。报告题名、摘要、标题与正文按用户指定语言，默认随任务语言。

按用户要求调整图表标签和说明。例程的 `params.plot_language`、`params.table_language` 各自默认 `en`，可设 `zh`。中文图优先用可用的 Cairo PNG 设备，复核实际字体能显示汉字和科学符号。

## 出版级绘图默认值

按实际展示或打印尺寸检查可读性。图内通常省略标题和副标题，把必要标题放在图注或报告结构中。

| 场景 | 起步样式与调整 |
| --- | --- |
| 通用 | 白底、无或弱网格。用 Arial/Helvetica 或 `sans`。轴标单位，图例放外侧，配合点形、线型或直标区分类别 |
| ggplot2 | 刻度约 10 pt、图例约 9 pt，数据线约 0.8–1.0、轴线约 0.5。长标签先换行、旋转或调画布，过密再减刻度或分面，按问题留重点标签 |
| ComplexHeatmap | 行列标签 8–10 pt，连续色带可用 viridis，有意义的零点可用零中心发散色带。密集矩阵减少标签并保留完整映射 |
| plotly | 轴标题约 14 px、刻度约 12 px、图例约 11 px、数据线约 2–3 px。需查询明细时才用交互，检查悬停、窄屏和客户端收到的数据范围 |

同一变量的颜色、单位、编码尽量一致。分类可用 Nature 风格配色，连续量用 viridis 等有序色带。检视色觉差异、灰度和浅底对比，避免彩虹色及只靠红绿区分。按需复制模板并声明用包，plotly 示例先载入配色。[ggplot2 主题](../assets/plots/nature_theme.R) · [分类配色](../assets/plots/nature_colors.R) · [ComplexHeatmap 示例](../assets/plots/complexheatmap_template.R) · [plotly 示例](../assets/plots/plotly_template.R)

## 导出和检查

报告可直接嵌图。独立静态图优先由正式入口导出矢量 PDF，投稿要求位图时按指定尺寸和分辨率导出。在任务工作区打开 JPG/PNG 预览，实查长标签、裁剪、希腊字母及中英文混排。已安装 Poppler 时可用以下命令，先建输出目录。

```sh
pdftoppm -jpeg -r 200 -f 1 -l 1 -singlefile "reports/Figure 1.pdf" ".bensz-api/task-YYYYMMDD-HHMM-example/bensz-rmd-rules/output/figure-1"
```

检查轴、刻度、单位、图例、对比度、字体、画布和叠压；正文解释对象、方向或对比、例外与不确定性。交互图交付可打开的 HTML 并实测操作。浏览器和预览工具只用于审阅。
