# Parallel-Vibe Plan Template

`auto-draw-plot` 对 `parallel-vibe` 的标准用法是：每一轮都必须先生成合法的 `parallel-vibe` plan，再决定是否真的把“下一轮 prompt 草案”交给独立线程。这样既保留统一协议，又避免把整个出图闭环都塞进 thread workspace。

示例结构：

```json
{
  "threads": [
    {
      "thread_id": "001",
      "title": "Round 1 prompt generation",
      "runner": {
        "type": "shell",
        "profile": "deep",
        "cmd_template": "python3 /abs/path/auto-draw-plot/scripts/parallel_round_worker.py --run-dir /abs/path/.draw-plot/run-xxxx --request-file /abs/path/.draw-plot/run-xxxx/requests/user-need.md --round 1 --result-file RESULT.md"
      },
      "prompt": "读取当前 run 的用户需求和历史 round 反馈，在隔离 workspace 中生成下一轮 prompt 草案，并写出 RESULT.md。"
    }
  ],
  "synthesize": false
}
```

说明：

- 本文件不是可选示例，而是 `auto-draw-plot` 每一轮都必须写出的标准协议。
- `runner.type` 必须是 `parallel-vibe` 当前支持的合法类型；对本 skill，推荐 `shell`。
- thread 的职责只应包括：读取需求、起草 prompt、写出 `RESULT.md`。
- PNG 生成、视觉评估、最佳轮次选择仍由 `auto-draw-plot/scripts/run_draw_plot.py` 主流程负责。
- 实际 plan 由 `scripts/build_parallel_plan.py` 生成，脚本会对路径做 shell quote；示例中的绝对路径必须位于当前 project/workspace 边界内，不应指向父目录或外部敏感位置。
