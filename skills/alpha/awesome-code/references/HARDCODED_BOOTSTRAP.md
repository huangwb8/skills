# 硬编码引导步骤 - 实现说明

## 问题回顾

你遇到的错误：
```bash
python3: can't open file '/Volumes/2T01/winE/Starup/LLMRide/scripts/agent_coordinator.py'
```

**根本原因**：
- AI 生成的命令使用了相对路径 `python3 scripts/agent_coordinator.py`
- 相对路径会在**当前工作目录**查找脚本
- 但脚本实际安装在技能目录中，不在当前项目目录

## 解决方案：硬编码引导步骤

### 核心思想

**让脚本自己告诉 AI 它在哪里**

而不是让 AI 猜测或硬编码路径。

### 实现方式

#### 1. 新增 `get_path.py` 脚本

**位置**：`awesome-code/scripts/get_path.py`

**功能**：
- 自动获取技能的真实安装路径
- 输出 JSON 格式，包含所有脚本的绝对路径
- 无论从哪里调用都能正确获取路径

**源码**：
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
        "executable_scripts": {}
    }

    # 获取所有可执行脚本的路径
    for script_file in (skill_root / "scripts").glob("*.py"):
        paths["executable_scripts"][script_file.stem] = str(script_file)

    # 输出 JSON 格式
    print(json.dumps(paths, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
```

#### 2. AI 调用流程（三步骤）

```bash
# 步骤 1：获取技能路径（硬编码）
python3 ~/.claude/skills/awesome-code/scripts/get_path.py

# 步骤 2：解析 JSON，提取脚本路径
# 从返回的 JSON 中提取需要的脚本路径

# 步骤 3：使用绝对路径调用
python3 <absolute_path_from_json> "task"
```

#### 3. SKILL.md 文档更新

在 SKILL.md 开头添加"步骤 0：获取技能路径"章节，明确说明：
- 这是硬编码引导步骤
- AI 必须首先调用它
- 输出格式和使用方式

## 优势

### 1. 环境无关性

无论技能安装在哪里，都能正确工作：

```bash
# 用户级安装
~/.claude/skills/awesome-code/

# 项目级安装
.claude/skills/awesome-code/

# 自定义路径
/custom/path/skills/awesome-code/
```

### 2. 目录无关性

无论当前工作目录在哪里，都能正确获取路径：

```bash
# 在项目目录中
cd /my/project
python3 ~/.claude/skills/awesome-code/scripts/get_path.py

# 在临时目录中
cd /tmp
python3 ~/.claude/skills/awesome-code/scripts/get_path.py

# 结果都是正确的绝对路径
```

### 3. 自动发现性

脚本通过 `Path(__file__).resolve().parent.parent` 自动发现路径：
- `__file__`：脚本自身的绝对路径
- `parent`：脚本所在目录（`scripts/`）
- `parent.parent`：技能根目录

### 4. AI 友好性

- 输出 JSON 格式，便于 AI 解析
- 包含所有可执行脚本的完整路径
- 无需 AI 猜测或计算路径

## 验证测试

从不同目录调用，验证路径正确性：

```bash
# 从技能目录
cd /path/to/skills/awesome-code
python3 scripts/get_path.py
# ✅ 返回正确的绝对路径

# 从项目目录
cd /my/project
python3 ~/.claude/skills/awesome-code/scripts/get_path.py
# ✅ 返回正确的绝对路径

# 从任意目录
cd /tmp
python3 ~/.claude/skills/awesome-code/scripts/get_path.py
# ✅ 返回正确的绝对路径
```

## 与其他方案的对比

| 方案 | 优势 | 劣势 |
|------|------|------|
| **相对路径** | 简洁 | ❌ 依赖当前目录，不可靠 |
| **硬编码绝对路径** | 明确 | ❌ 无法预知安装位置 |
| **环境变量** | 灵活 | ❌ 依赖用户配置 |
| **硬编码引导步骤** | 可靠、自动、环境无关 | 需要先调用引导脚本 |

## 扩展性

这个方案可以扩展到其他需要动态获取路径的场景：

1. **跨技能调用**：一个技能调用另一个技能的脚本
2. **CI/CD 集成**：在自动化环境中动态获取路径
3. **插件系统**：插件动态发现主程序路径

## 总结

通过引入 `get_path.py` 硬编码引导步骤，我们实现了：

✅ **环境无关**：无论技能安装在哪里都能工作
✅ **目录无关**：无论当前目录在哪里都能正确获取路径
✅ **自动发现**：脚本通过 `__file__` 自动发现自身位置
✅ **AI 友好**：JSON 输出，便于 AI 解析和使用
✅ **用户友好**：文档清晰，步骤明确

这是**最稳健、最通用的解决方案**。
