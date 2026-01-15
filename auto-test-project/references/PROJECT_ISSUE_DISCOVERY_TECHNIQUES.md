# 项目级问题挖掘技巧

本文档提供专门针对**项目级测试**的问题挖掘技巧，帮助发现跨模块、跨文件的系统性问题。

## 核心区别

**skill 级别测试** vs **项目 级别测试**：
- skill 级别：关注单个 SKILL.md、config.yaml 的质量
- 项目级别：关注**跨模块一致性**、**架构设计**、**依赖关系**、**配置管理**

---

## 技巧 1: 跨模块一致性检查

**适用场景**：验证多个模块是否遵循相同的规范

**检查维度**：

### 1.1 接口一致性
- 不同模块的 API 签名是否一致？
- 错误码定义是否统一？
- 返回值格式是否一致？

**示例问题**：
```
问题：模块 A 使用 `Result<T>` 返回类型，模块 B 使用 `Tuple[bool, T]`
影响：调用方需要处理两种不同的返回模式
优先级：P1
```

**验证方法**：
```bash
# 搜索函数签名模式
grep -r "def.*-> " src/ --include="*.py" | sort | uniq -c

# 检查返回类型定义
grep -r "class.*Result\|class.*Response" src/ --include="*.py"
```

### 1.2 配置一致性
- 相同的配置项在不同模块中是否有不同的值？
- 配置项命名是否统一（camelCase vs snake_case）？

**示例问题**：
```
问题：`api.timeout` 在 client.py 中是 20 秒（硬编码），在 server.py 中是 30 秒（配置读取）
影响：超时行为不一致
优先级：P0
```

**验证方法**：
```bash
# 搜索硬编码的超时值
grep -r "timeout=\\|timeout :" src/ --include="*.py"

# 对比配置文件
grep -r "timeout" config.yaml
```

### 1.3 日志格式一致性
- 日志级别使用是否统一（INFO vs info）？
- 日志格式是否统一（JSON vs 文本）？
- 日志位置是否统一（文件 vs 控制台）？

**验证方法**：
```bash
# 搜索不同的日志调用模式
grep -r "logger\\.\\|logging\\." src/ --include="*.py" | grep -oE "logger\\.[a-z]+" | sort | uniq -c
```

---

## 技巧 2: 依赖关系分析

**适用场景**：发现模块间的耦合问题和依赖风险

### 2.1 循环依赖检测
- 模块 A 是否导入模块 B，同时 B 也导入 A？
- 间接循环依赖（A → B → C → A）？

**示例问题**：
```
问题：src/api/__init__.py 导入 src/auth，src/auth/__init__.py 导入 src/utils，src/utils/__init__.py 导入 src/api
影响：模块耦合度高，难以独立测试
优先级：P1
```

**验证方法**：
```bash
# 使用 pydeps 生成依赖图
pip install pydeps
pydeps src --max-bacon=3 --cluster --dot
# 检查生成的图中是否有循环箭头

# 或者使用模块分析工具
python -c "
import sys
sys.path.insert(0, 'src')
import importlib
import pkgutil

def find_dependencies(module_name, visited=None):
    if visited is None:
        visited = set()
    if module_name in visited:
        return []
    visited.add(module_name)

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return []

    deps = []
    for importer, modname, ispkg in pkgutil.walk_packages(module.__path__ if hasattr(module, '__path__') else [], prefix=module.__name__ + '.'):
        if modname not in visited:
            deps.append(modname)
            deps.extend(find_dependencies(modname, visited))
    return deps

# 检查每个模块的依赖
for module in ['api', 'auth', 'utils']:
    print(f'{module}: {find_dependencies(module)}')
"
```

### 2.2 第三方依赖冲突检测
- 不同模块依赖的同一库的版本是否冲突？
- 是否有重复依赖（相同功能的不同库）？

**示例问题**：
```
问题：requests==2.28.0 要求 urllib3<1.27，但 requirements.txt 中 urllib3==2.0.0
影响：安装失败或运行时不确定
优先级：P0
```

**验证方法**：
```bash
# 使用 pip-check 检查依赖冲突
pip install pip-check
pip-check

# 或使用 pip-audit 检查安全漏洞
pip install pip-audit
pip-audit
```

### 2.3 未使用的依赖检测
- requirements.txt 中是否有从未导入的库？
- 是否有被导入但未使用的功能？

**验证方法**：
```bash
# 使用 pip-autoremove 检查未使用的依赖
pip install pip-autoremove
pip-autoremove --dry-run
```

---

## 技巧 3: 配置管理审查

**适用场景**：发现配置文件相关的问题

### 3.1 敏感信息检查
- 配置文件中是否包含硬编码的密钥、密码？
- 是否有敏感信息泄露到日志？

