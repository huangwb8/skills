#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path


_TEST_ID_RE = re.compile(r"^v\d{12}$")


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


def _render_template(template: str, *, values: dict[str, str]) -> str:
    """
    渲染模板，替换 {{KEY}} 格式的占位符

    Args:
        template: 模板内容
        values: 占位符键值对，如 {"TEST_ID": "v202601151200"}

    Returns:
        渲染后的内容
    """
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def _copy_or_template(
    *,
    dst_path: Path,
    src_path: Path | None,
    template_path: Path | None,
    template_values: dict[str, str] | None = None,
    overwrite: bool,
) -> None:
    """
    复制源文件或使用模板填充目标文件

    Args:
        dst_path: 目标文件路径
        src_path: 源文件路径（优先复制）
        template_path: 模板文件路径
        template_values: 模板变量值（用于替换 {{KEY}}）
        overwrite: 是否覆盖已存在的文件
    """
    if dst_path.exists() and not overwrite:
        return

    # 优先复制源文件
    if src_path is not None and src_path.exists():
        if dst_path.exists():
            dst_path.unlink()
        shutil.copyfile(src_path, dst_path)
        return

    # 使用模板文件并替换变量
    if template_path is not None and template_path.exists():
        template_text = template_path.read_text(encoding="utf-8")
        if template_values:
            template_text = _render_template(template_text, values=template_values)
        _safe_write(dst_path, template_text, overwrite=overwrite)
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
        print(f"⚠️  Warning: No project instruction file found in {project_root}", file=sys.stderr)
        print(f"   Expected one of: {', '.join(instruction_files)}", file=sys.stderr)

