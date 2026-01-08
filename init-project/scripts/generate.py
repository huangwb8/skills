#!/usr/bin/env python3
"""
Project Init Generator - 生成脚本

用于生成 AI 项目指令文件：
- CLAUDE.md（Claude Code 项目指令 - 主文件）
- AGENTS.md（OpenAI Codex CLI 项目指令 - 基于 CLAUDE.md 适配）
- README.md（项目介绍与使用方法 - 可选）
- CHANGELOG.md（AI 优化历史记录 - 可选）

支持语言检测、模板变量替换、自定义配置和自动项目分析。
"""

import os
import sys
import platform
import subprocess
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class ProjectAnalyzer:
    """项目结构分析器"""

    # 项目类型识别规则
    PROJECT_PATTERNS = {
        "python": {
            "indicators": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "__init__.py"],
            "default_dirs": ["src/", "tests/", "docs/", "notebooks/", "scripts/"],
            "name": "Python 项目"
        },
        "web": {
            "indicators": ["package.json", "yarn.lock", "pnpm-lock.yaml", "webpack.config.js"],
            "default_dirs": ["src/", "public/", "tests/", "docs/", "config/"],
            "name": "Web 项目"
        },
        "rust": {
            "indicators": ["Cargo.toml", "Cargo.lock"],
            "default_dirs": ["src/", "tests/", "benches/", "examples/"],
            "name": "Rust 项目"
        },
        "go": {
            "indicators": ["go.mod", "go.sum"],
            "default_dirs": ["cmd/", "pkg/", "internal/", "api/"],
            "name": "Go 项目"
        },
        "java": {
            "indicators": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "default_dirs": ["src/main/", "src/test/", "docs/"],
            "name": "Java 项目"
        },
        "data-science": {
            "indicators": ["*.ipynb", "*.R", "requirements.txt", "environment.yml"],
            "default_dirs": ["data/", "notebooks/", "src/", "models/", "reports/"],
            "name": "数据科学项目"
        },
        "docs": {
            "indicators": ["*.md", "docs/", "_docs/", "mkdocs.yml", "docusaurus.config.js"],
            "default_dirs": ["docs/", "assets/", "static/"],
            "name": "文档项目"
        },
    }

    @classmethod
    def analyze_project(cls, root_dir: Path) -> Dict:
        """
        分析项目目录结构，推断项目类型和用途

        Args:
            root_dir: 项目根目录

        Returns:
            包含项目信息的字典
        """
        result = {
            "name": None,
            "type": "通用",
            "description": None,
            "directory_tree": None,
            "detected_dirs": [],
        }

        # 1. 尝试从 README 获取项目名称和描述
        readme_files = ["README.md", "README.txt", "README.rst", "readme.md"]
        for readme_name in readme_files:
            readme_path = root_dir / readme_name
            if readme_path.exists():
                name, desc = cls._parse_readme(readme_path)
                if name:
                    result["name"] = name
                if desc:
                    result["description"] = desc
                break

        # 2. 从目录名推断项目名称
        if not result["name"]:
            result["name"] = cls._sanitize_name(root_dir.name)

        # 3. 检测项目类型
        project_type, type_info = cls._detect_project_type(root_dir)
        result["type"] = project_type
        result["type_info"] = type_info

        # 4. 生成目录树
        result["directory_tree"] = cls._generate_tree(root_dir, max_depth=2)

        return result

    @classmethod
    def _parse_readme(cls, readme_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        解析 README 文件，提取项目名称和描述

        Returns:
            (项目名称, 项目描述)
        """
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取标题（# 标题）
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            name = title_match.group(1).strip() if title_match else None

            # 提取第一段作为描述
            paragraphs = re.split(r'\n\n+', content)
            desc = None
            for para in paragraphs:
                # 跳过标题
                if para.startswith('#'):
                    continue
                # 获取第一个非空段落
                clean_para = para.strip()
                if clean_para and len(clean_para) > 10:
                    desc = clean_para[:200]  # 限制长度
                    break

            return name, desc
        except Exception:
            return None, None

    @classmethod
    def _detect_project_type(cls, root_dir: Path) -> Tuple[str, Dict]:
        """
        检测项目类型

        Returns:
            (类型键名, 类型信息字典)
        """
        all_files = []
        all_dirs = []

        # 收集所有文件和目录
        for item in root_dir.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                all_files.append(item.name)
            elif item.is_dir() and not item.name.startswith('.'):
                all_dirs.append(item.name)

        # 检查每种项目类型
        for type_key, type_info in cls.PROJECT_PATTERNS.items():
            for indicator in type_info["indicators"]:
                # 检查文件（支持通配符）
                if '*' in indicator:
                    pattern = indicator.replace('*', '.*')
                    if any(re.match(pattern, f) for f in all_files):
                        return type_key, type_info
                # 检查精确文件名
                elif indicator in all_files:
                    return type_key, type_info
                # 检查目录
                elif indicator.endswith('/') and indicator[:-1] in all_dirs:
                    return type_key, type_info

        # 默认返回通用类型
        return "generic", {
            "name": "通用项目",
            "default_dirs": ["src/", "docs/", "tests/"]
        }

    @classmethod
    def _generate_tree(cls, root_dir: Path, max_depth: int = 2) -> str:
        """
        生成目录树字符串

        Args:
            root_dir: 根目录
            max_depth: 最大深度

        Returns:
            目录树字符串
        """
        lines = []
        ignore = {'.git', '.DS_Store', '__pycache__', 'node_modules', '.venv', 'venv', '.env', 'dist', 'build'}

        def _add_tree(path: Path, prefix: str, depth: int):
            if depth > max_depth:
                return

            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                return

            # 过滤忽略项
            items = [i for i in items if i.name not in ignore and not i.name.startswith('.')]

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{item.name}")

                if item.is_dir() and depth < max_depth:
                    extension = "    " if is_last else "│   "
                    _add_tree(item, prefix + extension, depth + 1)

        lines.append(root_dir.name + "/")
        _add_tree(root_dir, "", 0)

        return "\n".join(lines)

    @classmethod
    def _sanitize_name(cls, name: str) -> str:
        """清理项目名称"""
        # 移除特殊字符，替换空格和连字符
        clean = re.sub(r'[^\w\s-]', '', name)
        clean = re.sub(r'[-\s]+', '-', clean)
        return clean.strip("-")


class ProjectInitGenerator:
    """项目初始化文档生成器"""

    def __init__(self, config_path: str = None):
        """
        初始化生成器

        Args:
            config_path: 配置文件路径（默认使用项目内 config.yaml）
        """
        # 获取脚本所在目录
        script_dir = Path(__file__).parent.parent
        self.config_path = config_path or script_dir / "config.yaml"
        self.template_dir = script_dir / "templates"

        # 加载配置
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

    def detect_language(self) -> str:
        """
        检测操作系统默认语言

        Returns:
            语言描述（如：简体中文、English）
        """
        system = platform.system().lower()
        lang_code = None

        # 根据系统选择检测命令
        commands = self.config.get('language_detection_commands', {}).get(system, [])
        if not commands:
            commands = ["echo $LANG"]

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    # 提取语言代码
                    output = result.stdout.strip()
                    if "=" in output:
                        lang_code = output.split("=")[1].split(".")[0]
                    else:
                        lang_code = output.split()[0].split(".")[0]
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                continue

        # 映射到对话语言
        mapping = self.config.get('language_mapping', {})
        return mapping.get(lang_code, mapping.get('default', '简体中文'))

    def load_template(self, template_name: str) -> str:
        """
        加载模板文件

        Args:
            template_name: 模板文件名（如 AGENTS.md.template）

        Returns:
            模板内容
        """
        template_path = self.template_dir / template_name
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def replace_placeholders(self, template: str, variables: dict) -> str:
        """
        替换模板中的占位符

        Args:
            template: 模板内容
            variables: 变量字典

        Returns:
            替换后的内容
        """
        result = template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, value or f"[待填写: {key}]")
        return result

    def generate_agents_md(self, variables: dict) -> str:
        """
        生成 AGENTS.md 内容

        Args:
            variables: 模板变量字典

        Returns:
            AGENTS.md 内容
        """
        template = self.load_template("AGENTS.md.template")
        return self.replace_placeholders(template, variables)

    def generate_claude_md(self, variables: dict) -> str:
        """
        生成 CLAUDE.md 内容

        Args:
            variables: 模板变量字典

        Returns:
            CLAUDE.md 内容
        """
        template = self.load_template("CLAUDE.md.template")
        return self.replace_placeholders(template, variables)

    def generate_readme_md(self, variables: dict) -> str:
        """
        生成 README.md 内容

        Args:
            variables: 模板变量字典

        Returns:
            README.md 内容
        """
        template = self.load_template("README.md.template")
        return self.replace_placeholders(template, variables)

    def generate_changelog_md(self, variables: dict) -> str:
        """
        生成 CHANGELOG.md 内容

        Args:
            variables: 模板变量字典

        Returns:
            CHANGELOG.md 内容
        """
        template = self.load_template("CHANGELOG.md.template")
        return self.replace_placeholders(template, variables)

    def append_changelog_entry(self, changelog_path: Path, entry: str) -> bool:
        """
        向 CHANGELOG.md 追加新条目

        Args:
            changelog_path: CHANGELOG.md 文件路径
            entry: 要追加的条目内容

        Returns:
            是否成功
        """
        try:
            with open(changelog_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 在 [Unreleased] 部分后面追加
            if "## [Unreleased]" in content:
                parts = content.split("## [Unreleased]")
                new_content = parts[0] + "## [Unreleased]\n\n" + entry + "\n" + parts[1]
            else:
                # 如果没有 Unreleased 部分，在文件末尾追加
                new_content = content + "\n" + entry

            with open(changelog_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"⚠️  追加 CHANGELOG 条目失败: {e}")
            return False

    def write_file(self, path: Path, content: str, overwrite: bool = False, merge: bool = False) -> bool:
        """
        写入文件

        Args:
            path: 文件路径
            content: 文件内容
            overwrite: 是否覆盖已存在的文件
            merge: 是否智能合并已存在的文件（仅用于 CLAUDE.md 和 AGENTS.md）

        Returns:
            是否成功写入
        """
        if path.exists() and not overwrite:
            if merge:
                # 智能合并模式：保留用户自定义内容，更新标准模板结构
                content = self.merge_existing_file(path, content, path.name)
            else:
                return False

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    def merge_existing_file(self, existing_path: Path, new_content: str, file_type: str) -> str:
        """
        智能合并现有文件和新内容

        策略：
        1. 读取现有文件，识别用户自定义的章节
        2. 保留以下用户自定义章节（如果存在）：
           - ## 项目目标 下的自定义描述
           - ## 核心工作流 下的自定义工作流
           - ## 变更边界 下的自定义规则
           - 用户添加的自定义章节（不在标准模板中的章节）
        3. 更新标准化章节：
           - ## 工程原则（更新为最新标准）
           - ## 默认语言（更新为检测值）
           - ## 目录结构（更新为最新目录树）
           - 平台特定说明（Claude Code / Codex CLI 特定部分）

        Args:
            existing_path: 现有文件路径
            new_content: 新生成的内容
            file_type: 文件类型（"CLAUDE.md" 或 "AGENTS.md"）

        Returns:
            合并后的内容
        """
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except Exception:
            # 如果读取失败，返回新内容
            return new_content

        # 解析现有文件，提取需要保留的自定义内容
        preserved_sections = {}
        custom_sections = []

        # 1. 提取需要保留的自定义章节
        section_patterns = {
            "项目目标": r"## 项目目标\s*\n+(.*?)(?=\n##|\Z)",
            "核心工作流": r"## 核心工作流\s*\n+(.*?)(?=\n##|\Z)",
            "变更边界": r"## 变更边界\s*\n+(.*?)(?=\n##|\Z)",
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, existing_content, re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                # 检查是否是默认模板内容（通过特征判断）
                default_indicators = ["待填写", "请根据实际情况", "[项目类型]", "[待补充"]
                if not any(indicator in section_content for indicator in default_indicators):
                    # 这是用户自定义的内容，保留它
                    preserved_sections[section_name] = section_content

        # 2. 提取用户添加的自定义章节（不在标准模板中的）
        standard_sections = {
            "CLAUDE.md": ["项目目标", "核心工作流", "工程原则", "默认语言", "目录结构",
                         "Claude Code 特定说明", "文件引用规范", "验证要点", "变更边界",
                         "有机更新原则"],
            "AGENTS.md": ["项目目标", "核心工作流", "工程原则", "默认语言", "目录结构",
                        "Codex CLI 特定说明", "文件引用规范", "验证要点", "变更边界",
                        "与 CLAUDE.md 的关系", "有机更新原则"]
        }

        # 找出所有章节标题
        all_sections = re.findall(r"^##\s+(.+)$", existing_content, re.MULTILINE)
        for section in all_sections:
            if section not in standard_sections.get(file_type, []):
                # 这是一个自定义章节，提取它的内容
                pattern = rf"## {re.escape(section)}\s*\n+(.*?)(?=\n##|\Z)"
                match = re.search(pattern, existing_content, re.DOTALL)
                if match:
                    custom_sections.append((section, match.group(1).strip()))

        # 3. 在新内容中应用保留的自定义内容
        merged_content = new_content

        # 替换保留的章节
        for section_name, section_content in preserved_sections.items():
            pattern = rf"(## {re.escape(section_name)}\s*\n+)(.*?)(?=\n##|\Z)"
            merged_content = re.sub(pattern, rf"\1{section_content}\n", merged_content, count=1, flags=re.DOTALL)

        # 添加自定义章节到文件末尾（在有机更新原则之前）
        if custom_sections:
            for section_name, section_content in custom_sections:
                # 检查新内容中是否已经有这个章节
                if f"## {section_name}" not in merged_content:
                    # 在有机更新原则之前插入
                    merged_content = merged_content.replace(
                        "## 有机更新原则",
                        f"## {section_name}\n\n{section_content}\n\n## 有机更新原则"
                    )

        return merged_content

    # 同步配置：核心章节（需要在所有文件中保持一致）
    CORE_SECTIONS = [
        "项目目标",
        "核心工作流",
        "工程原则",
        "默认语言",
        "目录结构",
        "变更边界",
        "有机更新原则",
    ]

    # 平台特定章节（不同步）
    PLATFORM_SPECIFIC_SECTIONS = {
        "CLAUDE.md": [
            "Claude Code 特定说明",
            "文件引用规范",
            "任务管理",
            "代码变更规范",
        ],
        "AGENTS.md": [
            "Codex CLI 特定说明",
            "文件引用规范",
            "代码编辑规范",
            "输出格式",
        ],
    }

    def extract_section(self, content: str, section_name: str) -> Optional[str]:
        """
        从文件内容中提取指定章节

        Args:
            content: 文件内容
            section_name: 章节名称

        Returns:
            章节内容（不包括标题），如果找不到则返回 None
        """
        pattern = rf"## {re.escape(section_name)}\s*\n+(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else None

    def sync_from_source(self, source_path: Path, target_path: Path) -> bool:
        """
        从源文件同步核心章节到目标文件

        策略：
        1. 读取源文件，提取核心章节
        2. 读取目标文件
        3. 保留目标文件的平台特定章节
        4. 用源文件的核心章节替换目标文件的对应章节

        Args:
            source_path: 源文件路径（如 AGENTS.md）
            target_path: 目标文件路径（如 CLAUDE.md）

        Returns:
            是否成功同步
        """
        if not source_path.exists():
            print(f"❌ 源文件不存在: {source_path}")
            return False

        if not target_path.exists():
            print(f"❌ 目标文件不存在: {target_path}")
            return False

        try:
            # 读取源文件和目标文件
            with open(source_path, 'r', encoding='utf-8') as f:
                source_content = f.read()
            with open(target_path, 'r', encoding='utf-8') as f:
                target_content = f.read()

            # 提取源文件的核心章节
            source_sections = {}
            for section_name in self.CORE_SECTIONS:
                section_content = self.extract_section(source_content, section_name)
                if section_content:
                    source_sections[section_name] = section_content

            if not source_sections:
                print(f"⚠️  源文件中未找到任何核心章节")
                return False

            # 同步到目标文件
            updated_content = target_content
            synced_sections = []

            for section_name, section_content in source_sections.items():
                # 检查目标文件中是否有这个章节
                if f"## {section_name}" in updated_content:
                    # 替换现有章节
                    pattern = rf"(## {re.escape(section_name)}\s*\n+)(.*?)(?=\n##|\Z)"
                    updated_content = re.sub(
                        pattern,
                        rf"\1{section_content}\n",
                        updated_content,
                        count=1,
                        flags=re.DOTALL
                    )
                    synced_sections.append(section_name)
                else:
                    # 在"有机更新原则"之前插入新章节
                    updated_content = updated_content.replace(
                        "## 有机更新原则",
                        f"## {section_name}\n\n{section_content}\n\n## 有机更新原则"
                    )
                    synced_sections.append(section_name)

            # 写入目标文件
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            print(f"✅ 已从 {source_path.name} 同步到 {target_path.name}")
            print(f"   同步的章节: {', '.join(synced_sections)}")
            return True

        except Exception as e:
            print(f"❌ 同步失败: {e}")
            return False

    def check_consistency(self, claude_path: Path, agents_path: Path) -> dict:
        """
        检查两个文件的核心章节是否一致

        Args:
            claude_path: CLAUDE.md 文件路径
            agents_path: AGENTS.md 文件路径

        Returns:
            {
                "consistent": bool,
                "diff_sections": ["项目目标", "核心工作流"],
                "details": {章节名: {"claude": "...", "agents": "..."}}
            }
        """
        result = {
            "consistent": True,
            "diff_sections": [],
            "details": {}
        }

        if not claude_path.exists() or not agents_path.exists():
            result["consistent"] = False
            result["error"] = "文件不存在"
            return result

        try:
            with open(claude_path, 'r', encoding='utf-8') as f:
                claude_content = f.read()
            with open(agents_path, 'r', encoding='utf-8') as f:
                agents_content = f.read()

            # 检查每个核心章节
            for section_name in self.CORE_SECTIONS:
                claude_section = self.extract_section(claude_content, section_name)
                agents_section = self.extract_section(agents_content, section_name)

                # 如果两个文件都有这个章节，比较内容
                if claude_section and agents_section:
                    # 标准化比较（移除空白差异）
                    claude_normalized = re.sub(r'\s+', ' ', claude_section.strip())
                    agents_normalized = re.sub(r'\s+', ' ', agents_section.strip())

                    if claude_normalized != agents_normalized:
                        result["consistent"] = False
                        result["diff_sections"].append(section_name)
                        result["details"][section_name] = {
                            "claude": claude_section[:100] + "..." if len(claude_section) > 100 else claude_section,
                            "agents": agents_section[:100] + "..." if len(agents_section) > 100 else agents_section
                        }
                # 如果只有一个文件有这个章节
                elif claude_section or agents_section:
                    result["consistent"] = False
                    result["diff_sections"].append(section_name)
                    result["details"][section_name] = {
                        "claude": claude_section or "(不存在)",
                        "agents": agents_section or "(不存在)"
                    }

        except Exception as e:
            result["consistent"] = False
            result["error"] = str(e)

        return result

    def check_consistency_reminder(self, claude_path: Path, agents_path: Path) -> None:
        """
        检查并提醒用户保持 CLAUDE.md 和 AGENTS.md 的一致性

        Args:
            claude_path: CLAUDE.md 文件路径
            agents_path: AGENTS.md 文件路径
        """
        both_exist = claude_path.exists() and agents_path.exists()

        if both_exist:
            print("\n" + "="*60)
            print("💡 使用 init-project 脚本同步 CLAUDE.md 和 AGENTS.md")
            print("="*60)
            print("\n📋 推荐工作流：")
            print("   1. 先修改 AGENTS.md（项目指令主文件）")
            print("   2. 运行同步命令：")
            print("      python3 init-project/scripts/generate.py --sync-from agents")
            print("   3. （可选）检查一致性：")
            print("      python3 init-project/scripts/generate.py --check-consistency")
            print("\n📌 核心章节将自动同步：")
            print("   - 项目目标、核心工作流、工程原则")
            print("   - 默认语言、目录结构、变更边界、有机更新原则")
            print("\n🔧 平台特定章节保持独立：")
            print("   - Claude Code 特定说明（仅 CLAUDE.md）")
            print("   - Codex CLI 特定说明（仅 AGENTS.md）")
            print("="*60 + "\n")

    def generate_auto(
        self,
        output_dir: Path = None,
        overwrite: bool = False,
        skip_readme: bool = False,
        skip_changelog: bool = False,
        only_readme: bool = False,
        only_changelog: bool = False
    ) -> bool:
        """
        完全自动生成：分析当前目录并生成文档

        Args:
            output_dir: 输出目录（默认当前目录）
            overwrite: 是否覆盖已存在的文件
            skip_readme: 跳过 README.md 生成
            skip_changelog: 跳过 CHANGELOG.md 生成
            only_readme: 仅生成 README.md
            only_changelog: 仅生成 CHANGELOG.md

        Returns:
            是否成功
        """
        output_dir = output_dir or Path.cwd()

        # 分析项目
        analysis = ProjectAnalyzer.analyze_project(output_dir)

        # 检测语言
        language = self.detect_language()

        # 准备变量
        variables = self._prepare_variables(analysis, language, output_dir)

        success = True
        generated_files = []

        # 定义文件路径
        claude_path = output_dir / "CLAUDE.md"
        agents_path = output_dir / "AGENTS.md"
        readme_path = output_dir / "README.md"
        changelog_path = output_dir / "CHANGELOG.md"

        # 如果是仅生成特定文件模式
        if only_readme:
            readme_content = self.generate_readme_md(variables)
            if self.write_file(readme_path, readme_content, overwrite):
                generated_files.append(readme_path)
            else:
                print(f"⚠️  {readme_path} 已存在，使用 --overwrite 覆盖")
                success = False
        elif only_changelog:
            changelog_content = self.generate_changelog_md(variables)
            if self.write_file(changelog_path, changelog_content, overwrite):
                generated_files.append(changelog_path)
            else:
                print(f"⚠️  {changelog_path} 已存在，使用 --overwrite 覆盖")
                success = False
        else:
            # 完整生成模式
            # 1. 生成 CLAUDE.md（主指令文件）- 使用智能合并模式
            claude_content = self.generate_claude_md(variables)
            claude_was_merged = claude_path.exists() and not overwrite
            if self.write_file(claude_path, claude_content, overwrite, merge=True):
                generated_files.append(claude_path)
                if claude_was_merged:
                    print(f"🔄 {claude_path} 已智能更新（保留了自定义内容）")
            else:
                print(f"⚠️  {claude_path} 已存在，使用 --overwrite 覆盖")
                success = False

            # 2. 生成 AGENTS.md（基于 CLAUDE.md 适配）- 使用智能合并模式
            agents_content = self.generate_agents_md(variables)
            agents_was_merged = agents_path.exists() and not overwrite
            if self.write_file(agents_path, agents_content, overwrite, merge=True):
                generated_files.append(agents_path)
                if agents_was_merged:
                    print(f"🔄 {agents_path} 已智能更新（保留了自定义内容）")
            else:
                print(f"⚠️  {agents_path} 已存在，使用 --overwrite 覆盖")
                success = False

            # 显示一致性提醒
            self.check_consistency_reminder(claude_path, agents_path)

            # 3. 生成 README.md（如果不存在或要求覆盖）
            if not skip_readme:
                if not readme_path.exists() or overwrite:
                    readme_content = self.generate_readme_md(variables)
                    if self.write_file(readme_path, readme_content, overwrite):
                        generated_files.append(readme_path)
                else:
                    print(f"ℹ️  {readme_path} 已存在，跳过生成（使用 --overwrite 覆盖）")

            # 4. 生成或更新 CHANGELOG.md
            if not skip_changelog:
                if not changelog_path.exists():
                    # 创建新的 CHANGELOG.md
                    changelog_content = self.generate_changelog_md(variables)
                    if self.write_file(changelog_path, changelog_content, True):
                        generated_files.append(changelog_path)
                elif overwrite:
                    # 如果要求覆盖，追加新条目
                    today = datetime.now().strftime("%Y-%m-%d")
                    entry = f"""## [1.0.0] - {today}

### Added（新增）

- 重新初始化 AI 项目指令文件
- 更新 `CLAUDE.md`（Claude Code 项目指令）
- 更新 `AGENTS.md`（OpenAI Codex CLI 项目指令）
"""
                    if self.append_changelog_entry(changelog_path, entry):
                        print(f"ℹ️  已更新 {changelog_path}")
                else:
                    print(f"ℹ️  {changelog_path} 已存在，跳过更新")

        # 输出结果
        if generated_files:
            print(f"✅ 已生成 AI 项目指令文档:")
            for f in generated_files:
                print(f"   - {f}")
            print(f"\n📊 项目分析结果:")
            print(f"   名称: {analysis['name']}")
            print(f"   类型: {analysis['type_info']['name']}")
            print(f"   语言: {language}")

        return success

    def _prepare_variables(self, analysis: dict, language: str, output_dir: Path) -> dict:
        """准备模板变量"""
        project_type = analysis['type_info']['name']
        today = datetime.now().strftime("%Y-%m-%d")

        # 根据项目类型生成默认工作流描述
        workflow_templates = {
            "Python 项目": "代码开发 → 单元测试 → 文档更新 → 版本发布",
            "Web 项目": "功能开发 → 组件测试 → 构建部署 → 监控反馈",
            "数据科学项目": "数据获取 → 探索分析 → 模型训练 → 验证评估",
            "Rust 项目": "API 设计 → 实现 → 单元测试 → 文档 → 发布",
            "Go 项目": "需求分析 → API 设计 → 实现 → 集成测试 → 部署",
            "Java 项目": "需求分析 → 设计 → 编码 → 测试 → 构建 → 部署",
            "文档项目": "内容规划 → 撰写 → 审校 → 发布",
            "通用项目": "需求分析 → 设计 → 实现 → 验证 → 交付",
        }

        # 根据项目类型生成特性描述
        feature_templates = {
            "Python 项目": "- 基于 Python 开发\n- 遵循 PEP 8 代码规范\n- 支持单元测试和文档生成",
            "Web 项目": "- 现代 Web 应用架构\n- 组件化开发模式\n- 响应式设计支持",
            "数据科学项目": "- 数据处理与分析\n- 机器学习模型训练\n- 可视化报告生成",
            "Rust 项目": "- 高性能系统编程\n- 内存安全保证\n- 零成本抽象",
            "Go 项目": "- 简洁高效的语法\n- 原生并发支持\n- 快速编译部署",
            "Java 项目": "- 企业级应用开发\n- 强类型系统\n- 丰富的生态系统",
            "文档项目": "- 结构化文档管理\n- 多格式输出支持\n- 版本控制集成",
            "通用项目": "- 模块化设计\n- 可扩展架构\n- 完善的文档",
        }

        # 根据项目类型生成环境要求
        env_templates = {
            "Python 项目": "- Python 3.8+\n- pip 或 uv 包管理器",
            "Web 项目": "- Node.js 18+\n- npm 或 pnpm 包管理器",
            "数据科学项目": "- Python 3.8+\n- Jupyter Notebook\n- 常用数据科学库",
            "Rust 项目": "- Rust 1.70+\n- Cargo 包管理器",
            "Go 项目": "- Go 1.21+\n- Go modules 支持",
            "Java 项目": "- JDK 17+\n- Maven 或 Gradle 构建工具",
            "文档项目": "- Markdown 编辑器\n- 静态站点生成器（可选）",
            "通用项目": "- 根据项目需求配置",
        }

        # 根据项目类型生成安装步骤
        install_templates = {
            "Python 项目": "```bash\n# 创建虚拟环境\npython -m venv .venv\nsource .venv/bin/activate  # Windows: .venv\\Scripts\\activate\n\n# 安装依赖\npip install -r requirements.txt\n```",
            "Web 项目": "```bash\n# 安装依赖\nnpm install\n# 或使用 pnpm\npnpm install\n```",
            "数据科学项目": "```bash\n# 创建虚拟环境\npython -m venv .venv\nsource .venv/bin/activate\n\n# 安装依赖\npip install -r requirements.txt\n```",
            "Rust 项目": "```bash\n# 构建项目\ncargo build\n\n# 运行测试\ncargo test\n```",
            "Go 项目": "```bash\n# 下载依赖\ngo mod download\n\n# 构建项目\ngo build ./...\n```",
            "Java 项目": "```bash\n# Maven 构建\nmvn clean install\n\n# 或 Gradle 构建\n./gradlew build\n```",
            "文档项目": "```bash\n# 根据使用的文档工具进行安装\n# 例如 MkDocs:\npip install mkdocs\nmkdocs serve\n```",
            "通用项目": "```bash\n# 根据项目需求进行安装\n```",
        }

        # 根据项目类型生成使用示例
        usage_templates = {
            "Python 项目": "```bash\n# 运行主程序\npython main.py\n\n# 运行测试\npytest\n```",
            "Web 项目": "```bash\n# 开发模式\nnpm run dev\n\n# 构建生产版本\nnpm run build\n```",
            "数据科学项目": "```bash\n# 启动 Jupyter Notebook\njupyter notebook\n\n# 或运行分析脚本\npython analyze.py\n```",
            "Rust 项目": "```bash\n# 运行项目\ncargo run\n\n# 发布构建\ncargo build --release\n```",
            "Go 项目": "```bash\n# 运行项目\ngo run .\n\n# 测试\ngo test ./...\n```",
            "Java 项目": "```bash\n# Maven 运行\nmvn exec:java\n\n# 或直接运行 JAR\njava -jar target/app.jar\n```",
            "文档项目": "```bash\n# 本地预览\nmkdocs serve\n\n# 构建静态站点\nmkdocs build\n```",
            "通用项目": "```bash\n# 根据项目需求运行\n```",
        }

        return {
            "项目名称": analysis['name'],
            "项目描述": analysis['description'] or f"{project_type}，遵循工程最佳实践",
            "工作目录": str(output_dir),
            "默认语言": language,
            "项目用途": analysis['description'] or f"{project_type}开发与维护",
            "核心功能描述": analysis['description'] or f"{project_type}的核心功能开发与维护",
            "工作流描述": workflow_templates.get(project_type, workflow_templates["通用项目"]),
            "目录树": analysis['directory_tree'],
            "项目类型": project_type,
            # README.md 专用变量
            "项目特性": feature_templates.get(project_type, feature_templates["通用项目"]),
            "环境要求": env_templates.get(project_type, env_templates["通用项目"]),
            "安装步骤": install_templates.get(project_type, install_templates["通用项目"]),
            "使用示例": usage_templates.get(project_type, usage_templates["通用项目"]),
            # CHANGELOG.md 专用变量
            "版本号": "1.0.0",
            "日期": today,
            "一句话概括项目的价值主张": analysis['description'] or f"提供 {project_type} 的核心功能",
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="为项目生成 AI 项目指令文件（CLAUDE.md + AGENTS.md + README.md + CHANGELOG.md）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完全自动生成（分析当前目录）
  python3 generate.py --auto

  # 自动生成并覆盖现有文件
  python3 generate.py --auto --overwrite

  # 仅生成 CLAUDE.md 和 AGENTS.md（跳过 README 和 CHANGELOG）
  python3 generate.py --auto --skip-readme --skip-changelog

  # 从 AGENTS.md 同步到 CLAUDE.md（推荐工作流）
  python3 generate.py --sync-from agents

  # 从 CLAUDE.md 同步到 AGENTS.md
  python3 generate.py --sync-from claude

  # 检查 CLAUDE.md 和 AGENTS.md 的一致性
  python3 generate.py --check-consistency

  # 同步后检查一致性
  python3 generate.py --sync-from agents && python3 generate.py --check-consistency

  # 手动指定项目信息
  python3 generate.py --project-name my-project --project-description "数据科学项目"

  # 仅检测语言
  python3 generate.py --detect-language-only
        """
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="完全自动模式：分析当前目录并生成文档"
    )
    parser.add_argument(
        "--project-name",
        help="项目名称（手动模式）"
    )
    parser.add_argument(
        "--project-description",
        help="项目描述（手动模式）"
    )
    parser.add_argument(
        "--workflow",
        help="核心工作流描述（手动模式）"
    )
    parser.add_argument(
        "--language",
        help="默认语言（留空则自动检测）"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="输出目录（默认当前目录）"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的文件"
    )
    parser.add_argument(
        "--detect-language-only",
        action="store_true",
        help="仅检测并显示语言"
    )
    parser.add_argument(
        "--skip-readme",
        action="store_true",
        help="跳过 README.md 生成"
    )
    parser.add_argument(
        "--skip-changelog",
        action="store_true",
        help="跳过 CHANGELOG.md 生成"
    )
    parser.add_argument(
        "--only-readme",
        action="store_true",
        help="仅生成 README.md"
    )
    parser.add_argument(
        "--only-changelog",
        action="store_true",
        help="仅生成 CHANGELOG.md"
    )
    parser.add_argument(
        "--sync-from",
        choices=["agents", "claude"],
        help="从指定文件同步核心章节到另一个文件（agents=从AGENTS.md同步到CLAUDE.md，claude=从CLAUDE.md同步到AGENTS.md）"
    )
    parser.add_argument(
        "--check-consistency",
        action="store_true",
        help="检查 CLAUDE.md 和 AGENTS.md 的核心章节是否一致"
    )

    args = parser.parse_args()

    # 创建生成器
    generator = ProjectInitGenerator()

    # 确定输出目录
    output_dir = Path(args.output_dir).resolve()
    claude_path = output_dir / "CLAUDE.md"
    agents_path = output_dir / "AGENTS.md"

    # 检查一致性
    if args.check_consistency:
        if not claude_path.exists() or not agents_path.exists():
            print("❌ CLAUDE.md 和 AGENTS.md 必须都存在才能检查一致性")
            return 1

        result = generator.check_consistency(claude_path, agents_path)

        if result.get("consistent"):
            print("✅ CLAUDE.md 和 AGENTS.md 的核心章节完全一致")
            return 0
        else:
            print("❌ CLAUDE.md 和 AGENTS.md 的核心章节存在差异：\n")
            for section in result.get("diff_sections", []):
                print(f"   📌 {section}")
                if "details" in result and section in result["details"]:
                    details = result["details"][section]
                    print(f"      CLAUDE.md: {details.get('claude', '(不存在)')[:60]}...")
                    print(f"      AGENTS.md: {details.get('agents', '(不存在)')[:60]}...")
                    print()
            return 1

    # 同步模式
    if args.sync_from:
        if args.sync_from == "agents":
            source = agents_path
            target = claude_path
            source_name = "AGENTS.md"
            target_name = "CLAUDE.md"
        else:  # claude
            source = claude_path
            target = agents_path
            source_name = "CLAUDE.md"
            target_name = "AGENTS.md"

        if not source.exists():
            print(f"❌ 源文件不存在: {source_name}")
            return 1

        if not target.exists():
            print(f"❌ 目标文件不存在: {target_name}")
            print(f"   提示：先运行 --auto 生成两个文件，然后再使用同步功能")
            return 1

        success = generator.sync_from_source(source, target)
        return 0 if success else 1

    # 仅检测语言
    if args.detect_language_only:
        lang = generator.detect_language()
        print(f"检测到的语言: {lang}")
        return 0

    # 完全自动模式
    if args.auto:
        success = generator.generate_auto(
            output_dir=output_dir,
            overwrite=args.overwrite,
            skip_readme=args.skip_readme,
            skip_changelog=args.skip_changelog,
            only_readme=args.only_readme,
            only_changelog=args.only_changelog
        )
        return 0 if success else 1

    # 手动模式（需要指定项目名称和描述）
    if not args.project_name or not args.project_description:
        parser.error("--project-name 和 --project-description 在手动模式下是必需的（或使用 --auto 自动模式）")

    # 检测语言（除非用户指定）
    language = args.language or generator.detect_language()

    # 准备变量
    variables = {
        "项目名称": args.project_name,
        "项目描述": args.project_description,
        "工作目录": os.path.abspath(args.output_dir),
        "默认语言": language,
        "项目用途": args.project_description,
        "核心功能描述": args.project_description,
        "工作流描述": args.workflow or "[待补充工作流描述]",
        "目录树": "[请根据实际项目结构补充]",
        "项目类型": "[项目类型，如：数据分析、Web开发等]",
    }

    # 生成文件
    agents_content = generator.generate_agents_md(variables)
    claude_content = generator.generate_claude_md(variables)

    # 写入文件（使用前面定义的路径）
    # output_dir 和 claude_path/agents_path 已经在前面定义

    success = True

    # 使用智能合并模式
    agents_was_merged = agents_path.exists() and not args.overwrite
    if not generator.write_file(agents_path, agents_content, args.overwrite, merge=True):
        print(f"错误: {agents_path} 已存在，使用 --overwrite 覆盖")
        success = False
    elif agents_was_merged:
        print(f"🔄 {agents_path} 已智能更新（保留了自定义内容）")

    claude_was_merged = claude_path.exists() and not args.overwrite
    if not generator.write_file(claude_path, claude_content, args.overwrite, merge=True):
        print(f"错误: {claude_path} 已存在，使用 --overwrite 覆盖")
        success = False
    elif claude_was_merged:
        print(f"🔄 {claude_path} 已智能更新（保留了自定义内容）")

    if success:
        print(f"✅ 已生成:")
        print(f"   - {agents_path}")
        print(f"   - {claude_path}")
        print(f"\n默认语言: {language}")
        print(f"\n请根据实际情况编辑这些文件，填补 [待补充] 的内容")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
