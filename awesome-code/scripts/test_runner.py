#!/usr/bin/env python3
"""
Awesome Code - TDD 测试运行器

功能：
- 自动发现并运行测试
- 生成覆盖率报告
- 支持监视模式（文件变更时自动运行）
- TDD 循环支持（Red-Green-Refactor）
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List


class TestRunner:
    """TDD 测试运行器"""

    def __init__(
        self,
        test_path: str = "tests",
        coverage: bool = False,
        watch: bool = False,
        fail_fast: bool = False,
        framework: str = "auto",
    ):
        self.test_path = Path(test_path)
        self.coverage = coverage
        self.watch = watch
        self.fail_fast = fail_fast
        self.framework = framework

    def detect_framework(self) -> str:
        """自动检测测试框架"""
        if self.framework != "auto":
            return self.framework

        # 只检查配置文件和测试文件，避免遍历所有文件导致内存问题

        # 检查 pytest 配置文件
        if Path("pytest.ini").exists() or Path("pyproject.toml").exists():
            return "pytest"

        # 检查 jest 配置文件
        if Path("jest.config.js").exists() or Path("jest.config.ts").exists():
            return "jest"

        # 检查 package.json 中是否包含 jest
        if Path("package.json").exists():
            try:
                import json
                with open("package.json", "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                    if "jest" in pkg.get("devDependencies", {}) or "jest" in pkg.get("dependencies", {}):
                        return "jest"
            except Exception:
                pass

        # 检查是否存在 Python 测试文件
        py_test_files = list(Path(".").glob("**/test_*.py"))[:10] + list(Path(".").glob("**/*_test.py"))[:10]
        if py_test_files:
            # 只检查前几个文件，限制文件大小
            for f in py_test_files[:5]:
                try:
                    if f.stat().st_size < 100000:  # 小于 100KB
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        if "unittest" in content:
                            return "unittest"
                except Exception:
                    pass
            return "pytest"

        # 检查是否存在 JavaScript 测试文件
        js_test_files = list(Path(".").glob("**/*.test.js"))[:5] + list(Path(".").glob("**/*.spec.js"))[:5]
        if js_test_files:
            return "jest"

        # 默认使用 pytest
        return "pytest"

    def run_pytest(self) -> int:
        """运行 pytest 测试"""
        cmd = [sys.executable, "-m", "pytest"]

        # 添加参数
        if self.fail_fast:
            cmd.append("-x")

        if self.coverage:
            cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])

        cmd.append(str(self.test_path))

        print(f"🧪 运行测试: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    def run_unittest(self) -> int:
        """运行 unittest 测试"""
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(self.test_path)]
        print(f"🧪 运行测试: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    def run_jest(self) -> int:
        """运行 Jest 测试"""
        cmd = ["npx", "jest"]

        if self.coverage:
            cmd.append("--coverage")

        if self.fail_fast:
            cmd.append("--bail")

        print(f"🧪 运行测试: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    def run_tests(self) -> int:
        """运行测试"""
        framework = self.detect_framework()
        print(f"📦 使用测试框架: {framework}")

        if framework == "pytest":
            return self.run_pytest()
        elif framework == "unittest":
            return self.run_unittest()
        elif framework == "jest":
            return self.run_jest()
        else:
            print(f"❌ 不支持的测试框架: {framework}")
            return 1

    def watch_files(self) -> None:
        """监视文件变更并自动运行测试"""
        print(f"👀 监视模式启动（目录: {self.test_path}）")
        print("按 Ctrl+C 停止\n")

        file_times = {}
        ignore_dirs = {
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            ".awesome-code",
            "dist",
            "build",
        }
        watch_suffixes = {".py", ".js"}

        try:
            while True:
                # 检查文件变更
                changed = False
                for file_path in Path(".").rglob("*"):
                    if file_path.suffix not in watch_suffixes:
                        continue
                    if any(part in ignore_dirs for part in file_path.parts):
                        continue
                    try:
                        mtime = os.path.getmtime(file_path)
                    except OSError:
                        # File may be deleted/locked between discovery and stat.
                        continue

                    if file_path not in file_times:
                        file_times[file_path] = mtime
                    elif mtime > file_times[file_path]:
                        print(f"\n📝 检测到文件变更: {file_path}")
                        file_times[file_path] = mtime
                        changed = True
                        break

                if changed:
                    print(f"\n{'='*60}")
                    result = self.run_tests()
                    print(f"{'='*60}\n")

                    if result == 0:
                        print("✅ 测试通过！继续 TDD 循环：")
                        print("   - Green 状态：考虑 Refactor")
                        print("   - 或开始下一个 Red 状态")
                    else:
                        print("❌ 测试失败（Red 状态）")
                        print("   - 编写最小实现使其通过（Green）")

                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n👋 监视模式已停止")

    def run(self) -> int:
        """主运行方法"""
        if not self.test_path.exists():
            print(f"❌ 测试目录不存在: {self.test_path}")
            return 1

        if self.watch:
            self.watch_files()
            return 0
        else:
            return self.run_tests()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Awesome Code - TDD 测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 运行所有测试
  %(prog)s

  # 运行测试并生成覆盖率报告
  %(prog)s --coverage

  # 监视模式（文件变更时自动运行）
  %(prog)s --watch

  # 快速失败（第一个测试失败即停止）
  %(prog)s --fail-fast

  # 指定测试目录
  %(prog)s --path tests/unit
        """,
    )

    parser.add_argument(
        "--path", "-p",
        default="tests",
        help="测试目录路径（默认: tests）",
    )

    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告",
    )

    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="监视模式（文件变更时自动运行）",
    )

    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="快速失败（第一个测试失败即停止）",
    )

    parser.add_argument(
        "--framework", "-f",
        choices=["auto", "pytest", "unittest", "jest"],
        default="auto",
        help="测试框架（默认: auto 自动检测）",
    )

    args = parser.parse_args()

    runner = TestRunner(
        test_path=args.path,
        coverage=args.coverage,
        watch=args.watch,
        fail_fast=args.fail_fast,
        framework=args.framework,
    )

    sys.exit(runner.run())


if __name__ == "__main__":
    main()
