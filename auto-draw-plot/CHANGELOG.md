## [Unreleased]

### Added
- 新增 `tests/nsfc-roadmap-schematic-v20260520144607/` 真实 NSFC 材料测试：分别使用 `roadmap` 与 `schematic` 模式复绘技术路线图和 SeqCCS 原理图，用于评估复杂中文科研插图生成效果
- 新增 `tests/cat-v20260520134108/` 小猫出图测试产物：包含最终 PNG、测试计划、测试报告与 `.draw-plot/` 追溯元数据，用于验证 `general` 模式调用 `gpt-image-2` 的基础出图链路

### Changed
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
