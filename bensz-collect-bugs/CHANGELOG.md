# bensz-collect-bugs - 变更日志

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与语义化版本规范。

## [Unreleased]

### Added（新增）
- 新增 `scripts/resolve_bug.py` 与 `templates/RESOLUTION_TEMPLATE.md`：在保留原始 `BUG_REPORT.md` / `bug-context.json` 的前提下追加 `RESOLUTION.md`，支持 `fixed`、`duplicate`、`--dry-run` 与重复执行幂等检查。
- 新增 resolution 专项回归，覆盖缺少验证证据拒绝 fixed、duplicate 必须关联 canonical 记录、相同内容幂等和冲突内容拒绝覆盖。

### Changed（变更）
- 数据模型扩展为“原始证据 + 追加式 resolution”两层结构，版本号 `0.3.2 → 0.4.0`；每条 resolution 统一记录 canonical 根因、修复版本或 commit、验证证据、时间与重复关系。

## [0.3.2] - 2026-08-08

### Fixed（修复）
- 修复 Windows 中文 locale 下 `subprocess` 用系统编码（GBK）解码 `gh` 的 UTF-8 输出，导致 `UnicodeDecodeError` 并丢失子进程 stderr 的问题：`common.py` 的 `run_command` / `gh_auth_ok` 与 `report_bugs.py` 的 `gh_api` 显式指定 `encoding="utf-8", errors="replace"`，提升 macOS/Windows/Linux 跨平台一致性

## [0.3.1] - 2026-03-27

### Added（新增）
- 新增 `reporting.privacy_notice` 配置项，使 `BUG_REPORT.md` 的隐私提示由配置统一驱动
- 扩展 `qa/test_privacy_protection.py`，覆盖 `storage.path_pattern`、`hashing.stable_fields` 与 `privacy_notice` 的行为验证

### Changed（变更）
- `collect_bug.py` 与 `common.py` 改为真正读取 `config.yaml:storage.path_pattern` 与 `config.yaml:hashing.stable_fields`
- `report_bugs.py` 改为支持 `config.yaml:github.api_host`，便于在非默认 GitHub 主机上复用相同工作流
- `--reporter-display-name` 标记为已弃用且默认忽略，避免形成“参数可用但实际不生效”的误导

### Fixed（修复）
- 修复去重指纹结构与 `hashing.stable_fields` 默认路径不一致，导致配置声明无法完全生效的问题
- 修复若干死配置/硬编码文案造成的配置集中化与实现不一致问题

## [0.3.0] - 2026-03-27

### Added（新增）
- 新增 `privacy` 配置段：支持敏感文本自动脱敏、本地高风险字段最小化采集，以及统一的脱敏占位符格式
- 新增 `qa/test_privacy_protection.py` 自动化回归测试，覆盖本地记录脱敏、旧数据公开脱敏和常见敏感文本识别

### Changed（变更）
- `collect_bug.py` 默认不再采集或落盘本地用户名、主机名、当前工作目录与 `local_path` 等高风险个人信息
- `BUG_REPORT.md` 模板移除了本地用户名展示，并明确标注敏感信息会在本地记录与公开上报前自动脱敏
- `README.md`、`SKILL.md`、`references/DATA_MODEL.md`、`references/REPORTING_PROTOCOL.md` 全部同步为“最小必要信息”隐私策略

### Fixed（修复）
- 修复本地 `bug-context.json` 与 `BUG_REPORT.md` 可能残留密钥、密码、邮箱、电话、银行卡号、身份号码和私密路径的问题
- 修复旧版本历史 bug 在再次收集或公开上报时，敏感文本不会被升级清洗的缺口

## [0.2.0] - 2026-03-27

### Added（新增）
- 初始化 `bensz-collect-bugs` skill，定义本地 bug 归档目录 `~/.bensz-skills/bugs/`
- 新增 `scripts/collect_bug.py`：收集环境信息、计算稳定哈希、生成 `bug-context.json` 与 `BUG_REPORT.md`
- 新增 `scripts/report_bugs.py`：使用本机 `gh` 轻量上传新增 bug 到 `huangwb8/bensz-bugs`
- 新增 `templates/BUG_REPORT_TEMPLATE.md`、`references/DATA_MODEL.md`、`references/REPORTING_PROTOCOL.md`

### Changed（变更）
- 公开上报阶段新增脱敏副本生成，避免把本地用户名、主机名、工作目录、绝对路径等隐私信息上传到公开仓库
- `report_bugs.py --dry-run` 改为纯预演模式：只输出预计上传项，不修改本地状态
- 本地目录的报告者层级改为“优先 GitHub 用户名；缺失时使用 `pending-github-identity` 占位”，减少本地用户名泄露到路径中的概率
