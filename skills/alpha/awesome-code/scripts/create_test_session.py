#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
import typing
from pathlib import Path

from _config import get_nested, load_skill_config


def _generate_test_id(now: dt.datetime) -> str:
    return f"v{now:%Y%m%d%H%M}"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _safe_write(path: Path, content: str, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing file: {path}\n"
            f"Hint: Use --overwrite to force overwrite existing files."
        )
    path.write_text(content, encoding="utf-8")


_TEST_ID_RE = re.compile(r"^v\d{12}$")


def _validate_test_id(parser: argparse.ArgumentParser, test_id: str) -> str:
    test_id = test_id.strip()
    if not _TEST_ID_RE.fullmatch(test_id):
        _fail(parser, "test id must match vYYYYMMDDHHMM (e.g. v202601170020)")
    return test_id


def _ensure_within_root(parser: argparse.ArgumentParser, root: Path, path: Path, what: str) -> Path:
    root_resolved = root.resolve()
    path_resolved = path.resolve()
    try:
        path_resolved.relative_to(root_resolved)
    except Exception:
        _fail(parser, f"{what} escapes the allowed root: {path}")
    return path_resolved


def _validate_rel_dir(parser: argparse.ArgumentParser, value: object, what: str) -> Path:
    p = Path(str(value))
    # Disallow absolute paths and parent traversal; allow nested relative dirs like "plans/a".
    if p.is_absolute() or p.anchor:
        _fail(parser, f"{what} must be a relative path, got: {p}")
    if any(part in {"..", ""} for part in p.parts):
        _fail(parser, f"{what} must not contain '..' segments, got: {p}")
    return p