**示例问题**：
```
问题：config.yaml 中包含 `database.password: "password123"`
影响：严重安全风险
优先级：P0
```

**验证方法**：
```bash
# 搜索硬编码密钥
grep -ri "password.*=\\|secret.*=\\|api.*key.*=" config/ src/ --include="*.yaml" --include="*.py" -i

# 搜索常见的密钥模式
grep -r "sk-.*\\|AKIA.*\\|Bearer.*" config/ src/ --include="*.yaml" --include="*.py"
```

### 3.2 配置项分类检查
- 配置文件是否按功能模块分组？
- 配置项命名是否具有描述性？

**验证方法**：
```bash
# 检查配置文件是否有清晰的章节
grep -E "^#+ .*:" config.yaml

# 检查配置项的嵌套层级
python -c "
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)

def print_structure(obj, prefix='', max_depth=3):
    if isinstance(obj, dict) and max_depth > 0:
        for key, value in obj.items():
            print(f'{prefix}{key}: {type(value).__name__}')
            if isinstance(value, dict):
                print_structure(value, prefix + '  ', max_depth - 1)
            elif isinstance(value, list) and value:
                print(f'{prefix}  - List of {type(value[0]).__name__}')

print_structure(config)
"
```

### 3.3 环境特定配置检查
- 是否有开发/生产环境的配置混合？
- 是否有环境变量未正确使用？

**验证方法**：
```bash
# 搜索环境相关的配置
grep -r "dev\\|prod\\|test\\|staging" config.yaml

# 检查是否有环境变量但未定义
grep -r "os\\.getenv\\|os\\.environ" src/ --include="*.py" | grep -oE 'os\\.getenv\\("([^"]+)"' | sort | uniq
```

---

## 技巧 4: 文档同步检查

**适用场景**：发现文档与代码不一致的问题

### 4.1 README 与代码一致性
- README 中的安装命令是否有效？
- README 中的示例代码是否可运行？

**示例问题**：
```
问题：README.md 中说 `pip install -r requirements-dev.txt`，但实际文件名是 requirements.txt
影响：新用户无法按文档成功安装
优先级：P1
```

**验证方法**：
```bash
# 测试 README 中的安装命令
pip install -r $(grep -oE "requirements[^ ]+" README.md | head -1)

# 测试示例代码
python -c "$(grep -A 10 "```python" README.md | grep -v "```" | head -5)"
```

### 4.2 API 文档与实际签名对比
- API 文档中的参数列表与实际函数签名是否一致？
- 返回值类型是否匹配？

**验证方法**：
```bash
# 提取 API 文档中的函数签名
grep -oE "[a-z_]+\\([^)]*\\)" docs/api.md

# 对比实际代码中的函数签名
grep -oE "^def [a-z_]+\\([^)]*\\)" src/api/endpoints.py

# 使用工具自动化检查
pip install interrogate
interrogate src/api --verbose
```

### 4.3 变更日志同步
- CHANGELOG.md 是否记录了最近的变更？
- 版本号是否在所有地方同步？

**验证方法**：
```bash
# 检查最近一次提交与 CHANGELOG 的日期差异
LATEST_CHANGE=$(grep -E "^## \\[" CHANGELOG.md | head -1 | grep -oE "[0-9-]+")
LATEST_COMMIT=$(git log -1 --format=%cs | head -1)
echo "CHANGELOG: $LATEST_CHANGE"
echo "Commit: $LATEST_COMMIT"
```

---

## 技巧 5: 边缘情况压力测试

**适用场景**：发现极端情况下的处理缺陷

### 5.1 空配置/缺失配置处理
- 配置文件为空时是否使用默认值？
- 配置文件格式错误时是否有友好提示？

**示例问题**：
```
问题：config.yaml 为空时，程序直接崩溃而非使用默认值
影响：用户误删配置后无法启动
优先级：P2
```

**验证方法**：
```bash
# 备份配置
cp config.yaml config.yaml.bak

# 测试空配置
echo "" > config.yaml
python -m src.main 2>&1 | head -20

# 测试格式错误
echo "invalid: yaml: content: [" > config.yaml
python -m src.main 2>&1 | head -20

# 恢复配置
mv config.yaml.bak config.yaml
```

### 5.2 资源耗尽场景
- 内存耗尽时的处理？
- 磁盘空间不足时的处理？
- 网络超时的处理？

**验证方法**：
```bash
# 使用 ulimit 限制内存
ulimit -v 1048576  # 限制为 1GB
python -m src.main

# 使用 fallocate 模拟磁盘满
dd if=/dev/zero of=disk_hog.img bs=1G seek=10G 2>&1 | head -1
```

### 5.3 并发访问场景
- 多个请求同时到达时的处理？
- 数据库连接池耗尽时的处理？

