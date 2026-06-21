# git-pr-review

本 README 面向**使用者**：如何触发并正确使用 `git-pr-review` skill。  
执行规范在 `SKILL.md`；默认参数与命名规则在 `config.yaml`。

## 用法

推荐用法：

```text
请使用 git-pr-review skill 帮我 review 这个 GitHub PR，并判断是否值得 merge。
输入：仓库地址 `https://github.com/owner/repo`，PR `https://github.com/owner/repo/pull/123`
输出：项目根目录下 1 份 Markdown 审查报告
```

进阶用法：

```text
请使用 git-pr-review skill 帮我 review 这个 GitHub PR，并重点检查是否存在恶意代码或供应链风险。
输入：仓库地址 `https://github.com/owner/repo`，PR `#123`，另外参考我附上的背景说明
输出：项目根目录下 1 份 Markdown 审查报告；所有中间文件放到 `.bensz-api/skills/git-pr-review/`
```

并行独立评审版：

```text
请使用 git-pr-review skill 帮我 review 这个 GitHub PR，并做 5 次独立评审后再综合结论。
输入：仓库地址 `https://github.com/owner/repo`，PR `#123`
输出：项目根目录下 1 份最终 Markdown 审查报告；`.bensz-api/skills/git-pr-review/` 里保留并行独立评审的全部中间产物
```

## 它能帮你做什么

`git-pr-review` 适合下面这些场景：

- 你想知道某个 PR 到底解决了什么问题
- 你不确定这个 PR 的方案值不值得 merge
- 你担心 PR 里藏着恶意逻辑、安全问题、权限扩大或 CI/CD 风险
- 你担心 PR 引入新的依赖、第三方代码或资源后会带来 license 冲突
- 你希望把这个 PR 和社区对“好 PR”的标准做一次对照
- 你希望让多个独立 reviewer 视角并行审查，再综合得出更稳的判断
- 你想把结论沉淀成一份可转发、可归档的 Markdown 报告

## 工作方式

这个 skill 默认是**只读评审**：

- 会读取 GitHub 上的 PR 信息、diff、评论、CI 状态和关联 issue
- 默认优先使用 skill 内置的“好 PR”标准参考，而不是每次实时联网
- 只有用户明确要求最新口径、指定特定社区规范，或内置标准明显不足时，才会联网补充“好 PR”标准来源
- 会默认基于 `parallel-vibe` 做 **5 次独立评审**
- 会在涉及依赖、vendored 代码、复制资源时给出 license / 合规建议
- 会把所有中间文件放进工作目录下的 `.bensz-api/skills/git-pr-review/`
- 会在项目根目录生成最终报告

它**不会**：

- 修改仓库代码
- 自动 merge PR
- approve PR
- checkout PR 分支后运行不可信代码

## 输出文件

默认会生成：

- `Git-PR-Review_{repo}_{pr}_{yyyy-mm-dd-hh-mm}.md`

例如：

- `Git-PR-Review_openai_openai-python_pr-2451_2026-03-24-15-30.md`

中间文件默认位于：

- `.bensz-api/skills/git-pr-review/{yyyy-mm-dd-hh-mm}/`

其中通常包含：

- `manifest.json`：本次评审的路径和元数据
- `raw/README.md`：原始材料目录说明
- `notes/user_context.md`：用户补充背景
- `notes/community_good_pr.md`：社区标准摘记
- `references/good-pr-standards.md`：skill 内置的“好 PR”标准参考
- `notes/license_review.md`：license / 合规审查笔记（如适用）
- `evidence/key_findings.md`：关键发现
- `evidence/missing_items.md`：缺失证据与影响
- `parallel_review/parallel_plan.json`：并行独立评审计划
- `parallel_review/parallel_runs/.bensz-api/skills/parallel-vibe/<project_id>/...`：独立 reviewer threads 产物
- `parallel_review/independent_review_summary.md`：独立评审聚合结果

## 关键行为

### Fail-fast 校验

脚本会尽早拦截明显错误，避免你在错误上下文上浪费时间：

- 仓库地址不是 GitHub 仓库，或误传成 `issues/`、`pull/`、`tree/` 这类子页面 URL
- PR URL 不是 GitHub Pull Request，或编号格式不是 `#123` / `123` / `pr-123`
- 仓库与 PR URL 不属于同一个仓库
- 最终报告文件名或章节结构不符合约定

### 工作区隔离

