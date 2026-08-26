# bensz-skill-kernel

无第三方运行时依赖的 Agent Skill verifier 与生命周期内核。

安装后，Skill 通过 `bsk` 发现和调用内置 verifier：

```bash
bsk verifier list --tag citation
bsk verifier describe citation.truth-and-fit --version 1.0.0
```

当前内置示例：

- `artifact.file-exists`：通用文件存在性检查，标签 `common`、`filesystem`、`deterministic`。
- `citation.truth-and-fit`：格式无关的引用真实性与适切性契约；要求 `subject_context`、`source_metadata`、`source_excerpt` 证据。kernel 只提供保守的 `unchecked` 结果，具体语义引擎由领域 Pack 注入。

引用真实性与适切性由格式无关的 `citation.truth-and-fit` Verifier 负责。Markdown、LaTeX、Word 等格式适配器只负责提取并规范化证据；kernel 不把任何文档格式写入该 Verifier 的能力边界。

需要审计时，为 `run` 增加 `--events EVENTS --run-id RUN_ID`；命令会输出统一 `results`、`gate` 和兼容的 `verification` 字段，并把标准化事实追加到事件账本。生命周期底层命令仍可通过 `bsk status/rebuild/append/transition/artifact/validation/delivery` 使用。
