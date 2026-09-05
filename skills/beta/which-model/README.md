# Which Model - 模型选择最佳实践调研工具

> 自动调研并生成技能的模型选择指南（WHICHMODEL 小节）

## 核心特性

### 🎯 混合模式设计

`which-model` 采用**混合模式**，结合 AI 自主规划的灵活性和硬编码评分的稳定性：

```
┌─────────────────────────────────────────────────────────────┐
│  AI 自主规划（灵活性）          硬编码稳定性（稳定性）        │
├─────────────────────────────────────────────────────────────┤
│  • 检索策略生成              • 来源可信度评分                │
│  • 场景识别与分析            • 营销倾向检测                  │
│  • 内容组织与展示            • 综合评分公式                  │
└─────────────────────────────────────────────────────────────┘
```

### ✨ 客观性保障

- ✅ **社区优先**：真实用户体验权重高于官方营销（社区 0.85 vs 官方 0.3）
- ✅ **缺点透明**：主动搜索模型缺点和批评，不回避争议
- ✅ **多源验证**：学术论文、社区讨论、技术博客交叉验证
- ✅ **披露透明**：覆盖范围、来源构成、局限性清晰展示

## 快速开始

```
请用 which-model 调研 systematic-literature-review 的模型选择最佳实践
```

## 功能概述

`which-model` 是一个**元技能**（meta-skill），用于：
1. **深度分析**目标技能的源代码（SKILL.md、config.yaml、scripts/）
2. **联网调研**模型选择最佳实践（使用 Tavily/SearXNG/DuckDuckGo）
3. **生成指南**并插入到目标技能的 README.md

### 核心价值

- ✅ **基于证据**：每条建议都有明确来源（官方文档/技术博客/社区经验）
- ✅ **自动更新**：模型建议随时间变化，可定期重新调研
- ✅ **结构化输出**：生成统一的 WHICHMODEL 小节格式
- ✅ **非破坏性**：不自动覆盖文档，需用户确认后插入
- ✅ **客观评分**：硬编码公式确保评分一致性

## 典型使用场景

### 场景一：为新技能生成模型指南

```
请用 which-model 调研我的新技能 xyz-skill
```

输出：
- `xyz-skill/WHICHMODEL_section.md`（可直接插入 README.md）
- `xyz-skill/skill_analysis.json`（技能分析结果）
- `xyz-skill/research_results.json`（调研原始数据）

**默认厂商**：Anthropic、OpenAI

### 场景二：指定目标厂商

```
请用 which-model 调研 xyz-skill，只关注 Anthropic 和 Google 的模型
```

或修改 `config.yaml`：

```yaml
research:
  target_vendors:
    - Anthropic
    - Google
```

**支持的厂商**：
- `Anthropic`（Claude 系列）
- `OpenAI`（GPT-4、GPT-4o、o1）
- `Google`（Gemini 系列）
- `Meta`（Llama 系列）
- `Mistral`（Mistral、Mixtral）
- `DeepSeek`（DeepSeek 系列）
- `Qwen`（阿里通义千问）
- `Moonshot`（月之暗面）
- `Zhipu`（智谱AI）

### 场景三：更新已有技能的模型指南

```
请用 which-model 重新调研 systematic-literature-review
```

行为：
- 检测到已有 WHICHMODEL 小节
- 询问：覆盖 / 追加 / 取消
- 选择后执行相应操作

### 场景四：查看调研过程

```
请用 which-model 调研 xyz-skill 并生成完整报告
```

输出：
- 所有中间结果（analysis、research、knowledge）
- `which_model_report.md`（完整调研报告）

## 工作流程

```
输入：目标技能名称
  ↓
阶段1：静态分析（analyze_skill.py）
  - 读取 SKILL.md、config.yaml、scripts/
  - 识别任务特征（文本生成/代码分析/联网搜索等）
  - 生成初步模型建议
  ↓
阶段2：模型调研（research_models.py）
  - 基于任务特征生成检索词
  - 使用 MCP 工具联网搜索
  - 收集官方文档与社区经验
  ↓
阶段3：知识提取（内部）
  - 从搜索结果中提取模型/参数建议
  - 识别常见模式
  ↓
阶段4：文档生成（generate_whichmodel.py）
  - 按 WHICHMODEL 模板组织内容
  - 生成 Markdown 格式的小节
  ↓
输出：WHICHMODEL_section.md
```

## WHICHMODEL 小节格式

