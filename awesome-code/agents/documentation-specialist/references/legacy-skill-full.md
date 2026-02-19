---
name: documentation-specialist
description: 文档专家。专注于技术文档编写、API 文档生成、README 优化和文档维护。提供清晰的文档结构、规范的格式和用户友好的内容。
metadata:
  short-description: 技术文档与 API 文档
  keywords:
    - 文档
    - API 文档
    - README
    - 技术写作
    - 文档生成
    - OpenAPI
    - Markdown
    - 文档维护
  category: 文档
  author: 社区最佳实践
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Documentation Specialist - 文档专家

## 核心理念

**优秀文档** 是项目成功的关键：

```
┌─────────────────────────────────────────────────────────┐
│  结构清晰 → 内容准确 → 格式统一 → 维护及时 → 用户友好  │
└─────────────────────────────────────────────────────────┘
```

**核心原则**：
- ✅ **用户视角**
- ✅ **简洁明了**
- ✅ **及时更新**
- ✅ **可操作性**
- ✅ **格式统一**

---

## 何时使用本技能

在以下场景时激活：

- 编写或更新 README
- 生成 API 文档
- 编写技术文档
- 优化现有文档
- 提到"文档"、"README"、"API 文档"

---

## 文档类型

### 1. README 文档

**项目门面**，必须包含：

```markdown
# 项目名称

简短描述项目功能（1-2 句话）

## 功能特性

- 特性 1
- 特性 2
- 特性 3

## 快速开始

### 前置要求

- Node.js >= 18
- Python >= 3.10

### 安装

\`\`\`bash
git clone https://github.com/user/repo.git
cd repo
npm install
\`\`\`

### 使用

\`\`\`bash
npm start
\`\`\`

## 文档

- [使用指南](docs/guide.md)
- [API 文档](docs/api.md)
- [贡献指南](CONTRIBUTING.md)

## 开发

\`\`\`bash
npm install
npm test
npm run build
\`\`\`

## 许可证

MIT License
```

### 2. API 文档

**OpenAPI/Swagger 规范**：

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
  description: |
    API 描述

    ## 认证
    所有 API 需要认证，使用 Bearer Token。

servers:
  - url: https://api.example.com/v1
    description: 生产环境
  - url: https://staging-api.example.com/v1
    description: 测试环境

security:
  - BearerAuth: []

paths:
  /users:
    get:
      summary: 获取用户列表
      tags:
        - Users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  meta:
                    type: object
                    properties:
                      page:
                        type: integer
                      limit:
                        type: integer
                      total:
                        type: integer

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      required:
        - id
        - email
      properties:
        id:
          type: integer
          example: 1
        email:
          type: string
          format: email
          example: user@example.com
```

### 3. 代码注释

**文档字符串**：

```python
def calculate_compound_interest(
    principal: float,
    rate: float,
    periods: int,
    compound_frequency: int = 1
) -> float:
    """
    计算复利。

    Args:
        principal: 本金金额
        rate: 年利率（小数形式，如 0.05 表示 5%）
        periods: 投资期数
        compound_frequency: 每年复利次数，默认为 1（年复利）

    Returns:
        最终金额

    Raises:
        ValueError: 如果 principal 为负数或 rate 不在合理范围内

    Examples:
        >>> calculate_compound_interest(1000, 0.05, 10)
        1628.89

        >>> calculate_compound_interest(1000, 0.05, 10, 12)
        1643.62
    """
    if principal < 0:
        raise ValueError("本金不能为负数")
    if not 0 <= rate <= 1:
        raise ValueError("利率必须在 0-1 之间")

    amount = principal * (1 + rate / compound_frequency) ** (periods * compound_frequency)
    return round(amount, 2)
```

---

## 文档结构

### 推荐目录结构

```
docs/
├── README.md              # 文档首页
├── getting-started.md     # 快速开始
├── guide/                 # 使用指南
│   ├── installation.md
│   ├── configuration.md
│   └── features.md
├── api/                   # API 文档
│   ├── overview.md
│   ├── users.md
│   └── posts.md
├── tutorials/             # 教程
│   ├── basic-tutorial.md
│   └── advanced-tutorial.md
├── reference/             # 参考手册
│   ├── cli.md
│   └── config.md
└── development/           # 开发文档
    ├── contributing.md
    ├── testing.md
    └── release.md
