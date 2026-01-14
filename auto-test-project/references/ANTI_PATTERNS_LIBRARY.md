# 技能开发反例库（项目级）

**文档版本**：v1.0.0
**创建时间**：2026-01-14
**用途**：为 auto-test-project 提供常见反例库，用于快速识别问题

---

## 使用说明

本文档按照"项目级七大质量原则"分类，每类包含常见反例。

**使用方法**：
1. 在检查项目时，对比本文档中的反例
2. 发现相似模式时，记录为问题
3. 参考"正确做法"给出修复建议

**项目级特点**：
- 反例涉及跨模块场景
- 强调项目级一致性
- 关注模块间接口和依赖关系

---

## 1. 硬编码/AI功能规划反例

### 反例 1: 让 AI "手动创建多个目录"

**错误表现**：
```markdown
## 执行步骤
1. 创建目录：`module_a/output/reports/{timestamp}/`
2. 创建目录：`module_b/output/logs/{timestamp}/`
3. 创建目录：`module_c/output/data/{timestamp}/`
```

**问题**：这是确定性操作，应脚本化

**涉及模块**：module_a、module_b、module_c

**正确做法**：
```markdown
## 执行步骤
1. 运行 `scripts/init_project_dirs.py` 自动创建所有模块的输出目录
```

---

### 反例 2: 配置值硬编码在文档中

**错误表现**：
```markdown
## 配置说明
最大重试次数：3次
超时时间：30秒
日志级别：INFO
```

**问题**：应移至项目级 config.yaml 或各模块 config.yaml

**涉及模块**：所有模块

**正确做法**：
```yaml
# project_config.yaml
retries:
  max: 3
timeout: 30  # 秒
logging:
  level: INFO
```

```markdown
## 配置说明
详见 project_config.yaml 中的 `retries.max`、`timeout` 和 `logging.level` 配置项
```

---

### 反例 3: 让 AI 每次编写相同的集成代码

**错误表现**：
```markdown
## 步骤 2
用 Python 读取 CSV 文件并验证格式：
```python
import csv
import os

def validate_csv(path):
    # ... 50 行验证逻辑
```

**问题**：AI 每次都要"记住"这段代码，且每个模块都要复制

**涉及模块**：module_a、module_b、module_c

**正确做法**：
```markdown
## 步骤 2
运行 `scripts/validate_csv.py --input {file}` 自动验证
```

---

### 反例 4: 过度配置化

**错误表现**：
```yaml
# config.yaml
file_formats:
  csv:
    extension: ".csv"
    delimiter: ","
    encoding: "utf-8"
  json:
    extension: ".json"
    encoding: "utf-8"
```

**问题**：这些是标准定义，不需要配置

**涉及模块**：所有使用文件格式的模块

**正确做法**：
```python
# shared/formats.py
CSV_DELIMITER = ","  # CSV 标准
CSV_ENCODING = "utf-8"  # 现代标准
JSON_ENCODING = "utf-8"  # 标准
```

---

## 2. 冗余残留错误检查反例

### 反例 1: 跨模块残留引用

**错误表现**：
```markdown
# CLAUDE.md
详见 module_a/references/OLD_API.md
```
```bash
# 实际情况
$ ls module_a/references/OLD_API.md
ls: cannot access: No such file or directory
```

**问题**：引用已删除的文件

**涉及模块**：项目文档、module_a

**正确做法**：
```markdown
# CLAUDE.md
详见 module_a/references/NEW_API.md
```

---

### 反例 2: 跨模块重复段落

**错误表现**：
```markdown
# module_a/README.md
## 输入格式
输入必须是 CSV 格式，文件大小不超过 10MB...
```
```markdown
# module_b/README.md
## 输入格式
输入必须是 CSV 格式，文件大小不超过 10MB...
```

**问题**：内容重复，应合并到项目文档或共享模块

**涉及模块**：module_a、module_b

**正确做法**：
```markdown
# CLAUDE.md
## 共享输入格式规范
所有模块的输入必须是 CSV 格式，文件大小不超过 10MB...
```

---

### 反例 3: 僵尸模块

**错误表现**：
```
module_deprecated/           # 标记为"已废弃"，但未说明替代方案
scripts/backup_old.py        # 标记为"备份"，但未说明用途
references/unused_guide.md   # 从未被引用
```

**问题**：无用的模块/文件占用空间，污染代码库

**涉及模块**：所有模块（影响项目结构）

**正确做法**：
```bash
# 使用 Grep 搜索引用
grep -r "module_deprecated" .
# 如果无结果，删除模块
rm -rf module_deprecated
```

---

### 反例 4: 跨模块配置重复定义

**错误表现**：
```yaml
# module_a/config.yaml
output:
  directory: "./output"
  format: "json"
