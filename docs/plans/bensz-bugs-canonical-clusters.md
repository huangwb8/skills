# Bensz Bugs Canonical 根因清单

数据日期：2026-08-09  
数据源：`huangwb8/bensz-bugs` main 分支 99 份公开 `bug-context.json`

## 审计口径

- `记录` 使用 bug hash 的唯一 12 位前缀；完整远端路径固定为 `{远端目录名}/huangwb8/{完整 hash}/bug-context.json`，可由 GitHub tree 唯一还原。
- 每条记录只分配一个 primary canonical ID。复合报告 `e78c98a7bb1a` 主归入 GBK 簇，同时作为 DT helper/公式边界的 secondary evidence，不重复计数。
- `occurrence` 合计为 100：99 个独立 hash 中，`30441ec4ad79` 的 `occurrence_count=2`，其余均为 1。
- “已修复”只表示本轮源码与专项回归已通过；在未追加远端 `RESOLUTION.md` 前，不等于公开记录已闭环。

## Canonical 根因簇

| ID | Skill | 记录（hash 前缀） | 记录数 / occurrence | Canonical 根因 | 当前状态 |
|---|---|---|---:|---|---|
| BRCC-001 | auto-draw-plot | `8c767314d8e7`, `c1ee56d38315`, `efc91786993d`, `f45edae9bddb` | 4 / 4 | image-to-image / async edits 请求体或图片传输不完整 | open |
| BRCC-002 | auto-draw-plot | `46ad41664937`, `869e3e22a4df`, `bf4d845ac897` | 3 / 3 | provider 资格、计费错误与重试分类不一致 | 当前源码 v0.2.12 已修复主要边界，待全簇验收 |
| BRCC-003 | auto-draw-plot | `1c60e14c8421`, `aa78f6bfad7c` | 2 / 2 | 画质参数与 JPEG 交付契约缺失 | open |
| BRCC-004 | auto-draw-plot | `69e48ac1a5ed` | 1 / 1 | async job 无图片时仍退出 0 | open |
| BRCC-005 | auto-draw-plot | `7fb353667f1f` | 1 / 1 | Python 3.9 缺少 `tomllib` fallback | open |
| BRCC-006 | auto-draw-plot | `7fcf01e002c1` | 1 / 1 | evaluation/result 的 passed 口径漂移 | open |
| BRCC-007 | auto-draw-plot | `870f29e95a18` | 1 / 1 | 固定 gpt-image-2 时仍强依赖 Gemini | open |
| BRCC-008 | auto-draw-plot | `c24acdd44ebd` | 1 / 1 | 未复用 Codex 本地 provider 凭据 | open |
| BRCC-009 | awesome-code | `5f83f9f2f326` | 1 / 1 | GBK 控制台无法输出协调器 Unicode JSON 状态符 | open |
| BRCC-010 | bac-contribution-ledger / bensz-auto-contribution | `4f06bb4e9d46`, `5d53aa20b4d4` | 2 / 2 | 初始化后新增 Git remote 使根身份失效 | 缺少授权源码根 |
| BRCC-011 | bensz-channel-vibe-config | `3a6bc33deb52` | 1 / 1 | 发布结果不确定时缺少禁止重试边界 | 当前源码已修复，待专项验收 |
| BRCC-012 | bensz-notes-vibe-config | `9c3fcf0a9ff2` | 1 / 1 | 环境检查泄露凭据前缀 | open |
| BRCC-013 | bensz-rmd-rules | `077549038489` | 1 / 1 | Poppler 无 JPEG 支持时缺少 PNG→JPG fallback | open |
| BRCC-014 | bensz-rmd-rules | `0ce03299a2a6`, `3a96df223126`, `4bac0a0b35a1`, `86e71e42fb77`, `9f3c2a34ab97`, `adb1b322772d`, `b47bd3dc90d2`, `bd7e03eaa48a`, `cb59ea1daaa0`, `d27b79d4bc47`, `da4db102da34`, `e0450d9b46f7`, `e78c98a7bb1a` | 13 / 13 | CLI 状态符在 Windows GBK 输出边界崩溃 | 已修复 v0.21.3，专项回归通过 |
| BRCC-015 | bensz-rmd-rules | `35a15f8cea2e`, `fd46d269598e` | 2 / 2 | 解读覆盖检查漏识别 `render_dt_output` | 已修复 v0.21.3；BRCC-014 的复合报告为 secondary evidence |
| BRCC-016 | benszai-xiaohongshu | `3cab1119c321`, `b81db89aba64`, `ef12935a136d` | 3 / 3 | 固定装饰符/备注改变快照要点语义 | 缺少授权源码根 |
| BRCC-017 | compact-bensz-skills | `e176df4897c3` | 1 / 1 | 中间 JSON 非原子读写与 description 假阳性 | open |
| BRCC-018 | complete-example | `7a1e1ca967d4` | 1 / 1 | 强制模板未定义的 `subsubsubsection` | open |
| BRCC-019 | docx | `38f9271f3b3c`, `a651e0f63628` | 2 / 2 | Python 3.9 不支持 `TemporaryDirectory(ignore_cleanup_errors=...)` | 缺少授权源码根 |
| BRCC-020 | docx | `b108a67e84ab` | 1 / 1 | validator 使用 Python 3.10 语法但无运行时门槛 | 缺少授权源码根 |
| BRCC-021 | init-project | `178f21b3d7b8` | 1 / 1 | BAC 失败后继续写入导致重试非幂等 | open |
| BRCC-022 | init-project | `3e105ee9fae6`, `a6f54f77b46c`, `f7e39ef31040` | 3 / 3 | Windows GBK 状态输出中止初始化 | 已修复 v2.3.4，待追加 resolution |
| BRCC-023 | init-project | `ab0c189a08fb`, `ac13d37e2d5d` | 2 / 2 | Markdown 合并误识别 fenced/三级标题 | open |
| BRCC-024 | install-bensz-skills | `59e987baabdf` | 1 / 1 | 连字符 source id 未映射 argparse dest | open |
| BRCC-025 | install-bensz-skills | `881f33052ffd` | 1 / 1 | Windows Git 解码与文件锁清理失败 | open |
| BRCC-026 | install-bensz-skills | `f6ad8eaf837b` | 1 / 1 | 子目录源仍完整 clone | 当前源码已修复，待专项验收 |
| BRCC-027 | knit-rmd-html | `03ffc551fed9`, `0b3829790f38`, `155538fac85d`, `214f86215a51`, `2663e8f5a473`, `5394652d409b`, `a378992d0726`, `afcac75ccb07`, `b579e0f6826b`, `bdfb38e55ec7`, `c57644ef2b99`, `dab823dbcbac`, `dacad173c2fb`, `e5bda788840a` | 14 / 14 | Windows Pandoc ZIP 布局与 `.exe` 发现错误 | 已修复 v0.1.1，4 项专项回归通过 |
| BRCC-028 | knit-rmd-html | `11e83f2967ef`, `1628a226919c`, `1bf8f1bd29b0`, `3d51d3f46852`, `651155894d24`, `af193390da33`, `fc0e7699bce1` | 7 / 7 | R UTF-8 子进程输出被按 GBK 解码 | 已修复 v0.1.1，专项回归通过 |
| BRCC-029 | nsfc-ref-alignment | `028733f3a73d` | 1 / 1 | Python 3.12 DOI inline regex flag 非法 | open |
| BRCC-030 | nsfc-ref-alignment | `d17979f0c36b` | 1 / 1 | 自定义正文 input 宏未进入引用扫描 | open |
| BRCC-031 | paper-explain-figures | `1d5ac6f17d83`, `ff8d1f0daf73` | 2 / 2 | `.DS_Store` 被误判为越界修改 | open |
| BRCC-032 | paper-explain-figures | `975a24345f2c`, `ae4894cd0e58` | 2 / 2 | 仍写旧工作区且不服从调用方 task root | open |
| BRCC-033 | research-literature-review | `0fd9f8dcf0cc` | 1 / 1 | Pipeline Unicode 阶段符在 GBK 控制台崩溃 | open |
| BRCC-034 | research-literature-review | `30441ec4ad79`, `732354392ab2` | 2 / 3 | JSONL 不完整行/U+2028 被错误切分 | open |
| BRCC-035 | research-literature-review | `33b0fe360d48`, `9d4722927835` | 2 / 2 | 配置路径跨子进程工作目录后失效或越界 | open |
| BRCC-036 | research-literature-review | `397bd118b6ea`, `bafc6ca201f9` | 2 / 2 | `--resume-from` 跳过 checkpoint 加载并覆盖状态 | 已修复 v1.1.1，2 项专项回归通过 |
| BRCC-037 | research-literature-review | `63c3dd150435` | 1 / 1 | Bib 元数据字面 `\\n` 生成非法命令 | open |
| BRCC-038 | research-literature-review（旧名 systematic-literature-review） | `836a8f1b6e36` | 1 / 1 | OpenAlex 接受 br 但运行环境无法解码 | open |
| BRCC-039 | sub2api-reimbursement | `27f8b60dadba`, `961239a83363` | 2 / 2 | detail-only 可见性承诺与上传实现不一致 | 当前源码可能已修复，待专项验收 |
| BRCC-040 | sub2api-reimbursement | `334d13a6de0d` | 1 / 1 | 固定技术备注不符合开票口径 | 当前源码可能已修复，待专项验收 |
| BRCC-041 | sub2api-reimbursement | `fb9e0d03cff2` | 1 / 1 | 未优先锚定既有发票记录绑定订单 | 当前源码可能已修复，待专项验收 |
| BRCC-042 | sub2api-summary | `0c04c9eba38e`, `1c63ef8646a8`, `9c20a075c5fe` | 3 / 3 | 通用 `user` / `recent_orders` 字符串邮箱漏脱敏 | 已修复 v0.3.1，专项回归通过 |
| BRCC-043 | sub2api-summary | `48f00a0ee285` | 1 / 1 | 请求缺少浏览器型 User-Agent，被 Cloudflare 1010 拦截 | open |
| BRCC-044 | validate-md-ref | `3a04502f632f` | 1 / 1 | 站内 anchor 被当作非法外部 URL | 已修复 v0.2.1，专项回归通过 |
| BRCC-045 | validate-md-ref | `9ab025b0a7c7` | 1 / 1 | HEAD-only 将 GET 可访问链接误判无效 | 已修复 v0.2.1，专项回归通过 |
| BRCC-046 | xlsx | `d779e61e0586` | 1 / 1 | Python 3.9 不支持 `TemporaryDirectory(ignore_cleanup_errors=...)` | 缺少授权源码根 |
| **合计** | **20 个当前 skill 身份** | **99 个唯一 hash** | **99 / 100** | **46 个 primary canonical 根因** | 旧名已合并 |

