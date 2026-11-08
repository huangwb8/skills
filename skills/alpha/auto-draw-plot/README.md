# auto-draw-plot — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `auto-draw-plot` skill。
执行规范在 `SKILL.md`；默认模式、画布尺寸和生成轮数在 `config.yaml`。

## 快速开始

### 启动前路径声明

通过 AI 助手调用本 skill 时，助手在正式检查 API、初始化工作区或开始出图前，应先明确声明本次任务 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot` 工作区根目录的绝对路径，例如：

```text
本次 auto-draw-plot .bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot 工作区绝对路径：/abs/project/.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot
```

如果你指定了自定义 `workspace_base`，这里应显示该自定义目录解析后的绝对路径。初始化完成后，实际 run 目录会写入 `run-manifest.json`，通常形如 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot/{yyyy-mm-dd-hh-mm}/`。

### 推荐 Prompt（最小可用）

```text
请使用 auto-draw-plot skill 生成一张科研展示图。
输入：展示上下游信号链，6 个节点，用箭头连接，突出关键蛋白；白底，文字清晰。
输出：至少 1 张可用 JPEG；中间文件保存在 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot/`。
```

### 进阶 Prompt（带比例参数）

```text
请使用 auto-draw-plot skill 生成一张科研展示图。
输入：展示上下游信号链，6 个节点，用箭头连接，突出关键蛋白；白底，文字清晰。
输出：至少 1 张可用 JPEG；中间文件保存在 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot/`。
另外，还有下列参数约束：
- mode：general
- 期望布局比例：1600 x 900
- 画布比例：16:9
- max_rounds：3
```

尺寸可以用自然语言写在 Prompt 里作为布局参考，例如 `画布比例：16:9`、`期望布局：1800 x 1697`。如果你直接运行脚本，`--canvas-width` 和 `--canvas-height` 只影响布局提示，不承诺最终像素。为控制真实调用成本，OpenAI 图片模型默认使用 `gpt-image-2.5-flare`，并显式请求 `quality=low`、最小方形原生尺寸 `1024x1024` 和 `output_format=jpeg`。

## GPT Image 2.6：矢量图、动图与标注编辑

支持显式选择 `gpt-image-2.6-flare`（交互迭代）与 `gpt-image-2.6-sunburst`（细节构图）。默认模型仍为 `gpt-image-2.5-flare`；请求 SVG/GIF 或 complexity 时请明确选 2.6，脚本不会静默更换模型。

