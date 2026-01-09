# 测试报告: [项目名称] v[版本号]

**测试时间**: {{TEST_DATE}}
**测试环境**: {{TEST_ENVIRONMENT}}
**测试状态**: ✅ 通过 / ❌ 失败 / ⚠️ 部分通过

---

## 执行摘要

### 测试状态概览

**总体状态**: {{OVERALL_STATUS}}

### 修复统计

| 指标 | 数值 | 目标 | 状态 |
|------|------|------|------|
| 计划修复问题数 | {{PLANNED_FIXES}} | - | - |
| 成功修复问题数 | {{ACTUAL_FIXES}} | {{PLANNED_FIXES}} | {{STATUS_1}} |
| 修复成功率 | {{FIX_RATE}}% | 100% | {{STATUS_2}} |
| 发现新问题数 | {{NEW_ISSUES}} | 0 | {{STATUS_3}} |

### 测试统计

| 指标 | 数值 | 目标 | 状态 |
|------|------|------|------|
| 测试用例总数 | {{TOTAL_TESTS}} | - | - |
| 通过用例数 | {{PASSED_TESTS}} | {{TOTAL_TESTS}} | {{STATUS_4}} |
| 失败用例数 | {{FAILED_TESTS}} | 0 | {{STATUS_5}} |
| 测试通过率 | {{PASS_RATE}}% | 95% | {{STATUS_6}} |

### 时间统计

| 阶段 | 预计时间 | 实际时间 | 差异 |
|------|----------|----------|------|
| 准备 | {{PREP_PLANNED}} | {{PREP_ACTUAL}} | {{PREP_DIFF}} |
| 开发 | {{DEV_PLANNED}} | {{DEV_ACTUAL}} | {{DEV_DIFF}} |
| 测试 | {{TEST_PLANNED}} | {{TEST_ACTUAL}} | {{TEST_DIFF}} |
| 验证 | {{VALIDATE_PLANNED}} | {{VALIDATE_ACTUAL}} | {{VALIDATE_DIFF}} |
| 文档 | {{DOC_PLANNED}} | {{DOC_ACTUAL}} | {{DOC_DIFF}} |
| **总计** | {{TOTAL_PLANNED}} | {{TOTAL_ACTUAL}} | {{TOTAL_DIFF}} |

---

## 问题修复详情

### 问题 #1: [标题]

**基本信息**:
- **严重程度**: Critical / High / Medium / Low
- **优先级**: P0 / P1 / P2 / P3
- **状态**: ✅ 已修复 / ❌ 未修复 / ⚠️ 部分修复

**修复内容**:

**修改文件**:
- `{{FILE_PATH}}` (第{{LINE_NUMBER}}行)

