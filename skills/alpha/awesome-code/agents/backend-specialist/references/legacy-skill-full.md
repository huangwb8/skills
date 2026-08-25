---
name: backend-specialist
description: 后端开发专家。精通 Node.js/Python/Go/Rust 等后端技术栈，专注于 API 设计、数据库优化、认证授权、微服务架构和性能调优。用于后端服务开发、API 设计和系统架构。
metadata:
  short-description: 后端开发与系统架构
  keywords:
    - 后端开发
    - API 设计
    - Node.js
    - Python
    - Go
    - Rust
    - 数据库
    - 微服务
    - 认证授权
    - 性能优化
  category: 后端开发
  author: 社区最佳实践
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Backend Specialist - 后端开发专家

## 核心理念

**现代后端开发** 的最佳实践：

```
┌─────────────────────────────────────────────────────────┐
│  API 设计 → 数据建模 → 性能优化 → 安全加固 → 可观测性  │
└─────────────────────────────────────────────────────────┘
```

**核心原则**：
- ✅ **RESTful / GraphQL 设计**
- ✅ **数据库优化**
- ✅ **安全第一**
- ✅ **可扩展性**
- ✅ **可观测性**

---

## 何时使用本技能

在以下场景时激活：

- 开发后端服务或 API
- 提到 Node.js、Python、Go、Rust
- 需要 API 设计
- 数据库设计与优化
- 认证授权实现
- 微服务架构
- 性能调优

---

## 技术栈选择

### 按场景选择

| 场景 | 推荐技术 | 理由 |
|------|----------|------|
| **快速原型** | Python + FastAPI | 开发效率高，生态丰富 |
| **高并发 I/O** | Node.js / Go | 异步 I/O 性能好 |
| **性能关键** | Rust / Go | 内存安全，执行效率高 |
| **数据密集** | Python + Pandas | 数据处理库丰富 |
| **微服务** | Go / Node.js | 轻量级，启动快 |

### 推荐技术栈组合

#### Node.js 生态
```typescript
// 全栈 TypeScript
{
  framework: 'NestJS',        // 企业级框架
  validation: 'Zod / class-validator',
  orm: 'Prisma / TypeORM',
  auth: 'Passport.js',
  queue: 'BullMQ',
  cache: 'Redis',
  testing: 'Jest + Supertest'
}
```

#### Python 生态
```python
# 现代异步栈
{
    framework: 'FastAPI',        # 现代异步框架
    validation: 'Pydantic',      # 类型验证
    orm: 'SQLAlchemy / Tortoise-ORM',
    auth: 'FastAPI Security',
    queue: 'Celery / RQ',
    cache: 'Redis / aiocache',
    testing: 'pytest + httpx'
}
```

#### Go 生态
```go
// 高性能服务
{
    framework: 'Gin / Fiber / Echo',
    validation: 'go-playground/validator',
    orm: 'GORM / sqlx',
    auth: 'golang-jwt/jwt',
    queue: 'Asynq',
    cache: 'go-redis',
    testing: 'testify'
}
```

---

## API 设计

### RESTful 设计原则

#### 资源命名

```http
# ✅ 好的 API 设计
GET    /api/users          # 获取用户列表
GET    /api/users/{id}     # 获取单个用户
POST   /api/users          # 创建用户
PUT    /api/users/{id}     # 更新用户（全量）
PATCH  /api/users/{id}     # 更新用户（部分）
DELETE /api/users/{id}     # 删除用户

# 嵌套资源
GET    /api/users/{id}/posts     # 获取用户的文章
POST   /api/users/{id}/posts     # 为用户创建文章

# ❌ 不好的设计
GET    /api/getUsers
GET    /api/user/{id}
POST   /api/createUser
```

#### HTTP 状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| **200** | OK | 成功 GET、PATCH |
| **201** | Created | 成功 POST |
| **204** | No Content | 成功 DELETE |
| **400** | Bad Request | 请求参数错误 |
| **401** | Unauthorized | 未认证 |
| **403** | Forbidden | 已认证但无权限 |
| **404** | Not Found | 资源不存在 |
| **422** | Unprocessable Entity | 验证失败 |
| **500** | Internal Server Error | 服务器错误 |

#### 统一响应格式

```typescript
// ✅ 统一的 API 响应格式
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
  };
}

// 成功响应
{
  "success": true,
  "data": { "id": 1, "name": "Alice" },
  "meta": { "total": 100 }
}

// 错误响应
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": { "email": "Invalid format" }
  }
}
```

---

## 数据库设计

### 数据建模原则

```sql
-- ✅ 好的表设计
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 索引
    CONSTRAINT idx_users_email UNIQUE (email),
    CONSTRAINT idx_users_username UNIQUE (username)
);

-- ✅ 添加适当的索引
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_email_lower ON users(LOWER(email));

-- ✅ 外键约束
CREATE TABLE posts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX idx_posts_user_id ON posts(user_id);
```

### 查询优化

