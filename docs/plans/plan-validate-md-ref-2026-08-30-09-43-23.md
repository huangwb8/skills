# validate-md-ref 状态机与验证器残余缺陷优化计划

## 通俗解释：究竟发生了什么

- **一句话说明：** 这次检查确实经过了状态机，也确实运行了链接和引用验证器，但账本仍可能把“别的运行的结果”当成当前运行的凭据，而且没有核对状态快照是否被篡改。
- **具体场景：** 状态机像门卫，验证器像检查包裹内容的仪器，事件账本像登记簿。本实例中门卫按 `input-ready → checking → reported → workspace.closed` 放行，登记簿也记录了两个验证结果和一个 Gate；但当前门卫对运行身份和快照完整性的核对还不够严格。
- **改变前后：** 现在只要 `attempt_id` 相同，旧 `run_id` 的结果可能满足新运行的离开检查；有人改写快照里的状态哈希，重放仍会照单全收。改进后必须绑定同一 `run_id + attempt_id`，并验证事件中的快照哈希与实际快照一致，否则状态转移或审计重放失败。

## 专业判断：问题在哪里

### 已确认的实例事实

- `validate-md-ref/log/meta-state.json` 和任务级 `log/events.ndjson` 显示状态转移、Verifier 结果和 Gate 均实际写入；因此状态机与 Verifier 不是“未生效”。
- 链接 Verifier 发现 24 条引用：11 条站内锚点有效，13 条外部 URL 因 DNS 不可观测而为 `unresolved`；Gate 为 `manual_review`，没有把网络故障判成确定性失效。
- `bsk rebuild` 能从 `state.transition` 事件投影 `skill_states`，说明当前版本已具备基本的状态事件化与回放能力；`packages/bensz-skill-kernel/tests` 的 85 项测试通过。

### 已复现的源代码缺陷

1. **运行身份校验可被部分身份绕过（Kernel，优先级 P1）。**
   `check_state_invariants()` 在调用方只提供 `attempt_id` 时，会筛选出所有相同尝试号的事件而忽略不同 `run_id`。实测旧运行写入 `verification.result`/`verification.gate` 后，新运行仅以同一 `attempt_id` 检查，`verifier-result-recorded` 返回空失败列表，允许错误放行。影响是重试或并发运行之间可能发生证据串线。

2. **状态快照哈希没有被验证（Kernel，优先级 P1）。**
   `reduce_events()` 直接把 `state.transition` 载荷中的 `snapshot_hash` 投影到 `skill_states`，没有读取快照或校验哈希；篡改事件载荷（在仍满足事件链哈希的情况下由有写权限的进程完成）或替换快照后，重放仍报告该哈希，无法发现快照漂移。当前 CLI 还在写入 `state_event_id`/`path` 后才落盘，哈希覆盖范围没有形成公开、可验证的契约。

### 契约风险（尚未在本实例触发，但应一并收敛）

- `SkillStateDeclaration` 只校验 Verifier ID 的格式和重复项，没有使用 registry 验证版本、存在性和 `required` 类型；不同适配器可能得到不一致的运行契约。
- `runtime.kernel.version` 目前不是 Kernel 状态声明的强制门禁；源码树优先路径可在配置声明不匹配时继续运行，版本漂移只能靠适配器自行处理。

## 要达到什么目标

- 每次状态转移只能消费同一 `run_id` 与 `attempt_id` 的验证证据；缺少或不完整的身份一律结构化拒绝。
- 事件回放和快照读取能够检测哈希不一致、缺失字段和快照漂移，并保留旧事件的只读兼容策略。
- Verifier requirements 与 Kernel 版本在进入业务执行前完成一次规范化校验，并让 Gate、metrics、事件和 manifest 使用同一份规范化契约。
- 保持本实例已验证的网络不确定性分类、SSRF 重定向防护、原文只读和 instruction-only 证据引用行为。

**不在本次处理范围：** 不在 Kernel 内实现引用真实性模型；不修改用户原始 Markdown；不恢复 Skill 侧第二套网络事实采集；不进行远程安装、发布或无关重构。

## 改进方向

### 强化运行身份与 Gate 绑定

