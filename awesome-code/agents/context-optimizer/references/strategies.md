# 上下文优化策略 — 详细实现参考

本文档包含 context-optimizer 技能中各优化策略的详细实现代码和检测逻辑。供代理在需要深入理解实现细节时按需加载。

---

## 问题检测实现

### Lost-in-Middle 检测

```python
def detect_lost_in_middle(conversation: list) -> bool:
    """检测是否出现 lost-in-middle 问题"""
    # 1. 检查对话长度
    if len(conversation) < 10:
        return False

    # 2. 检查是否有重复提问
    questions = [msg for msg in conversation if '?' in msg]
    unique_questions = set(questions)
    if len(questions) > len(unique_questions) * 1.5:
        return True  # 存在重复提问

    # 3. 检查中间内容是否被引用
    middle_start = len(conversation) // 3
    middle_end = len(conversation) * 2 // 3
    middle_content = conversation[middle_start:middle_end]

    # 检查后续对话是否引用中间内容
    later_refs = sum(
        1 for msg in conversation[middle_end:]
        if any(keyword in msg for keyword in extract_keywords(middle_content))
    )

    if later_refs < len(middle_content) * 0.1:
        return True  # 中间内容被遗忘

    return False
```

### Context Poisoning 检测

```python
def detect_context_poisoning(conversation: list) -> list:
    """检测上下文污染"""
    conflicts = []

    # 1. 提取所有事实陈述
    facts = extract_facts(conversation)

    # 2. 检测矛盾
    for fact1, fact2 in combinations(facts, 2):
        if are_contradictory(fact1, fact2):
            conflicts.append({
                'type': 'contradiction',
                'fact1': fact1,
                'fact2': fact2,
                'severity': 'high'
            })

    # 3. 检测信息源冲突
    sources = group_by_source(facts)
    for source, source_facts in sources.items():
        if has_internal_conflicts(source_facts):
            conflicts.append({
                'type': 'source_conflict',
                'source': source,
                'severity': 'medium'
            })

    return conflicts
```

---

## 策略 1：压缩策略 — 完整实现

### 历史压缩器

```python
class ContextCompressor:
    """上下文压缩器"""

    def compress_history(
        self,
        conversation: list,
        max_tokens: int,
        retention_priority: list[str] = None
    ) -> list:
        """
        压缩对话历史

        Args:
            conversation: 对话历史
            max_tokens: 最大 token 数
            retention_priority: 保留优先级 ["current_task", "decisions", "errors"]

        Returns:
            压缩后的对话
        """
        priority = retention_priority or ["current_task", "decisions", "errors"]

        # 1. 分类消息
        categorized = self._categorize_messages(conversation)

        # 2. 按优先级保留
        retained = []
        current_tokens = 0

        for category in priority:
            messages = categorized.get(category, [])

            for msg in messages:
                tokens = self._count_tokens(msg)
                if current_tokens + tokens > max_tokens:
                    compressed = self._compress_message(msg)
                    if current_tokens + self._count_tokens(compressed) <= max_tokens:
                        retained.append(compressed)
                        current_tokens += self._count_tokens(compressed)
                else:
                    retained.append(msg)
                    current_tokens += tokens

        return retained

    def _categorize_messages(self, conversation: list) -> dict:
        """分类消息"""
        categories = {
            'current_task': [],
            'decisions': [],
            'errors': [],
            'context': []
        }

        for msg in conversation:
            if self._is_task_related(msg):
                categories['current_task'].append(msg)
            elif self._is_decision(msg):
                categories['decisions'].append(msg)
            elif self._is_error(msg):
                categories['errors'].append(msg)
            else:
                categories['context'].append(msg)

        return categories

    def _compress_message(self, message: str) -> str:
        """压缩单条消息"""
        key_points = extract_key_points(message)
        summary = summarize(key_points)
        return f"[摘要] {summary}"

    def _count_tokens(self, text: str) -> int:
        """估算 token 数量"""
        return len(text.split()) * 1.3  # 粗略估计
```

### 增量摘要器

