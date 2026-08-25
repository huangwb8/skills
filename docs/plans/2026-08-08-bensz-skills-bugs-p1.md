# Bensz Skills Bug 修复综合计划 p1

## 问题是什么

`huangwb8/bensz-bugs` 有两种不同性质的入口：2 个公开 GitHub Issues，以及 99 条按目录保存的原始 Bug 记录。三份 p0 对公开 Issues #1、#2 的现象、根因和当前源码状态结论一致；对 99 条目录记录则只有一份报告做了广域静态映射，另外两份没有逐项复现，因此不能把 99 条记录直接等同为 99 个已经确认、可在本轮关闭的缺陷。

- **Issue #1：** `init-project` 在严格 GBK 控制台向 stdout/stderr 输出 emoji，可能抛出 `UnicodeEncodeError` 并中止初始化。
- **Issue #2：** `auto-test-project` 的文档已经采用任务级工作区，配置与四个路径消费脚本仍按旧 `.bensz-api/skills/` 模型创建或寻找文件。
- **影响：** #1 会让 Windows 用户得到失败或半途停止的初始化；#2 会破坏“一个逻辑任务只有一个已锁定 task root”的工作区契约，并让创建、验证和续跑互相找不到产物。
- **当前远端状态：** 2026-08-08 只读复核时，Issues #1、#2 均为 open、无评论。

### 已确认根因

| Bug | 当前源码证据 | 根因裁定 |
|---|---|---|
| Issue #1 / `init-project` | `scripts/generate.py` 在 BAC、自动模式、手动模式和错误提示等多处分支直接打印 `ℹ️`、`✅`、`📦` 等字符；入口没有输出流编码容错 | 这是输出边界缺失，不是某一个 emoji 或某一条 BAC 分支的问题 |
| Issue #2 / `auto-test-project` | `config.yaml` 1.3.1 仍配置 `.bensz-api/skills/auto-test-project/output/{plans,tests}`；`create_test_session.py`、`verify_test_session.py`、`verify_all_sessions.py` 和 `verify_skill.py` 都消费或假设该静态路径 | 2026-07-17 的工作区迁移只更新了文档，没有建立运行态 task-root 接口并同步全部路径消费者 |

## 要达到什么目标

- `init-project` 在 GBK、UTF-8、可重配置流和不可重配置流下都不会因装饰性 Unicode 输出中止；编码兼容层只处理编码失败，业务异常、退出码和错误分支继续按原逻辑传播。
- `auto-test-project` 的创建、单会话验证、批量验证和自检共用一个运行态路径解析规则；显式 task root 可被 A/B 轮和 continuation 原样复用，新任务不再创建 `.bensz-api/skills/`。
- 两个修复都有根因级自动化回归，版本、skill 文档、skill CHANGELOG 和项目根 CHANGELOG 一致。
- 所有本地门槛通过后，用脱敏证据关闭 GitHub Issues #1、#2。

### 本轮实际实施清单

| 优先级 | Bug / skill | 实施范围 | 远端动作 |
|---|---|---|---|
| P0 | Issue #2 / `auto-test-project` | 统一 task-root 解析、路径安全、continuation、legacy 只读验证、自检与文档口径 | 验证通过后评论并关闭 #2 |
| P0 | Issue #1 / `init-project` | 增加集中式 GBK 安全输出边界及自动/手动模式回归 | 验证通过后评论并关闭 #1 |

本轮正式源码只修改迁移前的 `pipelines/skills` 源码根（历史快照）中上述两个 skill 及该仓库的 `CHANGELOG.md`。该绝对路径不再作为当前源码入口；当前仓库实现位于 `skills/alpha/`。

## 改进方向

### 统一 `auto-test-project` 的运行态 task-root 接口

建立一个由四个脚本共同调用的路径解析器，避免创建端和验证端各自猜测目录。配置文件只保存 skill 边界内的相对后缀：

