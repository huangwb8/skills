<!-- Template-ID: skill-common-constraints; Sync-Policy: copy-and-hash -->

# Skill 公共约束

这是所有新建或修改 Skill 的公共约束权威长版本。`SKILL.md` 必须保留同义的最小摘要，运行时不能假定宿主会自动加载本文件。

## 工作区与产物

- 需要落盘的任务使用唯一的 `./.bensz-api/task-{yyyymmdd-hhmm}-{简短描述}/` 根目录。
- 任务共享材料放在 `shared/`；Skill 专属材料放在对应 Skill 子目录的 `input/`、`output/`、`log/`。
- 正式交付物、源代码和计划文档按项目约定保存，不写入任务工作区；不覆盖用户已有文件。

## BAC 贡献记录

- 项目更新必须检查 BAC 可用性并记录需求来源、AI 生成内容、工具结果、文件改动和验证证据。
- BAC 仅用于过程审计，不替代最终署名或合规判断；记录中不得包含密钥、令牌、Cookie、凭据或隐私。

## 隐私与安全

- 不记录 API Key、访问令牌、密码、Cookie、环境文件、凭据文件、私有 Prompt、用户身份信息、本地用户名、主机名或不必要的大体积原始数据。
- 文件路径必须规范化并限制在授权项目范围内；外部 URL、子进程和网络访问遵循最小权限，防止路径遍历、SSRF 和命令注入。

## 文件边界与版本

- Skill 版本唯一记录在自身 `config.yaml:skill_info.version`；公开 API、协议、目录和配置变更须同步文档与 `CHANGELOG.md`。
- `SKILL.md` 保留触发边界、输入输出、流程和关键安全摘要；详细专题规则下沉到 `docs/`，需要运行时读取的副本放在 Skill 的 `references/`。

## bensz-collect-bugs 协作

- 只记录 Skill 或基础设施模板本身的设计缺陷，不记录用户数据错误、第三方抖动或偶发模型波动。
- 先将脱敏报告写入 `~/.bensz-skills/bugs/`，当前任务不中断；只有用户明确要求时才通过本机 `gh api` 公开上报。
- 严禁直接修改用户本地已安装 Skill 的源代码来“顺手修 bug”。

## 副本同步

模板源文件位于 `docs/templates/`。Skill `references/` 中的副本必须在文件头写明 `Template-ID` 与 `Source-Hash: sha256:<hex>`；更新模板后运行结构检查器即可定位需要同步的副本。
