# Bensz Bugs 重复缺陷聚类修复计划

计划日期：2026-08-09

## 问题是什么

`huangwb8/bensz-bugs` 当前有 99 条目录化记录。此前综合计划正确识别了大量重复，但把“缺少逐条复现”作为主要收缩理由，没有充分利用重复报告本身提供的证据：当多个独立 hash 在不同任务或环境中反复指向同一现象、同一代码边界和同一修复方向时，重复不是噪音，而是缺陷稳定存在、影响面较大和应当优先修复的信号。

这 99 条记录覆盖 21 个远端 skill 名称；合并 `systematic-literature-review` 旧名后，对应 20 个当前 skill 身份。记录分布高度集中：`knit-rmd-html` 21 条、`bensz-rmd-rules` 16 条、`auto-draw-plot` 14 条、`research-literature-review` 9 条，仅这四个 skill 就占 60 条。

不调整处理方式会产生两个后果：高频、可稳定复现的缺陷长期保持 unresolved；修复后也缺少目录记录级的统一 resolution，无法把一个 canonical 根因与全部重复报告可靠关联。

## 要达到什么目标

- 把 99 条记录整理成可审计的 canonical 根因簇，每个簇明确证据数、受影响 skill、风险、源码位置、验证方式和重复关系。
- 把重复次数作为置信度和优先级加成：同根因报告越多，越应尽早建立复现并修复，而不是越容易被排除。
- 对高频簇执行“一次根因修复、多条记录共同验收”，避免重复写相同补丁。
- 为目录化记录建立追加式 fixed 闭环，使 canonical 根因、重复记录、修复版本和验证证据可追溯。
- 保持必要的防误合并门槛：只有现象、触发条件、代码边界和修复方向一致时才归为同一根因。

本计划不把 99 条记录机械地变成 99 个代码任务，也不因名称相似而跨 skill 强行抽象公共兼容库。单例的 critical/high 缺陷仍可凭影响进入高优先级。

## 记录全景

| Skill | 记录数 | 主要根因簇 |
|---|---:|---|
| knit-rmd-html | 21 | Pandoc 可执行文件发现 14；R 输出解码 7 |
| bensz-rmd-rules | 16 | GBK 状态输出 13；DT helper、公式数字和 PDF 预览兼容 |
| auto-draw-plot | 14 | edits 请求构造、provider 资格/重试、画质与 JPEG 契约，以及若干单例 |
| research-literature-review | 9 | resume 状态覆盖、JSONL 切分、配置路径边界，以及 Bib/OpenAlex/GBK 单例 |
| init-project | 6 | GBK 输出 3、Markdown 合并 2、BAC 失败重试 1 |
| paper-explain-figures | 4 | 旧工作区 2、.DS_Store 审计误报 2 |
| sub2api-reimbursement | 4 | detail-only 可见性 2、发票订单锚定与备注策略各 1 |
| sub2api-summary | 4 | 邮箱脱敏遗漏 3、Cloudflare User-Agent 1 |
| docx | 3 | TemporaryDirectory Python 3.9 兼容 2、验证器运行时门槛 1 |
| install-bensz-skills | 3 | source filter、Windows 清理、sparse checkout 各 1 |
| benszai-xiaohongshu | 3 | 快照装饰符和固定备注造成语义误导 |
| nsfc-ref-alignment | 2 | Python 3.12 DOI regex、自定义 input 宏 |
| validate-md-ref | 2 | 站内 anchor、HEAD-only 误判 |
| bac-contribution-ledger / bensz-auto-contribution | 2 | Git remote 后置添加导致根身份失效 |
| 其余 7 个 skill | 7 | awesome-code、channel、notes、compact、complete-example、xlsx 等单例 |
| **合计** | **99** | 旧名 systematic-literature-review 已并入 research-literature-review |

## 优先确认的重复根因

### Windows R Markdown 工具链

