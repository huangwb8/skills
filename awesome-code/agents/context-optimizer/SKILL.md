---
name: context-optimizer
description: "Use when long conversations degrade AI performance, context windows approach limits, or the agent forgets earlier information. Diagnoses lost-in-middle, context poisoning, and distraction problems, then applies compression, masking, or caching strategies to restore token efficiency."
metadata:
  short-description: 上下文管理与优化
  keywords:
    - context-optimizer
    - 上下文优化
    - token 效率
    - 长对话
    - 压缩策略
    - 缓存机制
    - 性能优化
    - 上下文窗口
  category: 性能优化
  author: Bensz Conan
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Context Optimizer - 上下文优化专家

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求"report bensz skills bugs"等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

## 工作流程

按以下步骤执行上下文优化：

### Step 1：诊断问题

检查对话是否存在以下症状：

| 问题类型 | 症状 | 严重程度 |
|---------|------|---------|
| **Lost-in-Middle** | AI 遗忘对话中间的关键信息；首尾记住但中间遗忘；用户需重复提问 | 高 |
| **Context Poisoning** | AI 产生矛盾回答；错误信息影响判断；不同来源信息冲突 | 高 |
| **Distraction** | 无关信息浪费 token；响应速度变慢 | 中 |
| **Context Clash** | 多信息源冲突；无法确定哪个版本正确 | 中 |

### Step 2：选择策略

根据诊断结果选择对应策略：

- **对话过长、token 接近上限** → 压缩策略
- **需要引用大量参考文档** → 掩码策略（按需加载）
- **反复查询相同内容** → 缓存策略
- **多种问题并存** → 按优先级组合使用：压缩 → 掩码 → 缓存

### Step 3：应用策略

#### 压缩策略

将对话历史按优先级分类并压缩：

1. 按 `current_task > decisions > errors > context` 优先级分类消息
2. 高优先级消息完整保留
3. 低优先级消息生成摘要（格式：`[摘要] 关键内容`）
4. 每 10 条消息生成一次增量摘要，保留任务、决策、错误、结果

#### 掩码策略

按需加载参考文档，避免一次性加载所有内容：

1. 仅加载相关性 > 0.7 的参考文档
2. 当前 token 使用率 < 80% 时才加载新内容
3. 已加载的内容复用，不重复加载

#### 缓存策略

缓存频繁访问的解析结果和内容：

1. 代码解析结果、配置数据等高频内容优先缓存
2. 按 `访问次数 × 优先级` 排序，淘汰低分项
3. 设置缓存上限，防止缓存本身成为负担

> 各策略的详细实现代码见 [references/strategies.md](references/strategies.md)。

### Step 4：验证效果

应用策略后，检查以下指标：

- [ ] 对话长度是否合理（token 使用率 < 80%）
- [ ] 关键决策和错误信息是否保留
- [ ] AI 是否仍能正确引用之前的信息
- [ ] 无关信息是否已过滤
- [ ] 参考文档是否按需加载（非一次性全部加载）
- [ ] 频繁访问内容是否已缓存

## 最佳实践

- **分阶段处理**：大文件先获取结构，再按 section 逐步加载分析，避免一次性读取全部内容
- **渐进式信息披露**：提供概述 + 文档链接（约 100 tokens），而非完整文档（10000+ tokens）
- **保留关键上下文**：压缩时始终保留当前任务、已做决策、已知错误

## 示例

**场景**：用户在 50 轮对话后，AI 遗忘了第 15 轮确定的数据库选型决策。

1. **诊断**：Lost-in-Middle — 中间决策被后续讨论淹没
2. **选择**：压缩策略 — 对话过长，需要精简历史
3. **应用**：将前 40 轮压缩为增量摘要，保留"决策：使用 PostgreSQL，原因是事务支持和 JSON 查询需求"，过滤无关的调试讨论
4. **验证**：压缩后 token 使用率从 95% 降至 60%，AI 能正确引用数据库选型决策

## 相关参考

- [策略详细实现](references/strategies.md)
- [上下文优化策略](../references/context-optimization.md)
- [多代理协调模式](../multi-agent-coordinator/SKILL.md)