```text
task_root = <project-root>/.bensz-api/task-YYYYMMDD-HHMM-<description>[-a|-b|...]
skill_root = <task-root>/auto-test-project
plans     = <skill-root>/output/plans
tests     = <skill-root>/output/tests
```

`config.yaml:directories` 相应改为 `output/plans` 和 `output/tests`。不得把时间戳占位符、项目根或 `.bensz-api/skills/` 写回静态配置。

#### 创建接口

- `create_test_session.py` 保留 `--project-root`，新增 `--task-root`；调用方已经公开并锁定任务根时必须显式传入，脚本复用该目录，不重选、不改名、不迁移。
- 未传 `--task-root` 只表示“开始一个新的逻辑任务”。此时脚本在 `<project-root>/.bensz-api/` 下分配 `task-{当前分钟}-{task-description}`，`--task-description` 缺省为 `auto-test-project`；同分钟冲突用原子建目录方式依次选择短后缀。
- 脚本自行分配 task root 时，创建最小任务 `README.md` 和 `auto-test-project/input|output|log/`；传入已有 task root 时不得覆盖任务 README，只补齐该 skill 实际需要的边界目录。
- 输出继续返回会话目录，且帮助文本说明其父级 task root 可供 continuation 显式复用。不得“自动选择最近一个 task root”，以免把两个逻辑任务混在一起。

#### Continuation 与验证接口

- A 轮、B 轮、工具 continuation 和重复调用只有在传入同一个 `--task-root` 时才视为同一逻辑任务；已存在 task root 永远原样复用，即使同分钟存在相似目录。
- `verify_test_session.py` 与 `verify_all_sessions.py` 接受同一组 `--project-root`、`--task-root`，从 `<task-root>/auto-test-project/output/` 定位计划和会话；不能再依据静态目录层数反推项目根。
- `verify_skill.py` 在临时项目内先创建一个显式 task root，再让 A/B 创建和两种验证共同使用它。路径不存在等预期失败要追加到结构化 `failures`，不能泄漏为未捕获 traceback。
- 可把共享规则放入一个小型 `scripts/workspace_paths.py`；它只负责解析、分配和校验路径，不承载测试业务逻辑。

#### Legacy 规则

- `.bensz-api/skills/auto-test-project/` 只允许通过验证命令的显式 `--legacy-root` 读取；legacy 模式不创建、不覆盖、不迁移任何文件。
- 创建命令不提供 legacy 写入开关；验证命令也不得自动扫描或优先选择旧目录。
- 活跃的配置、默认值、CLI 示例和帮助文本中不得残留旧路径。旧路径只能出现在标注为“只读兼容”的说明和对应回归测试中。

#### 路径安全规则

- `--task-root` 可用绝对路径或相对 `--project-root` 的路径表达，但原始输入不得含 `..`，规范化后必须位于 `<project-root>/.bensz-api/` 内，且目录名必须符合 `task-YYYYMMDD-HHMM-<非空描述>` 及可选短冲突后缀。
- 拒绝项目外绝对路径、文件系统根、用户家目录、指向项目外的 symlink，以及 task root、skill root、plans/tests 路径中的 symlink 逃逸。
- 创建目录前先完成全部参数和边界校验；已有会话文件继续遵守“不带 `--overwrite` 就不覆盖”。
- 默认创建流程不得新建 `.bensz-api/skills/`；测试应把这一点作为显式否定断言。

### 为 `init-project` 建立不会吞业务异常的 GBK 输出边界

在 `generate.py` 第一次业务输出之前调用一个集中式控制台配置函数，同时处理 stdout 和 stderr：

- 保留宿主选择的现有编码；对支持 `reconfigure()` 的文本流只把 `errors` 调整为 `backslashreplace`（或等价的非崩溃策略），不强制切换 UTF-8。
- 对不支持 `reconfigure()` 的嵌入流使用最小代理：正常 `write()` 原样委托；只有底层明确抛出 `UnicodeEncodeError` 时，才按该流编码转义不可编码字符并重试一次。
- 代理应转发 flush、isatty、encoding 等现有属性；除 `UnicodeEncodeError` 外的写入异常必须继续抛出。
- 配置函数只捕获“流不支持重配置”所需的窄异常，不得用 `except Exception` 包围 `main()`、`generate_auto()`、BAC 安装、文件写入或智能合并。

