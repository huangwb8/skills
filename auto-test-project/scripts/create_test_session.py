#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path


def _generate_test_id(now: dt.datetime) -> str:
    """生成测试会话 ID（分钟级时间戳）"""
    return f"v{now:%Y%m%d%H%M}"


def _ensure_dir(path: Path) -> None:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def _safe_write(path: Path, content: str, *, overwrite: bool) -> None:
    """安全写入文件（避免意外覆盖）"""
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content, encoding="utf-8")


def _copy_or_template(
    *,
    dst_path: Path,
    src_path: Path | None,
    template_path: Path | None,
    overwrite: bool,
) -> None:
    """复制源文件或使用模板填充目标文件"""
    if dst_path.exists() and not overwrite:
        return

    if src_path is not None and src_path.exists():
        if dst_path.exists():
            dst_path.unlink()
        shutil.copyfile(src_path, dst_path)
        return

    if template_path is not None and template_path.exists():
        _safe_write(dst_path, template_path.read_text(encoding="utf-8"), overwrite=overwrite)
        return

    # 回退：创建空模板
    _safe_write(
        dst_path,
        "# TEST_PLAN\n\n（未找到可复制的计划文档或模板，请手动补全）\n",
        overwrite=overwrite,
    )


def _normalize_kind(kind: str) -> str:
    """标准化轮次类型参数"""
    kind = kind.strip().lower()
    if kind in {"a", "a_round", "a-round"}:
        return "a"
    if kind in {"b", "b_round", "b-round"}:
        return "b"
    raise ValueError("kind must be 'a' or 'b'")


def _validate_project_root(project_root: Path) -> None:
    """验证项目根目录是否为有效项目"""
    if not project_root.exists() or not project_root.is_dir():
        raise FileNotFoundError(f"Project root does not exist or is not a directory: {project_root}")

    # 检查是否存在项目指令文件
    instruction_files = ["CLAUDE.md", "AGENTS.md", "PROJECT.md", "README.md"]
    has_instruction = any((project_root / f).exists() for f in instruction_files)

    if not has_instruction:
        # 如果没有项目指令文件，发出警告但不阻止（可能是一个新项目）
        print(f"⚠️  Warning: No project instruction file found in {project_root}")
        print(f"   Expected one of: {', '.join(instruction_files)}")


def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Create an auto-test-project test session skeleton (A round or B round).",
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Path to project root directory (contains CLAUDE.md, AGENTS.md, or similar).",
    )
    parser.add_argument(
        "--kind",
        default="a",
        help="Session kind: a (default) or b.",
    )
    parser.add_argument(
        "--id",
        default="",
        help="Explicit test id like vYYYYMMDDHHMM (optional).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing session files (not recommended).",
    )
    args = parser.parse_args()

    # 验证并规范化项目根目录
    project_root = Path(args.project_root).expanduser().resolve()
    _validate_project_root(project_root)

    # 标准化参数
    kind = _normalize_kind(args.kind)
    test_id = args.id.strip() or _generate_test_id(dt.datetime.now())
    if not test_id.startswith("v"):
        raise ValueError("test id must start with 'v', e.g. vYYYYMMDDHHMM")

    # 设置目录路径
    plans_dir = project_root / "plans"
    tests_dir = project_root / "tests"
    templates_dir = Path(__file__).parent.parent / "templates"

    _ensure_dir(plans_dir)
    _ensure_dir(tests_dir)

    # 根据轮次类型设置会话名称
    if kind == "a":
        session_name = test_id
        plan_src = plans_dir / f"{test_id}.md"
        test_plan_template = templates_dir / "TEST_PLAN_TEMPLATE.md"
    else:
        session_name = f"B轮-{test_id}"
        plan_src = plans_dir / f"B轮-{test_id}.md"
        test_plan_template = templates_dir / "TEST_PLAN_TEMPLATE.md"

    # 创建测试会话目录
    session_dir = tests_dir / session_name
    _ensure_dir(session_dir)
    _ensure_dir(session_dir / "_artifacts")
    _ensure_dir(session_dir / "_scripts")

    # 复制或创建测试计划
    _copy_or_template(
        dst_path=session_dir / "TEST_PLAN.md",
        src_path=plan_src if plan_src.exists() else None,
        template_path=test_plan_template if test_plan_template.exists() else None,
        overwrite=args.overwrite,
    )

    # 创建测试报告
    report_path = session_dir / "TEST_REPORT.md"
    if not report_path.exists() or args.overwrite:
        _safe_write(
            report_path,
            "# 测试报告（TEST_REPORT）\n\n"
            f"**测试会话**: {session_name}\n"
            f"**项目根目录**: {project_root}\n"
            f"**测试时间**: {dt.datetime.now():%Y-%m-%d %H:%M:%S}\n\n"
            "## 结果\n\n"
            "- 状态：✅ 通过 / ❌ 失败 / ⚠️ 部分通过\n\n"
            "## 证据\n\n"
            "- （填入命令输出、文件路径、对比结果等）\n",
            overwrite=args.overwrite,
        )

    # 输出会话目录路径（便于后续操作）
    print(str(session_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
