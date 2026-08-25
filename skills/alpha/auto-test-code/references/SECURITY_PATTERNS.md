# 安全漏洞模式库

**用途**：快速识别常见安全漏洞。

完整分类审查口径见 `SECURITY_TAXONOMY.md`。本文件提供快速模式库；每轮安全维度不能只停留在本文件的 11 个模式，还必须覆盖 CWE/OWASP/STRIDE/七大王国/CVSS、供应链、配置运维、密码学、认证授权、DoS 与内存安全。

---

## 注入类漏洞

### 1. SQL 注入（SQL Injection）

**特征**：用户输入直接拼接到 SQL 语句

**危险度**：P0（可能导致数据泄露/篡改）

**示例**：
```python
# 危险
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)

# 安全
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
```

**检测方法**：
- 搜索字符串拼接的 SQL 查询
- 检查是否使用参数化查询

---

### 2. 命令注入（Command Injection）

**特征**：用户输入直接用于系统命令

**危险度**：P0（可能导致系统被完全控制）

**示例**：
```python
# 危险
def convert_file(filename):
    os.system(f"convert {filename} output.pdf")

# 安全
def convert_file(filename):
    # 验证文件名
    if not re.match(r'^[\w.-]+$', filename):
        raise ValueError("Invalid filename")
    subprocess.run(["convert", filename, "output.pdf"])
```

**检测方法**：
- 搜索 os.system()、subprocess.call(shell=True)
- 检查输入验证

---

### 3. 路径遍历（Path Traversal）

**特征**：用户输入用于文件路径，未做验证

**危险度**：P0（可能访问任意文件）

**示例**：
```python
# 危险
def read_file(filename):
    path = f"./data/{filename}"
    return open(path).read()

# 安全
def read_file(filename):
    # 规范化路径
    path = os.path.normpath(f"./data/{filename}")
    base_dir = os.path.realpath("./data")
    real_path = os.path.realpath(path)

    # 验证路径在允许范围内
    if not real_path.startswith(base_dir):
        raise ValueError("Invalid path")

    return open(real_path).read()
```

**检测方法**：
- 搜索 open()、read() 使用用户输入
- 检查路径验证逻辑

---

### 4. XSS（跨站脚本）

**特征**：用户输入直接输出到 HTML

**危险度**：P0（可能导致用户会话劫持）

**示例**：
```python
# 危险
def render_page(username):
    return f"<h1>Welcome {username}</h1>"

# 安全
def render_page(username):
    from html import escape
    return f"<h1>Welcome {escape(username)}</h1>"
```

---

## 认证与授权

### 5. 硬编码凭证

**特征**：密钥/密码硬编码在代码中

**危险度**：P0（凭证泄露）

**示例**：
```python
# 危险
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

# 安全
API_KEY = os.getenv("API_KEY")
DB_PASSWORD = os.getenv("DB_PASSWORD")
```

**检测方法**：
- 搜索 "password"、"api_key"、"secret"
- 使用 secrets 扫描工具

---

### 6. 弱密码哈希

**特征**：使用 MD5/SHA1 哈希密码

**危险度**：P1（密码容易被破解）

**示例**：
```python
# 危险
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# 安全
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

---

### 7. 会话固定

**特征**：登录后未更新会话 ID

**危险度**：P1（会话劫持）

**示例**：
```python
# 危险
def login(username, password):
    if authenticate(username, password):
        session['user_id'] = user.id
        # 未更新会话 ID
```

---

## 数据安全

### 8. 敏感信息泄露

**特征**：错误消息/日志包含敏感信息

**危险度**：P1（信息泄露）

**示例**：
```python
# 危险
try:
    result = process payment(card_data)
except Exception as e:
    logging.error(f"Payment failed: {e}\nData: {card_data}")

# 安全
try:
    result = process_payment(card_data)
except Exception as e:
    logging.error(f"Payment failed: {e}")
    # 不记录敏感数据
```

---

### 9. 不安全的随机数

**特征**：使用伪随机数生成器生成安全 token

**危险度**：P0（token 可预测）

**示例**：
```python
# 危险
import random
token = random.randint(0, 1000000)

# 安全
import secrets
token = secrets.randbelow(1000000)
```

---

## 加密问题

### 10. 不安全的加密算法

**特征**：使用 DES/RC4/ECB 模式

**危险度**：P0（数据可被解密）

**示例**：
```python
# 危险
from Crypto.Cipher import DES
cipher = DES.new(key, DES.MODE_ECB)

# 安全
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_GCM)
```

---

## 并发安全

### 11. 竞态条件

**特征**：检查-使用模式未原子化

**危险度**：P0（可能导致数据不一致）

**示例**：
```python
# 危险
if not os.path.exists(filename):
    with open(filename, 'w') as f:  # 竞态窗口
        f.write(data)

# 安全
fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
with os.fdopen(fd, 'w') as f:
    f.write(data)
```

---

## 检查清单

在代码审查时，快速检查：

- [ ] 是否有 SQL 注入风险？（字符串拼接 SQL）
- [ ] 是否有命令注入风险？（os.system 使用用户输入）
- [ ] 是否有路径遍历风险？（文件路径未验证）
- [ ] 是否有 XSS 风险？（用户输入未转义）
- [ ] 是否有硬编码凭证？（密钥/密码在代码中）
- [ ] 是否使用弱加密？（MD5/SHA1/DES）
- [ ] 是否使用不安全的随机数？（random 模块）
- [ ] 错误消息是否泄露敏感信息？
- [ ] 是否有竞态条件？（检查-使用模式）
- [ ] 是否有认证/授权缺失或 IDOR？（对象级/功能级权限）
- [ ] 是否有 SSRF？（服务端请求内网/云元数据/文件协议）
- [ ] 是否有不可信反序列化、模板注入、XXE、NoSQL/LDAP/XPath 注入？
- [ ] 是否有供应链风险？（未锁版本、CI/CD 注入、依赖混淆、未验证下载/镜像）
- [ ] 是否有配置风险？（调试模式、CORS 任意源、TLS/安全头缺失、云资源公开）
- [ ] 是否有 DoS 风险？（ReDoS、XML/解压炸弹、无限队列/递归/连接、无速率限制）
- [ ] 是否有内存安全风险？（越界读写、UAF、双重释放、整数溢出、格式字符串）
