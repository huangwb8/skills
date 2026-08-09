# Data Model

`bug-context.json` 的目标是同时满足三件事：

1. 让 AI 能稳定重建 bug 背景
2. 让同一问题可以被稳定去重
3. 让后续公开上报时不必重新补环境信息

`RESOLUTION.md` 是独立的追加式闭环层。它不能改写或替代原始记录，只在修复与验证完成后创建。

## 顶层字段

- `schema_version`
- `bug_hash`
- `skill`
- `reporter`
- `bug`
- `environment`
- `tracking`
- `deduplication`

## 设计要点

- `skill` 保存 skill 名称、作者、来源路径、来源仓库
- `reporter` 保存展示名、GitHub 用户名；默认不再保留本地用户名
- `bug` 保存摘要、预期行为、实际行为、复现步骤、证据、临时 workaround
- `environment` 保存设备、OS、运行时、常见软件版本
- `tracking` 保存首次发现、最近发现、出现次数、是否已公开
- `deduplication.fingerprint_payload` 保存参与哈希的规范化字段，便于审计
- 所有自由文本字段在落盘前都要经过隐私清洗，避免把密钥、密码、身份信息、电话、邮箱、银行卡号与私密路径写入本地或公开副本

## 本地副本 vs 公开副本

当前版本默认采用“最小必要信息”策略，本地 `bug-context.json` 也不会再主动采集下列高风险字段：

- `reporter.local_username`
- `environment.device.hostname`
- `environment.runtime.cwd`
- `environment.runtime.local_username`
- `tracking.local_path`

若旧版本地记录仍含有上述字段，公开上报前必须生成脱敏副本，把它们替换为 `redacted` 或移除，避免公开仓库泄露本地隐私。

## 哈希策略

`bug_hash` 使用 `sha256`，基于规范化后的 bug 内容与环境指纹生成。

参与指纹的字段集合由 `config.yaml:hashing.stable_fields` 决定，脚本会按点路径从规范化 payload 中挑选字段后再计算哈希。

当前默认不把 `reporter` 放入哈希，原因是：

- 同一个人可能先在未登录 `gh` 的情况下收集 bug，后续再补 GitHub 身份
- 公开路径已经包含 `github_username`
- 这样可以减少“同一个 bug 仅因报告者身份补齐而重新生成新哈希”的重复

当前默认也不把 `reproduction_steps` 放入哈希，原因是：

- 同一 bug 在后续排查中常常会补充更多复现细节
- 如果把步骤文本直接纳入哈希，补写一条步骤就会错误地产生一个新 bug 目录
- 复现步骤仍然完整保留在 `bug-context.json` 与 `BUG_REPORT.md` 中，只是不参与去重指纹

## Resolution 模型

`RESOLUTION.md` 的 YAML frontmatter 固定包含：

- `status`：`fixed` 或 `duplicate`
- `canonical_root_cause`：稳定的 canonical 根因 ID
- `fixed_version_or_commit`：已验证的 skill 版本或源码 commit
- `resolved_at`：ISO 8601 时间
- `duplicate_of`：重复记录指向的 canonical bug；canonical 记录为 `null`
- `resolution_fingerprint`：忽略时间后的内容指纹，用于幂等判断

正文 `Verification` 至少保留一条可复核证据。已有 resolution 的指纹相同则视为幂等重跑，指纹不同则拒绝覆盖。
