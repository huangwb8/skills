#!/usr/bin/env python3
"""
Awesome Code - 技能路径获取工具

这是一个硬编码的引导脚本，用于获取技能的真实安装路径。
AI 可以通过这个脚本动态获取技能路径，然后构建正确的调用命令。

输出格式：JSON（便于 AI 解析）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict


def main() -> int:
    """主函数：输出技能路径的 JSON 映射"""
    # 获取脚本所在技能的根目录
    skill_root: Path = Path(__file__).resolve().parent.parent

    # 构建路径映射
    paths: Dict[str, str | Dict[str, str]] = {
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
        executable_scripts: Dict[str, str] = paths["executable_scripts"]  # type: ignore[assignment]
        for script_file in scripts_dir.glob("*.py"):
            script_name = script_file.stem
            executable_scripts[script_name] = str(script_file)

        for script_file in scripts_dir.glob("*.sh"):
            script_name = script_file.stem
            executable_scripts[script_name] = str(script_file)

    # 输出 JSON 格式
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
