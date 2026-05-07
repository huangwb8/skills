# auto-test-code

本 README 面向**使用者**：如何触发并正确使用 `auto-test-code` skill。
执行指令与硬性规范在 `SKILL.md`；默认参数在 `config.yaml`。

---

## 用法

### 最推荐用法

```
用 auto-test-code 测试 /path/to/project，进行 2 轮 A 轮审查 + B 轮质量检查
```

### 其他常见场景

#### 单轮快速审查

```
用 auto-test-code 测试 /path/to/project，只做 1 轮 A 轮审查
```

#### 指定代码语言

```
用 auto-test-code 测试 /path/to/project，重点审查 Python 和 JavaScript 代码
```

#### 指定深挖维度（全覆盖 + 重点深挖）

```
用 auto-test-code 测试 /path/to/project，本轮深挖并发安全和资源管理问题
```

---

## 设计理念

`auto-test-code` 是一个**批判性思维驱动的代码自审查技能**，核心价值在于：

- **独立评估模式**：每轮审查都基于当前代码状态独立分析，避免确认偏差
- **批判性思维驱动**：强制使用"刁钻角度"思考，发现深层系统性问题
- **可追溯文档**：所有问题、修复、验证都固化为文档，可复现可复盘

**与普通代码审查的区别**：

| 维度 | 普通代码审查 | auto-test-code |
|------|-------------|----------------|
| 目标 | 发现表面问题（风格、规范） | 发现系统性问题（算法/边界/并发/安全/设计） |
| 方法 | 人工检查 + 主观判断 | 批判性思维框架 + 静态分析 + 动态推理 |
| 输出 | 口头建议 | 可追溯的文档 + 修复计划 + 验证报告 |
| 质量 | 无明确标准 | 强制数量要求（≥10 个问题）和质量门槛（P0+P1 ≥ 60%） |

---

## 功能概述

| 特性 | 说明 |
|------|------|
| **多轮 A 轮迭代** | 静态分析 → 动态推理 → 计划 → 优化 → 轻量测试（可重复 N 次） |
| **独立评估模式** | 每轮基于当前代码状态独立审查，不查看历史记录 |
| **批判性思维驱动** | 强制使用刁钻角度（空输入/超大输入/竞态条件/资源耗尽） |
| **强制质量要求** | 每轮至少 10 个问题，P0+P1 占比 ≥ 60%，系统性问题 ≥ 3 个 |
| **B 轮质量检查** | 9 大维度代码质量原则检查（算法复杂度、边界覆盖、安全漏洞分类审查、设计质量等） |
| **可追溯文档** | 统一沉淀到 `tmp/run_*/tests/` 隔离工作区（REVIEW/PLAN/RUN/REPORT + artifacts），可复现可复盘 |

---

## 提示词示例

### 示例 1：完整审查流程（推荐）

```
你：用 auto-test-code 测试 /path/to/project，进行 3 轮 A 轮审查 + B 轮质量检查

技能：开始执行完整审查流程...
      [A 轮 #1] 发现 15 个问题（P0: 3, P1: 8, P2: 4）
      [A 轮 #2] 发现 12 个问题（P0: 2, P1: 7, P2: 3）
      [A 轮 #3] 发现 10 个问题（P0: 1, P1: 6, P2: 3）
      [B 轮] 完成 9 维度质量检查
      产出：tmp/run_*/tests/v*/（含 REVIEW/PLAN/RUN/REPORT）+ tmp/run_*/tests/b-v*/
```

### 示例 2：单轮快速检查

```
你：用 auto-test-code 测试当前目录的代码，只做 1 轮审查

技能：执行单轮 A 轮审查...
      发现 18 个问题（P0: 4, P1: 10, P2: 4）
      产出：tmp/run_YYYYMMDDHHMMSS/tests/vYYYYMMDDHHMM/
```

### 示例 3：指定深挖维度（全覆盖 + 重点深挖）

```
你：用 auto-test-code 测试 /path/to/project，深挖并发安全和资源管理问题

技能：本轮深挖维度：并发安全性、资源管理（其余维度仍全覆盖）
      刁钻角度（用于深挖）：竞态条件、死锁、文件描述符泄漏、内存泄漏
      发现 15 个相关问题（P0: 5, P1: 7, P2: 3）
```

### 示例 4：结合特定代码语言

```
你：用 auto-test-code 测试 /path/to/project，重点审查 Python 代码

技能：扫描 *.py 文件...
      发现 16 个问题（P0: 3, P1: 9, P2: 4）
      聚焦：Python 特有问题（GIL、动态类型、资源管理）
```

---

## 隔离工作区

