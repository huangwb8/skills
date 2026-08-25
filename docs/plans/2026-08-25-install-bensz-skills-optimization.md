# install-bensz-skills 与仓库约定一致性优化计划

## 通俗解释：究竟发生了什么

- **一句话说明：** 这次目录改造已经让安装器在正常路径下可以工作，但旧目录、旧文档和两个安装入口仍各自保留了一部分旧规则，可能让系统把“旧版本”当成当前版本，或让维护者以为两种安装方式完全等价。
- **生活类比或具体场景：** 可以把安装器看成一个按地址送货的仓库系统。现在仓库已经搬到 `skills/alpha`，但送货员仍会先去旧地址 `pipelines/skills/alpha`；两套送货单（本地安装 manifest 与 bootstrap manifest）填写的字段也不同；墙上的操作手册还留着旧地址和已经拆掉的临时仓库链接。
- **对应到本问题：** 当前目录结构是新仓库地址，`install.py` 和 `bootstrap_install.py` 是两名送货员，manifest 是交接单，`AGENTS.md`/README/计划文档是操作手册。
- **改变前后：** 现在同时存在新旧目录时可能安装旧源，远程 bootstrap 生成的记录也不能按本地记录的方式读取；改进后默认只认规范 alpha 源，两入口使用同一份公开记录契约，文档只引用仍存在的路径，并且这些行为有回归测试保护。

## 专业判断：问题在哪里

- **当前现象：**
  - 本地安装器的自动发现顺序仍是 `pipelines/skills/alpha` 后才是 `skills/alpha`，与当前仓库约定的默认源不一致。
  - 本地安装器和 bootstrap 虽然都能写安装记录，但字段结构不同；这违反 `AGENTS.md` 对双入口可观测行为对齐的要求。
  - bootstrap 的远程源和 fallback legacy 名称保留硬编码，配置变化不能稳定传递到无依赖入口。
  - `AGENTS.md` 自身存在“六大原则”却列出八项、要求标题不编号却使用编号标题等自相矛盾；`Prompts.md` 的 alpha/beta 句子也有反义冲突。
  - 旧计划和 bug 归属文档仍引用已不存在的 task-root 或旧绝对源码路径；安装器 changelog 的 0.6.0 与 `config.yaml` 的 0.5.10 不一致。
  - changelog 提到的安装器测试文件已不存在，现有自动测试没有覆盖安装器的关键分支。
  - README、运行包和 bootstrap 对 Python 支持范围的表达不同；根级版本治理示例要求的 `config.yaml` 也不存在。
- **影响范围：** 使用同时保留旧目录的项目、依赖 manifest 做审计或增量更新的工具、离线或远程配置读取失败的 bootstrap 用户，以及后续维护仓库约定的开发者都会受到影响。单纯在当前仓库根目录执行一次本地安装目前不会触发这些边界问题。
- **已知原因或待验证假设：** 旧 `pipelines` 路径是历史兼容逻辑，在目录迁移后没有重新收紧；bootstrap 从原远程一键脚本抽取时保留了独立的数据结构和 fallback 常量；文档迁移只更新了主要入口，历史计划与版本元数据没有统一清理。需要在实施阶段确认是否仍要支持 `pipelines` 作为隐式兼容源，以及是否允许 bootstrap 在无法读取远程配置时继续使用 fallback 清单。

## 要达到什么目标

- **完成后的变化：**
  - 默认安装源唯一指向当前仓库的 `skills/alpha`；beta 和任何旧布局只有显式指定时才会参与。
  - 本地安装和 bootstrap 对安装目标、版本判断、legacy 清理、manifest 核心字段和退出码有一致的公开契约。
  - 系统文件、README、计划文档、版本信息和测试说明使用同一套目录、版本和支持范围口径。
  - 安装器关键边界由可重复的自动化测试覆盖，未来目录迁移或入口变更能尽早失败。
- **不在本次处理范围：** 不重写各业务 skill 的领域流程；不迁移或删除用户系统级已安装目录；不改变远程仓库、GitHub Issue、Release 或其它外部状态；不把 beta skill 提升为默认生产源；不为修复文档一致性而引入新的运行时依赖。

## 改进方向

### 收紧默认源发现并明确兼容边界

将 `install.py` 的隐式发现收敛为当前约定的 `./skills/alpha`。如果确实需要兼容旧 `pipelines/skills/alpha`，把它改成显式参数或明确的最后兜底，并在输出中标记“兼容源”，避免旧目录在存在新目录时抢占优先级。同步更新 `SKILL.md`、README 和帮助文本，保证用户看到的入口规则与代码一致。

对普通用户而言，这意味着安装器会从当前仓库的“正式地址”取货，不会因为旁边还留着旧仓库而悄悄装错版本。

### 建立双入口共享的安装记录契约

定义一个最小且向后兼容的 manifest 核心结构：来源、目标平台、目标根目录、每个 skill 的名称、MD5、安装状态、忽略原因和运行时间。允许本地入口额外记录本地源根、远程缓存等实现细节，但 bootstrap 不再缺少核心 skill 明细；旧 manifest 只读兼容，不覆盖用户历史记录。

同步梳理 `--remote --check/--auto` 与 bootstrap `--check/--force` 的语义，明确“预览、增量更新、强制重装”各自的行为和退出码。对同一 skill 在两个目标平台的统计，统一采用按名称去重的规则。

对普通用户而言，这意味着无论从哪个入口安装，安装历史都能用同一种方式理解和审计。

### 消除 bootstrap 的配置漂移

