# BSK 最新生产版运行规范

## 适用范围

本文件指导 `verifier-state-architect` 为其它 Agent Skill 接入 BSK。它规定目标 Skill 如何声明依赖、确认最新生产版、更新托管环境和选择唯一执行入口。BSK 包开发、PyPI 发布和历史环境修复不属于本文件范围。

BSK 处于快速开发阶段，由 Bensz 托管运行时统一升级。新建或修改的目标 Skill 不选择最低版本、不固定精确版本，也不维护 `required_capabilities`；这些字段只作为 Kernel 对历史 Skill 的读取兼容，不是新契约。

## 目标 Skill 的声明

目标 `config.yaml` 只声明依赖 BSK：

```yaml
runtime:
  kernel:
    name: bensz-skill-kernel
```

不要在目标 Skill 中增加 `runtime.kernel.version`、`runtime.kernel.required_capabilities` 或自行定义版本区间。State/Verifier Pack 在集合索引和 `runtime.verifiers` 中声明的 `version` 是契约版本，必须继续维护；它们不是 BSK 包版本。

## 定位运行时管理器

优先从当前宿主已经发现的 `install-bensz-skills` Skill 定位 `scripts/install.py`，并把绝对路径记为 `INSTALLER`。常见安装位置包括：

```text
~/.codex/skills/install-bensz-skills/scripts/install.py
~/.claude/skills/install-bensz-skills/scripts/install.py
```

不得因为当前项目恰好存在 `bsk`、某个虚拟环境能 `import bensz_skill_kernel`，或 PATH 中存在同名命令，就改用该解释器。系统 Python 只有 3.8–3.10 时，先通过同一 Skill 的 `scripts/bootstrap_install.py --ensure-runtime` 建立托管环境；完整安装器、检查器和 Kernel 开发仍要求 Python 3.11+。

## 检查、更新与执行

只读查看当前托管环境是否健康及实际安装版本：

```bash
python3 "$INSTALLER" --runtime-status
```

这个命令不联网，只能证明本地环境健康，不能证明 PyPI 上没有更新版本。人工排查时可以从托管环境查询包索引；该输出只供观察，不作为自动化解析契约：

```bash
"$HOME/.bensz-skills/envs/benszapi/bin/python" \
  -m pip index versions bensz-skill-kernel
```

在开始任何依赖 BSK 的实现、集成检查或真实执行前，使用以下幂等命令联网确认并收敛到最新生产版：

```bash
python3 "$INSTALLER" --force-runtime-update
```

不要用 `--ensure-runtime` 代替上述前置步骤；它遵守更新 TTL，适合日常后台维护，但不能证明本次工作开始时已经检查最新版本。更新成功后验证固定入口：

```bash
"$HOME/.bensz-skills/bin/bsk" --version
"$HOME/.bensz-skills/bin/bsk" diagnostics
```

业务脚本调用 BSK CLI 时统一使用 `~/.bensz-skills/bin/bsk`，不得调用裸 `bsk`。必须使用 Python API 或运行本 Skill 的集成检查器时，使用 `~/.bensz-skills/envs/benszapi` 内的 Python，不使用项目 Python、系统 Python 或其它 Conda 环境。

## 失败与证据

- `--force-runtime-update` 成功且健康检查通过，才可以把本次 BSK 接入或执行标记为已验证；记录实际 BSK 版本和命令结果，不记录机器私密路径。
- 更新失败、包索引不可达或固定入口不健康时，保留安装器的 last-known-good 环境，但本次依赖“当前最新生产版”的实现和验证应标记受阻，不得用旧版本、项目源码或 PATH 中的命令冒充成功。
- 不自动修改系统安装的 Skill 源码，不直接向托管 Conda prefix 手工执行 `pip install`；修复和升级统一交给安装器，以保留锁、状态和健康检查语义。
- BSK 发布造成不兼容变化时，先发布并验证新的生产版，再迁移目标 Skill；目标 Skill 仍不新增版本下限。实际使用版本由 BAC 和任务验证记录追溯。
