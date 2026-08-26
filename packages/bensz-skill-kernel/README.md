# bensz-skill-kernel

无第三方运行时依赖的 Agent Skill verifier 与生命周期内核。

安装后，Skill 通过 `bsk` 发现和调用内置 verifier：

```bash
bsk verifier list --tag markdown
bsk verifier describe markdown.link-integrity --version 1.0.0
bsk verifier run markdown.link-integrity --version 1.0.0 --input README.md
```

当前内置示例：

- `artifact.file-exists`：通用文件存在性检查，标签 `common`、`filesystem`、`deterministic`。
- `markdown.link-integrity`：Markdown 链接提取、站内 anchor 和 HTTP(S) 可达性检查；版本通过 `--version` 指定，当前为 `1.0.0`，标签 `vertical`、`markdown`、`links`、`network-read`、`deterministic`。
- `citation.truth-and-fit`：格式无关的引用真实性与适切性契约；要求 `subject_context`、`source_metadata`、`source_excerpt` 证据。kernel 只提供保守的 `unchecked` 结果，具体语义引擎由领域 Pack 注入。

引用真实性与适切性不属于 Markdown 格式层。领域 Pack 应使用格式无关的 `citation.truth-and-fit` 能力契约，并至少接收目标论断上下文、来源元数据和来源摘录；kernel 不把只能检查可达性的适配器注册成语义核验器。

需要审计时，为 `run` 增加 `--events EVENTS --run-id RUN_ID`；命令会输出统一 `results`、`gate` 和兼容的 `verification` 字段，并把标准化事实追加到事件账本。生命周期底层命令仍可通过 `bsk status/rebuild/append/transition/artifact/validation/delivery` 使用。
