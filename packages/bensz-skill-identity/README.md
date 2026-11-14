<div align="center">

# Bensz Skill Identity（BSI）

**为 Skill 发行验证身份、文件与信任政策。**

[![PyPI](https://img.shields.io/pypi/v/bensz-skill-identity?style=flat-square)](https://pypi.org/project/bensz-skill-identity/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-2563eb?style=flat-square)](https://pypi.org/project/bensz-skill-identity/)
[![License](https://img.shields.io/badge/License-MIT-10b981?style=flat-square)](https://github.com/huangwb8/skills/blob/main/packages/bensz-skill-identity/LICENSE)

[安装与命令](#安装与命令) · [Python API](#python-api) · [协议](https://github.com/huangwb8/skills/blob/main/docs/skill-identity-protocol.md) · [English](https://github.com/huangwb8/skills/blob/main/packages/bensz-skill-identity/README_EN.md)

</div>

Bensz Skill Identity（简称 **BSI**，Python 发行名 `bensz-skill-identity`）是 Bensz Conan 开发的独立 Python 3.11+ Skill 发行身份库，与 Bensz Skill Kernel（BSK）配套，命令分别为 `bsi` 与 `bsk`。BSI 生成 Ed25519 签名发行，检查实际文件，执行显式信任与有限撤销政策，并锁定精确依赖；使用时不依赖 BSK 或 router。

当前保证为 `files_verified`。签名说明发布关系和文件完整性；代码是否安全、宿主实际加载什么、工具能执行什么，需要另外的政策和宿主证据。[协议](https://github.com/huangwb8/skills/blob/main/docs/skill-identity-protocol.md)与[宿主能力报告](https://github.com/huangwb8/skills/blob/main/docs/skill-identity-host-capability.md)说明具体范围。

## 原理与工作流程

![Skill 身份与发行流程：根密钥授权发布密钥；声明身份后构建签名发行，本地结合实际文件、管理员信任配置与安全修订进行验证，仅 allow 结果进入严格安装，trust_required 和 deny 分支停止。](https://chevereto.hwb0307.com/images/2026/11/14/skill-identity-workflow.jpg)

根公钥指纹与稳定键共同确定 Skill 身份，版本标识具体发行。发布者为完整文件清单签名；接收方重读文件，结合显式信任、撤销信息和本地安全修订决定是否允许安装。严格安装会再次校验暂存内容，并保留签名证据供后续重验。

## 安装与命令

```sh
python -m pip install "bensz-skill-identity==1.0.2"
bsi capabilities
python -c "from importlib.metadata import version; print(version('bensz-skill-identity'))"
```

需要 Python 3.11+，安装时会解析 PyYAML 和 cryptography。能力查询不需要密钥或信任文件，返回：

```json
{"assurance": "files_verified", "host_binding": false, "protocol": 1, "schema": "bensz-skill-identity/v1/capabilities", "strict_install": true}
```

包版本查询应输出 `1.0.2`。JSON 的协议版本 `1` 与示例 Skill 的版本独立于 Python 包版本。

已通过可信渠道取得签名发行并准备显式信任策略后，可执行验证或安装；这些命令会维护本地安全修订状态：

```sh
bsi verify --release ./release --trust-store ./trust.json --state ./security-state.json
bsi install --release ./release --trust-store ./trust.json --target ./temporary-skills
```

`trust.json` 由管理员显式维护，包含根公钥、根签名安全元数据和首次接受的最低修订。普通验证不会自动信任发行包里的根。`--state` 保存已接受的修订和已观察发行；应保留它，损坏时会拒绝使用，不能通过删掉状态声称撤销信息仍然新鲜。

库安装不会安装任何 Skill。需要管理 Codex 或 Claude Code 目录时，可用仓库安装器的 `--release` / `--trust-store` 严格入口；见[安装器指南](https://github.com/huangwb8/skills/blob/main/skills/alpha/install-bensz-skills/README.md)。

## Python API

```python
from pathlib import Path
from bensz_skill_identity import TrustPolicy, verify_persisted
from bensz_skill_identity.protocol import load_json

policy = TrustPolicy.from_dict(load_json(Path("trust.json")))
result = verify_persisted(
    Path("release"), policy, state_path=Path("security-state.json")
)
if result.decision == "allow":
    exact_requirement = result.as_requirement()
```

`verify_release(..., state=dict)` 是显式内存状态接口，调用方负责持久化和串行化；生产调用应使用 `verify_persisted` 或安装事务。结果分别包含 `verification`、`decision`、`assurance`、稳定 `reason`，并绑定请求、政策、清单、内容和安全元数据摘要。没有接收旧通过回执以跳过文件检查的 API。

`resolve_lock(requirements, candidates, policy, state=...)` 解析签名依赖闭包；`verify_lock` 重读内容和政策；`resolve_name` 对调用方提供的可信名称映射拒绝歧义。锁只包含完整 ID、精确版本和摘要，不包含绝对路径。政策变化需要重新解析锁。

`snapshot_release` 在独立目录保存完整发行，不清理既有快照；调用方必须在每个受控使用边界重验内容及撤销。目录可被拥有写权限的本机进程修改，因此快照本身不提供宿主绑定。`verify_installation(target, name, policy)` 重新检查实际安装内容与旁路签名，写入安全修订状态。

## 初始化发布者

自 `1.0.1` 起提供 `bsi init` 与 Python API `initialize_publisher`，用于创建或核验本地发布者身份。安装后运行：

```sh
bsi init
bsi init --config-dir /your/private/config
```

默认布局对每位开发者一致，密钥各自独立随机生成；`--config-dir` 只替换根目录，保留以下文件名：

```text
~/.bensz-skills/config/
├── remote.env
├── .bsi-init.lock
└── bsi-keys/
    ├── root.pem
    └── release.pem
```

`remote.env` 保留原有内容，追加以下五个字段。三项公开值可用于身份声明或分发；两项路径指向独立私钥，配置中不嵌入私钥：

| 字段 | 内容 |
|---|---|
| `BSI_PUBLISHER_ID` | 根公钥指纹派生的发布者 ID |
| `BSI_ROOT_PUBLIC_KEY` | 根公钥原始字节的小写十六进制 |
| `BSI_RELEASE_PUBLIC_KEY` | 发布公钥原始字节的小写十六进制 |
| `BSI_ROOT_PRIVATE_KEY_FILE` | `bsi-keys/root.pem` 的绝对路径 |
| `BSI_RELEASE_PRIVATE_KEY_FILE` | `bsi-keys/release.pem` 的绝对路径 |

首次成功输出 `state: created`；重复运行检查两把 Ed25519 PEM、公开值和配置路径，返回 `reused`，不修改身份材料。已有完整密钥对且尚无 BSI 配置时，恢复公开配置并返回 `recovered`。初始化不执行环境文件，也不展开其中的变量或命令。Python 调用为 `initialize_publisher(config_dir: Path | None = None)`，与 CLI 返回相同的公开 JSON 字段，不包含私钥、其它配置或本地路径。

密钥缺失/部分生成返回 `publisher_incomplete`；配置部分存在、重复或语法错误返回 `publisher_config_invalid`；配置与密钥不符返回 `publisher_identity_mismatch`；不安全权限返回 `publisher_permissions_invalid`；检测到外部并发编辑配置返回 `publisher_config_changed`。这些失败不会自动换钥或覆盖冲突配置；损坏 PEM 返回 `invalid_key`，初始化锁竞争返回 `state_locked`。若配置提交失败但两把密钥完整，重新执行可恢复；若生成中断只剩部分密钥，保留已有材料，人工确认恢复方式。

POSIX 下新建目录为 700，密钥、配置及锁文件为 600；既有私钥、密钥目录和已配置环境文件的权限过宽会被拒绝。PEM 不设置口令，发布者负责安全保管及独立备份，勿提交配置或私钥到 Git。初始化只在本地进行，不授权、不建立信任、不生成发行或安装 Skill，也不承诺断电原子性或宿主加载绑定。macOS 权限与并发已实测，Windows 尚未验收。开发者仍可自行准备密钥并使用原有显式参数接口；后续 `authorize`、`build`、`security` 仍需显式指定参数，不自动加载 `remote.env`。

## 创建发行

源码沿用 `config.yaml`：

```yaml
skill_info:
  name: sample
  version: "0.1.0"
  identity:
    publisher_id: ed25519-<根公钥原始字节的SHA256>
    skill_key: sample
```

发布者可通过 `bsi init` 建立本地 Ed25519 根密钥和独立发布密钥，也可自行准备；验证方仍须通过可信渠道接受根公钥。Python 使用内存 `Ed25519PrivateKey` 对象调用 `authorize`、`security_metadata`、`build_release`。CLI 可以读取发布者显式提供的 PEM 文件路径，错误与输出不包含密钥内容：

```sh
bsi authorize --private-key root.pem --release-public-key PUBLIC_HEX \
  --skill-key sample --expires-at UNIX_SECONDS --output authorization.json
bsi build --content ./sample --output ./release --private-key release.pem \
  --authorization authorization.json --history ./publisher-history.json
bsi security --private-key root.pem --revision 1 --issued-at UNIX_SECONDS \
  --expires-at LATER_UNIX_SECONDS --output security.json
```

安全元数据经管理员受信渠道放入信任策略，工具不联网确认是否最新。无 `config.yaml` 的第三方内容可用 `--external-identity` 提供 `{skill_id, version}` JSON；这表示分发者身份，不认证上游作者。已有配置不能被外部身份覆盖。依赖通过 `--dependencies` 显式输入精确要求，不从正文猜测。

发行端不自动过滤文件。应先准备干净内容目录；隐藏资源、README、脚本和子 Agent 均受保护。拒绝链接、特殊文件、路径碰撞及超限。版本不可变只针对本地已经观察的发行，不保证全球历史一致性。

## 严格安装与恢复

安装目录按稳定 `skill_key` 命名；同名异身份不能覆盖。旁路材料在目标根的 `.bensz-skill-identity/`，受签内容不写安装记录。严格安装重新检查候选及 staging，使用同文件系统备份、安装锁和恢复日志。`bsi recover --target DIR` 恢复未结束事务；记录提交为 commit point，之后中断保留新安装，之前中断恢复旧安装。支持进程终止恢复，不承诺突然断电后的文件系统耐久性。

兼容安装器不能更新这些受管目录；必须继续走严格入口。旧历史客户端和直接 Shell 不受此 guard 强制约束。多个目标平台分别提交，不承诺跨平台原子事务。Windows 执行位与锁行为尚未实际验收，当前运行证据来自 macOS。

## 验证

从仓库根目录创建独立开发环境，再安装本地包和测试依赖：

```sh
python -m venv .bensz-api/identity-dev
.bensz-api/identity-dev/bin/python -m pip install ./packages/bensz-skill-identity pytest
PYTHONPYCACHEPREFIX="$PWD/.bensz-api/pycache" \
  .bensz-api/identity-dev/bin/python -m pytest packages/bensz-skill-identity/tests \
  --basetemp=tmp/skill-identity -o cache_dir="$PWD/.bensz-api/.pytest_cache"
```

CLI 成功为 0；未知发布者需要信任为 2；验证或政策拒绝为 3；I/O 或调用错误为 4。解析参数错误遵循 argparse 的退出码 2。JSON 中的 `reason` 是细分原因，不能仅以进程正常退出或验签成功判断政策允许。

历史 API、安装恢复、篡改拒绝和独立 wheel 的验收范围见[验证记录](https://github.com/huangwb8/skills/blob/main/docs/events/2026-11-14-skill-identity-validation.md)；它不代表每个平台或宿主均已通过验收。

## 许可证与支持

采用 [MIT License](https://github.com/huangwb8/skills/blob/main/packages/bensz-skill-identity/LICENSE)。版本变化见 [CHANGELOG](https://github.com/huangwb8/skills/blob/main/packages/bensz-skill-identity/CHANGELOG.md)；问题反馈见[仓库 Issues](https://github.com/huangwb8/skills/issues)。
