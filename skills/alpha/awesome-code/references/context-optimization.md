# 上下文优化策略参考文档

## 核心问题

在长对话中，AI 代理的上下文窗口（context window）是有限的资源。不加以管理，会导致：

- **性能下降**：响应变慢，token 消耗增加
- **准确性降低**：关键信息被淹没，出现幻觉
- **成本增加**：更多的 token 意味着更高的 API 调用成本

## 上下文失败模式

### 失败模式 1：Lost-in-Middle（中间迷失）

**现象**：开头和结尾的信息能被记住，但中间的信息被遗忘。

**原因**：注意力的"U 型曲线"，AI 对中间内容的关注度降低。

**解决方案**：
- 关键信息放在开头或结尾
- 定期总结中间内容
- 使用引用而非重复内容

### 失败模式 2：Context Poisoning（上下文中毒）

**现象**：冲突或误导信息干扰 AI 判断。

**原因**：过时的信息、矛盾的指令、错误的假设。

**解决方案**：
- 明确标记过时信息（`[已废弃]`）
- 使用版本标记
- 清理冲突指令

### 失败模式 3：Distraction（注意力分散）

**现象**：无关信息浪费 token，降低相关性。

**原因**：加载了不必要的文件、过长的日志、冗余的代码。

**解决方案**：
- 只加载相关文件
- 使用摘要代替全文
- 清理无关内容

### 失败模式 4：Context Clash（上下文冲突）

**现象**：多个信息源提供冲突的信息。

**原因**：不同文件中的矛盾描述、更新不一致。

**解决方案**：
- 建立信息优先级
- 明确最后更新时间
- 冲突解决策略

## 优化策略

### 策略 1：压缩（Compression）

#### 压缩方式

| 方式 | 适用场景 | 示例 |
|------|---------|------|
| **总结** | 长文本、历史对话 | 将 100 行对话总结为 10 条要点 |
| **提取** | 关键决策、配置 | 提取 5 个关键参数 |
| **归档** | 已完成的任务 | 将已完成任务移至归档文件 |

#### 总结模板

```markdown
## 对话总结（截至 {timestamp}）

### 已完成的任务
1. ✅ 实现用户认证功能（2026-01-15 14:30）
2. ✅ 修复登录超时 Bug（2026-01-15 15:45）
3. ✅ 添加单元测试（2026-01-15 16:20）

### 关键决策
- 使用 JWT 而非 Session 认证
- 数据库选择 PostgreSQL 而非 MongoDB
- 测试框架选择 pytest

### 当前状态
正在实现：用户权限管理模块
进度：60%

### 遗留问题
1. 权限粒度设计待确认
2. RBAC 或 ABAC 模式未定

### 下一步行动
- 完成权限管理模块
- 编写权限测试
- 更新 API 文档
```

### 策略 2：掩码（Masking）

#### 按需加载

```markdown
## 核心说明

[简短的工作流程]

## 详细参考

详细信息请参阅：
- TDD 最佳实践：`tdd-best-practices.md`
- 调试指南：`debugging-systematic.md`
```

**原理**：SKILL.md 只包含核心信息，详细内容放在 references/ 中，按需加载。

#### 延迟加载

```python
# 不在上下文中立即加载大文件
def load_when_needed(file_path):
    """只有在实际需要时才加载"""
    if is_needed(file_path):
        return read_file(file_path)
    return None
```

### 策略 3：缓存（Caching）

#### 缓存策略

| 策略 | 描述 | 适用场景 |
|------|------|---------|
| **激进缓存** | 最大化重用，最小化重复读取 | 大型项目、有限 token |
| **适度缓存** | 平衡重用和新鲜度 | 一般场景 |
| **最小缓存** | 几乎不缓存，始终重新读取 | 快速变化的项目 |

#### 缓存实现

```python
# 简单缓存实现
_context_cache = {}

def get_file_content(file_path):
    """带缓存的文件读取"""
    if file_path in _context_cache:
        return _context_cache[file_path]

    content = read_file(file_path)
    _context_cache[file_path] = content
    return content

def invalidate_cache(file_path=None):
    """缓存失效"""
    if file_path:
        _context_cache.pop(file_path, None)
    else:
        _context_cache.clear()
```

### 策略 4：优先级管理（Prioritization）

#### 信息优先级