```
```yaml
# module_b/config.yaml
output:
  directory: "./output"
  format: "json"
```
```yaml
# module_c/config.yaml
output:
  directory: "./output"
  format: "json"
```

**问题**：所有模块的输出配置完全相同，应提升到项目级

**涉及模块**：module_a、module_b、module_c

**正确做法**：
```yaml
# project_config.yaml
output:
  directory: "./output"
  format: "json"
```
```yaml
# module_a/config.yaml
# 输出配置继承项目级配置
# 如需自定义，在此覆盖
```

---

## 3. 安全性检查反例

### 反例 1: 跨模块路径遍历漏洞

**错误表现**：
```python
# module_a/scripts/validator.py
def validate_path(path):
    if path.startswith("../"):
        raise ValueError("Invalid path")
```
```python
# module_b/scripts/reader.py
# 直接使用用户输入，未调用 validate_path
with open(user_input, 'r') as f:
    ...
```

**问题**：模块 B 绕过了模块 A 的验证

**涉及模块**：module_a（验证）、module_b（使用）

**正确做法**：
```python
# shared/security.py
def validate_path(path, base_dir):
    import os
    resolved = os.path.realpath(path)
    base = os.path.realpath(base_dir)
    if not resolved.startswith(base):
        raise ValueError("Path outside base directory")
    return resolved
```
```python
# module_a/scripts/validator.py
from shared.security import validate_path
```
```python
# module_b/scripts/reader.py
from shared.security import validate_path
safe_path = validate_path(user_input, "./data")
```

---

### 反例 2: 跨模块敏感信息泄露

**错误表现**：
```python
# module_a/scripts/api.py
except Exception as e:
    print(f"错误：API 调用失败，URL: {api_url}, 详情：{str(e)}")
    # api_url 可能包含敏感参数
```

**问题**：泄露敏感信息

**涉及模块**：module_a

**正确做法**：
```python
# shared/logger.py
import logging
logger = logging.getLogger(__name__)

def log_error(message, exc_info=False):
    logger.error(message, exc_info=exc_info)
```
```python
# module_a/scripts/api.py
from shared.logger import log_error
except Exception as e:
    log_error("API 调用失败", exc_info=True)
    # 不记录具体 URL，使用日志系统
```

---

### 反例 3: 跨模块命令注入风险

**错误表现**：
```python
# module_a/scripts/converter.py
os.system(f"convert {user_input} output.pdf")
```
```python
# module_b/scripts/processor.py
os.system(f"process {user_input} --output {output}")
```

**问题**：两个模块都有命令注入风险

**涉及模块**：module_a、module_b

**正确做法**：
```python
# shared/process.py
import subprocess

def run_command(cmd, args):
    """安全执行命令"""
    subprocess.run([cmd] + args, check=True)
```
```python
# module_a/scripts/converter.py
from shared.process import run_command
run_command("convert", [user_input, "output.pdf"])
```

---

## 4. 过度设计检查反例

### 反例 1: 项目级为未来预留功能

**错误表现**：
```yaml
# project_config.yaml
supported_formats:
  pdf:
    enabled: true
  docx:
    enabled: false  # 未来可能支持
  html:
    enabled: false  # 未来可能支持
  markdown:
    enabled: false  # 未来可能支持
```

**问题**：当前只支持 PDF，其他格式不应硬编码

**涉及模块**：所有模块

**正确做法**：
```yaml
# project_config.yaml
supported_formats:
  - pdf  # 唯一支持的格式
# 未来需要时再添加
```

---

### 反例 2: 过度抽象的共享模块

**错误表现**：
```python
# shared/formatters.py
class OutputFormatFactory:
    """输出格式工厂（当前只有一种格式）"""
    def create_formatter(self, format_type):
        if format_type == "pdf":
            return PDFFormatter()
        # 未来扩展点...

class PDFFormatter(AbstractFormatter):
    def format(self, data):
        # 实际上就是直接调用一个函数
        return convert_to_pdf(data)
```

**问题**：只有一种格式时，工厂和抽象层都是不必要的

**涉及模块**：所有使用格式化的模块

**正确做法**：
```python
# shared/formatters.py
def format_output(data, output_path):
    """格式化输出为 PDF"""
    convert_to_pdf(data, output_path)
