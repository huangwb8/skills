# auto-test-project

项目级自动化测试驱动优化技能 - 用于对完整项目进行持续性 AI 优化。

## 概述

本技能提供了一套完整的项目级测试驱动优化工作流，帮助用户对完整项目（如技能项目、工作流项目、或其他具有 `CLAUDE.md` 或类似指令文件的项目）进行系统性的测试、问题修复和迭代优化。

**核心价值**:
- ✅ **项目级问题管理**: 从 bug 发现到优先级排序的全流程管理（跨模块、跨文件）
- ✅ **可重复测试**: 规范化的测试目录和文档结构
- ✅ **渐进式优化**: 通过多轮 A 轮测试 + B 轮质量检查实现持续改进
- ✅ **完整追溯**: 每轮迭代都有明确的测试计划和报告
- ✅ **跨模块验证**: 支持模块间集成测试和依赖关系分析

**与 auto-test-skill 的区别**:
| 维度 | auto-test-skill | auto-test-project |
|------|-----------------|-------------------|
| **目标对象** | 单个 Agent Skill | 完整项目（多模块、多文件） |
| **测试范围** | 单个 skill 目录 | 整个项目目录 |
| **问题分析** | skill 级别 | 项目级别（跨模块） |
| **质量检查** | 维度以 `config.yaml:b_round_check.dimensions` 为准 | 维度以 `config.yaml:b_round_check.dimensions` 为准（项目级扩展） |

## 适用场景

- ✅ 对完整项目进行系统性测试和优化
- ✅ 发现跨模块问题并进行修复
- ✅ 需要制定项目级的优化计划
- ✅ 管理多轮迭代测试和修复流程
- ✅ 生成项目级测试报告和总结文档

## Quick Start

在“目标项目根目录”执行：

```bash
# 1) 创建 A 轮会话骨架（会自动创建 plans/ 与 tests/）
python3 /path/to/auto-test-project/scripts/create_test_session.py --project-root . --kind a --create-plan

# 2) 修复并补齐 tests/<id>/TEST_PLAN.md 与 tests/<id>/TEST_REPORT.md 后，运行验证（推荐严格模式）
python3 /path/to/auto-test-project/scripts/verify_test_session.py --require-plan tests/vYYYYMMDDHHMM
```

安全提示：该脚本会在 `--project-root` 下创建 `plans/` 与 `tests/`。为防止误用，默认拒绝将系统根目录或用户主目录作为 project-root；如你确有需要，可显式加 `--allow-unsafe-root` 覆盖。

更完整的工作流与输出规范请阅读 [SKILL.md](SKILL.md)。

## 项目定义

本技能中的"项目"是指：
- 具有项目指令文件（如 `CLAUDE.md`、`AGENTS.md`、`PROJECT.md` 等）
- 具有明确的目录结构和功能模块
- 包含可执行的代码、脚本、或流程定义
- 类似 `init-project` 定义的项目结构

