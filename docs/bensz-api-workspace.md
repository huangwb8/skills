# BenszAPI 任务工作区约定

所有会写入中间文件的 Skill 都使用同一任务根目录：

```text
./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/
├── README.md
├── shared/
│   ├── input/
│   ├── output/
│   └── log/
└── {skill名}/
    ├── input/
    ├── output/
    └── log/
```

这是运行时默认契约。`{简短描述}`使用稳定、可读且不含路径分隔符的任务标签；同一分钟冲突时在任务名末尾追加 `-a`、`-b` 等短后缀。Kernel 初始化任务时会固定创建 `shared/input|output|log`；Skill 目录则在首次解析其边界时创建。

任务 `README.md` 是任务治理摘要，记录任务目标、参与 Skill、跨 Skill 输入来源、临时产物、正式交付路径和验证摘要；它由协作流程维护，并非 Kernel 初始化时自动生成。`input/` 保存输入引用与参数快照，`output/` 保存仅供本任务消费的草稿、缓存和临时结果，`log/` 保存命令、验证、错误与关键决策。正式交付物、用户指定文件、源代码和正式计划不写入该目录。

Kernel 同时在任务根目录写入 `.workspace.json`，协议为 `bensz-api-task-v1`，初始状态为 `bensz.workspace.ready`。任务级运行事件使用 `log/events.ndjson`，可重建投影使用 `log/state.json`；每个 Skill 的元状态快照使用 `<skill>/log/meta-state.json`。这些运行时记录与 Skill 的领域阶段保持分层。

工作区可通过 Kernel API 写入可选 `run_snapshot`（Skill/State/Verifier/模型/工具/证据/授权摘要及契约哈希）。事件账本兼容读取旧事件，并对新事件记录协议版本、运行 ID、授权链与请求摘要；`reduce_events()` 生成状态投影和旁路执行审计轨迹，不会重新执行模型或工具。

显式传入的工作目录参数可用于读取或续跑历史任务，但不会成为新任务的默认值。历史 `.bensz-api/skills/`、`.nsfc-*`、`.parallel-*` 等目录仅按需兼容读取、迁移或清理；新写入不得再创建这些目录。

工作区创建前，先向用户说明将调用的 Skill 与具体工作；不得归档密钥、令牌、Cookie、环境文件、私有指令、隐私或不必要的大体积原始数据。Skill 的公共硬约束不在各自正文中手工维护，统一来自 `docs/templates/skill-common-constraints.md`，通过同步器写入 `SKILL.md`。
