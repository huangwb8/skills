---
entry_conditions: [bensz.workspace.ready]
invariants: [verifier-result-recorded, required-verifiers-pass, verifier-gate-allow]
transitions: [bensz.revision.ready]
---

# 正在准备和审查

原文、授权参数及当前候选正在准备或核对，尚未取得交付资格。进入时由唯一控制入口绑定原文和参数、建立 strict-v2 run/visit/attempt；不能用 legacy workspace-ready 冒充本阶段。

候选或证据变化后由入口启动新 attempt；未完成 handoff 或汇总未通过的审查都留在本态。三个子 Agent 的并行审查由 parallel-vibe 执行，主 Agent 独占实际润色；三份有效判断中至少两票 pass 才能通过。最多五轮；达到上限仍未通过时，由主 Agent 提交最后一轮草案并标明未通过原因，状态保持 working，不冒充 ready。此处没有检查组件，`mode: none` 只表示阶段；实际证据判断由配置中的 required Verifier 执行。

离开需要当前身份下完整 required 结果、Kernel 计算的允许 Gate 及同一证据哈希。上述机器 invariant 由 BSK 校验；原文、交付物和参数的字节重验由 Skill 控制入口执行，不依赖自然语言 invariant。异常不清空事件，不手写 ready。
