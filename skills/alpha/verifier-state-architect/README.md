# verifier-state-architect — 设计并落地 Verifier / State

[English](README_EN.md)

把目标 Agent Skill 交给它：先理解业务、选择真正有用的验证器和状态，再直接修改源码并验证接入。计划先保存，供 AI 执行、人类以后审查；**不需要审核计划后才开始实现**。

## 快速开始

在可调用此 Skill 的宿主中指定目标**开发源码**目录：

```text
请使用 verifier-state-architect，为 skills/beta/my-skill 设计并落地 verifier 和 state。
先判断哪些组件确实有用，计划保存后直接执行；遵循托管规范，验证实际接入并保留事后审查证据。
```

预期结果：目标 Skill 的组件、配置和调用流程完成必要改动，附计划、验证证据和剩余限制；若删除影响测试证明不需要组件，则交付有依据的“不接入”结论。

运行机械检查需要 Python 3.11+、PyYAML 和与目标声明匹配的 `bensz-skill-kernel`。设计本身可以先进行，但缺依赖或宿主时不会宣称执行成功。

## 使用模式

| 意图 | 行为 |
| --- | --- |
| 把目标交给本技能设计、实现、接入或精简 | 默认 `implement`：计划 → 本地实现 → 验证 → 交付 |
| 明确“仅计划 / 不修改源码” | `plan-only`：保存设计，不修改目标源码 |
| 只读审查已有组件 | `review-only`：只报告问题、证据和建议 |
| 已有计划要求落地 | 核对当前源码与计划，更新实质偏差后连续执行 |

```text
请使用 verifier-state-architect，只读审查 skills/alpha/reporting 的 verifier/state，不修改源码。
逐项做删除影响测试，说明 Kernel 复用、Gate、迁移和恢复风险。
```

```text
请使用 verifier-state-architect，按 docs/plans/my-skill-verifier-state-design.md 落实目标 Skill。
核对当前源码后直接执行，不等待计划审批；未完成验证的部分明确标记。
```

## 设计原则

- 不追求组件数量：零组件、只有 Verifier 或只有 State 都合法。
- 确定性脚本检查结构、路径、协议和事实；业务语义由 AI 按契约及证据判断。
- 先盘点 Kernel 的直接、组合或适配复用，再考虑专用组件；分开记录复用和跨领域提炼结论。
- 不把领域规则塞进 Kernel；专用 Pack 随目标 Skill 发布和安装。
- 与 `skill-creator` 的普通技能开发不同，本技能专门负责 Verifier/State 的设计和接入；Kernel 功能开发是另一个授权范围。

## 交付与目录

| 内容 | 位置 |
| --- | --- |
| 持续保留的执行计划 | 项目 `docs/plans/{skill-name}-verifier-state-design.md`，或指定位置 |
| 专用 Verifier | 目标 `references/verifiers/index.json` 与各子目录的 `VERIFIER.md` |
| 专用 State | 目标 `references/states/index.json` 与各子目录的 `STATE.md` |
| 声明与调用点 | 目标 `config.yaml`、`SKILL.md` 及必要的宿主/脚本入口 |
| 证据、日志和对账 | 同一任务 `.bensz-api/task-…/verifier-state-architect/` 边界 |

计划是流程中的一步，不再是默认最终交付。已有非本任务文件不直接覆盖；最终按“计划项 → 改动 → 验证 → 结果”对账。目录、字段、契约和加载方式统一见[托管规范](references/skill-pack-hosting.md)，操作步骤见[落地参考](references/implementation.md)；托管规范只在该 Skill 内维护一份。

## 配置与检查

默认模式、计划路径和安全设置见 [config.yaml](config.yaml)；完整执行契约见 [SKILL.md](SKILL.md)。用户显式只读要求优先于默认配置。`README.md` 与 `README_EN.md` 保持同一用法契约。

```bash
python3 /path/to/verifier-state-architect/scripts/check_integration.py /path/to/target-skill
```

只读脚本校验标准布局、索引/契约分工、State 图字段、canonical/alias、声明及真实 Kernel 加载。它不会执行目标脚本或模型、写目标文件、联网或修改安装副本。

JSON 报告的 `execution: unchecked` 表示此检查**不证明业务执行**。退出码 0 为结构通过或零组件不适用，1 为不符合，2 为依赖不可用。还需验证真实组件、缺证据失败、Gate、状态迁移及适用的重放；旧格式能被 Kernel 读取不等于符合新托管规范。

## 边界与恢复

- 只在授权开发源码中实施；不自动发布、远程写入、修改 Kernel 或系统安装副本。
- 保留用户已有改动；冲突、缺依赖或缺宿主回传时报告受阻，不伪造通过。
- 自动执行不取消业务自身需要的人类判断，也不绕过 required 证据与权限边界。
- 计划先落盘，失败保留证据；回退只针对本轮自身变更，不清除用户工作。
- 不保存密钥、令牌、Cookie、私有指令或不必要原始输入；中间文件不污染发布资产。

## WHICHMODEL：模型选择建议

保留按任务能力选择的策略：复杂业务理解、删除影响、架构取舍和跨文件落地使用可处理相应上下文的高推理模型；结构化计划和文档可用中高能力通用模型；字段、路径与加载检查优先确定性脚本。不固定型号，也不把换模型当成将 uncertain/unchecked 改成通过的理由。

## FAQ

**只说“设计”会停在计划吗？** 把目标交给本技能设计时默认继续落地；只想看方案请明确“仅计划，不修改源码”。

**一定生成两种组件吗？** 不一定。先证明组件有用；不为满足格式或加载器添加占位 State。

**文件生成后就是接入成功吗？** 不是。必须区分结构可加载、组件实际执行、业务语义验证；无执行证据就明确未验证。

**能在其它项目使用吗？** 可以针对不同领域设计；安装包自带参考与检查脚本。落地仍需要授权源码、兼容 Kernel 和真实宿主，不保证未知环境无需适配。

**如何回看？** 从计划和任务对账找到修改文件、决策理由、验证命令及未完成项；变更历史见 [CHANGELOG.md](CHANGELOG.md)。
