# auto-test-skill

批判性思维驱动的测试驱动优化技能 - 用于在 AI 辅助开发后进行系统性测试与迭代优化。

## 概述

本技能提供了一套完整的测试驱动优化工作流,帮助用户在AI辅助开发后进行系统性的测试、问题修复和迭代优化。

**核心价值**:
- ✅ **结构化问题管理**: 从bug发现到优先级排序的全流程管理
- ✅ **可重复测试**: 规范化的测试目录和文档结构
- ✅ **独立评估 + 迭代修复**: 每轮 A 轮独立审查当前状态，按计划修复并用轻量测试验证
- ✅ **完整追溯**: 每轮迭代都有明确的测试计划和报告

**设计理念**:
本技能借鉴了成熟的软件测试实践（如时间戳命名测试会话、规范化文档结构、测试数据/脚本/输出分离等），确保每个测试会话都是独立、透明、可重复的；其中 **A 轮默认采用“独立评估”模式**（不查看 `plans/` 与 `tests/`），以降低确认偏差并提升多轮价值。

## 适用场景

- ✅ 用户完成AI辅助开发后,需要进行系统性测试
- ✅ 发现bug需要记录和优先级排序
- ✅ 需要制定结构化的优化和测试计划
- ✅ 需要管理多轮迭代测试和修复流程
- ✅ 需要生成规范的测试报告和总结文档

## 使用方法

### 推荐用法（自动完整测试流程）

**开发者推荐 Prompt**：

```
使用 auto-test-skill 对 xxx 这个skill进行1个A轮迭代优化。
```

补充要求（推荐）：每轮 A 轮为**独立评估**（不查看上一轮 `plans/`/`tests/`），并明确本轮审查范围与排除范围。

### 人机协作用法（手动审核 AI 建议）

本技能支持灵活的"人机协作"模式，你可以手动查看和审核 AI 的建议，而不必自动执行完整的修复流程。

**典型场景**：

```
根据 auto-test-skill 的B轮原则，目前 target-skill 还有哪些优化的地方？
```

**优势**：
- 你可以先查看 AI 发现的问题，再决定是否修复
- 可以选择性采纳建议，而不是全盘接受
- 适合用于代码审查、质量评估等场景

**更多人机协作示例**：

```
根据 auto-test-skill 的批判性思维框架，分析一下 my-skill 在架构设计上可能有哪些问题？
```

```
用 auto-test-skill 的A轮独立评估模式，检查这个 skill 是否存在过度设计的问题。
```

### 触发方式

在支持 Agent Skills 的工具（如 Codex CLI、Claude Code、Cursor 等）中使用以下表述之一触发本技能:

**自动测试模式**：
- "帮我测试一下这个技能"
- "我需要制定测试计划"
- "需要进行迭代优化"
- "生成测试报告"

**人机协作模式**：
- "根据 auto-test-skill 的 B 轮原则分析这个 skill"
- "用 auto-test-skill 的批判性思维检查这个项目"
- "根据 auto-test-skill 的质量原则给出优化建议"

### 输入要求

使用本技能前,请准备:

1. **目标技能的根目录路径**
   - 示例: `/path/to/skills/your-skill`

2. **测试发现的问题列表**
   - 可来自:用户反馈、测试结果、代码审查等
   - 至少包含:问题描述、复现步骤、期望行为

3. **可选**: 已有测试数据或测试用例
   - 如果有,请提供数据路径

### 工作流程

本技能遵循 **A轮×N + B轮** 的多轮迭代工作流：

```
用户输入
  ↓
[A轮 × N]：分析 → 计划 → 优化 → 轻量测试
  ↓
B轮：质量原则检查 → 针对性优化 → 轻量验证
  ↓
完成（文档齐全 + 问题闭环）
```

详细说明请参阅 [SKILL.md](SKILL.md)。

## 输出交付

使用本技能后,您将获得:

1. **规划文档（A轮）**：`plans/vYYYYMMDDHHMM.md`
2. **测试会话目录（A轮）**：`tests/vYYYYMMDDHHMM/`（包含 `TEST_PLAN.md`、`TEST_REPORT.md`）
3. **质量检查报告（B轮）**：`plans/B轮-vYYYYMMDDHHMM.md`
4. **验证会话目录（B轮）**：`tests/B轮-vYYYYMMDDHHMM/`（包含 `TEST_PLAN.md`、`TEST_REPORT.md`）

## 确定性辅助脚本（推荐）

为避免每轮手工创建目录与文档骨架，推荐使用：

```bash
python3 auto-test-skill/scripts/create_test_session.py --skill-root /path/to/target-skill --kind a --id vYYYYMMDDHHMM --create-plan

# 或：省略 --id 自动生成 vYYYYMMDDHHMM
python3 auto-test-skill/scripts/create_test_session.py --skill-root /path/to/target-skill --kind a --create-plan
```

验证会话完整性（推荐，避免“空报告/占位符残留”）：

```bash
# 在目标 skill 根目录内执行
python3 /path/to/auto-test-skill/scripts/verify_test_session.py --require-plan tests/vYYYYMMDDHHMM
```

说明：
- `--skill-root` 指向“要被测试/被优化”的目标 skill 根目录（必须包含 `SKILL.md`）
- `--create-plan` 会在缺失时生成 `plans/` 下对应的计划文档骨架（默认不覆盖）
- 脚本会优先使用目标 skill 的 `templates/`（如存在）；否则使用 auto-test-skill 自带 `templates/` 作为回退模板
- B 轮可选：使用 `--a-test-id vYYYYMMDDHHMM` 记录“对应的 A 轮会话 id”（用于 B 轮报告可追溯）
- `--seed-test-plan-from-plan`（高级，不推荐）：会将 `plans/` 下的计划文档直接复制为 `TEST_PLAN.md`，通常你应当基于 `templates/TEST_PLAN_TEMPLATE.md` 补全验证点即可

## 文件结构

```
auto-test-skill/
├── SKILL.md                           # 技能主文档
├── README.md                          # 本文件
├── config.yaml                        # 配置文件
├── plans/                             # 规划文档目录
├── tests/                             # 测试会话目录
├── scripts/                           # 确定性辅助脚本（可选）
├── templates/                         # 文档模板
│   ├── BUG_REPORT_TEMPLATE.md         # Bug报告模板
│   ├── OPTIMIZATION_PLAN_TEMPLATE.md  # 优化计划模板
│   ├── TEST_PLAN_TEMPLATE.md          # 测试计划模板
│   ├── TEST_REPORT_TEMPLATE.md        # 测试报告模板
│   ├── FINAL_SUMMARY_TEMPLATE.md      # 最终总结模板
│   └── B_ROUND_CHECK_TEMPLATE.md      # B轮质量检查模板
└── references/                        # 参考文档
    └── TESTING_BEST_PRACTICES.md      # 测试最佳实践
```

## 配置说明

本技能使用 `config.yaml` 作为**口径统一**与**部分脚本参数**的单一来源。

主要配置项:

- **脚本会读取**：
  - **directories.\***：`plans/` 与 `tests/` 的相对目录（`scripts/create_test_session.py` 会做路径安全校验）
  - **templates.\***：计划/报告等模板路径（相对 skill 根目录）
- **规划口径（AI/人类参考）**：
  - **test_rounds**：每轮数量阈值（10-20、P0+P1≥60%、系统性问题≥3 等）
  - **a_round_check.independent_review**：A 轮独立评估的审查范围与排除范围（不看 `plans/` 与 `tests/`）
  - **b_round_check**：B 轮质量检查是否强制、数量阈值、修复率要求、检查维度（`b_round_check.dimensions`）

版本更新顺序（推荐）：先更新 `config.yaml:skill_info.version`，再同步 `SKILL.md` YAML 表头与 `CHANGELOG.md`。

详细配置请参阅 [config.yaml](config.yaml)。

## 示例使用场景

### 场景 1: 修复技能的 Bug

