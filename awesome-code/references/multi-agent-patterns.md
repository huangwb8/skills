# 多代理协调模式参考文档

## 核心概念

多代理协调是指将复杂任务分解为多个子任务，由专门的代理并行或协作完成，从而提升开发效率和系统可扩展性。

## 何时使用多代理协调

### 适用场景

✅ **适合使用多代理**：
- 多个独立的文件需要修改
- 不同模块的测试可以并行运行
- 需要同时分析和处理多个代码区域
- 大型重构涉及多个子系统
- 需要同时测试多个假设

❌ **不适合使用多代理**：
- 简单的单文件修改
- 线性依赖的任务序列
- 需要频繁同步的工作
- token 预算有限（多代理会增加 token 消耗）

## 协调模式

### 模式 1：编排器模式（Orchestrator）

**特点**：中央控制代理协调多个子代理

```
主代理（编排器）
├── 任务分解
├── 子代理分配
│   ├── 子代理 A：处理模块 X
│   ├── 子代理 B：处理模块 Y
│   └── 子代理 C：处理模块 Z
├── 结果收集与验证
└── 冲突解决与合并
```

**优势**：
- 集中控制，易于管理
- 结果聚合简单
- 适用于层级化任务

**示例**：

```python
# 主代理伪代码
def orchestrator_main():
    # 1. 任务分解
    modules = analyze_project_structure()
    tasks = decompose_tasks(modules)

    # 2. 并行分配
    agents = [spawn_agent(task) for task in tasks]

    # 3. 收集结果
    results = [agent.wait_for_result() for agent in agents]

    # 4. 合并与验证
    merged = merge_and_validate(results)

    return merged
```

### 模式 2：点对点模式（Peer-to-Peer）

**特点**：代理之间直接通信，无中央控制

```
子代理 A ←→ 子代理 B
    ↕         ↕
子代理 C ←→ 子代理 D
```

**优势**：
- 无单点故障
- 高度并行化
- 适合分布式任务

**示例场景**：代码库中的模块间相互引用检查

### 模式 3：流水线模式（Pipeline）

**特点**：代理按顺序处理，每个代理负责特定阶段

```
输入 → 子代理 A → 子代理 B → 子代理 C → 输出
       （解析）   （分析）   （生成）
```

**优势**：
- 清晰的职责分离
- 易于调试和监控
- 适合顺序处理任务

**示例**：代码审查流水线

1. 代理 A：静态分析
2. 代理 B：安全扫描
3. 代理 C：性能分析
4. 代理 D：生成报告

## 任务分解策略

### 策略 1：按模块分解

```
项目结构：
src/
├── auth/       → 子代理 A
├── database/   → 子代理 B
├── api/        → 子代理 C
└── utils/      → 子代理 D
```

**适用**：模块化良好的项目

### 策略 2：按功能分解

```
任务：实现用户注册功能
├── 前端表单    → 子代理 A
├── API 端点    → 子代理 B
├── 数据库模型  → 子代理 C
└── 测试用例    → 子代理 D
```

**适用**：跨功能的完整特性开发

### 策略 3：按文件类型分解

```
代码库：
├── *.py      → Python 代理
├── *.js      → JavaScript 代理
├── *.sql     → SQL 代理
└── *.md      → 文档代理
```

**适用**：多语言项目

## 冲突解决策略

### 冲突类型

| 冲突类型 | 示例 | 解决策略 |
|---------|------|---------|
| **命名冲突** | 两个代理创建同名函数 | 重命名（加前缀/后缀） |
| **逻辑冲突** | 对同一功能有不同的实现 | 投票机制或人工仲裁 |
| **依赖冲突** | 模块 A 和 B 需要不同版本的依赖 | 依赖隔离或统一版本 |
| **结构冲突** | 不同的代码组织方式 | 制定统一标准 |

### 解决策略

#### 策略 1：人工仲裁（Ask）

```
冲突检测 → 暂停任务 → 展示冲突 → 用户选择 → 继续执行
```

**适用**：重要决策、高风险变更

#### 策略 2：自动中止（Abort）

```
冲突检测 → 记录冲突 → 停止执行 → 生成报告
```

**适用**：不可自动解决的冲突

#### 策略 3：自动恢复（Resume）

```
冲突检测 → 应用预设规则 → 继续执行 → 记录日志
```

**适用**：常见、低风险的冲突

## 结果聚合

### 聚合方式

#### 方式 1：串行聚合

```python
def aggregate_results_serial(results):
    """逐个合并结果，冲突时使用后者"""
    final = {}
    for result in results:
        final.update(result)
    return final
```

