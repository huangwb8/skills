# parallel-vibe 集成说明

`git-pr-review` 的并行独立评审默认通过 `parallel-vibe` 落地。

推荐顺序：

1. `prepare_review_job.py`
2. `build_parallel_review_plan.py`
3. 优先执行 `parallel_review_job.json` 里的 `recommended_command`；若手动执行，则使用 `../parallel-vibe/scripts/parallel_vibe.py --plan-file ... --src-dir ... --out-dir ... --project-id ...`
4. `aggregate_parallel_reviews.py`
5. 宿主 AI 综合 `independent_review_summary.md` 与原始证据写最终报告

默认并行独立评审次数：5。

如果 `raw/`、`notes/`、`evidence/` 的证据材料发生变化，必须先重新运行 `build_parallel_review_plan.py`，让输入快照和 `project_id` 同步刷新。

关键产物：

- `parallel_review/parallel_review_job.json`
- `parallel_review/parallel_plan.json`
- `parallel_review/parallel_plan.md`
- `parallel_review/parallel_runs/.parallel-vibe/<project_id>/...`
- `parallel_review/independent_review_summary.md`
- `parallel_review/independent_review_summary.json`

最终报告应引用：

- 独立评审的 recommendation / risk 分布
- 主要共识
- 主要分歧
- 若涉及依赖/第三方代码，还应引用各 thread 对 license 风险的判断
- 这些分歧是否改变最终 merge 建议