**输入**:
- 用户报告某个技能的3个bug
- 技能根目录: `/path/to/skills/your-skill`

**执行流程**:
1. A轮：生成 `plans/vYYYYMMDDHHMM.md`（问题清单 + 改进计划）
2. A轮：创建 `tests/vYYYYMMDDHHMM/` 并按计划修复与验证
3. B轮：生成 `plans/B轮-vYYYYMMDDHHMM.md`（质量原则检查；维度以 `config.yaml:b_round_check.dimensions` 为准）
4. B轮：创建 `tests/B轮-vYYYYMMDDHHMM/` 并做针对性验证
5. 验收：更新 `CHANGELOG.md`

**输出**:
- 修复后的代码
- 完整的测试文档
- CHANGELOG.md 更新

### 场景 2: 多轮迭代优化

**背景**: 第一次测试发现10个问题,计划分3轮迭代

**迭代轮次**:
- **第1轮** (`v202601021313`): 修复 P0(2个) + P1(3个) → 测试通过
- **第2轮** (`v202601031015`): 修复 P1(2个) + P2(3个) → 测试通过
- **第3轮** (`v202601041420`): 修复剩余 P2 + 新发现的问题 → 测试通过

**最终输出**:
- FINAL_SUMMARY.md(总结3轮优化历程)
- 所有问题已修复
- 测试覆盖率提升

## 最佳实践

### 1. 问题分类原则

**严重程度判断标准**:

| 严重程度 | 判断问题 |
|----------|----------|
| **Critical** | 数据丢失、安全漏洞、完全无法使用 |
| **High** | 主要功能失效、性能严重退化、用户体验严重受损 |
| **Medium** | 边缘功能失效、性能轻微退化、用户体验一般受损 |
| **Low** | 文档错误、UI瑕疵、体验优化建议 |

### 2. 迭代计划原则

**每次迭代应该**:
- ✅ 专注修复少量高优先级问题(3-5个)
- ✅ 确保每个修复都有对应的测试
- ✅ 验证无回归后再合并

**每次迭代不应该**:
- ❌ 试图修复所有问题
- ❌ 修复没有测试的问题
- ❌ 引入新的破坏性变更

### 3. 测试设计原则

**好的测试用例**:
- ✅ 快速执行(几秒内)
- ✅ 独立运行(不依赖顺序)
- ✅ 结果明确(通过/失败清晰)
- ✅ 可重复执行(结果稳定)

**测试用例模板**:
```python
def test_fix_problem_1():
    """测试问题#1的修复效果"""
    # Arrange
    input_data = {...}

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result == expected_output
```

### 4. 文档管理原则

**测试文档应该**:
- ✅ 简洁明了(重点信息突出)
- ✅ 结构一致(使用统一模板)
- ✅ 及时更新(每个阶段结束后立即更新)
- ✅ 独立完整(不依赖外部文档)

## 常见问题

### Q1: 如果测试会话太多怎么办?

**A**: 测试会话目录本身就很轻量(主要是文档),可以保留所有历史会话。如果需要清理,建议:
- 保留最近10个会话
- 归档早期的会话到 `tests_archive/`（如你在项目里有该约定）
- 保留关键里程碑的会话(如首次完整测试、重大修复等)

### Q2: 如果一个问题需要多轮迭代才能修复怎么办?

**A**:
- 在第一轮迭代中,尝试最小化修复(缓解问题而非完美解决)
- 在后续迭代中,逐步完善修复
- 在 BUG_REPORT.md 中标记问题的演进历史

### Q3: 如果在修复过程中引入新问题怎么办?

**A**:
- 立即记录新问题到 BUG_REPORT.md
- 评估新问题的严重程度
- 如果是 P0/P1,停止当前修复,优先处理新问题
- 如果是 P2/P3,记录到下次迭代计划

### Q4: 如何确保测试的轻量级?

**A**:
- 优先使用单元测试而非集成测试
- 使用 mock/stub 隔离外部依赖
- 测试数据尽量小而精
- 避免耗时操作(如网络请求、文件IO)

