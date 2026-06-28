# auto-draw-plot — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `auto-draw-plot` skill。
执行规范在 `SKILL.md`；默认模式、画布尺寸和生成轮数在 `config.yaml`。

## 快速开始

### 启动前路径声明

通过 AI 助手调用本 skill 时，助手在正式检查 API、初始化工作区或开始出图前，应先明确声明本次任务 `.bensz-api/skills/auto-draw-plot` 工作区根目录的绝对路径，例如：

```text
本次 auto-draw-plot .bensz-api/skills/auto-draw-plot 工作区绝对路径：/abs/project/.bensz-api/skills/auto-draw-plot
```

如果你指定了自定义 `workspace_base`，这里应显示该自定义目录解析后的绝对路径。初始化完成后，实际 run 目录会写入 `run-manifest.json`，通常形如 `.bensz-api/skills/auto-draw-plot/{yyyy-mm-dd-hh-mm}/`。

### 推荐 Prompt（最小可用）

```text
请使用 auto-draw-plot skill 生成一张科研展示图。
输入：展示上下游信号链，6 个节点，用箭头连接，突出关键蛋白；白底，PNG，文字清晰。
输出：至少 1 张可用 PNG；中间文件保存在 `.bensz-api/skills/auto-draw-plot/`。
```

### 进阶 Prompt（带比例参数）

```text
请使用 auto-draw-plot skill 生成一张科研展示图。
输入：展示上下游信号链，6 个节点，用箭头连接，突出关键蛋白；白底，PNG，文字清晰。
输出：至少 1 张可用 PNG；中间文件保存在 `.bensz-api/skills/auto-draw-plot/`。
另外，还有下列参数约束：
- mode：general
- 期望布局比例：1600 x 900
- 画布比例：16:9
- max_rounds：3
```

尺寸可以用自然语言写在 Prompt 里作为布局参考，例如 `画布比例：16:9`、`期望布局：1800 x 1697`。如果你直接运行脚本，`--canvas-width` 和 `--canvas-height` 只影响布局比例和 provider 原生尺寸选择，不承诺最终 PNG 像素。最终输出默认保留图片 provider 返回的原生尺寸，不做插值放大。

## 模式选择

| 你的需求 | 推荐 `mode` | 默认画布 | 适合场景 |
| --- | --- | --- | --- |
| 普通展示图、概念图、信息图 | `general` | `1600 x 900` | 默认模式，适合汇报图和自由描述 |
| 技术路线图、roadmap、flowchart | `roadmap` | `1800 x 1697` | 阶段、任务、主链、风险/备选 |
| 原理图、机制图、架构图 | `schematic` | `1920 x 1200` | 模块分组、机制链、算法/实验闭环 |

`nsfc-roadmap` 和 `nsfc-schematic` 可作为别名触发对应模式，但这里只迁移 PNG-only 的 prompt 与评估经验，不再迁移 draw.io、SVG/PDF、TEX 抽取等 legacy 渲染栈。

`roadmap` / `schematic` 默认偏向正常字宽的中文标签：现代黑体/思源黑体/Noto Sans CJK 风格、常规到半粗体、深灰或黑色。标签过长时优先自然换行，不使用窄体、长体、压缩体或横向压缩字形。

## 使用示例

### 示例：技术路线图

```text
请使用 auto-draw-plot skill 生成技术路线图。
输入：把这段研究内容整理成 3-5 个阶段，突出主链、风险控制和备选方案。
输出：A4 缩印仍可读的白底 PNG。
另外，还有下列参数约束：
- mode：roadmap
- 期望布局比例：1800 x 1697
- 字体：中文标签使用正常字宽，禁止窄体/压缩体
```

### 示例：原理图/机制图

```text
请使用 auto-draw-plot skill 生成机制图。
输入：展示输入层、模型处理层、验证层和输出层之间的关系；保留这些中文术语，不要改写关键标签。
输出：分组清晰、箭头方向正确、中文标签可读的 PNG。
另外，还有下列参数约束：
- mode：schematic
- 期望布局比例：1920 x 1200
- 字体：中文标签使用正常字宽，禁止窄体/压缩体
```

### 示例：带参考图微调

```text
请使用 auto-draw-plot skill 根据参考图生成一张新版架构图。
输入：参考图是 `./old-figure.png`；保留三层结构，但改成白底、低饱和蓝灰配色，并让中文标签更清晰。
输出：一张适合论文补充材料的 PNG。
另外，还有下列参数约束：
- mode：schematic
- 期望布局比例：2560 x 1600
- max_rounds：4
```

