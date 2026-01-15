# B轮质量检查报告（{{SESSION_NAME}}）

**检查ID**: {{SESSION_NAME}}  
**检查时间**: {{PLAN_TIME}}  
**目标项目**: {{PROJECT_NAME}}  
**项目根目录**: {{PROJECT_ROOT}}  
**项目类型**: {{PROJECT_TYPE}}  
**对应A轮测试**: {{TEST_ID}}（如不同请手动填写）  

---

## 检查结果总览（七大质量原则）

| 维度 | 状态 | 关键发现（一句话） |
|------|------|--------------------|
| 硬编码/AI功能规划 | ✅ / ⚠️ / ❌ | {{NOTE_1}} |
| 冗余残留错误检查 | ✅ / ⚠️ / ❌ | {{NOTE_2}} |
| 安全性检查 | ✅ / ⚠️ / ❌ | {{NOTE_3}} |
| 过度设计检查 | ✅ / ⚠️ / ❌ | {{NOTE_4}} |
| 通用性检查 | ✅ / ⚠️ / ❌ | {{NOTE_5}} |
| 一致性检查 | ✅ / ⚠️ / ❌ | {{NOTE_6}} |
| 项目指令文件瘦身检查 | ✅ / ⚠️ / ❌ | {{NOTE_7}} |

---

## 问题与建议清单（P0-P2）

> 说明：
> - 为支持验证脚本的“计划-报告一致性检查”，请使用可引用编号（如 `P0-1`），并确保 B 轮验证会话的 TEST_REPORT 中出现相同编号。
> - 每条建议需注明所属维度（建议使用 `config.yaml:b_round_check.dimensions` 的 name）。

### P0（必须修复）

#### P0-1: {{P0_1_TITLE}}

**维度**: {{P0_1_DIMENSION}}

**位置/范围**: {{P0_1_LOCATION}}

**影响**:
{{P0_1_IMPACT}}

**修复建议**:
{{P0_1_FIX}}

**验证方法**:
{{P0_1_VERIFY}}

---

#### P0-2: {{P0_2_TITLE}}

**维度**: {{P0_2_DIMENSION}}

**位置/范围**: {{P0_2_LOCATION}}

**影响**:
{{P0_2_IMPACT}}

**修复建议**:
{{P0_2_FIX}}

**验证方法**:
{{P0_2_VERIFY}}

---

### P1（应修复或给出明确不修复理由）

#### P1-1: {{P1_1_TITLE}}

**维度**: {{P1_1_DIMENSION}}

**位置/范围**: {{P1_1_LOCATION}}

**影响**:
{{P1_1_IMPACT}}

**修复建议**:
{{P1_1_FIX}}

**验证方法**:
{{P1_1_VERIFY}}

---

### P2（可延后，但建议记录原因）

#### P2-1: {{P2_1_TITLE}}

**维度**: {{P2_1_DIMENSION}}

**位置/范围**: {{P2_1_LOCATION}}

**影响**:
{{P2_1_IMPACT}}

**修复建议**:
{{P2_1_FIX}}

**验证方法**:
{{P2_1_VERIFY}}

---

## 验收门槛（默认口径以 config.yaml 为准）

- 建议数量：`config.yaml:b_round_check.min_suggestions` / `config.yaml:b_round_check.target_suggestions_range`
- 修复率门槛：`config.yaml:b_round_check.p0_fix_rate_required` / `config.yaml:b_round_check.p1_fix_rate_required`

