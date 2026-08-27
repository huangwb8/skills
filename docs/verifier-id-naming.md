# Verifier ID 命名规范

## 目的

Verifier ID 是验证契约的稳定公开标识，不是脚本文件名、Skill 名称或一次运行的名称。它会出现在 Skill 调用、CLI、验证结果、Gate、事件账本、校准集和重放记录中，因此一旦发布就视为 API 外键。

## Canonical 格式

```text
<owner>.<domain>.<capability>
```

规则如下：

- 全部使用小写 ASCII。
- 每个词使用 kebab-case；允许字母、数字和连字符，必须以字母开头。
- `owner` 可以由一个或多个点分段组成，以支持组织或发行方命名空间。
- `domain` 必须是单个稳定领域词。
- `capability` 是可复核的判断能力，可以由多个连字符词组成。
- 不得把版本、模型、语言、实现方式、Gate 严格程度写入 ID。
- canonical ID 不得以 `v1`、`v2` 等版本后缀结尾。

官方内置 verifier 使用 `bensz` owner，例如：

```text
bensz.artifact.file-existence
bensz.document.markdown-link-integrity
bensz.evidence.citation-truth-fit
bensz.nsfc.justification-contract
```

第三方可使用组织前缀，例如 `org.example.document.link-integrity`。

## 各段含义

`owner` 表示维护者或发行方；`domain` 表示判断对象或知识边界；`capability` 表示验证器能够确认的稳定命题。

输入格式属于 Adapter 的职责。只有当不同格式需要不同判断契约时，才把格式写进 capability，例如 `markdown-link-integrity`。如果 Markdown、HTML 和 LaTeX 都提交同一种链接证据，应使用通用的 `link-integrity`，而不是为每种格式复制 verifier。

Verifier Pack 的公开 ID、Pack 内 Rule/Prompt 的组件 ID、输入 Adapter ID 和单次运行 ID 必须分开。组件只有在需要独立注册、版本化和复用时才提升为顶层 verifier。

## 版本与兼容

版本独立记录在 `version` 字段，并以 `id@version` 形式展示，例如 `bensz.evidence.citation-truth-fit@1.0.0`。

- patch：实现修复，判断含义和协议不变；
- minor：增加向后兼容的能力或可选证据；
- major：改变输入契约、判断含义、结果语义或 Gate 行为。

发布后的 ID 不重命名。重命名应把新 ID 设为 canonical，并在 `VERIFIER.md` 的 `aliases` 中保留旧 ID。旧事件记录不迁移、不覆盖；调用旧 alias 时，结果返回 canonical ID，目录/CLI 清单通过 `aliases` 字段暴露兼容旧名。

## 禁止模式

不要使用 Skill/任务名（`validate-md-ref`）、实现名（`python-checker`）、模型名（`gpt-review`）、版本名（`citation.v1`）、策略名（`strict-citation`）或含义过宽的名字（`quality-check`）作为 verifier ID。

## 契约示例

```yaml
id: bensz.document.markdown-link-integrity
version: 1.0.0
aliases: markdown.link-integrity
domain: document
subject_kinds: markdown
```

Kernel 必须校验 canonical ID，维护 alias 到 canonical ID 的解析，并在目录、Pack、CLI 和事件输出中保持同一身份。
