---
name: auto-test-skill
version: 2.0.2
category: normal
description: |
  自动化测试驱动优化技能 - 用于在技能/项目迭代时，通过多轮 A 轮轻量测试 + B 轮质量检查（六大原则），
  系统化发现、记录、修复问题，并沉淀可追溯的 `plans/` 与 `tests/` 文档。

  **核心能力**:
  - 支持多轮 A 轮迭代：分析 → 计划 → 优化 → 轻量测试（可重复 N 次）
  - A 轮结束后执行 B 轮质量检查：六大质量原则全覆盖
  - 规范化测试会话命名：`vYYYYMMDDHHMM`
  - 将每轮产出固化为文档与目录（可追溯、可复现、可复盘）
metadata:
  short-description: 多轮 A 轮测试 + B 轮质量检查 的测试驱动优化流水线
  keywords:
    - testing
    - QA
    - bug report
    - regression
    - iteration
    - optimization
    - workflow
---

# auto-test-skill（自动化测试驱动优化技能）

## 你要产出的东西

本 skill 的交付不是“口头建议”，而是一组可追溯的文件：

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
用户输入
  ↓
[A轮 × N]：分析 → 计划 → 优化 → 轻量测试
  ↓
B轮：六大质量原则检查 → 针对性优化 → 轻量验证
  ↓
完成（文档齐全 + 问题闭环）
```

### A 轮测试（可重复 N 次）

#### A.1 初始化会话（生成测试 ID + 目录）

目标：创建本轮的 `plans/` 与 `tests/` 骨架。

推荐使用确定性脚本（避免 AI 每次手动拼目录/文件名）：

```bash
# 方式1：在目标 skill 根目录内执行（--skill-root .）
python3 /path/to/auto-test-skill/scripts/create_test_session.py --skill-root . --kind a --id vYYYYMMDDHHMM --create-plan

# 方式2：在任意位置执行（--skill-root 指向目标 skill 根目录）
python3 auto-test-skill/scripts/create_test_session.py --skill-root /path/to/target-skill --kind a --id vYYYYMMDDHHMM --create-plan
```

最低要求：
- `plans/` 与 `tests/` 存在
- `tests/vYYYYMMDDHHMM/TEST_PLAN.md` 与 `tests/vYYYYMMDDHHMM/TEST_REPORT.md` 存在
可选增强（推荐）：
- 使用 `--create-plan` 自动生成 `plans/vYYYYMMDDHHMM.md` 的骨架（默认不覆盖）

#### A.2 问题分析与计划生成（写入 plans/）

目标：把本轮要解决的问题写成可执行计划，按 P0/P1/P2 排序。

输出：`plans/vYYYYMMDDHHMM.md`

要求：
- 每个问题必须包含：位置（文件:行号）、影响、修复建议、验证方法
- 如首轮无明确问题列表：先做静态检查与一致性检查，再给出问题清单

#### A.3 执行优化与轻量测试（写入 tests/）

目标：按计划逐项修复，并用轻量测试验证。

输出：`tests/vYYYYMMDDHHMM/TEST_REPORT.md`

轻量测试原则：
- 只验证“核心路径”与“本轮变更点”
- 每条结论必须有可复现证据（命令输出、文件、对比结果）
- 中间产物放入 `tests/vYYYYMMDDHHMM/_artifacts/`，不污染主目录

#### A.4 是否进入下一轮

进入下一轮 A 轮的典型条件：
- 用户指定的轮次数未完成
- 仍存在未解决的 P0 / P1
- 轻量测试报告中出现阻塞性失败

**重要**：A 轮结束后（无论多少轮），必须进入 B 轮质量检查，不得跳过。

### B 轮质量检查（六大质量原则）

⚠️ **强制执行**：B 轮质量检查是自动测试流程的强制性环节，除非用户明确要求跳过，否则不得省略。

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
python3 /path/to/auto-test-skill/scripts/create_test_session.py --skill-root . --kind b --id vYYYYMMDDHHMM --create-plan
```

输出：`tests/B轮-vYYYYMMDDHHMM/TEST_REPORT.md`

## 完成条件（验收）

- [ ] 用户指定的 A 轮次数已完成（或明确说明提前结束原因）
- [ ] B 轮质量检查已完成并形成报告（⚠️ 强制要求，参考 `config.yaml` 的 `b_round_check.mandatory`）
- [ ] 关键问题（P0/P1）已闭环：计划 → 修复 → 证据 → 结论
- [ ] `plans/` 与 `tests/` 结构完整且可追溯
- [ ] 目标 skill 的 `CHANGELOG.md` 已更新

## 可复用资源

- 配置：`config.yaml`
- 模板：`templates/`
- 参考：`references/TESTING_BEST_PRACTICES.md`
- 辅助脚本：`scripts/create_test_session.py`
