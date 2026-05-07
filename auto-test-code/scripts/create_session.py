#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
import typing
from pathlib import Path

_TEST_ID_RE = re.compile(r"^v\d{12}$")
_RUN_ID_RE = re.compile(r"^run_\d{14}$")

_DEFAULT_DIRECTORIES = {
    "tmp": "tmp",
    "tests": "tests",
}

_DEFAULT_TEMPLATES = {
    "code_review": "templates/CODE_REVIEW_TEMPLATE.md",
    "b_round_quality": "templates/B_ROUND_CODE_QUALITY_TEMPLATE.md",
    "session_test_plan": "templates/SESSION_TEST_PLAN_TEMPLATE.md",
    "session_test_run": "templates/SESSION_TEST_RUN_TEMPLATE.md",
    "session_test_report": "templates/SESSION_TEST_REPORT_TEMPLATE.md",
}


def _generate_test_id(now: dt.datetime) -> str:
    return f"v{now:%Y%m%d%H%M}"


def _generate_run_id(now: dt.datetime) -> str:
    return f"run_{now:%Y%m%d%H%M%S}"


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
    if "#" not in value:
        return value
    return value.split("#", 1)[0].rstrip()


def _parse_simple_yaml_sections(text: str, *, wanted_sections: set[str]) -> dict[str, dict[str, str]]:
    """
    Parse a minimal subset of YAML for auto-test-code.
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
    if not value:
        return default
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        return default
    return value


def _resolve_template_path(
    *,
    target_code_root: Path,
    bundled_skill_root: Path,
    rel_path: str,
) -> Path | None:
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

    return _candidate_within(target_code_root) or _candidate_within(bundled_skill_root)


def _ensure_dir_within_root(
    parser: argparse.ArgumentParser,
    *,
    code_root: Path,
    path: Path,
    label: str,
) -> None:
    if path.exists():
        if path.is_symlink():
            _fail(parser, f"{label} must not be a symlink: {path}")
        if not path.is_dir():
            _fail(parser, f"{label} must be a directory: {path}")

    _ensure_dir(path)
    resolved = path.resolve()
    try:
        resolved.relative_to(code_root)
    except ValueError:
        _fail(parser, f"{label} resolves outside allowed root: {path} -> {resolved}")


def _write_run_manifest(
    *,
    run_dir: Path,
    code_root: Path,
    tmp_dir: Path,
    tests_dir: Path,
    run_id: str,
    now: dt.datetime,
    overwrite: bool,
) -> None:
    manifest_path = run_dir / ".auto-test-code-run.json"
    if manifest_path.exists() and not overwrite:
        return

    manifest = {
        "run_id": run_id,
        "created_at": now.isoformat(timespec="seconds"),
        "code_root": code_root.as_posix(),
        "tmp_dir_rel": tmp_dir.relative_to(code_root).as_posix(),
        "run_dir_rel": run_dir.relative_to(code_root).as_posix(),
        "tests_dir_rel": tests_dir.relative_to(code_root).as_posix(),
    }
    _safe_write(
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        overwrite=overwrite,
    )


def _detect_code_language(code_root: Path) -> str:
    """检测代码语言（基于常见文件扩展名）"""
    ignored_parts = {
        ".git",
        "tmp",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        "dist",
        "build",
    }
    lang_counts: dict[str, int] = {
        "Python": 0,
        "JavaScript": 0,
        "TypeScript": 0,
        "Java": 0,
        "Go": 0,
        "Rust": 0,
        "C/C++": 0,
    }

    for ext in code_root.rglob("*"):
        if any(part in ignored_parts for part in ext.relative_to(code_root).parts):
            continue
        if ext.is_file():
            suffix = ext.suffix.lower()
            if suffix == ".py":
                lang_counts["Python"] += 1
            elif suffix in {".js", ".jsx"}:
                lang_counts["JavaScript"] += 1
            elif suffix in {".ts", ".tsx"}:
                lang_counts["TypeScript"] += 1
            elif suffix == ".java":
                lang_counts["Java"] += 1
            elif suffix == ".go":
                lang_counts["Go"] += 1
            elif suffix == ".rs":
                lang_counts["Rust"] += 1
            elif suffix in {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"}:
                lang_counts["C/C++"] += 1

    # 返回文件数最多的语言
    max_lang = max(lang_counts, key=lang_counts.get)
    return max_lang if lang_counts[max_lang] > 0 else "Unknown"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an auto-test-code session skeleton under tmp/run_*/tests/ (A round or B round).",
    )
    parser.add_argument(
        "--code-root",
        required=True,
        help="Target code root directory.",
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
        "--run-id",
        default="",
        help="Run workspace id like run_YYYYMMDDHHMMSS. Reuse the same id across A/B rounds in one skill execution.",
    )
    parser.add_argument(
        "--create-review",
        action="store_true",
        help="(Deprecated flag) Create REVIEW.md skeleton in the session directory (default: create if missing).",
    )
    parser.add_argument(
        "--seed-test-plan-from-review",
        action="store_true",
        help="Copy REVIEW.md into TEST_PLAN.md (advanced).",
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

    code_root = Path(args.code_root).expanduser().resolve()
    if not code_root.exists() or not code_root.is_dir():
        _fail(parser, f"--code-root does not exist or is not a directory: {code_root}")

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
    run_id = args.run_id.strip() or _generate_run_id(now)
    if not _RUN_ID_RE.fullmatch(run_id):
        _fail(
            parser,
            "run id must match run_YYYYMMDDHHMMSS, e.g. run_20260310153045 (omit --run-id to auto-generate).",
        )

    # 尝试从代码根目录的 auto-test-code 配置读取，否则使用内置配置
    bundled_skill_root = Path(__file__).resolve().parent.parent
    local_cfg_path = code_root / ".auto-test-code" / "config.yaml"
    target_cfg = _load_config_sections(local_cfg_path) if local_cfg_path.exists() else {}
    bundled_cfg = _load_config_sections(bundled_skill_root / "config.yaml")

    directories = _merge_section(
        base=_DEFAULT_DIRECTORIES,
        override=target_cfg.get("directories") or bundled_cfg.get("directories"),
    )
    templates = _merge_section(
        base=_DEFAULT_TEMPLATES,
        override=target_cfg.get("templates") or bundled_cfg.get("templates"),
    )
    target_template_keys = set((target_cfg.get("templates") or {}).keys())

    tmp_dir = code_root / _safe_rel_path(directories.get("tmp", ""), default=_DEFAULT_DIRECTORIES["tmp"])
    run_dir = tmp_dir / run_id
    tests_dir = run_dir / _safe_rel_path(directories.get("tests", ""), default=_DEFAULT_DIRECTORIES["tests"])

    def template_path(config_key: str) -> Path | None:
        rel = _safe_rel_path(templates.get(config_key, ""), default="")
        if not rel:
            return None
        return _resolve_template_path(
            target_code_root=code_root,
            bundled_skill_root=bundled_skill_root,
            rel_path=rel,
        )

    def template_path_any(*keys: str) -> Path | None:
        """
        Prefer new config keys, but keep backward compatibility with older
        `.auto-test-code/config.yaml` that used `test_plan/test_run/test_report`.
        """
        for k in keys:
            p = template_path(k)
            if p is not None:
                return p
        return None

    def template_path_prefer(*, new_keys: tuple[str, ...], old_keys: tuple[str, ...]) -> Path | None:
        """
        Prefer the key family that was explicitly configured in the *project-local*
        `.auto-test-code/config.yaml` (if present). Otherwise, default to `new_keys`.
        """
        if any(k in target_template_keys for k in new_keys):
            return template_path_any(*new_keys, *old_keys)
        if any(k in target_template_keys for k in old_keys):
            return template_path_any(*old_keys, *new_keys)
        return template_path_any(*new_keys, *old_keys)

    _ensure_dir_within_root(parser, code_root=code_root, path=tmp_dir, label="tmp directory")
    _ensure_dir_within_root(parser, code_root=code_root, path=run_dir, label="run directory")
    _ensure_dir_within_root(parser, code_root=run_dir, path=tests_dir, label="tests directory")
    _write_run_manifest(
        run_dir=run_dir,
        code_root=code_root,
        tmp_dir=tmp_dir,
        tests_dir=tests_dir,
        run_id=run_id,
        now=now,
        overwrite=args.overwrite,
    )

    # 检测代码语言
    code_language = _detect_code_language(code_root)

    template_values: dict[str, str] = {
        "TEST_ID": test_id,
        "RUN_ID": run_id,
        "TARGET_CODE_ROOT": code_root.as_posix(),
        "CODE_LANGUAGE": code_language,
        "PLAN_TIME": now.isoformat(timespec="minutes"),
        "CHECK_TIME": now.isoformat(timespec="minutes"),
        "REPORT_TIME": now.isoformat(timespec="minutes"),
        "PLAN_DATE": now.date().isoformat(),
        # 默认值
        "FOCUS_DIMENSIONS": "（待填写）",
        "TRICKY_ANGLE": "（待填写）",
        "FIX_1": "（待填写）",
        "FIX_2": "（待填写）",
        "FIX_3": "（待填写）",
        "P0_COUNT": "0",
        "P1_COUNT": "0",
        "P2_COUNT": "0",
        "P0_RATIO": "0",
        "P1_RATIO": "0",
        "P2_RATIO": "0",
        "TOTAL_COUNT": "0",
        "SYSTEMIC_COUNT": "0",
        "SECURITY_COUNT": "0",
    }

    if kind == "a":
        session_name = test_id
        test_plan_template = template_path_prefer(new_keys=("session_test_plan",), old_keys=("test_plan",))
        review_template = template_path("code_review")
        round_kind = "A轮代码审查"
    else:
        session_name = f"b-{test_id}"
        test_plan_template = template_path_prefer(new_keys=("session_test_plan",), old_keys=("test_plan",))
        review_template = template_path("b_round_quality")
        round_kind = "B轮代码质量检查"

    template_values["ROUND_KIND"] = round_kind
    template_values["TMP_DIR_REL"] = tmp_dir.relative_to(code_root).as_posix()
    template_values["RUN_DIR_REL"] = run_dir.relative_to(code_root).as_posix()
    template_values["SESSION_NAME"] = session_name

    session_dir_rel = (tests_dir / session_name).relative_to(code_root).as_posix()
    template_values["SESSION_DIR_REL"] = session_dir_rel
    template_values["REVIEW_DOC_PATH"] = f"{session_dir_rel}/REVIEW.md"
    template_values["TEST_PLAN_REL"] = f"{session_dir_rel}/TEST_PLAN.md"
    template_values["TEST_RUN_REL"] = f"{session_dir_rel}/TEST_RUN.md"
    template_values["TEST_REPORT_REL"] = f"{session_dir_rel}/TEST_REPORT.md"

    if kind == "b":
        a_test_id = args.a_test_id.strip() or test_id
        if not _TEST_ID_RE.fullmatch(a_test_id):
            _fail(parser, "--a-test-id must match vYYYYMMDDHHMM (e.g. v202601010000)")
        template_values["A_TEST_ID"] = a_test_id

    session_dir = tests_dir / session_name
    _ensure_dir_within_root(parser, code_root=code_root, path=session_dir, label="session directory")
    _ensure_dir(session_dir / "_artifacts")
    _ensure_dir(session_dir / "_scripts")

    # REVIEW.md（A轮批判性审查 / B轮质量检查）统一放在会话目录内
    review_doc_path = session_dir / "REVIEW.md"
    if (not review_doc_path.exists()) or args.overwrite or args.create_review:
        if review_template is not None:
            _safe_write(
                review_doc_path,
                _render_template(review_template.read_text(encoding="utf-8"), values=template_values),
                overwrite=args.overwrite,
            )
        else:
            _safe_write(
                review_doc_path,
                f"# {round_kind}\n\n（未找到模板，请手动补全）\n",
                overwrite=args.overwrite,
            )

    _copy_or_template(
        dst_path=session_dir / "TEST_PLAN.md",
        src_path=review_doc_path if (args.seed_test_plan_from_review and review_doc_path.exists()) else None,
        template_path=test_plan_template,
        template_values=template_values,
        overwrite=args.overwrite,
    )

    test_run_path = session_dir / "TEST_RUN.md"
    test_run_template = template_path_prefer(new_keys=("session_test_run",), old_keys=("test_run",))
    if not test_run_path.exists() or args.overwrite:
        if test_run_template is not None:
            _safe_write(
                test_run_path,
                _render_template(test_run_template.read_text(encoding="utf-8"), values=template_values),
                overwrite=args.overwrite,
            )
        else:
            _safe_write(
                test_run_path,
                "# 测试过程记录\n\n（建议记录：命令、关键输出摘录、关键决策与证据路径）\n",
                overwrite=args.overwrite,
            )

    report_path = session_dir / "TEST_REPORT.md"
    test_report_template = template_path_prefer(new_keys=("session_test_report",), old_keys=("test_report",))
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
                "# 测试报告\n\n"
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