def _render_template(template: str, *, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def _copy_or_template(
    *,
    dst_path: Path,
    src_path: Path | None,
    template_path: Path | None,
    template_values: dict[str, str] | None,
    overwrite: bool,
) -> None:
    if dst_path.exists() and not overwrite:
        return

    if src_path is not None and src_path.exists():
        if dst_path.exists():
            dst_path.unlink()
        shutil.copyfile(src_path, dst_path)
        return

    if template_path is not None and template_path.exists():
        template_text = template_path.read_text(encoding="utf-8")
        if template_values:
            template_text = _render_template(template_text, values=template_values)
        _safe_write(dst_path, template_text, overwrite=overwrite)
        return

    session_name = (template_values or {}).get("SESSION_NAME", "")
    a_test_id = (template_values or {}).get("A_TEST_ID", "")
    extra = f"\n**关联A轮测试ID**: {a_test_id}\n" if a_test_id else "\n"
    _safe_write(
        dst_path,
        "# 轻量测试计划（TEST_PLAN）\n\n"
        f"**测试会话**: {session_name}\n"
        + extra
        + "\n（未找到可复制的计划文档或模板，请手动补全）\n",
        overwrite=overwrite,
    )


def _normalize_kind(kind: str) -> str:
    kind = kind.strip().lower()
    if kind in {"a", "a_round", "a-round"}:
        return "a"
    if kind in {"b", "b_round", "b-round"}:
        return "b"
    raise ValueError("kind must be 'a' or 'b'")


def _fail(parser: argparse.ArgumentParser, message: str) -> typing.NoReturn:
    parser.print_usage(sys.stderr)
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an awesome-code test session skeleton (A round or B round).",
    )
    parser.add_argument(
        "--skill-root",
        required=True,
        help="Target Skill root directory (must contain SKILL.md).",
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
        "--a-test-id",
        default="",
        help="For B round only: the associated A round test id (vYYYYMMDDHHMM).",
    )
    parser.add_argument(
        "--create-plan",
        action="store_true",
        help="Create missing plan doc skeleton under plans/ (optional).",
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

    skill_root = Path(args.skill_root).expanduser().resolve()
    if not skill_root.exists() or not skill_root.is_dir():
        _fail(parser, f"--skill-root does not exist or is not a directory: {skill_root}")
    if not (skill_root / "SKILL.md").exists():
        _fail(parser, f"--skill-root is not a Skill directory (missing SKILL.md): {skill_root}")

    try:
        kind = _normalize_kind(args.kind)
    except ValueError as exc:
        _fail(parser, str(exc))
    now = dt.datetime.now()
    test_id = _validate_test_id(parser, args.id.strip() or _generate_test_id(now))
    a_test_id = args.a_test_id.strip()
    if kind == "b":
        if not a_test_id:
            _fail(parser, "--a-test-id is required for B round")
        a_test_id = _validate_test_id(parser, a_test_id)
    else:
        a_test_id = ""

    config = load_skill_config(skill_root)
    plans_dir_name = get_nested(config, "ab_test_optimization", "plans_dir", default="plans")
    tests_dir_name = get_nested(config, "ab_test_optimization", "tests_dir", default="tests")

    plans_rel = _validate_rel_dir(parser, plans_dir_name, "plans_dir")
    tests_rel = _validate_rel_dir(parser, tests_dir_name, "tests_dir")

    plans_dir = skill_root / plans_rel
    tests_dir = skill_root / tests_rel
    templates_dir = skill_root / "templates"

    _ensure_within_root(parser, skill_root, plans_dir, "plans dir")
    _ensure_within_root(parser, skill_root, tests_dir, "tests dir")

    _ensure_dir(plans_dir)
    _ensure_dir(tests_dir)

    template_values = {
        "TEST_ID": test_id,
        "A_TEST_ID": a_test_id,
        "TARGET_SKILL_NAME": skill_root.name,
        "TARGET_SKILL_ROOT": str(skill_root),
        "PLAN_TIME": now.isoformat(timespec="minutes"),
        "CHECK_TIME": now.isoformat(timespec="minutes"),
        "PLAN_DATE": now.date().isoformat(),
    }

    if kind == "a":
        session_name = test_id
        test_plan_template = templates_dir / "TEST_PLAN_TEMPLATE.md"
        plan_doc_path = plans_dir / f"{test_id}.md"
        plan_template = templates_dir / "OPTIMIZATION_PLAN_TEMPLATE.md"
        round_kind = "A轮"
    else:
        session_name = f"B轮-{test_id}"
        test_plan_template = templates_dir / "TEST_PLAN_TEMPLATE.md"
        plan_doc_path = plans_dir / f"B轮-{test_id}.md"
        plan_template = templates_dir / "B_ROUND_CHECK_TEMPLATE.md"
        round_kind = "B轮"

    template_values["ROUND_KIND"] = round_kind
    template_values["SESSION_NAME"] = session_name
    # Security: prevent path traversal even if config/inputs change in the future.
    _ensure_within_root(parser, skill_root, plan_doc_path, "plan doc path")
    template_values["PLAN_DOC_PATH"] = str(plan_doc_path.relative_to(skill_root))

    if args.create_plan and (not plan_doc_path.exists() or args.overwrite):
        if plan_template.exists():
            _safe_write(
                plan_doc_path,
                _render_template(plan_template.read_text(encoding="utf-8"), values=template_values),
                overwrite=args.overwrite,
            )
        else:
            a_hint = f"\n\n**关联A轮测试ID**: {a_test_id}\n" if a_test_id else "\n"
            _safe_write(
                plan_doc_path,
                f"# 计划文档（{session_name}）\n"
                + a_hint
                + "\n（未找到模板，请手动补全）\n",
                overwrite=args.overwrite,
            )

    session_dir = tests_dir / session_name
    _ensure_within_root(parser, skill_root, session_dir, "session dir")
    _ensure_dir(session_dir)
    _ensure_dir(session_dir / "_artifacts")
    _ensure_dir(session_dir / "_scripts")

    _copy_or_template(
        dst_path=session_dir / "TEST_PLAN.md",
        src_path=plan_doc_path if (args.seed_test_plan_from_plan and plan_doc_path.exists()) else None,
        template_path=test_plan_template if test_plan_template.exists() else None,
        template_values=template_values,
        overwrite=args.overwrite,
    )

    report_path = session_dir / "TEST_REPORT.md"
    test_report_template = templates_dir / "TEST_REPORT_TEMPLATE.md"
    if not report_path.exists() or args.overwrite:
        if test_report_template.exists():
            _safe_write(
                report_path,
                _render_template(test_report_template.read_text(encoding="utf-8"), values=template_values),
                overwrite=args.overwrite,
            )
        else:
            a_hint = f"\n**关联A轮测试ID**: {a_test_id}\n\n" if a_test_id else "\n"
            _safe_write(
                report_path,
                "# 测试报告（TEST_REPORT）\n\n"
                f"**测试会话**: {session_name}\n\n"
                + a_hint
                + "## 结果\n\n"
                "- 状态：✅ 通过 / ❌ 失败 / ⚠️ 部分通过\n\n"
                "## 证据\n\n"
                "- （填入命令输出、文件路径、对比结果等）\n",
                overwrite=args.overwrite,
            )

    print(str(session_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
