---
name: auto-draw-plot
description: 根据用户描述生成高质量绘图 prompt，并按通用、roadmap、schematic 模式调用 gpt-image-2 或 Nano Banana/Gemini 图片模型 API；gpt-image-2 默认使用低画质、原生尺寸和 JPEG，第 2 轮起基于上一轮图片做保真微调。
metadata:
  author: Bensz Conan
  short-description: 模式化需求理解 + multi-round image-to-image optimization + gpt-image-2 低成本 JPEG
  keywords:
    - auto-draw-plot
    - nano-banana
    - gemini
    - parallel-vibe
    - visual evaluation
    - 图像生成
---

# Auto Draw Plot

## BenszAPI 任务工作区

本 Skill 的新任务中间文件统一写入 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/{skill名}/input|output|log/`。同一任务复用一个任务根目录；多 Skill 协作才创建 `shared/`。正式交付物不写入该目录，历史隐藏目录只允许显式兼容读取、迁移或清理。

## 与 bensz-collect-bugs 的协作约定

- 如果用户环境里出现因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，禁止直接修改用户本地 Claude Code/Codex 已安装的 skill 源码。
- 只在用户明确要求“report bensz skills bugs”时，才通过本地 `gh` 调用将新 bug 推送到 `huangwb8/bensz-bugs`；上传前必须先脱敏本地路径/用户名等隐私。

## 定位

- 以用户需求为起点，由宿主 AI 进行语义规划，再构造适用于当前图片 provider 的 prompt；脚本默认不调用额外 Gemini 文本接口。
- 默认模式是 `general`；用户明确要技术路线图/roadmap/flowchart 时使用 `roadmap`，明确要原理图/机制图/架构图时使用 `schematic`。后续新增类型应作为 `config.yaml:modes.presets` 扩展，不改主流程。
- 默认通过 `scripts/run_draw_plot.py` 在独立隐藏工作区里完成“parallel-vibe 规划留痕 → prompt → 出图 → 视觉评估 → 继续/停止”的闭环；`parallel-vibe` 是必选工作流的一部分，不是可选增强。
- 默认工作区是当前目录下的 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot/{yyyy-mm-dd-hh-mm}/`；所有中间文件必须留在隐藏目录里。宿主 AI 在正式检查 API、初始化工作区或开始出图前，必须先向用户明确声明本次任务 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot` 根目录的绝对路径，方便用户实时监督。轻量测试目录固定为 `./tests/draw-plot`。

## 输入

- `user_need`（必需）：自然语言描述的图像需求、输出用途、必要的视觉语义与格式要求。
- `mode`（可选）：`general` / `roadmap` / `schematic`；默认 `general`。模式只改变 prompt preset、默认画布和评估口径，不引入 legacy draw.io 渲染器。
- `api_config`（可选）：指向 `~/.bensz-skills/config/remote.env` 的路径；默认 `auto` 只在运行前按优先级选择连接与鉴权检查通过的 provider，真实生成资格以 Images submit 响应为准。
- `image_provider`（可选）：用户明确指定的图片模型/provider，如 `gpt-image-2` 或 `nano_banana`。显式指定后必须只用该 provider，失败时暂停并报告原因，不得切换到其他模型。
- `allow_provider_fallback`（可选）：只有用户明确说“失败可以换模型/可以回退到另一个 provider”时才为 true；该授权仅覆盖 provider 故障，不覆盖订阅、余额、权限、overage 或计费服务错误。
- `max_rounds`（可选）：最大优化轮数，默认 3；若用户另有指定，以用户为准。
- `visual_constraints`（可选）：比例、期望布局、色调、字体等硬约束。尺寸只作为 provider 原生尺寸选择参考，不承诺最终导出像素。
- `quality` / `provider_size` / `output_format` / `output_compression`（可选）：`gpt-image-2` 显式 provider 参数；默认分别为 `low`、`1024x1024`、`jpeg`、`85`，均执行白名单或范围校验。
- `reference_images`（可选）：用于 prompt 引导的风格/布局图；第 2 轮起上一轮 `output.jpg` 会自动作为第一参考图，用户参考图排在其后。
- `workspace_base`（可选）：用户显式指定的隐藏工作区根目录；未指定时使用当前目录 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot/`。

## 输出

