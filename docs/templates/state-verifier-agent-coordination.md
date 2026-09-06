<!-- Template-ID: state-verifier-agent-coordination; Template-Version: 1; Sync-Policy: reference -->

# State/Verifier 子 Agent 协作约定（条件性）

本约定仅用于**明确采用 State/Verifier 子 Agent 协作**的 Skill，在其 `## 控制（按需）` 中引用；不是公共硬约束，不并入 `skill-common-constraints.md`，不自动推广至普通 Skill。它是给执行 Skill 的 LLM 与宿主 Harness 的声明式任务契约，不是跨平台 API，也不要求 Kernel 管理子 Agent 生命周期。

- Skill 必须说明协作的触发阶段、角色、输入证据、禁止副作用和结果格式；没有明确采用时，Agent 不应自行增加子 Agent。
- State 默认由 Agent 在需要检查点时请求一次独立协助；连续性由状态文件、事件和证据保证，不由子 Agent 记忆保证。是否复用上下文由当前 Harness 自主决定，并必须向主 Agent 报告实际模式。
- Verifier 默认建议使用 2 个相互独立的子 Agent 并行检查同一快照；需要复核时才声明串行轮次。并行/串行是执行意图，不是 Kernel 的 spawn、线程或进程实现。
- 主 Agent 应将每个子 Agent 的任务边界、证据引用、输出格式和独立性要求说清楚；子 Agent 不修改业务产物、不伪造验证事件、不继续扩展子 Agent，除非 Skill 明确允许。
- Harness 负责创建、隔离、并行、等待和回收子 Agent。Skill 不得假设某个平台的 API、host ID、沙箱参数或关闭机制；不支持子 Agent 时必须显式报告 fallback，不得声称完成了独立并行验证。
- 主 Agent 汇总结果时不得用多数票抹掉 required Verifier 的失败、缺失或不确定；最终仍通过既有 Verifier/Gate 和 State 迁移契约验收。

建议在 `config.yaml` 中保留机器可读的协作意图（如 `mode`、`count`、`rounds`），但这些字段只供 LLM/Harness 理解与报告，不构成 Kernel 调度协议。

示例：

```yaml
agent_assistance:
  verifier:
    enabled: true
    mode: parallel
    count: 2
    independent: true
    share_previous_results: false
```

执行 Skill 的 Agent 应把这段意图转换为当前 Harness 支持的原生操作；如果 Harness 不支持独立子 Agent，则返回 `single_agent_fallback`，说明实际执行方式、未满足的独立性和人工复核建议。不得仅凭配置字段声称已经产生了两个独立 Agent。