- 每次 skill 执行都会在目标项目根目录创建 `tmp/run_YYYYMMDDHHMMSS/` 作为当次隔离工作区。
- 所有计划、报告、日志、辅助脚本和中间产物都只写入该工作区，避免把 skill 文件泄露到源项目其他位置。
- 运行可能产生缓存或临时文件的命令时，优先将工作目录、`TMPDIR`、`XDG_CACHE_HOME`、`PYTHONPYCACHEPREFIX` 等重定向到当前工作区。
- 除了用户明确要求的源码修复外，`tmp/run_*/` 之外不应新增任何 auto-test-code 相关文件。

---

## 输出文件

技能执行后会在目标代码目录下的隔离工作区生成以下文件：

```
{项目根目录}/
└── tmp/
    └── run_20260310153045/           # 本次技能执行的隔离工作区（示例）
        ├── .auto-test-code-run.json  # 运行清单（记录 code_root / run_id / tests_dir）
        └── tests/                    # 会话目录（计划/过程/结果都在同一处）
            ├── v202602161028/        # A 轮会话（示例）
            │   ├── REVIEW.md         # 批判性审查（问题清单 + 改进计划）
            │   ├── TEST_PLAN.md      # 测试计划
            │   ├── TEST_RUN.md       # 测试过程（命令、关键输出摘录、决策）
            │   ├── TEST_REPORT.md    # 测试结果与证据
            │   ├── _artifacts/       # 中间产物
            │   └── _scripts/         # 会话内辅助脚本（可选）
            └── b-v202602161028/      # B 轮会话（质量检查 + 验证）
                └── ...
```

### 文件说明

| 文件 | 说明 |
|------|------|
| `tmp/run_*/tests/v*/REVIEW.md` | A 轮批判性审查（问题清单 + 改进计划） |
| `tmp/run_*/tests/b-v*/REVIEW.md` | B 轮代码质量检查报告（9 大维度评估） |
| `tmp/run_*/tests/*/TEST_PLAN.md` | 测试计划，列出本轮验证的修复点 |
| `tmp/run_*/tests/*/TEST_RUN.md` | 测试过程记录（命令、关键输出摘录、关键决策） |
| `tmp/run_*/tests/*/TEST_REPORT.md` | 测试报告，包含验证结果和证据 |
| `tmp/run_*/tests/*/_artifacts/` | 中间产物（命令输出、日志、截图等） |

---

## 配置选项

在 `config.yaml` 中可调整以下参数：

### 轮次控制

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `test_rounds.default_a_rounds` | 1 | 默认 A 轮次数 |
| `test_rounds.max_a_rounds` | 10 | 最大 A 轮次数 |
| `test_rounds.min_suggestions_per_round` | 10 | 每轮最少问题数 |
| `test_rounds.target_suggestions_range` | [15, 20] | 目标问题数范围 |
| `test_rounds.min_p0_p1_ratio` | 60 | P0+P1 最小占比（%） |

### A 轮审查范围

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `a_round_check.independent_review.enabled` | true | 独立评估模式开关 |
| `a_round_check.independent_review.scan_patterns` | ["**/*.py", "**/*.js", ...] | 扫描文件模式 |
| `a_round_check.independent_review.exclude_patterns` | ["tmp/**", "node_modules/**", ...] | 排除目录 |

### B 轮检查维度

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `b_round_check.mandatory` | true | B 轮是否强制执行 |
| `b_round_check.min_suggestions` | 10 | B 轮最少建议数 |
| `b_round_check.dimensions` | [9 大维度] | 检查维度列表 |

**修改方式**：编辑你的安装目录下的配置（Codex: `~/.codex/skills/auto-test-code/config.yaml`；Claude Code: `~/.claude/skills/auto-test-code/config.yaml`）。如需对单个项目做覆盖，可在目标项目根目录创建 `.auto-test-code/config.yaml`（仅覆盖 `directories.tmp`、`directories.tests` 与 `templates.*`，脚本会做路径安全校验）。

---

## 配套脚本（可选）

技能提供辅助脚本用于创建和验证测试会话：

### 创建测试会话

```bash
# 在目标代码根目录内执行
RUN_ID=run_20260310153045
python3 ~/.codex/skills/auto-test-code/scripts/create_session.py --code-root . --run-id "$RUN_ID" --kind a --id v202602161028
# 或
RUN_ID=run_20260310153045
python3 ~/.claude/skills/auto-test-code/scripts/create_session.py --code-root . --run-id "$RUN_ID" --kind a --id v202602161028
```

**作用**：自动创建 `tmp/run_*/tests/` 会话目录骨架（REVIEW/PLAN/RUN/REPORT + _artifacts/_scripts），并写入运行清单 `.auto-test-code-run.json`

### 验证测试会话

```bash
python3 ~/.codex/skills/auto-test-code/scripts/verify_session.py --require-review tmp/run_20260310153045/tests/v202602161028
# 或
python3 ~/.claude/skills/auto-test-code/scripts/verify_session.py --require-review tmp/run_20260310153045/tests/v202602161028
```