## 源码归属

| 当前 skill 身份 | 正式源码位置 | 授权状态 |
|---|---|---|
| auto-draw-plot | `/Volumes/2T01/Github/sub2api/skills/auto-draw-plot` | 已授权 |
| awesome-code | `/Volumes/2T01/winE/PythonCloud/Agents/pipelines/skills/awesome-code` | 已授权 |
| bensz-channel-vibe-config / bensz-notes-vibe-config | `/Volumes/2T01/winE/Starup/bensz-devtools/skills/` | 已授权 |
| bensz-rmd-rules / compact-bensz-skills / init-project / install-bensz-skills / knit-rmd-html / validate-md-ref | `/Volumes/2T01/winE/PythonCloud/Agents/pipelines/skills/` | 已授权 |
| complete-example / nsfc-ref-alignment / paper-explain-figures / research-literature-review | `/Volumes/2T01/Github/ChineseResearchLaTeX/skills/` | 已授权 |
| sub2api-reimbursement / sub2api-summary | `/Volumes/2T01/winE/PythonCloud/AI/sub2api运营/skills/` | 已授权 |
| bac-contribution-ledger / bensz-auto-contribution | 未在六个授权根发现；按历史名称合并为一个当前身份 | 缺少源码 |
| benszai-xiaohongshu | 未在六个授权根发现 | 缺少源码 |
| docx | 未在六个授权根发现 | 缺少源码 |
| xlsx | 未在六个授权根发现 | 缺少源码 |

## Resolution 门禁

只有表中标记为“已修复”且专项回归、版本核对均通过的簇，才具备追加 `RESOLUTION.md` 的本地条件。公开仓库尚未被本轮修改；远端追加、Issue 评论或关闭仍需用户明确授权。
