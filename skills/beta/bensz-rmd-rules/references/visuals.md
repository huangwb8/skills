# HTML 主题与图表规范

## Liquid Glass HTML

新项目的报告骨架默认启用 Liquid Glass。主题提供半透明卡片、系统深色模式、桌面动态/常驻目录、窄屏折叠目录、居中图片和点击放大、代码复制和视图状态恢复。代码样式关闭字体连字，使 R 的 `<-` 保持原样。需要其它外观时用 `--theme plain` 或 `--theme flatly`；已有项目保留用户选择。

要给已有报告启用主题，把 Skill 的 [Liquid Glass 资源](../assets/liquid-glass/)复制到项目的 `templates/liquid-glass/`，合并以下 Rmd 配置，保留项目原有的公式和代码选项：

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

CSS 走 `css`，交互文件走 `includes.after_body`。从子目录独立 knit 时，路径相对于 Rmd（如 `../templates/liquid-glass/…`）；骨架的 `run.R` 也可从项目根定位上面两条默认路径。先打开真实 HTML 检查桌面悬停目录、窄屏折叠、图片放大和复制代码；检查所有 DT 表的可读性，并实际操作明细表启用的搜索和局部横向滚动。自定义主题时检查深色模式和减少动态效果的系统偏好。

## 出版级绘图默认值

以实际展示或打印尺寸下的可读性为准。轴标题、图例、分面和必要注释默认用英文；类别有惯用英文时优先使用，基因和蛋白保留标准符号。一般不在图内重复写标题或副标题，必要的标题留在图注和报告结构里。用户明确需要中文时，可在 Rmd 用 `params.plot_language: zh` 切换图内标签，并核查图形设备实际使用的字体能显示汉字和科学符号。

| 场景 | 起步样式 | 按图调整 |
| --- | --- | --- |
| 通用 | 白底、无或弱网格、无衬线字体；Arial/Helvetica 不可用时用 `sans` | 轴清楚标单位；图例放外侧；颜色不足以区分类别时配合点形、线型或直接标注 |
| ggplot2 | 轴刻度约 10 pt、图例约 9 pt；数据线约 0.8–1.0、轴线约 0.5 | 长标签先换行、旋转或调整画布；过密时减少刻度或分面，重点标签按科学问题选择 |
| ComplexHeatmap | 行列标签 8–10 pt；连续数据用感知顺序明确的色带（如 viridis） | 有含义的零点可用以零为中心的发散色带；矩阵很密时减少标签，并保留可核对的完整映射 |
| plotly | 轴标题约 14 px、刻度约 12 px、图例约 11 px，数据线约 2–3 px | 只有需要查询明细时才用交互；检查悬停信息、窄屏和客户端接收的数据范围 |

同一变量在不同图里尽量保持颜色、单位和编码一致；分类可从 Nature 风格配色起步，连续量用 viridis 等有序色带。检查色觉差异、灰度和浅底对比，避免彩虹色与仅靠红绿区分。可按项目需要复制 [ggplot2 主题](../assets/plots/nature_theme.R)、[分类配色](../assets/plots/nature_colors.R)、[ComplexHeatmap 示例](../assets/plots/complexheatmap_template.R)或 [plotly 示例](../assets/plots/plotly_template.R)到项目并显式声明所用的包；plotly 示例先加载配色文件。

## 导出和检查

报告内可直接嵌图。要单独交付静态图，优先用正式入口输出矢量 PDF；期刊要求位图时，按指定尺寸和分辨率导出。长标签、裁剪、希腊字母和中英文混排要检查实际文件，在当前任务工作区生成并打开 JPG/PNG 预览。以下是已安装 Poppler 时的单页预览示例（先创建输出目录）：

```sh
pdftoppm -jpeg -r 200 -f 1 -l 1 -singlefile "reports/Figure 1.pdf" ".bensz-api/task-YYYYMMDD-HHMM-example/bensz-rmd-rules/output/figure-1"
```

检查轴、刻度、单位、图例、对比度、字体、画布和叠压；正文说明图画的对象、方向或对比、关键例外与不确定性。交互图以可打开的 HTML 交付，验证真实操作；浏览器和预览工具只用于审阅。
