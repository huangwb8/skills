---
name: code-reviewer
description: 用于任务完成、重大功能实现或合并前的检查，根据计划或需求审查实现并按严重程度分级（Critical/Important/Minor）。未经代码审查不得合并。
metadata:
  short-description: 代码审查与质量保证
  keywords:
    - 代码审查
    - Code Review
    - 代码质量
    - 安全检查
    - 性能优化
    - 最佳实践
    - code review
    - quality check
  category: 代码质量
  author: 社区最佳实践
  platform: Claude Code | OpenAI Codex | ChatGPT
  iron-law: |
    NO MERGE WITHOUT CODE REVIEW FIRST
---

# Code Reviewer - 代码审查专家

## 铁律

```
NO MERGE WITHOUT CODE REVIEW FIRST
```

**违反规则的信件就是违反规则的精神。**

**无例外**：
- 不跳过代码审查直接合并
- 不因"小改动"而跳过审查
- 不因"时间紧"而降低审查标准
- Critical 问题必须修复才能合并

---

## 常见合理化

| 借口 | 现实 |
|------|------|
| "只是小改动，不需要审查" | 小改动也可能引入大 Bug。所有改动都应审查 |
| "时间紧，先合并再审查" | 事后审查≠事前预防。合并后问题更难修复 |
| "我自己检查过了" | 自我审查有盲区。需要第二双眼睛 |
| "代码已经很完美了" | 完美代码也存在改进空间。审查是学习机会 |
| "只是重构，没有逻辑变化" | 重构最容易引入回归。必须审查测试 |

---

## 红色标志 - 停止并重新开始

- "只是小改动，不需要审查"
- "时间紧，先合并再审查"
- "我自己检查过了"
- "代码已经很完美了"
- "只是重构，没有逻辑变化"
- 跳过代码审查直接合并

**所有这些意味着：停止合并。先进行代码审查。**

---

## 核心理念

**代码审查** 不仅是找 Bug，更是：
- ✅ **确保代码安全**
- ✅ **提升代码质量**
- ✅ **传播最佳实践**
- ✅ **团队知识共享**

```
┌─────────────────────────────────────────────────────────┐
│  安全检查(P0) → 性能检查(P1) → 可维护性(P2) → 建设性反馈  │
└─────────────────────────────────────────────────────────┘
```

---

## 何时使用本技能

在以下场景时激活：

- 需要代码审查（Code Review）
- 提到"代码质量"、"最佳实践"、"重构"
- Pull Request / Merge Request 审查
- 代码提交前的质量检查
- 需要检查安全性、性能问题
- **子代理驱动开发中每个任务后**

---

## 审查维度与优先级

### 优先级定义

| 优先级 | 含义 | 响应时间 | 阻塞发布 |
|--------|------|----------|----------|
| **P0** | 安全风险、核心功能缺陷 | 立即修复 | ✅ 是 |
| **P1** | 重要优化、性能问题 | 本轮修复 | ⚠️ 可能 |
| **P2** | 改进建议、锦上添花 | 后续迭代 | ❌ 否 |

---

## 审查检查清单

### 1. 安全性检查（P0）⚠️

**必须修复的问题**：

#### SQL 注入

```python
# ❌ 危险：SQL 注入风险
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# ✅ 安全：使用参数化查询
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

#### XSS（跨站脚本）

```javascript
// ❌ 危险：XSS 风险
div.innerHTML = userInput;

// ✅ 安全：转义用户输入
div.textContent = userInput;
// 或使用 DOMPurify
div.innerHTML = DOMPurify.sanitize(userInput);
```

#### 认证与授权

```python
# ❌ 危险：硬编码密钥
API_KEY = "sk-1234567890abcdef"

# ✅ 安全：环境变量
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY not configured")

# ❌ 危险：缺少权限检查
def delete_user(user_id):
    db.delete(user_id)

# ✅ 安全：检查权限
@require_permission("admin")
def delete_user(user_id):
    db.delete(user_id)
```

#### 敏感数据泄露

```python
# ❌ 危险：日志中包含敏感信息
logger.info(f"User login: {username}, password: {password}")

# ✅ 安全：脱敏日志
logger.info(f"User login: {username}, password: ***")
```

**安全检查清单**：
- [ ] 无 SQL 注入风险
- [ ] 无 XSS 风险
- [ ] 无认证/授权缺陷
- [ ] 无敏感数据泄露
- [ ] 无不安全的随机数
- [ ] 无硬编码密钥
- [ ] 依赖无已知漏洞

---

### 2. 性能检查（P1）⚡

**重要优化**：

#### N+1 查询问题

```python
# ❌ 性能问题：N+1 查询
def get_users_with_posts():
    users = db.query("SELECT * FROM users")
    for user in users:
        user.posts = db.query(f"SELECT * FROM posts WHERE user_id = {user.id}")
    return users

# ✅ 优化：使用 JOIN
def get_users_with_posts():
    return db.query("""
        SELECT u.*, p.*
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
    """)
```

#### 算法复杂度

```python
# ❌ 性能问题：O(n²) 复杂度
def find_duplicates(items):
    duplicates = []
    for i, item1 in enumerate(items):
        for j, item2 in enumerate(items):
            if i != j and item1 == item2:
                duplicates.append(item1)
    return duplicates