## 参考资源

- **技能主文档**: [SKILL.md](SKILL.md)
- **配置文件**: [config.yaml](config.yaml)
- **文档模板**: [templates/](templates/)
- **Agent Skills标准**: [https://agentskills.io](https://agentskills.io)

**相关阅读**:
- 测试驱动开发(TDD)最佳实践
- 敏捷开发中的迭代优化方法
- 软件质量保证(SQA)标准流程

## WHICHMODEL - 模型选择最佳实践

本节由 `which-model` skill 自动调研生成，最后更新：2026-01-03

### 场景一：代码分析与 Bug 检测
- **推荐模型**：Claude Sonnet 4.5
- **推荐参数**：
  - 推理强度：medium
  - Thinking 模式：开
  - Temperature：0.3（平衡准确性与创造性）
  - Max Tokens：8192
- **理由**：Sonnet 4.5 在 SWE-bench Verified 上达到 state-of-the-art 性能，比 GPT-4o 高出约 25% 在代码分析任务上。特别适合静态代码分析和漏洞检测。[来源：Claude Sonnet 4.5 - Anthropic 官方 - Sonnet 在代码测试和分析上的性能提升]

### 场景二：测试用例生成
- **推荐模型**：Claude Sonnet 4.5
- **推荐参数**：
  - 推理强度：medium
  - Thinking 模式：开
  - Temperature：0.5（允许一定的测试场景多样性）
  - Max Tokens：4096
- **理由**：测试用例生成需要理解代码逻辑并设计边界条件，Sonnet 4.5 在代码理解和推理上表现优异，且支持 up to 64K output tokens 适合生成大量测试代码。[来源：Claude Sonnet 4.5 Technical Analysis - Sonnet 的长文本生成能力]

### 场景三：测试计划与优化方案制定
- **推荐模型**：Claude Opus 4.5
- **推荐参数**：
  - 推理强度：high
  - Thinking 模式：开
  - Temperature：0.7（鼓励多角度思考）
  - Max Tokens：16384
- **理由**：制定优化计划需要综合考虑多个因素（优先级、依赖关系、风险评估），Opus 4.5 的最强推理能力能确保计划的完整性和可执行性。[来源：Claude Code Best Practices - 复杂规划任务使用 Opus]

### 场景四：快速代码审查（轻量级）
- **推荐模型**：Claude Haiku 4.5
- **推荐参数**：
  - 推理强度：low
  - Thinking 模式：关
  - Temperature：0.3
  - Max Tokens：2048
- **理由**：对于简单的代码风格检查或基础问题识别，Haiku 4.5 能提供快速反馈，适合早期快速筛查。[来源：Choosing the right model - 从 Haiku 开始的渐进式策略]

### 通用原则
1. **代码分析用 Sonnet**：Sonnet 4.5 是代码分析和漏洞检测的最佳选择（SWE-bench Verified 领先）
2. **复杂规划用 Opus**：多轮迭代优化计划、复杂依赖关系分析需要 Opus 4.5 的最强推理
3. **快速筛查用 Haiku**：简单的风格检查或早期问题识别可用 Haiku 4.5 节省时间
4. **测试生成用 Sonnet**：Sonnet 4.5 支持长文本输出（64K tokens），适合生成大量测试代码
5. **Temperature 调整**：漏洞检测用低 Temperature（0.1-0.3），规划用中高 Temperature（0.5-0.7）

### 更新记录
- 2026-01-03：初始调研，基于 Anthropic 官方文档、SWE-bench Verified 基准测试和软件工程最佳实践

## 版本历史

- **v1.0.0** (2026-01-02): 初始版本
  - 6阶段工作流
  - 结构化问题管理
  - 测试会话管理
  - 文档模板系统

## 许可证

本技能遵循 [Agent Skills 开放标准](https://agentskills.io)。

## 联系方式

- **作者**: bensz
- **创建时间**: 2026-01-02
- **反馈渠道**: 通过 GitHub Issues 或项目讨论区反馈

---

**祝您测试愉快!** 🎉
