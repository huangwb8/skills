# 项目级问题挖掘技巧

本文档提供专门针对**项目级测试**的问题挖掘技巧，帮助发现跨模块、跨文件的系统性问题。

## 核心区别

**skill 级别测试** vs **项目 级别测试**：
- skill 级别：关注单个 SKILL.md、config.yaml 的质量
- 项目级别：关注**跨模块一致性**、**架构设计**、**依赖关系**、**配置管理**

## 使用原则

**⚠️ 批判性思维优先**：本文档的技巧分为两类，使用时**优先使用批判性分析框架**，再辅以技术检查技巧。

| 技巧类型 | 目的 | 优先级 |
|---------|------|--------|
| **批判性分析框架（技巧 0）** | 质疑设计合理性、评估架构价值、挖掘问题本质 | ⭐⭐⭐ **最高** |
| **技术检查技巧（技巧 1-8）** | 发现具体缺陷、验证一致性、检测安全隐患 | ⭐⭐ 辅助 |

**为什么批判性分析优先？**
- 技术检查容易发现"表面问题"（如配置不一致、日志格式不统一）
- 批判性分析能发现"本质问题"（如为什么需要两个配置？日志策略是否合理？）
- 项目级测试的核心价值在于**系统视角和架构洞察**，而非替代 linter

**必读（建议每轮 A 轮先过一遍）**：
- `references/CRITICAL_THINKING_GUIDE.md`：批判性思维框架（含“刁钻角度/边缘情况/恶意输入”）
- `references/CONSTRUCTIVE_SUGGESTION_GUIDELINES.md`：建设性建议标准（可执行/有证据/可验证）
- `references/ANTI_PATTERNS_LIBRARY.md`：反例库（快速识别常见反模式）

**独立评估提醒**：
- A 轮默认不查看历史 `plans/` 与 `tests/`，避免确认偏差；只基于当前项目状态做“重新审视”。

---

# 技巧 0: 批判性分析框架（系统视角）⭐️ 优先使用

**核心理念**：从"发现问题"升级为"质疑设计合理性"，挖掘问题的本质而非表象。

## 0.1 第一性原理思考

**适用场景**：评估项目是否偏离核心目标，识别"为了做而做"的功能。

### 检查维度

#### 核心目标对齐度分析
- 这个项目**真正要解决的问题**是什么？（从 CLAUDE.md/AGENTS.md 提取）
- 当前每个模块/功能是否**对核心目标有直接贡献**？
- 是否存在"看起来重要，但与核心目标无关"的功能？

**批判性问题示例**：
```
问题：项目目标是"简化 Agent Skills 开发"，但包含了一个复杂的依赖注入框架
批判性质疑：
- 这个依赖注入框架是否对"简化开发"有直接贡献？
- 还是增加了学习成本和复杂度？
- 能否用更简单的方案（如配置文件）替代？

影响：偏离核心目标，增加用户学习成本
优先级：P0（架构级偏离）
```

#### 功能必要性三问
对每个"功能/模块/配置项"，问：
1. **如果删除它，核心功能是否还能工作？** → 如果能，为什么存在？
2. **它解决的是真实痛点，还是假设的需求？** → 有证据表明用户需要吗？
3. **它的存在是否引入了新的复杂度？** → 收益是否大于成本？

**验证方法**：
```bash
# 1. 提取项目核心目标（从项目指令文件）
grep -A 5 "项目目标\|核心价值\|目的" CLAUDE.md AGENTS.md

# 2. 列出所有模块/功能
find . -name "*.py" -o -name "SKILL.md" | head -20

# 3. 对每个模块问：它对核心目标的贡献是什么？
# （需要人工评估，AI 无法自动化判断）
```

---

## 0.2 架构合理性质疑

**适用场景**：评估模块划分、依赖方向、抽象层次的合理性。

### 检查维度

#### 模块边界合理性
- 模块划分是否遵循**单一职责原则**？
- 是否存在"万能模块"（什么都做，职责不清）？
- 是否存在"碎片化模块"（一个功能拆成多个小模块）？

**批判性问题示例**：
```
问题：utils.py 包含了 15 个不相关的工具函数（从字符串处理到数据库连接）
批判性质疑：
- 这些函数真的属于"工具"吗？还是缺乏清晰的模块定位？
- 是否应该按领域拆分（如 string_utils.py, db_utils.py）？
- 还是有更高层的抽象可以统一它们？

影响：代码组织混乱，难以复用和测试
优先级：P1（模块组织问题）
```

#### 依赖方向合理性
- 依赖方向是否**符合分层架构**（如：业务层不应依赖基础设施层）？
- 是否存在**依赖倒置**（底层模块依赖上层模块）？
- 是否存在**循环依赖**（A → B → A）？

**批判性问题示例**：
```
问题：src/auth（认证模块）依赖 src/utils（工具模块），但 utils 又依赖 auth
批判性质疑：
- 为什么工具模块需要认证功能？是否职责混淆？
- 是否应该将认证相关功能提升为独立模块？
- 还是 utils 不应该包含业务逻辑？

影响：模块耦合度高，难以独立测试和复用
优先级：P0（架构级问题）
```

