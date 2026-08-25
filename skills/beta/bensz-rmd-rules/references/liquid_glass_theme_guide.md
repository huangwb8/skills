# Liquid Glass Theme 使用指南

## 概述

Liquid Glass Theme 是一套 glassmorphism 风格的专业级 R Markdown 主题，具有以下特点：

- **液态玻璃质感**：Glassmorphism 效果，背景模糊与半透明层次
- **流体渐变**：有机色彩过渡（默认静态，避免干扰复制/选中文本）
- **平滑过渡**：仅保留必要的 hover/交互过渡（无无限循环动画）
- **深度阴影**：多层阴影系统营造空间感
- **自动深色模式**：根据系统偏好自动切换
- **浮动目录两种模式**：静态浮动（常驻）/ 动态浮动（收起为左上角小圆点，悬停展开）
- **移动端友好目录**：窄屏自动折叠为卡片，点击顶部按钮展开/收起
- **图片默认居中**：独立图片在正文中自动居中显示
- **代码块一键复制**：代码块右上角提供“复制/Copy”按钮，点击复制完整代码

## 快速开始

### 1. 确保 CSS 文件在项目中

将 `templates/liquid_glass_theme.css` 复制到您的项目根目录下的 `templates/` 文件夹。
并将 `templates/liquid_glass_lightbox.html` 复制到同一目录（用于图片点击放大预览）。

更推荐直接使用本 skill 提供的一键脚本完成初始化：

```bash
python3 /path/to/bensz-rmd-rules/scripts/bootstrap_liquid_glass.py --with-env
```

### 2. 在 Rmd 文件中引用

在您的 `.Rmd` 文件的 YAML 头部添加：

```yaml
---
title: "您的分析标题"
author: "您的名字"
date: "`r Sys.Date()`"
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
---
```

**关键点**：
- `theme: default`：满足 rmarkdown 对 `toc_float` 的要求（Liquid Glass CSS 会覆盖主要视觉样式）
- `css`：引用 Liquid Glass CSS（推荐做法）
- `includes.after_body`：启用图片点击放大（Lightbox），点击图片可在浮层中查看，按 Esc 或点击空白处关闭

### 目录（TOC）两种模式

Liquid Glass 默认提供两种目录显示模式（仅在桌面宽屏上生效）：

- **动态浮动（默认）**：左上角显示一个小圆点（`TOC`），鼠标悬停/键盘聚焦后自动展开；移出目录区域后自动回缩。优点是为正文腾出更多空间。
- **静态浮动**：目录常驻显示，正文会为目录预留左侧空间，避免遮挡。

切换方式：在目录面板顶部点击“静态/动态”按钮即可切换（会写入浏览器本地存储，刷新后仍保持）。

### 移动端目录（窄屏）

在手机/窄屏（≤ 1024px）下，目录会自动回到正文顶部，并以“折叠目录条”的形式常驻在视口顶部（sticky），方便滚动阅读时随手呼出：

- 默认折叠，减少首屏占用。
- 点击目录顶部按钮切换“展开/收起”。
- 展开后可在目录内滚动（不影响正文滚动）。
- 点击任意目录项跳转后会自动收起，减少遮挡与二次操作。
- 标题锚点跳转已做顶部偏移处理，避免被 sticky 目录条遮住（表现尽量一致）。

**注意**：
- 不要用 `includes.in_header` 直接 include `.css` 文件内容；Pandoc 会把原始 CSS 作为“头部文本”插入，浏览器可能把它渲染到正文开头，导致页面顶部出现一大段“代码墙”。

### 3. 渲染 HTML

使用 `knit-rmd-html` skill 或 RStudio 的 Knit 按钮渲染：

```bash
python3 skills/knit-rmd-html/scripts/knit_rmd_html.py your_report.Rmd
```

## 设计特性详解

### 1. Glassmorphism（玻璃拟态）

所有卡片元素（目录、表格、代码块）都应用了玻璃拟态效果：

- **背景模糊**：`backdrop-filter: blur(20px)`
- **半透明背景**：`rgba(255, 255, 255, 0.72)`
- **微妙边框**：`1px solid rgba(255, 255, 255, 0.3)`
- **内发光**：`box-shadow` 内阴影模拟环境光

### 2. 流体渐变（默认静态）

- 默认不启用“背景呼吸/标题流光/分隔线光效”等无限循环动画。
- 原因：避免选中文本/代码时产生“高亮漂移/闪动”的观感，提升复制粘贴与阅读的稳定性。

### 3. 弹性过渡曲线

使用优化的 cubic-bezier 曲线：

```css
--lg-transition-elastic: 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
```

这创造了类似 iOS 的"弹跳"交互反馈。

### 4. 多层阴影系统

```css
--lg-shadow-xl:
  0 20px 48px rgba(0, 0, 0, 0.16),  /* 大范围柔阴影 */
  0 10px 24px rgba(0, 0, 0, 0.08),  /* 中等阴影 */
  0 0 0 1px rgba(255, 255, 255, 0.6) inset;  /* 内高光 */
```

### 5. 自动深色模式

通过 `@media (prefers-color-scheme: dark)` 自动检测系统主题：

- **浅色模式**：白色玻璃背景，深色文字
- **深色模式**：深色玻璃背景，浅色文字
- **自动切换**：无需手动配置

## 组件样式展示

### 标题层级

```markdown
# 一级标题（渐变文字）
## 二级标题（渐变底线）
### 三级标题（灰色）
#### 四级标题（浅灰）
```

### 代码块

````markdown
```r
# 代码块有玻璃效果（无光泽划过动画）
# 背景有内阴影营造深度
```
````

### 代码块复制按钮

