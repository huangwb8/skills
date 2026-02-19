# Awesome Code — 用户使用指南

本 README 面向**使用者**：如何触发并正确使用 `awesome-code` skill。

> **致谢**：本项目参考了 [obra/superpowers](https://github.com/obra/superpowers) 项目的设计理念和工作流程，部分代理技能借鉴了该项目的最佳实践。

执行指令与硬性规范在 `SKILL.md`；默认参数在 `config.yaml`。

---

## 快速开始（推荐用法）

### 开放性探索（最推荐）

当你不确定项目需要什么样的优化时，让 AI 来分析和决定：

```
请使用awesome-code这个skill帮我全面分析并优化这个项目。

技能将自动：
1. 分析项目结构和技术栈
2. 识别需要改进的维度（代码质量、架构、安全性、性能等）
3. 调用相应的专业代理处理问题
4. 按优先级执行优化
5. 验证变更不破坏现有功能
```

**其他等效写法**：
```
请使用 awesome-code 帮助改进这个项目。
```

```
这个项目可能存在一些代码质量问题，请帮我发现并修复它们。
```

### 让 Claude 自动处理特定任务

```
你：使用 TDD 方式实现用户登录功能

技能将自动：
1. 激活 TDD 工作流
2. 编写第一个失败测试（Red）
3. 运行测试确认失败
4. 编写最小实现（Green）
5. 运行测试确认通过
6. 重构代码（Refactor）
7. 重复直到功能完成
```

### 调试 Bug：系统化定位根因

```
你：生产环境出现 500 错误，堆栈信息如下：...

技能将自动：
1. 分析堆栈追踪
2. 形成假设
3. 设计验证实验
4. 定位根因（非症状）
5. 实施修复
6. 添加回归测试
```

### 技能优化：批判性思维 A/B 轮测试

```
你：使用 A/B 轮测试优化这个技能

技能将自动：
1. 初始化测试会话（plans/ + tests/）
2. 使用批判性思维框架分析问题
3. 生成 A 轮改进计划（≥ 10 个问题，P0+P1 ≥ 60%）
4. 执行优化并轻量测试
5. 重复 A 轮（如需要）
6. B 轮七大质量原则检查
7. 修复所有 P0 和 P1 问题
8. 生成可追溯的完整报告
```

---

## 设计理念

**Awesome Code** 是一个智能的多代理协调系统，基于社区最佳实践，通过**自动任务识别**与**智能代理协调**，提供从**需求分析**到**部署交付**的全流程开发辅助能力。

### 核心价值

| 维度 | 能力 |
|------|------|
| **测试驱动** | Red-Green-Refactor 循环，覆盖率 ≥ 80% |
| **系统调试** | 根因分析，非症状治疗 |
| **代码质量** | 安全性（P0）、性能（P1）、可维护性（P2） |
| **Git 规范** | Conventional Commits、PR 模板 |
| **多代理协调** | 并行执行独立任务，提升效率 |
| **上下文优化** | 压缩、掩码、缓存策略 |
| **批判性思维** | A/B 轮迭代，发现系统性问题 |

### 工作原理

1. **关键词提取**：从任务描述中提取关键词
2. **代理匹配**：基于关键词和代理能力进行匹配
3. **置信度评分**：计算每个代理的匹配度（0-1）
4. **策略选择**：单代理 / 顺序 / 并行模式

---

## 提示词示例

### 示例 1：TDD 开发（最简单）

```
使用 TDD 方式实现用户登录功能
```

### 示例 2：指定测试框架

```
使用 pytest 和 TDD 方式测试用户注册功能
```

### 示例 3：调试根因分析

```
帮我调试这个错误：ConnectionRefusedError，堆栈信息是...
```

### 示例 4：代码审查

```
审查 src/auth.py 的代码质量，重点关注安全性和性能
```

### 示例 5：Git 规范化提交

```
帮我创建一个符合 Conventional Commits 规范的提交
```

### 示例 6：多代理并行处理

```
同时优化前端组件和后端 API 的性能
```

### 示例 7：批判性思维优化

```
使用 A/B 轮测试优化 auto-test-skill
```

### 示例 8：复杂任务协调

```
重构用户模块，包括数据库设计、API 更新和前端组件
```

---

## 配置选项

编辑 `config.yaml` 自定义技能行为：

```yaml
# A/B 轮测试优化配置
ab_test_optimization:
  default_a_rounds: 1          # A 轮默认轮次
  max_a_rounds: 10             # 最大 A 轮轮次
  min_suggestions_per_round: 10  # 每轮最小问题数
  target_suggestions_range: [15, 20]  # 目标问题数
  min_p0_p1_ratio: 60          # P0+P1 最小占比
  min_systemic_issues: 3       # 系统性问题最小数量
  b_round_mandatory: true      # B 轮是否强制

# TDD 配置
tdd:
  min_coverage: 80            # 最低测试覆盖率
  framework: auto             # 测试框架（auto | pytest | jest | unittest）
  watch_mode: true            # 监视模式

# 代码审查配置
code_review:
  complexity_threshold: 10    # 圈复杂度阈值
  max_function_length: 50     # 函数最大行数

# Git 配置
git:
  commit_style: conventional  # 提交风格（conventional | simple）
  branch_naming:
    feature: "feature/*"
    bugfix: "bugfix/*"
```

---

## 备选用法（脚本调用）

> 提示：如安装在 Codex，请将路径中的 `~/.claude/skills` 替换为 `~/.codex/skills`，或先运行 `scripts/get_path.py` 获取绝对路径。

### TDD 测试运行器

```bash
# 运行所有测试
python3 ~/.claude/skills/awesome-code/scripts/test_runner.py

# 生成覆盖率报告
python3 ~/.claude/skills/awesome-code/scripts/test_runner.py --coverage

# 监视模式（文件变更时自动运行）
python3 ~/.claude/skills/awesome-code/scripts/test_runner.py --watch
```

### 代码分析器

```bash
# 分析当前目录
python3 ~/.claude/skills/awesome-code/scripts/code_analyzer.py

# 分析指定目录
python3 ~/.claude/skills/awesome-code/scripts/code_analyzer.py --path src/

# 生成报告
python3 ~/.claude/skills/awesome-code/scripts/code_analyzer.py --report analysis_report.md
```

### Git 辅助工具

```bash
# Conventional Commits 提交
bash ~/.claude/skills/awesome-code/scripts/git_helper.sh commit

# 创建 Pull Request
bash ~/.claude/skills/awesome-code/scripts/git_helper.sh pr

# 输出 PR 模板
bash ~/.claude/skills/awesome-code/scripts/git_helper.sh template > pr.md
```

### A/B 轮测试会话管理

```bash
# 初始化 A 轮测试会话
python3 ~/.claude/skills/awesome-code/scripts/create_test_session.py --skill-root . --kind a --id v202601161200 --create-plan

# 初始化 B 轮测试会话
python3 ~/.claude/skills/awesome-code/scripts/create_test_session.py --skill-root . --kind b --id v202601161300 --create-plan
```

---

## 常见问题

### Q：如何判断使用哪个代理？

A：你不需要手动选择，系统会根据任务关键词自动匹配。例如：
- 提到"测试"、"TDD" → `tdd-workflow`
- 提到"bug"、"调试"、"错误" → `systematic-debugging`
- 提到"审查"、"重构"、"质量" → `code-reviewer`

### Q：可以同时使用多个代理吗？

A：可以。当任务需要多个领域的专业知识时，系统会自动协调多个代理并行或顺序执行。

### Q：A/B 轮测试是什么？

A：这是一个批判性思维驱动的测试优化流程：
- **A 轮**：批判性分析与改进，发现系统性问题（可重复 N 次）
- **B 轮**：七大质量原则全面检查（硬编码/AI 规划、冗余残留、安全性、过度设计、通用性、一致性、配置集中化、SKILL.md 瘦身）

### Q：如何自定义质量标准？

A：编辑 `config.yaml`，修改 `tdd.min_coverage`、`code_review.complexity_threshold` 等参数。

### Q：脚本调用和 Prompt 调用有什么区别？

A：
- **Prompt 调用**（推荐）：AI 自动分析任务并选择合适的代理和工作流
- **脚本调用**（备用）：直接执行特定功能，适合已知具体需求的场景

---

## 更多文档

详细策略和标准请参考 `references/` 目录：

**核心工作流**：
- [TDD 最佳实践](references/tdd-best-practices.md)
- [系统化调试指南](references/debugging-systematic.md)
- [代码审查清单](references/code-review-checklist.md)
- [Git 工作流规范](references/git-workflow.md)

**批判性思维与测试优化**：
- [批判性思维指南](references/CRITICAL_THINKING_GUIDE.md)
- [A 轮计划模板](references/A_ROUND_PLAN_TEMPLATE.md)
- [建设性建议标准](references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md)

---

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic, OpenAI（2/6 = 33%）
- **来源构成**：社区 65%, 学术 20%, 官方 10%, 技术博客 5%
- **数据时效**：2024-06 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试多代理协调准确率

---

### 场景化建议

#### 场景 1：标准多代理协调（最常见）

**触发条件**：需要协调多个专业代理处理复杂开发任务（TDD + 代码审查 + Git 工作流等）

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium-high |
| **预期成本** | ~$0.20-1.00/任务 |

**理由**：
- Sonnet 在多步骤任务协调中表现出色，能够理解任务依赖关系
- 速度快，成本更低（显著快于 Opus）
- [社区测试](https://alirezarezvani.medium.com/claude-opus-4-5-vs-sonnet-i-tested-both-for-90-days-in-claude-code-bb4976923e3a) 显示 Sonnet 在多数代码任务中与 Opus 质量相当
- **多代理协调需要平衡推理能力与效率，Sonnet 的性价比最高**

**避免**：无需升级到 Opus，除非遇到极端复杂的架构问题

**来源**：90 天对比测试 + 官方内部数据

---

#### 场景 2：复杂架构分析与根因调试

**触发条件**：
- 需要深度推理的系统级调试（如分布式系统问题、内存泄漏）
- 复杂架构重构（如微服务拆分、模块依赖重组）
- 需要多步骤抽象推理的根因分析

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Opus 4.5 |
| **推理强度** | high |
| **预期成本** | ~$0.50-2.50/任务 |

**理由**：
- Opus 在复杂推理任务中表现更优，[社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/) 称其为"复杂推理的巨大飞跃"
- [用户报告](https://www.reddit.com/r/ClaudeAI/comments/1lqnqn6/anyone_else_in_the_mindset_of_its_opus_or_nothing/) 显示 Opus 在"规划、分析和创建上下文定义"方面更强
- **复杂根因分析需要深度推理能力，Opus 更适合**

**避免**：简单多代理协调不需要 Opus，用 Sonnet 即可

**来源**：Reddit 社区讨论 + 90 天对比测试

---

#### 场景 3：简单任务执行

**触发条件**：
- 单一代理任务（如只运行 TDD 或只做代码审查）
- 成本敏感，需要高性价比
- 不需要复杂协调，主要执行确定性的脚本

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 或 Sonnet 4.5 |
| **推理强度** | low-medium |
| **预期成本** | ~$0.02-0.30/任务 |

**理由**：
- Haiku 成本最低，适合简单任务执行
- 但对于多代理协调，Haiku 可能无法理解复杂的依赖关系
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1o856eb/tested_haiku_45_it_is_fast-but-cant-complete/) 显示 Haiku 在复杂任务中可能力不从心
- **推荐**：简单单代理任务用 Haiku，多代理协调用 Sonnet

**避免**：需要多代理协调时，不要只用 Haiku

**来源**：社区反馈 + 官方文档

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Sonnet 4.5** | 标准多代理协调（90% 场景） | 极端复杂的架构推理 | $$$$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Opus 4.5** | 复杂架构/根因调试分析 | 简单任务执行（浪费） | $$$$$$ | ⭐⭐ | ⭐⭐⭐ |
| **Haiku 4.5** | 简单单代理任务 | 多代理协调（复杂推理） | $$ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**说明**：
- **Sonnet 覆盖 90% 的多代理协调场景**：大多数情况下 Sonnet 性价比最高
- **Opus 用于极端复杂场景**：分布式系统调试、复杂架构重构、深层根因分析
- **Haiku 用于简单任务**：但不推荐用于需要复杂协调的多代理任务

---

### 通用原则

1. **默认从 Sonnet 开始**：90% 的多代理协调任务 Sonnet 足够，无需 Opus
2. **协调能力需要推理**：awesome-code 的核心是任务拆解和代理协调，需要比简单脚本调用更强的推理能力
3. **成本敏感但质量优先**：多代理协调是复杂任务，不能只追求低成本而牺牲协调质量
4. **并行执行优化成本**：如果任务可以并行执行，可考虑用 Haiku 处理简单子任务，Sonnet/Opus 处理复杂子任务
5. **Haiku 的局限性**：虽然 Haiku 速度快、成本低，但 [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1o856eb/tested_haiku_45_it-is-fast-but-cant-complete/) 显示它在完成基本任务时可能遇到困难

---

### ⚠️ 争议点

#### Sonnet vs Opus：多代理协调应该用哪个？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Sonnet 够用** | 社区多数意见 | Sonnet 在多代理协调中表现接近 Opus，但速度快、成本低 |
| **Opus 必要** | 部分开发者 | Opus 在复杂推理和深层问题分析上仍有优势 |

**数据支持**：
- [90 天对比测试](https://alirezarezvani.medium.com/claude-opus-4-5-vs-sonnet-i-tested-both-for-90-days-in-claude-code-bb4976923e3a)：Opus 在中等投入下成本与 Sonnet 相当
- [官方内部测试](https://spartner.software/blog/claude-sonnet-vs-opus-which-one-do-you-choose)：Sonnet 解决 64% 编程问题 vs Opus 38%（实际场景）
- [SWE-bench 得分](https://labs.adaline.ai/p/claude-4)：Sonnet 72.7%，接近 Opus 水平

**建议**：
- **默认使用 Sonnet**：性价比最高，覆盖 90% 多代理协调场景
- **仅在以下情况升级 Opus**：
  - 需要分析复杂架构（如分布式系统、微服务架构）
  - 需要深度根因分析（如内存泄漏、竞态条件）
  - Sonnet 无法解决的深层系统性问题
  - 关键项目上线前的最终审查

---

### 更新记录

- 2026-01-25：首次调研，覆盖 Anthropic/OpenAI
- 建议：2026-07 重新调研（6 个月后）

---

### 来源链接

**官方文档**：
- [Choosing the right model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)
- [Claude Opus 4.5 vs Sonnet 4.5: Full Report](https://www.datastudios.org/post/claude-opus-4-5-vs-claude-sonnet-4-5-full-report-and-comparison-of-features-performance-pricing-a)

**社区讨论**：
- [Claude Opus 4.5 is insane (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/)
- [Opus or nothing for 90% of tasks (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1lqnqn6/anyone_else_in_the_mindset_of_its_opus_or_nothing/)
- [Tested GPT-5.1, Gemini 3, and Claude Opus 4.5 (Reddit)](https://www.reddit.com/r/ClaudeAI/comments/1pd83la/tested_gpt51_gemini_3_and_claude_opus_45_on/)

**对比测试**：
- [90-Day Claude Code Decision Framework](https://alirezarezvani.medium.com/claude-opus-4-5-vs-sonnet-i-tested-both-for-90-days-in-claude-code-bb4976923e3a)
- [Claude Sonnet 4 Vs Opus 4.1: Which Model To Use For Coding](https://labs.adaline.ai/p/claude-4)
- [Claude 3.5 Sonnet vs. Opus: the fastest sprinter or the deepest thinker?](https://spartner.software/blog/claude-sonnet-vs-opus-which-one-do-you-choose)

**学术研究**：
- [Enhancing Software Code Vulnerability Detection Using GPT-4o and Claude-3.5 Sonnet](https://www.mdpi.com/2079-9292/13/13/2657)
- [Assessing the Quality and Security of AI-Generated Code](https://arxiv.org/html/2508.14727v1)

---

**v2.0.1** — 智能多代理软件开发协调系统
