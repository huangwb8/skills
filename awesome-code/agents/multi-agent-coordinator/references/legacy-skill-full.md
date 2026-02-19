---
name: multi-agent-coordinator
description: Use when executing implementation plans with independent tasks - dispatches fresh subagent for each task with code review between tasks, enabling fast iteration with quality gates. Supports orchestrator, peer-to-peer, and pipeline coordination modes.
metadata:
  short-description: 多代理协调与编排
  keywords:
    - 多代理
    - 协调器
    - 并行处理
    - 任务编排
    - 工作流
    - 任务分发
    - 结果聚合
    - subagent-driven-development
    - coordination
  category: 架构设计
  author: 社区最佳实践
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Multi-Agent Coordinator - 多代理协调专家

## 子代理驱动开发模式

### 核心原则

**每个任务的全新子代理 + 任务间代码审查 = 高质量，快速迭代**

```
┌─────────────────────────────────────────────────────────┐
│  加载计划 → 派遣子代理 → 审查工作 → 应用反馈 → 最终审查  │
└─────────────────────────────────────────────────────────┘
```

### vs. 其他模式

| 维度 | 子代理驱动 | 执行计划（并行会话） | 手动执行 |
|------|-----------|---------------------|---------|
| **上下文** | 相同会话（无上下文切换） | 不同会话（需交接） | 手动切换 |
| **子代理** | 每任务全新子代理（无上下文污染） | 共享子代理 | 无 |
| **代码审查** | 每任务后自动审查 | 无或手动 | 手动 |
| **迭代速度** | 快速（无人循环等待） | 慢（等待会话） | 最慢 |
| **质量保证** | 高（早期发现问题） | 中 | 低 |

### 工作流程

#### 1. 加载计划

读取计划文件，创建所有任务的 TodoWrite。

```markdown
## 任务清单

- [ ] Task 1: [Component A] - 创建文件并实现核心逻辑
- [ ] Task 2: [Component B] - 集成组件 A
- [ ] Task 3: [Component C] - 添加测试
- [ ] Task 4: [Documentation] - 更新文档
```

#### 2. 派遣子代理执行任务

对于每个任务，派遣**全新子代理**：

```
Task 工具（通用）：
description: "实施任务 N：[任务名称]"
prompt: |
  你正在实施 [plan-file] 中的任务 N。

  仔细阅读该任务。你的工作是：
  1. 精确实施任务指定的内容
  2. 编写测试（如果任务说遵循 TDD）
  3. 验证实施工作
  4. 提交你的工作
  5. 报告回来

  工作来自：[directory]
  报告：你实施了什么，你测试了什么，测试结果，更改的文件，任何问题
```

**子代理报告**工作摘要：
- ✅ 实施了什么功能
- ✅ 测试结果（通过/失败）
- ✅ 更改的文件列表
- ⚠️ 遇到的问题或疑问

#### 3. 审查子代理工作

派遣**代码审查者子代理**：

```
Task 工具（code-reviewer）：
description: "审查任务 N 的工作"
prompt: |
  使用 requesting-code-review/code-reviewer.md 中的模板

  WHAT_WAS_IMPLEMENTED: [来自子代理报告]
  PLAN_OR_REQUIREMENTS: [plan-file] 中的任务 N
  BASE_SHA: [任务前的提交]
  HEAD_SHA: [当前提交]
  DESCRIPTION: [任务摘要]
```

**代码审查者返回**：
- ✅ **优势**：做得好的地方
- ⚠️ **问题**：Critical（阻塞）、Important（重要）、Minor（次要）
- 📊 **评估**：总体质量评分

#### 4. 应用审查反馈

**如果发现问题**：
- 🔴 **Critical 问题**：立即修复
- 🟡 **Important 问题**：下一任务前修复
- 🟢 **Minor 问题**：记录，稍后处理

**如果需要，派遣后续子代理**：
```
"修复代码审查中的问题：[问题列表]"
```

#### 5. 标记完成，下一任务

- 在 TodoWrite 中标记任务为完成
- 移动到下一任务
- 重复步骤 2-5

#### 6. 最终审查

所有任务完成后，派遣**最终代码审查者**：
- 审查整个实施
- 检查所有计划要求满足
- 验证整体架构

