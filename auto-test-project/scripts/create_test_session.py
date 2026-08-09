#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
import typing
from pathlib import Path

from workspace_paths import resolve_workspace

_TEST_ID_RE = re.compile(r"^v\d{12}$")

_DEFAULT_DIRECTORIES = {
    "plans": "output/plans",
    "tests": "output/tests",
}

_DEFAULT_TEMPLATES = {
    "optimization_plan": "templates/OPTIMIZATION_PLAN_TEMPLATE.md",
    "b_round_check": "templates/B_ROUND_CHECK_TEMPLATE.md",
    "test_plan": "templates/TEST_PLAN_TEMPLATE.md",
    "test_report": "templates/TEST_REPORT_TEMPLATE.md",
}


def _generate_test_id(now: dt.datetime) -> str:
    return f"v{now:%Y%m%d%H%M}"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _safe_write(path: Path, content: str, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content, encoding="utf-8")


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

    _safe_write(dst_path, "# TEST_PLAN\n\n（未找到可复制的计划文档或模板，请手动补全）\n", overwrite=overwrite)


def _normalize_kind(kind: str) -> str:
    kind = kind.strip().lower()
    if kind in {"a", "a_round", "a-round", "a轮"}:
        return "a"
    if kind in {"b", "b_round", "b-round", "b轮"}:
        return "b"
    raise ValueError("kind must be a/b (also accepts: A轮/B轮)")


def _fail(parser: argparse.ArgumentParser, message: str) -> typing.NoReturn:
    parser.print_usage(sys.stderr)
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def _strip_inline_comment(value: str) -> str:
    if "#" not in value:
        return value
    return value.split("#", 1)[0].rstrip()


