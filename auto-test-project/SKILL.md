---
name: auto-test-project
version: 1.0.1
category: normal
description: |
  项目级自动化测试驱动优化技能 - 用于对完整项目（如 skill、workflow、或类似 init-project 定义的流程项目）进行持续性 AI 优化。

  **核心能力**:
  - 支持多轮 A 轮迭代：分析 → 计划 → 优化 → 轻量测试（可重复 N 次）
  - A 轮结束后执行 B 轮质量检查：项目级六大质量原则全覆盖
  - 规范化测试会话命名：`vYYYYMMDDHHMM`
  - 将每轮产出固化为文档与目录（可追溯、可复现、可复盘）
  - 项目级优化：从单个 skill 扩展到完整项目（多文件、多模块、跨目录）

metadata:
  short-description: 多轮 A 轮测试 + B 轮质量检查 的项目级测试驱动优化流水线
  keywords:
    - project testing
    - project QA
    - project optimization
    - bug report
    - regression testing
    - iteration
    - workflow
    - CI/CD
    - continuous improvement
---

# auto-test-project（项目级自动化测试驱动优化）

## 目标

为完整项目（包括技能项目、工作流项目、或其他具有 `CLAUDE.md` 或类似指令文件的项目）提供系统性的测试驱动优化能力，通过多轮迭代实现持续改进。

## 项目定义

本技能中的"项目"是指：
- 具有项目指令文件（如 `CLAUDE.md`、`AGENTS.md`、`PROJECT.md` 等）
- 具有明确的目录结构和功能模块
- 包含可执行的代码、脚本、或流程定义
- 类似 `init-project` 定义的项目结构