生成的 WHICHMODEL 小节包含：

### 1. 场景化建议
每个场景包括：
- 典型使用场景描述
- 推荐模型（Opus/Sonnet/Haiku）
- 推荐参数（推理强度、Thinking 模式等）
- 理由
- 来源

### 2. 通用原则
总结 3-5 条核心原则，如：
- 复杂度与模型匹配
- 成本效益平衡
- 参数调优

### 3. 更新记录
记录每次更新的时间和内容

## 配置选项

编辑 `config.yaml` 自定义行为：

```yaml
# 调研参数
research:
  query_groups_per_task: 5      # 每个任务类型生成的检索词组数
  max_results_per_query: 10     # 每组检索词获取的最大结果数
  relevance_threshold: 0.6      # 相关度阈值

  # 目标模型厂商（开发者默认：Anthropic + OpenAI）
  # 支持的厂商：Anthropic、OpenAI、Google、Meta、Mistral、DeepSeek、Qwen、Moonshot、Zhipu
  target_vendors:
    - Anthropic      # Claude (Opus/Sonnet/Haiku)
    - OpenAI         # GPT-4/GPT-4o/o1
    # 可选：Google、Meta、Mistral、DeepSeek、Qwen、Moonshot、Zhipu

# 来源可信度评分（硬编码）
source_credibility:
  domain_weights:
    academic:
      weight: 1.0      # 学术论文权重最高
      domains: [arxiv.org, semanticscholar.org, ...]
    community_discussions:
      weight: 0.85     # 社区讨论权重高
      domains: [reddit.com, news.ycombinator.com, ...]
    official_docs:
      weight: 0.3      # 官方文档权重低（营销倾向）
      domains: [docs.anthropic.com, platform.openai.com, ...]

# 营销倾向检测（硬编码）
bias_detection:
  marketing_words:
    positive_excess: [revolutionary, state-of-the-art, ...]
    absolute_words: [best, perfect, always, ...]
  balanced_indicators: [however, limitation, drawback, ...]

# 综合评分公式（硬编码）
scoring:
  formula:
    relevance_weight: 0.30     # 相关性权重
    credibility_weight: 0.50   # 可信度权重（最高）
    neutrality_weight: 0.20    # 中立性权重

# MCP 工具优先级
mcp_tools:
  search_priority:
    - tavily-search
    - searxng_web_search
    - search

# 文档生成参数
document_generation:
  min_scenarios: 3              # 最小场景数
  max_scenarios: 8              # 最大场景数

# 插入策略
insertion:
  auto_insert: false            # 自动插入（false = 需用户确认）
  on_existing: prompt           # 已存在时的行为
```

## 输出文件说明

| 文件 | 说明 | 是否必需 |
|------|------|---------|
| `WHICHMODEL_section.md` | 生成的 WHICHMODEL 小节 | ✅ 必需 |
| `skill_analysis.json` | 技能分析结果（任务特征、初步建议） | ✅ 必需 |
| `research_results.json` | 调研原始数据（搜索结果、相关性评分） | ✅ 必需 |
| `which_model_report.md` | 完整调研报告（可选） | ⚠️ 可选 |

## 与其他技能的协同

### 作为前置步骤
`which-model` 通常在技能开发/优化阶段使用：

```
开发新技能 → 运行 which-model → 将 WHICHMODEL 插入 README → 用户获得模型选择指南
```

### 定期更新
建议每 3-6 个月重新运行一次，以获取最新的模型建议：

```
请用 which-model 重新调研 xyz-skill，覆盖已有 WHICHMODEL 小节
```

## 注意事项

### 1. MCP 工具依赖
- 优先使用 Tavily（深度搜索）
- 如 Tavily 不可用，降级到 SearXNG
- 如都不可用，使用内置搜索（功能受限）

### 2. 非破坏性操作
- 默认不自动插入文档
- 需用户确认后才修改 README.md
- 建议先查看 `WHICHMODEL_section.md` 再决定

### 3. 证据要求
- 每条建议必须有明确来源
- 如搜索结果不足，会提示用户手动补充
- 不生成猜测性的建议

## 常见问题

### Q1: 为什么我的技能没有生成任何建议？
A: 可能原因：
- 任务特征识别失败（检查 SKILL.md 是否清晰）
- 搜索结果相关性太低（检查 `config.yaml` 的 `relevance_threshold`）
- MCP 工具不可用（检查 MCP 连接）

