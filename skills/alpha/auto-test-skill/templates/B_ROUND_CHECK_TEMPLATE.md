# B轮质量检查报告（质量原则检查）

**检查ID**: B轮-{{TEST_ID}}
**检查时间**: {{CHECK_TIME}}
**对应A轮测试**: {{A_TEST_ID}}
**目标技能**: {{TARGET_SKILL_NAME}}
**目标技能路径**: {{TARGET_SKILL_ROOT}}

---

## 检查结果总览

| 维度 | 状态 | 备注 |
|------|------|------|
| 硬编码/AI功能规划 | ✅ / ⚠️ / ❌ | {{NOTE_1}} |
| 冗余残留错误检查 | ✅ / ⚠️ / ❌ | {{NOTE_2}} |
| 安全性检查 | ✅ / ⚠️ / ❌ | {{NOTE_3}} |
| 过度设计检查 | ✅ / ⚠️ / ❌ | {{NOTE_4}} |
| 通用性检查 | ✅ / ⚠️ / ❌ | {{NOTE_5}} |
| 一致性检查 | ✅ / ⚠️ / ❌ | {{NOTE_6}} |
| 配置集中化检查 | ✅ / ⚠️ / ❌ | {{NOTE_7}} |
| SKILL.md瘦身检查 | ✅ / ⚠️ / ❌ | {{NOTE_8}} |

---

## 1. 硬编码/AI 功能规划

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**确定性操作应脚本化，启发式判断由AI处理**。两者应协调配合，让skill功能发挥更完全。

### 判断标准

#### ✅ 合理的硬编码/AI分工
- **确定性操作已脚本化**：文件解析、目录创建、命名规范、数据验证、格式转换等操作已通过 `scripts/` 中的脚本实现
- **可配置参数已集中**：阈值、路径、模板、选项等参数已提取到 `config.yaml`，避免硬编码在SKILL.md或脚本中
- **AI专注启发式任务**：AI仅负责需求理解、方案设计、内容生成、语义判断等需要灵活性的任务
- **无重复造轮子**：AI不会在每次执行时重复编写相同的代码逻辑

#### ⚠️ 需要改进的信号
- AI每次都要"手动"执行固定操作（如"创建目录X"、"复制模板Y"）
- 配置值硬编码在文档或脚本中，而非从config.yaml读取
- AI被要求执行确定性计算（如日期格式、路径拼接、数据验证）

#### ❌ 严重问题示例
- 让AI反复编写相同的文件操作代码（每次执行都从头写一遍）
- 时间戳、路径等基础逻辑未脚本化，依赖AI"每次记得正确执行"
- 可配置参数分散在多个文件中，难以统一维护

### 典型反例

**反例1**：SKILL.md中要求AI"手动创建目录"
```markdown
## 执行步骤
1. 创建目录：`output/reports/{timestamp}/`
2. 创建文件：`output/reports/{timestamp}/summary.md`
```
**问题**：这是确定性操作，应脚本化

**反例2**：配置值硬编码在文档中
```markdown
## 配置说明
最大重试次数：3次
超时时间：30秒
```
**问题**：应移至config.yaml

### 改进方向
- 将重复的确定性操作提取到 `scripts/`
- 将可配置参数集中到 `config.yaml`
- SKILL.md中仅描述AI需要做什么，而非如何一步步操作

### 本轮发现
- {{FINDING_1}}

### 改进建议
- {{SUGGESTION_1}}

### 🚨 挑衅性检查（必须回答）

1. **找出一个"伪脚本化"的例子**：看似已脚本化，但 AI 仍在手动执行的操作
   - 位置：{{PSEUDO_SCRIPT_LOCATION}}
   - 伪脚本化表现：{{PSEUDO_SCRIPT_MANIFESTATION}}
   - 应如何改进：{{PSEUDO_SCRIPT_FIX}}

2. **找出一个"过度配置化"的例子**：本应硬编码的常量，却放到了 config.yaml
   - 位置：{{OVER_CONFIG_LOCATION}}
   - 过度配置化表现：{{OVER_CONFIG_MANIFESTATION}}
   - 应如何改进：{{OVER_CONFIG_FIX}}

