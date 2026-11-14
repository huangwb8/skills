# Skill 身份 demo：旧 Skill 兼容性验证

## 结论

当前普通安装路径保留兼容性：未安装身份运行库、没有身份信息、声明尚未确证或声明残缺，均不会自动启用严格身份安装。验证覆盖普通源码安装、模拟下载后的远程安装和 bootstrap、快速更新的指定 Skill 分支、安装后合成脚本执行。严格身份能力继续作为显式入口；本轮没有迁移生产 Skill、修改系统安装副本或建立生产信任。

混合部署仍有推广阻塞项：快速更新器不指定 `--skill` 时，只要目标根存在受管记录，就会在网络请求前整体拒绝，返回 `managed_install_protected`。显式选择其它未受管 Skill 可以继续。当前应将严格安装试验放在独立临时目标，暂不将正式 Skill 目录转为混合目录；本轮保留该防降级行为，没有修改安装器语义。

## 实际验证

macOS / Python 3.12.7 定向回归 **156 项通过**，包括新增 **28 项兼容性回归**；保留安装器既有 `locale.getdefaultlocale` 弃用警告。

另在实际未安装 `cryptography` 的已有 Python 3.14.6 环境独立运行新增测试，**28 项再次全部通过**。两次执行覆盖同一组新增用例，不叠加计为独立测试数量。

| 场景 | 结果与证据边界 |
|---|---|
| 身份库、cryptography 导入不可用 | 加载安装器前阻断这两类导入，普通入口仍成功 |
| 无 config、无身份、未确证声明、残缺声明 | Codex / Claude 目标的 dry-run、安装、重复安装、源码更新均成功 |
| 默认双平台、无 Skill 筛选、force | 无身份及未确证声明可批量安装，两平台脚本均执行成功 |
| 普通远程安装、bootstrap | 模拟下载与远程配置，真实写入临时目标并执行安装后的合成脚本 |
| 同目录存在其它 Skill 受管记录 | 指定未受管 Skill 的本地、远程、bootstrap 和快速更新仍通过；记录不被改写 |
| 身份能力查询失败后继续普通安装 | 能力查询返回 3，随后普通安装及脚本执行成功 |
| 混合目录无筛选快速更新 | 实测整体拒绝；记录为推广阻塞项，不解释为旧路径全量无影响 |
| 严格安装与防降级 | 既有真实签名 fixture 回归通过，包含所有旧入口的覆盖保护 |
| BSK 公开 API | 既有创建、重放及公开入口 smoke 测试通过 |

同目录兼容性用例使用合成旁路记录来检查 guard 的影响范围，不把这些记录当作验签成功。实际签名验证由既有身份库与严格安装回归承担。

## 复现

使用已有 Python 3.11+ 环境，安装 pytest、PyYAML、cryptography 后运行：

```sh
PYTHONPYCACHEPREFIX="$PWD/.bensz-api/pycache" \
PYTHONPATH="$PWD/packages/bensz-skill-kernel/src" \
python -m pytest \
  tests/test_install_bensz_skills.py \
  tests/test_skill_identity_install.py \
  tests/test_skill_identity_compatibility.py \
  tests/test_bensz_skill_kernel.py \
  packages/bensz-skill-identity/tests \
  --basetemp=tmp/identity-compat-recheck \
  -o cache_dir=.bensz-api/.pytest_cache -q
```

新增兼容性测试可独立执行，不需要 cryptography 或身份包；安装器仍需 Python 3.11+，bootstrap 的既有 Python 3.8 边界未变化。

## 范围与后续条件

本次验证普通安装和可执行文件保留，不代表所有 Skill 的业务任务均完成，也没有重新运行真实模型加载会话。远程内容通过本地模拟提供，未验收线上下载服务。既有宿主发现证据见[宿主能力报告](../skill-identity-host-capability.md)。Windows 未实际执行。

推广前需解决并回归混合目录批量更新，明确受管 Skill 的升级与恢复方式，并取得目标宿主的真实加载与业务执行证据；不能仅凭库测试或签名通过替代这些检查。

任务证据保存在 `.bensz-api/task-20261114-1342-identity-compat/auto-test-code/log/`。正式计划见[兼容性测试计划](../plans/2026-11-14-skill-identity-compatibility-test-plan.md)，新增回归见[测试脚本](../../tests/test_skill_identity_compatibility.py)。
