# bensz-skill-kernel

轻量的 Agent Skill 状态、工作区与 Verifier 生命周期内核。

[English](README_EN.md)

## 适合谁

- **Skill 使用者**：用 `bsk` 发现状态、Verifier 和工作区边界。
- **Skill/Pack 作者**：声明 `config.yaml.runtime`、State/Verifier Contract Pack 与 JSON-stdio 组件。
- **内核开发者**：维护可重放事件账本、Gate、证据和安全边界。

## 快速开始

需要 Python 3.11+。在仓库根目录执行：

```bash
# 建议在隔离环境安装当前包
python3 -m venv .bensz-api/.venv
.bensz-api/.venv/bin/python -m pip install -e packages/bensz-skill-kernel

# 确认 CLI 与内置 Pack 已可发现
.bensz-api/.venv/bin/bsk --version
.bensz-api/.venv/bin/bsk verifier list
```

预期：第一条命令输出当前包版本，第二条列出内置 Verifier。只想安装已发布版本时，可改用 `python3 -m pip install bensz-skill-kernel`；版本与依赖以 `pyproject.toml` 为准。

## 声明式 State/Verifier 子 Agent 协作

Kernel 只负责 State、Verifier、证据和 Gate；它不实现跨 Harness 的 Agent 创建、并行、等待或回收。需要协作的 Skill 应引用[条件性协作模板](../../docs/templates/state-verifier-agent-coordination.md)，在 `SKILL.md` 中说明触发阶段、子 Agent 输入、独立性、输出格式和 fallback。

- `config.yaml` 可以声明 `mode`、`count`、`rounds` 等协作意图，供 LLM 与 Harness 理解和报告；这些字段不是 Kernel 调度 API。
- 默认的 Verifier 协作建议是两个独立子 Agent 并行检查同一快照；串行复核只在 Skill 明确需要时声明。
- Codex、Claude Code 或其他 Harness 自主决定如何创建和隔离子 Agent；Skill 不得假设平台 API、host ID 或沙箱参数。
- 子 Agent 结果仍须回到既有 Verifier/Gate 契约，缺失、不确定或失败不得被伪装为通过。

## Python 支持与依赖

- 最低支持 Python 3.11；已验证 3.11、3.12、3.13，推荐 3.12。
- 运行时仅依赖 PyYAML（读取 Skill 的 `config.yaml`）和 Python 标准库。
- 新 Python 版本通过测试矩阵后才进入支持范围。

## 目录化 Contract Pack

State 与 Verifier 都采用“Markdown 契约 + 索引元数据 + 零个或多个组件”的目录化 Pack。`contract_packs.py` 在 `packs.py` 的发现与 JSON-stdio 边界上编排 `script`、`agent`、`human` 组件，并绑定契约/计划/组件哈希、证据、依赖顺序、`run_id`/`attempt_id` 和执行者。共享执行层不混淆 State 的迁移语义与 Verifier 的 verdict/Gate 语义。

canonical ID、版本和 alias 迁移规则见 [`docs/verifier-id-naming.md`](../../docs/verifier-id-naming.md) 与 [`docs/state-id-naming.md`](../../docs/state-id-naming.md)。

## State：阶段与迁移

`states/index.json` 是 State 目录清单；每个状态目录包含 `STATE.md`，可选 JSON-stdio helper。内置生命周期状态为 `planned`、`active`、`waiting`、`checking`、`delivering`、`completed`、`failed`、`cancelled`；`workspace-ready` 与 `workspace-closed` 是工作区系统状态。领域 Skill 阶段仍放在自身 `references/states/`。

```bash
bsk state list
bsk state describe bensz.workspace.ready
bsk state list --root path/to/skill/states
```

`--root` 会叠加 Skill 状态，不替换内置状态。Skill 在根目录 `config.yaml.runtime` 声明初始状态、可用状态、状态根和 Verifier 子集；旧 `state-machine.json` 只读兼容。required 组件必须全部完成并通过，状态条件才成立。

先初始化任务工作区和 Skill 状态声明，再检查/持久化迁移：

```bash
bsk workspace init . --description citation-review
bsk state check bensz.workspace.ready org.example.skill.collecting --skill-root path/to/skill
bsk state transition .bensz-api/task-YYYYMMDD-HHMM-citation-review skill-name org.example.skill.collecting \
  --skill-root path/to/skill --context-json '{"input":"report.md"}'
```

