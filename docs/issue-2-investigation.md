# GitHub issue #2 安全调查

调查日期：2026-10-03。对象：[huangwb8/skills#2](https://github.com/huangwb8/skills/issues/2)。

后续处理：2026-10-03，用户明确要求删除该 issue，已执行删除；再次通过 GitHub API 查询返回 HTTP 410，响应明确为 `This issue was deleted`。下文保留删除前的调查结论和执行记录。

## 结论

现有公开证据更支持“批量推广、邀请收录”，未发现足以认定为钓鱼、恶意代码传播或提示注入攻击的内容。推广行为明显，但不能据此认定发帖人具有恶意。此结论仅适用于所检查的 issue、公开记录和文档，不等于对第三方软件或网站的安全认证。

## 证据与判断

| 检查对象 | 已确认事实 | 判断 |
|---|---|---|
| Issue 正文 | 2026-09-14 创建，邀请向 awesome-ai-plugins 提交 README 条目；正文四个链接均直接指向 github.com，包括本仓库、目标仓库、README 编辑页及 CONTRIBUTING.md；截至调查时没有评论或时间线事件 | 未见索要凭据、下载附件、执行命令、伪装域名或要求 AI 忽略指令的内容 |
| 发帖人与目标仓库的关系 | [PR #85](https://github.com/hashgraph-online/awesome-ai-plugins/pull/85) 的作者为 zerocodefast，GitHub 标记为 COLLABORATOR，2026-08-14 被维护者合并；贡献者列表亦包含此账号 | 其“我们维护该目录”的说法有公开记录支持；不构成对身份及软件安全的全面保证 |
| 批量行为 | GitHub 搜索返回该账号创建的 issue 共 922 条，其中含 awesome-ai-plugins 的 917 条；抽查最近 6 条，均为相似收录邀请，替换项目介绍、名称和链接 | 很可能是模板化或自动化推广；不能仅凭模板证明由 AI 或机器人发布 |
| 投稿指南 | [当前 CONTRIBUTING.md](https://github.com/hashgraph-online/awesome-ai-plugins/blob/main/CONTRIBUTING.md) 推荐运行 plugin-scanner，推荐在来源仓库添加扫描 CI；CI 可选，未添加会降低其平台注册评分 10%；目录自身的集中扫描需通过 | 邀请包含推广自家工具和评分体系的后续路径；并非单纯无利益关系的推荐 |
| Issue 发布时的规则 | 核对 2026-09-14 前最近一次修改 CONTRIBUTING.md 的提交 [436805e](https://github.com/hashgraph-online/awesome-ai-plugins/blob/436805e10c7debd4b420a6ea2536ee0b2cd68550/CONTRIBUTING.md)：来源仓库 CI 已明确可选，集中扫描当时为 advisory | 不能把更早时期的强制 CI 要求当作本 issue 发布时的规则 |
| 其他维护者的反馈 | [claude-plugins#2418 评论](https://github.com/laurigates/claude-plugins/issues/2418#issuecomment-5341243090) 曾指出“只收录”的描述与当时第三方 CI 接入要求不一致，并因此拒绝；该评论也表示其抽查未发现扫描路径向 hol.org 传出数据 | 这是第三方维护者的历史观察，说明曾有范围描述争议；不能替代本次代码审计或证明当前规则仍相同 |
| 扫描工具与 Action | 抽查 [SCANNER_GUIDE.md](https://github.com/hashgraph-online/awesome-ai-plugins/blob/main/SCANNER_GUIDE.md) 和 [Action 安装入口](https://github.com/hashgraph-online/ai-plugin-scanner-action/blob/main/action.yml)：示例限制 contents: read，不持久保存 checkout 凭据，固定 Action SHA；安装入口包含 wheel 哈希及 PyPI 来源验证；在线分析、SARIF 上传及提交功能默认关闭 | 有可见的供应链保护措施；未全面审计 scanner 代码及依赖，不能断言运行安全 |
| 平台认领路径 | [README 的 Claim Your Plugin](https://github.com/hashgraph-online/awesome-ai-plugins#claim-your-plugin) 引导进入 hol.org，使用 GitHub 登录及授权；文档称读取资料、邮箱和公开组织成员信息 | 与普通目录收录属于不同的授权动作；本次没有登录网站或验证实际 OAuth 权限 |

计数为调查时 GitHub Search API 的返回值，可能随后变化。对 issue 评论、事件、正文及仓库文档的读取均通过本机 gh API 完成。

## 建议

- 若不需要第三方收录，可忽略；若希望保持 issue 列表只承载问题和需求，可按推广内容关闭。
- 若愿意收录，先仅考虑公开 README 条目；安装扫描工具、接入 Action 和授权第三方网站应分别评估，不能因这条邀请直接视为必需步骤。
- 当前证据不足以按“恶意攻击”定性或举报。批量推广是否属于垃圾信息，可按项目维护政策判断。

## 调查边界和执行记录

本次未执行第三方安装命令、扫描器或 Action；未提交 PR、回复、关闭 issue 或授权第三方网站。未修改 Skill 或运行时源代码。

证据摘要及验证记录位于本轮固定工作区 `.bensz-api/task-20261003-1538-issue-2-investigation/`；贡献记录追加到 `docs/contribution.bac`，保留其既有未提交改动。
