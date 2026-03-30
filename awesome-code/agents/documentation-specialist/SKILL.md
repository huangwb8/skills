---
name: documentation-specialist
description: "Use when writing, restructuring, or reviewing technical documentation — generates READMEs, API docs, and user guides with clear structure, consistent formatting, and actionable content that lets readers install, use, and troubleshoot independently."
metadata:
  short-description: 技术文档与 API 文档
  keywords:
    - documentation-specialist
    - 文档
    - API 文档
    - README
    - 技术写作
    - 文档生成
    - OpenAPI
    - Markdown
    - 文档维护
  category: 文档
  author: Bensz Conan
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Documentation Specialist - 文档专家

目标：写出”可用、可维护、可验证”的技术文档，让用户能独立完成安装/使用/排错，让维护者能追溯变更与接口契约。

为满足社区推荐的 `SKILL.md` 500 行以内约束：长模板（README/OpenAPI/Sphinx/JSDoc 示例等）已下沉到 `awesome-code/agents/documentation-specialist/references/legacy-skill-full.md`。

## 何时使用

- 需要编写/重构 README、用户指南、开发者指南
- 需要生成/校正 API 文档（OpenAPI/Swagger）
- 需要把”隐含规则”变成可执行的文档约束与示例

## 工作流程

1. **收集上下文** — 确认目标读者（用户/开发者/运维）、现有文档、接口定义、CLI 参数和默认配置
2. **确定文档类型** — 根据需求选择输出格式：README、API 文档、用户指南等
3. **起草结构** — 按最小文档结构（见下方）规划章节，确保覆盖 What / Quickstart / Usage / Troubleshooting
4. **填充内容** — 遵循写作规则（正确性 > 可操作性 > 最小惊讶 > 可维护），每条命令和路径需可直接执行
5. **验证检查** — 确认所有命令可运行、路径存在、示例输出与实际一致；生成文档质量检查清单

## 输入

- 目标读者：用户 / 开发者 / 运维
- 当前状态：现有文档、接口、CLI 参数、默认配置
- 约束：目录结构、命名规范、版本来源（如 config.yaml）

## 输出

- README（快速开始 + 常见问题 + 约束/边界）
- API 文档（请求/响应 schema、错误码、示例、鉴权）
- 文档质量检查清单（可用于审查）

## 示例

**用户请求：**

> 我的 CLI 工具 `imgopt` 缺少 README，帮我写一份。它用 Python 写的，通过 `pip install imgopt` 安装，主命令是 `imgopt compress --input photo.png --quality 80`，输出压缩后的图片到 `./output/`。

**期望输出：**

```markdown
# imgopt

轻量级图片压缩 CLI 工具，支持 PNG/JPEG 批量压缩。

## 快速开始

pip install imgopt

## 使用方法

imgopt compress --input photo.png --quality 80

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| --input | 是 | — | 输入文件路径 |
| --quality | 否 | 85 | 压缩质量 (1-100) |

## 输出

压缩后文件保存到 `./output/`，保持原文件名。

## 常见问题

**Q: 提示 “FileNotFoundError”？**
A: 确认 --input 路径存在且有读取权限。
```

## 写作规则（优先级从高到低）

1. 正确性：与代码/配置一致；不写”猜测性承诺”
2. 可操作性：每一步都能照做（命令/路径/输入输出清晰）
3. 最小惊讶：默认行为符合直觉；不隐藏破坏性行为
4. 可维护：模板化结构 + 单一真相来源（例如版本号只在 config.yaml）

## 最小文档结构（推荐）

- What：它是什么，解决什么问题
- Quickstart：最短路径跑通
- Usage：常用用法与参数
- Outputs：输出文件/目录约定
- Troubleshooting：常见错误与定位
- Contributing（可选）：开发/测试/发布

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求”report bensz skills bugs”等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