```python
# ❌ N+1 查询问题
def get_users_with_posts():
    users = db.query("SELECT * FROM users")
    for user in users:
        user.posts = db.query(f"SELECT * FROM posts WHERE user_id = {user.id}")
    return users

# ✅ 使用 JOIN 优化
def get_users_with_posts():
    return db.query("""
        SELECT u.*, p.id as post_id, p.title, p.content
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        ORDER BY u.id, p.id
    """)
```

### 事务处理

```python
# ✅ 使用事务确保数据一致性
@db.transaction()
def transfer_money(from_user_id: int, to_user_id: int, amount: Decimal):
    # 检查余额
    from_user = db.query_one("SELECT * FROM users WHERE id = $1 FOR UPDATE", from_user_id)
    if from_user.balance < amount:
        raise InsufficientFundsError()

    # 扣款
    db.execute(
        "UPDATE users SET balance = balance - $1 WHERE id = $2",
        amount, from_user_id
    )

    # 加款
    db.execute(
        "UPDATE users SET balance = balance + $1 WHERE id = $2",
        amount, to_user_id
    )

    # 记录交易
    db.execute(
        "INSERT INTO transactions (from_user, to_user, amount) VALUES ($1, $2, $3)",
        from_user_id, to_user_id, amount
    )
```

---

## 认证与授权

### JWT 认证

```python
from datetime import datetime, timedelta
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

def create_access_token(user_id: int) -> str:
    """创建 JWT token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> int:
    """验证 JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid token")
```

### RBAC 授权

```python
from enum import Enum
from functools import wraps

class Permission(Enum):
    READ_USER = "user:read"
    WRITE_USER = "user:write"
    DELETE_USER = "user:delete"
    READ_POST = "post:read"
    WRITE_POST = "post:write"

class Role(Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

# 角色权限映射
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.READ_USER, Permission.WRITE_USER, Permission.DELETE_USER,
        Permission.READ_POST, Permission.WRITE_POST,
    ],
    Role.MODERATOR: [
        Permission.READ_USER, Permission.READ_POST, Permission.WRITE_POST,
    ],
    Role.USER: [
        Permission.READ_POST, Permission.WRITE_POST,
    ],
}

def require_permission(permission: Permission):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()  # 从上下文获取当前用户
            if permission not in ROLE_PERMISSIONS.get(user.role, []):
                raise ForbiddenError("Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用
@app.delete("/api/users/{user_id}")
@require_permission(Permission.DELETE_USER)
async def delete_user(user_id: int):
    await UserService.delete(user_id)
    return {"success": True}
```

---

## 性能优化

### 缓存策略

```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 1. 内存缓存
@lru_cache(maxsize=128)
def get_user_config(user_id: int):
    return db.query_one("SELECT * FROM user_config WHERE user_id = $1", user_id)

# 2. Redis 缓存
def get_user_with_cache(user_id: int):
    cache_key = f"user:{user_id}"

    # 尝试从缓存获取
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 缓存未命中，从数据库获取
    user = db.query_one("SELECT * FROM users WHERE id = $1", user_id)

    # 写入缓存（1小时过期）
    redis_client.setex(cache_key, 3600, json.dumps(user))

    return user

# 3. 缓存失效
def update_user(user_id: int, data: dict):
    user = db.update("users", user_id, data)

    # 删除相关缓存
    redis_client.delete(f"user:{user_id}")
    redis_client.delete(f"users:config:{user_id}")

    return user
```

### 连接池

```python
import asyncio
from asyncpg import create_pool

class Database:
    def __init__(self):
        self.pool = None

    async def init(self):
        """初始化连接池"""
        self.pool = await create_pool(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 5432)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            min_size=5,      # 最小连接数
            max_size=20,     # 最大连接数
            max_queries=50000,  # 每个连接最大查询数
            max_inactive_connection_lifetime=300.0,  # 不活跃连接生命周期
        )

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
```

---

## 可观测性

### 结构化日志

```python
import structlog

logger = structlog.get_logger()

async def process_order(order_id: int):
    logger.info("Processing order", order_id=order_id)

    try:
        order = await OrderService.get(order_id)
        logger.info("Order fetched", order_id=order_id, status=order.status)

        await PaymentService.charge(order.amount)
        logger.info("Payment successful", order_id=order_id, amount=order.amount)

    except PaymentError as e:
        logger.error(
            "Payment failed",
            order_id=order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

### 指标收集

```python
from prometheus_client import Counter, Histogram, generate_latest

# 定义指标
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# 中间件
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()

    response = await call_next(request)

    # 记录指标
    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

---

## 最佳实践清单

- [ ] API 遵循 RESTful 设计
- [ ] 统一的响应格式和错误处理
- [ ] 数据库设计规范，索引合理
- [ ] 使用事务确保数据一致性
- [ ] JWT + RBAC 认证授权
- [ ] 实现缓存策略
- [ ] 使用连接池
- [ ] 结构化日志
- [ ] 指标收集和监控
- [ ] API 文档（OpenAPI/Swagger）

---

## 相关参考

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [NestJS Documentation](https://docs.nestjs.com/)
- [Effective Go](https://go.dev/doc/effective_go)
