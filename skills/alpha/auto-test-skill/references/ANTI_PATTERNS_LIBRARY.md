# 技能开发反例库

**文档版本**：v1.0.0
**创建时间**：2026-01-14
**用途**：为 auto-test-skill 提供常见反例库，用于快速识别问题

---

## 使用说明

本文档按照"B 轮质量原则检查维度"分类（以 `config.yaml:b_round_check.dimensions` 为准），每类包含常见反例。

**使用方法**：
1. 在检查 skill 时，对比本文档中的反例
2. 发现相似模式时，记录为问题
3. 参考"正确做法"给出修复建议

---

## 1. 硬编码/AI功能规划反例

### 反例 1: 让 AI "手动创建目录"

**错误表现**：
```markdown
## 执行步骤
1. 创建目录：`output/reports/{timestamp}/`
2. 创建文件：`output/reports/{timestamp}/summary.md`
```

**问题**：这是确定性操作，应脚本化

**正确做法**：
```markdown
## 执行步骤
1. 运行 `scripts/init_session.py` 自动创建目录和文件
```

---

### 反例 2: 配置值硬编码在文档中

**错误表现**：
```markdown
## 配置说明
最大重试次数：3次
超时时间：30秒
```

**问题**：应移至 config.yaml

**正确做法**：
```yaml
# config.yaml
retries:
  max: 3
timeout: 30  # 秒
```

```markdown
## 配置说明
详见 config.yaml 中的 `retries.max` 和 `timeout` 配置项
```

---

### 反例 3: 让 AI 每次编写相同代码

**错误表现**：
```markdown
## 步骤 2
用 Python 读取 CSV 文件：
```python
import csv
with open(file, 'r') as f:
    reader = csv.reader(f)
    ...
```

**问题**：AI 每次都要"记住"这段代码

**正确做法**：
```markdown
## 步骤 2
运行 `scripts/read_csv.py --input {file}` 自动读取
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
```

**问题**：这些是 CSV 标准定义，不需要配置

**正确做法**：
```python
# scripts/reader.py
DELIMITER = ","  # CSV 标准
ENCODING = "utf-8"  # 现代标准
```

---

## 2. 冗余残留错误检查反例

### 反例 1: 残留引用

**错误表现**：
```markdown
# SKILL.md
详见 references/OLD_TEMPLATE.md
```
```bash
# 实际情况
$ ls references/OLD_TEMPLATE.md
ls: cannot access: No such file or directory
```

**问题**：引用已删除的文件

**正确做法**：
```markdown
# SKILL.md
详见 references/NEW_TEMPLATE.md
```

---

### 反例 2: 重复段落

**错误表现**：
```markdown
## 输入格式
输入必须是 PDF 格式，文件大小不超过 10MB...

## 使用示例
示例 1：输入一个 PDF 文件...
示例 2：输入一个 PDF 文件...（与示例 1 几乎相同）
```

**问题**：内容重复，应合并

**正确做法**：
```markdown
## 输入格式
输入必须是 PDF 格式，文件大小不超过 10MB...

## 使用示例
示例：输入一个 PDF 文件并解析...
```

---

### 反例 3: 僵尸文件

**错误表现**：
```
references/unused_guide.md  # 从未被 SKILL.md 或任何脚本引用
assets/old_template.txt     # 已被新模板替代，但未删除
scripts/backup_old.py       # 标记为"备份"，但未说明用途
```

**问题**：无用的文件占用空间，污染代码库

**正确做法**：
```bash
# 使用 Grep 搜索引用
grep -r "unused_guide" .
# 如果无结果，删除文件
rm references/unused_guide.md
```

---

### 反例 4: 配置重复定义

**错误表现**：
```yaml
# config.yaml
output:
  directory: "./output"
  format: "json"
```
```markdown
# SKILL.md
## 配置说明
- output_dir: 输出目录（默认：`output/`）
- output_format: 输出格式（默认：`json`）
```

**问题**：配置项名称不一致（`output.directory` vs `output_dir`）

**正确做法**：
```markdown
## 配置说明
详见 config.yaml 中的 `output.directory` 和 `output.format`
```

---

## 3. 安全性检查反例

### 反例 1: 路径遍历漏洞

**错误表现**：
```python
# 危险：未验证用户输入
user_path = input("输入文件路径：")
with open(user_path, 'r') as f:  # 可能访问任意文件
    ...
```

**问题**：用户可输入 `../../etc/passwd` 访问任意文件

**正确做法**：
```python
import os

user_path = input("输入文件路径：")
resolved = os.path.realpath(user_path)
base_dir = os.path.realpath("./data")