## 分辨率怎么理解

默认策略是“原生优先”：provider 返回多少像素，最终 PNG 就保存多少像素。`--canvas-width` / `--canvas-height` 和 Prompt 中的尺寸描述用于表达布局比例，并帮助脚本选择 provider 支持的原生请求尺寸；它们不是超分辨率或 4K 导出开关。

| 场景 | 适合用途 | 推荐写法 | 脚本参数 |
| --- | --- | --- | --- |
| 16:9 汇报图 | 普通展示图、概念图 | `画布比例：16:9` | `--canvas-width 1600 --canvas-height 900` |
| 技术路线图 | roadmap 首轮生成与多轮优化 | `接近 A4 的技术路线图比例` | `--canvas-width 1800 --canvas-height 1697` |
| 宽幅机制图 | schematic 首轮生成与多轮优化 | `宽幅机制图，约 16:10` | `--canvas-width 1920 --canvas-height 1200` |
| 竖版 A4 | 需要接近 A4 竖版比例 | `竖版 A4 比例` | `--canvas-width 2400 --canvas-height 3394` |

`gpt-image-2` 会被映射到 provider 支持的原生尺寸，例如横图通常请求 `1536x1024`，竖图通常请求 `1024x1536`，方图请求 `1024x1024`。Nano Banana/Gemini 会按 provider 的 `aspectRatio` / `imageSize` 能力返回图片。若要出版级清晰文字，优先使用矢量重排、程序化绘图或后续排版处理，不要依赖插值放大。

## 工作原理

`auto-draw-plot` 会由当前宿主 AI 把你的需求拆成主体、结构、风格、硬约束和禁止项，然后按 `general` / `roadmap` / `schematic` 模式生成图片 prompt。脚本默认只做本地模板拼装和护栏合并，不会为了文本规划或视觉评估额外调用 Gemini。第 1 轮按文本出图；第 2 轮起会自动把上一轮 `output.png` 作为第一参考图，再结合评估反馈做 image-to-image 微调，直到达到质量阈值或达到 `max_rounds`。

图片生成默认使用 `auto` provider 选择：运行前按优先级寻找一个可用图片 provider。生成过程中默认不跨模型回退；如果你明确要求“用 `gpt-image-2` 画图”，`gpt-image-2` 失败时会停止并报告原因，不会自动改用 Nano Banana / Gemini。只有你明确说“失败可以换模型”时，才允许开启 provider fallback。

`gpt-image-2` 默认主动使用 Sub2API 的 image job endpoint：文本出图提交到 `/images/jobs/generations`，参考图编辑提交到 `/images/jobs/edits`。这样长耗时图片任务会在服务端 job 中运行，客户端只负责轮询，避免同步 `/images/generations` 或 `/images/edits` 长连接更容易暴露在 504 风险下。

同步接口只作为兼容回退：当 job endpoint 明确返回 404/405/501 且 `api.async_image_job.fallback_to_sync_on_unsupported=true` 时，脚本才会改用旧同步端点。429、500、502、503、504 不会触发同步回退，而是继续按 async job 提交失败处理。轮询默认最多等待 30 分钟；证据保存在每轮 `image-debug/request.json`、`async-job-initial.json`、`async-job-polls.json`、`async-job-result.json` 和 `response.json`。

## 配置

推荐配置在 `~/.bensz-skills/config/remote.env` 或环境变量中。如果只使用 `gpt-image-2`，不需要配置 Gemini。

```bash
# gpt-image-2 主路径
OPENAI_BASE_URL=https://api.benszresearch.com/v1
OPENAI_API_KEY=你的密钥
OPENAI_IMAGE_MODEL=gpt-image-2

# Nano Banana/Gemini 图片 provider 路径（仅在使用该 provider 或明确允许图片回退时需要）
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_API=你的密钥
GEMINI_MODEL=nano-banana-preview
```

默认情况下，skill 会先读取本地 Codex 配置：从 `~/.codex/config.toml` 获取 BenszAPI base URL，从 `~/.codex/auth.json` 获取 `OPENAI_API_KEY` / `OPENAI_API`。只有 Codex 本地配置缺少对应字段时，才使用环境变量或 `remote.env` 作为兜底。

## 输出结果

