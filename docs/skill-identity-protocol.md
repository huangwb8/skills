# Skill 身份发行协议 v1

实现位于 [`bensz-skill-identity`](../packages/bensz-skill-identity/README.md)。Python 包按用户指定版本发布为 1.0.0，本文协议仍为 v1；发布 Python 包不会创建生产 Skill 身份或签名发行，当前保证范围仍为 `files_verified`。

## 身份与内容

根公钥采用 Ed25519 原始 32 字节、小写十六进制。发布者 ID 为 `ed25519-` 加原始公钥的 SHA-256；完整身份为 `skill://<publisher_id>/<skill_key>`。稳定键接受最长 128 字符的小写 ASCII 数字、字母和单个分隔连字符。名称和仓库地址不参与身份；根密钥更换产生新身份，发布密钥轮换保持身份。

配置中的 `skill_info.identity` 只包含 `publisher_id`、`skill_key`，版本仍来自 `skill_info.version`。版本是无前导零的三段非负整数。无身份返回未验证兼容状态；残缺身份、重复 YAML 键、锚点、别名、显式 tag、深度超限均拒绝。无配置的第三方内容只支持显式外部 `{skill_id, version}` 构建输入。

发行目录只有 `content/`、`manifest.json`、`authorization.json`。后两个文件为 `{payload, public_key, signature}` envelope。公钥为 64 位 hex，签名为 128 位 hex；manifest 的发布公钥必须由 authorization 的根签名授权。不能执行发行脚本或安装钩子。

清单包含 `schema`、`skill_id`、`version`、`identity_source`、`files`、`content_digest`、`dependencies`。`identity_source` 为 `config` 或 `external`。文件项按路径 UTF-8 字节排序：目录项为 `{path,type:"directory"}`；常规文件项为 `{path,type:"file",size,sha256,executable}`。执行属性表示任一执行位，mtime、uid、ACL 不参与摘要。`content_digest` 是完整 items 的 canonical JSON SHA-256；`manifest_digest` 是清单 payload 的相同摘要。配置原始字节也在文件列表中。

每个路径必须为 NFC、正斜杠相对路径，拒绝绝对路径、空段、`.`、`..`、反斜线、控制字符、Windows 非法字符/设备名和尾部点/空格。整个目录树检查 casefold 碰撞，拒绝软链接、多硬链接和特殊文件。默认最多 10,000 个条目、单文件 64 MiB、总文件 256 MiB；元数据最多 4 MiB、配置 1 MiB，结构深度最多 32。没有归档解包入口。读取前后检查文件身份、大小和变更时间；这不构成恶意本机并发写入的安全沙箱。

## 签名输入

canonical JSON 为 UTF-8、键排序、无多余空白、`ensure_ascii=False`。只接受字符串键、JSON 整数/布尔/null/字符串/数组/对象，拒绝重复键、浮点和越界整数。对象可用可读 JSON 序列化存储，签验均对解析后 canonical 字节进行。未知机器字段拒绝。

签名输入为 UTF-8 `bensz-skill-identity/v1/<purpose>`、一个 NUL 字节、payload canonical JSON。purpose 只能为 `manifest`、`authorization`、`security`；签名不可跨域复用。Ed25519 来自 `cryptography`，摘要来自 SHA-256。

authorization payload 为 `schema`、`publisher_id`、`release_public_key`、`skill_keys`、`not_before`、`expires_at`。只支持精确稳定键授权，不支持正则/glob。时间为整数 Unix 秒，当前时间处于 `[not_before, expires_at)` 才可用。发布密钥和根密钥允许不同，根私钥不进入发行目录。

## 信任与有限撤销

TrustPolicy JSON：

```json
{
  "schema": "bensz-skill-identity/v1/policy",
  "roots": {"<publisher_id>": "<root_public_hex>"},
  "security": {"<publisher_id>": {"payload": {}, "public_key": "...", "signature": "..."}},
  "minimum_revisions": {"<publisher_id>": 1},
  "offline": false
}
```

示意 envelope 中的 payload 需要真实根签名，空对象不能通过。首次根信任和最低修订由管理员明确建立；工具不从发行包接受自签信任，也不把显式配置等同于确认元数据最新。

security payload 为 `schema`、`publisher_id`、`revision`、`issued_at`、`expires_at`、`revoked_keys`、`revoked_releases`、`disabled`。key 撤销项为发布公钥原始字节的 SHA-256；发行撤销项为 manifest digest；disabled 停用发布者。安全元数据必须由已接受根签名，有效期为 `[issued_at, expires_at)`。严格检查不可省略 security。根失陷需通过外部管理渠道重新建立信任。

安全状态保存最高 revision 和该 envelope 摘要；低修订或同修订不同内容拒绝。已认证且有效的新撤销元数据即使拒绝本发行，也保留其高水位。无效签名或过期元数据不污染状态。`verify_persisted` 以文件锁和原子替换提交；内存 API 的状态由调用者负责。初次记录与删失的旧状态无法自动区分，备份和保管状态属于管理前提。

