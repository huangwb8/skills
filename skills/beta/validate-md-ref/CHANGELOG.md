# 变更日志

本文件记录 validate-md-ref 技能的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### Changed（变更）
- **Kernel Verifier 接入**：验证脚本改为薄封装，调用内置 `bsk verifier run markdown.references.v1`；Skill 只声明命令、所需 verifier 和标签，`--events`、`--run-id`、`--attempt-id` 用于可选审计记录。
- **Verifier Pack 声明补齐**：`verifier-pack.yaml` 增加公开命令、所需 verifier ID 与标签，便于 AI 或工具发现调用契约。

### Added（新增）
- 接入 `bensz-skill-kernel` Verifier Pack：以版本化 `hybrid` 契约输出证据快照、规则结果、语义检查缺口与保守 Gate 决策；保留原有 JSON 字段以兼容既有调用方。

### Fixed（修复）
- 站内 `#anchor` 改为在当前 Markdown 的显式 HTML anchor 与标题 slug 中本地校验，不再作为非法外部 URL 计入失败。
- 外部 URL 的 HEAD 请求返回 403/405 时执行一次有限 GET 回退，避免把“禁止 HEAD、允许 GET”的页面误判为不可访问；版本号 `0.2.0 → 0.2.1`。

### Added（新增）
- HTML `<a>` 标签支持：识别和验证 HTML 格式的超链接（`<a href="URL">文本</a>`）

### Changed（变更）
- **SKILL.md**：
  - 更新引用模式说明，增加 HTML `<a>` 标签描述
  - 更新"当前实现范围"到 v0.2.0
- **scripts/validate_links.py**：
  - 新增 `html_tag` 引用类型
  - 正则表达式支持单引号和双引号包裹的 href 值
  - 不区分大小写匹配 `<a>` 标签（`<A>`、`<a>` 均可识别）

---

## [0.1.1] - 2026-01-18

### Added（新增）
- 跨目录路径定位：脚本自动定位技能根目录，支持从任意工作目录调用
- 多层回退机制：通过 `__file__`、环境变量、常见路径探测自动定位配置文件
- 路径安全策略优化：允许验证任意可访问文件，同时防止路径遍历攻击

### Changed（变更）
- **scripts/validate_links.py**：
  - 新增 `get_skill_root()` 和 `get_skill_root_cached()` 函数实现自动路径定位
  - 新增 `get_config_path()` 函数自动获取默认配置文件路径
  - 优化 `validate_path()` 函数：放宽路径限制，允许跨目录验证文件
  - 配置文件加载逻辑：默认使用技能内 config.yaml，无需手动指定
- **SKILL.md**：
  - 更新工作流程说明：明确 `python3 scripts/validate_links.py` 调用方式
  - 新增"技术实现"章节：详细说明自动路径定位机制
  - 更新"输入要求"：说明配置文件自动加载机制
  - 更新"当前实现范围"：标注自动配置加载功能

### Fixed（修复）
- **P0**：跨目录调用失败 - 相对路径 `scripts/validate_links.py` 在不同工作目录下无法解析
- **P0**：配置文件路径硬编码 - 必须手动指定配置文件路径，缺乏灵活性

---

## [0.1.1] - 2026-01-18

### Added（新增）
- URL 安全验证：检查 URL 格式，防止命令注入攻击
- 路径遍历防护：使用 `Path.resolve()` 验证文件路径在允许范围内
- 跨平台超时机制：使用 `subprocess.check_output(timeout=)` 替代 `signal.SIGALRM`
- 错误处理改进：yaml 加载失败时输出明确的错误提示

### Changed（变更）
- **SKILL.md**：
  - 聚焦到已实现的功能（引用提取 + URL 验证）
  - 删除未实现功能的描述（内容对比、无效链接处理、引用重编号）
  - 增加"注意事项"说明当前实现范围
  - 更新输出规范，使用实际的 JSON 格式
- **config.yaml**：
  - 删除 `concurrent_checks` 配置（未实现）
  - 删除 `renumbering` 配置（未实现）
  - 删除 `invalid_link_action` 和 `placeholder_text` 配置（未实现）
  - 删除 `content_comparison` 配置（未实现）
  - 删除 `reference_patterns` 配置（与代码重复）
  - 简化为只包含实际生效的配置项
- **scripts/validate_links.py**：
  - 移除 `signal` 模块依赖（Windows 不兼容）
  - 使用 `subprocess.TimeoutExpired` 捕获超时
  - 改进配置加载逻辑（空配置文件处理）
  - 增加路径验证函数 `validate_path()`

### Fixed（修复）
- **P0-1**：命令注入风险 - URL 未经验证直接传递给 curl
- **P0-2**：路径遍历风险 - 未验证文件路径是否在允许范围内
- **P0-3**：架构缺陷 - 工作流描述与实际实现严重脱节
- **P1-1**：过度设计 - `concurrent_checks` 配置项未实现
- **P1-2**：过度设计 - `renumbering.format` 配置项无效
- **P1-3**：一致性问题 - SKILL.md 与 config.yaml 的无效链接处理方式描述不一致
- **P1-4**：冗余检查 - `content_comparison` 配置项无效
- **P1-5**：跨平台兼容性 - `signal.SIGALRM` 在 Windows 上不可用
- **P1-6**：错误处理不完整 - config.yaml 加载失败时降级到空配置
- **P1-7**：一致性 - `reference_patterns` 配置与实际代码重复
- **Bug**：解析 HTTP 状态码时出错（curl 输出格式解析有误）

### Security（安全）
- URL 格式验证：防止命令注入攻击
- 路径规范化：防止路径遍历攻击
- 协议限制：仅支持 http/https

---

## [0.1.0] - 2026-01-13

### Added（新增）
- 初始化技能，实现核心功能
- 引用提取：支持标准链接、参考文献、脚注格式
- URL 验证：使用 curl 检查可达性
- 域名过滤：支持白名单/黑名单配置