### Q2: WHICHMODEL 小节应该插入 README.md 的哪个位置？
A: 推荐位置（按优先级）：
1. "档位选择指南"之后
2. "设计理念"之后
3. "快速开始"之后

### Q3: 如何自定义 WHICHMODEL 模板？
A: 编辑 `references/WHICHMODEL_template.md`，修改格式和内容结构。

### Q4: 生成的建议是否准确？
A: 取决于：
- 搜索结果的质量（官方文档 > 技术博客 > 社区经验）
- 任务特征的识别准确性（SKILL.md 描述清晰度）
- 建议：人工审核后再插入 README.md

## 维护者信息

### 脚本文件
- `scripts/analyze_skill.py`：分析技能源代码
- `scripts/research_models.py`：执行联网搜索
- `scripts/generate_whichmodel.py`：生成 WHICHMODEL 小节

### 参考文件
- `references/WHICHMODEL_template.md`：WHICHMODEL 模板
- `config.yaml`：可配置参数

---

**最后更新**：2025-01-03
**技能版本**：1.0.0

## 使用示例

### 示例 1：默认配置（Anthropic + OpenAI）

```bash
# 用户提示
请用 which-model 调研 systematic-literature-review

# AI 执行流程
1. 分析 systematic-literature-review/SKILL.md
   → 任务类型：文本生成、数据处理
   → 复杂度：high

2. 生成检索词（包含 Anthropic 和 OpenAI 模型）
   - "Claude long text generation"
   - "GPT-4 long text generation"
   - "Claude vs GPT-4 comparison"
   - ...

3. 联网搜索并收集最佳实践

4. 生成 WHICHMODEL_section.md
```

**生成的 WHICHMODEL 小节示例**：

```markdown
## WHICHMODEL - 模型选择最佳实践

### 场景 1：标准综述生成
- **推荐模型**：Claude Sonnet 4.5
- **推荐参数**：
  - 推理强度：medium
  - Thinking 模式：关
- **理由**：平衡性能与成本，适用于大多数综述任务
- **来源**：[Anthropic 官方文档]

### 场景 2：相关性评分
- **推荐模型**：Claude Haiku 4.5
- **推荐参数**：
  - 推理强度：low
  - Thinking 模式：关
- **理由**：结构化任务，快速响应优先
- **来源**：[社区经验]
```

### 示例 2：仅关注 Anthropic

**修改 config.yaml**：

```yaml
research:
  target_vendors:
    - Anthropic
```

**或直接指定**：

```bash
请用 which-model 调研 systematic-literature-review，只关注 Anthropic 的模型
```

**生成的检索词**：
- "Claude Opus literature review"
- "Claude Sonnet vs Haiku"
- "Claude model selection guide"

**不会出现**：
- ❌ "GPT-4 literature review"
- ❌ "Claude vs GPT-4 comparison"

### 示例 3：多厂商对比

**修改 config.yaml**：

```yaml
research:
  target_vendors:
    - Anthropic
    - OpenAI
    - Google
```

**生成的检索词包括**：
- "Claude vs GPT-4 comparison"
- "Claude vs Gemini comparison"
- "GPT-4 vs Gemini which is better"

### 示例 4：国产模型

**修改 config.yaml**：

```yaml
research:
  target_vendors:
    - Anthropic
    - DeepSeek
```

**生成的检索词包括**：
- "Claude long text generation"
- "DeepSeek long text generation"
- "Claude vs DeepSeek comparison"

### 示例 5：开源模型

**修改 config.yaml**：

```yaml
research:
  target_vendors:
    - Meta      # Llama 系列
    - Mistral   # Mistral/Mixtral
```

**生成的检索词包括**：
- "Llama 3 code analysis"
- "Mistral Large complex reasoning"
- "Llama vs Mistral comparison"

## 支持的厂商对照表

| 厂商 | 模型名称 | 代码中的标识 |
|------|---------|-------------|
| Anthropic | Claude, Opus, Sonnet, Haiku | `Anthropic` |
| OpenAI | GPT-4, GPT-4o, o1 | `OpenAI` |
| Google | Gemini, Gemini Pro, Gemini Ultra | `Google` |
| Meta | Llama, Llama 2, Llama 3 | `Meta` |
| Mistral | Mistral, Mixtral, Mistral Large | `Mistral` |
| DeepSeek | DeepSeek, DeepSeek-V2, DeepSeek-Coder | `DeepSeek` |
| 阿里云 | 通义千问, Qwen, Qwen-Max | `Qwen` |
| 月之暗面 | Moonshot, Kimi | `Moonshot` |
| 智谱AI | GLM, ChatGLM | `Zhipu` |

