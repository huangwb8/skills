---
name: backend-specialist
description: "后端开发专家。精通 Node.js/Python/Go/Rust 等后端技术栈，专注于 API 设计、数据库优化、认证授权、微服务架构和性能调优。Use when building or refactoring backend services, designing APIs, modeling data layers, or adding authentication/authorization to an application."
metadata:
  short-description: 后端开发与系统架构
  keywords:
    - backend-specialist
    - 后端开发
    - API 设计
    - Node.js
    - Python
    - Go
    - Rust
    - 数据库
    - 微服务
    - 认证授权
    - 性能优化
  category: 后端开发
  author: Bensz Conan
  platform: Claude Code | OpenAI Codex | ChatGPT
---

# Backend Specialist - 后端开发专家

目标：设计并实现可靠的后端服务（API/数据层/鉴权/可观测性），在正确性优先的前提下优化性能与可维护性。

为满足社区推荐的 `SKILL.md` 500 行以内约束：详细技术栈对比、长示例代码与模板已下沉到 `awesome-code/agents/backend-specialist/references/legacy-skill-full.md`。

## 何时使用

- 设计/实现 API、服务层、数据库模型、任务队列、微服务拆分
- 需要鉴权/授权设计（JWT/RBAC/SSO 等）
- 需要性能优化（缓存、连接池、查询优化）或稳定性治理

## 输入

- 业务目标与 SLA：延迟、吞吐、可用性
- 数据模型与一致性要求：强一致/最终一致、事务边界
- 运行环境：单体/容器/K8s、数据库类型、缓存组件
- 安全约束：权限模型、审计需求、敏感数据

## 输出

- API 设计（端点、请求/响应 schema、错误码、幂等性策略）
- 数据层方案（表结构/索引/迁移策略/查询计划建议）
- 鉴权/授权方案（token 生命周期、权限模型、越权防护）
- 性能与可观测性骨架（缓存/限流/日志/指标/追踪）

## 工作流

1. 澄清契约
   - 明确资源模型、边界条件、错误语义（4xx/5xx）
   - 决策：REST（资源型 CRUD）vs GraphQL（多实体聚合查询）vs gRPC（内部高吞吐服务间调用）
   - 输出物：端点清单 + 请求/响应 schema + 错误码映射表
   - **检查点**：端点清单经确认后方可进入数据层设计

2. 设计数据层
   - 先建模再写 API；提前定义索引与热点路径
   - 决策树：
     - 强一致 + 复杂关联查询 → PostgreSQL/MySQL（schema-first，先定义 CREATE TABLE + 索引策略）
     - 文档型 / 灵活 schema → MongoDB（定义 JSON Schema 验证 + 复合索引）
     - 高频键值读写 → Redis 作缓存层；持久化仍需后端数据库
   - 索引规则：WHERE/JOIN 字段必建索引；复合索引遵循最左前缀；覆盖索引优先
   - **检查点**：用 `EXPLAIN` 验证热点查询计划，确认无全表扫描后进入服务层

3. 实现服务层
   - 输入验证 → 权限校验 → 业务逻辑 → 持久化 → 输出规范化
   - 鉴权选型：无状态 API → JWT（短 access + 长 refresh）；多系统 SSO → OAuth2/OIDC；内部服务 → mTLS
   - 权限模型：简单角色 → RBAC；细粒度资源级 → ABAC/策略引擎
   - **检查点**：所有端点通过权限校验测试（含越权场景）后进入性能优化

4. 可靠性与性能
   - 缓存策略：读多写少 → Cache-Aside + TTL；一致性要求高 → Write-Through
   - N+1 排查：ORM 批量预加载（`eager loading`）或手写 JOIN
   - 限流/重试/熔断（按需）：对外 API 限流（令牌桶）；下游调用加指数退避重试 + 熔断
   - **检查点**：核心接口延迟 < SLA 目标，连接池无泄漏

5. 可观测性
   - 结构化日志（含 request_id）、核心指标（QPS/P99/错误率）、关键告警
   - 最低要求：每个请求可通过 request_id 端到端追踪

## 示例

**场景**：为电商系统设计订单服务

1. **澄清契约**：REST API — `POST /orders`（创建）、`GET /orders/{id}`（查询）、`PATCH /orders/{id}/cancel`（取消）；幂等键 `Idempotency-Key` 头防重复提交
2. **数据层**：PostgreSQL — `orders` 表含 `user_id`（索引）、`status`（枚举）、`created_at`（索引，用于分页）；`order_items` 表外键关联；`EXPLAIN` 确认 `WHERE user_id = ? ORDER BY created_at DESC` 走索引
3. **服务层**：JWT 鉴权 + RBAC（普通用户只能操作自己的订单）；输入用 JSON Schema 验证
4. **性能**：订单详情 Cache-Aside（TTL 5min，写时失效）；商品库存扣减用数据库行锁避免超卖
5. **可观测性**：每笔订单操作记录 `request_id` + `order_id`，P99 延迟 < 200ms 告警

## 质量门槛

- 所有外部输入必须验证（含路径/文件/URL）
- 授权必须服务端强制执行
- 热点查询必须有索引与可解释的性能证据
- 关键路径必须有最小回归测试/验证步骤

## 与 bensz-collect-bugs 的协作约定

- 因本 skill 设计缺陷导致的 bug，先用 `bensz-collect-bugs` 规范记录到 `~/.bensz-skills/bugs/`，不要直接修改用户本地已安装的 skill 源码；若有 workaround，先记 bug，再继续完成任务。
- 只有用户明确要求"report bensz skills bugs"等公开上报时，才用本地 `gh` 上传新增 bug 到 `huangwb8/bensz-bugs`；不要 pull / clone 整个仓库。

