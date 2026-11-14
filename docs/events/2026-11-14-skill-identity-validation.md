# Skill 身份基础包与安装入口验收

## 交付判断

已实现独立 `bensz-skill-identity` 包、显式签名发行安装、防降级和 bootstrap 委派。保证限定为 `files_verified`。原生宿主加载/工具绑定与独立 router 仓库接入未实施，不能把本次基础能力验收当作端到端防护通过。

需求依据为[实施计划](../plans/2026-11-14-skill-identity-system-plan.md)，当前协议见[身份协议](../skill-identity-protocol.md)，入口见[包指南](../../packages/bensz-skill-identity/README.md)。本轮没有创建生产密钥、修改真实 Skill 的身份字段、系统级安装或远程发布。

## 实现与审查

通过 `awesome-code` 规划、`parallel-vibe` 智能模式执行三轮协作：第一轮两个独立评估和一个总结收敛方案；第二轮安全及安装审查复现三项问题；第三轮独立复验后统一总结。主 Agent 为唯一源码执行主体。多个 Agent 使用同一模型的独立上下文，证据域分别为协议/信任与安装/恢复，不将模型数量等同于完全独立的安全保证。

已关闭的问题：拒绝发行后丢失有效撤销高水位；CLI/API 使用不同状态锁导致并发回退；安装证据逐文件建立导致重试沿用半成品。高水位与业务成功分离，状态事务共用锁；完整 evidence 在 staging 准备后原子发布，并以两份 envelope 的摘要存储。事务记录使用唯一标识区分同发行重装。

主流程另复现并修复构建竞争时误删他人输出：只有本调用成功创建的目录才进入异常清理；竞争目录保留与自有半成品清理均有回归。旧 force dry-run 提前删除 manifest 的行为也已移除。

## 实际验证

环境为 macOS、Python 3.12.7；独立 wheel 安装环境不含 BSK/router。测试密钥仅在内存生成，没有序列化私钥。公共固定测试向量只含 payload、公钥、签名和摘要。

定向命令：

```sh
PYTHONPYCACHEPREFIX="$PWD/.bensz-api/pycache" python -m pytest \
  packages/bensz-skill-identity/tests \
  tests/test_skill_identity_install.py tests/test_install_bensz_skills.py \
  --basetemp=tmp/skill-identity-final -o cache_dir=.bensz-api/.pytest_cache -q
```

最终 125 项通过，保留安装器既有 `locale.getdefaultlocale` 弃用警告。新增源码与测试 Ruff 检查、安装器 strict 结构检查、diff 空白检查通过。

| 场景 | 结论与证据范围 |
|---|---|
| 同名两发布者、改名保持稳定身份 | 通过；实际生成两份不同根授权的发行，可信名称歧义拒绝 |
| 无身份、残缺配置、重复键及 YAML alias | 通过；兼容缺失返回 None，非法身份明确失败 |
| 未受信根、签名篡改、跨签名域复用 | 通过；未知根不自动受信，坏签名拒绝 |
| 配置、正文、脚本、reference、子 Agent、隐藏资源、执行位与文件集合变动 | 通过；实际重读字节，不接受旧结果或 MD5 跳过 |
| 路径、链接、特殊文件与限额 | 通过；本机实际测试路径拒绝、软/硬链接、FIFO 与条目限额；未在 Windows 或大小写敏感卷独立运行 |
| 确定性、公开固定向量、同版本异内容 | 通过；确定性清单/签名输入，已观察冲突拒绝；不保证全球历史 |
| 发布密钥轮换、范围、撤销、过期、回退与同修订异摘要 | 通过；包括失败仍保留认证高水位、无效/过期输入不抬高状态 |
| CLI/API 并发状态更新 | 通过；共享锁下拒绝并发写，真实 barrier 探针确认高修订不会被旧调用覆盖 |
| 精确依赖闭包、缺失、冲突与锁错绑 | 通过；实际签名父子发行、旧内容/政策拒绝；环检测另以合成图算法单元验证，未伪造环形签名发行 |
| 成功安装、候选篡改、实际安装被修改 | 通过；原样资源与外部记录，拒绝候选不破坏有效安装；可重新检查/修复实际内容 |
| 中断与证据半成品 | 通过；六个事务 checkpoint 注入异常与真实进程退出；恢复、重试和历史半成品修复经实际重验 |
| 旧入口与 alias 清理防降级 | 通过；local/remote/bootstrap/updater/cleaner/force/unchanged 路径及别名预检；损坏旁路也拒绝 |
| bootstrap 能力缺失与委派 | 通过；下载前能力失败、argv 数组与退出码；3.8 语法检查通过，未使用真实 Python 3.8 解释器运行 |
| 真实仓库资产 | 通过；`git-commit` 临时副本完整打包、安装和重验；源码没有加入测试身份 |
| wheel 与无关工作目录 | 通过；从临时源码副本构建，隔离 venv 中 API、`bsi verify`、`bsi install` 和篡改拒绝均执行；无 BSK/router |
| Codex 原生发现 | 实际发现无签名描述及 repo/user 同名条目，详见[宿主报告](../skill-identity-host-capability.md) |
| 加载/执行绑定、运行中撤销门禁、router 步骤依赖 | 未实施；不纳入本次通过结论 |

## 证据与限制

任务工作区为 `.bensz-api/task-20261114-1205-skill-identity/`。独立评估、总结及复现位于 `parallel-vibe/` 三个 run；最终 wheel/独立环境结果在 `shared/output/`，日志在 `shared/log/`。宿主只保留合成 fixture 结果，临时 CODEX_HOME 的自动生成日志、数据库和安装标识已清理。

没有运行 BSK 全量测试：本次没有改动 Kernel、State 或 Verifier。没有做全平台、安全审计认证或断电耐久性承诺。安装保证依赖合作入口、完整本地安全状态与可信验证工具；历史客户端和直接文件写入仍可越过安装 guard，下一次受控使用必须重新验证。
