# auto-draw-plot — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `auto-draw-plot` skill。执行规范在 `SKILL.md`；默认参数在 `config.yaml`。

## 快速开始

```text
请使用 auto-draw-plot skill 生成一张科研展示图。
输入：
- mode：general
- 需求：展示上下游信号链，6 个节点，用箭头连接，突出关键蛋白。
- 约束：白底，16:9，PNG，文字清晰，长边不低于 3840 px。
输出：至少 1 张可用 PNG；中间文件保存在 `.draw-plot/`。
```

技术路线图：

```text
请使用 auto-draw-plot skill 生成技术路线图。
输入：
- mode：roadmap
- 需求：把这段研究内容整理成 3-5 个阶段，突出主链、风险控制和备选方案。
输出：A4 缩印仍可读的白底 PNG。
```

原理图/机制图：

```text
请使用 auto-draw-plot skill 生成机制图。
输入：
- mode：schematic
- 需求：展示输入层、模型处理层、验证层和输出层之间的关系。
输出：分组清晰、箭头方向正确、中文标签可读的 PNG。
```

## 模式选择

| 你的需求 | 推荐 `mode` | 适合场景 |
| --- | --- | --- |
| 普通展示图、概念图、信息图 | `general` | 默认模式，最通用 |
| 技术路线图、roadmap、flowchart | `roadmap` | 阶段、任务、主链、风险/备选 |
| 原理图、机制图、架构图 | `schematic` | 模块分组、机制链、算法/实验闭环 |

`nsfc-roadmap` 和 `nsfc-schematic` 可作为别名触发对应模式，但这里只迁移 PNG-only 的 prompt 与评估经验，不再迁移 draw.io、SVG/PDF、TEX 抽取等 legacy 渲染栈。

## 模型优先级

图片生成默认按以下顺序选择：

| 优先级 | Provider | 要求 |
| --- | --- | --- |
| 1 | `gpt-image-2` | 必须绑定 `*.benszresearch.com` 子域名 base URL |
| 2 | Nano Banana / Gemini | 使用 `GEMINI_BASE_URL`、`GEMINI_API`、`GEMINI_MODEL` |

`gpt-image-2` 的 base URL 必须是 HTTPS 且形如 `https://api.benszresearch.com/v1`。裸域 `https://benszresearch.com`、非白名单域名、带 query/fragment 的 URL 都会被拒绝并回退。

## 配置

推荐配置在 `~/.bensz-skills/config/remote.env` 或环境变量中：

```bash
# gpt-image-2 主路径
OPENAI_BASE_URL=https://api.benszresearch.com/v1
OPENAI_API_KEY=你的密钥
OPENAI_IMAGE_MODEL=gpt-image-2

# Nano Banana/Gemini 回退路径
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_API=你的密钥
GEMINI_MODEL=nano-banana-preview
```

默认情况下，skill 会先读取本地 Codex 配置：从 `~/.codex/config.toml` 获取 BenszAPI base URL，从 `~/.codex/auth.json` 获取 `OPENAI_API_KEY` / `OPENAI_API`。只有 Codex 本地配置缺少对应字段时，才使用环境变量或 `remote.env` 作为兜底。

## 脚本用法

```bash
python3 auto-draw-plot/scripts/run_draw_plot.py \
  --mode roadmap \
  --request-text "画一张白底技术路线图：三阶段研究任务，包含风险控制和验证闭环。" \
  --output-png ./roadmap.png
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--mode` | `general` / `roadmap` / `schematic` |
| `--max-rounds` | 最大迭代轮数，默认 `3` |
| `--canvas-width` / `--canvas-height` | 覆盖模式默认画布 |
| `--reference-image` | 参考图；有参考图时优先使用 Nano Banana 路径 |
| `--api-env` | 自定义 env 文件 |
| `--allow-outside-project` | 允许输出或工作区写到 `project_root` 外部 |

检查 provider：

```bash
python3 auto-draw-plot/scripts/nano_banana_check.py
```

这个命令名保留旧兼容性，实际会检查当前图片 provider 优先级。

## 输出

- 最终 PNG：默认 `draw-plot.png`，或你传入的 `--output-png`
- 隐藏工作区：`.draw-plot/run-<timestamp>/`
- 追溯文件：`meta/analysis.json`、`meta/result.json`
- 每轮证据：`rounds/round-XX/prompt.txt`、`output.png`、`evaluation.json`
- provider 记录：`meta/result.json` 中的 `providers_used`

## FAQ

### Q：为什么有时会从 `gpt-image-2` 回退到 Nano Banana？

A：常见原因是 base URL 不在 `*.benszresearch.com` 白名单、缺少 key、生成接口临时失败，或你提供了参考图。

### Q：`roadmap` / `schematic` 会输出 draw.io 吗？

A：不会。它们现在是 `auto-draw-plot` 的特殊 PNG 模式；legacy draw.io/SVG/PDF 能力不在本 skill 内继续维护。

### Q：没有 Gemini 配置还能运行吗？

A：可以尝试用 `gpt-image-2` 出图；但文本规划和视觉评估缺 Gemini 时会降级到本地模板/启发式评估，最终仍建议由宿主 AI 或人工复核。