典型项目类型：
- **Agent Skills**: 符合 [Agent Skills 开放标准](https://agentskills.io) 的技能
- **工作流项目**: 定义了开发流程的项目
- **脚本工具集**: 一组协同工作的脚本和工具
- **文档项目**: 具有结构化文档和模板的项目

## 使用方法

### 推荐用法（自动完整测试流程）

**开发者建议**：

```
使用 auto-test-project 这个skill 对xxx流程进行1轮迭代优化。
```

### 人机协作用法（手动审核 AI 建议）

本技能支持灵活的"人机协作"模式，你可以手动查看和审核 AI 的建议，而不必自动执行完整的修复流程。

**典型场景**：

```
根据 auto-test-project 的B轮原则，目前 xxx 项目还有哪些优化的地方？
```

**优势**：
- 你可以先查看 AI 发现的项目级问题，再决定是否修复
- 可以选择性采纳建议，而不是全盘接受
- 适合用于项目代码审查、架构评估、技术债务分析等场景

**更多人机协作示例**：

```
根据 auto-test-project 的批判性思维框架，分析一下这个项目在跨模块设计上可能有哪些问题？
```

```
用 auto-test-project 的A轮独立评估模式，检查这个项目是否存在配置集中化的问题。
```

```
根据 auto-test-project 的质量原则检查维度，评估这个项目的模块划分是否合理。
```

### 触发方式

在 Claude Code 中使用以下表述之一触发本技能:

**自动测试模式**：
- "帮我测试一下这个项目"
- "我需要制定项目测试计划"
- "需要对项目进行迭代优化"
- "生成项目测试报告"

**人机协作模式**：
- "根据 auto-test-project 的 B 轮原则分析这个项目"
- "用 auto-test-project 的批判性思维检查这个项目架构"
- "根据 auto-test-project 的质量原则给出优化建议"

### 输入要求

使用本技能前，请准备：

1. **项目根目录路径**
   - 示例: `/path/to/project`

2. **测试发现的问题列表或优化目标**
   - 可来自: 用户反馈、测试结果、代码审查等
   - 至少包含: 问题描述、复现步骤、期望行为

3. **可选**: 已有测试数据或测试用例
   - 如果有，请提供数据路径

### 工作流程

本技能遵循 **项目初始化 + A轮×N + B轮** 的多轮迭代工作流：

```
用户输入（项目根目录 + 问题列表/优化目标）
  ↓
[项目初始化]：验证项目结构、识别项目类型
  ↓
[A轮 × N]：分析 → 计划 → 优化 → 轻量测试
  ↓
B轮：质量原则检查（以 `config.yaml:b_round_check.dimensions` 为准） → 针对性优化 → 轻量验证
  ↓
完成（文档齐全 + 问题闭环 + 项目 CHANGELOG.md 已更新）
```

详细说明请参阅 [SKILL.md](SKILL.md)。

## 输出交付

使用本技能后，您将获得：

1. **项目类型分析报告**（可选）：`PROJECT_TYPE.md`（记录项目类型和关键信息）
2. **规划文档（A轮）**：`plans/vYYYYMMDDHHMM.md`
3. **测试会话目录（A轮）**：`tests/vYYYYMMDDHHMM/`（包含 `TEST_PLAN.md`、`TEST_REPORT.md`）
4. **质量检查报告（B轮）**：`plans/B轮-vYYYYMMDDHHMM.md`
5. **验证会话目录（B轮）**：`tests/B轮-vYYYYMMDDHHMM/`（包含 `TEST_PLAN.md`、`TEST_REPORT.md`）

## 文件结构

```
auto-test-project/
├── SKILL.md                              # 技能主文档
├── README.md                             # 本文件
├── config.yaml                           # 配置文件
├── plans/                                # 规划文档目录
├── tests/                                # 测试会话目录
├── scripts/                              # 确定性辅助脚本
│   └── create_test_session.py           # 创建测试会话
├── templates/                            # 文档模板
│   ├── BUG_REPORT_TEMPLATE.md            # Bug报告模板
│   ├── OPTIMIZATION_PLAN_TEMPLATE.md     # 优化计划模板
│   ├── TEST_PLAN_TEMPLATE.md             # 测试计划模板
│   ├── TEST_REPORT_TEMPLATE.md           # 测试报告模板
│   ├── FINAL_SUMMARY_TEMPLATE.md         # 最终总结模板
│   ├── B_ROUND_CHECK_TEMPLATE.md         # B轮质量检查模板
│   └── PROJECT_TYPE_ANALYSIS_TEMPLATE.md # 项目类型分析模板
└── references/                           # 参考文档
    └── PROJECT_TESTING_BEST_PRACTICES.md # 项目级测试最佳实践
```

## 配置说明

本技能使用 `config.yaml` 配置项目级测试参数。

主要配置项:

- 说明：`config.yaml` 主要用于记录默认参数与检查维度；确定性脚本会读取必要配置（如 `directories/templates/verification`）并支持 CLI 覆盖，其余字段作为规划口径参考。
- **project_detection**: 项目类型识别配置（指令文件、配置文件、类型标志）
- **test_rounds**: 轮次控制（每轮最少问题数量与目标范围）
- **test_session**: 测试会话配置（时间戳格式、最大迭代轮数）
- **priority**: 优先级定义（P0/P1/P2/P3 的详细说明和示例）
- **b_round_check**: B轮质量检查（维度以 `b_round_check.dimensions` 为准 + 建议数量与修复率门槛）
- **verification**: 会话验证脚本默认阈值（报告长度、问题数量、严格模式开关）
- **project_testing**: 项目级测试边界配置（核心模块、跨模块测试、排除路径）

详细配置请参阅 [config.yaml](config.yaml)。

## 示例使用场景

### 场景 1: 优化一个技能项目

**输入**:
- 用户报告某个技能项目的 3 个 bug
- 项目根目录: `/path/to/skills/your-skill`

**执行流程**:
1. 项目初始化：识别项目类型为 Agent Skill
2. A轮：生成 `plans/vYYYYMMDDHHMM.md`（问题清单 + 改进计划）
3. A轮：创建 `tests/vYYYYMMDDHHMM/` 并按计划修复与验证
4. B轮：生成 `plans/B轮-vYYYYMMDDHHMM.md`（质量原则检查；维度以 `b_round_check.dimensions` 为准）
5. B轮：创建 `tests/B轮-vYYYYMMDDHHMM/` 并做针对性验证
6. 验收：更新项目 `CHANGELOG.md`

**输出**:
- 修复后的代码
- 完整的测试文档
- 项目 CHANGELOG.md 更新

### 场景 2: 多轮迭代优化一个工作流项目

**背景**: 第一次测试发现 10 个问题，计划分 3 轮迭代

**迭代轮次**:
- **第1轮** (`v202601021313`): 修复 P0(2个) + P1(3个) → 测试通过
- **第2轮** (`v202601031015`): 修复 P2(3个) + 跨模块问题(2个) → 测试通过
- **第3轮** (`v202601041420`): 修复 P3(2个) + 新发现的问题 → 测试通过

**最终输出**:
- `FINAL_SUMMARY.md`（总结 3 轮优化历程）
- 所有问题已修复
- 跨模块集成测试通过
- 测试覆盖率提升

## 更多参考

- 常见问题与证据标准：`references/FAQ.md`
- 项目级最佳实践：`references/PROJECT_TESTING_BEST_PRACTICES.md`
- 项目级问题挖掘技巧：`references/PROJECT_ISSUE_DISCOVERY_TECHNIQUES.md`
- 批判性思维指南：`references/CRITICAL_THINKING_GUIDE.md`
- 建设性建议标准：`references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md`
- 反例库（反模式速查）：`references/ANTI_PATTERNS_LIBRARY.md`
- 严格模式最小示例（P0-1 编号）：`references/EXAMPLE_STRICT_MINIMAL.md`

## 参考资源

- **技能主文档**: [SKILL.md](SKILL.md)
- **配置文件**: [config.yaml](config.yaml)
- **文档模板**: [templates/](templates/)
- **参考文档**:
  - [references/FAQ.md](references/FAQ.md)
  - [references/PROJECT_TESTING_BEST_PRACTICES.md](references/PROJECT_TESTING_BEST_PRACTICES.md)
  - [references/PROJECT_ISSUE_DISCOVERY_TECHNIQUES.md](references/PROJECT_ISSUE_DISCOVERY_TECHNIQUES.md)
  - [references/CRITICAL_THINKING_GUIDE.md](references/CRITICAL_THINKING_GUIDE.md)
  - [references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md](references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md)
  - [references/ANTI_PATTERNS_LIBRARY.md](references/ANTI_PATTERNS_LIBRARY.md)
- **Agent Skills标准**: [https://agentskills.io](https://agentskills.io)

**相关阅读**:
- 测试驱动开发（TDD）最佳实践
- 敏捷开发中的迭代优化方法
- 软件质量保证（SQA）标准流程
- 项目级质量管理体系

## 版本历史

- **v1.0.0** (2026-01-12): 初始版本
  - 从 auto-test-skill 迁移核心能力
  - 扩展为项目级测试支持
  - 项目类型识别
  - 跨模块问题分析
  - 项目级质量检查

## 许可证

本技能遵循 [Agent Skills 开放标准](https://agentskills.io)。

## 联系方式

- **作者**: bensz
- **创建时间**: 2026-01-12
- **反馈渠道**: 通过 GitHub Issues 或项目讨论区反馈

---

**祝您测试愉快!** 🎉
