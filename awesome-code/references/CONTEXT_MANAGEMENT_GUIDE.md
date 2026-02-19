# Context Window 管理优化指南

**版本**: v2.1.0
**最后更新**: 2026-01-17

---

## 概述

本指南描述了 Awesome Code 技能中的 Context Window 管理优化策略，旨在解决长对话中的性能和准确性问题。

---

## 常见问题

### Lost-in-Middle 现象

关键信息被中间内容淹没，AI 无法准确定位重要上下文。

**症状**:
- AI 重复询问已提供的信息
- 忽略早期的指令或约束
- 生成的内容与上下文矛盾

**解决方案**:
1. 使用压缩策略总结历史对话
2. 提取关键决策并持久化
3. 归档已完成任务

### Context Poisoning

冲突或误导信息干扰 AI 判断。

**症状**:
- AI 在矛盾信息间摇摆
- 生成的内容不符合最新要求
- 无法区分当前和过时信息

**解决方案**:
1. 使用掩码策略只加载相关文件
2. 分阶段处理任务，避免信息混乱
3. 明确标记信息的时效性

### Token 浪费

无关信息消耗宝贵的 token 预算。

**症状**:
- 对话早期就达到 token 限制
- 加载了大量不相关的文档
- 重复加载相同内容

**解决方案**:
1. 实现智能缓存机制
2. 按需加载详细引用
3. 使用摘要代替全文

---

## 优化策略

### 1. 压缩策略

#### 对话摘要

将历史对话压缩为结构化摘要：

```markdown
## 对话摘要 (v202601171420)

### 关键决策
- 采用 TDD 工作流开发登录功能
- 使用 pytest 作为测试框架
- 目标测试覆盖率 ≥ 80%

### 已完成任务
- [x] 编写登录功能的失败测试
- [x] 实现基本的用户认证

### 待办任务
- [ ] 添加密码强度验证
- [ ] 实现记住登录状态

### 约束条件
- 必须使用 bcrypt 加密密码
- 禁止存储明文密码
```

#### 决策提取

提取并持久化关键决策：

```python
@dataclass
class Decision:
    """关键决策记录"""
    id: str
    timestamp: datetime
    topic: str
    decision: str
    rationale: str
    implications: List[str]
```

#### 归档已完成任务

将已完成的任务移至归档：

```
当前对话: 最近 5 轮
短期归档: 最近 20 轮（摘要形式）
长期归档: 更早内容（仅关键决策）
```

---

### 2. 掩码策略

#### 按需加载文件

只加载与当前任务相关的文件：

```python
def load_relevant_files(
    task: Task,
    all_files: List[Path],
    relevance_threshold: float = 0.3,
) -> List[Path]:
    """基于任务相关性加载文件"""
    relevant_files = []
    for file_path in all_files:
        relevance = calculate_relevance(task, file_path)
        if relevance >= relevance_threshold:
            relevant_files.append(file_path)
    return relevant_files
```

#### 延迟加载详细引用

第一阶段只加载摘要，按需加载详细内容：

```markdown
## 参考文档索引

| 文档 | 摘要 | 详见 |
|------|------|------|
| TDD 最佳实践 | TDD 工作流指南 | `tdd-best-practices.md` |
| 代码审查清单 | 代码质量检查项 | `code-review-checklist.md` |
```

#### 分阶段处理

将大型任务分解为阶段，每阶段只关注相关上下文：

```
阶段 1: 需求分析（只加载需求相关文档）
阶段 2: 设计方案（只加载设计相关文档）
阶段 3: 实现编码（只加载代码相关文档）
阶段 4: 测试验证（只加载测试相关文档）
```

---

### 3. 缓存策略

#### 重用已解析信息

缓存解析后的配置、AST 等结构化数据：

```python
@file_cache(ttl_seconds=3600)
def parse_config(config_path: Path) -> Dict:
    """解析配置文件（带缓存）"""
    return yaml.safe_load(config_path.read_text())
```

#### 避免重复读取文件

使用文件哈希作为缓存键：

```python
@file_cache(key_func=lambda path: hashlib.md5(path.read_bytes()).hexdigest())
def analyze_code(path: Path) -> AnalysisResult:
    """分析代码（只在文件变更时重新分析）"""
    ...
```

