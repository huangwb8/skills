#!/usr/bin/env python3
"""
Awesome Code - 性能基准测试工具

用于为关键路径建立性能基准、记录性能数据并生成趋势图。
支持性能回归检测。
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class BenchmarkResult:
    """单次基准测试结果"""

    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    std_dev: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BenchmarkHistory:
    """基准测试历史记录"""

    name: str
    results: List[BenchmarkResult] = field(default_factory=list)
    baseline: Optional[BenchmarkResult] = None
    regression_threshold: float = 0.2  # 20% 回归阈值


class BenchmarkRunner:
    """性能基准测试运行器"""

    def __init__(
        self,
        output_dir: str | Path = ".bensz-api/skills/awesome-code/output/benchmarks",
        warmup_iterations: int = 3,
        benchmark_iterations: int = 100,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.warmup_iterations = warmup_iterations
        self.benchmark_iterations = benchmark_iterations
        self.history: Dict[str, BenchmarkHistory] = {}
        self._load_history()

    def _load_history(self) -> None:
        """从文件加载历史记录"""
        history_file = self.output_dir / "history.json"
        if history_file.exists():
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                for name, history_data in data.items():
                    results = [
                        BenchmarkResult(**r) for r in history_data.get("results", [])
                    ]
                    baseline_data = history_data.get("baseline")
                    baseline = BenchmarkResult(**baseline_data) if baseline_data else None
                    self.history[name] = BenchmarkHistory(
                        name=name,
                        results=results,
                        baseline=baseline,
                        regression_threshold=history_data.get("regression_threshold", 0.2),
                    )
            except Exception as e:
                print(f"警告：加载历史记录失败: {e}")

    def _save_history(self) -> None:
        """保存历史记录到文件"""
        history_file = self.output_dir / "history.json"
        data: Dict[str, Dict[str, Any]] = {}
        for name, history in self.history.items():
            data[name] = {
                "name": history.name,
                "results": [
                    {
                        "name": r.name,
                        "iterations": r.iterations,
                        "total_time": r.total_time,
                        "avg_time": r.avg_time,
                        "min_time": r.min_time,
                        "max_time": r.max_time,
                        "median_time": r.median_time,
                        "std_dev": r.std_dev,
                        "timestamp": r.timestamp,
                    }
                    for r in history.results
                ],
                "baseline": (
                    {
                        "name": history.baseline.name,
                        "iterations": history.baseline.iterations,
                        "total_time": history.baseline.total_time,
                        "avg_time": history.baseline.avg_time,
                        "min_time": history.baseline.min_time,
                        "max_time": history.baseline.max_time,
                        "median_time": history.baseline.median_time,
                        "std_dev": history.baseline.std_dev,
                        "timestamp": history.baseline.timestamp,
                    }
                    if history.baseline
                    else None
                ),
                "regression_threshold": history.regression_threshold,
            }
        history_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def benchmark(
        self,
        name: str,
        func: F | None = None,
        *,
        iterations: int | None = None,
    ) -> F | Callable[[F], F]:
        """装饰器或上下文管理器：对函数进行基准测试"""

        def decorator(f: F) -> F:
            @wraps(f)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # 预热
                for _ in range(self.warmup_iterations):
                    f(*args, **kwargs)

                # 基准测试
                iters = iterations or self.benchmark_iterations
                times: List[float] = []
                for _ in range(iters):
                    start = time.perf_counter()
                    result = f(*args, **kwargs)
                    end = time.perf_counter()
                    times.append(end - start)

                # 计算统计信息
                total_time = sum(times)
                avg_time = total_time / len(times)
                min_time = min(times)
                max_time = max(times)
                median_time = statistics.median(times)
                std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

                result_obj = BenchmarkResult(
                    name=name,
                    iterations=iters,
                    total_time=total_time,
                    avg_time=avg_time,
                    min_time=min_time,
                    max_time=max_time,
                    median_time=median_time,  # type: ignore[arg-type]
                    std_dev=std_dev,
                )

                self._record_result(result_obj)
                return result

            return wrapper  # type: ignore[return-value]

        if func is not None:
            return decorator(func)
        return decorator

    def _record_result(self, result: BenchmarkResult) -> None:
        """记录基准测试结果"""
        if result.name not in self.history:
            self.history[result.name] = BenchmarkHistory(name=result.name)

        history = self.history[result.name]
        history.results.append(result)

        # 检查性能回归
        if history.baseline:
            baseline = history.baseline
            if result.avg_time > baseline.avg_time * (1 + history.regression_threshold):
                print(
                    f"⚠️  性能回归检测: {result.name}\n"
                    f"    当前平均时间: {result.avg_time:.6f}s\n"
                    f"    基线平均时间: {baseline.avg_time:.6f}s\n"
                    f"    回退程度: {(result.avg_time / baseline.avg_time - 1) * 100:.2f}%"
                )
            else:
                print(
                    f"✅ {result.name}: 平均 {result.avg_time:.6f}s "
                    f"(最小: {result.min_time:.6f}s, 最大: {result.max_time:.6f}s)"
                )
        else:
            print(
                f"📊 {result.name}: 平均 {result.avg_time:.6f}s "
                f"(最小: {result.min_time:.6f}s, 最大: {result.max_time:.6f}s) "
                f"[设为新基线]"
            )
            history.baseline = result

        self._save_history()

    def set_baseline(self, name: str, index: int | None = None) -> None:
        """设置指定基准测试结果为基线"""
        if name not in self.history:
            print(f"错误：未找到基准测试 '{name}'")
            return

        history = self.history[name]
        if not history.results:
            print(f"错误：基准测试 '{name}' 没有结果")
            return

        if index is None:
            # 使用最新结果
            history.baseline = history.results[-1]
        else:
            if 0 <= index < len(history.results):
                history.baseline = history.results[index]
            else:
                print(f"错误：索引 {index} 超出范围")
                return

        print(f"✅ 已设置 '{name}' 的基线")
        self._save_history()

    def compare(self, name: str, index1: int, index2: int) -> None:
        """比较两次基准测试结果"""
        if name not in self.history:
            print(f"错误：未找到基准测试 '{name}'")
            return

        history = self.history[name]
        if not (0 <= index1 < len(history.results) and 0 <= index2 < len(history.results)):
            print(f"错误：索引超出范围")
            return

        result1 = history.results[index1]
        result2 = history.results[index2]

        diff_pct = (result2.avg_time - result1.avg_time) / result1.avg_time * 100

        print(f"\n📊 比较: {name}")
        print(f"  运行 #{index1 + 1} ({result1.timestamp}): {result1.avg_time:.6f}s")
        print(f"  运行 #{index2 + 1} ({result2.timestamp}): {result2.avg_time:.6f}s")
        print(f"  差异: {diff_pct:+.2f}%")

    def report(self, name: str | None = None) -> None:
        """生成性能报告"""
        if name:
            if name not in self.history:
                print(f"错误：未找到基准测试 '{name}'")
                return
            self._print_single_report(self.history[name])
        else:
            for history in self.history.values():
                self._print_single_report(history)

    def _print_single_report(self, history: BenchmarkHistory) -> None:
        """打印单个基准测试的报告"""
        print(f"\n{'='*60}")
        print(f"基准测试: {history.name}")
        print(f"{'='*60}")

        if history.baseline:
            b = history.baseline
            print(f"基线 (运行时间: {b.timestamp}):")
            print(f"  平均: {b.avg_time:.6f}s")
            print(f"  最小: {b.min_time:.6f}s")
            print(f"  最大: {b.max_time:.6f}s")
            print(f"  中位数: {b.median_time:.6f}s")
            print(f"  标准差: {b.std_dev:.6f}s")

        if history.results:
            latest = history.results[-1]
            print(f"\n最新结果 (运行时间: {latest.timestamp}):")
            print(f"  平均: {latest.avg_time:.6f}s")
            print(f"  最小: {latest.min_time:.6f}s")
            print(f"  最大: {latest.max_time:.6f}s")
            print(f"  中位数: {latest.median_time:.6f}s")
            print(f"  标准差: {latest.std_dev:.6f}s")

            if history.baseline:
                change_pct = (latest.avg_time - history.baseline.avg_time) / history.baseline.avg_time * 100
                print(f"  相对基线变化: {change_pct:+.2f}%")

        print(f"\n总运行次数: {len(history.results)}")


def main() -> int:
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description="Awesome Code - 性能基准测试工具",
    )
    parser.add_argument(
        "--output-dir",
        default=".bensz-api/skills/awesome-code/output/benchmarks",
        help="输出目录（默认: .bensz-api/skills/awesome-code/output/benchmarks）",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="每次基准测试的迭代次数（默认: 100）",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="预热迭代次数（默认: 3）",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # report 命令
    report_parser = subparsers.add_parser("report", help="生成性能报告")
    report_parser.add_argument("--name", help="基准测试名称（可选）")

    # baseline 命令
    baseline_parser = subparsers.add_parser("baseline", help="设置基线")
    baseline_parser.add_argument("name", help="基准测试名称")
    baseline_parser.add_argument("--index", type=int, help="结果索引（默认: 最新）")

    # compare 命令
    compare_parser = subparsers.add_parser("compare", help="比较两次结果")
    compare_parser.add_argument("name", help="基准测试名称")
    compare_parser.add_argument("index1", type=int, help="第一次结果索引")
    compare_parser.add_argument("index2", type=int, help="第二次结果索引")

    args = parser.parse_args()

    runner = BenchmarkRunner(
        output_dir=args.output_dir,
        warmup_iterations=args.warmup,
        benchmark_iterations=args.iterations,
    )

    if args.command == "report":
        runner.report(args.name)
    elif args.command == "baseline":
        runner.set_baseline(args.name, args.index)
    elif args.command == "compare":
        runner.compare(args.name, args.index1, args.index2)
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