```
P0 - 必须保留（当前任务、关键决策）
P1 - 重要（配置、API 定义）
P2 - 可选（示例、注释）
P3 - 低优先（历史日志、调试信息）
```

#### 优先级示例

```markdown
## 优先级管理

### P0 - 当前任务
- 正在实现：用户权限管理

### P1 - 关键配置
- JWT_SECRET: ***
- DB_NAME: users_db

### P2 - 参考
- 权限设计文档：references/auth-design.md

### P3 - 历史
- 2026-01-14：完成认证模块（已归档）
```

## 实用技巧

### 技巧 1：分阶段处理

```
阶段 1：需求分析（只加载需求文档）
   ↓
阶段 2：设计（加载设计文档，卸载需求）
   ↓
阶段 3：实现（加载代码，卸载设计）
   ↓
阶段 4：测试（加载测试，卸载部分代码）
```

### 技巧 2：使用摘要代替全文

```python
# ❌ 加载整个配置文件
# （假设有 1000 行）

# ✅ 只加载需要的部分
config = load_config_section("database")
```

### 技巧 3：定期清理

```markdown
## 清理检查清单

每次完成一个任务后：
- [ ] 移除已完成的任务描述
- [ ] 归档历史对话
- [ ] 删除无关文件引用
- [ ] 更新当前状态
```

## 配置示例

### config.yaml 配置

```yaml
# 上下文优化配置
context:
  # 最大历史 token 数
  max_history_tokens: 8000

  # 压缩触发阈值（使用率达到 70% 时触发）
  compression_threshold: 0.7

  # 缓存策略
  cache_strategy: moderate  # aggressive | moderate | minimal

  # 压缩方式
  compression_method: summary  # summary | extract | archive

  # 信息保留优先级
  retention_priority:
    - "current_task"
    - "decisions"
    - "errors"
    - "context"

  # 自动清理
  auto_cleanup: true

  # 清理频率（每 N 轮对话）
  cleanup_frequency: 10
```

## 实战示例

### 示例 1：长对话压缩

```markdown
## 压缩前（5000 tokens）

[50 轮对话，包含详细讨论]

---

## 压缩后（500 tokens）

## 对话总结

### 已完成
1. ✅ 需求分析：用户认证系统
2. ✅ 技术选型：JWT + PostgreSQL
3. ✅ API 设计：/auth/login, /auth/register
4. ✅ 核心实现：认证服务

### 关键决策
- 使用 JWT 而非 Session（无状态）
- BCrypt 加密密码
- Token 有效期：24 小时

### 当前任务
正在实现：刷新 token 机制（进度 50%）

### 下一步
1. 完成刷新 token
2. 编写测试
3. 部署到测试环境
```

### 示例 2：按需加载参考文档

```markdown
## SKILL.md（核心信息，1000 tokens）

# Awesome Code

## 何时使用
[简要描述]

## 核心工作流
[概览]

## 详细参考

详细策略请参考：
- TDD 最佳实践：`tdd-best-practices.md`
- 调试指南：`debugging-systematic.md`

---

## references/tdd-best-practices.md（按需加载，3000 tokens）

# TDD 最佳实践

[详细的 TDD 指南]
```

## 监控与诊断

### 监控指标

```python
# 上下文使用监控
def monitor_context_usage():
    return {
        "total_tokens": count_tokens(),
        "usage_percentage": calculate_usage(),
        "compression_count": get_compression_count(),
        "cache_hit_rate": calculate_cache_hit_rate(),
    }
```

### 诊断检查清单

- [ ] 上下文使用率 < 80%
- [ ] 关键信息在开头或结尾
- [ ] 无明显的内容重复
- [ ] 引用文件正确加载
- [ ] 缓存命中率 > 50%

## 最佳实践

### 原则 1：渐进式信息披露

```
第一层：YAML frontmatter（name + description）
第二层：SKILL.md 核心内容
第三层：references/ 详细参考
```

### 原则 2：定期维护

- 每完成一个任务：清理一次
- 每 10 轮对话：压缩一次
- 每天开始：归档前一天的内容

### 原则 3：可观测性

- 记录压缩决策
- 记录缓存命中率
- 记录 token 使用趋势

## 参考资源

- [Context Engineering Skills (muratcankoylan)](https://github.com/VoltAgent/awesome-claude-skills)
- [Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Equipping Agents for the Real World with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
