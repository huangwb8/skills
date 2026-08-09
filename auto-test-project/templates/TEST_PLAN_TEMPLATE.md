# 测试计划（{{ROUND_KIND}}）

**测试ID**: {{TEST_ID}}
**项目根目录**: {{PROJECT_ROOT}}
**项目类型**: {{PROJECT_TYPE}}
**测试时间**: {{TEST_TIME}}
**对应计划**: {{PLAN_DOC_PATH}}

---

## 测试目标

{{TEST_OBJECTIVE}}

---

## 测试范围

### 核心模块

- {{MODULE_1}}: {{SCOPE_1}}
- {{MODULE_2}}: {{SCOPE_2}}

### 测试边界

- **包含**: {{INCLUDE_SCOPE}}
- **排除**: {{EXCLUDE_SCOPE}}

---

## 验证点

### 验证点 1: {{VERIFICATION_POINT_1}}

**描述**: {{DESCRIPTION_1}}

**验证方法**:
- {{METHOD_1}}

**预期结果**: {{EXPECTED_RESULT_1}}

---

### 验证点 2: {{VERIFICATION_POINT_2}}

**描述**: {{DESCRIPTION_2}}

**验证方法**:
- {{METHOD_2}}

**预期结果**: {{EXPECTED_RESULT_2}}

---

## 测试步骤

1. {{STEP_1}}
2. {{STEP_2}}
3. {{STEP_3}}

---

## 通过标准

- [ ] {{CRITERION_1}}
- [ ] {{CRITERION_2}}
- [ ] {{CRITERION_3}}

---

## 风险与注意事项

- {{RISK_1}}
- {{RISK_2}}

---

完成后建议运行验证脚本检查会话质量：

```bash
python3 auto-test-project/scripts/verify_test_session.py \
  --project-root "{{PROJECT_ROOT}}" \
  --task-root "{{TASK_ROOT}}" \
  --require-plan \
  "{{SKILL_WORKSPACE}}/output/tests/{{SESSION_NAME}}"
```
