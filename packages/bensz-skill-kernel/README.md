# bensz-skill-kernel

无第三方运行时依赖的 Agent Skill 状态、工作区与 verifier 生命周期内核。

状态定义采用目录化协议：每个元状态目录包含一个 `STATE.md`，可选附带 JSON-stdio
检查或演示脚本。内置状态可以通过统一命令发现；`--root` 会在内置状态之外叠加 Skill
状态包，而非替换它：

```bash
bsk state list
bsk state describe workspace.ready
bsk state list --root path/to/skill/states
```

一个 Skill 用根目录中的 `state-machine.json` 声明它采用哪些状态包、初始状态及可用状态。
kernel 只校验该格式，不理解领域动作。Agent 先读取状态契约，再用同一命令检查或持久化
转移；转移会在目标状态有 `entrypoint` 时执行其 JSON-stdio 检查，只有返回 `pass` 才落盘：

```bash
bsk state list --skill-root path/to/skill
bsk state describe workspace.ready --skill-root path/to/skill
bsk state check workspace.ready skill.collect --skill-root path/to/skill
bsk state transition .bensz-api/task-YYYYMMDD-HHMM-demo skill-name skill.collect \
  --skill-root path/to/skill --context-json '{"input":"report.md"}'
```

状态操作统一返回 `bensz-meta-state-v1` JSON，包含操作、状态、结果、可选脚本回执和
持久化快照。每个 Skill 的当前元状态写入自身 `log/meta-state.json`；它与任务级
`events.ndjson` / `state.json` 分层，后者仍只记录生命周期、验证与交付事实。

`STATE.md` 的 frontmatter 至少应有稳定的 `id`；推荐同时声明 `version`、`kind`、
`description`、`entry_conditions`、`invariants` 和 `transitions`。正文是 Agent 必须遵守的
阶段说明。可选 `entrypoint` 是相对于该 `STATE.md` 目录的脚本：stdin 接收
`{"protocol":"bensz-meta-state-v1","state":...,"request":...}`，stdout 只能输出一个
JSON 对象，其中 `verdict` 是 `pass`、`fail`、`uncertain`、`unchecked`、`error`、
`timed_out` 或 `skipped`，并可带 `summary`、`facts`、`evidence_refs`。只有成功执行且
`verdict=pass` 的 helper 会允许持久化转移；没有 helper 的 instruction-only 状态由 Agent
按照正文执行。

每个逻辑任务先初始化一个不可变的 BenszAPI 工作区；Skill 不应自行拼接路径，而应通过
工作区命令取得自己的 `input`、`output` 和 `log` 边界：

```bash
bsk workspace init . --description citation-review
bsk workspace path .bensz-api/task-YYYYMMDD-HHMM-citation-review validate-md-ref input
bsk workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

初始化结果中的 `workspace.ready` 是所有 Skill 状态的系统级前置状态。工作区还会创建
共享 `shared/input|output|log` 边界；工作区清单保存协议版本和初始状态，事件账本仍由
下方的生命周期命令追加和重放；两者保持分层，避免把 Skill 领域状态硬编码进核心 reducer。

安装后，Skill 通过 `bsk` 发现和调用包内 `bensz_skill_kernel/verifiers/` 目录中的 verifier。每个 verifier
由一个 `VERIFIER.md` 契约和可选 `scripts/` 入口组成；入口通过 stdin 接收 JSON、
通过 stdout 返回一个标准化 JSON 结果：

```bash
bsk verifier list --tag citation
bsk verifier describe citation.truth-and-fit --version 1.0.0
bsk verifier run markdown.link-integrity --input README.md
```

`VERIFIER.md` 使用 YAML 风格的轻量 frontmatter，至少包含 `id` 和 `version`；可选
`description`、`tags`、`entrypoint`。没有 `entrypoint` 的 verifier 是
instruction-only，由 Agent 读取正文执行。脚本入口遵循：stdin 一个请求 JSON，stdout
一个结果 JSON（`verdict` 为 `pass`、`fail`、`uncertain`、`unchecked`、`error`、
`timed_out` 或 `skipped`）。kernel 负责超时、异常、非法 JSON 和结果字段归一化。

当前内置示例：

- `markdown.link-integrity`：Markdown 链接和锚点完整性检查，标签 `common`、`markdown`、`links`、`deterministic`。
- `citation.truth-and-fit`：格式无关的引用真实性与适切性契约；这是 instruction-only verifier，由 Agent 或领域引擎按 `VERIFIER.md` 执行并返回 `unchecked`/语义结果。

代码只定义发现、调用、超时、结果归一化和事件记录协议，不内置领域判断流程。Markdown、LaTeX、Word 等格式适配器可各自选择适用 verifier。

需要审计时，为 `run` 增加 `--events EVENTS --run-id RUN_ID`；命令会输出统一 `results`、`gate` 和兼容的 `verification` 字段，并把标准化事实追加到事件账本。生命周期底层命令仍可通过 `bsk status/rebuild/append/transition/artifact/validation/delivery` 使用。
