# 检索策略指南

## 你的任务

根据目标技能的任务特征，**自主生成**高质量的检索词，避免回音室效应和营销陷阱。

---

## 核心原则

### 1. 多元化原则

**必须包含的检索词类型**：
- ✅ 任务特定："{model} for {task_type}"
- ✅ 社区反馈："{model} reddit experience"
- ✅ 缺点查询："{model} problems limitations"
- ✅ 对比查询："{model1} vs {model2}"

**避免的检索词类型**（营销陷阱）：
- ❌ "best practices"（营销内容太多）
- ❌ "official guide"（官方文档单独处理）
- ❌ "how to use"（低质量内容）

### 2. 厂商覆盖原则

即使目标厂商列表只有 1-2 个，也应该：
- 主动搜索"为什么不用其他厂商"
- 包含对比查询（vs 其他主流厂商）
- 理解用户为什么选择/不选择某个厂商

**目的**：避免回音室效应

### 3. 社区优先原则

**社区平台优先级**：
1. Reddit（r/LocalLLama, r/MachineLearning）
2. Hacker News
3. GitHub Issues
4. Stack Overflow

**检索词模板**：
```
"{model} reddit experience"
"{model} hacker news discussion"
"{model} github issues"
"{model} real world usage"
```

### 4. 缺点透明原则

**必须包含的缺点查询**：
```
"{model} disadvantages"
"{model} limitations"
"{model} problems"
"{model} not good for"
"why not {model}"
"{model} fails at"
```

---

## 自主规划流程

```
输入：task_features = {task_types: [...], complexity: "..."}
  ↓
步骤 1：分析任务特征
  - 主要任务类型是什么？
  - 复杂度如何？
  - 有什么特殊需求？
  ↓
步骤 2：为每个任务类型生成检索词
  - 任务特定查询（每个任务 2-3 个）
  - 社区反馈查询（每个任务 2 个）
  - 缺点查询（每个任务 1-2 个）
  ↓
步骤 3：生成对比查询
  - 如果单厂商：vs 主流对手
  - 如果多厂商：两两对比（最多 3 组）
  ↓
步骤 4：检查多样性
  - 是否包含社区查询？
  - 是否包含缺点查询？
  - 是否包含对比查询？
  ↓
输出：queries = [...]
```

---

## 示例

### 输入：文献综述技能
```
task_features = {
  task_types: ["文本生成", "数据处理", "联网搜索"],
  complexity: "high"
}
target_vendors = ["Anthropic", "OpenAI"]
```

### AI 自主生成的检索词
```python
queries = [
    # 文本生成 - 任务特定
    "Claude long text generation",
    "Opus literature review",
    "GPT-4 long text generation",
    "GPT-4o academic writing",

    # 文本生成 - 社区反馈
    "Claude long text reddit",
    "GPT-4 literature review experience",

    # 文本生成 - 缺点查询
    "Claude long text limitations",
    "GPT-4 coherence issues",

    # 数据处理 - 任务特定
    "Claude JSON processing",
    "GPT-4 structured output",

    # 数据处理 - 社区反馈
    "Claude data extraction reddit",

    # 联网搜索 - 任务特定
    "Claude web search",
    "GPT-4 browsing",

    # 对比查询
    "Claude vs GPT-4 literature review",
    "Opus vs GPT-4o long text",

    # 通用原则
    "LLM model selection academic writing"
]
```

---

## 检查清单

生成检索词后，检查：
- [ ] 是否包含社区反馈查询？
- [ ] 是否包含缺点查询？
- [ ] 是否包含对比查询？
- [ ] 是否避免了"best practices"等营销陷阱？
- [ ] 检索词数量是否在 15-30 之间（过多则精简）？

---

## 你需要自主判断的内容

1. **检索词数量**：根据任务复杂度调整（复杂任务多查询，简单任务少查询）
2. **检索词具体度**：根据任务类型调整（技术任务用术语，通用任务用描述）
3. **对比组合**：选择最有意义的对比（不一定要两两对比）
4. **是否需要跨语言**：某些国产模型可能需要中文检索词

---

## 与硬编码评分的配合

你的检索策略与 `scripts/score_sources.py` 的硬编码评分形成互补：

| 阶段 | 你的角色（自主规划） | 硬编码角色（稳定性） |
|------|---------------------|-------------------|
| 检索词生成 | ✅ 自主生成多样化检索词 | ❌ 不参与 |
| 搜索结果收集 | ✅ 收集所有相关结果 | ❌ 不参与 |
| **结果评分** | ❌ 不参与 | ✅ 硬编码公式评分 |
| 场景分析 | ✅ 自主识别和分类场景 | ❌ 不参与 |

记住：**检索策略没有标准答案，根据具体情况灵活调整**。