def _parse_simple_yaml_sections(text: str, *, wanted_sections: set[str]) -> dict[str, dict[str, str]]:
    """
    Parse a minimal subset of YAML:
    - top-level mapping keys (no indentation)
    - one level nested key/value pairs under a wanted section (2+ spaces)
    """
    result: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        if not line.startswith(" ") and line.endswith(":"):
            section = line[:-1].strip()
            current = section if section in wanted_sections else None
            continue

        if current is None:
            continue

        if line.startswith("  ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = _strip_inline_comment(value.strip())
            if not value:
                continue
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            result.setdefault(current, {})[key] = value

    return result


def _load_config_sections(config_path: Path) -> dict[str, dict[str, str]]:
    wanted = {"directories", "templates"}
    if not config_path.exists():
        return {}

    text = config_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except Exception:
        return _parse_simple_yaml_sections(text, wanted_sections=wanted)

    try:
        data = yaml.safe_load(text) or {}
    except Exception:
        return _parse_simple_yaml_sections(text, wanted_sections=wanted)

    out: dict[str, dict[str, str]] = {}
    for section in wanted:
        v = data.get(section)
        if isinstance(v, dict):
            out[section] = {str(k): str(vv) for k, vv in v.items() if isinstance(vv, (str, int, float))}
    return out


def _merge_section(*, base: dict[str, str], override: dict[str, str] | None) -> dict[str, str]:
    merged = dict(base)
    if override:
        merged.update({k: v for k, v in override.items() if v})
    return merged


def _safe_rel_path(value: str, *, default: str) -> str:
    if not value:
        return default
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        return default
    return value


def _resolve_template_path(*, skill_root: Path, rel_path: str) -> Path | None:
    # Safety: refuse templates that resolve outside skill root (symlink escape).
    candidate = skill_root / rel_path
    if not candidate.exists():
        return None
    resolved = candidate.resolve()
    try:
        resolved.relative_to(skill_root)
    except ValueError:
        return None
    return resolved


def _ensure_dir_within_root(
    parser: argparse.ArgumentParser,
    *,
    root: Path,
    path: Path,
    label: str,
) -> None:
    """
    Ensure we only create/write under --project-root; reject symlinks for safety.
    """
    if path.exists():
        if path.is_symlink():
            _fail(parser, f"{label} must not be a symlink: {path}")
        if not path.is_dir():
            _fail(parser, f"{label} must be a directory: {path}")

    _ensure_dir(path)
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        _fail(parser, f"{label} resolves outside --project-root: {path} -> {resolved}")


def _validate_project_root(project_root: Path) -> None:
    if not project_root.exists() or not project_root.is_dir():
        raise FileNotFoundError(f"Project root does not exist or is not a directory: {project_root}")

    instruction_files = ["CLAUDE.md", "AGENTS.md", "PROJECT.md", "README.md"]
    has_instruction = any((project_root / f).exists() for f in instruction_files)
    if not has_instruction:
        print(f"warning: no project instruction file found in {project_root}", file=sys.stderr)
        print(f"expected one of: {', '.join(instruction_files)}", file=sys.stderr)


def _detect_project_type(project_root: Path) -> str:
    """
    Minimal heuristic used only for template filling.
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
        help="Session kind: a (default) or b (also accepts: A轮/B轮).",
    )
    parser.add_argument(
        "--task-root",
        default="",
        help=(
            "Existing task root to reuse, relative to --project-root or absolute. "
            "It must be a direct .bensz-api/task-YYYYMMDD-HHMM-<description> child."
        ),
    )
    parser.add_argument(
        "--task-description",
        default="auto-test-project",
        help="Description slug used only when allocating a new task root (default: auto-test-project).",
    )
    parser.add_argument(
        "--id",
        default="",
        help="Explicit test id like vYYYYMMDDHHMM (optional).",
    )
    parser.add_argument(
        "--a-test-id",
        default="",
        help="For B round: the corresponding A-round id (optional; defaults to --id).",
    )
    parser.add_argument(
        "--create-plan",
        action="store_true",
        help="Create missing plan doc skeleton under configured plans dir (optional).",
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

    explicit_id = args.id.strip()
    if explicit_id and not _TEST_ID_RE.fullmatch(explicit_id):
        _fail(parser, "--id must match vYYYYMMDDHHMM (e.g. v202601151230)")

    try:
        kind = _normalize_kind(args.kind)
    except ValueError as exc:
        _fail(parser, str(exc))

    now = dt.datetime.now()
    test_id = explicit_id or _generate_test_id(now)
    if not _TEST_ID_RE.fullmatch(test_id):
        _fail(parser, "test id must match vYYYYMMDDHHMM (omit --id to auto-generate)")

    if kind == "a":
        session_name = test_id
        round_kind = "A轮"
        plan_rel = f"{test_id}.md"
        plan_template_key = "optimization_plan"
        a_test_id = test_id
    else:
        session_name = f"B轮-{test_id}"
        round_kind = "B轮"
        plan_rel = f"B轮-{test_id}.md"
        plan_template_key = "b_round_check"
        a_test_id = args.a_test_id.strip() or test_id
        if not _TEST_ID_RE.fullmatch(a_test_id):
            _fail(parser, "--a-test-id must match vYYYYMMDDHHMM (e.g. v202601151230)")

    project_root = Path(args.project_root).expanduser().resolve()

    # Safety guard: prevent accidental pollution of extremely broad directories.
    anchor_root = Path(project_root.anchor) if project_root.anchor else project_root
    is_fs_root = project_root == anchor_root
    is_home = project_root == Path.home().resolve()
    if (is_fs_root or is_home) and not args.allow_unsafe_root:
        _fail(parser, f"Refusing unsafe --project-root: {project_root} (use --allow-unsafe-root to override)")

    skill_source_root = Path(__file__).resolve().parent.parent
    cfg = _load_config_sections(skill_source_root / "config.yaml")
    directories = _merge_section(base=_DEFAULT_DIRECTORIES, override=cfg.get("directories"))
    templates = _merge_section(base=_DEFAULT_TEMPLATES, override=cfg.get("templates"))

    def template_path(config_key: str) -> Path | None:
        rel = _safe_rel_path(templates.get(config_key, ""), default=_DEFAULT_TEMPLATES.get(config_key, ""))
        if not rel:
            return None
        return _resolve_template_path(skill_root=skill_source_root, rel_path=rel)

    try:
        plan_template = template_path(plan_template_key)
        test_plan_template = template_path("test_plan")
        test_report_template = template_path("test_report")
    except (FileNotFoundError, ValueError) as exc:
        _fail(parser, str(exc))

    try:
        _validate_project_root(project_root)
    except FileNotFoundError as exc:
        _fail(parser, str(exc))

    try:
        workspace = resolve_workspace(
            project_root=project_root,
            task_root_arg=args.task_root,
            task_description=args.task_description,
            directories=directories,
            create=True,
            now=now,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        _fail(parser, str(exc))

    plans_dir = workspace.plans_dir
    tests_dir = workspace.tests_dir

    plan_src = plans_dir / plan_rel

    project_type = _detect_project_type(project_root)
    template_values: dict[str, str] = {
        "TEST_ID": test_id,
        "PROJECT_NAME": project_root.name,
        "PROJECT_ROOT": str(project_root),
        "TASK_ROOT": workspace.task_root.relative_to(project_root).as_posix(),
        "SKILL_WORKSPACE": workspace.skill_root.relative_to(project_root).as_posix(),
        "SESSION_NAME": session_name,
        "ROUND_KIND": round_kind,
        "TEST_TIME": now.strftime("%Y-%m-%d %H:%M:%S"),
        "TEST_DATE": now.date().isoformat(),
        "PLAN_ID": test_id,
        "PLAN_TIME": now.isoformat(timespec="minutes"),
        "PLAN_DOC_PATH": plan_src.relative_to(project_root).as_posix(),
        "PLAN_FILE": plan_src.relative_to(project_root).as_posix(),
        "PROJECT_TYPE": project_type,
    }

    template_values["A_TEST_ID"] = a_test_id
    template_values["A_ROUND_ID"] = a_test_id

    if args.create_plan and (not plan_src.exists() or args.overwrite):
        if plan_template is not None:
            _safe_write(
                plan_src,
                _render_template(plan_template.read_text(encoding="utf-8"), values=template_values),
                overwrite=args.overwrite,
            )
        else:
            _safe_write(plan_src, f"# 计划文档（{session_name}）\n\n（未找到模板，请手动补全）\n", overwrite=args.overwrite)

    session_dir = tests_dir / session_name
    _ensure_dir_within_root(
        parser, root=workspace.skill_root, path=session_dir, label="session directory"
    )
    _ensure_dir_within_root(
        parser, root=workspace.skill_root, path=session_dir / "_artifacts", label="artifacts directory"
    )
    _ensure_dir_within_root(
        parser, root=workspace.skill_root, path=session_dir / "_scripts", label="scripts directory"
    )

    _copy_or_template(
        dst_path=session_dir / "TEST_PLAN.md",
        src_path=plan_src if (args.seed_test_plan_from_plan and plan_src.exists()) else None,
        template_path=test_plan_template,
        template_values=template_values,
        overwrite=args.overwrite,
    )

    report_path = session_dir / "TEST_REPORT.md"
    if not report_path.exists() or args.overwrite:
        if test_report_template is not None:
            _safe_write(
                report_path,
                _render_template(test_report_template.read_text(encoding="utf-8"), values=template_values),
                overwrite=args.overwrite,
            )
        else:
            _safe_write(
                report_path,
                "# 测试报告（TEST_REPORT）\n\n"
                f"**测试会话**: {session_name}\n"
                f"**项目根目录**: {project_root}\n\n"
                "## 结果\n\n"
                "- 状态：✅ 通过 / ❌ 失败 / ⚠️ 部分通过\n\n"
                "## 证据\n\n"
                "- （填入命令输出、文件路径、对比结果等）\n",
                overwrite=args.overwrite,
            )

    print(str(session_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
