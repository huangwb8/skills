---
name: install-bensz-skills
category: auxiliary
description: 当需要把本仓库 pipelines/skills 下的所有 skills 安装到系统级（默认同时安装到 Codex: ~/.codex/skills 和 Claude Code: ~/.claude/skills），以便在任意项目/对话中可被发现与调用时使用。使用 MD5 哈希进行版本控制，仅安装有更新的 skills；支持强制覆盖安装和指定单一目标安装。
---

# Install Bensz Skills（系统级安装器）

目的：把当前仓库 `pipelines/skills/` 中的所有 skills（不包括 `install-bensz-skills`）**复制安装**到：

- Codex：`~/.codex/skills/`
- Claude Code：`~/.claude/skills/`

从而让这些 skills 在**任意项目**里都能被发现与触发（不依赖当前 workdir，也不使用软链接）。

## 你要做的事（触发后必须执行）

1) 运行安装脚本：

```bash
# 默认：同时安装到 Codex 和 Claude Code（仅安装有更新的）
python3 install-bensz-skills/scripts/install.py

# 仅安装到 Claude Code
python3 install-bensz-skills/scripts/install.py --claude

# 仅安装到 Codex
python3 install-bensz-skills/scripts/install.py --codex

# 强制重新安装所有 skills（忽略版本检查）
python3 install-bensz-skills/scripts/install.py --force

# 预览模式（不实际安装）
python3 install-bensz-skills/scripts/install.py --dry-run
```

2) 验证（建议在任意其它目录执行）：

```bash
codex exec "列出所有可用的技能"
```

## MD5 版本控制机制

脚本使用 **MD5 哈希值**进行智能版本控制：

- **版本计算**：计算每个 skill 目录中 `SKILL.md` 的 MD5 哈希值作为版本标识
- **版本存储**：安装后在目标目录生成 `.skill-manifest.json` 记录版本信息
- **智能安装**：
  - ✅ **已安装且版本未变**：跳过，不重复安装
  - ✅ **版本已变化**：强制覆盖安装
  - ✅ **新 skill**：直接安装

### 安装报告示例

```
============================================================
📦 正在安装到 CLAUUDE: /Users/xxx/.claude/skills
============================================================

【安装过程】
────────────────────────────────────────────────────────────
installed: /Users/xxx/.claude/skills/nsfc-bib-manager

【安装摘要】
────────────────────────────────────────────────────────────
┌────────────────────────┬──────────────┬─────────────────┐
│ Skill 名称              │ 状态         │ 原因            │
├────────────────────────┼──────────────┼─────────────────┤
│ nsfc-bib-manager        │ ✅ 已安装    │ 版本已更新...  │
│ git-commit              │ ⏭️  跳过     │ 版本未变化     │
└────────────────────────┴──────────────┴─────────────────┘

【辅助技能（已忽略，仅用于开发）】(1 个)
   • install-bensz-skills ⏭️ 跳过

────────────────────────────────────────────────────────────
📊 统计
────────────────────────────────────────────────────────────
普通技能: 1 个已安装, 1 个跳过

============================================================
🎯 总体安装摘要
============================================================

总计数:
  • 已安装/更新: 1 个
  • 跳过: 1 个
```

**注**：完整报告格式规范见 [references/install-report-template.md](references/install-report-template.md)。

## 安装策略（脚本保证）

- 仅安装"包含 `SKILL.md` 的目录"（即每个 skill 的根目录）。
- **排除**：`install-bensz-skills`。
- **MD5 版本检查**：优先检查 `.skill-manifest.json`，回退到重新计算
- **直接替换**：发现到目标路径已存在同名目录且版本变化时，直接删除旧版本并安装新版本（不备份）
  - 理由：Git 已提供版本控制，可随时回退；新版本通常比旧版本更好
- 若存在旧的 `pipeline-skills` 软链接：会移除该软链接（不删除真实目录）。

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 预览模式，不实际写入文件 |
| `--codex` | 仅安装到 Codex |
| `--claude` | 仅安装到 Claude Code |
| `--force` | 强制重新安装所有 skills（忽略 MD5 检查） |

## 常见问题

- **如果你刚更新了本仓库的技能**：再次触发本 skill 运行脚本即可完成系统级更新（仅安装有变化的）。
- **需要强制重装**：使用 `--force` 参数。
- **Claude Code / Codex 都需要新会话**才会重新加载更新后的技能；安装后建议新建会话验证。
- **如何回退到旧版本**：使用 Git 回退源代码后，重新运行安装脚本即可（不备份旧版本）。

