# write-readme — GitHub 项目 README 写作指南

`write-readme` 帮你为项目生成两份对齐的说明文档：中文 `README.md` 与英文 `README_EN.md`。它会先读取仓库事实，再按项目类型组织 Quick Start、示例、配置、限制、安全、贡献和许可证。

## 快速开始

```text
请使用 write-readme skill 为 /path/to/project 写好 GitHub README。
先根据仓库事实选择合适模板，输出中文 README.md 和英文 README_EN.md，二者章节、命令、链接和事实完全对齐。
```

如果是 Agent Skill：

```text
请使用 write-readme skill 为 skills/beta/my-skill 生成用户指南。
读取 SKILL.md、config.yaml、scripts/ 和 references/，输出 README.md（中文）与 README_EN.md（英文）；不要修改 Skill 源代码。
```

## 它会怎么写

README 的第一屏回答三件事：项目是什么、为什么值得用、怎样在最短路径跑起来。后面按任务组织示例，再逐步展开架构、部署、限制和贡献说明。不能从代码或配置验证的功能、数字、徽章和命令会被标记为待确认，而不是猜出来。

### 模板选择

| 项目形态 | 首屏重点 | 参考模板 |
|---|---|---|
| Python/JS/Rust 库或 SDK | 安装 + 最小 API + 支持版本 | `references/templates/library.md` |
| CLI、HTTP 服务或 Worker | 一条命令运行 + 配置 + 健康检查 | `references/templates/cli-service.md` |
| Web/桌面应用 | 截图或 Demo + 用户体验路径 + 部署 | `references/templates/web-app.md` |
| 数据集、训练或推理项目 | 数据/模型许可 + 复现实验 + 资源需求 | `references/templates/data-ml.md` |
| Agent Skill 或插件 | 触发 Prompt + 输入输出 + 宿主安装 | `references/templates/agent-skill.md` |

## 推荐检查点

- Quick Start 能从干净环境走完，且写清前置条件和预期结果。
- 示例优先使用最小可运行代码；复杂内容链接到更深文档。
- 徽章、图片、链接、版本和性能数字都有仓库或公开来源。
- 中文和英文标题树、代码块、命令、环境变量、路径、链接和许可证保持一致。
- 限制、安全、数据许可和未验证事项说清楚，不用营销话术代替证据。

## 生成后的确定性检查

```bash
# 在项目根目录执行
python3 /path/to/write-readme/scripts/check_readme_pair.py README.md README_EN.md
```

脚本检查文件、标题树、代码围栏、相对链接和命令/环境变量 token 漂移；它不代替人工判断语义是否准确。

## 可选的运行时验证

安装 `bensz-skill-kernel` 的宿主可读取 `config.yaml.runtime`，按
`input-ready → facts-collected → bilingual-draft-ready → delivery-ready → reported`
记录领域阶段。`bensz.document.readme-pair-alignment` 负责确定性双语结构检查，路径范围、
文件存在、Markdown 链接、脱敏和证据来源复用 Kernel 原子 Verifier。结构错误、越界或敏感
信息命中会阻止交付；token 漂移、网络不可观测和事实语义缺口保留为不确定项并转人工复核。
没有 Kernel 时仍可运行上面的脚本，但不能声称已完成运行时 Gate。

## 常见问题

### 为什么一定有两个 README？

中文版本服务中文读者，英文版本方便国际协作；二者共享同一事实和结构，避免一边更新、一边过期。

### 项目没有截图或在线 Demo 怎么办？

不虚构视觉材料。改用最小终端输出、API 响应或真实示例，并说明当前没有 Demo。

### 能只写英文吗？

可以在明确需求下只交付英文，但本仓库默认契约仍是双语；若省略中文，应在任务摘要中记录例外。

### 旧的 `write-skill-readme` 还能用吗？

它的 Agent Skill README 能力已经并入本 Skill。旧目录作为 legacy 源码保留，安装器不再默认安装，并会在安装时清理系统级旧目录。

## 更多文档

- `SKILL.md`：AI 执行契约与安全边界
- `references/readme-principles.md`：社区与 Trending 调研提炼
- `references/research-notes.md`：来源和样本记录
- `references/templates/`：不同项目类型的章节骨架
- `scripts/check_readme_pair.py`：双语 README 结构检查
- `references/states/` 与 `references/verifiers/`：可选 Kernel 阶段和验证契约
