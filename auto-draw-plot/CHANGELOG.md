## [Unreleased]

### Changed
- 明确 `auto-draw-plot` 是经 BenszAPI 自行完成 prompt、generation/edit 与多轮迭代的自包含图片工作流；选中后不得默认调用或依赖 `imagegen`，并把版本号从 `0.2.13` 更新至 `0.2.14`

### Fixed
- 修复 Windows/Git Bash/PowerShell 可能因 HOME 与 USERPROFILE 不一致而读取旧 Codex 配置的问题：统一解析用户目录，检测 Codex 与 BenszAPI 环境变量的 Base URL/API Key 冲突，并在脱敏诊断证据中记录实际路径与 Key 短指纹；同步将版本号 `0.2.17 → 0.2.18`
- 修复 Codex 或环境变量提供 BenszAPI 子域名根地址时，Images job 请求可能落入边缘层 HTML fallback 的问题：`gpt-image-2` 配置加载会在完成 HTTPS、子域名与路径校验后统一补齐 `/v1`，generation/edit、轮询和结果下载均使用规范 API 基址；同步将版本号 `0.2.16 → 0.2.17`
- 补齐 Images submit 的端到端低敏关联证据：JSON 与 multipart 请求自动发送安全 `X-Client-Request-ID`，空/非 JSON 协议错误优先保存服务端回传的 `X-Request-ID` 与 `X-Client-Request-ID`，并对关联 ID 执行长度和字符白名单校验；同步将版本号 `0.2.15 → 0.2.16`
- 修复 Images generation/edit 在 `2xx` 空正文或非 JSON 正文时只抛出裸解析异常、无法关联边缘链路的问题：JSON 与 multipart 路径新增 `PROVIDER_EMPTY_RESPONSE` / `PROVIDER_NON_JSON_RESPONSE`，仅记录状态、origin/path、Content-Type、声明/实际长度、SHA-256、首字节类别和重定向变化；不保存 query、鉴权、prompt 或原始正文，并继续禁止 submit 重试及不确定任务跨 provider 重放；同步将版本号 `0.2.14 → 0.2.15`
- 修复 `gpt-image-2` 默认质量、格式、重试与参考图契约不完整的问题：generation/edit 显式发送 `quality=low`、`size=1024x1024`、`output_format=jpeg`，输出校验扩展名、magic bytes 和 MIME，参考图记录 SHA-256 与稳定来源；无持久幂等保证时 submit 只执行一次，静态计价错误立即停止；同步将版本号 `0.2.12 → 0.2.13`
- 修复 `gpt-image-2` 准入语义与错误分类缺陷：`/v1/models` 探测仅表示连接与鉴权可用，真实 Images submit 才决定当前请求是否具备生成资格；结构化保留 `error.type` / `error.code` / 安全 `error.message`，计费与权限 4xx 立即停止且即使用户允许 provider fallback 也不跨模型，异步 job 终态错误沿用同一分类；补充无联网回归测试并将版本号 `0.2.11 → 0.2.12`

### Added
- 新增图片尺寸元数据：每轮结果记录 `requested_provider_size`、`native_size`、`output_size`、`postprocess_resize_applied`，并补充 OpenAI generation/edit 原生尺寸保持、显式后处理、参考图校验的无联网单测
- 新增 `tests/nsfc-roadmap-schematic-v20260520144607/` 真实 NSFC 材料测试：分别使用 `roadmap` 与 `schematic` 模式复绘技术路线图和 SeqCCS 原理图，用于评估复杂中文科研插图生成效果
- 新增 `tests/cat-v20260520134108/` 小猫出图测试产物：包含最终 PNG、测试计划、测试报告与 `.draw-plot/` 追溯元数据，用于验证 `general` 模式调用 `gpt-image-2` 的基础出图链路