- 至少 1 张合乎需求的图像；`gpt-image-2` 正式输出默认为 `jpeg`。
- 隐藏目录里的 `meta/analysis.json` / `meta/result.json`：记录每轮 prompt、模型参数、参考图策略、评估结果、最终选图和停止原因。
- 每轮图片 meta 必须区分 `requested_provider_size`、`native_size`、`output_size` 与 `postprocess_resize_applied`；默认 `postprocess_resize_applied=false`。
- `image-debug/gpt-image-2-error.json` 只保留错误类别、HTTP 状态和服务端安全返回的 `error.type` / `error.code` / `error.message`；不得写入 Authorization、API Key、订阅明细或原始内部错误对象。
- 每轮目录：`rounds/round-XX/prompt.txt`、`rounds/round-XX/prompt-plan.json`、`rounds/round-XX/parallel-plan.json`、`rounds/round-XX/output.jpg`、`rounds/round-XX/evaluation.json` 以及 `image-debug/` / `evaluation-debug/`；`gpt-image-2` 默认主动使用 Sub2API image job endpoint，generation/edit 均显式发送 `quality=low`、原生尺寸和 `output_format=jpeg`，并在 debug meta 中保留参考图 SHA-256。
- run 级 `parallel-vibe/parallel-plan.json` 与 `parallel-vibe/parallel-plan.round-XX.json`：每轮必留痕的 parallel-vibe plan。

## 运行前检查

1. 先解析本次任务的隐藏工作区根目录：若用户传入 `workspace_base`，解析该路径；否则使用 `project_root/.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot`。必须把解析后的绝对路径用可见消息告诉用户，例如：`本次 auto-draw-plot .bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot 工作区绝对路径：/abs/project/.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot`。这条消息必须出现在 API 检查、`init_workspace.py`、`run_draw_plot.py` 或任何图片生成调用之前；不要只把路径写进 `run-manifest.json`。
2. 默认优先读取本地 Codex 配置：从 `~/.codex/config.toml` 获取 BenszAPI base URL，从 `~/.codex/auth.json` 获取 `OPENAI_API_KEY | OPENAI_API`，再使用 `gpt-image-2`；环境变量与 `remote.env` 只作为缺失字段的兜底来源。
3. `gpt-image-2` 只能绑定 `benszresearch.com` 子域名 base URL；非 HTTPS、裸域、非白名单域名或缺少 key 时不得绕过校验。
4. 如果用户点名 `gpt-image-2`、`Nano Banana`、`Gemini` 或其他具体 provider，运行前检查和后续出图都必须固定在该 provider；失败时输出可执行的配置/额度/端点错误，不自动切到另一个模型。
5. 只有用户主动要求允许回退时，才设置 `allow_provider_fallback=true` 或脚本参数 `--allow-provider-fallback`；回退路径使用 `~/.bensz-skills/config/remote.env` 中的 `GEMINI_BASE_URL`、`GEMINI_API | GEMINI_API_KEY`、`GEMINI_MODEL`。即使已授权，计费、订阅、余额、权限、overage 与 `BILLING_SERVICE_ERROR` 仍必须停在原 provider 并展示结构化错误。
6. 再运行 `scripts/nano_banana_check.py`。默认 `auto` 会按 provider 优先级检查配置、连接和鉴权；若用户指定 provider，应把 `--provider <name>` 传给主脚本。`/v1/models` 成功只能表述为 `connectivity/authentication_ok`，不得写成“可生图”或 `generation_eligible=true`；真实 Images submit 才是当前请求的准入判断。

## 工作流

1. **理解需求与模式**：宿主 AI 先把用户需求拆成“主体 / 结构 / 风格 / 硬约束 / 禁止项”，并解析 `mode`；未指定时用 `general`。需要时参考 `references/prompt-guidelines.md`。
2. **声明监督路径**：在正式动作开始前，宿主 AI 必须根据当前 `project_root` 与可选 `workspace_base` 计算 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot` 根目录绝对路径，并用可见消息告诉用户；初始化后可再补充实际 `run_dir`，但不能用 `run_dir` 补充替代启动前的 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot` 根目录声明。
3. **检查 API**：运行 `scripts/nano_banana_check.py`。若用户指定模型/provider，主流程必须传 `--provider <name>` 并只检查该 provider；若默认 `auto`，可按优先级选择一个连接与鉴权检查通过的 provider。此步骤不执行完整 Images 计费资格检查，不得把 `/v1/models` 成功描述为“当前请求可生图”；不要把“指定模型失败”改写成“自动使用另一个模型”。
4. **初始化隐藏工作区**：运行 `scripts/init_workspace.py`，默认建立 `.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/auto-draw-plot/{yyyy-mm-dd-hh-mm}/`，写出 `run-manifest.json`。
5. **生成 parallel-vibe 计划**：每一轮开始前，必须生成该轮的 `parallel-vibe` plan，至少写出：
   - `parallel-vibe/parallel-plan.round-XX.json`
   - `parallel-vibe/parallel-plan.json`（latest）
   - `rounds/round-XX/parallel-plan.json`
