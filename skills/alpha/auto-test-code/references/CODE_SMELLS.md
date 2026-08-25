# 代码异味识别指南

**用途**：快速识别代码中的常见异味

---

## 什么是代码异味？

代码异味（Code Smell）是代码中**可能存在问题**的表面特征。它不一定是 bug，但通常表明代码需要重构。

---

## 常见代码异味

### 1. 重复代码（Duplicated Code）

**特征**：
- 相同或相似的代码出现在多个地方
- 复制粘贴代码片段

**问题**：
- 维护成本高（修改需要改多处）
- 容易出现不一致

**示例**：
```python
# 重复的验证逻辑
def create_user(name):
    if not name or len(name) < 3:
        raise ValueError("Invalid name")
    # ...

def update_user(user_id, name):
    if not name or len(name) < 3:
        raise ValueError("Invalid name")  # 重复
    # ...
```

**重构**：
```python
def validate_name(name):
    if not name or len(name) < 3:
        raise ValueError("Invalid name")

def create_user(name):
    validate_name(name)
    # ...
```

---

### 2. 过长函数（Long Method）

**特征**：
- 函数超过 50 行
- 函数做太多事情

**问题**：
- 难以理解
- 难以测试
- 难以复用

**示例**：
```python
def process_request(request):
    # 100+ 行代码
    # 1. 验证请求
    # 2. 认证用户
    # 3. 处理业务逻辑
    # 4. 格式化响应
    # ...
```

**重构**：
```python
def process_request(request):
    validate_request(request)
    user = authenticate_user(request)
    result = process_business_logic(user, request)
    return format_response(result)
```

---

### 3. 过大类（Large Class）

**特征**：
- 类超过 300 行
- 类有太多职责

**问题**：
- 难以理解
- 难以维护
- 违反单一职责原则

**示例**：
```python
class UserManager:
    def create_user(self): ...
    def update_user(self): ...
    def delete_user(self): ...
    def send_email(self): ...  # 不相关
    def generate_report(self): ...  # 不相关
    def backup_data(self): ...  # 不相关
```

**重构**：
```python
class UserManager:
    def create_user(self): ...
    def update_user(self): ...
    def delete_user(self): ...

class EmailService:
    def send_email(self): ...

class ReportGenerator:
    def generate_report(self): ...
```

---

### 4. 过长参数列表（Long Parameter List）

**特征**：
- 函数参数超过 4 个

**问题**：
- 难以理解
- 难以使用
- 容易传错参数

**示例**：
```python
def create_user(name, email, age, address, phone, country, city, zip_code):
    # ...
```

**重构**：
```python
def create_user(user_data: UserData):
    # ...

class UserData:
    name: str
    email: str
    age: int
    # ...
```

---

### 5. 特征依恋（Feature Envy）

**特征**：
- 函数更关心其他类的数据而非自己的类

**问题**：
- 违反封装原则
- 高耦合

**示例**：
```python
class Order:
    def calculate_price(self):
        # 大量访问 Customer 的数据
        discount = self.customer.get_discount()
        tax_rate = self.customer.get_tax_rate()
        # ...
```

**重构**：
```python
class Order:
    def calculate_price(self):
        return self.customer.calculate_order_price(self)
```

---

### 6. 数据泥团（Data Clumps）

**特征**：
- 多个参数总是一起出现

**问题**：
- 代码冗余
- 容易遗漏

**示例**：
```python
def func1(x, y, width, height): ...
def func2(x, y, width, height): ...
def func3(x, y, width, height): ...
```

**重构**：
```python
class Rectangle:
    x: int
    y: int
    width: int
    height: int

def func1(rect: Rectangle): ...
```

---

### 7. 基本类型偏执（Primitive Obsession）

**特征**：
- 过度使用基本类型而非对象

**问题**：
- 丢失类型安全
- 代码重复

**示例**：
```python
def connect(host: str, port: int, timeout: int): ...
# 调用：connect("localhost", 8080, 30)
```

**重构**：
```python
class ConnectionConfig:
    host: str
    port: int
    timeout: int

def connect(config: ConnectionConfig): ...
```

---

### 8. 过度继承（Shotgun Surgery）

**特征**：
- 修改需要同时修改多个类

**问题**：
- 难以维护
- 容易遗漏

**示例**：
```python
# 添加新字段需要在多个类中修改
class User:
    def __init__(self, name):
        self.name = name

class UserView:
    def render(self, user):
        return f"Name: {user.name}"

class UserSerializer:
    def serialize(self, user):
        return {"name": user.name}
```

---

### 9. 魔法数字（Magic Numbers）

**特征**：
- 代码中出现未命名的数字常量

**问题**：
- 难以理解
- 难以修改

**示例**：
```python
if score > 75:  # 75 是什么？
    grade = "A"
elif score > 60:  # 60 是什么？
    grade = "B"
```

**重构**：
```python
GRADE_A_THRESHOLD = 75
GRADE_B_THRESHOLD = 60

if score > GRADE_A_THRESHOLD:
    grade = "A"
elif score > GRADE_B_THRESHOLD:
    grade = "B"
```

---

### 10. 死代码（Dead Code）

**特征**：
- 从未被执行的代码
- 已注释的代码

**问题**：
- 增加维护负担
- 造成困惑

**示例**：
```python
def old_function():
    # 这个函数不再被调用
    pass

# def deprecated_function():
#     ...
```

**重构**：删除这些代码

---

## 快速检查清单

在代码审查时，快速检查：

- [ ] 是否有重复代码？
- [ ] 是否有超过 50 行的函数？
- [ ] 是否有超过 4 个参数的函数？
- [ ] 是否有未命名的魔法数字？
- [ ] 是否有从未被调用的函数？
- [ ] 是否有总是一起出现的参数组？
- [ ] 是否有过度使用基本类型的情况？
- [ ] 类是否过大（>300 行）？