### Changed
- 收紧 `roadmap` / `schematic` 模式的正常字宽护栏：默认要求现代黑体/思源黑体/Noto Sans CJK 风格与自然字形比例，明确禁止窄体、长体、压缩体、condensed/narrow/compressed font、横向压缩和瘦长拉伸字体；同步更新 prompt 指南、负面 prompt 与 README，并将版本号 `0.2.10 → 0.2.11`
- 收紧 `roadmap` / `schematic` 模式的中文标签字重护栏：默认要求无衬线常规到半粗体、深灰或黑色文字，避免细体、浅灰字和过轻笔画导致的“字偏瘦”观感；同步更新 prompt 指南并将版本号 `0.2.9 → 0.2.10`
- 将 `gpt-image-2` generation/edit 默认提交方式改为 Sub2API 异步 image job endpoint：文本出图使用 `/images/jobs/generations`，参考图编辑使用 `/images/jobs/edits`；仅当 job endpoint 返回 404/405/501 且配置允许时回退旧同步接口，429/500/502/503/504 不触发同步回退；新增 `async-job-result.json` 结果下载证据与 run manifest 中的 async job 策略字段。同步将版本号 `0.2.8 → 0.2.9`
- 明确启动前监督路径声明规则：宿主 AI 在正式检查 API、初始化工作区或开始出图前，必须先向用户声明本次任务 `.draw-plot` 根目录的绝对路径；同步在配置中新增 `workspace.announce_absolute_path_before_start` 与声明模板，并将版本号 `0.2.7 → 0.2.8`
- 取消 gpt-image-2 与 Nano Banana/Gemini 路径的默认插值放大/贴画布行为，默认保留 provider 原生 PNG；`--canvas-width` / `--canvas-height` 改为布局比例和 provider 原生尺寸选择参考，只有显式 `--postprocess-resize --postprocess-width <W> --postprocess-height <H>` 才启用尺寸后处理；参考图上传前增加真实图片格式与大小上限校验。同步将版本号 `0.2.6 → 0.2.7`
- 为 `gpt-image-2` provider 增加异步图片任务兼容层：当 `/images/generations` 或 `/images/edits` 返回 job/task 状态而非直接图片时，按 `api.async_image_job` 配置轮询状态接口，直到得到图片、失败或超时。注意：这是早期被动兼容层，`0.2.9` 起已改为默认主动提交 Sub2API 异步 image job，以避免同步长请求导致 504；同步将版本号 `0.2.5 → 0.2.6`
- 将图片生成请求超时从 `180s` 调整为 `1800s`（30 分钟），用于适配高分辨率或服务端排队较久的出图请求。同步将版本号 `0.2.4 → 0.2.5`
- 修复 `gpt-image-2` 路径下文本规划与视觉评估仍调用 Gemini 的设计缺陷：脚本默认使用本地 prompt 模板与启发式评估，不再要求用户配置 Gemini；Gemini 只作为 Nano Banana 图片 provider 或显式允许的图片回退路径使用。同步将版本号 `0.2.3 → 0.2.4`
- 收紧图片 provider 回退规则：用户显式指定 `gpt-image-2` / `nano_banana` / Gemini 等模型时，运行前检查与出图过程都固定在该 provider，失败后不自动切换到其他模型；只有用户明确允许时才通过 `--allow-provider-fallback` 开启跨 provider 回退。同步将版本号 `0.2.2 → 0.2.3`
- 将默认画布策略调整为“中等分辨率优先跑通”：`roadmap` 从 `2400 x 2263` 降为 `1800 x 1697`，`schematic` 从 `3200 x 2000` 降为 `1920 x 1200`，`general` 保持 `1600 x 900`；README 新增快速草稿、默认、高清与 4K/A4 等分辨率档位说明；同步将版本号 `0.2.1 → 0.2.2`
- 为 `gpt-image-2` provider 增加参考图编辑路径：传入 `reference_images` 时优先调用 OpenAI-compatible `/images/edits` multipart 请求，纯文本出图继续使用 `/images/generations`；若当前 BenszAPI bridge 暂未实现编辑端点或请求失败，则保留 Nano Banana/Gemini 回退。同步将版本号 `0.2.0 → 0.2.1`
- 将多轮优化从“文本反馈后重新生成”改为连续 image-to-image 微调：第 2 轮起自动把上一轮 `output.png` 作为第一参考图，并使用上一轮评估反馈生成下一轮 prompt；若 image-to-image 轮次没有可消费参考图的 provider，则明确失败而不再静默从零重画
- 修复 `gpt-image-2` provider 的 Codex 本地凭据读取：默认优先使用 `~/.codex/config.toml` 与 `~/.codex/auth.json`，环境变量与 `remote.env` 只作为缺失字段兜底；同时为 BenszAPI HTTP 请求添加正常 `User-Agent`，避免默认 `Python-urllib` 指纹被 Cloudflare 拦截
- 规划支持 `general`、`roadmap`、`schematic` 三种绘图模式，默认保持通用模式；`roadmap` / `schematic` 吸收 legacy `nsfc-roadmap` 与 `nsfc-schematic` 的 PNG-only 画图约束，作为可扩展 preset 维护
- 图片模型调用优先尝试与 `benszresearch.com` 子域名绑定的 `gpt-image-2`，若本地 Codex / 环境配置不可用或 base URL 不在白名单内，则自动回退到既有 Nano Banana / Gemini 流程
- 加强 provider 与路径安全：记录每轮实际 provider、限制 GPT base URL path/query、脱敏 OpenAI 图片响应、默认禁止工作区/输出写到项目外，并修复 parallel-vibe plan shell quoting
- 使用 `parallel-vibe` + `auto-test-skill` 完成两轮 A 轮独立审查与 B 轮质量检查，新增可追溯 `plans/v202605200027.md`、`plans/v202605200036.md`、`plans/B轮-v202605200037.md` 与对应测试报告
- 将 `parallel-vibe` 从“可选协作层”上调为必选工作流层；`run_draw_plot.py` 现会为每一轮强制生成 `parallel-vibe/parallel-plan.json`、`parallel-vibe/parallel-plan.round-XX.json` 与 `rounds/round-XX/parallel-plan.json`
- 明确默认优化轮次的单一真相来源为 `config.yaml:generation.default_max_rounds`（默认 `3`），并同步更新 `SKILL.md`、README 与参考文档

## [0.1.0] - 2026-03-30

### Added
- 初始版本：新增 `auto-draw-plot` skill，支持从 `~/.bensz-skills/config/remote.env` 加载 Nano Banana/Gemini API，在 `.draw-plot/run-<timestamp>/` 中执行多轮 prompt 优化、PNG 生成和视觉评估闭环
- 新增 `scripts/init_workspace.py`、`scripts/nano_banana_check.py`、`scripts/generate_image.py`、`scripts/evaluate_image.py`、`scripts/run_draw_plot.py`、`scripts/build_parallel_plan.py`、`scripts/parallel_round_worker.py`
- 新增 `README.md`、`references/prompt-guidelines.md`、`references/parallel-plan.md`，覆盖默认工作流与 `parallel-vibe` 协作层
