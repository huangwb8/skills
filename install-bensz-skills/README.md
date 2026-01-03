# install-bensz-skills

**系统级技能安装器** — 将 `pipelines/skills/` 下的所有技能安装到系统级位置（Codex 和 Claude Code），使其在任意项目中可用。

## 快速开始

```bash
# 默认：同时安装到 Codex 和 Claude Code（仅安装有更新的）
python3 install-bensz-skills/scripts/install.py

# 仅安装到 Claude Code
python3 install-bensz-skills/scripts/install.py --claude

# 仅安装到 Codex
python3 install-bensz-skills/scripts/install.py --codex

# 强制重新安装所有技能（忽略版本检查）
python3 install-bensz-skills/scripts/install.py --force

# 预览模式（不实际安装）
python3 install-bensz-skills/scripts/install.py --dry-run
```

## 技能类型分类

安装器会自动识别并分类技能，**仅安装普通技能**，辅助技能和测试技能将被忽略。

### 1. 普通技能（Normal Skills）

**定义**：供用户在项目中使用的功能技能。

**识别规则**：
- 默认所有包含 `SKILL.md` 的目录为普通技能
- 除非被明确标记为辅助技能或测试技能

**行为**：✅ **会被安装**到 `~/.codex/skills/` 和 `~/.claude/skills/`

**示例**：
- `systematic-literature-review` — 系统文献综述生成
- `knit-rmd-html` — R Markdown 渲染
- `init-project` — 项目初始化
- `check-review-alignment` — 综述引用一致性核查
- `nfsc/` 下的所有 NSFC 写作技能

### 2. 辅助技能（Auxiliary Skills）

**定义**：仅用于开发或维护本技能仓库的工具，不会在生产环境中使用。

**识别规则**（优先级从高到低）：
1. **YAML frontmatter** 中的 `category` 字段为 `auxiliary`/`dev`/`development`
2. **目录名匹配**：
   - `auto-test-skill` — 自动测试技能
   - `install-bensz-skills` — 安装器自身

**行为**：❌ **不会被安装**（在报告中显示为"已忽略"）

**原因**：这些技能仅在开发本仓库时需要，在其他项目中没有用途。

### 3. 测试技能（Test Skills）

**定义**：用于测试其他技能功能的临时或专用技能。

**识别规则**（优先级从高到低）：
1. **YAML frontmatter** 中的 `category` 字段为 `test`/`testing`
2. **路径**：位于 `test/` 或 `tests/` 目录下
3. **目录名模式**：
   - 以 `test` 开头（如 `test-skill`）
   - 包含 `test-`、`-test`、`_test`、`test_`
   - 时间戳格式（如 `20260103_123456`）

**行为**：❌ **不会被安装**（在报告中显示为"已忽略"）

**原因**：这些技能仅在测试和开发时使用，不应分发到生产环境。

## 安装报告示例

```
============================================================
📦 正在安装到 CLAUUDE: /Users/xxx/.claude/skills
============================================================

【安装过程】
------------------------------------------------------------
removed legacy symlink: /Users/xxx/.claude/skills/pipeline-skills
installed: /Users/xxx/.claude/skills/systematic-literature-review
installed: /Users/xxx/.claude/skills/nsfc-abstract-writer

【安装摘要】
------------------------------------------------------------
┌──────────────────────────────────────┬──────────────┬─────────────────────────────────┐
│ Skill 名称                           │ 状态         │ 原因                             │
├──────────────────────────────────────┼──────────────┼─────────────────────────────────┤
│ systematic-literature-review         │ ✅ 已安装    │ 版本已更新 (MD5: a3f5e8d9c2b1)  │
│ knit-rmd-html                        │ ⏭️  跳过     │ 版本未变化                      │
└──────────────────────────────────────┴──────────────┴─────────────────────────────────┘

【辅助技能（已忽略，仅用于开发）】(2 个)
   • auto-test-skill ⏭️ 跳过
     原因: 辅助技能（开发用，不安装到生产环境）
   • install-bensz-skills ⏭️ 跳过
     原因: 辅助技能（开发用，不安装到生产环境）

【测试技能（已忽略，仅用于测试）】(1 个)
   • v20260103_123456 ⏭️ 跳过
     原因: 测试技能（测试用，不安装到生产环境）

------------------------------------------------------------
📊 统计
------------------------------------------------------------
普通技能: 1 个已安装, 1 个跳过
辅助技能: 2 个已忽略（开发用，不安装）
测试技能: 1 个已忽略（测试用，不安装）

============================================================
🎯 总体安装摘要
============================================================
总计数:
  • 已安装/更新: 1 个
  • 跳过: 1 个

CLAUUDE:
  新安装: systematic-literature-review
  未变化: knit-rmd-html

辅助技能: 2 个已忽略（开发用）
测试技能: 1 个已忽略（测试用）
============================================================

📝 安装清单已保存: /Users/xxx/.bensz-skills-install-manifest.20260103-123456.json
```