**修改详情**:
\```python
# 修改前
{{OLD_CODE}}

# 修改后
{{NEW_CODE}}
\```

**修改说明**:
{{MODIFICATION_NOTES}}

**验证结果**:

**测试用例**: `{{TEST_CASE_NAME}}`
**测试脚本**: `scripts/test_fix_1.py`

**测试输出**:
\```
{{TEST_OUTPUT}}
\```

**验证点检查**:
- [ ] ✅ 验证点1: {{DESCRIPTION_1}}
- [ ] ✅ 验证点2: {{DESCRIPTION_2}}
- [ ] ✅ 验证点3: {{DESCRIPTION_3}}

**结论**: {{CONCLUSION_1}}

**截图/日志**:
\```
{{SCREENSHOT_OR_LOG}}
\```

---

### 问题 #2: [标题]

(重复上述结构)

---

(按修复顺序列出所有问题的修复情况)

---

## 测试用例结果

### 测试用例 1: [名称]

**基本信息**:
- **测试场景**: {{TEST_SCENARIO}}
- **测试类型**: 单元测试 / 集成测试 / 回归测试
- **状态**: ✅ 通过 / ❌ 失败

**测试详情**:

**输入**:
\```python
{{TEST_INPUT}}
\```

**预期输出**:
\```python
{{EXPECTED_OUTPUT}}
\```

**实际输出**:
\```python
{{ACTUAL_OUTPUT}}
\```

**差异说明**:
{{DIFFERENCE_NOTES}}

**执行时间**: {{EXECUTION_TIME}} 秒

**结论**: {{CONCLUSION_2}}

---

### 测试用例 2: [名称]

(重复上述结构)

---

(列出所有测试用例的结果)

---

## 发现的新问题

### 新问题 #N+1: [标题]

**基本信息**:
- **严重程度**: Critical / High / Medium / Low
- **优先级**: P0 / P1 / P2 / P3
- **发现时间**: {{DISCOVERY_DATE}}

**问题描述**:
{{NEW_ISSUE_DESCRIPTION}}

**复现步骤**:
1. {{STEP_1}}
2. {{STEP_2}}
3. {{STEP_3}}

**建议处理**:
- [ ] 下次迭代修复
- [ ] 立即修复
- [ ] 暂缓处理

**原因分析**:
{{ROOT_CAUSE_ANALYSIS}}

---

### 新问题 #N+2: [标题]

(重复上述结构)

---

## 回归测试结果

### 已修复问题验证

| 问题 # | 标题 | 修复状态 | 回归测试 | 结论 |
|--------|------|----------|----------|------|
| #1 | ... | ✅ 已修复 | ✅ 通过 | ✅ 无回归 |
| #2 | ... | ✅ 已修复 | ✅ 通过 | ✅ 无回归 |
| #3 | ... | ✅ 已修复 | ❌ 失败 | ❌ 有回归 |

### 功能完整性检查

**核心功能**:
- [ ] ✅ 核心功能A正常
- [ ] ✅ 核心功能B正常
- [ ] ❌ 核心功能C异常

**边缘场景**:
- [ ] ✅ 边缘场景1正常
- [ ] ⚠️ 边缘场景2部分异常

**性能测试**:
- [ ] ✅ 响应时间正常
- [ ] ✅ 内存占用正常
- [ ] ❌ 吞吐量下降{{PERFORMANCE_DEGRADATION}}%

### 兼容性检查

- [ ] ✅ 向后兼容性保持
- [ ] ✅ API接口未破坏
- [ ] ✅ 数据格式未改变
- [ ] ⚠️ 配置文件格式变更(需更新文档)

---

## 质量指标

### 代码质量

| 指标 | 修复前 | 修复后 | 改进 |
|------|--------|--------|------|
| 代码行数 | {{LOC_BEFORE}} | {{LOC_AFTER}} | {{LOC_CHANGE}} |
| 圈复杂度 | {{CC_BEFORE}} | {{CC_AFTER}} | {{CC_CHANGE}} |
| 测试覆盖率 | {{COVERAGE_BEFORE}}% | {{COVERAGE_AFTER}}% | {{COVERAGE_IMPROVEMENT}}% |
| 代码重复率 | {{DUPLICATION_BEFORE}}% | {{DUPLICATION_AFTER}}% | {{DUPLICATION_REDUCTION}}% |

### Bug密度

| 阶段 | Bug数 | 每千行Bug数 |
|------|-------|-------------|
| 修复前 | {{BUGS_BEFORE}} | {{BUG_DENSITY_BEFORE}} |
| 修复后 | {{BUGS_AFTER}} | {{BUG_DENSITY_AFTER}} |
| 改进 | {{BUG_REDUCTION}} | {{BUG_DENSITY_IMPROVEMENT}} |

---

## 问题分析

### 未修复问题分析

**问题 #X**: [标题]

**未修复原因**:
{{UNFIXED_REASON}}

**建议方案**:
{{SUGGESTED_SOLUTION}}

**计划时间**:
{{PLANNED_TIME}}

---

### 失败测试分析

**测试用例 Y**: [名称]

**失败原因**:
{{FAILURE_REASON}}

**错误日志**:
\```
{{ERROR_LOG}}
\```

**修复建议**:
{{FIX_SUGGESTION}}

---

## 下一步行动

### 如果测试通过 ✅

1. **更新文档**:
   - [ ] 更新 CHANGELOG.md
   - [ ] 更新 README.md
   - [ ] 更新 API 文档

2. **代码审查**:
   - [ ] 提交 Pull Request
   - [ ] 通过代码审查
   - [ ] 合并到主分支

3. **发布准备**:
   - [ ] 打版本标签
   - [ ] 编写 Release Notes
   - [ ] 通知用户

4. **归档测试会话**:
   - [ ] 移动到 `test_archive/`
   - [ ] 更新测试历史记录

### 如果测试失败 ❌

1. **分析失败原因**:
   - [ ] 识别失败的根本原因
   - [ ] 评估影响范围
   - [ ] 制定修复方案

2. **更新优化计划**:
   - [ ] 记录未修复的问题
   - [ ] 记录新发现的问题
   - [ ] 调整优先级

3. **创建新测试会话**:
   - [ ] 创建新的测试目录
   - [ ] 复制相关文档
   - [ ] 准备新的测试数据

4. **进入下一轮迭代**:
   - [ ] 重新制定修复计划
   - [ ] 执行修复和测试
   - [ ] 重复验证流程

### 如果部分通过 ⚠️

1. **风险评估**:
   - [ ] 评估未修复问题的风险
   - [ ] 评估对用户的影响
   - [ ] 评估业务影响

2. **决策**:
   - [ ] 接受当前状态(低风险)
   - [ ] 继续修复(高风险)
   - [ ] 部分发布(中风险)

3. **相应行动**:
   - [ ] 根据"如果测试通过"的流程
   - [ ] 根据"如果测试失败"的流程

---

## 附录

### 测试环境详情

**硬件环境**:
- CPU: {{CPU_INFO}}
- 内存: {{MEMORY_INFO}}
- 磁盘: {{DISK_INFO}}

**软件环境**:
- 操作系统: {{OS_INFO}}
- Python版本: {{PYTHON_VERSION}}
- 依赖包版本:
  - {{PACKAGE_1}}: {{VERSION_1}}
  - {{PACKAGE_2}}: {{VERSION_2}}
  - {{PACKAGE_3}}: {{VERSION_3}}

### 测试数据清单

- `data/input1.json` ({{SIZE_1}} KB) - {{DESCRIPTION_1}}
- `data/input2.json` ({{SIZE_2}} KB) - {{DESCRIPTION_2}}
- `data/test_cases.yaml` ({{SIZE_3}} KB) - {{DESCRIPTION_3}}

### 测试脚本清单

- `scripts/test_fix_1.py` - 测试问题#1修复
- `scripts/test_fix_2.py` - 测试问题#2修复
- `scripts/test_fix_3.py` - 测试问题#3修复
- `scripts/validate_all.py` - 执行所有测试

### 测试输出清单

- `output/results.json` - 测试结果汇总
- `output/logs/test.log` - 测试执行日志
- `output/screenshots/` - 测试截图(如果有)

### 参考文档

- Bug报告: `BUG_REPORT.md`
- 优化计划: `OPTIMIZATION_PLAN.md`
- 项目README: `../../README.md`
- CHANGELOG: `../../CHANGELOG.md`

---

**报告生成时间**: {{REPORT_GENERATION_TIME}}
**报告生成人**: {{REPORT_GENERATOR}}
**报告版本**: 1.0
