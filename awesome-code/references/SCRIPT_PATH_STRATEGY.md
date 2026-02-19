# Awesome Code 脚本调用策略

## 核心原则

**硬编码引导步骤 → 动态获取路径 → 使用绝对路径调用**

通过 `get_path.py` 硬编码引导脚本，让 AI 动态获取技能真实安装路径，确保在任何情况下都能正常工作。

## AI 调用流程（三步骤）

### 步骤 1：获取技能路径（硬编码）

```bash
python3 ~/.claude/skills/awesome-code/scripts/get_path.py
```

**输出示例**：
```json
{
  "skill_root": "/Users/username/.claude/skills/awesome-code",
  "skill_name": "awesome-code",
  "scripts_dir": "/Users/username/.claude/skills/awesome-code/scripts",
  "config_file": "/Users/username/.claude/skills/awesome-code/config.yaml",
  "executable_scripts": {
    "agent_coordinator": "/Users/username/.claude/skills/awesome-code/scripts/agent_coordinator.py",
    "create_test_session": "/Users/username/.claude/skills/awesome-code/scripts/create_test_session.py",
    "test_runner": "/Users/username/.claude/skills/awesome-code/scripts/test_runner.py",
    "code_analyzer": "/Users/username/.claude/skills/awesome-code/scripts/code_analyzer.py",
    "git_helper": "/Users/username/.claude/skills/awesome-code/scripts/git_helper.sh"
  }
}
```

### 步骤 2：解析 JSON，提取脚本路径

AI 从返回的 JSON 中提取需要的脚本路径：

```python
import json

# 假设已运行 get_path.py 并保存输出
paths = json.loads(output)
coordinator_path = paths["executable_scripts"]["agent_coordinator"]
# /Users/username/.claude/skills/awesome-code/scripts/agent_coordinator.py
```

### 步骤 3：使用绝对路径调用

```bash
python3 /Users/username/.claude/skills/awesome-code/scripts/agent_coordinator.py "fix bug"
```

## 为什么需要硬编码引导步骤？

### 问题背景

1. **技能安装位置不固定**
   - 用户级：`~/.claude/skills/awesome-code/`
   - 项目级：`.claude/skills/awesome-code/`
   - 自定义路径

2. **当前工作目录可变**
   - 用户可能在任意项目目录中使用
   - 相对路径无法正确定位

3. **AI 无法预知安装位置**
   - 硬编码路径会因环境而失效
   - 环境变量依赖用户配置

### 解决方案

让脚本**自己告诉 AI 它在哪里**：

```python
# get_path.py 核心逻辑
from pathlib import Path

skill_root = Path(__file__).resolve().parent.parent
# 无论脚本安装在哪里，都能正确获取路径
```

## 脚本分类与调用方式

### 1. 路径引导脚本（硬编码）

| 脚本 | 功能 | 调用方式 |
|------|------|----------|
| **get_path.py** | 获取技能真实安装路径 | `python3 ~/.claude/skills/awesome-code/scripts/get_path.py` |

**特点**：
- 硬编码调用（AI 必须先调用这个脚本）
- 输出 JSON 格式，便于 AI 解析
- 包含所有可执行脚本的绝对路径

### 2. 技能内部脚本（需要访问技能配置）

这些脚本需要访问 `awesome-code` 技能自身的配置文件。

| 脚本 | 实现方式 | 调用示例 |
|------|----------|----------|
| `agent_coordinator.py` | `Path(__file__).resolve().parent.parent` | `python3 <absolute_path> "task"` |

**实现原理**：
```python
# 脚本会自动找到技能根目录
self.skill_root = Path(__file__).resolve().parent.parent
# /Users/username/.claude/skills/awesome-code/
```

### 3. 项目操作脚本（作用于当前项目）

这些脚本在**当前项目目录**中运行，操作项目文件。

| 脚本 | 实现方式 | 调用示例 |
|------|----------|----------|
| `test_runner.py` | 在项目目录运行 | `python3 <absolute_path> --watch` |
| `code_analyzer.py` | 在项目目录运行 | `python3 <absolute_path> --path src/` |
| `git_helper.sh` | 在项目目录运行 | `bash <absolute_path> commit` |

**使用场景**：在任意项目目录中调用，脚本会自动检测当前项目环境。

### 4. 跨技能脚本（作用于指定技能）

这些脚本需要指定**目标技能**的路径。

| 脚本 | 实现方式 | 调用示例 |
|------|----------|----------|
| `create_test_session.py` | 通过 `--skill-root` 参数 | `python3 <absolute_path> --skill-root . --kind a` |

**使用场景**：用于测试和优化其他技能，`--skill-root` 指向目标技能目录。