3. **质疑隐式假设**：文档假设用户会做 X（如"用户会先创建目录"），实际可能不会
   - 假设内容：{{IMPLICIT_ASSUMPTION}}
   - 失效场景：{{ASSUMPTION_FAILURE_SCENARIO}}
   - 应如何改进：{{ASSUMPTION_FIX}}

4. **边缘情况挑战**：如果用户输入的路径是 `../../etc/passwd`，当前逻辑能防御吗？
   - 位置：{{EDGE_CASE_LOCATION}}
   - 防御措施：{{EDGE_CASE_DEFENSE}}
   - 是否足够？：{{EDGE_CASE_ADEQUATE}}

---

## 2. 冗余残留错误检查

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**消除冗余、清理残留、修复错误**。确保skill结构清晰、无遗留问题。

### 判断标准

#### ✅ 无冗余残留
- **无重复逻辑**：相似逻辑已抽象复用，无复制粘贴的代码段或文档段落
- **无残留引用**：已删除的文件/功能，其引用已全部清理
- **无僵尸文件**：所有文件都有明确用途，被其他文件引用或被工作流使用
- **无逻辑错误**：文档描述与实际实现一致，无矛盾或错误陈述

#### ⚠️ 需要清理的信号
- 存在相似或相同的代码段/文档段落（可合并但未合并）
- 文档中引用了不存在的文件、目录或配置项
- `references/`、`assets/` 中存在未被SKILL.md或脚本引用的文件
- 文档中存在"已废弃"、"旧版本"、"TODO"等未清理的标记

#### ❌ 严重问题示例
- 删除功能后，相关引用散落在多个文件中未清理
- 相同的配置参数在config.yaml和SKILL.md中重复定义
- 存在"备份文件"（如file_old.md、file_backup.md）但未说明用途

### 典型反例

**反例1**：残留引用
```
文档中：参考 `references/OLD_TEMPLATE.md`
实际情况：该文件已被删除，应引用 `references/NEW_TEMPLATE.md`
```

**反例2**：重复段落
```markdown
# SKILL.md
## 输入格式
输入必须是PDF格式...

## 使用示例
示例1：输入一个PDF文件...
示例2：输入一个PDF文件...（与示例1几乎相同）
```

**反例3**：僵尸文件
```
references/unused_guide.md  # 从未被SKILL.md或任何脚本引用
assets/old_template.txt     # 已被新模板替代，但未删除
```

### 改进方向
- 使用Grep工具全局搜索被删除文件/功能的引用
- 合并相似的文档段落或代码逻辑
- 清理未使用的参考文件和资产
- 移除过时的标记和注释

### 本轮发现
- {{FINDING_2}}

### 改进建议
- {{SUGGESTION_2}}

---

## 3. 安全性检查

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**预防常见安全漏洞和风险**。确保skill在输入处理、文件操作、信息泄露等方面无重大安全隐患。

### 判断标准

#### ✅ 安全性良好
- **输入路径已规范化和校验**：用户提供的路径已验证其合法性（防止路径遍历攻击），确保在项目范围内
- **无敏感信息泄露**：日志、错误消息、示例中不包含密钥、凭证、内部路径等敏感信息
- **外部调用可控**：网络请求、系统调用等外部操作显式、可控、可复现，不执行任意用户输入
- **文件路径跨平台兼容**：使用正斜杠，确保在Windows/macOS/Linux上都能正常工作

#### ⚠️ 潜在安全风险
- 用户输入直接用于文件路径操作，未做边界检查
- 错误消息中包含详细路径或系统信息
- 外部调用使用用户输入作为参数，未做验证
- 硬编码了临时路径或测试路径

#### ❌ 严重安全漏洞
- 路径遍历漏洞：允许访问项目目录外的文件（如 `../../../etc/passwd`）
- 命令注入风险：用户输入未过滤直接传递给系统命令
- 敏感信息硬编码：API密钥、密码等直接写在代码或配置中
- 不安全的反序列化/解析：对不可信数据直接反序列化

### 典型反例