#### 7. 完成开发

最终审查通过后：
- 宣布："我正在使用 finishing-a-development-branch 技能完成此工作"
- **必需子技能**：使用 finishing-a-development-branch

### 优势

- **vs. 手动执行**：子代理自然遵循 TDD
- **vs. 执行计划**：相同会话（无交接）、连续进步（无等待）、自动审查检查点

---

## 核心理念

**多代理系统** 通过协调专业化的子代理，高效处理复杂任务：

```
┌─────────────────────────────────────────────────────────┐
│  任务分解 → 代理分配 → 并行执行 → 结果聚合 → 冲突解决  │
└─────────────────────────────────────────────────────────┘
```

**核心价值**：
- ✅ **并行加速**：多个代理同时工作
- ✅ **专业分工**：每个代理专注特定领域
- ✅ **可扩展性**：轻松添加新代理
- ✅ **容错性**：单个代理失败不影响整体

---

## 何时使用本技能

在以下场景时激活：

- 大型项目开发
- 需要同时处理多个独立任务
- 不同模块可以并行开发
- 复杂重构涉及多个子系统
- 需要跨领域专业知识

---

## 协调模式

### 1. 编排器模式（Orchestrator）

**中央控制代理**协调多个子代理：

```
┌─────────────────────────────────────────────┐
│         主代理（编排器）                      │
│  - 任务分解                                  │
│  - 代理分配                                  │
│  - 结果聚合                                  │
│  - 冲突解决                                  │
└──────────┬───────────────────┬──────────────┘
           │                   │
    ┌──────▼──────┐     ┌─────▼──────┐
    │ 子代理 A    │     │ 子代理 B   │
    │ (前端专家)  │     │ (后端专家) │
    └─────────────┘     └────────────┘
```

**适用场景**：
- 任务需要严格协调
- 子代理间有依赖关系
- 需要全局视图

**示例**：

```typescript
interface Orchestrator {
  // 分解任务
  decompose(task: ComplexTask): SubTask[];

  // 分配代理
  assign(subTask: SubTask): Agent;

  // 执行协调
  async coordinate(task: ComplexTask): Promise<Result>;
}

class WebAppOrchestrator implements Orchestrator {
  private agents: Map<string, Agent>;

  constructor() {
    this.agents = new Map([
      ['frontend', new FrontendSpecialist()],
      ['backend', new BackendSpecialist()],
      ['database', new DatabaseSpecialist()],
      ['devops', new DevOpsSpecialist()],
    ]);
  }

  decompose(task: ComplexTask): SubTask[] {
    return [
      { type: 'frontend', work: task.ui },
      { type: 'backend', work: task.api },
      { type: 'database', work: task.schema },
      { type: 'devops', work: task.deployment },
    ];
  }

  assign(subTask: SubTask): Agent {
    return this.agents.get(subTask.type)!;
  }

  async coordinate(task: ComplexTask): Promise<Result> {
    // 1. 分解任务
    const subTasks = this.decompose(task);

    // 2. 分配代理
    const assignments = subTasks.map(st => ({
      agent: this.assign(st),
      task: st
    }));

    // 3. 并行执行
    const results = await Promise.allSettled(
      assignments.map(({ agent, task }) => agent.execute(task))
    );

    // 4. 聚合结果
    return this.aggregate(results);
  }

  private aggregate(results: PromiseSettledResult<any>[]): Result {
    // 合并所有成功结果
    // 处理失败情况
    // 解决冲突
  }
}
```

### 2. 点对点模式（Peer-to-Peer）

**代理间直接通信**，无中央协调：

```
┌─────────────┐         ┌─────────────┐
│ 子代理 A    │◄───────►│ 子代理 B    │
│ (前端专家)  │  协商   │ (后端专家) │
└─────────────┘         └─────────────┘
       ▲                       ▲
       │                       │
       └───────┬───────────────┘
               │
         ┌─────▼─────┐
         │ 子代理 C   │
         │ (数据库)   │
         └───────────┘
```

**适用场景**：
- 任务相对独立
- 代理需要协商
- 去中心化架构

**示例**：