## 用户手动调用

### 推荐配置：Shell 别名

在 `~/.zshrc` 或 `~/.bashrc` 中添加：

```bash
# Awesome Code 脚本别名
alias ac-coordinator='python3 ~/.claude/skills/awesome-code/scripts/agent_coordinator.py'
alias ac-test='python3 ~/.claude/skills/awesome-code/scripts/test_runner.py'
alias ac-analyze='python3 ~/.claude/skills/awesome-code/scripts/code_analyzer.py'
alias ac-git='bash ~/.claude/skills/awesome-code/scripts/git_helper.sh'
alias ac-session='python3 ~/.claude/skills/awesome-code/scripts/create_test_session.py'
```

使用示例：
```bash
ac-coordinator "fix login bug"
ac-test --watch --coverage
ac-analyze --path src/ --report analysis.md
ac-git commit
ac-session --skill-root . --kind a --id v202601171200
```

### 直接调用

```bash
# 用户级安装
python3 ~/.claude/skills/awesome-code/scripts/agent_coordinator.py "fix bug"

# 项目级安装
python3 .claude/skills/awesome-code/scripts/agent_coordinator.py "fix bug"
```

## 安装位置支持

脚本支持两种安装位置：

| 安装位置 | get_path.py 路径 |
|---------|------------------|
| **用户级** | `~/.claude/skills/awesome-code/scripts/get_path.py` |
| **项目级** | `.claude/skills/awesome-code/scripts/get_path.py` |

AI 应优先尝试用户级路径，失败后尝试项目级路径。

## 技术实现细节

### get_path.py 源码

```python
#!/usr/bin/env python3
"""Awesome Code - 技能路径获取工具"""

import json
from pathlib import Path

def main():
    # 获取脚本所在技能的根目录
    skill_root = Path(__file__).resolve().parent.parent

    # 构建路径映射
    paths = {
        "skill_root": str(skill_root),
        "skill_name": skill_root.name,
        "scripts_dir": str(skill_root / "scripts"),
        "config_file": str(skill_root / "config.yaml"),
        "skill_file": str(skill_root / "SKILL.md"),
        "references_dir": str(skill_root / "references"),
        "templates_dir": str(skill_root / "templates"),
    }

    # 获取所有可执行脚本的路径
    scripts_dir = skill_root / "scripts"
    if scripts_dir.exists():
        paths["executable_scripts"] = {}
        for script_file in scripts_dir.glob("*.py"):
            paths["executable_scripts"][script_file.stem] = str(script_file)
        for script_file in scripts_dir.glob("*.sh"):
            paths["executable_scripts"][script_file.stem] = str(script_file)

    # 输出 JSON 格式
    print(json.dumps(paths, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
```

### Python 脚本路径自发现

```python
# _config.py 和 agent_coordinator.py 使用
from pathlib import Path

# 获取脚本所在技能的根目录
skill_root = Path(__file__).resolve().parent.parent
# __file__ = /path/to/skills/awesome-code/scripts/agent_coordinator.py
# parent = /path/to/skills/awesome-code/scripts/
# parent.parent = /path/to/skills/awesome-code/ ✅

# 读取配置
config_path = skill_root / "config.yaml"
```

### Shell 脚本路径自发现

```bash
# git_helper.sh 示例
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"

# 读取配置
CONFIG_FILE="$SKILL_ROOT/config.yaml"
```

## 常见问题

### Q: 为什么不能直接输入 `agent_coordinator.py`？

A: 脚本需要完整路径才能被找到。AI 应先调用 `get_path.py` 获取路径，用户可使用 shell 别名。

### Q: 技能安装在不同位置怎么办？

A: `get_path.py` 会自动发现，无需手动配置。

### Q: 如何在 CI/CD 中使用？

A: 直接使用 `get_path.py` 或设置环境变量：

```bash
# 方式1：使用 get_path.py
export SKILL_PATHS=$(python3 ~/.claude/skills/awesome-code/scripts/get_path.py)

# 方式2：设置环境变量
export AWESOME_CODE_ROOT="${GITHUB_WORKSPACE}/.claude/skills/awesome-code"
python3 "$AWESOME_CODE_ROOT/scripts/agent_coordinator.py" "task"
```

### Q: AI 如何知道要调用 `get_path.py`？

A: 这是**硬编码引导步骤**，在 SKILL.md 开头明确说明，AI 必须首先调用它。

## 版本历史

- **2026-01-17**：新增 `get_path.py` 硬编码引导脚本，实现动态路径发现
- **2026-01-17**：明确 AI 调用流程（三步骤），区分 AI 和用户调用方式