#### 使用摘要代替全文

对于大型文件，存储和传输摘要而非全文：

```python
def get_file_summary(file_path: Path) -> str:
    """获取文件摘要"""
    content = file_path.read_text()
    # 如果文件很小，返回全文
    if len(content) < 1000:
        return content
    # 否则返回摘要
    return summarize_content(content)
```

---

## 实现指南

### Token 监控

实时监控 token 使用情况：

```python
class TokenMonitor:
    """Token 使用监控器"""

    def __init__(self, limit: int = 100000):
        self.limit = limit
        self.usage = 0
        self.warning_threshold = int(limit * 0.7)

    def add_tokens(self, count: int) -> None:
        """增加 token 计数"""
        self.usage += count
        if self.usage >= self.warning_threshold:
            self.warn_threshold_exceeded()

    def warn_threshold_exceeded(self) -> None:
        """警告阈值超出"""
        usage_pct = self.usage / self.limit * 100
        print(f"⚠️ Token 使用率: {usage_pct:.1f}%")

    def should_compress(self) -> bool:
        """判断是否需要压缩"""
        return self.usage >= self.warning_threshold
```

### 自动清理机制

达到阈值时自动清理过时上下文：

```python
def auto_compress_context(
    messages: List[Message],
    token_monitor: TokenMonitor,
) -> List[Message]:
    """自动压缩上下文"""
    if not token_monitor.should_compress():
        return messages

    # 保留最近 N 轮对话
    recent_messages = messages[-10:]

    # 压缩较早的对话为摘要
    older_messages = messages[:-10]
    summary = compress_messages_to_summary(older_messages)

    # 返回压缩后的消息列表
    return [summary] + recent_messages
```

### 分级加载策略

实现三级文件加载：

```python
class FileLoader:
    """分级文件加载器"""

    def __init__(self):
        self.l1_cache: Dict[Path, str] = {}  # 热数据
        self.l2_cache: Dict[Path, str] = {}  # 温数据（摘要）
        self.l3_storage: Dict[Path, str] = {}  # 冷数据（索引）

    def load_file(self, path: Path, level: str = "auto") -> str:
        """加载文件"""
        if level == "auto":
            level = self._determine_load_level(path)

        if level == "l1":
            return self._load_full(path)
        elif level == "l2":
            return self._load_summary(path)
        else:
            return self._load_index(path)

    def _determine_load_level(self, path: Path) -> str:
        """自动判断加载级别"""
        # 基于文件大小、访问频率、相关性等判断
        ...
```

---

## 配置建议

在 `config.yaml` 中添加以下配置：

```yaml
# Context Window 管理配置
context:
  # 最大历史 token 数
  max_history_tokens: 8000

  # 压缩触发阈值（使用率百分比）
  compression_threshold: 0.7

  # 缓存策略：aggressive | moderate | minimal
  cache_strategy: moderate

  # 压缩方式：summary | extract | archive
  compression_method: summary

  # 信息保留优先级
  retention_priority:
    - "current_task"
    - "decisions"
    - "errors"
    - "context"

  # 自动清理开关
  auto_cleanup: true

  # Token 监控告警阈值
  warning_threshold: 0.7
  critical_threshold: 0.9
```

---

## 最佳实践

### 对话开始时

1. 明确任务范围和边界
2. 识别可能需要的参考文档
3. 设置合理的 token 预算

### 对话进行中

1. 定期检查 token 使用情况
2. 及时归档已完成任务
3. 提取并记录关键决策

### 对话结束时

1. 生成完整的对话摘要
2. 保存重要的决策和约束
3. 清理临时缓存

---

## 工具支持

### Context 诊断命令

```bash
# 查看当前 token 使用情况
ac-context status

# 手动压缩上下文
ac-context compress

# 查看缓存统计
ac-context cache-stats

# 清理过期缓存
ac-context cleanup
```

### 日志输出

```
[Context] Token usage: 6500/100000 (6.5%)
[Context] Cache hit rate: 85%
[Context] Compression not needed
```

---

**相关参考**:
- `context-optimization.md`
- [scripts/cache.py](../scripts/cache.py)
- [scripts/logger.py](../scripts/logger.py)