保留 bootstrap 的“仅标准库、无需克隆”的边界，但把可公开变化的远程源、alpha 路径和 legacy 名单集中到一个可获取的配置契约中。远程配置不可用时，要么安全失败并明确提示，要么使用带版本和来源标记的 fallback；不能静默把过期 fallback 当成完整配置。特别验证 `--skill` 选择性下载时 legacy 配置仍能正确加载。

对普通用户而言，这意味着配置更新只需改一个地方，首次安装器和已安装安装器不会各自遵循不同的旧清单。

### 整理系统约定与历史文档

统一 `AGENTS.md` 的原则数量、标题格式、测试边界、版本单一事实来源和安装入口描述；修正 `Prompts.md` 的 alpha/beta 反义句。检查 `CLAUDE.md` 的引用说明是否仍与实际工具行为一致。

对正式计划、bug 归属和迁移文档做一次可复现性清理：历史事实可以保留，但失效的绝对源码路径和已经不存在的 `.bensz-api` task-root 应改为当前仓库相对路径、归档说明或明确的“历史快照”标记。

### 统一版本与运行环境口径

确定项目级版本和安装器 skill 版本的单一事实来源：若仓库级版本需要治理，新增并纳入约定的根级配置；否则删除会误导执行者的根级 `project_info` 示例，明确以 Git tag 或其它既定来源为准。同步安装器 `config.yaml`、skill changelog、根级 changelog 和 README 的版本描述。

同时明确支持矩阵：区分“仓库开发包”的 Python 要求与“标准库 bootstrap”的最低 Python 要求，并让 README、脚本检查和 CI 使用同一口径。

### 补齐安装器回归验证

增加不依赖真实用户 HOME 和远程写入的测试场景，至少覆盖：规范 alpha 优先、旧 pipelines 兼容边界、beta 默认排除、显式 beta、skill 过滤、重复安装的 MD5 跳过、legacy 清理保护、两个目标平台、dry-run 不写入、远程失败退出码、bootstrap 选择性解压和 manifest 核心字段。测试产物遵循 `AGENTS.md` 的 `tmp/` 与任务工作区约定，不把运行缓存写入 skill 目录。

对普通用户而言，这意味着下一次目录调整或入口重构会在发布前被自动检查，而不是等到系统级技能已经装错后才发现。

## 实施范围与顺序

1. 先锁定公开契约：确认默认源是否彻底移除隐式 `pipelines`，确认 manifest 核心字段、远程模式语义、版本来源和 Python 支持矩阵；把这些决策写入计划变更说明。
2. 再调整本地发现、bootstrap 配置读取和共享 manifest 生成逻辑；保持已有系统级目录可读，避免在安装过程中扩大删除范围。
3. 随后同步更新 `AGENTS.md`、`CLAUDE.md`、README、Skill 文档、版本与 changelog，并清理或标记失效历史链接。
4. 最后补齐隔离环境回归测试，执行本地与 bootstrap 的 dry-run/真实临时安装对照，确认 alpha、beta、legacy、退出码和 manifest 行为后再考虑发布版本变更。

## 如何确认完成

- 在同时存在 `pipelines/skills/alpha` 与 `skills/alpha` 的临时项目中，默认安装只使用规范 alpha；旧路径只有显式兼容选项才会被使用。
- 默认安装不会触碰 beta；显式 beta 安装只处理用户指定的源。
- 本地入口和 bootstrap 对同一组临时 skill 生成可互相读取的 manifest 核心字段，未变化 skill 的跳过结果和失败退出码一致。
- 远程源、legacy 名单、版本号、Python 支持矩阵在配置、脚本、README、SKILL 和 changelog 中没有互相矛盾的说法。
- 历史计划中的引用要么可解析到当前仓库文件，要么明确标为不可复现的历史快照；不再把失效绝对路径当作当前源码位置。
- 安装器专项测试通过，且根级 `pytest -q`、两个安装脚本的语法检查、隔离 HOME 本地安装和 bootstrap dry-run 均通过。
- 真实用户 HOME、远程仓库和系统级已安装 skill 未被测试过程写入、删除或覆盖。

## 风险与待确认事项

- 是否仍需要隐式兼容 `pipelines/skills/alpha`？若需要，必须确定优先级、告警文案和最终移除时间；否则应直接删除该隐式分支。
- bootstrap 在无法读取远程配置时，是安全失败还是允许带明确版本号的 fallback？这会影响首次安装在弱网环境下的可用性与 legacy 清理完整性。
- manifest 结构一旦统一，是否已有外部工具依赖当前任一入口的旧字段？实施前应先搜索仓库和已知消费者，再决定兼容字段保留期限。
- 项目级版本究竟由根配置、Git tag 还是其它发布元数据负责？未作决定前不要单独提升 `0.6.0` 或修改根版本。
- 当前工作区已有 `Prompts.md` 修改和旧文档删除；实施时应保留用户改动，并在提交前区分本轮改动与既有未提交状态。

## 技术补充（按需阅读）

- 相关源码：`skills/alpha/install-bensz-skills/scripts/install.py`、`skills/alpha/install-bensz-skills/scripts/bootstrap_install.py`。
- 相关约定：`AGENTS.md`、`CLAUDE.md`、`skills/alpha/install-bensz-skills/SKILL.md`、`skills/alpha/install-bensz-skills/config.yaml`。
- 当前验证基线：`pytest -q` 通过 7 项；本地 alpha 隔离安装 15 个 skill 成功；bootstrap 的 `general + install-bensz-skills + --check` 成功。