#### 方式 2：智能合并

```python
def aggregate_results_smart(results):
    """智能合并，检测并解决冲突"""
    final = {}
    for result in results:
        for key, value in result.items():
            if key in final:
                # 检测冲突
                if final[key] != value:
                    # 应用解决策略
                    final[key] = resolve_conflict(final[key], value)
            else:
                final[key] = value
    return final
```

#### 方式 3：投票机制

```python
def aggregate_results_voting(results):
    """多个代理投票决定"""
    from collections import Counter

    decisions = {}
    for result in results:
        for key, value in result.items():
            if key not in decisions:
                decisions[key] = []
            decisions[key].append(value)

    # 选择最常见的决定
    final = {}
    for key, values in decisions.items():
        final[key] = Counter(values).most_common(1)[0][0]

    return final
```

## 性能优化

### 优化策略

1. **任务独立性**：确保子任务间无依赖
2. **批量启动**：一次性启动所有代理
3. **结果缓存**：避免重复计算
4. **超时控制**：防止单个代理阻塞整体

### 超时处理

```python
def run_with_timeout(agent, timeout):
    """带超时的代理执行"""
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Agent timeout after {timeout}s")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        result = agent.run()
        signal.alarm(0)  # 取消超时
        return result
    except TimeoutError:
        return None  # 或返回默认值
```

## 错误处理

### 错误传播

```python
def agent_with_error_handling(agent):
    """带错误处理的代理执行"""
    try:
        result = agent.run()
        return {"status": "success", "result": result}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "agent": agent.name,
            "traceback": traceback.format_exc()
        }
```

### 部分失败处理

```python
def handle_partial_failure(results):
    """处理部分代理失败的情况"""
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] == "error"]

    if failures:
        logger.warning(f"{len(failures)} agents failed:")
        for f in failures:
            logger.warning(f"  {f['agent']}: {f['error']}")

    # 决定是否继续
    if len(successes) >= len(results) * 0.5:  # 至少一半成功
        return merge_results(successes)
    else:
        raise RuntimeError("Too many agents failed")
```

## 实战示例

### 示例 1：并行测试多个模块

```python
# 主代理
def parallel_test_modules(modules):
    """并行测试多个模块"""

    # 任务分解
    tasks = [
        {"agent": "test-runner", "module": module}
        for module in modules
    ]

    # 并行执行
    agents = [spawn_agent(task) for task in tasks]
    results = [agent.wait_for_result() for agent in agents]

    # 聚合结果
    test_report = aggregate_test_results(results)

    return test_report
```

### 示例 2：分布式代码审查

```python
# 主代理
def distributed_code_review(files):
    """分布式代码审查"""

    # 按文件类型分组
    groups = group_files_by_type(files)

    # 为每组分配一个代理
    agents = []
    for file_type, file_list in groups.items():
        task = {
            "agent": "code-reviewer",
            "type": file_type,
            "files": file_list
        }
        agents.append(spawn_agent(task))

    # 收集审查结果
    reviews = [agent.wait_for_result() for agent in agents]

    # 生成统一报告
    final_report = merge_review_reports(reviews)

    return final_report
```

## 最佳实践

### 设计原则

1. **明确边界**：清晰定义每个代理的职责
2. **最小依赖**：代理间应尽量独立
3. **可恢复性**：支持失败重试和状态恢复
4. **可观测性**：记录代理的决策和过程

### 配置建议

```yaml
# config.yaml 中的多代理配置
multi_agent:
  # 最大并行任务数
  max_parallel_tasks: 5

  # 单任务超时（秒）
  timeout_per_task: 300

  # 重试次数
  max_retries: 2

  # 结果聚合策略
  result_aggregation: auto  # auto | manual | voting

  # 冲突解决策略
  conflict_resolution: ask  # ask | abort | resume | current | incoming
```

## 检查清单

使用多代理协调前确认：

- [ ] 任务可分解为独立的子任务
- [ ] 子任务间无强依赖
- [ ] 有明确的聚合策略
- [ ] 定义了冲突解决机制
- [ ] 设置了合理的超时时间
- [ ] 考虑了部分失败的后果
- [ ] 有足够的 token 预算

## 参考资源

- [Multi-Agent Coordination (obra/dispatching-parallel-agents)](https://github.com/VoltAgent/awesome-claude-skills)
- [Subagent Driven Development (obra/subagent-driven-development)](https://github.com/VoltAgent/awesome-claude-skills)
- [Context Engineering Skills (muratcankoylan)](https://github.com/VoltAgent/awesome-claude-skills)