def _detect_project_type(project_root: Path) -> str:
    """
    尝试用最小启发式识别项目类型（不依赖第三方 YAML 库）。

    说明：这是给模板自动填充用的“提示信息”，不是强约束；如无法识别则返回 unknown。
    """
    if (project_root / "SKILL.md").exists():
        return "skill"
    if (project_root / ".github" / "workflows").exists() or (project_root / "workflows").exists():
        return "workflow"
    if (project_root / "scripts").exists() or (project_root / "bin").exists():
        return "script_collection"
    if (project_root / "docs").exists() or (project_root / "mkdocs.yml").exists():
        return "documentation"
    return "unknown"


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
        "--create-plan",
        action="store_true",
        help="Create missing plan doc skeleton under plans/ (optional).",
    )
    parser.add_argument(
        "--allow-unsafe-root",
        action="store_true",
        help="Allow using filesystem root or user home as --project-root (not recommended).",
    )
    parser.add_argument(
        "--seed-test-plan-from-plan",
        action="store_true",
        help="If plan doc exists, seed TEST_PLAN.md from it (optional).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing session files (not recommended).",
    )
    args = parser.parse_args()

    # 先做参数格式校验，避免后续报堆栈
    explicit_id = args.id.strip()
    if explicit_id and not _TEST_ID_RE.match(explicit_id):
        parser.error("--id must match vYYYYMMDDHHMM (e.g. v202601151230)")

    try:
        # 验证并规范化项目根目录
        project_root = Path(args.project_root).expanduser().resolve()

        # Safety guard: prevent accidental pollution of extremely broad directories.
        anchor_root = Path(project_root.anchor) if project_root.anchor else project_root
        is_fs_root = project_root == anchor_root
        is_home = project_root == Path.home().resolve()
        if (is_fs_root or is_home) and not args.allow_unsafe_root:
            parser.error(
                f"Refusing unsafe --project-root: {project_root} (use --allow-unsafe-root to override)"
            )

        _validate_project_root(project_root)

        # 标准化参数
        kind = _normalize_kind(args.kind)
        test_id = explicit_id or _generate_test_id(dt.datetime.now())
        if not _TEST_ID_RE.match(test_id):
            parser.error("--id must match vYYYYMMDDHHMM (e.g. v202601151230)")

        # 根据轮次类型设置会话名称（在渲染模板前先确定，避免引用未定义变量）
        if kind == "a":
            session_name = test_id
            round_kind = "A轮"
        else:
            session_name = f"B轮-{test_id}"
            round_kind = "B轮"

        # 设置目录路径
        plans_dir = project_root / "plans"
        tests_dir = project_root / "tests"
        templates_dir = Path(__file__).parent.parent / "templates"

        _ensure_dir(plans_dir)
        _ensure_dir(tests_dir)

        # 准备模板变量
        now = dt.datetime.now()
        project_type = _detect_project_type(project_root)
        template_values = {
            "TEST_ID": test_id,
            "PROJECT_NAME": project_root.name,
            "PROJECT_ROOT": str(project_root),
            "SESSION_NAME": session_name,
            "TEST_TIME": now.strftime("%Y-%m-%d %H:%M:%S"),
            "TEST_DATE": now.date().isoformat(),
            "ROUND_KIND": round_kind,
            # 计划模板（OPTIMIZATION_PLAN_TEMPLATE.md）中使用的头字段
            "PLAN_ID": test_id,
            "PLAN_TIME": now.isoformat(timespec="minutes"),
            "A_ROUND_ID": test_id,
            # 测试计划模板中使用的字段
            "PROJECT_TYPE": project_type,
        }

        # 根据轮次类型设置会话相关模板/文件名
        if kind == "a":
            plan_src = plans_dir / f"{test_id}.md"
            plan_template = templates_dir / "OPTIMIZATION_PLAN_TEMPLATE.md"
            test_plan_template = templates_dir / "TEST_PLAN_TEMPLATE.md"
        else:
            plan_src = plans_dir / f"B轮-{test_id}.md"
            plan_template = templates_dir / "B_ROUND_CHECK_TEMPLATE.md"
            test_plan_template = templates_dir / "TEST_PLAN_TEMPLATE.md"

        # 更新模板变量
        template_values["SESSION_NAME"] = session_name
        template_values["PLAN_DOC_PATH"] = str(plan_src.relative_to(project_root))
        template_values["PLAN_FILE"] = template_values["PLAN_DOC_PATH"]

        # 可选：创建计划文档骨架
        if args.create_plan:
            if not plan_src.exists() or args.overwrite:
                if plan_template.exists():
                    _safe_write(
                        plan_src,
                        _render_template(plan_template.read_text(encoding="utf-8"), values=template_values),
                        overwrite=args.overwrite,
                    )
                else:
                    _safe_write(
                        plan_src,
                        f"# 计划文档（{session_name}）\n\n（未找到模板，请手动补全）\n",
                        overwrite=args.overwrite,
                    )

        # 创建测试会话目录
        session_dir = tests_dir / session_name
        _ensure_dir(session_dir)
        _ensure_dir(session_dir / "_artifacts")
        _ensure_dir(session_dir / "_scripts")

        # 复制或创建测试计划（使用模板变量替换）
        _copy_or_template(
            dst_path=session_dir / "TEST_PLAN.md",
            src_path=plan_src if (args.seed_test_plan_from_plan and plan_src.exists()) else None,
            template_path=test_plan_template if test_plan_template.exists() else None,
            template_values=template_values,
            overwrite=args.overwrite,
        )

        # 创建测试报告（使用模板变量替换）
        report_path = session_dir / "TEST_REPORT.md"
        test_report_template = templates_dir / "TEST_REPORT_TEMPLATE.md"
        if not report_path.exists() or args.overwrite:
            if test_report_template.exists():
                # 使用模板文件并替换变量
                _safe_write(
                    report_path,
                    _render_template(test_report_template.read_text(encoding="utf-8"), values=template_values),
                    overwrite=args.overwrite,
                )
            else:
                # 回退到内联模板
                _safe_write(
                    report_path,
                    _render_template(
                    "# 测试报告（{{ROUND_KIND}}测试）\n\n"
                    "**测试会话**: {{SESSION_NAME}}\n"
                    "**项目根目录**: {{PROJECT_ROOT}}\n"
                    "**测试时间**: {{TEST_TIME}}\n\n"
                    "## 执行摘要\n\n"
                    "**状态**: （在此填写：✅ 通过 / ❌ 失败 / ⚠️ 部分通过）\n\n"
                    "**简要说明**: （在此填写本轮测试的总体结论，不超过 3 句话）\n\n"
                    "## 验证点执行情况\n\n"
                    "### 验证点 1: （验证点名称）\n\n"
                    "**状态**: ✅ 通过 / ❌ 失败\n\n"
                    "**执行过程**:\n"
                    "```bash\n"
                    "# 在此填入实际执行的命令\n"
                    "```\n\n"
                    "**输出结果**:\n"
                    "```\n"
                    "# 在此填入命令的实际输出\n"
                    "```\n\n"
                    "**结论**: （在此填入验证结论）\n\n"
                    "## 问题修复记录\n\n"
                    "### P0-1: （问题标题）\n\n"
                    "**修复前**: （描述修复前的状态）\n\n"
                    "**修复措施**: （描述具体做了什么）\n\n"
                    "**修复后**: （描述修复后的状态）\n\n"
                    "**验证方法**:\n"
                    "```bash\n"
                    "# 在此填入验证命令\n"
                    "```\n\n"
                    "## 遗留问题\n\n"
                    "- （在此填入本轮未解决的问题）\n\n"
                    "## 下一步建议\n\n"
                    "（在此填入是否需要下一轮、重点是什么）\n\n"
                    "---\n\n"
                    "**⚠️ 重要提醒**: 本报告必须完全替换上述占位文本，不得保留任何「在此处填写」或「（...）」的内容。\n"
                    "**验证方法**: 运行 `python3 auto-test-project/scripts/verify_test_session.py <session_dir>` 检查报告完整性。\n",
                        values=template_values
                    ),
                    overwrite=args.overwrite,
                )

        # 输出会话目录路径（便于后续操作）
        print(str(session_dir))
        return 0
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