`offline=true` 只表示有效缓存检查，结果为 `cached_valid`；在线字段也只表示 `locally_supplied_valid`，库没有联网新鲜度服务。过期元数据拒绝。有效期不能证明掌握最新撤销状态。

## 结果与依赖

`result` JSON schema 为 `bensz-skill-identity/v1/result`。`verification` 为 `verified` 或 `failed`；缺少身份的兼容读取由 `read_identity -> None` 表达。`decision` 为 `allow`、`deny`、`trust_required`；`assurance` 为 `none` 或 `files_verified`。合法签名但未知根可以 files verified 且 trust required；撤销也不会改变已验签事实，但政策仍拒绝。

结果含 `skill_id`、`version`、`manifest_digest`、`content_digest`、`request_digest`、`policy_digest`、`security_digest`、`security_revision`、`metadata_status`、`checked_at`、受限相对 `path` 与稳定 `reason`。错误不会回显配置、私钥、绝对路径或原始异常。

常见原因码：`identity_absent`、`invalid_identity`、`invalid_version`、`invalid_yaml`、`duplicate_key`、`unsafe_path`、`path_collision`、`unsupported_file_type`、`limit_exceeded`、`file_mismatch`、`signature_invalid`、`identity_mismatch`、`request_mismatch`、`publisher_untrusted`、`metadata_missing`、`metadata_expired`、`metadata_rollback`、`metadata_equivocation`、`authorization_scope_mismatch`、`authorization_expired`、`key_revoked`、`release_revoked`、`publisher_disabled`、`release_conflict`、`dependency_missing`、`dependency_conflict`、`dependency_ambiguous`、`dependency_cycle`、`lock_mismatch`、`policy_mismatch`、`state_locked`、`security_state_invalid`、`recovery_required`。格式错误统一为 `invalid_metadata` 或 `invalid_json`，详见 API。

依赖固定 `{skill_id,version,manifest_digest,content_digest}`，由构建输入写入受签清单。解析完整闭包，拒绝缺失、环和同身份冲突。相同发行的镜像副本等价；名称映射有多个可信候选时拒绝歧义。锁 schema 为 `.../lock`，包含根要求、完整 releases 和 policy digest，不保存路径。锁内容和旧 result 都不替代后续重验。政策变更需重新解析锁；清理快照和宿主活动引用由消费方负责，库不自动删除快照。

## 安装与兼容

身份能力的试验与推广必须保留普通安装路径：无身份或尚未确证身份的 Skill 继续使用源码、远程和 bootstrap 安装，不因缺少签名或未安装身份库而自动被拒绝。配置中的身份声明不会自动启用严格安装，也不表示发布者已受信任。兼容安装不提供身份认证保证。

当前阶段先在独立临时目标验证严格安装，不将正式 Skill 目录批量转为受管目录。混合目录存在一项限制：快速更新器未指定 `--skill` 时会因任一受管记录拒绝整次更新，显式选择其它未受管 Skill 则可继续；受管 Skill 本身仍须通过严格入口更新。该限制解决并完成回归前，不宣称混合部署对原有批量更新零影响。验证范围见[兼容性记录](events/2026-11-14-skill-identity-compatibility.md)。

完整安装器严格入口为 `--release DIR --trust-store FILE`，与普通源码/远程/运行时操作互斥；`--force` 不放宽检查。严格路径不使用 MD5 或过滤器，受签隐藏资源和文档照常复制。未知根和能力缺失都不能静默进入兼容安装。

旁路布局：目标根的 `.bensz-skill-identity/{records/<skill_key>.json,state.json,releases/<evidence_digest>/,journal.json,install.lock,staging/,backup/}`。内容目录为 `<target>/<skill_key>/`，同名异身份返回冲突。evidence digest 绑定两份完整签名 envelope，完整证据先准备再原子发布；事务唯一标识区分同发行重装；记录原子提交为 commit point。此前失败恢复旧目录和记录，此后恢复完成新安装；备份在提交前保留。目标根与 staging 在同一文件系统。可通过 `recover_install` 或 `bsi recover` 恢复进程终止；不声称跨平台批量或断电原子性。

更新后的完整安装器、bootstrap、快速更新和独立 legacy cleaner 在 MD5 跳过/清理之前识别旁路记录并拒绝 unsigned 覆盖；损坏记录同样受保护。这是合作入口的防降级约定，历史客户端及直接文件写入仍可能修改内容。使用 `verify_installation` 重验实际字节。

Python 3.8 标准库 bootstrap 通过显式 `--identity-python`、`--identity-installer`（或 `BENSZ_IDENTITY_PYTHON`、`BENSZ_IDENTITY_INSTALLER`）探测 `--identity-capabilities`，随后数组形式转发严格参数并保留退出码。未明确配置可信工具时，在下载和目标写入前以 `identity_capability_unavailable` 退出，不自动下载工具自证可信。
