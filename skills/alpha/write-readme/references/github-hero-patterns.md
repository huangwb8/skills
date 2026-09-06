# GitHub Hero 首屏模式

## 目的与默认规则

GitHub README 的首屏通常不是一条孤立的标题，而是一个帮助读者快速判断和行动的 Hero 区域。除非项目是极短的内部说明、纯 API 索引或用户明确要求极简排版，否则默认按以下顺序设计：

1. **居中标题或品牌标识**：项目名是唯一主标题；有真实 logo/banner 时才使用，并提供准确的 `alt`、尺寸和相对路径。
2. **事实徽章**：先放维护/构建/版本/许可证等可信度徽章，再放能力或生态徽章；只保留能帮助决策的 3–8 个，不堆星数和无关装饰。
3. **导航行**：把语言切换、在线 Demo、Quick Start、文档、示例、Issue/Discussion 等高频入口压缩为一行或两行；链接必须真实可达，短 README 不强行放目录。
4. **价值主张**：用一句可验证的话说明“为谁、解决什么任务、产出什么结果”；不要用“下一代、革命性”等不可证实形容词。
5. **解释段**：紧接价值主张，用 2–4 句说明工作方式、边界和最短下一步，让读者无需滚动到正文才知道项目是否适合自己。
6. **证据或行动入口**：根据项目类型放真实截图/GIF、终端/API 输出，或直接给一条可复制的安装/启动命令；没有可靠视觉材料时使用文本，不要生成占位图。

Hero 的目标是让读者在约 30 秒内完成“这是什么 → 是否适合我 → 如何开始”的判断；它不是把所有信息都塞进首屏。Quick Start、功能细节和安全/限制应在 Hero 后渐进展开。

## 四种可复用套路

### 1. 产品展示型：视觉先行

适合 Web 应用、桌面应用、交互式工具和有真实 Demo 的项目。

````html
<div align="center">
  <img src="docs/assets/hero.png" alt="产品主界面或核心产物" width="760" />
  <h1>项目名</h1>
  <p><strong>一句话价值主张</strong></p>
  <p>许可证徽章 · Demo 徽章 · 构建/版本徽章</p>
  <p><a href="README_EN.md">English</a> · <a href="#quick-start">Quick Start</a> · <a href="docs/">Docs</a> · <a href="https://example.com">Live Demo</a></p>
</div>
````

随后用一段解释交代用户体验和适用边界，再给“体验 Demo / 本地运行 / 部署”三条路径。截图必须是仓库真实文件或稳定的公开资源；图片不可用时，退化为文本价值主张和 Quick Start。

### 2. 开发者工具型：命令先行

适合 CLI、服务、Agent Skill 和开发者工具。视觉材料不是必需项，首屏应该优先让读者复制第一条命令。

`````html
<div align="center">
  <h1>项目名</h1>
  <p><strong>为某类开发者把某个输入变成某个可验证结果</strong></p>
  <p>维护状态 · 版本 · 许可证 · 兼容宿主</p>
  <p><a href="README_EN.md">English</a> · <a href="#quick-start">Quick Start</a> · <a href="docs/">Docs</a> · <a href="CONTRIBUTING.md">Contributing</a></p>
</div>

````bash
# 最短成功路径
{verified command}
````
`````

命令后立即写出预期结果、必要环境变量和不支持的场景；不要把生产部署、开发调试和高级插件混成一条命令。

### 3. 库/SDK 型：可信度与最小 API

适合包、SDK 和可嵌入组件。徽章应集中表达版本、构建、许可证和运行时支持，导航链接到 API/示例；Hero 后直接给安装命令和最小导入代码。

推荐顺序：`标题 → 价值主张 → 徽章 → 语言/文档导航 → 安装 → 最小 API`。不要在首屏放完整 API 表或未经基准条件的性能数字。

### 4. 资源/集合型：规模证据与分流

适合 awesome list、Skill 集合、模板库和数据资源。用简短徽章或统计说明规模，但必须能在仓库中核对；导航按“开始使用、目录/分类、贡献、许可证”分流。

推荐顺序：`标题/标识 → 价值主张 → 规模/兼容性徽章 → 目录与安装导航 → 一段解释 → 按任务或受众分类`。如果规模会频繁变化，优先链接到可维护的目录或生成页，不要在 Hero 中硬编码易过期数字。

## 视觉与可访问性门槛

- HTML 居中布局是可选表达方式；纯 Markdown 也能组成完整 Hero，不为了“好看”引入脆弱的表格或脚本。
- 所有图片、GIF 和徽章都要有准确 `alt`；装饰性图片可使用空 `alt`，但不得把关键信息只放在图片里。
- 控制首屏高度：通常一张主视觉、两行徽章、两行导航足够；大图应设置合理宽度并使用仓库相对路径。
- 使用 GitHub 可渲染的 HTML/Markdown，不依赖 JavaScript、外链字体或无法在暗色主题显示的颜色。
- 徽章风格保持一致（例如统一 `flat-square`），按“状态 → 能力 → 社区”分组，避免每个依赖都占一个徽章。
- 中英文 README 的 Hero 结构、入口链接和事实保持对齐；语言切换链接可互相指向对应文件，不要把翻译链接藏在文末。

## 反模式与回退策略

- **徽章墙**：超过决策所需数量或包含不可核验数字时，删除或移到“项目状态/生态”章节。
- **空壳视觉**：只有模板 logo、失效图片或与当前版本不一致的 GIF 时，改用终端输出/API 响应。
- **导航迷宫**：首屏放十几个链接、目录和社交入口时，只保留语言、开始、文档、Demo/支持四类入口。
- **口号代替说明**：价值主张没有对象、动作和结果时，重写为可验证句子，并在其后补边界解释。
- **同质化模板**：项目形态不适合居中 HTML 时，保留信息顺序，使用左对齐 Markdown；Hero 是信息契约，不是固定视觉外壳。

## 调研样本与可追溯来源

以下公开页面仅用于提炼模式，不复制第三方项目文本或资产：

- [OpenMAIC README](https://github.com/THU-MAIC/OpenMAIC)：横幅、双语/指南导航、多层徽章、Demo 与首段产品承诺组合；适合产品展示型。
- [Archify README](https://github.com/tt-a1i/archify)：真实产物预览、价值主张、版本/许可证徽章、项目页/场景指南/Proof Lab 导航和一条安装命令；适合开发者工具型。
- [Scientific Agent Skills README](https://github.com/K-Dense-AI/scientific-agent-skills)：徽章集中表达许可、版本、规模、兼容宿主和 CI，随后用解释段和目录分流；适合集合型。
- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)：居中 logo/标题/价值主张/行动链接的经典骨架，并展示目录只在正文较长时出现；适合作为通用低风险起点。
- [GitHub Docs — About README files](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)：README 应解释项目用途、价值、开始方式、求助和维护信息，并支持标题 Outline 与相对链接。