**反例1**：路径遍历风险
```python
# 危险：未验证用户输入
user_path = input("输入文件路径：")
with open(user_path, 'r') as f:  # 可能访问任意文件
    ...
```
**修复**：验证路径在项目范围内

**反例2**：敏感信息泄露
```python
# 错误日志中暴露详细信息
except Exception as e:
    print(f"错误：处理文件 {user_path} 时失败，详情：{str(e)}")
    # user_path可能是用户数据，e可能包含内部路径
```

**反例3**：命令注入风险
```python
# 危险：用户输入直接用于系统命令
os.system(f"convert {user_input} output.pdf")
```
**修复**：使用参数化API或严格验证输入

### 改进方向
- 所有用户输入必须验证和规范化
- 文件操作前检查路径是否在允许范围内
- 避免在日志/错误中泄露敏感信息
- 使用参数化API而非字符串拼接执行外部命令
- 敏感配置使用环境变量或加密存储

### 本轮发现
- {{FINDING_3}}

### 改进建议
- {{SUGGESTION_3}}

---

## 4. 过度设计检查

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**用奥卡姆剃刀原则审视每个设计决策**。避免为"未来可能用到"的场景预留功能，优先选择最简单的解决方案。

### 判断标准

#### ✅ 设计简洁适度
- **只实现当前需要的功能**：无"为未来预留"的复杂抽象或扩展点
- **配置项合理**：配置项数量适中，每个都有明确用途，不过度抽象
- **实现直观**：使用最直观、最易理解的实现方式
- **职责单一**：每个函数/模块/文件只做一件事，职责清晰

#### ⚠️ 存在过度设计信号
- 配置项过多（超过15-20个）且大量嵌套，难以理解
- 引入了多层抽象解决简单问题（如"管理器工厂的建造者"）
- 提供了大量可选配置，但大部分场景下只需使用默认值
- 文档中大量解释"这个设计是为了未来的XX场景"

#### ❌ 严重过度设计
- 明显的YAGNI违反：为"未来可能需要"的功能预留接口/配置
- 过度泛化：试图用一套逻辑处理所有场景，导致代码难以理解
- 不必要的抽象层次：引入"中间层"但只起到简单的传递作用

### 典型反例

**反例1**：为未来预留功能
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
**问题**：当前只支持PDF，其他格式不应硬编码在配置中

**反例2**：过度抽象
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

**反例3**：配置项过多
```yaml
# 本可以简单的功能，配置项却超过20个
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
  # ... 还有10+个配置项
```
**问题**：大部分场景下这些值不需要改变，应简化为必要的配置

### 改进方向
- 删除未使用的"预留"功能和配置
- 合并相似的配置项，使用合理的默认值
- 简化抽象层次，优先使用直接的实现方式
- 遵循KISS原则：能用简单方法解决的，不引入复杂设计

### 本轮发现
- {{FINDING_4}}

### 改进建议
- {{SUGGESTION_4}}

---

## 5. 通用性检查

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**避免不必要的场景和年份限制**。提高skill复用性，使其能适应更广泛的场景和时间跨度。

### 判断标准

#### ✅ 通用性良好
- **无时间敏感性**：不包含具体年份、日期等会过时的信息（除非是命名规范要求）
- **无场景限制**：不过度限定使用场景，可适配多种类似需求
- **无平台依赖**：不强制依赖特定平台或工具（除非是skill的核心定位）
- **使用相对时间**：描述使用"当前版本"、"最新版"等相对时间表述
- **通用术语**：使用通用术语，避免特定品牌或产品名称（除非必要）

#### ⚠️ 通用性受限
- 文档中包含"2024年版"、"2025年"等具体年份（非必要）
- 示例硬编码了特定场景（如"用于NSFC申请书"而非"用于科研申请书"）
- 假设了特定语言或文化背景
- 依赖特定平台的特有功能（非核心需求）

#### ❌ 严重通用性问题
- skill名称或描述中包含年份（如`nsfc-2025-formatter`）
- 硬编码了特定工作流（如"适配XX公司的内部流程"）
- 包含特定品牌的专有术语或缩写（无解释）

### 典型反例