将 `verifier-result-recorded` 的上下文契约固定为成对的 `run_id`、`attempt_id`（或明确的无历史事件例外），拒绝只给一半身份的调用。检查结果和 Gate 的事件顺序、运行身份、`result_event_id`、`result_refs`、Verifier canonical ID/版本及 Gate 的 `computed_by`；另提供独立的 `verifier-gate-allow` invariant，避免把“已记录”误解为“已通过”。

对普通用户而言，这意味着重试一次检查不会误用上一次检查的凭据，且 `manual_review`/`reject` 不会被状态门禁悄悄当成成功。

### 让状态快照真正可审计、可回放

定义快照哈希覆盖的稳定字段（排除哈希自身和明确的缓存字段），在写入前完成最终快照组装；事件记录、`meta-state.json` 和 `bsk rebuild` 采用同一规范。回放时校验事件链、状态转移前后关系、快照哈希和当前快照，发现漂移返回结构化错误而不是继续投影。保留 `state.transition` 的 skill/domain 分层，不能把领域状态硬编码进生命周期 reducer。

对普通用户而言，删除或损坏缓存后仍可从账本恢复正确状态，篡改会被明确指出而不是生成看似正常的报告。

### 集中校验运行时版本与 Verifier requirements

在 Kernel 提供只读的 requirements 解析器：解析 alias 为 canonical ID，校验 SemVer、版本存在性、重复项、`required` 布尔值和必需链接 Verifier；同时校验 `runtime.kernel.name/version` 与实际运行时。`validate_links.py` 只消费这份规范化结果，并把它写入 Gate、metrics、运行快照和事件；不再保留适配器独有的校验分支。

对普通用户而言，使用旧版 `bsk` 或拼写错误的 Verifier 配置会立即得到清晰错误，不会产生版本混杂的报告。

## 实施范围与顺序

1. 先为身份绑定、Gate 引用、快照哈希和版本不匹配补充失败用例，冻结兼容字段和错误类别。
2. 在 Kernel 实现成对身份校验、顺序/绑定检查和快照哈希规范，并让 CLI、reducer、事件回放共享同一函数。
3. 将 Verifier requirements 与 Kernel 版本校验集中到 Kernel accessor，精简 `validate_links.py` 的重复逻辑；同步状态机/Verifier references、README、Pack 版本和 CHANGELOG。
4. 完成回放、安装后发现和跨工作目录验证；确认已有网络安全与结果语义回归不退化。

## 如何确认完成

- 旧 `run_id`、只给 `attempt_id`、缺少身份、错序 Gate、错配 `result_event_id`/`result_refs`、非 Kernel Gate 均不能离开 `checking`。
- 修改或删除 `meta-state.json` 后，`bsk rebuild` 能恢复一致状态；任意快照哈希漂移都返回结构化 `integrity_error`（或等价稳定错误类别）。
- 运行时 Kernel 名称/版本与配置不匹配时，在执行 Verifier 前失败；canonical/alias、未知 ID、重复项、非法版本和非布尔 `required` 均有明确错误。
- HTTP 4xx/5xx 与缺失 anchor 仍为确定性 `fail`；DNS/连接/超时仍为 `unchecked`/`timed_out` 并进入人工复核；SSRF 重定向测试继续通过。
- 运行 `PYTHONPATH=packages/bensz-skill-kernel/src python3 -m pytest -q packages/bensz-skill-kernel/tests`，现有 85 项及新增边界测试全部通过；另执行 Pack/index 一致性、事件重放和安装后 package-data 检查。
- 通过 BAC 记录计划、实现、测试命令和环境限制，不记录原始私密路径、凭据或完整文档内容。

## 风险与待确认事项

- 快照哈希契约属于审计协议变更，需要决定是 patch 兼容旧哈希，还是以新协议/版本迁移；历史事件不得被重写。
- 若业务确实允许“报告但未通过”，应保留 `reported` 与 Gate 决策分层；只有需要验证通过才能结束的 Skill 才声明 `verifier-gate-allow`。
- 事件账本完整性依赖写入权限控制；哈希校验能发现漂移，不能替代文件系统权限和备份策略。