- 默认中间文件只允许写入 `.bensz-api/skills/git-pr-review/`
- 最终 Markdown 报告默认写到当前工作目录
- 如果你明确指定其他 `workspace_dir` 或 `report_dir`，skill 会按你的指定执行

### 默认独立评审次数

- 默认会做 `5` 次独立评审
- 如果你明确指定 `review_count=7` 或“做 7 次独立评审”，skill 会按你的值执行
- 在底层辅助脚本里，这个值会映射为 `build_parallel_review_plan.py --n <review_count>`
- 如果你只想单次评审，也可以明确要求 `review_count=1`

## 使用示例

### 示例 1：常规技术评审

```text
请使用 git-pr-review skill 帮我 review 这个 PR。
输入：仓库 `https://github.com/pallets/flask`，PR `https://github.com/pallets/flask/pull/5432`
输出：给我一份是否建议 merge 的 Markdown 报告
```

### 示例 2：重点怀疑恶意行为

```text
请使用 git-pr-review skill 评估这个 PR 是否恶意。
输入：仓库 `https://github.com/owner/repo`，PR `#87`
输出：一份带风险等级和处理建议的报告
```

### 示例 3：带团队背景说明

```text
请使用 git-pr-review skill 审查这个 PR。
输入：仓库 `https://github.com/owner/repo`，PR `#201`
另外，还有下列参数约束：
- 重点看 CI/CD、权限配置和 secrets 是否被动了手脚
- 我们团队更偏好小而清晰、易回滚的 PR
- 输出时请明确写出“是否建议 merge”
```

### 示例 4：指定独立评审次数

```text
请使用 git-pr-review skill 审查这个 PR，并做 7 次独立评审。
输入：仓库 `https://github.com/owner/repo`，PR `#88`
输出：最终审查报告中请单独总结 7 次独立评审的共识与分歧
```

## 结果里会回答哪些问题

最终报告通常会明确回答：

- 多个独立 reviewer 的 recommendation / risk 是否形成共识
- 这个 PR 解决的问题是否真实、是否描述清楚
- 方案的优势、局限和潜在替代路径
- 改动范围是否合理，是否便于 review 和回滚
- 是否存在恶意或高风险信号
- 是否存在 license 冲突、copyleft 风险、第三方归属缺失或需要法务确认的点
- 它是否符合社区里“好 PR”的基本标准
- 如果证据不够，缺的是什么、会如何影响结论
- 最后到底建议 `Merge`、`Request changes` 还是 `Do not merge`

## 常见问题

### Q：它会不会自己把 PR merge 掉？

不会。除非你明确提出，否则这个 skill 不会执行 merge、approve、rebase、squash 这类操作。

### Q：它会不会运行 PR 里的代码？

默认不会。这个 skill 的原则是只读评审，避免执行不可信代码。

### Q：如果我想把中间文件放到别处呢？

可以。默认目录是 `.bensz-api/skills/git-pr-review/`，但如果你明确指定其他目录，skill 会按你的目录来。

### Q：它会只看 diff 吗？

不会。它还会结合 PR 描述、评论、CI 状态、关联 issue，以及外部社区对“好 PR”的标准一起判断。

### Q：它会检查 license 问题吗？

会。尤其当 PR 引入新依赖、复制第三方代码、字体、图标、模板、数据或模型资源时，它会明确给出 license / 合规风险和建议动作。

### Q：默认为什么是 5 次独立评审？

因为 5 个独立视角通常足够覆盖：整体质量、安全风险、可维护性、测试/验证、社区标准这几类核心问题，同时又不会把成本拉得过高。

## 备选用法（脚本/硬编码流程）

### 步骤 1：创建隔离工作区

```bash
python3 git-pr-review/scripts/prepare_review_job.py \
  --repo "https://github.com/owner/repo" \
  --pr "https://github.com/owner/repo/pull/123"
```

### 步骤 2：完成评审后校验产物

```bash
python3 git-pr-review/scripts/validate_review_artifacts.py \
  --manifest .bensz-api/skills/git-pr-review/{yyyy-mm-dd-hh-mm}/manifest.json \
  --report /absolute/path/to/Git-PR-Review_<...>.md
```

### 步骤 3：生成 parallel-vibe 并行独立评审计划

```bash
# 例如用户要求 review_count=5 时，这里传 --n 5
python3 git-pr-review/scripts/build_parallel_review_plan.py \
  --manifest .bensz-api/skills/git-pr-review/{yyyy-mm-dd-hh-mm}/manifest.json \
  --n 5
