---
name: auto-draw-plot
description: 根据用户描述生成高质量绘图 prompt，并按通用、roadmap、schematic 模式调用 gpt-image-2 或 Nano Banana/Gemini 图片模型 API；第 2 轮起基于上一轮 PNG 做 image-to-image 微调，迭代出满足视觉要求的 PNG 结果。
metadata:
  author: Bensz Conan
  short-description: 模式化需求理解 + multi-round image-to-image optimization + gpt-image-2/Nano Banana 生成 PNG
  keywords:
    - auto-draw-plot
    - nano-banana
    - gemini
    - parallel-vibe
    - visual evaluation
    - 图像生成
---

# Auto Draw Plot

## 与 bensz-collect-bugs 的协作约定

- 如果用户环境里出现因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，禁止直接修改用户本地 Claude Code/Codex 已安装的 skill 源码。
- 只在用户明确要求“report bensz skills bugs”时，才通过本地 `gh` 调用将新 bug 推送到 `huangwb8/bensz-bugs`；上传前必须先脱敏本地路径/用户名等隐私。

## 定位

- 以用户需求为起点，由宿主 AI 进行语义规划，再构造适用于当前图片 provider 的 prompt；脚本默认不调用额外 Gemini 文本接口。
- 默认模式是 `general`；用户明确要技术路线图/roadmap/flowchart 时使用 `roadmap`，明确要原理图/机制图/架构图时使用 `schematic`。后续新增类型应作为 `config.yaml:modes.presets` 扩展，不改主流程。
- 默认通过 `scripts/run_draw_plot.py` 在独立隐藏工作区里完成“parallel-vibe 规划留痕 → prompt → 出图 → 视觉评估 → 继续/停止”的闭环；`parallel-vibe` 是必选工作流的一部分，不是可选增强。
- 默认工作区是当前目录下的 `.draw-plot/run-<timestamp>/`；所有中间文件必须留在隐藏目录里。宿主 AI 在正式检查 API、初始化工作区或开始出图前，必须先向用户明确声明本次任务 `.draw-plot` 根目录的绝对路径，方便用户实时监督。轻量测试目录固定为 `./tests/draw-plot`。

## 输入

- `user_need`（必需）：自然语言描述的图像需求、输出用途、必要的视觉语义与格式要求。
- `mode`（可选）：`general` / `roadmap` / `schematic`；默认 `general`。模式只改变 prompt preset、默认画布和评估口径，不引入 legacy draw.io 渲染器。
- `api_config`（可选）：指向 `~/.bensz-skills/config/remote.env` 的路径；默认 `auto` 只在运行前按优先级选择可用 provider。
- `image_provider`（可选）：用户明确指定的图片模型/provider，如 `gpt-image-2` 或 `nano_banana`。显式指定后必须只用该 provider，失败时暂停并报告原因，不得切换到其他模型。
- `allow_provider_fallback`（可选）：只有用户明确说“失败可以换模型/可以回退到另一个 provider”时才为 true。
- `max_rounds`（可选）：最大优化轮数，默认 3；若用户另有指定，以用户为准。
- `visual_constraints`（可选）：比例、期望布局、色调、字体等硬约束。尺寸只作为 provider 原生尺寸选择参考，不承诺最终 PNG 像素。
- `reference_images`（可选）：用于 prompt 引导的风格/布局图；第 2 轮起上一轮 `output.png` 会自动作为第一参考图，用户参考图排在其后。
- `workspace_base`（可选）：用户显式指定的隐藏工作区根目录；未指定时使用当前目录 `.draw-plot/`。

## 输出

- 至少 1 张合乎需求的 `png` 图像。
- 隐藏目录里的 `meta/analysis.json` / `meta/result.json`：记录每轮 prompt、模型参数、参考图策略、评估结果、最终选图和停止原因。
- 每轮图片 meta 必须区分 `requested_provider_size`、`native_size`、`output_size` 与 `postprocess_resize_applied`；默认 `postprocess_resize_applied=false`。
- 每轮目录：`rounds/round-XX/prompt.txt`、`rounds/round-XX/prompt-plan.json`、`rounds/round-XX/parallel-plan.json`、`rounds/round-XX/output.png`、`rounds/round-XX/evaluation.json` 以及 `image-debug/` / `evaluation-debug/`；`gpt-image-2` 默认主动使用 Sub2API image job endpoint，`image-debug/request.json`、`async-job-initial.json`、`async-job-polls.json` 与成功下载时的 `async-job-result.json` 必须保留完整证据。
- run 级 `parallel-vibe/parallel-plan.json` 与 `parallel-vibe/parallel-plan.round-XX.json`：每轮必留痕的 parallel-vibe plan。

## 运行前检查

