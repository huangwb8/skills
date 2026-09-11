# Verifier Pack 热插拔完善实施计划

## 通俗解释：究竟发生了什么

- **一句话说明：** Verifier 已经按独立目录包装好，但公共入口仍只会从固定货架取内置检查器，Skill 自带的检查器无法用同一方式发现和运行。
- **生活类比或具体场景：** 这像仓库已经统一了包裹标签和验货流程，但前台窗口只接受仓库自营商品，也只允许递交一种“文件”货物；其它合规包裹仍要工作人员绕到后台手工处理。
- **对应到本问题：** Pack 目录是包裹，索引和 ID 是标签，Registry/CLI 是前台窗口，subject/context/evidence 是不同货物的申报单。
- **改变前后：** 当前 Skill 本地 Verifier 只能由调用方自行拼装 Python API；改进后，CLI 和公开 Registry 都能显式加载 Skill/额外根目录、接收完整 JSON 请求、按声明执行并给出一致的 Gate 与指标。

## 专业判断：问题在哪里

- **当前现象：** Verifier CLI 固定加载内置目录、`run` 固定构造文件型 subject；Combined Registry 只能解析不能执行；新旧 Registry/Runner 重复登记内置元数据；两条 Gate 路径对 optional 未知结果的处理不同；CLI 没有正确统计 Contract 组件。
- **影响范围：** 使用 Skill 专用 Verifier、非文件 subject、Agent/human 组件或 required/advisory 声明的调用方，无法获得统一、可重放的执行闭环。
- **已知原因：** 目录化 Pack 和共享 Contract 层已经完成，但 CLI、兼容外观与声明加载仍停留在较早的内置示例阶段。

## 要达到什么目标

- **完成后的变化：** Verifier 和 State 都能从内置根、显式额外根或 Skill runtime 声明发现 Pack；Combined Registry 可执行；CLI 同时支持旧文件输入和完整 JSON 请求；Gate 与指标在不同入口保持一致。
- **不在本次处理范围：** 不重命名 Pack、不改变现有 Verifier 的领域命题和 1.0.0 Pack 版本、不自动执行未经显式选择的任意第三方目录、不发布 PyPI。

## 改进方向

### 对称的声明与发现入口

增加独立的 Skill Verifier 声明对象和 Registry 构建入口，支持受限于 Skill 根目录内的 `runtime.verifier_roots`，默认使用 `references/verifiers`。CLI 的 list/describe/run 都能显式选择 `--skill-root` 或重复 `--root`，两者互斥；本地脚本仍经过既有路径、信任和资源边界。

### 通用请求与执行闭环

保留 `--input` 文件兼容入口，新增互斥的 `--request-json`/`--request-file`，把完整 subject/context/evidence 交给 Pack。Skill 声明模式只允许运行已声明 Verifier，并把该项 required/advisory 语义应用到 Gate。

### 收敛兼容层和 Gate 语义

让 Combined Registry 代理到实际拥有 Pack 的 Filesystem Registry；让旧内置 Registry 从 `index.json` 派生，而不是维护第二份 ID/版本目录表；`run_atomic` 也从索引定位 Pack。统一 required fail、required unknown/pending、optional 非 pass 的 Gate 优先级。

### 修正审计指标并同步契约

Contract 执行时使用真实 component results 计算绑定率和执行者覆盖率。同步中英文 README、托管规范、公开导出、版本和根 CHANGELOG。

## 实施范围与顺序

1. 先补 Registry/声明 API 和对应单元测试，建立安全的发现边界。
2. 再接入 CLI 的 source、JSON 请求、声明限制与 Gate，保留旧命令兼容。
3. 收敛兼容 Registry/atomic 映射，统一 Gate 和 metrics。
4. 同步文档、版本、CHANGELOG 与 BAC，运行完整包测试、Ruff 和安装后发现验证。

## 如何确认完成

- 内置、额外根和 Skill 本地 Pack 均可 list/describe/run；越界 root、重复 ID、未声明 ID 和 source 冲突会拒绝。
- 文件兼容输入行为不变；JSON 请求可驱动 contract/schema/diff 等非文件 Verifier。
- required 失败拒绝，required 未完成等待或人工复核，optional 的失败/未知只告警。
- 新旧 Registry 得到同一内置 ID/版本集合；索引新增 Pack 时不再修改中央映射。
- CLI metrics 能看到实际 Contract component 和绑定比例。
- 包内完整测试、Ruff、构建/安装后资产发现、`git diff --check` 与 BAC 校验通过。

## 风险与待确认事项

- Skill 本地脚本具有代码执行风险，因此只接受用户显式给出的 `--skill-root`/`--root`；不扫描全局目录，并继续使用既有 `ContractPackExecutor` 的信任和资源限制。
- 旧 `PackRegistry`/`VerifierRunner` 是公开兼容 API，本轮保留外观；完全删除应留到未来主版本。
- 原子 Verifier 的 vacuous-pass 属于已公开命题语义；本轮通过结构化请求和文档警告降低误用，不在未保留旧版本目录的情况下静默改变判定。
