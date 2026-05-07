# A 轮代码审查计划结构

**用途**：作为 A 轮代码审查报告的结构参考

---

## 报告头部

```markdown
# 代码审查计划（v202601231200）

**审查日期**: 2026-01-23
**审查ID**: v202601231200
**目标代码路径**: /path/to/project
**代码语言**: Python
**代码规模**: 约 5,000 行（10 个模块）
```

---

## 独立评估声明

```markdown
## 独立评估与审查范围（强制）

- [x] 本轮基于目标代码的**当前状态**独立评估
- [x] **未查看**历史 `tmp/run_*/` 工作区中的审查文件

**扫描命令证据**：
```bash
# 扫描 Python 文件
find /path/to/project -name "*.py" | head -20

# 统计代码行数
cloc /path/to/project --include-lang=Python

# 搜索潜在问题模式
rg -n "TODO|FIXME|XXX|HACK" /path/to/project
```

**审查维度与深挖策略**：
- 全维度覆盖（强制）：本轮必须覆盖全部审查维度（以 `a_round_check.dimensions` 为准；如项目存在 `.auto-test-code/config.yaml`，同名字段可覆盖）
- 深挖维度（可选）：算法复杂度分析、边界条件覆盖
- 刁钻角度：空输入、超大输入、并发竞态（用于深挖维度）
```

---

## 问题清单示例

### P0 示例

```markdown
### P0（必须修复）

1) 文件资源泄漏：异常情况下文件未关闭

- **位置**：`src/file_processor.py:56-65`
- **问题类型**：资源泄漏

**现象**：
```python
def process_file(path):
    f = open(path, 'r')
    data = f.read()
    result = parse(data)  # 如果这里抛出异常
    f.close()
    return result
```

**推理**：
- parse(data) 可能抛出异常（如 JSON 解析错误）
- 异常时 f.close() 不会执行
- 高频调用会耗尽文件描述符

**影响**：
- 程序运行一段时间后无法打开新文件
- "Too many open files" 错误
- 服务不可用

**优先级**：P0（资源泄漏，会导致服务不可用）

**修复建议**：
```python
def process_file(path):
    with open(path, 'r') as f:
        data = f.read()
    return parse(data)
```

**验证方法**：
1. 单元测试：在 parse() 中人为抛出异常
2. 验证文件描述符在异常后仍然释放（lsof -p PID）
3. 压力测试：循环 1000 次，确认文件描述符不泄漏
```

### P1 示例

```markdown
### P1（强烈建议）

1) 算法性能问题：使用线性搜索而非哈希表

- **位置**：`src/user_manager.py:45-52`
- **问题类型**：性能问题

**现象**：
```python
def find_user(users, user_id):
    for user in users:
        if user.id == user_id:
            return user
    return None
```

**推理**：
- users 是列表，查找是 O(n)
- 如果有 100,000 个用户，平均需要 50,000 次比较

**影响**：
- 用户量大时响应时间线性增长
- 每个请求都调用 find_user 时会成为瓶颈

**优先级**：P1（性能问题，影响用户体验）

**修复建议**：
```python
def find_user(users_dict, user_id):
    return users_dict.get(user_id)
```

**验证方法**：
1. 构造 100,000 个用户的测试数据
2. 测量查找耗时：应从毫秒级降至微秒级
3. 单元测试验证正确性
```

---

## 执行步骤示例

```markdown
## 执行步骤

1. 修复文件资源泄漏（P0-1）
   - 文件：src/file_processor.py:56-65
   - 改为使用 with 语句

2. 修复除零错误（P0-2）
   - 文件：src/calculator.py:23
   - 添加除零检查

3. 优化查找性能（P1-1）
   - 文件：src/user_manager.py:45-52
   - 将 users 列表改为字典

4. 添加输入验证（P1-2）
   - 文件：src/api.py:34-40
   - 验证 user_id 类型
```

---

## 轻量测试计划

```markdown
## 本轮轻量测试

- 会话目录：`tmp/run_20260123115959/tests/v202601231200/`
- 测试计划：`tmp/run_20260123115959/tests/v202601231200/TEST_PLAN.md`
- 测试报告：`tmp/run_20260123115959/tests/v202601231200/TEST_REPORT.md`

**测试范围**：
- 验证 P0-1 修复：异常时文件正确关闭
- 验证 P0-2 修复：除零时抛出明确异常
- 验证 P1-1 修复：查找性能 < 1ms
```

---

## 问题统计

```markdown
## 问题统计

| 优先级 | 数量 | 占比 |
|--------|------|------|
| P0 | 3 | 30% |
| P1 | 5 | 50% |
| P2 | 2 | 20% |
| **总计** | **10** | 100% |

**系统性问题**：
- 算法问题：2 个（查找、排序）
- 资源问题：2 个（文件泄漏、内存泄漏）
- 边界问题：1 个（除零）

**质量检查**：
- [x] 总问题数 ≥ 10
- [x] P0 + P1 占比 ≥ 60%（80%）
- [x] 系统性问题 ≥ 3（5 个）
```
