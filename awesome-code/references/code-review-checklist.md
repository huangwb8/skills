# 代码审查与质量保证参考文档

## 审查流程

### 预审查阶段（自动化）

1. **运行自动化检查**
   ```bash
   # Linting
   eslint . || flake8 . || pylint src/

   # 类型检查
   tsc --noEmit || mypy src/

   # 安全扫描
   npm audit || snyk test || bandit -r src/

   # 测试
   pytest || npm test
   ```

2. **查看 CI/CD 结果**
   - 所有检查必须通过
   - 测试覆盖率不能下降
   - 性能基准测试通过

### 人工审查阶段

## 安全性检查（P0 - Critical）

### 注入攻击

- [ ] **SQL 注入**：使用参数化查询
  ```python
  # ❌ 易受攻击
  query = f"SELECT * FROM users WHERE name = '{user_input}'"

  # ✅ 安全
  query = "SELECT * FROM users WHERE name = ?"
  cursor.execute(query, [user_input])
  ```

- [ ] **命令注入**：避免直接拼接命令
  ```python
  # ❌ 危险
  os.system(f"cat {user_file}")

  # ✅ 安全
  subprocess.run(["cat", user_file], check=True)
  ```

- [ ] **XSS**：转义用户输入
  ```javascript
  // ❌ 危险
  div.innerHTML = userContent

  // ✅ 安全
  div.textContent = userContent
  ```

### 认证与授权

- [ ] **认证**：敏感操作需要身份验证
- [ ] **授权**：检查资源访问权限
- [ ] **会话管理**：适当的超时和注销

### 敏感数据处理

- [ ] **密钥管理**：不在代码中硬编码密钥
  ```python
  # ❌ 错误
  API_KEY = "sk-1234567890"

  # ✅ 正确
  API_KEY = os.getenv("API_KEY")
  ```

- [ ] **日志脱敏**：不在日志中记录敏感信息
  ```python
  # ❌ 错误
  logger.info(f"User login: {username}, password: {password}")

  # ✅ 正确
  logger.info(f"User login: {username}")
  ```

- [ ] **数据传输**：使用 HTTPS/TLS

### 加密与哈希

- [ ] **密码存储**：使用 bcrypt/argon2（非 MD5/SHA1）
- [ ] **敏感数据**：静态加密
- [ ] **随机数**：使用加密安全随机数生成器

## 性能检查（P1 - High）

### 数据库查询

- [ ] **N+1 查询问题**
  ```python
  # ❌ N+1 问题
  for order in orders:
      customer = db.query(Customer, order.customer_id)  # N 次查询

  # ✅ 使用 JOIN
  orders = db.query(Orders).join(Customer).all()
  ```

- [ ] **缺少索引**：查询字段应有索引
- [ ] **选择性查询**：避免 SELECT *

### 算法复杂度

- [ ] **时间复杂度**：关注嵌套循环
  ```python
  # ❌ O(n²)
  for item in items:
      if item in other_items:  # O(n) 查找
          pass

  # ✅ O(n)
  lookup = set(other_items)  # O(1) 查找
  for item in items:
      if item in lookup:
          pass
  ```

- [ ] **空间复杂度**：避免不必要的数据复制

### 缓存策略

- [ ] **重复计算**：缓存昂贵操作结果
- [ ] **缓存失效**：正确处理缓存更新
- [ ] **缓存穿透**：处理不存在的键

### 资源管理

- [ ] **连接池**：复用数据库/HTTP 连接
- [ ] **流式处理**：大文件使用流式读取
- [ ] **内存泄漏**：正确释放资源

## 可维护性检查（P2 - Medium）

### 代码复杂度

- [ ] **圈复杂度** ≤ 10（每函数）
- [ ] **嵌套深度** ≤ 4
- [ ] **函数长度** ≤ 50 行
- [ ] **参数数量** ≤ 5

### 命名规范

- [ ] **变量名**：描述性、小写下划线
  ```python
  # ❌ 不清晰
  d = calculate(u, p)

  # ✅ 清晰
  discount = calculate_discount(unit_price, quantity)
  ```

- [ ] **函数名**：动词开头，描述行为
- [ ] **类名**：名词，大驼峰
- [ ] **常量**：全大写下划线

### 代码重复

- [ ] **重复逻辑**：提取为函数
- [ ] **相似结构**：使用模板/泛型
- [ ] **魔法值**：定义为常量

### 注释与文档

- [ ] **复杂逻辑**：添加注释说明"为什么"
- [ ] **公共 API**：提供文档字符串
- [ ] **TODO/FIXME**：有跟踪 issue

```python
# ❌ 无意义注释
# 增加计数
count += 1

# ✅ 解释原因
# 使用计数器而不是 len()，因为列表可能为空且性能关键
count += 1
```

### 错误处理

- [ ] **异常捕获**：具体异常类型（不裸 except）
- [ ] **错误传播**：适当处理或重新抛出
- [ ] **错误消息**：提供有用的调试信息

```python
# ❌ 过于宽泛
try:
    process()
except:
    pass

# ✅ 具体且有意义
try:
    process()
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    raise
```

## 测试覆盖（P1 - High）

- [ ] **单元测试**：核心逻辑有测试
- [ ] **边界条件**：测试空值、边界值
- [ ] **错误路径**：测试异常情况
- [ ] **集成测试**：关键流程有端到端测试

## 设计模式与架构（P2 - Medium）

### SOLID 原则

- [ ] **单一职责**：每个类/函数只做一件事
- [ ] **开闭原则**：对扩展开放，对修改封闭
- [ ] **里氏替换**：子类可替换父类
- [ ] **接口隔离**：接口专一，不臃肿
- [ ] **依赖倒置**：依赖抽象而非具体

### 耦合度

- [ ] **模块依赖**：单向依赖，无循环
- [ ] **全局状态**：避免使用全局变量
- [ ] **硬编码**：配置外部化

## 审查反馈模板

### 反馈格式

```markdown
## [P0/P1/P2] 问题类型

**位置**：[filename:line]

**问题**：简要描述问题

**风险/影响**：为什么这是个问题

**建议**：如何修复

**示例**（可选）：
```python
# 当前代码
...
# 建议代码
...
```

**优先级说明**：...
```

### 建设性反馈原则

1. **具体化**：指向具体代码位置
2. **解释原因**：说明为什么需要修改
3. **提供方案**：给出具体建议
4. **区分优先级**：P0（必须修复）vs P2（建议改进）
5. **正面反馈**：认可好的做法

## 审查检查清单总结

### 提交前自查

- [ ] 代码符合团队规范
- [ ] 自动化检查全部通过
- [ ] 自我审查完成
- [ ] 注释充分且准确
- [ ] 文档已更新
- [ ] 测试覆盖率不降低
- [ ] 无敏感信息泄露

### 审查人检查

- [ ] 安全性：无 P0 问题
- [ ] 性能：无 P1 问题
- [ ] 可维护性：P2 问题可接受
- [ ] 测试：核心功能有覆盖
- [ ] 整体：设计合理，易于理解

## 参考资源

- [Code Review (getsentry/code-review)](https://github.com/getsentry/sentry-skills)
- [Code Auditor (qdhenry/Claude-Command-Suite)](https://github.com/qdhenry/Claude-Command-Suite)
- [Find Bugs (getsentry/find-bugs)](https://github.com/getsentry/sentry-skills)