这项裁定比逐个把 emoji 改成 ASCII 更小且更完整：公开 Issue 命中的装饰字符和动态项目路径中的其它不可编码字符都由同一边界处理；UTF-8 终端仍保留现有显示。业务失败不会被转换成成功，原退出码也不改变。

本轮不顺带修改 BAC 早返回或 Markdown 二级标题合并。它们是目录记录提出的独立根因，不是解决 GBK 崩溃的必要条件；若新增回归意外证明现有失败重试会破坏文件，再停止扩围并另立可审查修复项。

### 版本、文档与变更记录

- `auto-test-project/config.yaml` 作为版本单一来源，从 `1.3.1` 升至 `1.3.2`；更新 `SKILL.md`、`README.md`、涉及快速开始/严格验证的 references、CLI help 和 `CHANGELOG.md` 的 `[Unreleased]`。
- `init-project/config.yaml` 作为版本单一来源，从 `2.3.3` 升至 `2.3.4`；在 `SKILL.md`、`README.md` 和 `CHANGELOG.md` 的 `[Unreleased]` 说明跨平台控制台行为与退出语义不变。
- 修改前在仓库根 `CHANGELOG.md` 的 `[Unreleased]` 草拟两个 Fixed 条目，修改后补全根因、影响范围和验证摘要；合并现有未提交内容，不覆盖 `Prompts.md` 或用户其它脏改动。
- 不修改系统级安装副本，也不在本轮执行安装器。正式源码验证通过即可关闭对应源码缺陷；安装发布另属发布流程。

## 实施范围与顺序

1. 为 Issue #2 增加 task-root、continuation、legacy 和路径逃逸失败用例，再实现共享路径解析器并同步四个路径消费者。
2. 为 Issue #1 增加严格 GBK 失败用例，再实现窄范围输出兼容层；确认编码错误被处理而人为注入的普通 `OSError` 或业务异常仍传播。
3. 更新两个 skill 的配置版本、用户文档、skill CHANGELOG 与仓库根 CHANGELOG，执行静态旧路径守卫。
4. 运行两个 skill 的定向测试与现有自检，检查仓库 diff 没有越界或覆盖用户改动。
5. 再次只读获取 Issues #1/#2 当前状态；仍为 open 且各自验收全部通过时，发布脱敏评论并关闭，随后把 API 返回和验证摘要保存在本任务日志中。

## 如何确认完成

### `auto-test-project`

- 显式 task root 下创建 A 轮与 B 轮，二者都位于同一个 `auto-test-project/output/tests/`，计划位于同一个 `output/plans/`。
- 不传 task root 时只分配一个新任务；同分钟已有同名目录时使用不同短后缀且不覆盖原目录。
- 单会话严格验证、批量验证和 `verify_skill.py` 均通过；缺少路径时得到可读 failure 而不是 traceback。
- `..`、项目外绝对路径、非法目录名、外部 symlink 均返回非零且不写文件。
- 显式 legacy 验证可以读取 fixture；默认创建和默认验证均不扫描或写入 legacy 根。
- 临时项目内断言 `.bensz-api/skills/` 不存在；活跃源码与文档只在 legacy 说明/测试中出现旧路径。

### `init-project`

- 子进程以 `PYTHONIOENCODING=gbk:strict` 运行 `--auto --disable-bac`，退出 0、无 `UnicodeEncodeError`，核心生成物完整。
- 覆盖自动模式、手动模式、stdout、stderr 和至少一个 warning/error 分支；GBK 下不可显示字符可以被转义，但不能出现 traceback。
- UTF-8 环境的输出与生成结果保持兼容。
- 不提供 `reconfigure()` 的流不会引发兼容层自身错误；模拟普通 `OSError` 和业务异常时仍按原语义传播，证明兼容层没有吞异常。
- 重复运行保持现有幂等行为，CHANGELOG、`.gitignore` 和已有文档不因编码修复而重复或截断。