#### 抽象层次合理性
- 配置项数量是否反映**过度设计**？（如 50+ 配置项）
- 是否存在"为了扩展性而扩展性"的抽象？（如用户不需要的功能开关）
- 抽象层次是否**符合项目规模**？（小项目用企业级框架）

**批判性问题示例**：
```
问题：config.yaml 包含 67 个配置项，但项目只有 3 个核心功能
批判性质疑：
- 这些配置项是否真的都需要用户配置？
- 还是缺乏合理的默认值？
- 是否应该提供"预设模式"（如 --mode=simple）？

影响：用户配置负担重，学习成本高
优先级：P1（配置设计问题）
```

**验证方法**：
```bash
# 1. 生成依赖关系图（Python 项目）
pip install pydeps
pydeps src --max-bacon=3 --cluster --show-deps
# 检查是否有循环依赖、不合理的依赖方向

# 2. 统计配置项数量
grep -c "^[a-z_]*:" config.yaml
# 对比项目规模（如代码行数、模块数量）
```

---

## 0.3 价值导向的问题分类

**适用场景**：避免发现大量"噪音级问题"，聚焦高价值问题。

### 分类维度

#### 痛点级（P0-P1）- 用户核心功能受阻
- **特征**：不修复就无法使用，或严重影响体验
- **示例**：核心功能崩溃、安全漏洞、性能严重退化
- **判断标准**：用户是否会因为这个问题放弃使用项目？

#### 隐患级（P1-P2）- 当前可用但未来风险
- **特征**：不影响当前功能，但会累积技术债务
- **示例**：代码重复、模块耦合、缺少测试
- **判断标准**：3 个月内是否会引发更大的问题？

#### 噪音级（P2-P3）- 不影响功能的表面问题
- **特征**：只在代码审查时有意义，用户无感知
- **示例**：变量命名风格、注释格式、空行数量
- **判断标准**：修复它是否会让项目更好？还是只是为了"看起来专业"？

**⚠️ 使用建议**：
- **优先记录痛点级和隐患级问题**，噪音级问题可选
- **每轮至少有 1-2 个痛点级问题**，否则说明分析深度不够
- **对噪音级问题标注"可选优化"**，避免浪费资源

---

## 0.4 根本原因分析（5 Whys）

**适用场景**：挖掘问题的本质，而非修复表象。

### 分析方法

对每个 P0/P1 问题，连续问 5 次"为什么"，直到找到根本原因。

**示例**：
```
表面问题：配置超时值在两个文件中不一致（20秒 vs 30秒）

为什么 1：为什么会有两个超时值？
→ 因为 client.py 和 server.py 各自定义了超时

为什么 2：为什么各自定义，而不是共享配置？
→ 因为没有统一的配置管理模块

为什么 3：为什么没有统一配置管理？
→ 因为项目初期是快速原型，后来功能增长但没重构

为什么 4：为什么没重构？
→ 因为缺少配置管理的架构设计

为什么 5：为什么缺少架构设计？
→ 因为项目从"脚本"演进为"框架"时，没有重新评估架构

根本原因：**项目演进过程中缺少架构重构机制**
修复建议：
- P0：创建统一配置管理模块
- P1：建立"架构演进检查点"（如每新增一个模块，评估是否需要重构）
- 避免修复：只统一超时值（表象修复，未来还会出现类似问题）
```

**验证方法**：
- 在问题记录中增加"根本原因"字段
- 修复建议应针对根本原因，而非表象
- 如果无法回答 5 次"为什么"，说明问题理解不够深入

---

## 0.5 批判性分析检查清单

**每轮 A 轮必须回答的问题**：

### 系统视角
- [ ] 本轮发现的问题中，至少有 **1-2 个是架构级/设计级问题**（非表面问题）
- [ ] 本轮使用的批判性分析框架是：（如技巧 0.1 第一性原理、0.2 架构质疑）
- [ ] 本轮发现的问题中，**痛点级:隐患级:噪音级 的比例是否合理**（推荐 2:5:3）

### 问题深度
- [ ] 每个 P0/P1 问题都有**根本原因分析**（至少回答 3 次"为什么"）
- [ ] 每个 P0/P1 问题都有**批判性质疑**（质疑设计合理性，而非只描述现象）
- [ ] 修复建议是否针对**根本原因**，而非表象

### 价值判断
- [ ] 本轮发现的问题中，**是否至少有 1 个问题质疑了"为什么需要这个功能/模块/配置？"**
- [ ] 本轮发现的问题中，**是否避免了"为了修复而修复"的噪音问题？**
- [ ] 本轮是否对**项目架构合理性**提出了建设性质疑？

**如果无法勾选以上项目，说明本轮分析深度不足，需要重新使用批判性分析框架。**

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