```typescript
class PeerAgent implements Agent {
  private peers: Map<string, PeerAgent>;

  async execute(task: Task): Promise<Result> {
    // 1. 检查自己能处理的部分
    const myPart = this.extractMyPart(task);

    // 2. 识别需要其他代理的部分
    const delegation = this.identifyDelegation(task);

    // 3. 与对等代理协商
    const peerResults = await Promise.all(
      delegation.map(d => this.delegateToPeer(d))
    );

    // 4. 整合结果
    return this.integrate(myPart, peerResults);
  }

  private async delegateToPeer(
    delegation: Delegation
  ): Promise<Result> {
    const peer = this.peers.get(delegation.targetPeer);
    return peer?.execute(delegation.task);
  }
}
```

### 3. 流水线模式（Pipeline）

**顺序处理**，每个代理处理任务的一个阶段：

```
输入 ──► [代理 A] ──► [代理 B] ──► [代理 C] ──► 输出
         阶段1        阶段2        阶段3
```

**适用场景**：
- 任务有明显阶段
- 每个阶段依赖前一阶段
- 数据转换流

**示例**：

```typescript
class PipelineAgent implements Agent {
  private stages: Agent[];

  constructor(stages: Agent[]) {
    this.stages = stages;
  }

  async execute(task: Task): Promise<Result> {
    let current = task;

    for (const stage of this.stages) {
      try {
        const result = await stage.execute(current);

        // 传递到下一阶段
        current = result.nextStage || result;

      } catch (error) {
        // 阶段失败处理
        return this.handleStageError(error, stage, current);
      }
    }

    return current as Result;
  }
}

// 使用示例
const reviewPipeline = new PipelineAgent([
  new SecurityReviewer(),     // 安全审查
  new PerformanceReviewer(),  // 性能审查
  new StyleReviewer(),        // 代码风格审查
  new DocumentationReviewer() // 文档审查
]);
```

---

## 任务分配策略

### 基于能力的分配

```typescript
interface Capability {
  domain: string;      // 领域（前端、后端等）
  expertise: number;   // 专精度（0-1）
  availability: number; // 可用性（0-1）
}

class CapabilityBasedAllocator {
  private agents: Map<string, { agent: Agent; capability: Capability }>;

  allocate(task: Task): Agent {
    const candidates = this.findCandidates(task);

    // 评分排序
    const scored = candidates.map(c => ({
      agent: c.agent,
      score: this.score(c.capability, task)
    }));

    scored.sort((a, b) => b.score - a.score);

    return scored[0].agent;
  }

  private score(capability: Capability, task: Task): number {
    // 领域匹配度
    const domainMatch = capability.domain === task.domain ? 1 : 0;

    // 专精度权重
    const expertise = capability.expertise;

    // 可用性权重
    const availability = capability.availability;

    // 综合评分
    return (domainMatch * 0.5) + (expertise * 0.3) + (availability * 0.2);
  }
}
```

### 基于负载的分配

```typescript
class LoadBalancingAllocator {
  private agents: Map<string, { agent: Agent; load: number }>;

  allocate(task: Task): Agent {
    // 找到负载最低的代理
    const sorted = Array.from(this.agents.values())
      .sort((a, b) => a.load - b.load);

    return sorted[0].agent;
  }

  recordCompletion(agent: Agent, task: Task) {
    const entry = this.agents.get(agent.id);
    if (entry) {
      entry.load -= task.weight;
    }
  }
}
```

---

## 结果聚合

### 结果合并策略

```typescript
interface AggregationStrategy {
  aggregate(results: Result[]): Result;
}

// 1. 追加策略（结果独立）
class AppendAggregation implements AggregationStrategy {
  aggregate(results: Result[]): Result {
    return {
      success: results.every(r => r.success),
      data: results.flatMap(r => r.data),
      errors: results.flatMap(r => r.errors || []),
    };
  }
}

// 2. 合并策略（结果可合并）
class MergeAggregation implements AggregationStrategy {
  aggregate(results: Result[]): Result {
    return {
      success: results.every(r => r.success),
      data: results.reduce((acc, r) => ({ ...acc, ...r.data }), {}),
      errors: results.flatMap(r => r.errors || []),
    };
  }
}

// 3. 覆盖策略（后者覆盖前者）
class OverrideAggregation implements AggregationStrategy {
  aggregate(results: Result[]): Result {
    // 从后往前，后者覆盖前者
    return results.reduceRight((acc, r) => ({
      ...r,
      ...acc,
      errors: [...(r.errors || []), ...(acc.errors || [])]
    }));
  }
}
```

