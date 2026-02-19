---
name: security-specialist
description: 安全专家。专注于应用安全、威胁建模、安全合规和数据保护。提供安全审查、漏洞扫描、安全配置和合规检查。用于构建安全可靠的应用系统。
metadata:
  short-description: 应用安全与合规
  keywords:
    - 安全
    - 漏洞扫描
    - 威胁建模
    - OWASP
    - 数据保护
    - 安全合规
    - 渗透测试
    - 安全审计
  category: 安全
  author: 社区最佳实践
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Security Specialist - 安全专家

## 核心理念

**安全第一** 的开发实践：

```
┌─────────────────────────────────────────────────────────┐
│  威胁建模 → 安全设计 → 安全编码 → 漏洞扫描 → 合规检查  │
└─────────────────────────────────────────────────────────┘
```

**核心原则**：
- ✅ **纵深防御**
- ✅ **最小权限原则**
- ✅ **默认安全**
- ✅ **透明可审计**
- ✅ **持续监控**

---

## 何时使用本技能

在以下场景时激活：

- 需要安全审查
- 漏洞扫描或安全测试
- 威胁建模
- 安全合规检查
- 提到"安全"、"漏洞"、"渗透测试"
- 处理敏感数据

---

## OWASP Top 10 防护

### 1. 访问控制失效 (A01:2021)

```python
# ❌ 不安全的实现
def get_user_profile(user_id):
    user = get_current_user()
    # 任何用户都可以访问任何用户的数据
    return db.query(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ 安全的实现
def get_user_profile(requested_user_id):
    current_user = get_current_user()

    # 验证权限：只能访问自己的数据
    if current_user.id != requested_user_id and not current_user.is_admin:
        raise ForbiddenError("You don't have permission to access this resource")

    return db.query(
        "SELECT * FROM users WHERE id = %s",
        requested_user_id
    )

# ✅ 使用装饰器进行权限检查
def require_owner_or_admin(resource_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            resource_id = kwargs.get('resource_id')

            if not has_permission(user, resource_type, resource_id):
                raise ForbiddenError()
            return func(*args, **kwargs)
        return wrapper
    return decorator

@require_owner_or_admin('user_profile')
def get_user_profile(resource_id):
    return db.query("SELECT * FROM user_profiles WHERE id = %s", resource_id)
```

### 2. 加密失败 (A02:2021)

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os

# ✅ 密钥管理
class SecureConfig:
    def __init__(self):
        self.encryption_key = self._load_or_generate_key()

    def _load_or_generate_key(self):
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY not configured")
        return key.encode()

# ✅ 数据加密
def encrypt_sensitive_data(data: str, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_sensitive_data(encrypted_data: bytes, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()

# ✅ 密码哈希
import bcrypt

def hash_password(password: str) -> str:
    # bcrypt 自动加盐
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )
```

### 3. 注入 (A03:2021)

```python
# SQL 注入防护
# ❌ 危险
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# ✅ 安全：参数化查询
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))

# ✅ 安全：使用 ORM
user = User.objects.filter(id=user_id).first()

# 命令注入防护
import subprocess

# ❌ 危险
subprocess.run(f"ls {user_input}", shell=True)

# ✅ 安全：使用列表参数
subprocess.run(['ls', user_input], check=True)

# ✅ 安全：输入验证
import re

def sanitize_filename(filename: str) -> str:
    # 只允许字母、数字、下划线、点和连字符
    if not re.match(r'^[\w.-]+$', filename):
        raise ValueError("Invalid filename")
    return filename
```

### 4. 不安全设计 (A04:2021)

```python
# ✅ 安全设计原则

# 1. 最小权限原则
class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

def check_permission(user: User, required_permission: Permission):
    if required_permission not in user.permissions:
        raise ForbiddenError("Insufficient permissions")

# 2. 失败安全
def transfer_money(from_id: int, to_id: int, amount: Decimal):
    # 默认拒绝，明确允许
    if amount <= 0:
        raise InvalidAmountError()

    # 使用事务确保原子性
    with db.transaction():
        # ... 转账逻辑 ...

# 3. 深度防御
@require_permission(Permission.WRITE)
@validate_input(amount=PositiveDecimal)
@rate_limit(max_requests=10, window=60)
def create_payment(request: PaymentRequest):
    # 多层防护
    pass
```

### 5. 安全配置错误 (A05:2021)

```yaml
# ✅ 安全配置示例

# config.py
import os
from pydantic import BaseSettings, Field

