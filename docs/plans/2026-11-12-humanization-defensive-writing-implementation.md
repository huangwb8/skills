# humanization 防御性写作实施对账

依据 [原计划](2026-11-12-humanization-defensive-writing-optimization.md)，实施范围为 P0–P2。基线为 humanization 2.1.0，提交与未提交状态已保存至本轮任务工作区。生产安装器已确认 BSK 2.1.6，使用托管 Python 3.12.14。架构核验由 verifier-state-architect 完成，后续源码落地由 skill-creator 承担。

## 删除影响与复用判断

保留 revision-readiness：删除会失去语义、格式及证据强度保护。新增 defensive-framing：单独保真不能拒绝虽未改错意思但保留大量假想反驳的稿件；独立结果也能分别追踪误伤和收益。保留 working/ready，不新增阶段；它们已经覆盖待审查、重试和绑定批准。

| 能力 | 决策 | 依据与边界 |
| --- | --- | --- |
| Pack 发现、绑定、结果、Gate、transition、重放 | 复用生产 BSK | 现有公开 API 支持多个 required；无需复制事件或 Gate |
| defensive-framing | Skill 专属混合 Pack | 写作语域决定必要性；没有跨不相邻领域稳定复用证据，不提升到 Kernel |
| 审查记录与严重异议核验 | Skill 共用 helper | 两个命题共享文件/身份/投票结构；领域分类与裁决仍归各 Pack |
| working → ready | 保留现有 State | 两项 required 都通过才放行；失败仍 working，五轮后只能交付未获批草案 |

## 最小契约与实现顺序

P0：新增五问判别与六类处置，定位线索的脚本不判断语言质量。两个标准 ComponentResult 分别绑定当前 handoff；同组三名真实审查者分别投票。RESULT.md 内的结构化记录绑定 run/visit/attempt、证据哈希、reviewer ID 和两命题结果。汇总记录引用文件哈希并复算票数，拒绝重复文件、旧轮、漏票和未结案的实质异议；驳回须有原文/候选锚点及理由，修复须新 attempt 重审。

P1：更新主流程、两个 Pack、运行 schema、双语 README 与回归。脚本只验证结构、身份、锚点、票数和结案记录；不能认证独立身份或判断结案是否正确。BSK 仍负责真实 Gate 和迁移。无论 ordinary English、LaTeX、keep_original、diagnosis_only，都保留原行为及语义审查。

P2：12 个开发单元与 24 个独立保留合成单元，对照基线、仅规则和双命题审查，保留原文为对照，每条件两次生成。记录实际覆盖与未执行项目；用户已说明暂无真实稿件，因此不能宣称完成真实长文/作者评价或证明默认强制门禁的增量收益。代码在开发源交付，不发布、不安装；真实长文与作者评价仍是默认推广前的质量门槛。

## 兼容、恢复与验收

新增 required 和结构化审查证据改变批准合同，Skill 使用 3.0.0；revision-readiness 使用 2.0.0，新 Pack 使用 1.0.0。用户文本参数与控制回执协议保持不变。旧工作区、旧事件和回执不改写；旧批准只在原契约快照下读回，新源码拒绝旧运行的资产漂移，不将历史 pass 升格为双门禁批准。

验收覆盖双 Gate 缺失/失败/不确定、重复/错绑 reviewer、空审查/假锚点、实质异议结案、哈希漂移、重试/重放/中断、安装副本发现和只读资产。成功链使用真实宿主审查；合成协议回归单独标记。缓存集中在 .bensz-api，运行夹具在 tmp。若新增审查无增量收益，保留规则并在后续作者评估后撤回或降为 advisory；本轮不擅自发布。
