# auto-test-project

这个 skill 用来对完整项目做 A 轮批判性测试和 B 轮质量检查，适合“项目级测试驱动优化”；如果你只是想修一个明确功能点，通常不该直接用它。

## 用法

### 最推荐用法

```text
请使用 auto-test-project skill 对本项目进行项目级测试驱动优化。
输入：项目根目录 `.`，以及要重点检查的问题或优化目标
输出：`plans/` 与 `tests/` 下的 A 轮/B 轮计划、测试记录和验证结果
```

### 进阶用法

```text
请使用 auto-test-project skill 对这个项目做完整测试闭环。
输入：项目根目录 `.`，重点关注认证流程、文档一致性和配置安全
输出：多轮 A 轮计划、测试记录、B 轮质量检查结果
另外，还有下列参数约束：
- A 轮要求：至少发现 10 个问题
- B 轮要求：必须执行
- 输出要求：所有证据都写入 `plans/` 和 `tests/`
```

## 能做什么

- 把一次“项目测试”拆成可追溯的 A 轮问题发现和 B 轮质量复检。
- 为技能项目、工作流项目、脚本工具集、文档项目提供统一的测试闭环。
- 强制把测试计划、问题清单、验证结果写入文件，而不是只给口头建议。
- 默认把 B 轮质量检查视为必做步骤。
- 不适合替代单个 bugfix、单个功能开发或日常答疑。

## 使用示例

### 示例 1：测试一个技能仓库

```text
请使用 auto-test-project skill 测试这个 skill 项目。
输入：项目根目录 `.`，重点关注 README、SKILL.md、config.yaml 和 scripts 的一致性
输出：A 轮问题计划、测试记录和 B 轮质量检查结果
```

### 示例 2：做一轮带重点的项目审查

```text
请使用 auto-test-project skill 对这个项目做项目级测试。
输入：项目根目录 `.`，重点检查路径安全、输出目录隔离和文档口径
输出：测试报告与修复建议
```

### 示例 3：要求完整闭环

```text
请使用 auto-test-project skill 对本项目做完整测试驱动优化。
输入：项目根目录 `.`
输出：`plans/`、`tests/`、B 轮质量检查结果
另外，还有下列参数约束：
- 至少执行 1 轮 A 轮
- 不跳过 B 轮
- 收尾时验证测试会话完整性
```

## 输出

- `plans/vYYYYMMDDHHMM.md`：A 轮问题分析与改进计划。
- `tests/vYYYYMMDDHHMM/`：A 轮测试会话目录，至少包含 `TEST_PLAN.md` 和 `TEST_REPORT.md`。
- `plans/B轮-vYYYYMMDDHHMM.md`：B 轮质量检查报告。
- `tests/B轮-vYYYYMMDDHHMM/`：B 轮验证会话目录。
- README 不会替你“自动通过测试”；它强调的是问题发现、证据沉淀和闭环验证。

## 配置

- 配置文件：`auto-test-project/config.yaml`
- 默认 A 轮轮次：`1`
- 单轮最少问题数：`10`
- A 轮建议目标问题数：`15-25`
- B 轮默认：`mandatory: true`
- 关键配置节：
  - `directories`
  - `test_rounds`
  - `b_round_check.dimensions`
  - `verification`

## 备选用法（脚本/硬编码）

如果你想先创建标准会话骨架，再人工补计划和报告，可以直接走脚本。

### 创建 A 轮或 B 轮会话

```bash
python3 auto-test-project/scripts/create_test_session.py \
  --project-root . \
  --kind a \
  --create-plan
```

### 用现有计划填充 TEST_PLAN

```bash
python3 auto-test-project/scripts/create_test_session.py \
  --project-root . \
  --kind a \
  --create-plan \
  --seed-test-plan-from-plan
```

### 校验测试会话完整性

```bash
python3 auto-test-project/scripts/verify_test_session.py \
  --require-plan \
  tests/v202603241200
```

## 常见问题

### Q：它和 `auto-test-code` 有什么区别？

A：`auto-test-project` 面向整个项目，强调跨模块、跨文档、跨配置的一致性和闭环；不是单文件或单函数测试器。

### Q：我只想修一个功能，还要用它吗？

A：通常不用。只有当你需要系统性测试、质量复检、沉淀计划与证据时，它才最有价值。

### Q：为什么一定要写 `plans/` 和 `tests/`？

A：这是它的核心价值之一。没有计划和证据，项目级测试很难复现、比较和收尾。

### Q：可以跳过 B 轮吗？

A：默认不建议。B 轮负责检查一致性、安全性、过度设计和配置集中化，缺了它就不算完整闭环。