典型项目类型：
- **Agent Skills**：符合 [Agent Skills 开放标准](https://agentskills.io) 的技能
- **工作流项目**：定义了开发流程的项目
- **脚本工具集**：一组协同工作的脚本和工具
- **文档项目**：具有结构化文档和模板的项目

## 你要产出的东西

本 skill 的交付不是"口头建议"，而是一组可追溯的文件：

- `plans/vYYYYMMDDHHMM.md`：A 轮问题分析与改进计划（每轮 1 份）
- `tests/vYYYYMMDDHHMM/`：A 轮测试会话目录（包含 `TEST_PLAN.md` + `TEST_REPORT.md`）
- `plans/B轮-vYYYYMMDDHHMM.md`：B 轮质量检查报告（六大质量原则）
- `tests/B轮-vYYYYMMDDHHMM/`：B 轮验证会话目录（包含 `TEST_PLAN.md` + `TEST_REPORT.md`）

## 目录与命名规范

- 测试会话 ID：`vYYYYMMDDHHMM`（分钟级时间戳）
- 规划文档：放在 `plans/`
- 测试会话：放在 `tests/`
- B 轮统一加前缀：`B轮-`

## 工作流程

### 概览

```
用户输入（项目根目录 + 问题列表/优化目标）
  ↓
[项目初始化]：验证项目结构、识别项目类型
  ↓
[A轮 × N]：分析 → 计划 → 优化 → 轻量测试
  ↓
B轮：项目级六大质量原则检查 → 针对性优化 → 轻量验证
  ↓
完成（文档齐全 + 问题闭环 + 项目 CHANGELOG.md 已更新）
```

### 项目初始化

#### P.1 验证项目结构

目标：确认目标是一个有效的"项目"，并识别项目类型。

检查项：
- [ ] 是否存在项目指令文件（`CLAUDE.md`、`AGENTS.md`、`PROJECT.md` 等）
- [ ] 是否存在配置文件（`config.yaml`、`package.json`、`pyproject.toml` 等）
- [ ] 是否有明确的目录结构（源码、文档、脚本等）

输出：`PROJECT_TYPE.md`（可选，记录项目类型和关键信息）

#### P.2 识别测试边界

目标：确定测试范围和优先级。

分析维度：
- **核心模块**：哪些文件/目录是项目的核心功能？
- **测试路径**：哪些功能需要优先测试？
- **依赖关系**：模块间的依赖关系是什么？

输出：在首个 A 轮计划中记录测试边界。

### A 轮测试（可重复 N 次）

#### A.1 初始化会话（生成测试 ID + 目录）

目标：创建本轮的 `plans/` 与 `tests/` 骨架。

推荐使用确定性脚本：

```bash
python3 auto-test-project/scripts/create_test_session.py --project-root . --kind a --id vYYYYMMDDHHMM
```

最低要求：
- `plans/` 与 `tests/` 存在
- `tests/vYYYYMMDDHHMM/TEST_PLAN.md` 与 `tests/vYYYYMMDDHHMM/TEST_REPORT.md` 存在

#### A.2 问题分析与计划生成（写入 plans/）

目标：把本轮要解决的问题写成可执行计划，按 P0/P1/P2 排序。

输出：`plans/vYYYYMMDDHHMM.md`

要求：
- 每个问题必须包含：位置（文件:行号）、影响、修复建议、验证方法
- 如首轮无明确问题列表：先做静态检查与一致性检查，再给出问题清单
- 项目级问题需要考虑跨模块影响和依赖关系

#### A.3 执行优化与轻量测试（写入 tests/）

目标：按计划逐项修复，并用轻量测试验证。

输出：`tests/vYYYYMMDDHHMM/TEST_REPORT.md`

轻量测试原则：
- 只验证"核心路径"与"本轮变更点"
- 每条结论必须有可复现证据（命令输出、文件、对比结果）
- 中间产物放入 `tests/vYYYYMMDDHHMM/_artifacts/`，不污染主目录
- 项目级测试需要考虑模块间交互

#### A.4 是否进入下一轮

进入下一轮 A 轮的典型条件：
- 用户指定的轮次数未完成
- 仍存在未解决的 P0 / P1
- 轻量测试报告中出现阻塞性失败
- 发现新的跨模块问题需要解决

**重要**：A 轮结束后（无论多少轮），必须进入 B 轮质量检查，不得跳过。

### B 轮质量检查（项目级六大质量原则）

⚠️ **强制执行**：B 轮质量检查是项目级自动测试流程的强制性环节，除非用户明确要求跳过，否则不得省略。

#### B.1 产出质量检查报告（写入 plans/）

目标：对 A 轮后的最新状态做系统性质量检查。

输出：`plans/B轮-vYYYYMMDDHHMM.md`

检查维度（以 `config.yaml` 的 `b_round_check.dimensions` 为准）：
- 硬编码/AI 功能规划
- 冗余残留错误检查
- 安全性检查
- 过度设计检查
- 通用性检查
- 一致性检查

模板：`templates/B_ROUND_CHECK_TEMPLATE.md`

#### B.2 B 轮优化与验证（写入 tests/）

目标：对 B 轮发现的 P0/P1 进行针对性修复并验证。

推荐创建独立会话目录：

```bash
python3 auto-test-project/scripts/create_test_session.py --project-root . --kind b --id vYYYYMMDDHHMM
```

输出：`tests/B轮-vYYYYMMDDHHMM/TEST_REPORT.md`

## 完成条件（验收）

- [ ] 用户指定的 A 轮次数已完成（或明确说明提前结束原因）
- [ ] B 轮质量检查已完成并形成报告（⚠️ 强制要求，参考 `config.yaml` 的 `b_round_check.mandatory`）
- [ ] 关键问题（P0/P1）已闭环：计划 → 修复 → 证据 → 结论
- [ ] `plans/` 与 `tests/` 结构完整且可追溯
- [ ] 目标项目的 `CHANGELOG.md` 已更新

## 与 auto-test-skill 的区别

| 维度 | auto-test-skill | auto-test-project |
|------|-----------------|-------------------|
| **目标对象** | 单个 Agent Skill | 完整项目（多模块、多文件） |
| **测试范围** | 单个 skill 目录 | 整个项目目录 |
| **问题分析** | skill 级别（SKILL.md、config.yaml） | 项目级别（跨模块、跨文件） |
| **质量检查** | skill 六大原则 | 项目级六大原则（扩展） |
| **输出位置** | 在 skill 内部创建 `plans/` 和 `tests/` | 在项目根目录创建 `plans/` 和 `tests/` |
| **CHANGELOG** | 更新 skill 的 CHANGELOG.md | 更新项目的 CHANGELOG.md |

## 可复用资源

- 配置：`config.yaml`
- 模板：`templates/`
- 参考：`references/PROJECT_TESTING_BEST_PRACTICES.md`
- 辅助脚本：`scripts/create_test_session.py`

## 项目级最佳实践

### 1. 测试边界管理

- 明确测试范围：核心功能 vs 边缘功能
- 识别模块依赖：哪些模块可以独立测试，哪些需要集成测试
- 设置优先级：先测试核心路径，再测试边缘情况

### 2. 跨模块问题处理

- 记录问题影响的模块范围
- 分析修复的连锁反应
- 验证修复后是否影响其他模块

### 3. 项目级一致性

- 确保所有模块遵循相同的工程原则
- 检查跨模块的接口一致性
- 验证项目级配置的正确性

### 4. 文档同步更新

- 项目级变更需要更新项目 CHANGELOG.md
- 跨模块变更需要同步更新相关模块文档
- 保持项目指令文件（CLAUDE.md 等）与实际状态一致
