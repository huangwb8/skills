# bensz-skill-kernel

无第三方运行时依赖的 Agent Skill verifier 与生命周期内核。

安装后，Skill 通过 `bsk` 发现和调用内置 verifier：

```bash
bsk verifier list --tag markdown
bsk verifier describe markdown.references.v1
bsk verifier run markdown.references.v1 --input README.md
```

当前内置示例：

- `artifact.file-exists`：通用文件存在性检查，标签 `common`、`filesystem`、`deterministic`。
- `markdown.references.v1`：Markdown 引用、站内 anchor 和 HTTP(S) 可达性检查，标签 `vertical`、`markdown`、`references`、`network-read`。

需要审计时，为 `run` 增加 `--events EVENTS --run-id RUN_ID`；命令会输出统一 `results`、`gate` 和兼容的 `verification` 字段，并把标准化事实追加到事件账本。生命周期底层命令仍可通过 `bsk status/rebuild/append/transition/artifact/validation/delivery` 使用。