if not resolved.startswith(base_dir):
    raise ValueError("路径必须在 data 目录内")

with open(resolved, 'r') as f:
    ...
```

---

### 反例 2: 敏感信息泄露

**错误表现**：
```python
# 错误日志中暴露详细信息
except Exception as e:
    print(f"错误：处理文件 {user_path} 时失败，详情：{str(e)}")
    # user_path 可能是用户数据，e 可能包含内部路径
```

**问题**：泄露用户数据和系统内部信息

**正确做法**：
```python
except Exception as e:
    logger.error(f"处理文件失败：{e}", exc_info=True)
    # 不记录 user_path，使用日志系统而非 print
```

---

### 反例 3: 命令注入风险

**错误表现**：
```python
# 危险：用户输入直接用于系统命令
os.system(f"convert {user_input} output.pdf")
```

**问题**：用户可输入 `; rm -rf /` 执行任意命令

**正确做法**：
```python
import subprocess

subprocess.run(["convert", user_input, "output.pdf"], check=True)
# 使用参数化 API，而非字符串拼接
```

---

### 反例 4: 硬编码密钥

**错误表现**：
```python
# config.yaml
api_key: "sk-1234567890abcdef"
```

**问题**：密钥硬编码，会提交到 Git

**正确做法**：
```python
# config.yaml
api_key: ${API_KEY}  # 从环境变量读取
```

```bash
# .env（不提交到 Git）
API_KEY=sk-1234567890abcdef
```

---

## 4. 过度设计检查反例

### 反例 1: 为未来预留功能

**错误表现**：
```yaml
# config.yaml
output_formats:
  pdf:
    enabled: true
    engine: "reportlab"
  docx:
    enabled: false  # 未来可能支持
  html:
    enabled: false  # 未来可能支持
  markdown:
    enabled: false  # 未来可能支持
```

**问题**：当前只支持 PDF，其他格式不应硬编码

**正确做法**：
```yaml
# config.yaml
output_format: "pdf"  # 唯一支持的格式
# 未来需要时再添加
```

---

### 反例 2: 过度抽象

**错误表现**：
```python
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

**正确做法**：
```python
def format_output(data, output_path):
    """格式化输出为 PDF"""
    convert_to_pdf(data, output_path)
```

---

### 反例 3: 配置项过多

**错误表现**：
```yaml
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

**正确做法**：
```yaml
# 只暴露真正需要配置的项
processing:
  timeout: 30  # 大部分场景够用
  retries: 3   # 大部分场景够用
# 其他值使用合理的默认值，硬编码在代码中
```

---

## 5. 通用性检查反例

### 反例 1: 年份限定

**错误表现**：
```markdown
## 功能说明
本 skill 用于处理 2024 年度 NSFC 申请书格式
```

**问题**：年份硬编码，2025 年就需要修改

**正确做法**：
```markdown
## 功能说明
本 skill 用于处理 NSFC 申请书格式（支持所有版本）
```

---

### 反例 2: 场景限定过窄

**错误表现**：
```markdown
## 适用场景
- 将 WeChat 文章同步到 Notion
```

**问题**：限制了平台，实际逻辑可通用化

**正确做法**：
```markdown
## 适用场景
- 将网页文章同步到笔记应用（支持 WeChat、Notion、Obsidian 等）
```

---

### 反例 3: 时间敏感示例

**错误表现**：
```markdown
## 示例
输入：`--date 2025-01-14`
输出：`report_20250114.pdf`
```

**问题**：示例日期会过时

**正确做法**：
```markdown
## 示例
输入：`--date {YYYY-MM-DD}`
输出：`report_{YYYYMMDD}.pdf`
```

---

### 反例 4: 不必要的品牌限定

**错误表现**：
```markdown
本 skill 专为 ChatGPT Plus 用户设计...
```

**问题**：限制了 AI 平台，实际功能通用

**正确做法**：
```markdown
本 skill 适用于各类 AI 助手平台（Claude、ChatGPT、Gemini 等）
```

---

## 6. 一致性检查反例

### 反例 1: YAML 与正文不一致

**错误表现**：
```yaml
---
name: pdf-merger
description: 合并多个 PDF 文件
---
```
```markdown
# SKILL.md
## 功能说明
本 skill 用于分割和提取 PDF 页面...
```

**问题**：YAML 说是合并，正文说是分割提取

**正确做法**：
```yaml
---
name: pdf-splitter
description: 分割和提取 PDF 页面
---
```

---

### 反例 2: 配置项不一致

**错误表现**：
```markdown
# SKILL.md
## 配置说明
- `output_dir`: 输出目录（默认：`output/`）
- `max_retries`: 最大重试次数（默认：3）
```
```yaml
# config.yaml
output:
  directory: "./output"
