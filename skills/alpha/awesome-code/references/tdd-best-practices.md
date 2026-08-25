# TDD 最佳实践参考文档

## 核心原则

测试驱动开发（Test-Driven Development）是一种软件开发方法，强调先编写测试，再编写实现代码。

### Red-Green-Refactor 循环

```
┌─────────────────────────────────────────┐
│  1. RED：编写一个失败的测试              │
│     - 描述新的功能或行为                 │
│     - 运行测试确认失败                   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  2. GREEN：编写最简单的代码使测试通过    │
│     - 不追求完美，只求通过               │
│     - 运行测试确认成功                   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  3. REFACTOR：在测试保护下优化代码      │
│     - 改善代码结构                      │
│     - 保持测试通过                       │
└─────────────────────────────────────────┘
              ↓
           回到步骤 1
```

## 测试命名规范

### AAA 模式（Arrange-Act-Assert）

```python
def test_should_return_discount_when_customer_is_premium():
    # Arrange（准备）：设置测试数据和依赖
    customer = create_premium_customer()
    cart = create_cart_with_items(["item1", "item2"])

    # Act（执行）：调用被测试的方法
    total = calculate_total(customer, cart)

    # Assert（断言）：验证结果
    assert total == expected_discounted_total
```

### 命名模板

```
should_{ExpectedBehavior}_when_{StateUnderTest}

示例：
- should_return_error_when_input_is_invalid
- should_send_notification_when_payment_succeeds
- should_redirect_to_login_when_user_not_authenticated
```

## 测试覆盖策略

### 测试金字塔

```
        /\
       /E2E\        少量端到端测试
      /------\
     / Integration \  适量集成测试
    /--------------\
   /    Unit Tests    \  大量单元测试
  /--------------------\
```

| 测试类型 | 数量 | 速度 | 成本 | 覆盖范围 |
|---------|------|------|------|----------|
| 单元测试 | 多 | 快 | 低 | 函数/方法 |
| 集成测试 | 中 | 中 | 中 | 模块交互 |
| E2E 测试 | 少 | 慢 | 高 | 完整流程 |

### 边界条件测试

必须测试的边界条件：

- [ ] 空值（null/None）
- [ ] 空集合（[]、""）
- [ ] 最小值/最大值
- [ ] 负数
- [ ] 非法类型
- [ ] 并发场景

## 测试隔离原则

### 每个测试必须独立

```python
# ❌ 错误：测试间有依赖
def test_a():
    global_state.set_value(1)

def test_b():
    # 依赖 test_a 的执行顺序
    assert global_state.get_value() == 1

# ✅ 正确：每个测试独立
def test_a():
    state = create_state()
    state.set_value(1)
    assert state.get_value() == 1

def test_b():
    state = create_state()
    state.set_value(1)
    assert state.get_value() == 1
```

### 使用 Setup/Teardown

```python
@pytest.fixture(autouse=True)
def reset_database():
    # Setup
    db.reset()
    yield
    # Teardown
    db.cleanup()
```

## Mock 与 Stub

### 何时使用 Mock

- 外部服务调用（API、数据库）
- 复杂依赖（文件系统、网络）
- 不可控资源（时间、随机数）

### Mock 示例

```python
def test_should_charge_payment_when_order_valid():
    # Arrange
    payment_gateway = Mock()
    payment_gateway.charge.return_value = Success(amount=100)

    order = create_order(amount=100)
    service = PaymentService(gateway=payment_gateway)

    # Act
    result = service.process_payment(order)

    # Assert
    assert result.is_success()
    payment_gateway.charge.assert_called_once_with(amount=100)
```

## 测试覆盖率目标

### 推荐标准

| 代码类型 | 覆盖率目标 |
|---------|-----------|
| 核心业务逻辑 | ≥ 90% |
| 工具函数 | ≥ 80% |
| UI/前端 | ≥ 70% |
| 配置/常量 | ≥ 50% |

### 覆盖率工具

```bash
# Python
pytest --cov=src --cov-report=html

# JavaScript
jest --coverage

# Java
jacoco:report
```

## 常见反模式

### ❌ 测试实现细节

```python
# 测试内部变量名称（脆弱）
def test_method_sets_internal_variable():
    obj = MyClass()
    obj.method()
    assert obj._internal_var == 1  # 测试细节
```

### ✅ 测试行为

```python
# 测试可观察行为（稳定）
def test_method_produces_expected_output():
    obj = MyClass()
    result = obj.method()
    assert result == expected_value  # 测试行为
```

## TDD 流程检查清单

在完成 TDD 循环后，验证：

- [ ] 所有测试通过
- [ ] 覆盖率达标
- [ ] 测试命名清晰
- [ ] 测试独立且可重复
- [ ] 无 Mock 滥用
- [ ] 代码经过重构
- [ ] 无测试私有方法
- [ ] 边界条件已测试

## 参考资源

- [Test-Driven Development with Claude Code](https://stevekinney.com/courses/ai-development/test-driven-development-with-claude)
- [TDD Guard for Claude Code](https://nizar.se/tdd-guard-for-claude-code/)
- [VoltAgent/awesome-claude-skills: TDD 相关 Skills](https://github.com/VoltAgent/awesome-claude-skills)