```

---

### 反例 3: 项目级配置项过多

**错误表现**：
```yaml
# project_config.yaml
# 本可以简单的功能，配置项却超过 20 个
processing:
  retries: 3
  retry_delay: 1.0
  retry_backoff: 2.0
  retry_jitter: true
  timeout:
    connect: 10
    read: 30
    total: 60
  validation:
    strict: true
    level: "high"
    custom_rules: []
  # ... 还有 10+ 个配置项
```

**问题**：大部分场景下这些值不需要改变

**涉及模块**：所有模块

**正确做法**：
```yaml
# project_config.yaml
# 只暴露真正需要配置的项
processing:
  timeout: 30  # 大部分场景够用
  retries: 3   # 大部分场景够用
# 其他值使用合理的默认值，硬编码在代码中
```

---

## 5. 通用性检查反例

### 反例 1: 项目级年份限定

**错误表现**：
```markdown
# CLAUDE.md
## 项目说明
本项目用于处理 2024 年度 NSFC 申请书格式
```

**问题**：年份硬编码，2025 年就需要修改

**涉及模块**：所有模块

**正确做法**：
```markdown
# CLAUDE.md
## 项目说明
本项目用于处理 NSFC 申请书格式（支持所有版本）
```

---

### 反例 2: 过度限定使用场景

**错误表现**：
```markdown
# README.md
## 适用场景
- 将 WeChat 文章同步到 Notion
- 将 WeChat 文章同步到 Obsidian
```

**问题**：限制了平台，实际逻辑可通用化

**涉及模块**：所有模块

**正确做法**：
```markdown
# README.md
## 适用场景
- 将网页文章同步到笔记应用（支持 Notion、Obsidian、Logseq 等）
- 从任意平台抓取内容并格式化
```

---

### 反例 3: 时间敏感示例

**错误表现**：
```markdown
# CLAUDE.md
## 示例
输入：`--date 2025-01-14`
输出：`report_20250114.pdf`
```

**问题**：示例日期会过时

**涉及模块**：所有模块

**正确做法**：
```markdown
# CLAUDE.md
## 示例
输入：`--date {YYYY-MM-DD}`
输出：`report_{YYYYMMDD}.pdf`
```

---

### 反例 4: 不必要的平台限定

**错误表现**：
```markdown
# README.md
本项目专为 macOS 用户设计...
```

**问题**：限制了操作系统，实际功能通用

**涉及模块**：所有模块

**正确做法**：
```markdown
# README.md
本项目支持跨平台使用（macOS、Linux、Windows）
```

---

## 6. 一致性检查反例

### 反例 1: 跨模块接口不一致

**错误表现**：
```python
# module_a/api.py
def process_data(data, options):
    pass
```
```python
# module_b/api.py
def process_data(data, config):
    pass
```

**问题**：两个模块的接口参数名不一致

**涉及模块**：module_a、module_b

**正确做法**：
```python
# shared/api.py
def process_data(data, options):
    """标准接口"""
    pass
```
```python
# module_a/api.py
from shared.api import process_data
```
```python
# module_b/api.py
from shared.api import process_data
```

---

### 反例 2: 跨模块配置项不一致

**错误表现**：
```yaml
# module_a/config.yaml
output:
  directory: "./output"
  format: "json"
```
```yaml
# module_b/config.yaml
output:
  dir: "./output"    # 注意：是 dir 而非 directory
  fmt: "json"        # 注意：是 fmt 而非 format
```

**问题**：配置项名称不一致

**涉及模块**：module_a、module_b

**正确做法**：
```yaml
# project_config.yaml
# 定义标准配置项名称
output:
  directory: "./output"
  format: "json"