## 为技能添加类型标记

如果你是技能开发者，可以通过在 SKILL.md 的 YAML frontmatter 中添加 `category` 字段来明确指定技能类型：

```yaml
---
name: my-skill
category: normal  # 可选值: normal, auxiliary, test
description: 技能描述
---
```

**推荐做法**：
- **普通技能**：可以省略 `category` 字段（默认为 normal）
- **辅助技能**：明确添加 `category: auxiliary`
- **测试技能**：明确添加 `category: test`

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 预览模式，不实际写入文件 |
| `--codex` | 仅安装到 Codex |
| `--claude` | 仅安装到 Claude Code |
| `--force` | 强制重新安装所有技能（忽略 MD5 检查） |

## MD5 版本控制机制

- **版本计算**：计算每个技能目录中 `SKILL.md` 的 MD5 哈希值作为版本标识
- **版本存储**：安装后在目标目录生成平台特定的 manifest 文件（`.skill-manifest.{codex,claude}.json`）
- **智能安装**：
  - ✅ **已安装且版本未变**：跳过，不重复安装
  - ✅ **版本已变化**：强制覆盖安装
  - ✅ **新技能**：直接安装

## 安装策略

- 仅安装**普通技能**
- **排除**：辅助技能和测试技能（记录在报告中但不安装）
- **MD5 版本检查**：优先检查平台特定的 manifest 文件，回退到重新计算
- **直接替换**：发现目标路径已存在同名目录且版本变化时，直接删除旧版本并安装新版本（不备份）
  - 理由：Git 已提供版本控制，可随时回退；新版本通常比旧版本更好
- 若存在旧的 `pipeline-skills` 软链接：会移除该软链接（不删除真实目录）

## 常见问题

### Q: 为什么我的辅助技能没有被安装？

A: 辅助技能（如 `auto-test-skill` 和 `install-bensz-skills`）仅用于开发本仓库，在其他项目中没有用途，因此不会被安装。这是设计行为，详见上面的"技能类型分类"部分。

### Q: 如何让我的技能被识别为辅助技能或测试技能？

A: 在技能的 `SKILL.md` 文件的 YAML frontmatter 中添加 `category` 字段：

```yaml
---
category: auxiliary  # 或 test
---
```

### Q: 如果我刚更新了本仓库的技能？

A: 再次运行安装脚本即可完成系统级更新（仅安装有变化的）。

### Q: 需要强制重装？

A: 使用 `--force` 参数。

### Q: Claude Code / Codex 都需要新会话？

A: 是的，安装后建议新建会话验证，因为技能在会话启动时加载。

### Q: 如何回退到旧版本？

A: 使用 Git 回退源代码后，重新运行安装脚本即可（不备份旧版本）。

## 相关文件

- `SKILL.md` — 技能定义（供 Claude Code/Codex 加载）
- `CHANGELOG.md` — 优化日志（记录版本优化历史）
- `scripts/install.py` — 核心安装脚本
- `scripts/i18n.py` — 国际化模块（中/英）