**反例1**：年份限定
```markdown
## 功能说明
本skill用于处理2024年度NSFC申请书格式
```
**问题**：年份硬编码，2025年就需要修改
**修复**：改为"本skill用于处理NSFC申请书格式"

**反例2**：场景限定过窄
```markdown
## 适用场景
- 将WeChat文章同步到Notion
```
**问题**：限制了平台，实际逻辑可通用化
**修复**：改为"将网页文章同步到笔记应用（支持WeChat、Notion等）"

**反例3**：时间敏感示例
```markdown
## 示例
输入：`--date 2025-01-14`
输出：`report_20250114.pdf`
```
**问题**：示例日期会过时
**修复**：使用占位符`--date {YYYY-MM-DD}`

**反例4**：不必要的品牌限定
```markdown
本skill专为ChatGPT Plus用户设计...
```
**问题**：限制了AI平台，实际功能通用
**修复**：改为"本skill适用于各类AI助手平台..."

### 改进方向
- 将具体年份改为相对时间表述（"当前版本"）
- 将特定场景泛化为通用场景（如"NSFC"→"科研基金"）
- 提供扩展机制（如config.yaml），而非硬编码特定配置
- 在YAML `description` 中说明适用场景，而非硬编码到工作流
- 使用占位符替代时间敏感的示例数据

### 本轮发现
- {{FINDING_5}}

### 改进建议
- {{SUGGESTION_5}}

---

## 6. 一致性检查

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**确保文档、配置、实现三者一致**。避免相互矛盾、描述不符、版本不匹配等问题。

### 判断标准

#### ✅ 一致性良好
- **YAML frontmatter 与 SKILL.md 正文一致**：
  - `name`、`description` 与正文中的技能名称、功能描述一致
  - `metadata.keywords` 涵盖了正文中的关键场景
  - 版本号（如有）与 config.yaml 一致
- **SKILL.md 与 config.yaml 一致**：
  - 文档中提到的配置项在 config.yaml 中存在
  - 文档中提到的路径、模板在 config.yaml 中定义且路径正确
  - config.yaml 中的配置项在文档中都有说明
- **README.md 与 SKILL.md 一致**（B 轮额外检查）：
  - README 中的示例与 SKILL.md 中的工作流一致
  - README 中的触发方式与 YAML `description` 一致
- **术语一致**：同一概念在所有文件中使用相同的术语
- **示例一致**：文档中的示例可以实际运行，与当前版本功能一致

#### ⚠️ 存在不一致信号
- YAML frontmatter 中的 `description` 与正文描述有差异
- SKILL.md 中引用了 config.yaml 中不存在的配置项
- README 中的示例使用旧版语法或已废弃的功能
- 同一概念在不同文件中使用不同术语（如"测试会话"vs"测试轮次"）

#### ❌ 严重不一致问题
- YAML frontmatter 中的 `name` 与实际目录名不一致
- 文档中提到的核心功能在当前版本中不存在或已移除
- config.yaml 中的路径指向不存在的文件或目录
- 版本号在不同文件中不一致

### 典型反例

**反例1**：YAML与正文不一致
```yaml
---
name: pdf-merger
description: 合并多个PDF文件
---
```
```markdown
# SKILL.md
## 功能说明
本skill用于分割和提取PDF页面...
```
**问题**：YAML说是合并，正文说是分割提取

**反例2**：配置项不一致
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
  max: 5  # 与文档中的默认值3不一致
```

**反例3**：示例与实际不一致
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
**问题**：README中的语法是旧版本

**反例4**：术语不一致
```markdown
# 一处文档使用"测试会话"（session）
## 创建测试会话
v202601141900