`knit-rmd-html` 的 21 条记录实际上形成两个高度确定的根因：14 条指向 Windows Pandoc ZIP 布局和 `pandoc.exe` 发现逻辑，7 条指向用 GBK 解码 R 的 UTF-8 子进程输出。两簇都应直接进入首批修复，不再要求每一条报告单独证明一次同样的事实。

`bensz-rmd-rules` 的 13 条 GBK 报告覆盖成功、失败和不同检查器分支，说明问题不是某一个 emoji，而是整个 CLI 输出边界缺少非 UTF-8 兼容策略。另有两条专门记录和一条复合记录共同确认 `render_dt_output` helper 漏检，应作为第二个 canonical 根因处理。

### 状态、隐私与数据完整性

`research-literature-review` 有两条 critical 记录指向 `resume-from` 跳过已有状态并覆盖 checkpoint；这是高置信的数据损失风险。JSONL 根因由两个 hash 支持，其中一个 `occurrence_count=2`，至少代表三次出现。配置路径跨工作目录失效也有两条独立记录。

`sub2api-summary` 的三条记录共同指向通用 `user` 或 `recent_orders` 中的邮箱脱敏遗漏。由于涉及隐私，优先级不应低于记录数更多但影响较轻的兼容性问题。

BAC 的两个历史名称各有一条记录，现象均为初始化后新增 Git remote 导致根身份变化、账本不能继续追加，应合并为一个跨名称 canonical 根因。

### 工作区与审计契约

`paper-explain-figures` 的两条旧工作区记录共同证明脚本没有正确服从调用方 task root；另两条记录共同证明 `.DS_Store` 会触发错误的越界写入告警。两簇分别修复，不应把工作区迁移和审计忽略规则混成一个补丁。

`init-project` 的 GBK 根因已有三条目录记录和公开 Issue #1 支持，且已在 2.3.4 修复。下一步应把三条重复记录关联到同一 resolution。其余两条 Markdown 合并记录共同指向标题解析边界，但仍需分别覆盖 fenced code block 和二级/三级标题识别。

### Provider 与请求契约

`auto-draw-plot` 的 14 条记录不是一个根因，但存在三个明显重复簇：四条与 image-to-image / async edits 请求构造相关，三条与 provider 资格、计费错误和重试分类相关，两条与画质和 JPEG 输出契约相关。先用最小复现判断每簇最终是一项还是两项底层缺陷，再按共享请求边界修复；剩余单例分别保留。

### 跨 skill 运行时兼容

`docx` 的两条记录和 `xlsx` 的一条记录都指向 Python 3.9 不支持 `TemporaryDirectory(ignore_cleanup_errors=...)`。这是跨 skill 的同类根因，但应在各自源码中采用一致的小范围兼容方案和共享验收矩阵，不为三处调用新建额外公共包。

## 改进方向

### 建立 canonical 根因清单

为每个根因簇指定唯一 canonical ID，并保存以下信息：涉及的远端路径、报告数与总 occurrence、共同现象、已确认代码边界、置信度、风险等级、受影响版本和待验证假设。重复记录通过 `duplicate_of` 指向 canonical 根因，但保留原始报告不覆盖。

聚类门槛同时要求四项一致：可观察症状、触发条件、失败代码边界、预期修复。只共享“Windows”“编码”或“路径”等关键词的记录不能自动合并。

### 按证据强度和影响排序

首批处理高频且边界清晰的簇：`knit-rmd-html` 两簇、`bensz-rmd-rules` GBK 和 helper 两簇。随后处理记录数较少但风险更高的 research 状态覆盖、sub2api 脱敏和 BAC 身份稳定性。

第二批处理 `auto-draw-plot` 的三个重复簇、`paper-explain-figures` 两簇、`init-project` Markdown 合并、research JSONL/配置路径，以及 docx/xlsx 兼容簇。单例缺陷按 severity 和复现成本插入，不等待所有重复簇完成。

### 一簇一修复闭环