```

### 步骤 4：运行 parallel-vibe 独立评审

```bash
# 推荐直接复制 `parallel_review_job.json` 里的 `recommended_command`
python3 ../parallel-vibe/scripts/parallel_vibe.py \
  --plan-file .bensz-api/skills/git-pr-review/{yyyy-mm-dd-hh-mm}/parallel_review/parallel_plan.json \
  --src-dir .bensz-api/skills/git-pr-review/{yyyy-mm-dd-hh-mm}/parallel_review/input_snapshot \
  --out-dir .bensz-api/skills/git-pr-review/{yyyy-mm-dd-hh-mm}/parallel_review/parallel_runs \
  --project-id <parallel_review_job.json.project_id>
```

补充说明：

- `build_parallel_review_plan.py` 会把解析后的 `parallel-vibe` 脚本路径、固定 `project_id` 和可直接执行的 `recommended_command` 写进 `parallel_review/parallel_review_job.json`
- 如果你补充了 `raw/`、`notes/`、`evidence/` 里的材料，请重新运行 `build_parallel_review_plan.py`，让输入快照和 `project_id` 一起刷新

### 步骤 5：聚合独立评审结果

```bash
python3 git-pr-review/scripts/aggregate_parallel_reviews.py \
  --job-file .bensz-api/skills/git-pr-review/{yyyy-mm-dd-hh-mm}/parallel_review/parallel_review_job.json
```

如果 `parallel-vibe` 尚未执行完成，或某个 thread 没有生成 `RESULT.md`，聚合脚本会直接报错并提示先补齐输入，避免拿不完整结果做 merge 决策。

## 更多文档

- `SKILL.md`：执行流程与硬规则
- `config.yaml`：版本、命名与审查口径
- `references/report-template.md`：报告模板
- `references/good-pr-standards.md`：内置“好 PR”标准参考
- `references/security-checklist.md`：恶意/安全审查清单
- `references/license-checklist.md`：license / 合规审查清单
- `references/community-research-playbook.md`：社区标准检索建议
- `references/parallel-review-result-template.md`：独立评审 thread 模板
- `references/parallel-vibe-integration.md`：parallel-vibe 集成说明

## WHICHMODEL - 模型选择最佳实践

**最后更新**：2026-03-24

### 披露信息

- **覆盖厂商**：Anthropic、OpenAI
- **来源类型**：官方模型文档 / 官方模型总览
- **局限性**：本节优先采用官方资料来保证时效与权威性，未纳入社区主观体验对比；因此更适合做“保守默认选择”，不适合做极端成本优化结论

### 场景 1：默认 PR 审查

| 项目 | 建议 |
|------|------|
| 推荐模型 | Claude Sonnet 4 / GPT-5.2 |
| 推荐原因 | 这个 skill 需要同时处理 diff、评论、社区资料和安全判断，属于“中高复杂度的多源证据综合”；默认优先选择推理和速度更平衡的模型 |
| 适用情况 | 常规 PR、几十到上百行 diff、需要联网和结构化报告输出 |

### 场景 2：高风险 / 安全敏感 PR

| 项目 | 建议 |
|------|------|
| 推荐模型 | Claude Opus 4.1 / GPT-5.2 |
| 推荐原因 | 当 PR 涉及 CI/CD、权限、密钥、供应链或大规模重构时，更强的上下文整合和细粒度推理更重要 |
| 适用情况 | 可疑 PR、超大 diff、需要更谨慎的恶意行为识别 |

### 场景 3：快速分诊

| 项目 | 建议 |
|------|------|
| 推荐模型 | Claude Haiku 3.5 / GPT-5 mini |
| 推荐原因 | 仅做“先看值不值得深审”的低成本分诊时，可以用更便宜更快的模型先产出初筛结论 |
| 适用情况 | 批量 triage、多 PR 排队、先判断是否需要人工深审 |

### 选择原则

1. 只做初筛时优先“快而便宜”；一旦涉及安全与 merge 决策，就升级到默认档或高风险档。
2. 这个 skill 的核心不是写代码，而是**跨来源证据综合判断**，所以默认更适合通用高推理模型，而不是纯编码特化模型。
3. 如果你打算把这个 skill 嵌入会频繁读取本地仓库、做更多 agentic coding 操作的工作流里，再考虑编码特化模型；单次 PR 决策报告通常不需要这样做。

### 官方参考

- Anthropic Models Overview: https://docs.anthropic.com/en/docs/about-claude/models/overview
- OpenAI Models Overview: https://platform.openai.com/docs/models
