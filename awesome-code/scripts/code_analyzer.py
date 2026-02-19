#!/usr/bin/env python3
"""
Awesome Code - 代码静态分析工具

功能：
- 代码复杂度分析
- 代码重复检测
- 命名规范检查
- 生成分析报告
"""

import argparse
import ast
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class CodeAnalyzer:
    """代码静态分析器"""

    def __init__(self, path: str = ".", complexity_threshold: int = 10):
        self.path = Path(path)
        self.complexity_threshold = complexity_threshold
        self.issues = []

    def analyze(self) -> Dict:
        """执行完整分析"""
        results = {
            "complexity": self.analyze_complexity(),
            "duplication": self.analyze_duplication(),
            "naming": self.analyze_naming(),
            "summary": self.generate_summary(),
        }
        return results

    def analyze_complexity(self) -> List[Dict]:
        """分析代码复杂度（圈复杂度）"""
        complexities = []

        for py_file in self.path.rglob("*.py"):
            if any(skip in str(py_file) for skip in ["__pycache__", ".venv"]):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        complexity = self.calculate_complexity(node)

                        if complexity > self.complexity_threshold:
                            complexities.append({
                                "file": str(py_file.relative_to(self.path)),
                                "function": node.name,
                                "line": node.lineno,
                                "complexity": complexity,
                                "threshold": self.complexity_threshold,
                            })

            except Exception as e:
                self.issues.append(f"解析 {py_file} 失败: {e}")

        return complexities

    def calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, (
                ast.If, ast.While, ast.For, ast.AsyncFor,
                ast.ExceptHandler, ast.With, ast.AsyncWith
            )):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def analyze_duplication(self) -> List[Dict]:
        """分析代码重复"""
        # 简化的重复检测：查找重复的函数名和类名
        names = defaultdict(list)

        for py_file in self.path.rglob("*.py"):
            if any(skip in str(py_file) for skip in ["__pycache__", ".venv"]):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        names[node.name].append({
                            "file": str(py_file.relative_to(self.path)),
                            "line": node.lineno,
                        })
                    elif isinstance(node, ast.ClassDef):
                        names[f"class:{node.name}"].append({
                            "file": str(py_file.relative_to(self.path)),
                            "line": node.lineno,
                        })

            except Exception:
                pass

        # 找出重复的定义
        duplications = []
        for name, locations in names.items():
            if len(locations) > 1:
                duplications.append({
                    "name": name,
                    "count": len(locations),
                    "locations": locations,
                })

        return duplications

    def analyze_naming(self) -> List[Dict]:
        """分析命名规范"""
        issues = []

        # 命名规范
        function_pattern = re.compile(r"^[a-z][a-z0-9_]*$")  # snake_case
        class_pattern = re.compile(r"^[A-Z][a-zA-Z0-9]*$")  # PascalCase
        constant_like_pattern = re.compile(r"^[A-Za-z0-9_]+$")  # simple identifiers

        for py_file in self.path.rglob("*.py"):
            if any(skip in str(py_file) for skip in ["__pycache__", ".venv"]):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    # 检查函数命名
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not function_pattern.match(node.name):
                            issues.append({
                                "type": "function_naming",
                                "file": str(py_file.relative_to(self.path)),
                                "name": node.name,
                                "line": node.lineno,
                                "suggestion": "函数名应使用 snake_case",
                            })

                    # 检查类命名
                    elif isinstance(node, ast.ClassDef):
                        if not class_pattern.match(node.name):
                            issues.append({
                                "type": "class_naming",
                                "file": str(py_file.relative_to(self.path)),
                                "name": node.name,
                                "line": node.lineno,
                                "suggestion": "类名应使用 PascalCase",
                            })

                # 检查常量命名（模块级赋值，启发式：带下划线且大小写混用）
                # 例如: Api_KEY, my_CONST, Max_Value
                for stmt in getattr(tree, "body", []):
                    if not isinstance(stmt, ast.Assign):
                        continue
                    for target in stmt.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        name = target.id
                        if not constant_like_pattern.match(name):
                            continue
                        if "_" not in name:
                            continue
                        if re.search(r"[A-Z]", name) and re.search(r"[a-z]", name):
                            issues.append({
                                "type": "constant_naming",
                                "file": str(py_file.relative_to(self.path)),
                                "name": name,
                                "line": stmt.lineno,
                                "suggestion": "疑似常量但大小写混用，建议使用 UPPER_CASE",
                            })

            except Exception:
                pass

        return issues

    def generate_summary(self) -> Dict:
        """生成分析摘要"""
        return {
            "total_issues": len(self.issues),
            "issues": self.issues,
        }