**作用**：检查会话完整性（REVIEW/PLAN/RUN/REPORT + 引用一致性）；如需强制检查模板占位符是否全部替换，可加 `--strict`

---

## 常见问题

### Q：技能没有被触发怎么办？

A：尝试用更明确的描述：
- ✅ "用 auto-test-code 测试 XXX"
- ✅ "运行 auto-test-code 对 XXX 进行代码审查"
- ❌ "帮我测试一下代码"（太模糊）

### Q：A 轮和 B 轮有什么区别？

A：
- **A 轮**：批判性代码审查，发现具体问题（P0/P1/P2），要求每轮 ≥ 10 个问题
- **B 轮**：代码质量原则检查，从 9 大维度评估代码质量（算法复杂度、边界覆盖、安全漏洞分类审查、设计质量等）

### Q：问题优先级 P0/P1/P2 是什么意思？

A：

| 优先级 | 含义 | 典型场景 |
|--------|------|----------|
| **P0** | 必须修复 | 崩溃风险、安全漏洞、数据损坏、资源泄漏 |
| **P1** | 强烈建议 | 性能问题、边界条件缺陷、逻辑错误 |
| **P2** | 建议优化 | 代码风格、可读性、冗余代码 |

### Q：如何选择 A 轮次数？

A：

| 场景 | 推荐轮次 | 理由 |
|------|---------|------|
| 初次审查/代码质量较差 | 3-5 轮 | 多轮逐步发现深层问题 |
| 日常审查/代码质量较好 | 1-2 轮 | 快速检查主要问题 |
| 关键项目/上线前 | 5-10 轮 | 确保代码质量达到高标准 |

### Q：什么是"独立评估模式"？

A：每轮 A 轮都基于代码的**当前状态**独立分析，不查看历史 `tmp/run_*/` 工作区中的审查文件。好处是让"多轮"带来"多角度"，而非"重复确认"。

### Q：如何理解"批判性思维"？

A：使用"刁钻角度"思考代码可能的问题：
- 空输入、超大输入、恶意输入会怎样？
- 并发访问时会有竞态条件吗？
- 资源耗尽时会发生什么？
- 异常抛出时资源会正确释放吗？

详见 `references/CRITICAL_THINKING_FOR_CODE.md`

---

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-01-25

### 披露信息

- **覆盖厂商**：Anthropic, OpenAI（2/6 = 33%）
- **来源构成**：社区 65%, 学术 20%, 官方 10%, 技术博客 5%
- **数据时效**：2024-06 至 2026-01
- **局限性**：未覆盖国产模型，未独立测试代码审查准确率

---

### 场景化建议

#### 场景 1：标准代码审查（最常见）

**触发条件**：日常代码审查，需要发现系统性问题（算法/边界/并发/安全）

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Sonnet 4.5 |
| **推理强度** | medium-high |
| **预期成本** | ~$0.10-0.50/轮 |