`mode` 与 `output_format` 独立。例如，技术路线图可用 `roadmap + svg`，动态机制展示可用 `schematic + gif`。原生格式通过 BenszAPI Images generations/edits 或默认异步 jobs 提交；上游需使用已确认支持相应能力、且在账号 `extra.openai_images_native_formats` 显式声明 `svg`／`gif` 的 API Key 通道；OAuth bridge 明确拒绝这两种原生格式。服务端提交前检查能力，成功结果逐张验证真实字节。未支持时会明确失败，不降级成 JPEG，也不跨 provider 重试。配置方法见 [服务端能力说明](../../docs/OpenAI图片桥接说明.md#原生格式能力声明与结果验证)。

### 生成 SVG

```bash
python3 skills/auto-draw-plot/scripts/run_draw_plot.py \
  --provider gpt-image-2.6-sunburst --mode roadmap \
  --request-text "生成三阶段研究路线图，白底，简洁矢量节点与箭头，文字清晰。" \
  --complexity high --quality medium \
  --output-format svg --output-image ./roadmap.svg
```

SVG 原件按 UTF-8 XML 保存，校验静态矢量内容，拒绝脚本、外部资源、内嵌位图和实体声明。需要 PNG 预览时可在调用该 skill 的 Python 环境安装可选的 `CairoSVG`，同时提供其系统依赖 Cairo；不可用时原件照常交付，并明确提示使用浏览器检查。矢量原件方便继续编辑，但不保证模型生成的文字一定保持为文本节点。

### 生成循环 GIF

```bash
python3 skills/auto-draw-plot/scripts/run_draw_plot.py \
  --provider gpt-image-2.6-flare --mode schematic \
  --request-text "蓝色粒子沿环形通路匀速运动，固定镜头、固定标签，首尾无缝循环。" \
  --complexity medium --output-format gif --provider-size auto \
  --frame-count 9 --frame-duration-ms 200 --output-image ./mechanism.gif
```

输出完整 GIF 与 `mechanism.preview.png` 接触表，结果记录实际帧数、逐帧时长、总时长和循环信息。显式 GIF 尺寸是每帧尺寸，宽高必须为 16 的倍数；总像素预算由上游校验。帧数与时长是请求参数，实际成品元数据独立记录。

SVG/GIF 都只支持文本生成，不接受参考图编辑、markup、位图后处理缩放或 `output_compression`；请求中不发送流式、partial images 或 prompt_rewriter。默认单轮避免无视觉反馈的额外生成；用户显式要求多轮时只依据文字反馈重新生成，不能把前一轮 SVG/GIF 当作 edits 输入。

### 原生格式诊断

| 错误码 | 含义 |
| --- | --- |
| `MODEL_NOT_IN_CATALOG` | 站点尚未开放该模型 |
| `IMAGE_OUTPUT_FORMAT_UNSUPPORTED` | 当前模型、账号通道或 provider 未确认支持此格式，或处于格式失败冷却期 |
| `IMAGE_OUTPUT_FORMAT_MISMATCH` | 上游返回了 PNG 等错误内容，或 SVG／GIF 安全结构、帧约束、MIME 不匹配 |
| `IMAGE_OUTPUT_UNCONFIRMED` | 上游请求已发出但结果无法确认，自动重提交可能重复计费 |

这些错误都停止当前任务，不重试 submit，也不跨 provider 回退。失败 job 保留服务端错误码与安全诊断；再次 poll／result 不触发新的生成。成功时客户端读取服务端格式字段，记录 `server_format_validated` 与逐图 `server_format_metadata`，同时继续验证本地字节。旧服务端没有新字段时仍检查真实格式，并将 `server_format_validated` 记录为 `false`，不伪称服务端已验证。GIF 最多 64 帧、单边最多 8192，解码前限制累计帧像素 64 Mi，拒绝单帧伪动画和缺少循环信息的 GIF。

### 使用标注层修改静态图

```bash
python3 skills/auto-draw-plot/scripts/run_draw_plot.py \
  --provider gpt-image-2.6-flare --max-rounds 1 \
  --reference-image ./original.png --markup ./overlay.png \
  --request-text "将红圈内节点改成蓝色，其余内容保持，成品移除红圈标注。" \
  --complexity low --output-format png --output-image ./edited.png
```

`overlay.png` 必须是与原图等大的透明 PNG。原图与标注层作为独立 multipart 字段上传，标注编辑不等于 mask 的像素级硬约束；仍需检查目标区域与其它内容是否符合要求。多轮使用原始原图和原标注层，避免套用新图造成标注位置漂移。2.5 Flare／Sunburst 也接受 markup，但 `complexity` 只向 2.6 提供。

### 检查成品

结构检查只证明文件可解析。SVG 应检查实际渲染、文字与缩放；GIF 应播放完整动画，检查运动语义、闪烁、主体一致性和循环接缝。接触表不能替代动画播放。`evaluation.json` 保持 `passed=false`，直到宿主完成视觉与语义复核；脚本不会把结构通过宣称为图像质量通过。

官方能力与参数来源：[图像生成指南](https://developers.openai.com/api/docs/guides/image-generation#gpt-image-26)。

## 模式选择

| 你的需求 | 推荐 `mode` | 默认画布 | 适合场景 |
| --- | --- | --- | --- |
| 普通展示图、概念图、信息图 | `general` | `1600 x 900` | 默认模式，适合汇报图和自由描述 |
| 技术路线图、roadmap、flowchart | `roadmap` | `1800 x 1697` | 阶段、任务、主链、风险/备选 |
| 原理图、机制图、架构图 | `schematic` | `1920 x 1200` | 模块分组、机制链、算法/实验闭环 |

`nsfc-roadmap` 和 `nsfc-schematic` 可作为别名触发对应模式，但这里只迁移光栅图片的 prompt 与评估经验，不再迁移 draw.io、PDF、TEX 抽取等 legacy 渲染栈；SVG 可通过 2.6 原生输出选择。

`roadmap` / `schematic` 默认偏向正常字宽的中文标签：现代黑体/思源黑体/Noto Sans CJK 风格、常规到半粗体、深灰或黑色。标签过长时优先自然换行，不使用窄体、长体、压缩体或横向压缩字形。

## 使用示例

### 示例：技术路线图

```text
请使用 auto-draw-plot skill 生成技术路线图。
输入：把这段研究内容整理成 3-5 个阶段，突出主链、风险控制和备选方案。
输出：A4 缩印仍可读的白底 JPEG。
另外，还有下列参数约束：
- mode：roadmap
- 期望布局比例：1800 x 1697
- 字体：中文标签使用正常字宽，禁止窄体/压缩体
```

### 示例：原理图/机制图

```text
请使用 auto-draw-plot skill 生成机制图。
输入：展示输入层、模型处理层、验证层和输出层之间的关系；保留这些中文术语，不要改写关键标签。
输出：分组清晰、箭头方向正确、中文标签可读的 JPEG。
另外，还有下列参数约束：
- mode：schematic
- 期望布局比例：1920 x 1200
- 字体：中文标签使用正常字宽，禁止窄体/压缩体
```

### 示例：带参考图微调

```text
请使用 auto-draw-plot skill 根据参考图生成一张新版架构图。
输入：参考图是 `./old-figure.png`；保留三层结构，但改成白底、低饱和蓝灰配色，并让中文标签更清晰。
输出：一张适合论文补充材料的 JPEG。
另外，还有下列参数约束：
- mode：schematic
- 期望布局比例：2560 x 1600
- max_rounds：4
```

## 分辨率怎么理解

默认策略是“原生优先”：provider 返回多少像素，最终图片就保存多少像素。`--canvas-width` / `--canvas-height` 和 Prompt 中的尺寸描述用于表达布局比例，并帮助脚本选择 provider 支持的原生请求尺寸；它们不是超分辨率或 4K 导出开关。

可以通过 `--provider-size` 显式请求 `2048x2048`、`4096x4096`、`3840x2160` 或 `2160x3840`，原有 `auto`、`1024x1024`、`1536x1024`、`1024x1536` 继续支持。高尺寸档优先尝试可用 API Key 通道，不可用时允许 OAuth 回退；最终原生尺寸由实际图片决定。客户端按网关现有档位（≤1024 / ≤1792 / 更大）检测降级，`2048x2048` 也属于网关 4K 档，档名不保证每边 4096 像素。降级时 stderr、轮次 meta 和最终 `meta/result.json` 都会给出 `size_downgrade_detected`／`size_downgrade_warning`；交付必须明确说明请求与实际尺寸，即使显式后处理已经放大。

| 场景 | 适合用途 | 推荐写法 | 脚本参数 |
| --- | --- | --- | --- |
| 16:9 汇报图 | 普通展示图、概念图 | `画布比例：16:9` | `--canvas-width 1600 --canvas-height 900` |
| 技术路线图 | roadmap 首轮生成与多轮优化 | `接近 A4 的技术路线图比例` | `--canvas-width 1800 --canvas-height 1697` |
| 宽幅机制图 | schematic 首轮生成与多轮优化 | `宽幅机制图，约 16:10` | `--canvas-width 1920 --canvas-height 1200` |
| 竖版 A4 | 需要接近 A4 竖版比例 | `竖版 A4 比例` | `--canvas-width 2400 --canvas-height 3394` |

OpenAI 图片模型默认固定请求最低成本的 `1024x1024` 原生尺寸；画布宽高仍会进入 prompt 作为布局意图，但不会把 provider 请求提高到更大的原生尺寸。Nano Banana/Gemini 会按 provider 的 `aspectRatio` / `imageSize` 能力返回图片。若要出版级清晰文字，优先使用矢量重排、程序化绘图或后续排版处理，不要依赖插值放大。

## 工作原理

`auto-draw-plot` 会由当前宿主 AI 把你的需求拆成主体、结构、风格、硬约束和禁止项，然后按模式生成图片 prompt。普通静态位图第 1 轮按文本出图；第 2 轮起会自动把上一轮 `output.jpg` 作为第一参考图，并追加保留主体、构图和背景的保真约束。首轮已有用户参考图时也会正确记录为 `image-to-image`。

它是自包含的图片生成工作流：本 skill 自己通过 BenszAPI 完成 prompt、出图、编辑与迭代，不依赖 `imagegen` skill。仅当你明确要求同时使用 `imagegen` 或其特有能力时，助手才应额外调用它，并说明两者独立的职责；正常使用 `auto-draw-plot` 时，不应出现“先由它写 prompt、再交给 imagegen 出图”的说法。

图片生成默认使用 `auto` provider 选择：运行前按优先级寻找一个配置、连接和鉴权检查通过的图片 provider。这里的 `/v1/models` 探测不执行完整 Images 计费资格检查，因此输出 `connectivity/authentication_ok` 只表示“能连通且 Key 可鉴权”，不表示当前请求已经 `generation_eligible`。真实生成资格以 `/images/jobs/generations` 或 `/images/jobs/edits` 的 submit 响应为准。

生成过程中默认不跨模型回退；如果你明确要求“用 `gpt-image-2.5-sunburst` 画图”或“用 `gpt-image-2` 画图”，对应模型失败时会停止并报告原因，不会自动改用 Nano Banana / Gemini。只有你明确说“provider 故障时可以换模型”时，才允许开启 provider fallback；订阅、余额、权限、overage、计费服务错误，以及 submit 空/非 JSON 等无法确认 job 是否已创建的协议错误，即使开启该选项也不会跨 provider，以免掩盖真实业务故障或重复生成计费。

`gpt-image-2.5-flare`、`gpt-image-2.5-sunburst` 与 `gpt-image-2` 共享 OpenAI Images provider，默认主动使用 Sub2API 的 image job endpoint：文本出图提交到 `/v1/images/jobs/generations`，参考图编辑提交到 `/v1/images/jobs/edits`。配置为 `https://<subdomain>.benszresearch.com` 的根地址时，客户端会在安全校验后自动规范为 `.../v1`；已显式配置 `/v1` 时保持不变。这样长耗时图片任务会在服务端 job 中运行，客户端只负责轮询，避免同步 `/v1/images/generations` 或 `/v1/images/edits` 长连接更容易暴露在 504 风险下。

同步接口只作为兼容回退：当 job endpoint 明确返回 404/405/501 时，脚本才会改用旧同步端点。服务端尚未确认持久幂等语义前，submit 固定只提交一次；`BILLING_PRICING_NOT_CONFIGURED` 等 `retryable=false` 错误不会退避重试，`2xx` 空/非 JSON 响应也不会重放，poll/result 的临时故障独立处理。JSON 与 multipart 请求都会发送单次生成的安全 `X-Client-Request-ID`；此类协议错误会在 `image-debug/gpt-image-2-error.json` 中记录服务端回传的安全 `X-Request-ID` / `X-Client-Request-ID`、HTTP 状态、origin/path、Content-Type、声明/实际长度、正文 SHA-256、首字节类别和重定向变化，但不会保存 query、鉴权头、prompt 或原始响应正文。参考图证据同样只记录 SHA-256，不记录 API Key 或内部订阅明细。

## 配置

推荐配置在 `~/.bensz-skills/config/remote.env` 或环境变量中。如果只使用 OpenAI 图片模型，不需要配置 Gemini。

```bash
# OpenAI 图片模型主路径；不设置 OPENAI_IMAGE_MODEL 时默认 gpt-image-2.5-flare
OPENAI_BASE_URL=https://api.benszresearch.com/v1
OPENAI_API_KEY=你的密钥
OPENAI_IMAGE_MODEL=gpt-image-2.5-flare

# Nano Banana/Gemini 图片 provider 路径（仅在使用该 provider 或明确允许图片回退时需要）
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_API=你的密钥
GEMINI_MODEL=nano-banana-preview
```

默认情况下，skill 会先读取本地 Codex 配置：从 `~/.codex/config.toml` 获取 BenszAPI base URL，从 `~/.codex/auth.json` 获取 `OPENAI_API_KEY` / `OPENAI_API`。只有 Codex 本地配置缺少对应字段时，才使用环境变量或 `remote.env` 作为兜底。Windows 会优先按 `%USERPROFILE%`、`%HOMEDRIVE%%HOMEPATH%` 解析 `~`，同时兼容 Git Bash/PowerShell 的 `HOME`。每次运行会在脱敏诊断证据中记录实际配置路径、来源和 API Key 短指纹；如果 Codex 配置与 BenszAPI 环境变量冲突，会在发图前停止并指出 `base_url_mismatch` 或 `api_key_mismatch`，避免静默读取旧配置。

## 输出结果

- 最终图片：默认 `draw-plot.jpg`，或你传入的 `--output-image`（`--output-png` 保留为兼容别名）
- 启动前声明：AI 助手应先输出 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot` 根目录绝对路径，便于实时监督
- 隐藏工作区：`.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot/{yyyy-mm-dd-hh-mm}/`
- 追溯文件：`meta/analysis.json`、`meta/result.json`
- 每轮证据：`rounds/round-XX/prompt.txt`、`output.jpg`、`evaluation.json`
- provider 与参考图记录：`meta/result.json` 中的 `providers_used`，以及 `meta/analysis.json` 每轮的 `reference_strategy`

## 备选用法（脚本）

Prompt 调用是推荐用法；当你需要固定参数、批量跑图或接入自动化流程时，再直接运行脚本。

```bash
python3 auto-draw-plot/scripts/run_draw_plot.py \
  --mode roadmap \
  --provider gpt-image-2.5-flare \
  --request-text "画一张白底技术路线图：三阶段研究任务，包含风险控制和验证闭环。" \
  --canvas-width 1800 \
  --canvas-height 1697 \
  --output-image ./roadmap.jpg
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--mode` | `general` / `roadmap` / `schematic` |
| `--max-rounds` | 静态位图默认 `3`；SVG/GIF 默认 `1`，显式多轮按文字反馈重新生成 |
| `--canvas-width` | 期望布局宽度/比例参考，不承诺最终图片像素 |
| `--canvas-height` | 期望布局高度/比例参考，不承诺最终图片像素 |
| `--postprocess-resize` | 显式启用尺寸后处理；必须同时提供 `--postprocess-width` 与 `--postprocess-height` |
| `--postprocess-width` | 后处理目标宽度，需配合 `--postprocess-resize` |
| `--postprocess-height` | 后处理目标高度，需配合 `--postprocess-resize` |
| `--quality` | OpenAI 图片模型画质：`low` / `medium` / `high` / `auto`，默认 `low` |
| `--provider-size` | 静态图原生尺寸枚举，默认 `1024x1024`；GIF 默认 `auto`，显式每帧宽高为 16 的倍数 |
| `--output-format` | `jpeg` / `png` / `webp` / `svg` / `gif`；省略时按输出扩展名推断，无路径则默认 `jpeg` |
| `--output-compression` | JPEG/WebP 压缩 `0-100`，默认 `85`；SVG/GIF 不接受，PNG 不发送 |
| `--complexity` | 2.6 规划复杂度 `low` / `medium` / `high`；省略使用上游默认 `high` |
| `--frame-count` | GIF 帧数 `2-64`，省略使用上游默认 `9` |
| `--frame-duration-ms` | GIF 每帧时长 `20-2000ms`，上游按 `10ms` 取整；默认 `200ms` |
| `--markup` | 独立透明 PNG 标注层；尺寸须与唯一原图一致 |
| `--reference-image` | 用户参考图；第 2 轮起上一轮输出图会自动排在这些参考图之前 |
| `--provider` | 图片 provider/model：`auto` / `gpt-image-2.6-flare` / `gpt-image-2.6-sunburst` / `gpt-image-2.5-flare` / `gpt-image-2.5-sunburst` / `gpt-image-2` / `nano_banana`；用户点名模型时应显式传入 |
| `--allow-provider-fallback` | 只有用户明确允许 provider 故障时换模型才使用；计费、权限与客户端策略错误仍不回退 |
| `--api-env` | 自定义 env 文件 |
| `--allow-outside-project` | 允许输出或工作区写到 `project_root` 外部 |

长耗时图片任务由配置项 `api.async_image_job.submit_mode`、`fallback_to_sync_on_unsupported`、`max_wait_s`、`poll_interval_s` 和 `poll_timeout_s` 控制。一般不需要改；只有目标 Sub2API 部署没有 job endpoint，或服务端排队明显超过默认 30 分钟时再调整。

检查 provider：

```bash
python3 auto-draw-plot/scripts/nano_banana_check.py
```

这个命令名保留旧兼容性，实际会检查当前图片 provider 优先级。对 OpenAI 图片模型，它只检查配置、连接与鉴权；看到 `generation_eligible=unknown_until_image_submit` 是正常结果，真正的准入判断发生在图片 submit。

## FAQ

### Q：分辨率写在 Prompt 里就够了吗？

A：可以写，但它只作为布局和 provider 尺寸选择参考。默认最终图片保留 provider 原生尺寸；如果 meta 里看到 `native_size` 与 `output_size` 一致，说明没有后处理插值。

### Q：为什么指定 OpenAI 图片模型后没有自动回退到 Nano Banana？

A：这是预期行为。用户点名模型时，skill 会尊重这个选择；如果配置、额度或端点失败，会停止并报告原因。只有你明确允许 provider 故障时换模型，脚本才会使用 `--allow-provider-fallback`；订阅、余额、权限、overage 与计费服务错误不会借此切换模型。

### Q：为什么 provider 检查显示 OK，提交图片时仍可能失败？

A：检查阶段的 `OK connectivity/authentication_ok` 只证明 base URL 可连接且 Key 可鉴权。图片请求的模型、分组、订阅、余额、overage 等条件只有真实 submit 才能完整判断；请以 submit 返回的 `SUBSCRIPTION_REQUIRED`、`BILLING_SERVICE_ERROR`、`OVERAGE_LIMIT_EXCEEDED` 等结构化错误码为准。

### Q：`PROVIDER_EMPTY_RESPONSE` 或 `PROVIDER_NON_JSON_RESPONSE` 是什么？

A：它表示 HTTP 客户端收到了成功状态，但正文为空或不是 Sub2API Images 约定的 JSON。由于客户端无法确认服务端是否已经创建 job，脚本不会自动重试，也不会跨 provider 再生成；请保留 `image-debug/gpt-image-2-error.json`，用其中不含密钥和正文的 `request_id`、`client_request_id`、状态、路径、长度、类型与指纹联系管理员排查边缘/代理链路。

### Q：使用 OpenAI 图片模型时还会调用 Gemini 做文本规划或评估吗？

A：不会。OpenAI 图片路径默认不需要 Gemini 配置；prompt 规划由当前宿主 AI 和脚本本地模板完成，脚本评估默认是启发式检查，最终语义质量由宿主 AI 根据图片把关。

### Q：多轮优化是在重画，还是沿着上一张图继续改？

A：普通静态图沿着上一张图继续改。第 1 轮是 text-to-image；从第 2 轮开始，第 `n+1` 轮会把第 `n` 轮 JPEG 作为第一参考图，并结合反馈做 image-to-image 保真微调。

### Q：为什么 roadmap / schematic 里的中文默认不用窄体？

A：中文标签以正常字宽更接近论文图和汇报图的常规排版，也更利于缩印阅读。`roadmap` / `schematic` 会默认要求现代黑体/思源黑体/Noto Sans CJK 风格，优先自然换行，避免窄体、长体、压缩体、横向压缩和瘦长字体。只有你明确要求海报感、窄体标题或压缩排版时，才应覆盖这个默认偏好。

### Q：`roadmap` / `schematic` 会输出 draw.io 吗？

A：不会。模式负责图意与布局，输出格式独立选择；2.6 可以生成原生 SVG，legacy draw.io/PDF 渲染栈不在本 skill 内维护。