# 另一处使用"测试轮次"（round）
## 测试轮次说明
第一轮测试...
```

### 改进方向
- 更新 YAML frontmatter 使其准确反映当前技能的功能
- 确保文档中引用的所有配置项在 config.yaml 中存在且名称一致
- 同步更新 README 中的示例，使其与当前版本一致
- 统一术语，在所有文件中使用相同的词汇描述同一概念
- 定期检查：文档描述 → config.yaml → 实际脚本/模板 三者是否匹配

### 本轮发现
- {{FINDING_6}}

### 改进建议
- {{SUGGESTION_6}}

---

## 7. SKILL.md 瘦身检查

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**遵循渐进披露（Progressive Disclosure）原则**。SKILL.md 应保持简洁，只包含 AI 执行所需的核心信息；详细内容应模块化到 `references/`。

### 判断标准

#### ✅ SKILL.md 瘦身良好
- **行数合理**：SKILL.md 不超过 300 行（建议阈值，可根据复杂度调整）
- **核心内容保留**：工作流概览、输入输出、关键步骤、验证标准
- **详细内容已模块化**：详细策略、标准、模板、示例已移至 `references/`
- **配置说明已分离**：配置项的详细说明已移至 `config.yaml` 注释
- **技术细节已下沉**：实现逻辑、参数说明已移至 `scripts/` 注释或 README

#### ⚠️ 存在臃肿信号
- SKILL.md 超过 300-400 行
- 包含大量详细的策略说明（可独立为文档）
- 包含完整的模板内容（可移至 `assets/` 或 `references/`）
- 包含冗长的配置项说明（可移至 config.yaml 注释）
- 包含详细的技术实现细节（可移至脚本注释或 README）

#### ❌ 严重臃肿问题
- SKILL.md 超过 500 行
- 包含多个完整的模板文件内容
- 包含大量配置项的详细说明（每个配置项一段说明）
- 包含详细的技术架构和实现细节
- `references/` 目录几乎为空，但 SKILL.md 非常长

### 渐进披露策略

| 内容类型 | 保留位置 | 示例 |
|---------|---------|------|
| **核心工作流** | SKILL.md | 概览、输入输出、关键步骤、验证标准 |
| **详细模板** | references/ 或 assets/ | 完整的 A 轮计划结构、B 轮检查清单 |
| **技术实现细节** | scripts/ 注释或 README | 实现逻辑、参数说明、算法细节 |
| **配置说明** | config.yaml 注释 | 参数含义、默认值、使用示例 |
| **详细策略/标准** | references/ | 质量原则、最佳实践、设计决策 |

### 典型反例

**反例1**：完整模板内容嵌入 SKILL.md
```markdown
# SKILL.md（臃肿）
## A 轮计划模板

## 测试 ID: {{TEST_ID}}
## 测试时间: {{CHECK_TIME}}
## ... 完整的 100 行模板内容 ...
```
**问题**：应引用 `references/A_ROUND_PLAN_TEMPLATE.md`

**反例2**：详细配置说明
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

**反例3**：详细技术实现
```markdown
# SKILL.md（臃肿）
## 实现细节