### 版本与仓库边界

- 两个 `config.yaml` 的版本分别为 `1.3.2`、`2.3.4`，文档与 CHANGELOG 不维护冲突版本。
- `git diff --check` 通过；相关 Python 文件可编译；两个定向测试集合与已有 skill 自检通过。
- 另外三个授权源码根无修改；`Prompts.md` 等任务开始前已有脏改动保持原样。

## 远端 fixed 闭环

本轮不扩展 `bensz-collect-bugs` 的 resolution schema。理由是 Issues #1/#2 本身已有 GitHub 的 comment + closed 状态，可完成用户要求的最小、公开、可审计闭环；为 99 条原始目录记录新增 `RESOLUTION.md`、JSON 字段或更新协议并不是关闭这两个 Issue 的必要条件，反而会把一次两项源码修复扩成数据模型和批量远端写入任务。

- #1 仅在严格 GBK 自动/手动回归、UTF-8 回归和异常传播测试全部通过后评论并关闭。
- #2 仅在创建、单会话验证、批量验证、自检、continuation、legacy 只读与路径安全测试全部通过后评论并关闭。
- 评论包含公开根因、修复版本、受影响文件类别和测试结果；不得包含本地用户名、主机名、绝对路径、工作目录、临时目录或凭据。
- 关闭前用 `gh api` 再次读取状态，避免盲写；如 Issue 已变化或测试未全过，保持 open 并记录阻塞，不用“部分修复”冒充 fixed。
- Issue #1 评论可列出三个同根因目录记录的公开 hash 并说明由 canonical Issue 覆盖，但不改写这些原始记录。

## 不在本次处理范围

### 99 条目录记录的裁定

| 类别 | 本轮处理 | 原因 |
|---|---|---|
| Issue #1 的 3 条重复 `init-project` GBK 记录 | 由 #1 的同一补丁和测试覆盖；不单独改代码或写 resolution 文件 | 同一根因不应重复实现；当前 resolution 协议未定义 |
| `init-project` BAC 早返回、Markdown 合并等独立记录 | 不实施 | 不是关闭 #1 的必要改动，且另外两份 p0 没有复现支持 |
| 目录盘点提出的 research、paper、knit、Rmd、installer、NSFC、validate、compact、notes 等候选 | 不实施、不标 fixed | 只有广域静态映射，缺少本轮逐项根因复现和完整回归；应按 skill/根因簇另开任务 |
| 当前源码看似已自然修复的 channel 幂等和 installer sparse checkout | 不改写、不标 fixed | 本轮没有执行其专项验收，不能以静态观察代替 fixed 证据 |
| 对应四个授权根之外源码的 31 条记录 | 不修改、不标 fixed | 没有获授权源码根，也无法建立可验证修复链 |

目录记录仍是后续任务的重要输入，但不能以数量驱动本轮批量改动。下一轮应按“一个 canonical 根因簇、一个复现、一个最小补丁、一组回归、一个明确 resolution”推进。

### 其它非目标

- 不对其它 skill 做相似字符串驱动的 GBK 或工作区批量重构。
- 不修改 `ChineseResearchLaTeX/skills`、`bensz-devtools/skills`、`dudu/skills`。
- 不提交 Git commit、不发布 release、不安装系统级 skill；这些动作没有被本综合计划视为关闭 Issues 的前置条件。

## 风险与停止条件

- 若实现时发现 task-root 接口会破坏现有会话验证格式，优先保留显式 legacy 只读兼容，不恢复旧默认写入。
- 若 GBK 兼容必须捕获业务级宽异常才能“通过”，视为方案失败；保持 Issue open，重新设计输出边界。
- 若现有用户脏改动与目标文件重叠，主 agent 应先做只读 diff 并增量合并，不得覆盖。
- 任一 Issue 只有部分测试通过时都不得关闭；远端状态变化或权限失败要记录真实结果，不做重复破坏性重试。