```

### 文档模板

```markdown
# 标题

简短描述（1-2 句话）

## 用途

描述什么时候使用这个功能/API。

## 前置条件

列出使用前需要满足的条件。

## 使用方法

### 基本用法

\`\`\`language
代码示例
\`\`\`

### 高级用法

\`\`\`language
复杂示例
\`\`\`

## 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| name | string | 是 | - | 名称 |
| age | integer | 否 | 0 | 年龄 |

## 返回值

描述返回值的类型和含义。

## 错误

| 错误代码 | 描述 | 解决方法 |
|----------|------|----------|
| 400 | 参数错误 | 检查参数格式 |
| 401 | 未认证 | 提供有效 token |

## 示例

### 示例 1：基本场景

\`\`\`language
\`\`\`

### 示例 2：边界情况

\`\`\`language
\`\`\`

## 注意事项

- 注意事项 1
- 注意事项 2

## 相关文档

- [相关功能 A](feature-a.md)
- [相关功能 B](feature-b.md)
```

---

## 文档生成工具

### Python (Sphinx)

```python
# conf.py
project = 'My Project'
copyright = '2024, Author'
author = 'Author'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

# autodoc 配置
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
```

```bash
# 生成文档
sphinx-quickstart docs
sphinx-apidoc -o docs src
make html
```

### JavaScript (JSDoc)

```javascript
/**
 * 用户类
 * @class
 * @classdesc 表示系统中的用户
 */
class User {
  /**
   * 创建用户实例
   * @param {Object} data - 用户数据
   * @param {string} data.name - 用户名
   * @param {string} data.email - 邮箱地址
   * @param {number} [data.age=0] - 年龄
   * @example
   * const user = new User({
   *   name: 'Alice',
   *   email: 'alice@example.com',
   *   age: 25
   * });
   */
  constructor(data) {
    this.name = data.name;
    this.email = data.email;
    this.age = data.age || 0;
  }

  /**
   * 获取用户全名
   * @returns {string} 全名
   */
  getFullName() {
    return this.name;
  }
}
```

```bash
# 生成文档
jsdoc src -d docs
```

---

## 文档最佳实践

### 1. 用户视角

**❌ 不好的做法**：
```markdown
## processUser 函数

这个函数处理用户数据，首先验证输入，然后保存到数据库。
```

**✅ 好的做法**：
```markdown
## 创建用户

将新用户添加到系统中。系统会自动验证邮箱格式和用户名唯一性。

### 前置条件
- 邮箱格式正确
- 用户名未被使用

### 使用方法
\`\`\`javascript
const user = await createUser({
  name: 'Alice',
  email: 'alice@example.com'
});
\`\`\`
```

### 2. 及时更新

**文档与代码同步**：

```python
# 在代码中添加文档更新提醒
# TODO: Update documentation when adding new parameters
def new_feature(param1, param2):
    pass
```

### 3. 可操作性

**提供可运行的示例**：

```markdown
## 快速开始

1. 克隆仓库：
\`\`\`bash
git clone https://github.com/user/repo.git
\`\`\`

2. 安装依赖：
\`\`\`bash
cd repo
npm install
\`\`\`

3. 运行示例：
\`\`\`bash
npm run example
\`\`\`

你应该看到输出：
\`\`\`
Hello, World!
\`\`\`
```

---

## 文档质量检查清单

- [ ] 标题清晰描述内容
- [ ] 提供快速开始指南
- [ ] 包含可运行的示例
- [ ] 参数/返回值完整描述
- [ ] 错误情况有说明
- [ ] 使用一致的格式
- [ ] 代码示例有注释
- [ ] 保持简洁但完整
- [ ] 及时更新
- [ ] 链接有效

---

## 相关参考

- [Google Developer Documentation Style Guide](https://developers.google.com/tech-writing/one)
- [Write the Docs](https://www.writethedocs.org/)
- [Documentation as Code](https://www.writethedocs.org/guide/docs-as-code/)