6. **生成第 1 轮 prompt**：
   - 优先由宿主 AI 在调用脚本前完成需求拆解与 prompt 规划；
   - `run_draw_plot.py` 只做本地模板拼装与护栏合并，不默认调用 Gemini / Nano Banana 等远端文本规划接口；
   - prompt 仍需忠实反映用户需求，不得暴露密钥或绝对路径。
7. **调用图片模型**：运行 `scripts/generate_image.py` 或主入口 `scripts/run_draw_plot.py`；`gpt-image-2` 纯文本出图默认提交到 `/images/jobs/generations`，存在参考图时默认提交到 `/images/jobs/edits`，同步端点只在 job endpoint 明确不支持时兼容回退。submit 在服务端尚无持久幂等契约时只提交一次；结构化 `retryable=false`（包括 `BILLING_PRICING_NOT_CONFIGURED`）立即停止，poll/result 的暂时故障独立处理。默认请求 `quality=low`、最小匹配原生尺寸和 `output_format=jpeg`，输出扩展名、magic bytes、MIME 与 meta 必须一致；PNG/WebP 回退结果导出 JPEG 时以白色合成透明背景。参考图编辑会追加“只改明确要求、保留主体/构图/背景”的契约，并记录原始参考图 SHA-256。
8. **视觉评估**：
   - `scripts/evaluate_image.py` 默认只做启发式文件/分辨率检查并标记 `fallback_mode=heuristic`，不调用 Gemini 文本接口；
   - 宿主 AI 必须根据最终图片、用户需求与 `evaluation.json` 做语义把关，必要时人工触发下一轮。
9. **多轮优化**：上一轮若未通过，第 `n+1` 轮必须把第 `n` 轮 `output.jpg` 作为第一参考图传给可消费参考图的图片 provider，并把反馈拼进 prompt，要求模型保真微调而不是从零重画；首轮用户参考图也必须标记为 `image-to-image`，来源使用 `user_reference` / `previous_round` / `mixed`。
10. **交付**：输出至少 1 张最终 JPEG；隐藏目录里保留 `meta/result.json` 供追溯。

## 模式说明

- `general`：通用绘图模式，适合普通信息图、封面图、概念图和自由描述。
- `roadmap`：技术路线图模式，强调 3-5 阶段、阶段标题条、主链箭头、风险/备选虚线、A4 打印可读；中文标签默认使用正常字宽。
- `schematic`：原理图/机制图模式，强调分组大框、圆角节点、机制链/模块关系、主链与辅助箭头分层；中文标签默认使用正常字宽。

`roadmap` / `schematic` 的文字策略：优先把标签自然换成 2-3 行，也不要横向压缩字形；默认使用现代黑体/思源黑体/Noto Sans CJK 风格的正常字宽、常规到半粗体。除非用户明确要求窄体标题或压缩排版，否则禁止窄体、长体、压缩体、condensed/narrow/compressed font、横向压缩和瘦长拉伸字体。

不要把 `roadmap` / `schematic` 回退成 draw.io、SVG/PDF 或 TEX 强绑定流程；这些 legacy 能力只作为 prompt 和评估经验迁移。

## parallel-vibe 必选层

- `parallel-vibe` 是必选层：即使宿主 AI 最终不真正启动 `parallel-vibe` CLI，也必须按它的 thread/workspace 协议为每一轮写出合法 `plan.json`。
- 主入口 `scripts/run_draw_plot.py` 已经会为每一轮自动生成 parallel-vibe plan，用户无需额外手工执行。
- 若宿主 AI 想把“下一轮 prompt 草案”真正交给独立线程处理，则直接复用该轮 `parallel-plan.round-XX.json`。
- `parallel-vibe` worker 当前仍只负责在隔离 workspace 里产出 prompt 草案与评估请求模板；真正的出图与评估继续由本 skill 的主脚本完成，避免跨 workspace 回写导致不稳定。

## 测试与验证

- 轻量测试必须在 `tests/draw-plot` 下完成；每次执行都应该在该目录内生成 `TEST_PLAN.md`/`TEST_REPORT.md`，并把中间文件限定在 `tests/draw-plot/_artifacts/`。
- auto-test-skill 的 A/B 轮也只能操作 tests 目录，确保 `p0-p2` 问题均闭环。

## 参考文件

- `references/prompt-guidelines.md`：prompt 结构模板与迭代策略。
- `references/parallel-plan.md`：合法的 `parallel-vibe` shell plan 模板，说明 thread 如何只负责 prompt 草案。