### PDF 解析逻辑
使用 PyPDF2 库解析 PDF 文件。首先打开文件，然后逐页读取...
具体实现：[100 行技术说明]
```
**问题**：应移至 scripts/ 注释或独立技术文档

### 瘦身操作指南

#### 步骤1：识别可迁移内容
- [ ] 完整的模板文件（移至 `assets/` 或 `references/`）
- [ ] 详细的策略/标准/最佳实践（移至 `references/`）
- [ ] 配置项的详细说明（移至 `config.yaml` 注释）
- [ ] 技术实现细节（移至 `scripts/` 注释或 README）

#### 步骤2：执行迁移
- 在 SKILL.md 中使用引用而非嵌入内容：`详见 references/XXX.md`
- 在 config.yaml 中添加注释说明配置项
- 在脚本中添加 docstring 和注释说明实现逻辑
- 在 references/ 中创建详细文档

#### 步骤3：精简 SKILL.md
- 保留核心工作流和关键步骤
- 使用简洁的描述，避免冗长说明
- 用链接/引用替代详细内容

### 本轮发现
- {{FINDING_7}}

### 瘦身建议
- {{SUGGESTION_7}}

---

## 7. 配置集中化检查

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**精确端（config.yaml）与模糊端（工作文档）完全分离**。所有可配置参数必须集中在 `config.yaml` 作为单一真相来源，工作文档仅引用配置，不硬编码任何值。

### 判断标准

#### ✅ 配置集中化良好
- **config.yaml 是唯一参数来源**：所有阈值、路径、选项、超时、重试次数等可配置参数都定义在 `config.yaml` 中
- **scripts/ 仅读取配置**：脚本通过加载 `config.yaml` 获取参数，不硬编码任何魔法数字或路径
- **SKILL.md 仅引用配置**：文档中提及参数时，仅说明"参考 config.yaml 中的 `xxx` 选项"，不直接写出具体值
- **无参数分散**：不存在"同一个参数在多个文件中重复定义"的情况
- **无硬编码常量**：代码和文档中不存在 `MAX_RETRY = 3`、`TIMEOUT = 30` 这类硬编码（除非是真正的数学/物理常数）

#### ⚠️ 存在配置分散信号
- 部分参数在 `config.yaml` 中定义，但部分参数硬编码在 `scripts/` 中
- SKILL.md 中写死了参数值（如"最大重试 3 次"），而非引用 `config.yaml`
- 修改参数需要同时修改多个文件
- 不同环境/用户使用时，需要修改代码而非仅修改配置

#### ❌ 严重配置分散问题
- 完全没有 `config.yaml`，所有参数硬编码在代码和文档中
- 存在 `config.yaml` 但内容为空或仅有少量配置，大量参数仍硬编码
- 同一参数在多个文件中有不同的值（如文档说"默认 3 次"，代码写的是 5 次）
- 脚本中存在大量魔法数字且无注释说明来源

### 典型反例

**反例1**：参数硬编码在脚本中
```python
# scripts/process.py - 错误做法
MAX_RETRIES = 3  # 硬编码
TIMEOUT = 30     # 硬编码
OUTPUT_DIR = "./output"  # 硬编码

def process_file(file):
    for i in range(MAX_RETRIES):  # 应该从 config.yaml 读取
        ...
```
**问题**：修改参数需要改代码，且无法针对不同环境提供不同配置

**正确做法**：
```python
# scripts/process.py - 正确做法
import yaml

def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

config = load_config()
MAX_RETRIES = config.get('max_retries', 3)
TIMEOUT = config.get('timeout', 30)
OUTPUT_DIR = config.get('output_dir', './output')
```

**反例2**：文档中写死参数值
```markdown
# SKILL.md - 错误做法
## 配置说明
本技能最大重试 3 次，超时时间 30 秒。
```
**问题**：修改 config.yaml 后，文档仍然显示旧的默认值

**正确做法**：
```markdown
# SKILL.md - 正确做法
## 配置说明
重试次数和超时时间请参考 `config.yaml` 中的 `max_retries` 和 `timeout` 选项。
```

**反例3**：同一参数多处定义且不一致
```python
# scripts/process.py
MAX_RETRIES = 3
```
```markdown
# README.md
默认最大重试次数：5 次
```
```yaml
# config.yaml
max_retries: 5
```
**问题**：文档与代码不一致，用户会困惑

### 改进方向
- 将所有可配置参数提取到 `config.yaml`，提供合理的默认值
- 脚本启动时加载 `config.yaml`，使用 `config.get('key', default_value)` 模式读取参数
- 文档中仅说明参数的含义和位置，不写出具体值
- 使用环境变量或配置文件覆盖机制，支持不同环境的配置需求

### 检查方法（建议）
```bash
# 搜索脚本中的硬编码数字
rg "(?<=MAX_RETRIES|TIMEOUT|DELAY)\s*=\s*\d+" scripts/

# 搜索硬编码路径
rg "(?<=path|dir|file)\s*=\s*[\"'][\w/]+[\"']" scripts/

# 搜索 SKILL.md 中的具体数值
rg "\d+\s*(次|秒|分钟|字节)" SKILL.md