class SecurityConfig(BaseSettings):
    # 强制 HTTPS
    force_https: bool = True

    # 安全头部
    secure_headers: bool = True

    # CORS 配置
    cors_origins: list[str] = Field(
        default=["https://example.com"],
        description="Allowed CORS origins"
    )

    # 会话配置
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"

    # 密码策略
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_special: bool = True

    # 速率限制
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = False
```

---

## 威胁建模

### STRIDE 方法

| 威胁类型 | 描述 | 检查问题 | 缓解措施 |
|---------|------|----------|----------|
| **Spoofing** | 伪装 | 攻击者能否伪装成合法用户？ | 强认证、令牌 |
| **Tampering** | 篡改 | 数据/代码能否被修改？ | 加密、签名 |
| **Repudiation** | 抵赖 | 用户能否否认操作？ | 审计日志 |
| **Information Disclosure** | 信息泄露 | 敏感信息是否暴露？ | 加密、访问控制 |
| **Denial of Service** | 拒绝服务 | 服务能否被破坏？ | 限流、冗余 |
| **Elevation of Privilege** | 权限提升 | 用户能否获得更高权限？ | 最小权限、角色分离 |

### 威胁建模流程

```python
from dataclasses import dataclass
from enum import Enum

class ThreatType(Enum):
    SPOOFING = "spoofing"
    TAMPERING = "tampering"
    REPUDIATION = "repudiation"
    INFO_DISCLOSURE = "information_disclosure"
    DOS = "denial_of_service"
    ELEVATION = "elevation_of_privilege"

@dataclass
class Threat:
    type: ThreatType
    description: str
    impact: str  # High/Medium/Low
    likelihood: str  # High/Medium/Low
    mitigation: str

def threat_model_login():
    """登录功能威胁建模"""
    return [
        Threat(
            type=ThreatType.SPOOFING,
            description="攻击者伪装成合法用户",
            impact="High",
            likelihood="High",
            mitigation="实施多因素认证（MFA）"
        ),
        Threat(
            type=ThreatType.INFO_DISCLOSURE,
            description="密码在传输中被窃取",
            impact="High",
            likelihood="Medium",
            mitigation="强制 HTTPS、使用 TLS 1.3"
        ),
        Threat(
            type=ThreatType.DOS,
            description="暴力破解攻击",
            impact="Medium",
            likelihood="High",
            mitigation="实施速率限制和账户锁定"
        ),
        Threat(
            type=ThreatType.ELEVATION,
            description="会话劫持",
            impact="High",
            likelihood="Medium",
            mitigation="短期会话、IP 绑定、安全 Cookie"
        ),
    ]
```

---

## 安全扫描工具

### 依赖漏洞扫描

```bash
# Python
pip install safety
safety check

# JavaScript
npm audit
npm audit fix

# 自动化扫描
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 0 * * 0'  # 每周日

jobs:
  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Safety Check
        run: |
          pip install safety
          safety check --json > safety-report.json

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r . -f json > bandit-report.json

      - name: Upload Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            safety-report.json
            bandit-report.json
```

### 静态代码分析

```python
# .bandit
# Bandit 配置文件
exclude_dirs = ['/tests', '/venv']
tests = ['B201', 'B301', 'B401', 'B501', 'B601']
```

### 容器镜像扫描

```bash
# Trivy 扫描
trivy image myapp:latest

# 集成到 CI/CD
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ secrets.REGISTRY_URL }}/myapp:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'

- name: Upload Trivy results
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: 'trivy-results.sarif'
```

---

## 安全头部配置

### HTTP 安全头部

```python
# security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)

        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"

        # 防止 MIME 类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 启用浏览器 XSS 过滤器
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 严格传输安全
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 内容安全策略
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # Referrer 策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

# 使用
app.add_middleware(SecurityHeadersMiddleware)
```

---

## 敏感数据处理

### 数据分类

```python
from enum import Enum
from dataclasses import dataclass

class DataClassification(Enum):
    PUBLIC = "public"           # 可公开
    INTERNAL = "internal"       # 仅内部
    CONFIDENTIAL = "confidential"  # 机密
    RESTRICTED = "restricted"   # 高度机密

@dataclass
class UserData:
    user_id: int
    classification: DataClassification
    email: str
    phone: str | None = None
    ssn: str | None = None  # 社会安全号

    def mask_sensitive_fields(self):
        """脱敏敏感字段"""
        if self.phone:
            self.phone = self.phone[:3] + "****" + self.phone[-2:]
        if self.ssn:
            self.ssn = "***-**-" + self.ssn[-4:]
```

### 日志脱敏

```python
import logging
from typing import Any

class SensitiveDataFilter(logging.Filter):
    """过滤日志中的敏感数据"""

    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[\w]+["\']?', 'password=***'),
        (r'token["\']?\s*[:=]\s*["\']?[\w.-]+["\']?', 'token=***'),
        (r'api_key["\']?\s*[:=]\s*["\']?[\w]+["\']?', 'api_key=***'),
        (r'ssn["\']?\s*[:=]\s*["\']?\d{3}[-]?\d{2}[-]?\d{4}["\']?', 'ssn=***-**-****'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        record.msg = msg
        return True
```

---

## 安全检查清单

- [ ] 所有用户输入已验证
- [ ] SQL 查询使用参数化
- [ ] 敏感数据已加密
- [ ] 使用强密码策略
- [ ] 实施 HTTPS/TLS
- [ ] 安全头部已配置
- [ ] 访问控制已实现
- [ ] 审计日志已启用
- [ ] 依赖无已知漏洞
- [ ] 密钥管理安全
- [ ] 错误处理不泄露信息
- [ ] 速率限制已配置

---

## 相关参考

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
