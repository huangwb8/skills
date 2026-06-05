---
name: auto-draw-plot
description: 根据用户描述生成高质量绘图 prompt，并按通用、roadmap、schematic 模式调用 gpt-image-2 或 Nano Banana/Gemini 图片模型 API 迭代出满足视觉要求的 PNG 结果。
metadata:
  author: Bensz Conan
  short-description: 模式化需求理解 + multi-round prompt optimization + gpt-image-2/Nano Banana 生成 PNG
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

- 以用户需求为起点，构造适用于 Nano Banana/Gemini 图片模型的 prompt。
- 默认模式是 `general`；用户明确要技术路线图/roadmap/flowchart 时使用 `roadmap`，明确要原理图/机制图/架构图时使用 `schematic`。后续新增类型应作为 `config.yaml:modes.presets` 扩展，不改主流程。
- 默认通过 `scripts/run_draw_plot.py` 在独立隐藏工作区里完成“parallel-vibe 规划留痕 → prompt → 出图 → 视觉评估 → 继续/停止”的闭环；`parallel-vibe` 是必选工作流的一部分，不是可选增强。
- 默认工作区是当前目录下的 `.draw-plot/run-<timestamp>/`；所有中间文件必须留在隐藏目录里。轻量测试目录固定为 `./tests/draw-plot`。

## 输入

- `user_need`（必需）：自然语言描述的图像需求、输出用途、必要的视觉语义与格式要求。
- `mode`（可选）：`general` / `roadmap` / `schematic`；默认 `general`。模式只改变 prompt preset、默认画布和评估口径，不引入 legacy draw.io 渲染器。
- `api_config`（可选）：指向 `~/.bensz-skills/config/remote.env` 的路径；图片生成优先尝试 `gpt-image-2`，再回退 Nano Banana/Gemini。
- `max_rounds`（可选）：最大优化轮数，默认 3；若用户另有指定，以用户为准。
- `visual_constraints`（可选）：尺寸、比例、色调、字体等硬约束。
- `reference_images`（可选）：用于 prompt 引导的风格/布局图。
- `workspace_base`（可选）：用户显式指定的隐藏工作区根目录；未指定时使用当前目录 `.draw-plot/`。

## 输出

- 至少 1 张合乎需求的 `png` 图像。
- 隐藏目录里的 `meta/analysis.json` / `meta/result.json`：记录每轮 prompt、模型参数、AI 评价结论、最终选图和停止原因。
- 每轮目录：`rounds/round-XX/prompt.txt`、`rounds/round-XX/prompt-plan.json`、`rounds/round-XX/parallel-plan.json`、`rounds/round-XX/output.png`、`rounds/round-XX/evaluation.json` 以及 `image-debug/` / `evaluation-debug/`。
- run 级 `parallel-vibe/parallel-plan.json` 与 `parallel-vibe/parallel-plan.round-XX.json`：每轮必留痕的 parallel-vibe plan。

## 运行前检查

1. 默认优先读取本地 Codex 配置：从 `~/.codex/config.toml` 获取 BenszAPI base URL，从 `~/.codex/auth.json` 获取 `OPENAI_API_KEY | OPENAI_API`，再使用 `gpt-image-2`；环境变量与 `remote.env` 只作为缺失字段的兜底来源。
2. `gpt-image-2` 只能绑定 `benszresearch.com` 子域名 base URL；非 HTTPS、裸域、非白名单域名或缺少 key 时必须回退，不得绕过校验。
3. 回退路径使用 `~/.bensz-skills/config/remote.env` 中的 `GEMINI_BASE_URL`、`GEMINI_API | GEMINI_API_KEY`、`GEMINI_MODEL`。
4. 先运行 `scripts/nano_banana_check.py`。该脚本会按 provider 优先级检查可用图片模型；报告中不要泄露秘密，仅说明 provider、模型和 base URL。

## 工作流

1. **理解需求与模式**：宿主 AI 先把用户需求拆成“主体 / 结构 / 风格 / 硬约束 / 禁止项”，并解析 `mode`；未指定时用 `general`。需要时参考 `references/prompt-guidelines.md`。
2. **检查 API**：运行 `scripts/nano_banana_check.py`。如果 gpt-image-2 不满足 BenszAPI 白名单或不可用，自动尝试 Nano Banana；全部失败时才暂停并提示补配置。
3. **初始化隐藏工作区**：运行 `scripts/init_workspace.py`，默认建立 `.draw-plot/run-<timestamp>/`，写出 `run-manifest.json`。
4. **生成 parallel-vibe 计划**：每一轮开始前，必须生成该轮的 `parallel-vibe` plan，至少写出：
   - `parallel-vibe/parallel-plan.round-XX.json`
   - `parallel-vibe/parallel-plan.json`（latest）
   - `rounds/round-XX/parallel-plan.json`
5. **生成第 1 轮 prompt**：
   - 优先由宿主 AI 或 `run_draw_plot.py` 的 text-planner 生成结构化 prompt；
   - 若远端模型不支持文本规划，脚本会自动退化到本地模板拼装；
   - prompt 仍需忠实反映用户需求，不得暴露密钥或绝对路径。
6. **调用图片模型**：运行 `scripts/generate_image.py` 或主入口 `scripts/run_draw_plot.py`，优先尝试 BenszAPI 绑定的 `gpt-image-2`；生成失败则回退 Nano Banana，把 PNG 和 request/response debug 落到本轮目录。
7. **视觉评估**：
   - 优先让宿主 AI 或 `scripts/evaluate_image.py` 根据图片 + 用户需求做结构化评估；
   - 若远端文本评估失败，则回退到启发式评估并明确标记 `fallback_mode=heuristic`，此时应优先由宿主 AI 做最终把关。
8. **多轮优化**：上一轮若未通过，就把 `evaluation.json` 的 `must_fix` / `prompt_patch` 拼进下一轮 prompt；直到 AI 满意或达到 `max_rounds`。默认轮数是 3，单一真相来源是 `config.yaml:generation.default_max_rounds`。
9. **交付**：输出至少 1 张最终 PNG；隐藏目录里保留 `meta/result.json` 供追溯。

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