```
```yaml
# module_a/config.yaml
# 继承项目级配置
```
```yaml
# module_b/config.yaml
# 继承项目级配置
```

---

### 反例 3: 项目文档与实际不一致

**错误表现**：
```markdown
# CLAUDE.md
## 项目结构
本项目包含三个模块：module_a、module_b、module_c
```
```bash
# 实际情况
$ ls
module_a  module_b  module_d  # 注意：是 module_d 而非 module_c
```

**问题**：文档与实际不符

**涉及模块**：项目文档

**正确做法**：
```markdown
# CLAUDE.md
## 项目结构
本项目包含三个模块：module_a、module_b、module_d
```

---

### 反例 4: 跨模块术语不一致

**错误表现**：
```markdown
# module_a/README.md
## 创建测试会话
v202601141900
```
```markdown
# module_b/README.md
## 创建测试轮次
第一轮测试...
```

**问题**：术语不统一

**涉及模块**：module_a、module_b

**正确做法**：
```markdown
# CLAUDE.md
## 术语表
- 测试会话（session）：一次完整的测试运行
- 测试轮次（round）：测试会话中的一个迭代
```
```markdown
# module_a/README.md
## 创建测试会话
v202601141900
```
```markdown
# module_b/README.md
## 创建测试会话
v202601141900
```

---

## 7. 项目指令文件瘦身检查反例

### 反例 1: 完整模板内容嵌入 CLAUDE.md

**错误表现**：
```markdown
# CLAUDE.md（臃肿）
## A 轮计划模板

## 测试 ID: {{TEST_ID}}
## 测试时间: {{CHECK_TIME}}
## ... 完整的 100 行模板内容 ...
```

**问题**：应引用 `references/A_ROUND_PLAN_TEMPLATE.md`

**涉及模块**：项目文档

**正确做法**：
```markdown
# CLAUDE.md（精简）
## A 轮计划模板

详见 `references/A_ROUND_PLAN_TEMPLATE.md`
```

---

### 反例 2: 详细配置说明

**错误表现**：
```markdown
# CLAUDE.md（臃肿）
## 配置说明

### output_dir
- 类型：字符串
- 默认值："output/"
- 说明：指定输出目录的路径。可以是相对路径或绝对路径...
- 示例：output_dir: "./reports"

### max_retries
- 类型：整数
- 默认值：3
- 说明：最大重试次数。当操作失败时会自动重试...
- 示例：max_retries: 5

# ... 20+ 个配置项的详细说明
```

**问题**：应移至 config.yaml 注释

**涉及模块**：项目文档

**正确做法**：
```markdown
# CLAUDE.md（精简）
## 配置说明

详见 project_config.yaml 中的注释说明。
```

```yaml
# project_config.yaml
# 输出目录（可包含环境变量，如：${HOME}/reports）
output_dir: "./output"

# 最大重试次数（0 表示不重试）
max_retries: 3
```

---

### 反例 3: 详细技术实现

**错误表现**：
```markdown
# CLAUDE.md（臃肿）
## 实现细节

### 跨模块通信机制
模块间使用 HTTP REST API 进行通信。首先启动服务器...
具体实现：[100 行技术说明]
```

**问题**：应移至各模块的文档或技术文档

**涉及模块**：项目文档

**正确做法**：
```markdown
# CLAUDE.md（精简）
## 实现细节

详见 `docs/architecture.md` 和各模块的 README.md。
```

---

### 反例 4: 行数过多

**错误表现**：
```
CLAUDE.md: 800+ 行
references/: 空目录或只有 1-2 个文件
```

**问题**：CLAUDE.md 过于冗长

**涉及模块**：项目文档

**正确做法**：
- CLAUDE.md 控制在 300 行以内
- 详细内容移至 references/
- 技术细节移至 docs/
- 配置说明移至 config.yaml 注释
- 模块详情移至各模块 README.md

---

## 使用反例库进行问题发现

### 步骤 1: 快速扫描

浏览项目文件，对比反例库中的模式：
- 是否有"让 AI 手动操作"的模式？
- 是否有"为未来预留功能"的配置？
- 是否有"年份限定"的文档？
- 是否有跨模块不一致？

### 步骤 2: 深度验证

对发现的疑似问题，进一步验证：
- 这个配置项真的需要吗？
- 这个抽象真的有必要吗？
- 这个限定真的合理吗？
- 这个不一致会影响使用吗？

### 步骤 3: 记录问题

使用问题记录模板记录：
```
#### 问题 X: [反例名称]

**位置**: `文件:行号`

**涉及模块**: [列出相关模块]

**反例类型**: [七大原则之一]

**问题描述**:
[具体描述问题现象，参考反例库]

**优先级**: P0/P1/P2

**修复建议**:
[参考反例库中的"正确做法"]

**跨模块影响**:
[修复会影响哪些模块]

**验证方法**:
[如何确认修复成功]
```

---

**模板说明**：

本文档用于 auto-test-project 快速识别常见问题。

使用时：
1. 熟悉七大原则的反例模式
2. 检查项目时对比反例库
3. 发现相似模式时记录为问题
4. 参考"正确做法"给出修复建议
5. 特别注意跨模块问题和项目级一致性问题
