# Reporting Protocol

## 本地阶段

- 只写入 `~/.bensz-skills/bugs/`
- 不修改用户本地已安装 skills 的源代码
- 落盘前先对自由文本做敏感信息清洗，严禁把密钥、密码、身份信息、电话、邮箱、银行卡号和私密路径写进记录
- 每次记录都更新 `tracking.last_seen_at`
- 同一 `bug_hash` 再次出现时，只增加 `tracking.occurrence_count`
- 默认不记录本地用户名、主机名、工作目录、local_path 等高风险个人字段

## 公开阶段

- 必须使用用户本机的 `gh`
- 如使用 GitHub Enterprise，调用时需遵循 `config.yaml:github.api_host`
- 先检查 `gh auth status`
- 若未登录，先引导执行 `gh auth login`
- 先验证远端仓库可访问，再开始遍历本地 bug
- 不拉取整个 `bensz-bugs` 仓库
- 公开前先生成脱敏副本，确保本地用户名、主机名、工作目录、绝对路径，以及 bug 文本中的敏感个人信息不进入公开仓库
- 直接通过 GitHub Contents API 创建：
  - `{skill_name}/{github_username}/{bug_hash}/bug-context.json`
  - `{skill_name}/{github_username}/{bug_hash}/BUG_REPORT.md`

## 去重规则

- 若远端目标路径已存在，则视为该 bug 已公开
- 已公开 bug 不重复上传，不做远端覆盖
- 本地只把公开状态标记为完成
- `--dry-run` 只输出“预计上传项”，不修改本地文件，也不创建远端文件

## Resolution 阶段

- 只有源码修复、专项回归和版本核对全部通过后，才创建 `RESOLUTION.md`
- canonical 记录使用稳定的 `canonical_root_cause`；重复记录额外使用 `duplicate_of` 指向 canonical bug
- resolution 必须包含修复版本或 commit 与至少一条验证证据
- `resolve_bug.py --dry-run` 不创建文件；相同参数重复执行幂等
- `RESOLUTION.md` 一旦存在，不允许覆盖、截断或静默更新；内容变化应先人工审计原记录
- 原始 `BUG_REPORT.md` 与 `bug-context.json` 永远保持不变