**理由**：
- Sonnet 在代码审查任务中表现出色，SWE-bench 得分 72.7%（接近 Opus）
- 速度更快，成本更低（4-5 倍于 Haiku，显著快于 Opus）
- [社区测试](https://alirezarezvani.medium.com/claude-opus-4-5-vs-sonnet-i-tested-both-for-90-days-in-claude-code-bb4976923e3a) 显示 Sonnet 在多数代码任务中与 Opus 质量相当
- [内部测试](https://spartner.software/blog/claude-sonnet-vs-opus-which-one-do-you-choose) 显示 Sonnet 解决 64% 编程问题 vs Opus 38%

**避免**：无需升级到 Opus，除非遇到极端复杂的算法分析

**来源**：90 天对比测试 + 官方内部数据

---

#### 场景 2：复杂算法与安全审查

**触发条件**：
- 需要深度推理的复杂算法（如分布式系统、加密算法）
- 安全漏洞深度分析（如竞态条件、内存安全）
- 需要多步骤抽象推理的场景

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Opus 4.5 |
| **推理强度** | high |
| **预期成本** | ~$0.30-1.50/轮 |

**理由**：
- Opus 在复杂推理任务中表现更优，[社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1por062/claude_opus_45_is_insane_and_it_ruined_other/) 称其为"复杂推理的巨大飞跃"
- [用户报告](https://www.reddit.com/r/ClaudeAI/comments/1lqnqn6/anyone_else_in_the_mindset_of_its_opus_or_nothing/) 显示 Opus 在"规划、分析和创建上下文定义"方面更强
- [90 天测试](https://alirezarezvani.medium.com/claude-opus-4-5-vs-sonnet-i-tested-both-for-90-days-in-claude-code-bb4976923e3a) 显示 Opus 在中等投入下成本与 Sonnet 相当

**避免**：简单代码审查不需要 Opus，用 Sonnet 即可

**来源**：Reddit 社区讨论 + 90 天对比测试

---

#### 场景 3：快速批量检查

**触发条件**：
- 需要快速审查多个文件/模块
- 成本敏感，需要高性价比
- 不需要深度推理，主要发现明显问题

| 项目 | 建议 |
|------|------|
| **推荐模型** | Claude Haiku 4.5 或 Sonnet 4.5 |
| **推理强度** | low-medium |
| **预期成本** | ~$0.02-0.20/轮 |

**理由**：
- Haiku 成本最低，适合快速批量检查
- 但对于批判性思维驱动的代码审查，Haiku 可能无法发现深层系统性问题
- [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1o856eb/tested_haiku_45_it_is_fast_but_cant_complete/) 显示 Haiku 在复杂任务中可能力不从心
- **推荐**：快速检查用 Haiku，但质量要求高时用 Sonnet

**避免**：需要发现系统性问题（算法/边界/并发）时，不要只用 Haiku

**来源**：社区反馈 + 官方文档

---

### 对比总结

| 模型 | 最适合 | 最不适合 | 相对成本 | 相对速度 | 推荐度 |
|------|-------|---------|---------|---------|-------|
| **Sonnet 4.5** | 标准代码审查（95% 场景） | 极端复杂的算法推理 | $$$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Opus 4.5** | 复杂算法/安全深度分析 | 简单代码审查（浪费） | $$$$$ | ⭐⭐ | ⭐⭐⭐ |
| **Haiku 4.5** | 快速批量检查 | 批判性思维审查（深层问题） | $ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**说明**：
- **Sonnet 覆盖 95% 的代码审查场景**：大多数情况下 Sonnet 性价比最高
- **Opus 用于极端复杂场景**：分布式系统、加密算法、深层安全分析
- **Haiku 用于快速检查**：但不推荐用于需要批判性思维的系统性问题发现

---

### 通用原则

1. **默认从 Sonnet 开始**：95% 的代码审查任务 Sonnet 足够，无需 Opus
2. **批判性思维需要强推理**：auto-test-code 的核心是发现系统性问题（算法/边界/并发/安全），需要比简单工具调用更强的推理能力
3. **成本敏感但质量优先**：代码审查是质量问题，不能只追求低成本而牺牲审查深度
4. **多轮迭代优化成本**：如果需要进行多轮 A 轮审查，可考虑第 1-2 轮用 Sonnet，发现问题后用 Opus 深度分析关键问题
5. **Haiku 的局限性**：虽然 Haiku 速度快、成本低，但 [社区反馈](https://www.reddit.com/r/ClaudeAI/comments/1o856eb/tested_haiku_45_it_is_fast-but-cant-complete/) 显示它在完成基本任务时可能遇到困难

---

### ⚠️ 争议点

#### Sonnet vs Opus：代码审查应该用哪个？

| 观点 | 支持者 | 理由 |
|------|-------|------|
| **Sonnet 够用** | 社区多数意见 | Sonnet 在代码审查中表现接近 Opus，但速度快、成本低 |
| **Opus 必要** | 部分开发者 | Opus 在复杂推理和深层问题发现上仍有优势 |

**数据支持**：
- [90 天对比测试](https://alirezarezvani.medium.com/claude-opus-4-5-vs-sonnet-i-tested-both-for-90-days-in-claude-code-bb4976923e3a)：Opus 在中等投入下成本与 Sonnet 相当
- [官方内部测试](https://spartner.software/blog/claude-sonnet-vs-opus-which-one-do-you-choose)：Sonnet 解决 64% 编程问题 vs Opus 38%（实际场景）
- [SWE-bench 得分](https://labs.adaline.ai/p/claude-4)：Sonnet 72.7%，接近 Opus 水平

**建议**：
- **默认使用 Sonnet**：性价比最高，覆盖 95% 代码审查场景
- **仅在以下情况升级 Opus**：
  - 需要分析复杂算法（如分布式系统、加密算法）
  - 需要深度安全分析（如竞态条件、内存安全）
  - Sonnet 无法发现的深层系统性问题
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

## 更多文档

- `SKILL.md` — 技能执行指令与硬性规范
- `config.yaml` — 可配置参数
- `references/` — 详细策略与参考文档
  - `CRITICAL_THINKING_FOR_CODE.md` — 批判性思维框架（核心）
  - `A_ROUND_REVIEW_TEMPLATE.md` — A 轮审查报告结构
  - `CODE_SMELLS.md` — 代码异味识别指南
  - `SECURITY_PATTERNS.md` — 安全漏洞模式库
  - `SECURITY_TAXONOMY.md` — 安全漏洞分类审查体系
  - `BOUNDARY_CHECKLIST.md` — 边界条件检查清单