每个 canonical 根因只实施一次最小修复，但回归矩阵要覆盖该簇中不同报告提供的触发分支。例如 GBK 簇必须覆盖成功和失败状态，Pandoc 簇必须覆盖不同 ZIP 布局，resume 簇必须覆盖已有 checkpoint 与显式起始阶段组合。

如果复现显示一个簇其实包含两个失败边界，立即拆分 canonical ID，不为了减少任务数量而强行合并。

### 增加目录记录 resolution 协议

在 `bensz-collect-bugs` 中增加追加式 resolution 能力，至少记录 `status`、`canonical_root_cause`、`fixed_version_or_commit`、`verification`、`resolved_at` 和 `duplicate_of`。原始 `BUG_REPORT.md` 与 `bug-context.json` 保持不变，避免破坏证据和历史 hash。

只有源码修复、专项回归和当前版本核对全部通过后，canonical 记录及其已覆盖的重复记录才能标记 fixed。当前源码看似已经修复的 channel 幂等和 installer sparse checkout，也必须先执行专项验收。

### 重新核对源码归属

实施前为 20 个当前 skill 身份逐一确认正式源码根、当前名称和版本。此前“无法映射”不能仅凭目录名称裁定；同名源码存在时还要核对是否为报告涉及的实现。确实不在四个授权根的项目，列出缺失源码和所需授权，不再笼统归入一个 31 条集合。

## 实施范围与顺序

1. 完成 99 条记录的 canonical 聚类表和源码映射，优先确认上述高频簇，不改写原始报告。
2. 为 `bensz-collect-bugs` 设计并验证追加式 resolution 协议，使后续批量关联重复记录有正式数据模型。
3. 修复 Windows R Markdown 工具链的四个高频根因簇，并用所有报告分支构建回归矩阵。
4. 修复 research 状态覆盖、sub2api 脱敏和 BAC 身份稳定性等高影响簇。
5. 处理 provider、工作区、解析和运行时兼容等第二批重复簇，再按严重度处理剩余单例。
6. 每个 canonical 根因完成后更新对应 skill 版本、README、CHANGELOG 和根项目 CHANGELOG，并把所有已覆盖重复记录追加为 fixed/duplicate resolution。

## 如何确认完成

- 99 条目录记录全部出现在聚类清单中，每条恰好属于一个 canonical 根因或明确标记为独立单例，不丢失、不重复计数。
- 21 个远端目录名与 20 个当前 skill 身份的旧名映射清晰，正式源码位置和授权状态逐项确认。
- 每个重复簇都有至少一个可稳定失败的 canonical 复现；不同报告提供的关键分支进入同一回归矩阵。
- 修复后的专项测试、skill 自检和项目级回归全部通过，版本与文档一致。
- resolution 工具支持 dry-run、重复执行幂等、只追加不覆盖，并拒绝在缺少验证证据时标记 fixed。
- 已修复簇的所有重复记录都能追溯到同一个 canonical 根因、修复版本和验证摘要；未修复记录保持 open/unresolved。
- GitHub Issues 与目录化记录的状态一致，不再出现 Issue 已关闭但同根因目录记录无法判断状态的情况。

## 风险与待确认事项

- 相似症状可能来自不同代码边界，尤其是 `auto-draw-plot` edits 和 provider 错误处理；必须先复现再决定合并粒度。
- `occurrence_count` 只直接证明同一 hash 的重复出现；不同 hash 的语义聚类仍需人工和测试双重确认。
- 部分 skill 可能已在后续版本自然修复。应验证后补 resolution，不重复改写源码，也不能仅凭静态阅读标 fixed。
- `sub2api-*`、BAC 和其它独立仓库若不在当前授权根，需要先确认正式源码位置和写入授权；这不影响先完成聚类和复现设计。
- resolution 协议属于 `bensz-collect-bugs` 的行为扩展，应先定义兼容格式和幂等规则，再批量写入远端记录。
