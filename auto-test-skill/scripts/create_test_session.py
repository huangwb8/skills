#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
import typing
from pathlib import Path

_TEST_ID_RE = re.compile(r"^v\d{12}$")

_DEFAULT_DIRECTORIES = {
    "plans": "plans",
    "tests": "tests",
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

    _safe_write(
        dst_path,
        "# TEST_PLAN\n\n（未找到可复制的计划文档或模板，请手动补全）\n",
        overwrite=overwrite,
    )


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
    # Best-effort: config.yaml in this repo uses simple scalar strings for
    # directories/templates; we only need those sections and should not require
    # non-stdlib dependencies.
    if "#" not in value:
        return value
    return value.split("#", 1)[0].rstrip()


def _parse_simple_yaml_sections(text: str, *, wanted_sections: set[str]) -> dict[str, dict[str, str]]:
    """
    Parse a minimal subset of YAML:
    - top-level mapping keys (no indentation)
    - one level nested key/value pairs under a wanted section (2+ spaces)
    This is used as a fallback when PyYAML isn't available.
    """
    result: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        # Section header: "directories:" / "templates:"
        if not line.startswith(" ") and line.endswith(":"):
            section = line[:-1].strip()
            current = section if section in wanted_sections else None
            continue

        if current is None:
            continue

        # Section entry: "  key: value"
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


def _merge_section(
    *,
    base: dict[str, str],
    override: dict[str, str] | None,
) -> dict[str, str]:
    merged = dict(base)
    if override:
        merged.update({k: v for k, v in override.items() if v})
    return merged


def _safe_rel_path(value: str, *, default: str) -> str:
    """
    Prevent writing outside the target skill root when reading config-provided
    directories/templates.
    """
    if not value:
        return default
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        return default
    return value


def _resolve_template_path(
    *,
    target_skill_root: Path,
    bundled_skill_root: Path,
    rel_path: str,
) -> Path | None:
    # Prefer target skill templates, then fall back to auto-test-skill bundled templates.
    #
    # Safety: if the template path is a symlink that resolves outside the expected
    # root, ignore it (prevents accidental/hostile template substitution).
    def _candidate_within(root: Path) -> Path | None:
        candidate = root / rel_path
        if not candidate.exists():
            return None
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            return None
        return resolved

    return _candidate_within(target_skill_root) or _candidate_within(bundled_skill_root)


def _ensure_dir_within_root(
    parser: argparse.ArgumentParser,
    *,
    skill_root: Path,
    path: Path,
    label: str,
) -> None:
    """
    Ensure we only create/write under --skill-root, even when directories are configured.
    """
    if path.exists():
        if path.is_symlink():
            _fail(parser, f"{label} must not be a symlink: {path}")
        if not path.is_dir():
            _fail(parser, f"{label} must be a directory: {path}")

    _ensure_dir(path)
    resolved = path.resolve()
    try:
        resolved.relative_to(skill_root)
    except ValueError:
        _fail(parser, f"{label} resolves outside --skill-root: {path} -> {resolved}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an auto-test-skill test session skeleton (A round or B round).",
    )
    parser.add_argument(
        "--skill-root",
        required=True,
        help="Target Skill root directory (must contain SKILL.md).",
    )
    parser.add_argument(
        "--kind",
        default="a",
        help="Session kind: a (default) or b (also accepts: A轮/B轮).",
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
        "--seed-test-plan-from-plan",
        action="store_true",
        help="Copy the plan doc into TEST_PLAN.md (advanced; usually you should edit the template instead).",
    )
    parser.add_argument(
        "--a-test-id",
        default="",
        help="For B round: the corresponding A-round id (defaults to --id).",
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
    test_id = args.id.strip() or _generate_test_id(now)
    if not _TEST_ID_RE.fullmatch(test_id):
        _fail(
            parser,
            "test id must match vYYYYMMDDHHMM, e.g. v202601010000 (omit --id to auto-generate).",
        )

    bundled_skill_root = Path(__file__).resolve().parent.parent
    # Read config from target skill first (if it provides directories/templates),
    # otherwise fall back to auto-test-skill's own config.yaml.
    target_cfg = _load_config_sections(skill_root / "config.yaml")
    bundled_cfg = _load_config_sections(bundled_skill_root / "config.yaml")
    directories = _merge_section(
        base=_DEFAULT_DIRECTORIES,
        override=target_cfg.get("directories") or bundled_cfg.get("directories"),
    )
    templates = _merge_section(
        base=_DEFAULT_TEMPLATES,
        override=target_cfg.get("templates") or bundled_cfg.get("templates"),
    )

    plans_dir = skill_root / _safe_rel_path(directories.get("plans", ""), default=_DEFAULT_DIRECTORIES["plans"])
    tests_dir = skill_root / _safe_rel_path(directories.get("tests", ""), default=_DEFAULT_DIRECTORIES["tests"])

    def template_path(config_key: str) -> Path | None:
        rel = _safe_rel_path(templates.get(config_key, ""), default="")
        if not rel:
            return None
        return _resolve_template_path(
            target_skill_root=skill_root,
            bundled_skill_root=bundled_skill_root,
            rel_path=rel,
        )

    _ensure_dir_within_root(parser, skill_root=skill_root, path=plans_dir, label="plans directory")
    _ensure_dir_within_root(parser, skill_root=skill_root, path=tests_dir, label="tests directory")

    template_values: dict[str, str] = {
        "TEST_ID": test_id,
        "TARGET_SKILL_NAME": skill_root.name,
        # Display paths in docs with forward slashes for cross-platform consistency.
        "TARGET_SKILL_ROOT": skill_root.as_posix(),
        "PLAN_TIME": now.isoformat(timespec="minutes"),
        "CHECK_TIME": now.isoformat(timespec="minutes"),
        "PLAN_DATE": now.date().isoformat(),
        # Provide sensible defaults for common placeholders so skeleton docs are usable
        # without leaving raw `{{...}}` everywhere.
        "CHANGED_FILE_1": "（待填写）",
        "CHANGED_FILE_2": "（待填写）",
        "BEHAVIOR_CHANGE_1": "（待填写）",
        "BEHAVIOR_CHANGE_2": "（待填写）",
        "P0_CHECK_1": "（待填写）",
        "P0_CHECK_2": "（待填写）",
        "P1_CHECK_1": "（待填写）",
        "P1_CHECK_2": "（待填写）",
        "P2_CHECK_1": "（待填写）",
    }

    if kind == "a":
        session_name = test_id
        test_plan_template = template_path("test_plan")
        plan_doc_path = plans_dir / f"{test_id}.md"
        plan_template = template_path("optimization_plan")
        round_kind = "A轮"
    else:
        session_name = f"B轮-{test_id}"
        test_plan_template = template_path("test_plan")
        plan_doc_path = plans_dir / f"B轮-{test_id}.md"
        plan_template = template_path("b_round_check")
        round_kind = "B轮"

    template_values["ROUND_KIND"] = round_kind
    template_values["SESSION_NAME"] = session_name
    template_values["PLAN_DOC_PATH"] = plan_doc_path.relative_to(skill_root).as_posix()

    # Provide session-relative paths to avoid hardcoding "tests/" in templates.
    session_dir_rel = (tests_dir / session_name).relative_to(skill_root).as_posix()
    template_values["SESSION_DIR_REL"] = session_dir_rel
    template_values["TEST_PLAN_REL"] = f"{session_dir_rel}/TEST_PLAN.md"
    template_values["TEST_REPORT_REL"] = f"{session_dir_rel}/TEST_REPORT.md"

    if kind == "b":
        a_test_id = args.a_test_id.strip() or test_id
        if not _TEST_ID_RE.fullmatch(a_test_id):
            _fail(parser, "--a-test-id must match vYYYYMMDDHHMM (e.g. v202601010000)")
        template_values["A_TEST_ID"] = a_test_id

    if args.create_plan and (not plan_doc_path.exists() or args.overwrite):
        if plan_template is not None:
            _safe_write(
                plan_doc_path,
                _render_template(plan_template.read_text(encoding="utf-8"), values=template_values),
                overwrite=args.overwrite,
            )
        else:
            _safe_write(
                plan_doc_path,
                f"# 计划文档（{session_name}）\n\n（未找到模板，请手动补全）\n",
                overwrite=args.overwrite,
            )

    session_dir = tests_dir / session_name
    _ensure_dir_within_root(parser, skill_root=skill_root, path=session_dir, label="session directory")
    _ensure_dir(session_dir / "_artifacts")
    _ensure_dir(session_dir / "_scripts")

    _copy_or_template(
        dst_path=session_dir / "TEST_PLAN.md",
        src_path=plan_doc_path if (args.seed_test_plan_from_plan and plan_doc_path.exists()) else None,
        template_path=test_plan_template,
        template_values=template_values,
        overwrite=args.overwrite,
    )

    report_path = session_dir / "TEST_REPORT.md"
    test_report_template = template_path("test_report")
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
                f"**测试会话**: {session_name}\n\n"
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
