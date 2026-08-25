# 系统化调试与根因分析参考文档

## 核心理念

系统化调试不是猜测，而是**科学方法在软件调试中的应用**：观察 → 假设 → 实验 → 结论。

## 调试流程

### 第一步：收集证据（信息收集）

#### 必需信息

- [ ] **完整堆栈追踪**（不只是最后一行）
- [ ] **错误消息**（完整文本，包括错误代码）
- [ ] **复现步骤**（最小可复现示例）
- [ ] **环境信息**（OS、语言版本、依赖版本）
- [ ] **相关日志**（错误发生前后的日志）
- [ ] **最近变更**（代码、配置、依赖）

#### 堆栈追踪分析模板

```python
# 示例：分析堆栈追踪
Traceback (most recent call last):
  File "app.py", line 42, in process_order       # ← 错误入口
  File "services/payment.py", line 15, in charge  # ← 调用链
  File "utils/api.py", line 78, in request        # ← 失败点
ConnectionError: Failed to connect to payment-gateway.com

分析：
1. 错误类型：ConnectionError（网络连接失败）
2. 失败位置：utils/api.py:78
3. 业务上下文：处理订单的支付流程
4. 可能原因：网络问题、服务宕机、DNS 解析失败
```

### 第二步：形成假设（假设驱动）

#### 假设格式

使用 **"因为...，所以..."** 结构：

```
假设：因为 API endpoint URL 配置错误，所以请求发送到错误的服务器。
      因为支付网关服务宕机，所以连接被拒绝。
      因为网络防火墙阻止出站连接，所以请求超时。
```

#### 假设优先级排序

| 优先级 | 类型 | 示例 |
|-------|------|------|
| P0 | 最近变更 | 昨天部署的代码引入的 Bug |
| P1 | 配置问题 | 环境变量设置错误 |
| P2 | 外部依赖 | 第三方 API 服务异常 |
| P3 | 边界条件 | 特殊输入触发的罕见逻辑 |

### 第三步：系统性验证（实验设计）

#### 一次验证一个假设

```python
# ❌ 错误：同时验证多个假设
def test_hypothesis():
    change_config()
    restart_service()
    update_dependency()
    assert works()  # 哪个修改起作用？

# ✅ 正确：隔离变量
def test_config_hypothesis():
    only_change_config()
    assert works()

def test_service_hypothesis():
    only_restart_service()
    assert works()
```

#### 二分查找法

```python
def binary_search_bug():
    # 确定是否有问题
    if bug_exists():
        # 确定时间范围
        old_version = "v1.0.0"  # 无问题
        new_version = "v1.5.0"  # 有问题

        # 二分查找引入问题的版本
        mid = bisect_versions(old_version, new_version)
        # 缩小范围，最终定位到具体 commit
```

### 第四步：定位根因（区分症状与原因）

#### 根因分析方法：五问法（5 Whys）

```
问题：用户登录失败

问1：为什么登录失败？
答：因为数据库查询超时。

问2：为什么数据库查询超时？
答：因为用户表没有索引。

问3：为什么没有索引？
答：因为迁移脚本没有执行。

问4：为什么迁移脚本没有执行？
答：因为部署流程中缺少迁移步骤。

问5：为什么部署流程缺少迁移步骤？
答：因为部署文档没有更新。

根本原因：部署文档不完整（而非数据库慢）
```

#### 症状 vs 根因对比

| 症状 | 根因 |
|------|------|
| 页面加载慢 | N+1 查询问题 |
| 内存溢出 | 缓存未设置过期时间 |
| 数据丢失 | 事务未正确提交 |
| 偶发性错误 | 并发竞争条件 |

### 第五步：实施修复（最小化原则）

#### 修复策略

1. **最小化修复**：只修改必要的代码
2. **添加测试**：防止回归
3. **文档更新**：记录决策和教训
4. **验证修复**：多环境测试

#### 修复示例

```python
# ❌ 过度修复
def fix_bug():
    # 修改整个函数结构
    # 引入新依赖
    # 重构相关代码
    # ...（风险高）

# ✅ 最小化修复
def fix_bug():
    # 只修复特定问题
    if critical_condition:
        return safe_default  # 防御性编程
    # 保持原有逻辑不变
```

## 常见调试模式

### 模式 1：日志驱动的调试

```python
import logging

# 配置结构化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def process_order(order):
    logger.info(f"Processing order: {order.id}")

    try:
        result = payment_service.charge(order.amount)
        logger.info(f"Payment successful: {result.transaction_id}")
        return result

    except PaymentError as e:
        logger.error(f"Payment failed for order {order.id}: {e}")
        logger.debug(f"Order details: {order.to_dict()}")
        raise
```

### 模式 2：断言驱动的调试

```python
def calculate_discount(customer, cart):
    # 前置条件断言
    assert customer is not None, "Customer cannot be None"
    assert cart.total > 0, "Cart total must be positive"

    discount_rate = customer.discount_rate

    # 不变式断言
    assert 0 <= discount_rate <= 1, f"Invalid discount rate: {discount_rate}"

    final_price = cart.total * (1 - discount_rate)

    # 后置条件断言
    assert final_price >= 0, "Final price cannot be negative"
    assert final_price <= cart.total, "Discount cannot exceed total"

    return final_price
```

### 模式 3：二分定位法

```python
def locate_bug_position():
    # 确定问题范围
    if works_in_isolation():
        # 问题在交互逻辑
        if works_with_simplified_inputs():
            # 问题在边界条件
            test_edge_cases()
        else:
            # 问题在基本逻辑
            test_core_functionality()
    else:
        # 问题在单元内部
        test_dependencies()
```

## 生产环境调试

### 远程调试原则

- [ ] **只读优先**：先查询，不修改
- [ ] **最小权限**：使用只读凭证
- [ ] **审计日志**：记录所有操作
- [ ] **灰度验证**：先在测试环境验证

### 安全检查清单

在生产环境调试前确认：

- [ ] 有授权（运维批准）
- [ ] 有监控（告警通知）
- [ ] 有回滚计划
- [ ] 非高峰时段
- [ ] 数据已备份

## 调试完成检查清单

- [ ] 根本原因已识别（非症状）
- [ ] 修复方案最小化
- [ ] 添加回归测试
- [ ] 文档已更新（注释、README）
- [ ] 代码审查完成
- [ ] 多环境验证通过
- [ ] 监控告警正常
- [ ] 团队分享（如需要）

## 参考资源

- [Systematic Debugging (obra/systematic-debugging)](https://github.com/VoltAgent/awesome-claude-skills)
- [Root Cause Tracing (obra/root-cause-tracing)](https://github.com/VoltAgent/awesome-claude-skills)
- [9 Ways Claude Code Helps Me with Testing and Debugging](https://medium.com/@joe.njenga/9-ways-claude-code-helps-me-with-testing-and-debugging-like-a-pro-tester-69c8776282ab)