retries:
  max: 5  # 与文档中的默认值 3 不一致
```

**问题**：文档与配置不一致

**正确做法**：
```markdown
# SKILL.md
## 配置说明
详见 config.yaml 中的 `output.directory` 和 `retries.max`
```
```yaml
# config.yaml
output:
  directory: "./output"  # 默认输出目录
retries:
  max: 5  # 最大重试次数
```

---

### 反例 3: 示例与实际不一致

**错误表现**：
```markdown
# README.md
## 使用示例
/run pdf-merger --input file1.pdf,file2.pdf --output merged.pdf
```
```markdown
# SKILL.md（当前版本）
## 参数说明
- `--input`: 输入文件（支持目录和文件，非逗号分隔列表）
```

**问题**：README 中的语法是旧版本

**正确做法**：
```markdown
# README.md
## 使用示例
/run pdf-merger --input ./input_dir --output merged.pdf
```

---

### 反例 4: 术语不一致

**错误表现**：
```markdown
# 一处文档使用"测试会话"（session）
## 创建测试会话
v202601141900

# 另一处使用"测试轮次"（round）
## 测试轮次说明
第一轮测试...
```

**问题**：术语不统一

**正确做法**：
```markdown
# 统一使用"测试会话"（session）
## 创建测试会话
v202601141900

## 测试会话说明
第一个测试会话...
```

---

## 7. SKILL.md 瘦身检查反例

### 反例 1: 完整模板内容嵌入 SKILL.md

**错误表现**：
```markdown
# SKILL.md（臃肿）
## A 轮计划模板

## 测试 ID: {{TEST_ID}}
## 测试时间: {{CHECK_TIME}}
## ... 完整的 100 行模板内容 ...
```

**问题**：应引用 `references/A_ROUND_PLAN_TEMPLATE.md`

**正确做法**：
```markdown
# SKILL.md（精简）
## A 轮计划模板

详见 `references/A_ROUND_PLAN_TEMPLATE.md`
```

---

### 反例 2: 详细配置说明

**错误表现**：
```markdown
# SKILL.md（臃肿）
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

**正确做法**：
```markdown
# SKILL.md（精简）
## 配置说明

详见 config.yaml 中的注释说明。
```

```yaml
# config.yaml
# 输出目录（可包含环境变量，如：${HOME}/reports）
output_dir: "./output"

# 最大重试次数（0 表示不重试）
max_retries: 3
```

---

### 反例 3: 详细技术实现

**错误表现**：
```markdown
# SKILL.md（臃肿）
## 实现细节

### PDF 解析逻辑
使用 PyPDF2 库解析 PDF 文件。首先打开文件，然后逐页读取...
具体实现：[100 行技术说明]
```

**问题**：应移至 scripts/ 注释或独立技术文档

**正确做法**：
```markdown
# SKILL.md（精简）
## 实现细节

详见 `scripts/parse_pdf.py` 中的 docstring 和注释。
```

---

### 反例 4: 行数过多

**错误表现**：
```
SKILL.md: 500+ 行
references/: 空目录或只有 1-2 个文件
```

**问题**：SKILL.md 过于冗长

**正确做法**：
- SKILL.md 控制在 300 行以内
- 详细内容移至 references/
- 技术细节移至 scripts/ 注释
- 配置说明移至 config.yaml 注释

---

## 使用反例库进行问题发现

### 步骤 1: 快速扫描

浏览 skill 文件，对比反例库中的模式：
- 是否有"让 AI 手动操作"的模式？
- 是否有"为未来预留功能"的配置？
- 是否有"年份限定"的文档？

### 步骤 2: 深度验证

对发现的疑似问题，进一步验证：
- 这个配置项真的需要吗？
- 这个抽象真的有必要吗？
- 这个限定真的合理吗？

### 步骤 3: 记录问题

使用问题记录模板记录：
```
#### 问题 X: [反例名称]

**位置**: `文件:行号`

**反例类型**: [质量原则之一]

**问题描述**:
[具体描述问题现象，参考反例库]

**优先级**: P0/P1/P2

**修复建议**:
[参考反例库中的"正确做法"]

**验证方法**:
[如何确认修复成功]
```

---

**模板说明**：

本文档用于 auto-test-skill 快速识别常见问题。

使用时：
1. 熟悉质量原则的反例模式
2. 检查 skill 时对比反例库
3. 发现相似模式时记录为问题
4. 参考"正确做法"给出修复建议
