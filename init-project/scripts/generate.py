#!/usr/bin/env python3
"""
Project Init Generator - 生成脚本

用于生成 AGENTS.md 和 CLAUDE.md 文件。
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

    def write_file(self, path: Path, content: str, overwrite: bool = False) -> bool:
        """
        写入文件

        Args:
            path: 文件路径
            content: 文件内容
            overwrite: 是否覆盖已存在的文件

        Returns:
            是否成功写入
        """
        if path.exists() and not overwrite:
            return False

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    def generate_auto(self, output_dir: Path = None, overwrite: bool = False) -> bool:
        """
        完全自动生成：分析当前目录并生成文档

        Args:
            output_dir: 输出目录（默认当前目录）
            overwrite: 是否覆盖已存在的文件

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

        # 生成文件
        agents_content = self.generate_agents_md(variables)
        claude_content = self.generate_claude_md(variables)

        # 写入文件
        agents_path = output_dir / "AGENTS.md"
        claude_path = output_dir / "CLAUDE.md"

        success = True

        if not self.write_file(agents_path, agents_content, overwrite):
            print(f"⚠️  {agents_path} 已存在，使用 --overwrite 覆盖")
            success = False

        if not self.write_file(claude_path, claude_content, overwrite):
            print(f"⚠️  {claude_path} 已存在，使用 --overwrite 覆盖")
            success = False

        if success:
            print(f"✅ 已生成项目初始化文档:")
            print(f"   - {agents_path}")
            print(f"   - {claude_path}")
            print(f"\n📊 项目分析结果:")
            print(f"   名称: {analysis['name']}")
            print(f"   类型: {analysis['type_info']['name']}")
            print(f"   语言: {language}")

        return success

    def _prepare_variables(self, analysis: dict, language: str, output_dir: Path) -> dict:
        """准备模板变量"""
        project_type = analysis['type_info']['name']

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
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="为项目生成 AGENTS.md 和 CLAUDE.md 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完全自动生成（分析当前目录）
  python3 generate.py --auto

  # 自动生成并覆盖现有文件
  python3 generate.py --auto --overwrite

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

    args = parser.parse_args()

    # 创建生成器
    generator = ProjectInitGenerator()

    # 仅检测语言
    if args.detect_language_only:
        lang = generator.detect_language()
        print(f"检测到的语言: {lang}")
        return 0

    # 完全自动模式
    if args.auto:
        output_dir = Path(args.output_dir).resolve()
        success = generator.generate_auto(output_dir, args.overwrite)
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

    # 写入文件
    output_dir = Path(args.output_dir)
    agents_path = output_dir / "AGENTS.md"
    claude_path = output_dir / "CLAUDE.md"

    success = True

    if not generator.write_file(agents_path, agents_content, args.overwrite):
        print(f"错误: {agents_path} 已存在，使用 --overwrite 覆盖")
        success = False

    if not generator.write_file(claude_path, claude_content, args.overwrite):
        print(f"错误: {claude_path} 已存在，使用 --overwrite 覆盖")
        success = False

    if success:
        print(f"✅ 已生成:")
        print(f"   - {agents_path}")
        print(f"   - {claude_path}")
        print(f"\n默认语言: {language}")
        print(f"\n请根据实际情况编辑这些文件，填补 [待补充] 的内容")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
