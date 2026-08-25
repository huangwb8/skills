# bensz-collect-bugs

这个 skill 用来处理你开发的 Bensz 系列 skills 在真实用户环境里暴露出的“设计缺陷类 bug”。它先把 bug 规范化记到本地，再在你明确要求时用本机 `gh` 轻量公开上报到 `huangwb8/bensz-bugs`。

## 用法

### 最推荐用法：先本地记录 bug

```text
请使用 bensz-collect-bugs skill 记录这个 Bensz skill 的设计缺陷 bug。
输入：
- skill 名称：`<skill_name>`
- 预期行为：`<expected>`
- 实际行为：`<actual>`
- 复现步骤：`<steps>`
- 关键证据：`<error/output>`
输出：把 bug 规范记录到 `~/.bensz-skills/bugs/`
```

### 最推荐用法：公开上报已收集的 bug

```text
我想 report bensz skills bugs，请使用 bensz-collect-bugs skill。
输入：扫描我本地 `~/.bensz-skills/bugs/` 里的 bug
输出：把尚未公开的 bug 用本机 `gh` 上传到 `huangwb8/bensz-bugs`
```

## 它会帮你做什么

- 统一 bug 的本地存储位置：`~/.bensz-skills/bugs/`
- 为每个 bug 自动生成结构化 `bug-context.json`
- 为每个 bug 自动生成统一格式的 `BUG_REPORT.md`
- 在修复通过验证后追加不可覆盖的 `RESOLUTION.md`，并把重复记录关联到同一 canonical 根因
- 自动采集当前 OS、shell、常见软件版本
- 在本地写入前自动清洗自由文本里的密钥、密码、身份信息、电话、邮箱、银行卡号和私密路径
- 按 `config.yaml:hashing.stable_fields` 计算稳定 `bug_hash`，避免重复上传同一问题
- 在公开上报时直接调用 `gh api` 上传，不需要把 `bensz-bugs` 仓库整仓拉下来
- 默认不再采集本地用户名、主机名、当前工作目录等高风险个人信息
- 公开上报前自动脱敏，避免把本地用户名、主机名、工作目录、绝对路径上传到公开仓库

## 什么时候该用它

- 某个 Bensz skill 在用户机器上因为 skill 设计缺陷而出问题
- 你想保留 bug 证据，但暂时不打算公开
- 你已经积累了一批本地 bug，想统一公开 report

## 什么时候不要用它

- 问题只是第三方服务短暂故障
- 问题是用户输入错了
- 你只是想立即修复自己本地开发仓库里的源码 bug
- 你要修改用户已安装的 skill 源码

## 本地输出结构

每个 bug 使用以下层级：

```text
~/.bensz-skills/bugs/{skill_name}/{reporter}/{bug_hash}/
├── bug-context.json
├── BUG_REPORT.md
└── RESOLUTION.md  # 仅在完成修复闭环后追加
```

说明：

- `reporter` 优先使用当前 GitHub 用户名
- 如果采集阶段尚未配置 `gh`，本地会暂存到 `pending-github-identity/`
- 如果没有 GitHub 用户名，本地报告展示名会退回匿名占位，而不是本地用户名
- `storage.path_pattern` 控制本地目录层级，默认仍是 `{skill_name}/{reporter}/{bug_hash}`
- 真正公开上报时，远端目录会改用当前 `gh` 登录用户名

## 手动命令

### 本地记录 bug

```bash
python3 bensz-collect-bugs/scripts/collect_bug.py \
  --skill-name "example-skill" \
  --skill-author "Bensz Conan" \
  --bug-summary "技能把相对路径误判为绝对路径" \
  --expected-behavior "应正确接受相对路径输入" \
  --actual-behavior "脚本直接拒绝并退出" \
  --reproduction-step "在项目根目录执行 skill" \
  --reproduction-step "输入相对路径 docs/a.md" \
  --evidence "ValueError: absolute path required" \
  --agent-runtime "codex-cli"
```

### 公开上报全部未公开 bug

```bash
python3 bensz-collect-bugs/scripts/report_bugs.py
```

说明：

- 若使用 GitHub Enterprise，可在 `config.yaml:github.api_host` 中配置主机名，脚本会据此调用 `gh api --hostname ...`

### 先预演，不真正上传

```bash
python3 bensz-collect-bugs/scripts/report_bugs.py --dry-run
```

### 只上报某个 skill 的 bug

```bash
python3 bensz-collect-bugs/scripts/report_bugs.py --skill-name "example-skill"
```

修复和专项回归都通过后，先用 dry-run 预演 resolution：

```bash
python3 bensz-collect-bugs/scripts/resolve_bug.py \
  --bug-dir ~/.bensz-skills/bugs/example-skill/octocat/<bug_hash> \
  --status fixed \
  --canonical-root-cause BRCC-2026-001 \
  --fixed-version-or-commit v1.2.3 \
  --verification "pytest tests/test_regression.py: 4 passed" \
  --dry-run
```

确认后移除 `--dry-run`。重复记录使用 `--status duplicate --duplicate-of <canonical_bug_hash>`；相同参数重复执行不会改写文件，内容冲突时脚本会拒绝覆盖。

## 公开上报前提

- 你的机器已安装 `gh`
- `gh auth status` 能通过
- 如果还没登录，先运行 `gh auth login`

## 输出

- 本地记录阶段：生成 `bug-context.json` 与 `BUG_REPORT.md`
- 修复闭环阶段：追加 `RESOLUTION.md`；缺少修复版本或验证证据时拒绝标记 resolved
- 公开上报阶段：把新 bug 上传到 `https://github.com/huangwb8/bensz-bugs`
- 已公开的本地 bug 会在 `bug-context.json` 里被标记为 `public_reported=true`

## 隐私保护

- 本地和公开两个阶段都遵循“最小必要信息”原则，不会为了排障方便而保留无关的个人标识
- 如果你提供的 bug 文本里含有密钥、密码、电话、邮箱、身份号码、银行卡号或私密路径，脚本会先替换成脱敏占位符再落盘
- `--reporter-display-name` 已废弃；为保护隐私，该参数当前不会写入记录
- 若旧版本地记录中残留了这类信息，重新执行收集或公开上报时也会按新版规则自动清洗

## FAQ

### Q：它会直接修用户机器里的 skill 吗？

A：不会。这个 skill 的硬规则就是“记录 bug，不碰用户本地已安装 skill 的源码”。

### Q：为什么公开上报时不用 `git clone`？

A：因为 bug 仓库可能越来越大；直接用 `gh api` 按路径创建文件更轻量，也更适合只上传新增 bug。

### Q：如果同一个 bug 又出现一次怎么办？

A：本地再次记录时会命中同一 `bug_hash`，脚本只更新次数和最近出现时间，不会重复造目录。

### Q：公开仓库会不会泄露我本地机器的路径和用户名？

A：不会。公开上报会先生成脱敏副本，只保留公开协作需要的字段；而且新版默认连本地记录也不再保留本地用户名、主机名、工作目录这些高风险字段。