# 对比 config.yaml 和脚本中的变量名
rg "config\.get\(" scripts/ | grep -oP 'get\(\K[^\)]+' | sort -u
```

### 本轮发现
- {{FINDING_7}}

### 改进建议
- {{SUGGESTION_7}}

---

## 8. SKILL.md 瘦身检查

**状态**: ✅ / ⚠️ / ❌

### 核心原则
**遵循渐进披露原则**。SKILL.md 应保持简洁，只包含 AI 执行所需的核心信息；详细内容应模块化到 `references/`。

### 判断标准

#### ✅ SKILL.md 瘦身良好
- **行数合理**：SKILL.md 不超过 300 行（建议阈值，可根据复杂度调整）
- **核心内容保留**：工作流概览、输入输出、关键步骤、验证标准
- **详细内容已模块化**：详细策略、标准、模板、示例已移至 `references/`
- **配置说明已分离**：配置项的详细说明已移至 `config.yaml` 注释
- **技术细节已下沉**：实现逻辑、参数说明已移至 `scripts/` 注释或 README

#### ⚠️ 存在臃肿信号
- SKILL.md 超过 300-400 行
- 包含大量详细的策略说明（可独立为文档）
- 包含完整的模板内容（可移至 `assets/` 或 `references/`）
- 包含冗长的配置项说明（可移至 `config.yaml` 注释）
- 包含详细的技术实现细节（可移至脚本注释或 README）

#### ❌ 严重臃肿问题
- SKILL.md 超过 500 行
- 包含多个完整的模板文件内容
- 包含大量配置项的详细说明（每个配置项一段说明）
- 包含详细的技术架构和实现细节
- `references/` 目录几乎为空，但 SKILL.md 非常长

### 渐进披露策略

| 内容类型 | 保留位置 | 示例 |
|---------|---------|------|
| **核心工作流** | SKILL.md | 概览、输入输出、关键步骤、验证标准 |
| **详细模板** | references/ 或 assets/ | 完整的 A 轮计划结构、B 轮检查清单 |
| **技术实现细节** | scripts/ 注释或 README | 实现逻辑、参数说明、算法细节 |
| **配置说明** | config.yaml 注释 | 参数含义、默认值、使用示例 |
| **详细策略/标准** | references/ | 质量原则、最佳实践、设计决策 |

### 本轮发现
- {{FINDING_8}}

### 瘦身建议
- {{SUGGESTION_8}}

---

## 改进建议汇总（按优先级）

⚠️ **数量要求**：B 轮必须提出至少 10-20 个建设性建议（P0 + P1 + P2 总和）

### P0（必须修复）
- {{P0_ITEM_1}}

### P1（强烈建议）
- {{P1_ITEM_1}}

### P2（可选）
- {{P2_ITEM_1}}

---

## 🚨 全局挑衅性检查（必须全部回答）

### 1. 最挑剔的问题：这个 skill 有哪些"自我感动"的设计？

列出 3 个"看似专业，实际无用"的过度设计：

- {{SELF_INDULGENT_1}}
- {{SELF_INDULGENT_2}}
- {{SELF_INDULGENT_3}}

### 2. 边缘情况压力测试

模拟极端输入场景，验证 skill 的鲁棒性：

- 如果用户输入**空目录**会怎样？
  - 预期行为：{{EMPTY_DIR_EXPECTATION}}
  - 实际行为：{{EMPTY_DIR_ACTUAL}}
  - 是否有明确的错误提示？{{YES_NO}}

- 如果用户输入**包含特殊字符的路径**（如空格、引号、`../`）会怎样？
  - 预期行为：{{SPECIAL_CHARS_EXPECTATION}}
  - 实际行为：{{SPECIAL_CHARS_ACTUAL}}
  - 是否有路径规范化？{{YES_NO}}

- 如果 config.yaml **被用户删空或包含无效值**会怎样？
  - 预期行为：{{INVALID_CONFIG_EXPECTATION}}
  - 实际行为：{{INVALID_CONFIG_ACTUAL}}
  - 是否有默认值回退？{{YES_NO}}

### 3. 隐式假设挖掘

列出 5 个文档未说明、但 AI 默认假设会成立的条件：

1. {{ASSUMPTION_1}} → 在什么情况下会失效？{{ASSUMPTION_1_FAILURE}}
2. {{ASSUMPTION_2}} → 在什么情况下会失效？{{ASSUMPTION_2_FAILURE}}
3. {{ASSUMPTION_3}} → 在什么情况下会失效？{{ASSUMPTION_3_FAILURE}}
4. {{ASSUMPTION_4}} → 在什么情况下会失效？{{ASSUMPTION_4_FAILURE}}
5. {{ASSUMPTION_5}} → 在什么情况下会失效？{{ASSUMPTION_5_FAILURE}}

### 4. "如果我是恶意用户"测试

尝试构造 3 个恶意输入场景，验证 skill 是否安全：

- **场景 1**：{{MALICIOUS_SCENARIO_1}}
  - 攻击向量：{{ATTACK_VECTOR_1}}
  - 当前防御：{{DEFENSE_1}}
  - 是否足够？{{YES_NO}}

- **场景 2**：{{MALICIOUS_SCENARIO_2}}
  - 攻击向量：{{ATTACK_VECTOR_2}}
  - 当前防御：{{DEFENSE_2}}
  - 是否足够？{{YES_NO}}

- **场景 3**：{{MALICIOUS_SCENARIO_3}}
  - 攻击向量：{{ATTACK_VECTOR_3}}
  - 当前防御：{{DEFENSE_3}}
  - 是否足够？{{YES_NO}}

### 5. 文档与实现的"鸿沟"

找出 3 个"文档说 A，实际做 B"的不一致之处：

1. **位置**：{{INCONSISTENCY_1_LOCATION}}
   - 文档说：{{DOC_SAYS_1}}
   - 实际做：{{CODE_DOES_1}}
   - 影响：{{INCONSISTENCY_1_IMPACT}}

2. **位置**：{{INCONSISTENCY_2_LOCATION}}
   - 文档说：{{DOC_SAYS_2}}
   - 实际做：{{CODE_DOES_2}}
   - 影响：{{INCONSISTENCY_2_IMPACT}}

3. **位置**：{{INCONSISTENCY_3_LOCATION}}
   - 文档说：{{DOC_SAYS_3}}
   - 实际做：{{CODE_DOES_3}}
   - 影响：{{INCONSISTENCY_3_IMPACT}}

### 6. "你会真的用这个 skill 吗？"测试

模拟真实使用场景，评估 skill 的可用性：

- **第一印象**：如果我是新用户，看到 SKILL.md 后，我能在 5 分钟内理解如何使用吗？
  - 评分（1-10）：{{FIRST_IMPRESSION_SCORE}}
  - 主要障碍：{{FIRST_IMPRESSION_BARRIER}}

- **实际操作**：如果我要按照文档执行一次，我会卡在哪里？
  - 预期卡点 1：{{FRICTION_POINT_1}}
  - 预期卡点 2：{{FRICTION_POINT_2}}
  - 预期卡点 3：{{FRICTION_POINT_3}}

- **错误处理**：如果我在中间步骤出错了，文档是否告诉我如何恢复？
  - 是否有错误恢复指南？{{YES_NO}}
  - 如果没有，应该补充什么？{{RECOVERY_GUIDANCE}}

---

## 技能评分（百分制）

| 维度 | 得分 | 满分 | 扣分原因 |
|------|------|------|----------|
| 硬编码/AI功能规划 | {{SCORE_1}} | 15 | {{REASON_1}} |
| 冗余残留错误检查 | {{SCORE_2}} | 15 | {{REASON_2}} |
| 安全性检查 | {{SCORE_3}} | 20 | {{REASON_3}} |
| 过度设计检查 | {{SCORE_4}} | 15 | {{REASON_4}} |
| 通用性检查 | {{SCORE_5}} | 10 | {{REASON_5}} |
| 一致性检查 | {{SCORE_6}} | 15 | {{REASON_6}} |
| 配置集中化检查 | {{SCORE_7}} | 15 | {{REASON_7}} |
| SKILL.md瘦身检查 | {{SCORE_8}} | 10 | {{REASON_8}} |
| **总分** | **{{TOTAL_SCORE}}** | **115** | |

### 评分标准
- **90-100 分**：优秀（生产就绪）
- **75-89 分**：良好（可用于生产，有改进空间）
- **60-74 分**：及格（需要重要优化）
- **< 60 分**：不及格（需要重大改进）

### 与上轮对比
- 上轮得分：{{PREV_SCORE}}（如有）
- 本轮进步：{{IMPROVEMENT}}