- 最终 PNG：默认 `draw-plot.png`，或你传入的 `--output-png`
- 启动前声明：AI 助手应先输出 `.bensz-api/skills/auto-draw-plot` 根目录绝对路径，便于实时监督
- 隐藏工作区：`.bensz-api/skills/auto-draw-plot/{yyyy-mm-dd-hh-mm}/`
- 追溯文件：`meta/analysis.json`、`meta/result.json`
- 每轮证据：`rounds/round-XX/prompt.txt`、`output.png`、`evaluation.json`
- provider 与参考图记录：`meta/result.json` 中的 `providers_used`，以及 `meta/analysis.json` 每轮的 `reference_strategy`

## 备选用法（脚本）

Prompt 调用是推荐用法；当你需要固定参数、批量跑图或接入自动化流程时，再直接运行脚本。

```bash
python3 auto-draw-plot/scripts/run_draw_plot.py \
  --mode roadmap \
  --provider gpt-image-2 \
  --request-text "画一张白底技术路线图：三阶段研究任务，包含风险控制和验证闭环。" \
  --canvas-width 1800 \
  --canvas-height 1697 \
  --output-png ./roadmap.png
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--mode` | `general` / `roadmap` / `schematic` |
| `--max-rounds` | 最大迭代轮数，默认 `3` |
| `--canvas-width` | 期望布局宽度/比例参考，不承诺最终 PNG 像素 |
| `--canvas-height` | 期望布局高度/比例参考，不承诺最终 PNG 像素 |
| `--postprocess-resize` | 显式启用尺寸后处理；必须同时提供 `--postprocess-width` 与 `--postprocess-height` |
| `--postprocess-width` | 后处理目标宽度，需配合 `--postprocess-resize` |
| `--postprocess-height` | 后处理目标高度，需配合 `--postprocess-resize` |
| `--reference-image` | 用户参考图；第 2 轮起上一轮输出图会自动排在这些参考图之前 |
| `--provider` | 图片 provider：`auto` / `gpt-image-2` / `nano_banana`；用户点名模型时应显式传入 |
| `--allow-provider-fallback` | 只有用户明确允许失败后换模型时才使用 |
| `--api-env` | 自定义 env 文件 |
| `--allow-outside-project` | 允许输出或工作区写到 `project_root` 外部 |

长耗时图片任务由配置项 `api.async_image_job.submit_mode`、`fallback_to_sync_on_unsupported`、`max_wait_s`、`poll_interval_s` 和 `poll_timeout_s` 控制。一般不需要改；只有目标 Sub2API 部署没有 job endpoint，或服务端排队明显超过默认 30 分钟时再调整。

检查 provider：

```bash
python3 auto-draw-plot/scripts/nano_banana_check.py
```

这个命令名保留旧兼容性，实际会检查当前图片 provider 优先级。

## FAQ

### Q：分辨率写在 Prompt 里就够了吗？

A：可以写，但它只作为布局和 provider 尺寸选择参考。默认最终 PNG 保留 provider 原生尺寸；如果 meta 里看到 `native_size` 与 `output_size` 一致，说明没有后处理插值。

### Q：为什么指定 `gpt-image-2` 后没有自动回退到 Nano Banana？

A：这是预期行为。用户点名模型时，skill 会尊重这个选择；如果配置、额度或端点失败，会停止并报告原因。只有你明确允许失败后换模型，脚本才会使用 `--allow-provider-fallback`。

### Q：使用 `gpt-image-2` 时还会调用 Gemini 做文本规划或评估吗？

A：不会。`gpt-image-2` 路径默认不需要 Gemini 配置；prompt 规划由当前宿主 AI 和脚本本地模板完成，脚本评估默认是启发式检查，最终语义质量由宿主 AI 根据 PNG 把关。

### Q：多轮优化是在重画，还是沿着上一张图继续改？

A：沿着上一张图继续改。第 1 轮是 text-to-image；从第 2 轮开始，第 `n+1` 轮会把第 `n` 轮 PNG 作为第一参考图，并结合第 `n` 轮评估反馈做 image-to-image 微调。

### Q：为什么 roadmap / schematic 里的中文默认不用窄体？

A：中文标签以正常字宽更接近论文图和汇报图的常规排版，也更利于缩印阅读。`roadmap` / `schematic` 会默认要求现代黑体/思源黑体/Noto Sans CJK 风格，优先自然换行，避免窄体、长体、压缩体、横向压缩和瘦长字体。只有你明确要求海报感、窄体标题或压缩排版时，才应覆盖这个默认偏好。

### Q：`roadmap` / `schematic` 会输出 draw.io 吗？

A：不会。它们现在是 `auto-draw-plot` 的特殊 PNG 模式；legacy draw.io/SVG/PDF 能力不在本 skill 内继续维护。