1. 先解析本次任务的隐藏工作区根目录：若用户传入 `workspace_base`，解析该路径；否则使用 `project_root/.draw-plot`。必须把解析后的绝对路径用可见消息告诉用户，例如：`本次 auto-draw-plot .draw-plot 工作区绝对路径：/abs/project/.draw-plot`。这条消息必须出现在 API 检查、`init_workspace.py`、`run_draw_plot.py` 或任何图片生成调用之前；不要只把路径写进 `run-manifest.json`。
2. 默认优先读取本地 Codex 配置：从 `~/.codex/config.toml` 获取 BenszAPI base URL，从 `~/.codex/auth.json` 获取 `OPENAI_API_KEY | OPENAI_API`，再使用 `gpt-image-2`；环境变量与 `remote.env` 只作为缺失字段的兜底来源。
3. `gpt-image-2` 只能绑定 `benszresearch.com` 子域名 base URL；非 HTTPS、裸域、非白名单域名或缺少 key 时不得绕过校验。
4. 如果用户点名 `gpt-image-2`、`Nano Banana`、`Gemini` 或其他具体 provider，运行前检查和后续出图都必须固定在该 provider；失败时输出可执行的配置/额度/端点错误，不自动切到另一个模型。
5. 只有用户主动要求允许回退时，才设置 `allow_provider_fallback=true` 或脚本参数 `--allow-provider-fallback`；回退路径使用 `~/.bensz-skills/config/remote.env` 中的 `GEMINI_BASE_URL`、`GEMINI_API | GEMINI_API_KEY`、`GEMINI_MODEL`。
6. 再运行 `scripts/nano_banana_check.py`。默认 `auto` 会按 provider 优先级检查可用图片模型；若用户指定 provider，应把 `--provider <name>` 传给主脚本，报告中不要泄露秘密，仅说明 provider、模型和 base URL。

## 工作流

1. **理解需求与模式**：宿主 AI 先把用户需求拆成“主体 / 结构 / 风格 / 硬约束 / 禁止项”，并解析 `mode`；未指定时用 `general`。需要时参考 `references/prompt-guidelines.md`。
2. **声明监督路径**：在正式动作开始前，宿主 AI 必须根据当前 `project_root` 与可选 `workspace_base` 计算 `.draw-plot` 根目录绝对路径，并用可见消息告诉用户；初始化后可再补充实际 `run_dir`，但不能用 `run_dir` 补充替代启动前的 `.draw-plot` 根目录声明。
3. **检查 API**：运行 `scripts/nano_banana_check.py`。若用户指定模型/provider，主流程必须传 `--provider <name>` 并只检查该 provider；若默认 `auto`，可按优先级选择一个运行前可用 provider。不要把“指定模型失败”改写成“自动使用另一个模型”。
4. **初始化隐藏工作区**：运行 `scripts/init_workspace.py`，默认建立 `.draw-plot/run-<timestamp>/`，写出 `run-manifest.json`。
5. **生成 parallel-vibe 计划**：每一轮开始前，必须生成该轮的 `parallel-vibe` plan，至少写出：
   - `parallel-vibe/parallel-plan.round-XX.json`
   - `parallel-vibe/parallel-plan.json`（latest）
   - `rounds/round-XX/parallel-plan.json`
6. **生成第 1 轮 prompt**：
   - 优先由宿主 AI 在调用脚本前完成需求拆解与 prompt 规划；
   - `run_draw_plot.py` 只做本地模板拼装与护栏合并，不默认调用 Gemini / Nano Banana 等远端文本规划接口；
   - prompt 仍需忠实反映用户需求，不得暴露密钥或绝对路径。
7. **调用图片模型**：运行 `scripts/generate_image.py` 或主入口 `scripts/run_draw_plot.py`；`gpt-image-2` 纯文本出图默认提交到 `/images/jobs/generations`，存在参考图时默认提交到 `/images/jobs/edits`，同步 `/images/generations` / `/images/edits` 只在 job endpoint 明确返回 404/405/501 且配置允许时作为兼容回退。429、500、502、503、504 不得改走同步接口，应按 async job 提交失败重试或报错。`--canvas-width` / `--canvas-height` 只表达期望布局比例，并映射到 provider 支持的原生尺寸；默认直接保存 provider 返回的 PNG，不插值放大、不贴到伪 4K 画布。只有用户明确要求统一导出尺寸时，才可使用 `--postprocess-resize --postprocess-width <W> --postprocess-height <H>`，并必须在 meta 中保留后处理记录。若 `gpt-image-2` 返回 job/task 状态、内联 `response` 或 `result_url`，脚本按 `config.yaml:api.async_image_job` 轮询/下载，直到拿到图片、任务失败或超时。默认不在生成/编辑失败后跨 provider 重试；只有用户明确授权时才加 `--allow-provider-fallback`，否则把失败原因和 debug 落到本轮目录后暂停。
8. **视觉评估**：
   - `scripts/evaluate_image.py` 默认只做启发式文件/分辨率检查并标记 `fallback_mode=heuristic`，不调用 Gemini 文本接口；
   - 宿主 AI 必须根据最终 PNG、用户需求与 `evaluation.json` 做语义把关，必要时人工触发下一轮。
9. **多轮优化**：上一轮若未通过，第 `n+1` 轮必须把第 `n` 轮 `output.png` 作为第一参考图传给可消费参考图的图片 provider，并把第 `n` 轮 `evaluation.json` 的 `must_fix` / `prompt_patch` 拼进 prompt，要求模型在上一张图上做 image-to-image 微调，而不是从零重画；直到 AI 满意或达到 `max_rounds`。默认轮数是 3，单一真相来源是 `config.yaml:generation.default_max_rounds`。
10. **交付**：输出至少 1 张最终 PNG；隐藏目录里保留 `meta/result.json` 供追溯。

## 模式说明

- `general`：通用绘图模式，适合普通信息图、封面图、概念图和自由描述。
- `roadmap`：技术路线图模式，吸收 legacy `nsfc-roadmap` 的 PNG-only 约束；强调 3-5 阶段、阶段标题条、主链箭头、风险/备选虚线、A4 打印可读。
- `schematic`：原理图/机制图模式，吸收 legacy `nsfc-schematic` 的 PNG-only 约束；强调分组大框、圆角节点、机制链/模块关系、主链与辅助箭头分层。

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