# ✅ 优化：O(n) 复杂度
def find_duplicates(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
```

#### 内存效率

```python
# ❌ 性能问题：一次性加载所有数据
def process_large_file(filename):
    with open(filename) as f:
        data = f.readlines()  # 可能占用大量内存
    for line in data:
        process(line)

# ✅ 优化：流式处理
def process_large_file(filename):
    with open(filename) as f:
        for line in f:  # 逐行读取
            process(line)
```

#### 缓存策略

```python
# ❌ 性能问题：重复计算
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# ✅ 优化：添加缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

**性能检查清单**：
- [ ] 无 N+1 查询问题
- [ ] 算法复杂度合理
- [ ] 无内存泄漏
- [ ] 使用适当的缓存
- [ ] 数据库查询优化
- [ ] 避免不必要的计算

---

### 3. 可维护性检查（P2）🔧

**改进建议**：

#### 命名规范

```python
# ❌ 不好的命名
def d(x):
    return x * 2

# ✅ 好的命名
def double_value(value):
    return value * 2
```

#### 函数长度

```python
# ❌ 不好的函数：过长（100+ 行）
def process_order(order):
    # 100 行代码...
    pass

# ✅ 好的做法：拆分为多个函数
def process_order(order):
    validate_order(order)
    calculate_totals(order)
    save_order(order)
    send_confirmation(order)
```

#### 代码重复

```python
# ❌ 不好的重复
def validate_user(user):
    if not user.name:
        raise ValueError("Name required")
    if not user.email:
        raise ValueError("Email required")

def validate_admin(admin):
    if not admin.name:
        raise ValueError("Name required")
    if not admin.email:
        raise ValueError("Email required")

# ✅ 好的做法：提取公共逻辑
def validate_person(person):
    if not person.name:
        raise ValueError("Name required")
    if not person.email:
        raise ValueError("Email required")
```

#### 注释质量

```python
# ❌ 无用的注释
# 设置 i 为 0
i = 0

# ✅ 有用的注释
# 使用二分查找查找用户索引
user_index = binary_search(users, target_user_id)
```

**可维护性检查清单**：
- [ ] 命名清晰且一致
- [ ] 函数长度 < 50 行
- [ ] 文件长度 < 500 行
- [ ] 无重复代码
- [ ] 注释有意义
- [ ] 遵循团队规范

---

### 4. 测试覆盖（P1）🧪

```python
# ❌ 测试覆盖不足
def calculate_discount(price, user_level):
    if user_level == "VIP":
        return price * 0.8
    return price

# 只测试了正常情况
def test_calculate_discount():
    assert calculate_discount(100, "VIP") == 80

# ✅ 完整的测试覆盖
def test_calculate_discount():
    # 正常情况
    assert calculate_discount(100, "VIP") == 80
    assert calculate_discount(100, "NORMAL") == 100

    # 边界条件
    assert calculate_discount(0, "VIP") == 0
    assert calculate_discount(100, "") == 100

    # 异常情况
    with pytest.raises(TypeError):
        calculate_discount(None, "VIP")
```

**测试检查清单**：
- [ ] 测试覆盖率 ≥ 80%
- [ ] 测试边界条件
- [ ] 测试异常情况
- [ ] 测试独立且可重复

---

### 5. 设计模式（P2）🎨

#### SOLID 原则

```python
# ❌ 违反单一职责原则
class User:
    def save(self): pass
    def send_email(self): pass
    def generate_report(self): pass

# ✅ 遵循单一职责原则
class User:
    def save(self): pass

class EmailService:
    def send_email(self, user): pass

class ReportService:
    def generate_report(self, user): pass
```

**设计检查清单**：
- [ ] 遵循 SOLID 原则
- [ ] 适当使用设计模式
- [ ] 模块间耦合度低
- [ ] 接口清晰且稳定

---

## 审查流程

### 1. 自动检查

```bash
# 运行 linter
eslint src/

# 类型检查
tsc --noEmit

# 安全扫描
npm audit

# 测试
pytest
```

### 2. 静态分析

```bash
# 代码复杂度
lizard src/

# 依赖检查
depcheck

# 重复代码检测
jscpd src/
```

### 3. 人工审查

### 4. 建�设性反馈

**反馈模板**：

```markdown
## 问题：[简短描述]

**优先级**：P0 / P1 / P2

**位置**：[文件名:行号]

**问题说明**：
[当前代码的问题]

**建议修改**：
```python
[修改后的代码]
```

**理由**：
[为什么要这样修改]

**相关资源**：
[文档、最佳实践链接]
```

**反馈示例**：

```markdown
## 问题：SQL 注入风险

**优先级**：P0

**位置**：`user_service.py:45`

**问题说明**：
当前代码使用字符串拼接构建 SQL 查询，存在 SQL 注入风险。攻击者可以通过构造恶意的 `user_id` 参数执行任意 SQL 命令。

**建议修改**：
```python
# 修改前
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# 修改后
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

**理由**：
使用参数化查询可以防止 SQL 注入，数据库驱动会自动转义特殊字符。

**相关资源**：
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [Python DB-API 参数化查询](https://www.python.org/dev/peps/pep-0249/)
```

---

## 审查完成清单

- [ ] 所有 P0 安全问题已修复
- [ ] 所有 P1 性能问题已处理
- [ ] 代码复杂度可控
- [ ] 测试覆盖充分
- [ ] 符合团队规范
- [ ] 提供建设性反馈
- [ ] 更新相关文档

---

## 相关参考

- [代码审查清单](../references/code-review-checklist.md)
- [代码审查代理模板](../references/code-reviewer/code-reviewer.md)
