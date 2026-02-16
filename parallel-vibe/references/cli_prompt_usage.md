# CLI Prompt 用法速查（Codex / Claude）

本文档用于 `parallel-vibe` 的“可执行命令规划”阶段：把每个 thread 落到“一条命令一次执行”的 CLI 形态。

注意：不同版本 CLI 的参数可能不同；以你本机 `--help` 输出为准。

## Claude（claude）

官方文档（Claude Code SDK / CLI reference）：

```
https://docs.anthropic.com/en/docs/claude-code/sdk
```

常用形态：

```bash
# 打印（非交互）模式
claude -p "你的指令内容"

# 指定模型（示例形态；可用参数以 --help 为准）
claude --model <model_id> -p "你的指令内容"

# 从 stdin 提供上下文（文件内容），再给一个 query
cat some_context.md | claude -p "请基于以上内容完成任务"
```

## OpenAI Codex CLI（codex）

官方文档（Codex CLI 非交互模式 / CLI 参考）：

```
https://developers.openai.com/codex/
```

官方入门文章中常见的模型指定形态：

```bash
codex -m <model_id>
```

非交互执行（一次命令一次执行）：

```bash
codex exec "你的指令内容"

# 指定模型（常见形态；也可能支持 --model）
codex -m <model_id> exec "你的指令内容"

# 从 stdin 读取 prompt（PROMPT 为 "-"）
cat synthesis_input.md | codex exec -
```

