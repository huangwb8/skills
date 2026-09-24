# Liquid Glass Theme 使用指南

本主题为 R Markdown HTML 提供 glassmorphism 风格：半透明/模糊卡片、渐变与多层阴影、自动深色模式、响应式目录、图片 Lightbox、代码复制按钮和默认居中图片。默认无无限循环动画，避免复制/选中文本抖动；目录支持桌面动态/静态浮动和窄屏折叠。

## 快速开始

将 `templates/liquid_glass_theme.css` 与 `templates/liquid_glass_lightbox.html` 放入项目 `templates/`，或运行：

```bash
python3 /path/to/bensz-rmd-rules/scripts/bootstrap_liquid_glass.py --with-env
```

在 Rmd YAML 中使用：

```yaml
output:
  html_document:
    toc: true
    toc_float: true
    theme: default
    highlight: tango
    code_folding: show
    includes:
      after_body: "templates/liquid_glass_lightbox.html"
    css: "templates/liquid_glass_theme.css"
```

`theme: default` 兼容 `toc_float`；`css` 加载主题；`after_body` 启用图片放大、代码复制和视图状态保持。不要用 `includes.in_header` 直接 include CSS，否则 Pandoc 可能把 CSS 当正文。

渲染：

```bash
python3 skills/knit-rmd-html/scripts/knit_rmd_html.py your_report.Rmd
```

## 目录与交互

- 桌面（>1024px）：动态模式以左上角小圆点展开；可切换静态常驻，偏好写入浏览器存储。
- 窄屏（≤1024px）：目录回到顶部并折叠为 sticky 卡片；点击展开，跳转后收起并处理标题偏移。
- 代码块：启用 `after_body` 后在右上角显示 Copy；现代浏览器用 Clipboard API，旧浏览器或 `file://` 降级为 `execCommand`。主题会关闭代码字体连字，确保 R 的 `<-` 等多字符运算符保持源码字面形态，不被合成箭头字形。
- Lightbox：点击图片放大，Esc/空白处关闭；`Ctrl/Cmd + (+/-/0)` 可用页面缩放，刷新后尽量恢复位置。

## 视觉与自定义

主题使用 `backdrop-filter`、半透明背景和 CSS custom properties；默认支持系统深色模式。常用变量：

```css
:root {
  --lg-accent-blue: #007aff;
  --lg-accent-purple: #5856d6;
  --lg-accent-pink: #ff2d55;
  --lg-gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

可用工具类：

```html
<div class="lg-glass">玻璃容器</div>
<h2 class="lg-gradient-text">渐变标题</h2>
<div class="lg-card">卡片内容</div>
```

在 Rmd 末尾用 CSS chunk 覆盖样式；动画应克制，并尊重 `prefers-reduced-motion`。主题默认最大容器宽度约 1200px，带明显焦点轮廓与 WCAG AA 对比目标。

## 兼容性与故障排查

需要支持 `backdrop-filter` 和 CSS 自定义属性；已验证目标为 Chrome 90+、Safari 14+、Firefox 88+、Edge 90+（Safari 需要 `-webkit-` 前缀）。主题无运行时 JS 依赖，`after_body` 只提供交互增强。

- 样式无效：确认两个模板存在，YAML 使用正确相对路径，且 `toc_float` 时保留 `theme: default`；必要时强制刷新。
- 目录不显示：检查文档有 H2/H3，桌面窗口宽度是否 >1024px。
- 深色模式不切换：检查系统偏好和浏览器 `prefers-color-scheme` 支持。
- `<-` 显示成 `←`：确认项目中的 `liquid_glass_theme.css` 已更新；旧项目需重新运行初始化脚本并显式使用 `--force`，或手动同步主题文件。该现象只影响字体显示，复制出的源码通常仍是 `<-`。
- 不需要缩放/滚动保持：移除 `includes.after_body` 或换用仅含 Lightbox 的文件。

主题文件：`templates/liquid_glass_theme.css`；交互文件：`templates/liquid_glass_lightbox.html`。问题和建议请在 bensz-rmd-rules issue 反馈。
