# Good PR Standards

最后整理时间：2026-03-24

这份文档是 `git-pr-review` 内置的“好 PR”标准参考。
默认执行时优先使用本文件，不要求每次实时联网。

## 来源

1. GitHub Docs: Setting guidelines for repository contributors  
链接：https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors  
访问日期：2026-03-24

2. GitHub Docs: About issue and pull request templates  
链接：https://docs.github.com/enterprise-cloud@latest/communities/using-templates-to-encourage-useful-issues-and-pull-requests/manually-creating-a-single-issue-template-for-your-repository  
访问日期：2026-03-24

3. GitHub Docs: About code owners  
链接：https://docs.github.com/articles/about-code-owners  
访问日期：2026-03-24

4. GitHub Docs: About pull request reviews  
链接：https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-request-reviews  
访问日期：2026-03-24

5. Balachandran, Sawant et al. What Makes a Code Change Easier to Review  
链接：https://www.mozillafoundation.org/en/research/library/what-makes-a-code-change-easier-to-review-an-empirical-investigation-on-code-change-reviewability/  
访问日期：2026-03-24

## 沉淀出的核心标准

### 1. 目标清楚

好 PR 应该让 reviewer 很快知道：
- 它要解决什么问题
- 为什么现在要改
- 改动影响什么范围

如果 reviewer 需要从大量 diff 猜意图，这通常不是好信号。

### 2. 描述充分且结构化

好 PR 通常会提供：
- 背景 / 动机
- 主要改动点
- 测试或验证方式
- 风险、限制或待确认点

GitHub 官方关于贡献指南和 PR 模板的实践，本质上都在推动这件事：让贡献者提交“格式良好、信息完整”的 PR。

### 3. 粒度合适、便于 review

研究和工程实践都支持一个结论：
- 更小、更聚焦、边界清楚的改动，通常更容易 review
- 把多个不相关改动揉在一起，会降低 review 质量
- tangled change（缠结改动）会让理解、回滚和追责都变难

所以评审时要看：
- 这个 PR 是单一问题还是混了多个目标
- 是否存在 scope drift（标题说 A，diff 里还夹了 B/C）

### 4. 可验证

好 PR 不只是“看起来有道理”，还要便于验证。
常见正向信号：
- 有测试
- 有复现步骤或验证步骤
- CI 信号清楚
- 对 reviewer 来说可重复检查

如果缺少测试、CI 失败、验证方式含糊，通常至少应降低 merge 信心。

### 5. 容易找到合适 reviewer

GitHub 官方关于 code owners 和 review request 的机制说明了一个事实：
- 好 PR 应该能较容易路由到正确 reviewer
- 改动范围清晰时，CODEOWNERS / reviewer assignment 才真正有效

如果改动横跨太多模块、责任边界模糊，就会降低 review 质量和 merge 可靠性。

### 6. review 反馈可阻断 merge 时，要严肃对待

GitHub 官方 review 机制强调：
- `Request changes` 不是装饰性意见
- 在启用了 required reviews 的仓库中，这类反馈本身就意味着 merge gate

因此在 `git-pr-review` 里：
- 如果 PR 存在阻断性问题，不应把它描述成“小瑕疵”
- 要明确区分“可 merge 但建议后补”与“当前不应 merge”

### 7. 需要显式说明风险与限制

好 PR 不应只讲优点。
更可靠的 PR 往往会主动说明：
- 已知限制
- 未覆盖场景
- 迁移 / 回滚风险
- 还需要谁确认

如果 PR 完全不提这些，而 diff 又涉及高风险路径，review 时要主动补这一层判断。

## 在 git-pr-review 里的使用方式

最终报告至少要回答：
- 目标是否清楚
- 描述是否充分
- 粒度是否合适
- 是否可验证
- reviewer / ownership 是否清晰
- 是否存在阻断 merge 的问题
- 风险和限制是否被诚实披露

## 使用提醒

这份参考是“默认基线”，不是死板 checklist。
如用户明确要求最新社区口径、特定组织规范、或当前 PR 场景明显超出这份基线，再联网补充即可。