---

## 冲突解决

### 冲突检测

```typescript
interface Conflict {
  type: 'modification' | 'deletion' | 'addition';
  file: string;
  agents: string[];  // 冲突涉及的代理
  content: any;
}

class ConflictDetector {
  detect(results: Map<string, Result>): Conflict[] {
    const conflicts: Conflict[] = [];
    const fileMap = new Map<string, Map<string, any>>();

    // 按文件分组
    for (const [agentId, result] of results) {
      for (const [file, content] of result.files) {
        if (!fileMap.has(file)) {
          fileMap.set(file, new Map());
        }
        fileMap.get(file)!.set(agentId, content);
      }
    }

    // 检测冲突
    for (const [file, agents] of fileMap) {
      if (agents.size > 1) {
        conflicts.push({
          type: 'modification',
          file,
          agents: Array.from(agents.keys()),
          content: Array.from(agents.values())
        });
      }
    }

    return conflicts;
  }
}
```

### 冲突解决策略

```typescript
enum ConflictResolution {
  ASK = 'ask',        // 询问用户
  ABORT = 'abort',    // 中止执行
  RESUME = 'resume',  // 继续执行（忽略冲突）
  CURRENT = 'current', // 使用当前版本
  INCOMING = 'incoming', // 使用新版本
}

class ConflictResolver {
  async resolve(conflict: Conflict, strategy: ConflictResolution) {
    switch (strategy) {
      case ConflictResolution.ASK:
        return await this.askUser(conflict);

      case ConflictResolution.ABORT:
        throw new Error(`Conflict in ${conflict.file}, aborting`);

      case ConflictResolution.RESUME:
        return null; // 忽略冲突

      case ConflictResolution.CURRENT:
        return conflict.content[0]; // 使用第一个

      case ConflictResolution.INCOMING:
        return conflict.content[1]; // 使用第二个
    }
  }

  private async askUser(conflict: Conflict) {
    // 实现用户交互逻辑
    return null;
  }
}
```

---

## 错误处理

### 容错机制

```typescript
class FaultTolerantCoordinator {
  private maxRetries = 3;
  private timeout = 30000; // 30秒

  async executeWithErrorHandling(task: Task, agent: Agent): Promise<Result> {
    let lastError: Error;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        // 带超时的执行
        return await this.withTimeout(
          agent.execute(task),
          this.timeout
        );
      } catch (error) {
        lastError = error;
        console.warn(`Attempt ${attempt} failed:`, error);

        // 判断是否可重试
        if (!this.isRetryable(error)) {
          break;
        }

        // 指数退避
        await this.backoff(attempt);
      }
    }

    // 所有重试都失败
    return {
      success: false,
      errors: [lastError.message]
    };
  }

  private isRetryable(error: Error): boolean {
    // 网络错误、超时等可重试
    return error instanceof NetworkError
      || error instanceof TimeoutError;
  }

  private async backoff(attempt: number) {
    const delay = Math.pow(2, attempt) * 1000; // 指数退避
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  private async withTimeout<T>(
    promise: Promise<T>,
    timeout: number
  ): Promise<T> {
    return Promise.race([
      promise,
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new TimeoutError()), timeout)
      )
    ]);
  }
}
```

---

## 最佳实践

### 协调器设计清单

- [ ] 任务分解合理
- [ ] 代理职责清晰
- [ ] 并行执行安全
- [ ] 结果聚合正确
- [ ] 冲突处理完善
- [ ] 错误处理健壮
- [ ] 超时机制配置
- [ ] 进度可观测

### 代理设计清单

- [ ] 单一职责
- [ ] 接口标准化
- [ ] 状态独立
- [ ] 幂等操作
- [ ] 错误报告
- [ ] 超时控制

---

## 相关参考

- [多代理协调模式](../references/multi-agent-patterns.md)
- [上下文优化策略](../references/context-optimization.md)