---

## 设计理念：混合模式

### 为什么采用混合模式？

**纯 AI 自主规划的问题**：
- ❌ 评分不稳定，每次执行可能不同
- ❌ 容易受到提示词波动影响
- ❌ 难以追溯评分依据

**纯硬编码规则的问题**：
- ❌ 缺乏灵活性，无法适应新场景
- ❌ 维护成本高，每次调整需要修改代码
- ❌ 无法处理边界情况

**混合模式的优势**：
- ✅ **灵活性与稳定性兼备**：AI 自主规划策略，硬编码确保评分一致
- ✅ **可追溯性**：评分公式固定，便于调试和验证
- ✅ **可维护性**：策略调整只需更新 references/，评分调整只需修改 config.yaml

### AI 自主规划部分

**参考资料**（AI 执行前阅读）：
- [references/SEARCH_STRATEGY.md](references/SEARCH_STRATEGY.md) - 检索策略指南
- [references/SCENARIO_ANALYSIS.md](references/SCENARIO_ANALYSIS.md) - 场景分析指南
- [references/CONTENT_ORGANIZATION.md](references/CONTENT_ORGANIZATION.md) - 内容组织指南

**自主规划内容**：
- 检索词生成（任务特定、社区反馈、缺点查询、对比查询）
- 场景识别与分类
- 内容组织与展示

### 硬编码稳定性部分

**配置文件**（[config.yaml](config.yaml)）：
```yaml
# 来源可信度权重
source_credibility.domain_weights:
  academic: {weight: 1.0}
  community_discussions: {weight: 0.85}
  official_docs: {weight: 0.3}

# 营销倾向检测关键词
bias_detection.marketing_words:
  positive_excess: [revolutionary, state-of-the-art, ...]
  absolute_words: [best, perfect, ...]

# 综合评分公式
scoring.formula:
  relevance_weight: 0.30
  credibility_weight: 0.50
  neutrality_weight: 0.20
```

**评分脚本**（[scripts/score_sources.py](scripts/score_sources.py)）：
- 硬编码评分公式：`final_score = relevance × 30% + credibility × 50% + neutrality × 20%`
- 硬编码域名权重映射
- 硬编码营销倾向检测逻辑

---

## 检索词生成逻辑

### 单厂商（如仅 Anthropic）

```
任务类型：文本生成
厂商：Anthropic

生成检索词：
- Claude long text generation
- Opus long text generation
- Claude writing best practice
- Opus writing best practice
- Claude content generation
- Opus content generation
+ 通用参数查询（3 条）
= 9 条检索词
```

### 双厂商（Anthropic + OpenAI）

```
任务类型：文本生成
厂商：Anthropic, OpenAI

生成检索词：
- Claude long text generation
- Opus long text generation
- GPT-4 long text generation
- GPT-4o long text generation
- ... (每个模型 × 每个模板)
+ Claude vs GPT-4 comparison (跨厂商对比)
+ Claude or GPT-4 which is better
+ 通用参数查询（3 条）
= 17 条检索词
```

### 多厂商（6 个厂商）

```
任务类型：文本生成
厂商：Anthropic, OpenAI, Google, Meta, Mistral, DeepSeek

生成检索词：
- 每个厂商 2 个模型 × 3 个模板 = 36 条
- 跨厂商对比（最多 2 组）= 4 条
- 通用参数查询 = 3 条
= 43 条检索词
```

## 最佳实践

### 1. 厂商数量建议

| 厂商数量 | 适用场景 | 检索词数量 |
|---------|---------|-----------|
| 1 个 | 专注单一生态 | ~9 条 |
| 2-3 个 | 常规对比 | ~17-25 条 |
| 4-6 个 | 全面调研 | ~30-45 条 |

### 2. 厂商选择建议

**如果你主要使用**：
- Claude Code → `Anthropic`
- GitHub Copilot → `OpenAI`
- Gemini API → `Google`
- 自部署模型 → `Meta`, `Mistral`
- 国内服务 → `DeepSeek`

### 3. 性能与成本

更多厂商 = 更多检索词 = 更长的调研时间

建议：
- 初次调研：1-2 个厂商
- 更新已有指南：保持原配置
- 全面对比：不超过 4 个厂商