**验证方法**：
```bash
# 使用 wrk 进行压力测试
pip install wrk
wrk -t10 -c100 -d30s http://localhost:8000/api/endpoint
```

---

## 技巧 6: 代码"模式匹配"

**适用场景**：发现代码风格和不一致的模式

### 6.1 异常处理模式
- try-except 块是否统一使用日志记录？
- 是否有"吞掉异常"的情况？

**示例问题**：
```
问题：client.py 中使用 `except Exception: pass`，而 server.py 中使用 `except Exception: raise`
影响：调试困难，错误处理不一致
优先级：P2
```

**验证方法**：
```bash
# 搜索所有 try-except 块
grep -r "try:" src/ --include="*.py" -A 2 | grep -E "(except|raise|return)"

# 搜索吞掉异常
grep -r "except.*:" src/ --include="*.py" -A 1 | grep "pass"
```

### 6.2 资源清理模式
- 文件句柄是否正确关闭？
- 数据库连接是否正确释放？
- 是否使用 context managers？

**验证方法**：
```bash
# 搜索文件操作但没有使用 with
grep -r "open(" src/ --include="*.py" | grep -v "with open"

# 搜索数据库连接但没有使用 context manager
grep -r "connect(" src/ --include="*.py" | grep -v "with"
```

### 6.3 导入顺序模式
- 导入语句是否按标准顺序（stdlib、第三方、本地）？
- 是否有未使用的导入？

**验证方法**：
```bash
# 使用 isort 检查导入顺序
pip install isort
isort --check-only --diff src/

# 使用 pyflakes 检查未使用的导入
pip install pyflakes
pyflakes src/
```

---

## 技巧 7: 安全性扫描

**适用场景**：发现潜在的安全漏洞

### 7.1 SQL 注入风险
- 是否有字符串拼接的 SQL 查询？
- 是否有用户输入直接拼接到查询中？

**验证方法**：
```bash
# 搜索字符串拼接的 SQL
grep -r "SELECT.*FROM.*+\\|UPDATE.*SET.*+" src/ --include="*.py" -i

# 使用 bandit 进行安全扫描
pip install bandit
bandit -r src/
```

### 7.2 命令注入风险
- 是否有用户输入直接传递到 subprocess？
- 是否有 shell=True 的调用？

**验证方法**：
```bash
# 搜索 subprocess 调用
grep -r "subprocess\\.\\|os\\.system" src/ --include="*.py"

# 搜索 shell=True
grep -r "shell=True" src/ --include="*.py"
```

### 7.3 路径遍历风险
- 是否有用户输入直接用于文件路径？
- 是否有 `..` 路径的检查？

**验证方法**：
```bash
# 搜索路径操作
grep -r "open(.*+\\|Path(.*+\\|os\\.path\\.join" src/ --include="*.py"

# 使用 semgrep 检查路径遍历
pip install semgrep
semgrep --config=auto --lang=python --pattern="path_traversal" src/
```

---

## 技巧 8: 性能分析

**适用场景**：发现性能瓶颈

### 8.1 N+1 查询问题
- 是否有循环中的数据库查询？
- 是否有重复的查询？

**验证方法**：
```bash
# 使用 Django Debug Toolbar 或类似工具
# 或手动检查循环中的查询
grep -r "for.*in.*:" src/ --include="*.py" -A 5 | grep -E "\\.filter\\|\\.get\\|\\.all"
```

### 8.2 内存泄漏风险
- 是否有未释放的资源？
- 是否有全局列表不断增长？

**验证方法**：
```bash
# 使用 memory_profiler
pip install memory_profiler
python -m memory_profiler src/main.py
```

### 8.3 算法复杂度问题
- 是否有 O(n²) 的嵌套循环？
- 是否有不必要的大数据集处理？

**验证方法**：
```bash
# 使用 vprof 进行性能分析
pip install vprof
vprof src/main.py
```

---

## 使用建议

### 组合使用技巧

**每轮推荐使用 3-5 个技巧组合**，例如：

**第一轮**（基础检查）：
1. 跨模块一致性检查
2. 配置管理审查
3. 文档同步检查

**第二轮**（深度分析）：
4. 依赖关系分析
5. 代码"模式匹配"
6. 边缘情况压力测试

**第三轮**（专项检查）：
7. 安全性扫描
8. 性能分析

### 记录问题发现技巧

在 `plans/vYYYYMMDDHHMM.md` 中，为每个问题标注使用的挖掘技巧：

```markdown
#### P0-1: 敏感信息硬编码

**发现技巧**：技巧 3.1（敏感信息检查）

**位置**: `config.yaml:45`

...
```

这样可以追踪哪些技巧最有效，调整后续轮次的策略。
