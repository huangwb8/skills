# Parallel-Vibe Plan Template

`auto-draw-plot` 每轮在出图前生成一份合法的 `parallel-vibe` plan。仅在需要时才把 Prompt 草案交给独立线程。

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
- thread 负责复用已准备的 Prompt 或按需求起草，并在隔离 workspace 写出 `RESULT.md`。
- 主入口将本轮已写好的 `prompt.txt` 通过 `--prompt-file` 传给 worker，复用其中的蓝图和迭代反馈。手动生成的 plan 仍可按示例调用，worker 在缺少该参数时从用户需求起草。
- PNG 生成、视觉评估、最佳轮次选择仍由 `auto-draw-plot/scripts/run_draw_plot.py` 主流程负责。
- 实际 plan 由 `scripts/build_parallel_plan.py` 生成，脚本会对路径做 shell quote；示例中的绝对路径必须位于当前 project/workspace 边界内，不应指向父目录或外部敏感位置。
