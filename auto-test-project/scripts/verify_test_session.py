#!/usr/bin/env python3
"""
验证测试会话的完整性

用途：防止 auto-test-project 流程中出现"假计划、空报告"问题

检查项：
1. 必需文件是否存在（TEST_PLAN.md、TEST_REPORT.md）
2. 模板占位符是否被替换（不允许出现 {{...}}）
3. 报告内容是否充实（不少于 500 字）
4. 是否包含具体证据（命令输出、文件路径等）
5. 计划与报告的一致性（新增）

用法:
    python3 verify_test_session.py <session_dir>
    python3 verify_test_session.py tests/v202601151400

退出码:
    0 - 验证通过
    1 - 验证失败
    2 - 参数错误
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Tuple

# 配置常量
MIN_REPORT_LENGTH = 500  # 报告最小字符数
REQUIRED_FILES = ["TEST_PLAN.md", "TEST_REPORT.md"]
MIN_ISSUE_COUNT = 10  # 最少问题数量（P0 + P1 + P2）

def _read_text(path: Path) -> str:
    # Be tolerant to non-UTF8 files in real projects; verification should not crash.
    return path.read_text(encoding="utf-8", errors="replace")


def check_required_files(session_dir: Path) -> Tuple[bool, List[str]]:
    """检查必需文件是否存在"""
    issues = []
    for file_name in REQUIRED_FILES:
        file_path = session_dir / file_name
        if not file_path.exists():
            issues.append(f"缺少必需文件: {file_name}")
    return len(issues) == 0, issues


def check_template_placeholders(session_dir: Path) -> Tuple[bool, List[str]]:
    """检查模板占位符是否被替换"""
    issues = []
    placeholder_pattern = re.compile(r'\{\{[^}]+\}\}')

    for file_name in REQUIRED_FILES:
        file_path = session_dir / file_name
        if file_path.exists():
            content = _read_text(file_path)
            placeholders = placeholder_pattern.findall(content)

            if placeholders:
                # 去重并限制显示数量
                unique_placeholders = list(set(placeholders))[:5]
                issues.append(
                    f"{file_name} 包含未替换的模板占位符: {', '.join(unique_placeholders)}"
                )

    return len(issues) == 0, issues


def check_report_content(session_dir: Path, *, min_report_length: int) -> Tuple[bool, List[str]]:
    """检查报告内容是否充实"""
    issues = []
    report_file = session_dir / "TEST_REPORT.md"

    if not report_file.exists():
        return True, issues  # 已在 check_required_files 中处理

    content = _read_text(report_file)

    # 检查是否包含未填写的占位文本
    placeholder_patterns = [
        r'（在此[处处]填写[^）]*）',
        r'（在此[处处]填入[^）]*）',
        r'（描述[^）]*）',
        r'（填入[^）]*）',
        r'\[TODO[^\]]*\]',
        r'\[待[^\]]*\]',
        r'待[补充填写添加][^。。。]*。',
    ]

    for pattern in placeholder_patterns:
        matches = re.findall(pattern, content)
        if matches:
            # 取前 3 个示例
            examples = matches[:3]
            issues.append(
                f"TEST_REPORT.md 包含未填写的占位文本: {', '.join(examples)}"
            )
            break  # 找到一个类型就够了

    # 移除占位文本后计算实际内容长度
    cleaned_content = content
    for pattern in placeholder_patterns:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL)

    actual_length = len(cleaned_content.strip())

    if actual_length < min_report_length:
        issues.append(
            f"TEST_REPORT.md 内容过短（{actual_length} 字符，要求 ≥ {min_report_length} 字符），"
            "可能未填充实际内容"
        )

    return len(issues) == 0, issues


def check_evidence_presence(session_dir: Path) -> Tuple[bool, List[str]]:
    """检查是否包含具体证据"""
    issues = []
    report_file = session_dir / "TEST_REPORT.md"

    if not report_file.exists():
        return True, issues  # 已在 check_required_files 中处理

    content = _read_text(report_file)

    # 检查证据类型的标记（命令输出、文件路径、对比结果等）
    evidence_patterns = [
        r'```[a-z]*\n',  # 代码块（命令输出）
        r'\[.*?\]\([^)]+\)',  # Markdown 链接（文件路径）
        # 文件引用（如 src/file.py:123 / auto-test-project/scripts/x.py:10 / ./path/to/a.md:3）
        r'(?<!\w)(?:\./)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.[A-Za-z0-9_]+:\d+',
        # Windows 路径引用（如 C:\path\to\file.py:123）
        r'(?<!\w)[A-Za-z]:\\[^:\n]+:\d+',
        r'✅|❌|⚠️',  # 状态标记
        r'修复前|修复后|对比|验证',  # 对比关键词
    ]

    has_evidence = any(re.search(pattern, content) for pattern in evidence_patterns)

    if not has_evidence:
        issues.append(
            "TEST_REPORT.md 缺少具体证据（命令输出、文件路径、对比结果、状态标记等）"
        )

    return len(issues) == 0, issues


def check_plan_report_consistency(
    session_dir: Path,
    *,
    min_issue_count: int,
    require_plan: bool,
) -> Tuple[bool, List[str]]:
    """
    检查计划与报告的一致性

    验证：
    - plans/ 中的每个问题是否在 TEST_REPORT.md 中有对应记录
    - 成功标准是否在报告中有验证结论
    """
    issues = []

    # 尝试找到对应的 plan 文件
    session_name = session_dir.name
    project_root = session_dir.parent.parent
    plan_file = project_root / "plans" / f"{session_name}.md"

    if not plan_file.exists():
        if require_plan:
            issues.append(f"缺少规划文档: plans/{session_name}.md")
            return False, issues
        # 如果 plan 文件不存在且未强制要求，跳过一致性检查
        return True, issues

    report_file = session_dir / "TEST_REPORT.md"
    if not report_file.exists():
        return True, issues  # 已在 check_required_files 中处理

    plan_content = _read_text(plan_file)
    report_content = _read_text(report_file)

    # 提取计划中的问题编号（如 P0-1, P1-2）
    plan_issues = re.findall(r'#### ([Pp][012]-\d+):', plan_content)

    if not plan_issues:
        # 计划中没有可引用的问题编号时，一致性检查无法落地
        if require_plan:
            issues.append("规划文档未包含形如 '#### P0-1:' 的问题编号，无法执行计划-报告一致性检查")
            return False, issues
        return True, issues

    # 检查每个问题是否在报告中有记录
    missing_issues = []
    for issue_id in plan_issues:
        # 检查问题编号是否出现在报告中
        if issue_id not in report_content:
            missing_issues.append(issue_id)

    if missing_issues:
        issues.append(
            f"计划中的问题在测试报告中无对应记录: {', '.join(missing_issues[:5])}"
            + (f" ... (共 {len(missing_issues)} 个)" if len(missing_issues) > 5 else "")
        )

    # 检查问题数量是否达到最低要求
    total_issues = len(plan_issues)
    if total_issues < min_issue_count:
        issues.append(
            f"计划中的问题数量不足：发现 {total_issues} 个，要求 ≥ {min_issue_count} 个"
        )

    return len(issues) == 0, issues


def verify_test_session(
    session_dir: Path,
    *,
    min_report_length: int,
    min_issue_count: int,
    require_plan: bool,
) -> Tuple[bool, List[str]]:
    """验证测试会话目录的完整性"""
    all_issues = []

    # 检查 1: 必需文件
    passed, issues = check_required_files(session_dir)
    all_issues.extend(issues)

    # 检查 2: 模板占位符
    passed, issues = check_template_placeholders(session_dir)
    all_issues.extend(issues)

    # 检查 3: 报告内容长度
    passed, issues = check_report_content(session_dir, min_report_length=min_report_length)
    all_issues.extend(issues)

    # 检查 4: 证据存在性
    passed, issues = check_evidence_presence(session_dir)
    all_issues.extend(issues)

    # 检查 5: 计划与报告一致性
    passed, issues = check_plan_report_consistency(
        session_dir,
        min_issue_count=min_issue_count,
        require_plan=require_plan,
    )
    all_issues.extend(issues)

    return len(all_issues) == 0, all_issues


def print_summary(session_dir: Path, is_valid: bool, issues: List[str]):
    """打印验证结果摘要"""
    if is_valid:
        print(f"✅ 验证通过: {session_dir}")
        print(f"   所有检查项均满足要求")
    else:
        print(f"❌ 验证失败: {session_dir}")
        print(f"   发现 {len(issues)} 个问题：")
        for issue in issues:
            print(f"   - {issue}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an auto-test-project test session directory.")
    parser.add_argument("session_dir", help="Test session directory, e.g. tests/v202601151400")
    parser.add_argument(
        "--require-plan",
        action="store_true",
        help="Fail if plans/<session_name>.md is missing or lacks issue ids like '#### P0-1:'.",
    )
    parser.add_argument(
        "--min-report-length",
        type=int,
        default=MIN_REPORT_LENGTH,
        help=f"Minimum TEST_REPORT.md length after cleaning placeholders (default: {MIN_REPORT_LENGTH}).",
    )
    parser.add_argument(
        "--min-issue-count",
        type=int,
        default=MIN_ISSUE_COUNT,
        help=f"Minimum issue ids in plan (default: {MIN_ISSUE_COUNT}).",
    )
    args = parser.parse_args()

    session_dir = Path(args.session_dir)
    if not session_dir.exists():
        print(f"错误: 目录不存在: {session_dir}", file=sys.stderr)
        return 1
    if not session_dir.is_dir():
        print(f"错误: 不是目录: {session_dir}", file=sys.stderr)
        return 1

    is_valid, issues = verify_test_session(
        session_dir,
        min_report_length=args.min_report_length,
        min_issue_count=args.min_issue_count,
        require_plan=args.require_plan,
    )
    print_summary(session_dir, is_valid, issues)
    return 0 if is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
