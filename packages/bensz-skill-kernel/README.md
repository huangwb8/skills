# bensz-skill-kernel

无第三方运行时依赖的 Agent Skill 状态、工作区与 verifier 生命周期内核。

状态定义采用目录化协议：每个元状态目录包含一个 `STATE.md`，可选附带检查或演示
脚本。内置状态可以通过统一命令发现，Skill 专属状态可通过 `--root` 指向自己的目录：

```bash
bsk state list
bsk state describe workspace.ready
bsk state list --root path/to/skill/states
```

每个逻辑任务先初始化一个不可变的 BenszAPI 工作区；Skill 不应自行拼接路径，而应通过
工作区命令取得自己的 `input`、`output` 和 `log` 边界：

```bash
bsk workspace init . --description citation-review
bsk workspace path .bensz-api/task-YYYYMMDD-HHMM-citation-review validate-md-ref input
bsk workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

初始化结果中的 `workspace.ready` 是所有 Skill 状态的系统级前置状态。工作区清单保存
协议版本和状态，事件账本仍由下方的生命周期命令追加和重放；两者保持分层，避免把
Skill 领域状态硬编码进核心 reducer。

安装后，Skill 通过 `bsk` 发现和调用 `verifiers/` 目录中的 verifier。每个 verifier
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