状态操作返回 `bensz-meta-state-v1` JSON，含操作、状态、结果、可选 helper 回执和快照。Skill 元状态写入自身 `log/meta-state.json`；任务 `events.ndjson`/`state.json` 仍是独立的生命周期与证据层。成功迁移追加 `state.transition`（`state_domain: skill`）事件，`bsk rebuild` 投影到 `skill_states`/`skill_state_transitions` 并核验稳定字段哈希。缺失快照可由事件恢复，哈希漂移返回结构化 `integrity_error`。

Kernel 只执行有明确协议的 invariant。当前 `verifier-result-recorded` 要求离开该状态前同时存在 `verification.result` 与 `verification.gate`；不满足时返回 `rejected`，不写入新快照。领域 invariant 仍由 Skill helper 或人工复核负责。带运行身份时，`run_id` 与 `attempt_id` 必须成对传入。

## Verifier：证据与 Gate

`verifiers/index.json` 是 Verifier 包目录和执行计划的单一来源；每个 Pack 有 `VERIFIER.md` 和可选组件。脚本组件 stdin 接收一个 JSON 请求、stdout 输出一个结果 JSON；`verdict` 支持 `pass`、`fail`、`uncertain`、`unchecked`、`error`、`timed_out`、`skipped`。Kernel 负责超时、异常、非法 JSON 和结果字段归一化。

```bash
bsk verifier list --tag citation
bsk verifier describe bensz.evidence.citation-truth-fit --version 1.0.0
bsk verifier run bensz.document.markdown-link-integrity --input README.md
```

内置示例包括文件存在、Markdown 链接完整性和引用真实性/适切性；旧 ID alias 仍可解析。引用 Verifier 显式声明为 `agent` 组件，未收到绑定结果时保持 `unchecked`/`wait`。旧单入口 Pack、无 `index.json` 的兼容目录和 instruction-only 状态仍可发现，但会给出缺少显式组件元数据的诊断。原子 Pack 还覆盖合同一致性、路径范围、Schema、diff、敏感信息脱敏、证据来源、事件完整性、状态转移和任务完整性；领域规则不写入 Kernel。

审计运行增加 `--events EVENTS --run-id RUN_ID`，返回统一 `results`、`gate` 和兼容 `verification` 字段。Agent/人工 handoff 会在顶层返回，但不把契约正文或原始上下文写入账本。Python API 的 `trusted=False` 是不可信 Pack 的进程级 fail-closed 选项，不是 `bsk verifier run` 的 CLI 参数。

## Workspace：不可变任务边界

每个逻辑任务先初始化一个不可变 BenszAPI 工作区；Skill 不应自行拼接路径：

```bash
bsk workspace init . --description citation-review
bsk workspace path .bensz-api/task-YYYYMMDD-HHMM-citation-review validate-md-ref input
bsk workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

初始化会创建 `bensz.workspace.ready`（旧 alias：`workspace.ready`）和 `shared/input|output|log` 边界。工作区 manifest、生命周期事件账本和 Skill 元状态快照分层保存且可重放。

## 运行边界与审计

Pack helper 默认以受信本地进程运行；Kernel 限制输入、stdout/stderr 体积、环境变量和执行时长，超时终止整个进程组。对不可信 Pack 传入 `trusted=False` 会 fail-closed；这是进程级资源边界，不等同于容器或操作系统沙箱。stdio 子进程默认设置 `PYTHONDONTWRITEBYTECODE=1`，不会向 Pack 目录写入 `__pycache__`；显式提供的 `PYTHONPYCACHEPREFIX` 仍会透传，便于把缓存归档到指定目录。

追加式账本保留可选契约快照、授权链和执行审计。`reduce_events()` 只做离线投影重放，不重新调用模型或工具。`verification-v2` 在记录和完成门禁处复核组件唯一性、哈希、证据引用、运行身份、执行者/模型及人工确认；调用方自报的 aggregate pass 不能覆盖 required 失败或漏跑。`summarize_metrics()` 额外汇总组件绑定率和执行者身份覆盖率。

## 开发、测试与发布

```bash
# 包内单元测试（需要已安装 pytest）
python3 -m pytest packages/bensz-skill-kernel/tests

# 构建并检查发布包；默认不上传
python3 tests/publish_bsk_pypi.py
# 只有明确授权时才上传到 PyPI
python3 tests/publish_bsk_pypi.py --upload
```

发布助手把构建产物写入 `tmp/bsk-pypi/`，不读取、复制或记录 PyPI 凭据。完整 API、State/Verifier 契约和变更记录见仓库 `docs/`、源码与 `CHANGELOG.md`。

## 许可证

本包使用 MIT License，详见 [`LICENSE`](LICENSE)。