```python
class IncrementalSummarizer:
    """增量摘要器"""

    def __init__(self, summary_interval: int = 10):
        self.summary_interval = summary_interval
        self.summaries = []

    def add_messages(self, messages: list) -> str:
        """添加消息并生成摘要"""
        if len(messages) % self.summary_interval == 0:
            summary = self._generate_summary(messages[-self.summary_interval:])
            self.summaries.append(summary)

        return "\n\n".join(self.summaries)

    def _generate_summary(self, messages: list) -> str:
        """生成消息摘要"""
        key_info = {
            'tasks': self._extract_tasks(messages),
            'decisions': self._extract_decisions(messages),
            'errors': self._extract_errors(messages),
            'outcomes': self._extract_outcomes(messages)
        }

        summary_parts = []
        if key_info['tasks']:
            summary_parts.append(f"任务: {', '.join(key_info['tasks'])}")
        if key_info['decisions']:
            summary_parts.append(f"决策: {', '.join(key_info['decisions'])}")
        if key_info['errors']:
            summary_parts.append(f"错误: {', '.join(key_info['errors'])}")
        if key_info['outcomes']:
            summary_parts.append(f"结果: {', '.join(key_info['outcomes'])}")

        return " | ".join(summary_parts)
```

---

## 策略 2：掩码策略 — 懒加载实现

```python
class LazyContextLoader:
    """懒加载上下文"""

    def __init__(self):
        self.loaded_references = {}
        self.reference_metadata = {}

    def load_reference(
        self,
        ref_name: str,
        force: bool = False
    ) -> str | None:
        """
        按需加载参考文档

        Args:
            ref_name: 参考文档名称
            force: 是否强制重新加载
        """
        if ref_name in self.loaded_references and not force:
            return self.loaded_references[ref_name]

        metadata = self.reference_metadata.get(ref_name)
        if not metadata:
            return None

        if self._should_load(metadata):
            content = self._load_from_disk(ref_name)
            self.loaded_references[ref_name] = content
            return content

        return None

    def _should_load(self, metadata: dict) -> bool:
        """判断是否应该加载"""
        relevance = metadata.get('relevance', 0)
        token_usage = metadata.get('token_usage', 0)
        return relevance > 0.7 or token_usage < 0.8
```

---

## 策略 3：缓存策略 — 智能缓存实现

```python
class SmartCache:
    """智能缓存系统"""

    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}

    def get(self, key: str) -> any:
        """获取缓存"""
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        return None

    def set(self, key: str, value: any, priority: int = 1):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            self._evict_low_priority()

        self.cache[key] = value
        self.access_count[key] = 0

    def _evict_low_priority(self):
        """淘汰低优先级缓存"""
        items = list(self.cache.items())
        items.sort(key=lambda x: self.access_count.get(x[0], 0) * x[1].get('priority', 1))

        if items:
            key_to_remove = items[0][0]
            del self.cache[key_to_remove]
            del self.access_count[key_to_remove]

# 使用示例
cache = SmartCache()
code_structure = parse_code('main.py')
cache.set('code:main.py', code_structure, priority=2)

cached = cache.get('code:main.py')
if cached:
    use_cached_structure(cached)
```

---

## 最佳实践代码示例

### 分阶段处理

```python
# ❌ 一次性处理所有信息
def process_large_file(filename):
    content = read_file(filename)  # 可能很大
    result = analyze(content)
    return result

# ✅ 分阶段处理
def process_large_file(filename):
    # 第一阶段：获取结构
    structure = get_file_structure(filename)

    # 第二阶段：按需加载
    for section in structure.sections:
        content = load_section(filename, section)
        result = analyze_section(content)

    return aggregate_results(results)
```

### 渐进式信息披露

```python
# ❌ 一次性提供所有信息
def provide_context():
    return """
    这是项目的完整文档，包括架构、API、配置等...
    （可能 10000+ tokens）
    """

# ✅ 渐进式披露
def provide_context():
    return """
    项目概述：这是一个 Web 应用

    需要详细信息时，可查阅：
    - [架构设计](docs/architecture.md)
    - [API 文档](docs/api.md)
    - [配置指南](docs/config.md)

    （约 100 tokens）
    """
```
