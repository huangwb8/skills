# @install - 快速安装脚本

此目录包含用于快速安装 bensz 技能的脚本。支持通过一行命令从 GitHub 下载并自动安装所有技能。

## 使用方法

### macOS / Linux / WSL

```bash
# 使用 curl
curl -fsSL https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.sh | bash

# 或使用 wget
wget -qO- https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.sh | bash
```

### Windows PowerShell

```powershell
# 方法 1: 使用 irm (推荐)
irm https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.ps1 | iex

# 方法 2: 使用 iwr
. { iwr -useb https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.ps1 } | iex
```

### Windows CMD

```cmd
REM 由于 CMD 不支持直接管道下载执行，需要先下载后运行
bitsadmin /transfer myDownloadJob /download /priority normal https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.bat %TEMP%\install.bat && %TEMP%\install.bat
```

## 默认行为

所有脚本默认执行以下命令（相当于）：

```bash
python3 install-bensz-skills/scripts/install.py --remote --auto
```

这将：
- 从 GitHub 远程仓库下载技能
- 自动安装到 `~/.claude/skills/` 和 `~/.codex/skills/`
- 无需用户确认，自动安装所有推荐的技能

## 系统要求

- **Python 3.7 或更高版本**
- **网络连接**（用于从 GitHub 下载）
- **Git**（用于克隆远程技能仓库）

## 安装位置

| 平台 | Claude Code | OpenAI Codex |
|------|-------------|--------------|
| Unix | `~/.claude/skills/` | `~/.codex/skills/` |
| Windows | `%USERPROFILE%\.claude\skills\` | `%USERPROFILE%\.codex\skills\` |

## 远程源配置

脚本使用以下远程源（定义在 `install-bensz-skills/config.yaml`）：

| 源 ID | 名称 | 描述 | 推荐安装 |
|-------|------|------|---------|
| `general` | 通用技能 | 通用技能，建议所有用户安装 | 是 |
| `research` | 科研技能 | 科研相关技能，建议有科研需要的用户安装 | 否 |

## 故障排除

### Python 未找到

请先安装 Python 3.7+：
- macOS: `brew install python3`
- Ubuntu/Debian: `sudo apt install python3`
- Windows: 从 [python.org](https://www.python.org/downloads/) 下载安装

### PyYAML 依赖缺失

脚本会尝试自动安装 PyYAML。如果失败，请手动安装：

```bash
pip install pyyaml --user
```

### PowerShell 执行策略限制

如果遇到执行策略错误，运行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

然后再执行安装命令。

## 相关链接

- [主仓库](https://github.com/huangwb8/skills)
- [问题反馈](https://github.com/huangwb8/skills/issues)