当启用 `includes.after_body: "templates/liquid_glass_lightbox.html"` 后，页面中的代码块（`div.sourceCode`）会自动在右上角出现“复制/Copy”按钮：

- 有 `code_folding` 的代码块：复制按钮会出现在 Hide 按钮左侧
- 无 `code_folding` 的代码块：会自动创建一个轻量工具条，并在其中展示复制按钮
- 工具条为右上角浮动胶囊样式（不额外占用一整行空间）

**兼容性说明**：
- 现代浏览器优先使用 Clipboard API
- 在 `file://` 或旧浏览器场景会自动降级为 `document.execCommand('copy')`

### 表格

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据 | 数据 | 数据 |

# 表格特点：
# - 玻璃拟态背景
# - 渐变色表头
# - 悬停行高亮 + 轻微放大
```

### 引用块

```markdown
> 引用内容
>
# 特点：
# - 左侧渐变边框
# - 玻璃拟态背景
# - 左上角装饰性引号
```

### 按钮（如需使用）

```html
<button class="btn">点击按钮</button>

# 特点：
# - 玻璃拟态背景
# - 悬停阴影增强（无位移动效）
```

## 自定义工具类

如需在文档中应用样式，可以使用以下工具类：

### `.lg-glass`

应用玻璃拟态效果：

```html
<div class="lg-glass">
  玻璃拟态内容
</div>
```

### `.lg-gradient-text`

渐变文字效果：

```html
<h2 class="lg-gradient-text">渐变标题</h2>
```

### `.lg-card`

卡片容器（带悬停效果）：

```html
<div class="lg-card">
  卡片内容
</div>
```

## 颜色变量

如需自定义颜色，可在 CSS 中修改以下变量：

```css
:root {
  /* 主要颜色 */
  --lg-accent-blue: #007aff;
  --lg-accent-purple: #5856d6;
  --lg-accent-pink: #ff2d55;

  /* 渐变 */
  --lg-gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

## 响应式设计

### 浮动目录

- **桌面（>1024px）**：固定在左上角
- **平板（1024px）**：宽度缩小到 240px
- **手机（<1024px）**：变为静态，位于内容顶部

### 主容器

- **最大宽度**：1200px
- **自适应**：小屏幕自动调整 padding

## 无障碍设计

- **焦点状态**：明显的焦点轮廓（2px 蓝色）
- **减少动画**：默认即无无限动画；仍保留 `prefers-reduced-motion` 兼容口径
- **对比度**：符合 WCAG AA 标准

## 性能优化

- **无 JS 依赖**：纯 CSS，减少运行时开销
- **克制动效**：避免无限循环动画，降低 GPU/CPU 负担与视觉干扰

## 浏览器兼容性

| 浏览器 | 版本要求 | 说明 |
|--------|----------|------|
| Chrome | 90+ | 完全支持 |
| Safari | 14+ | 完全支持（需 `-webkit-` 前缀） |
| Firefox | 88+ | 完全支持 |
| Edge | 90+ | 完全支持 |

**关键依赖**：
- `backdrop-filter`：玻璃拟态核心
- `custom-properties`：CSS 变量

## 故障排除

### 样式未生效

1. **检查路径**：确认 `templates/liquid_glass_theme.css` 文件存在
2. **检查 YAML**：确认已设置 `css: "templates/liquid_glass_theme.css"`（如启用 `toc_float`，建议 `theme: default`）
3. **清除缓存**：强制刷新浏览器（Cmd+Shift+R）

### 浮动目录不显示

1. **确认内容**：文档需要有 H2/H3 标题
2. **检查宽度**：浏览器窗口宽度 > 1024px

### 深色模式不切换

1. **系统设置**：检查操作系统主题偏好
2. **浏览器支持**：确保浏览器支持 `prefers-color-scheme`

### 刷新后缩放/阅读位置丢失

某些场景下（尤其是 `file://` 打开本地 HTML 或 IDE 内置预览器），浏览器未必会记忆“页面级缩放”和滚动位置。Liquid Glass 默认在 `includes.after_body: "templates/liquid_glass_lightbox.html"` 中启用了“视图状态保持”：

- `Ctrl/Cmd + (+/-/0)`：使用页面内部缩放（可在刷新后保持）
- `Ctrl/Cmd + R` 刷新后：尽量恢复刷新前的阅读位置（scroll）

如你希望关闭该行为（回到完全依赖浏览器默认缩放/滚动恢复），可移除 YAML 中的 `includes.after_body`，或替换为旧版仅含 Lightbox 的 after_body 文件。

## 进阶：自定义样式

### 覆盖默认样式

在 Rmd 文件末尾添加：

````markdown
```{css, echo=FALSE}
/* 自定义覆盖 */
h2 {
  color: #your-color;
}
```
````

### 添加自定义动画

```css
@keyframes my-animation {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

.my-element {
  animation: my-animation 0.5s ease;
}
```

## 示例对比

### 传统 `flatly` 主题

- 基础 Bootstrap 样式
- 平面设计，无深度
- 静态，无动画
- 单一配色

### Liquid Glass 主题

- 现代玻璃拟态
- 多层阴影深度
- 克制交互过渡（默认无无限动画）
- 渐变配色系统
- 自动深色模式

## 技术栈

- **主题样式为纯 CSS**：`templates/liquid_glass_theme.css`
- **可选 after_body JavaScript**：`templates/liquid_glass_lightbox.html`（图片放大预览 + 视图状态保持）
- **CSS 变量**：便于自定义
- **现代 CSS**：backdrop-filter、custom-properties
- **响应式**：media queries 适配所有设备

## 反馈与贡献

如有问题或建议，请在 bensz-rmd-rules skill 的 issue 中反馈。
