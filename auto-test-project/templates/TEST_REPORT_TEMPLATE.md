# 测试报告（A轮）

**测试ID**: {{TEST_ID}}
**项目根目录**: {{PROJECT_ROOT}}
**测试时间**: {{TEST_TIME}}
**测试计划**: {{TEST_PLAN}}

---

## 执行摘要

**测试状态**: ✅ 通过 / ❌ 失败 / ⚠️ 部分通过

**关键发现**:
- {{KEY_FINDING_1}}
- {{KEY_FINDING_2}}

---

## 验证点结果

### 验证点 1: {{VERIFICATION_POINT_1}}

**状态**: ✅ 通过 / ❌ 失败 / ⚠️ 部分通过

**证据**:
- {{EVIDENCE_1}}

**结论**:
{{CONCLUSION_1}}

---

### 验证点 2: {{VERIFICATION_POINT_2}}

**状态**: ✅ 通过 / ❌ 失败 / ⚠️ 部分通过

**证据**:
- {{EVIDENCE_2}}

**结论**:
{{CONCLUSION_2}}

---

## 新发现的问题

| ID | 问题描述 | 位置 | 严重程度 |
|----|---------|------|----------|
| {{NEW_ISSUE_1_ID}} | {{NEW_ISSUE_1_DESC}} | {{NEW_ISSUE_1_LOC}} | P0/P1/P2/P3 |
| {{NEW_ISSUE_2_ID}} | {{NEW_ISSUE_2_DESC}} | {{NEW_ISSUE_2_LOC}} | P0/P1/P2/P3 |

---

## 测试产物

### 测试脚本

- `{{SCRIPT_NAME}}`: {{SCRIPT_DESCRIPTION}}

### 测试数据

- `{{DATA_FILE}}`: {{DATA_DESCRIPTION}}

### 输出结果

- `{{OUTPUT_FILE}}`: {{OUTPUT_DESCRIPTION}}

---

## 跨模块验证

### 模块间交互

| 模块组合 | 测试结果 | 备注 |
|---------|---------|------|
| {{MODULE_PAIR_1}} | ✅ / ❌ | {{NOTE_1}} |
| {{MODULE_PAIR_2}} | ✅ / ❌ | {{NOTE_2}} |

---

## 建议与后续行动

### 立即行动

- {{IMMEDIATE_ACTION_1}}
- {{IMMEDIATE_ACTION_2}}

### 后续优化

- {{FOLLOW_UP_OPTIMIZATION_1}}
- {{FOLLOW_UP_OPTIMIZATION_2}}

---

## 测试环境

**操作系统**: {{OS}}
**Python版本**: {{PYTHON_VERSION}}
**依赖版本**: {{DEPENDENCIES}}

---

## 附录

### 命令输出

```
{{COMMAND_OUTPUT}}
```

### 日志文件

- `{{LOG_FILE}}`