class ReportGenerator:
    """报告生成器"""

    def __init__(self, results: Dict, output_file: str = None):
        self.results = results
        self.output_file = output_file

    def generate_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        report = []

        report.append("# 代码分析报告\n")
        report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 复杂度报告
        report.append("## 📊 代码复杂度\n")
        if self.results["complexity"]:
            report.append(f"⚠️ 发现 {len(self.results['complexity'])} 个高复杂度函数:\n\n")
            for item in self.results["complexity"]:
                report.append(
                    f"- **{item['function']}** ({item['file']}:{item['line']})\n"
                    f"  - 复杂度: {item['complexity']} (阈值: {item['threshold']})\n"
                )
        else:
            report.append("✅ 未发现高复杂度函数\n")

        # 重复代码报告
        report.append("\n## 🔄 代码重复\n")
        if self.results["duplication"]:
            report.append(f"⚠️ 发现 {len(self.results['duplication'])} 个重复定义:\n\n")
            for item in self.results["duplication"]:
                report.append(f"- **{item['name']}** ({item['count']} 处)\n")
                for loc in item["locations"]:
                    report.append(f"  - {loc['file']}:{loc['line']}\n")
        else:
            report.append("✅ 未发现重复定义\n")

        # 命名规范报告
        report.append("\n## 📝 命名规范\n")
        if self.results["naming"]:
            report.append(f"⚠️ 发现 {len(self.results['naming'])} 个命名问题:\n\n")
            for item in self.results["naming"]:
                report.append(
                    f"- **{item['type']}**: {item['name']} "
                    f"({item['file']}:{item['line']})\n"
                    f"  - {item['suggestion']}\n"
                )
        else:
            report.append("✅ 命名规范检查通过\n")

        # 摘要
        if self.results["summary"]["total_issues"] > 0:
            report.append("\n## ⚠️ 其他问题\n")
            for issue in self.results["summary"]["issues"]:
                report.append(f"- {issue}\n")

        return "".join(report)

    def save_report(self) -> None:
        """保存报告到文件"""
        if not self.output_file:
            return

        content = self.generate_markdown()

        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"📄 报告已保存到: {output_path}")

    def print_report(self) -> None:
        """打印报告到控制台"""
        print(self.generate_markdown())


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Awesome Code - 代码静态分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 分析当前目录
  %(prog)s

  # 分析指定目录
  %(prog)s --path src/

  # 设置复杂度阈值为 15
  %(prog)s --complexity-threshold 15

  # 生成报告文件
  %(prog)s --report analysis_report.md
        """,
    )

    parser.add_argument(
        "--path", "-p",
        default=".",
        help="要分析的目录路径（默认: 当前目录）",
    )

    parser.add_argument(
        "--complexity-threshold", "-c",
        type=int,
        default=10,
        help="圈复杂度阈值（默认: 10）",
    )

    parser.add_argument(
        "--report", "-r",
        help="输出报告文件路径（Markdown 格式）",
    )

    args = parser.parse_args()

    # 执行分析
    analyzer = CodeAnalyzer(
        path=args.path,
        complexity_threshold=args.complexity_threshold,
    )

    results = analyzer.analyze()

    # 生成报告
    generator = ReportGenerator(results, output_file=args.report)
    generator.print_report()

    if args.report:
        generator.save_report()


if __name__ == "__main__":
    main()
