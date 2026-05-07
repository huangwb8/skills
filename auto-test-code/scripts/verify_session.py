#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import typing
from dataclasses import dataclass
from pathlib import Path

_TEST_ID_RE = re.compile(r"^v\d{12}$")
_RUN_ID_RE = re.compile(r"^run_\d{14}$")
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

_DEFAULT_DIRECTORIES = {
    "tmp": "tmp",
    "tests": "tests",
}


@dataclass(frozen=True)
class Issue:
    severity: str  # P0/P1/P2
    message: str


def _fail(message: str) -> typing.NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def _find_code_root(start: Path) -> Path | None:
    """尝试找到代码根目录（优先读取 run manifest；兼容旧版 tests/reviews 布局）"""
    p = start.resolve()
    for _ in range(20):
        manifest_path = p / ".auto-test-code-run.json"
        if manifest_path.exists() and manifest_path.is_file():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                data = None
            if isinstance(data, dict):
                raw = data.get("code_root")
                if isinstance(raw, str) and raw:
                    candidate = Path(raw).expanduser().resolve()
                    if candidate.exists() and candidate.is_dir():
                        return candidate

        if _RUN_ID_RE.fullmatch(p.name) and p.parent != p:
            return p.parent.parent if p.parent.parent != p.parent else None

        if p.parent == p:
            break
        p = p.parent

    p = start
    for _ in range(20):
        if (p / ".auto-test-code" / "config.yaml").exists():
            return p
        if (p / "reviews").exists() or (p / "tests").exists():
            return p
        if p.parent == p:
            return None
        p = p.parent
    return None


def _strip_inline_comment(value: str) -> str:
    if "#" not in value:
        return value
    return value.split("#", 1)[0].rstrip()


def _parse_simple_yaml_sections(text: str, *, wanted_sections: set[str]) -> dict[str, dict[str, str]]:
    """解析最小 YAML 子集"""
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


def _load_directories(config_path: Path) -> dict[str, str]:
    if not config_path.exists():
        return dict(_DEFAULT_DIRECTORIES)
    text = config_path.read_text(encoding="utf-8")
    data = _parse_simple_yaml_sections(text, wanted_sections={"directories"})
    out = data.get("directories") or {}
    merged = dict(_DEFAULT_DIRECTORIES)
    merged.update({str(k): str(v) for k, v in out.items()})
    return merged


def _safe_rel_path(value: str, *, default: str) -> str:
    if not value:
        return default
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        return default
    return value


def _extract_markdown_field(text: str, field_label: str) -> str | None:
    pat = re.compile(rf"^\*\*{re.escape(field_label)}\*\*:\s*(.+?)\s*$", re.MULTILINE)
    m = pat.search(text)
    if not m:
        return None
    return m.group(1).strip()


def _scan_placeholders(text: str) -> list[str]:
    return [m.group(0) for m in _PLACEHOLDER_RE.finditer(text)]


def _check_report_status(text: str) -> tuple[bool, bool]:
    """检查报告状态（是否选择了明确的状态）"""
    for line in text.splitlines():
        if "状态：" in line or "**状态**：" in line:
            return ("/" not in line, True)
    return (False, False)


def _classify_session(session_dir: Path) -> tuple[str, str] | None:
    name = session_dir.name
    if name.startswith("b-"):
        test_id = name.removeprefix("b-")
        if _TEST_ID_RE.fullmatch(test_id):
            return ("b", test_id)
        return None
    if name.startswith("B轮-"):
        test_id = name.removeprefix("B轮-")
        if _TEST_ID_RE.fullmatch(test_id):
            return ("b", test_id)
        return None
    if _TEST_ID_RE.fullmatch(name):
        return ("a", name)
    return None


def _find_run_dir(session_dir: Path) -> Path | None:
    current = session_dir.resolve()
    for candidate in (current, *current.parents):
        if _RUN_ID_RE.fullmatch(candidate.name):
            return candidate
    return None


def verify_session(
    *,
    session_dir: Path,
    code_root: Path,
    require_review: bool,
    strict: bool,
) -> list[Issue]:
    issues: list[Issue] = []

    if not session_dir.exists() or not session_dir.is_dir():
        return [Issue("P0", f"session_dir is not a directory: {session_dir}")]

    # 读取配置
    local_cfg_path = code_root / ".auto-test-code" / "config.yaml"
    directories = _load_directories(local_cfg_path) if local_cfg_path.exists() else {}
    if not directories:
        directories = dict(_DEFAULT_DIRECTORIES)

    tmp_dir = code_root / _safe_rel_path(directories.get("tmp", ""), default=_DEFAULT_DIRECTORIES["tmp"])
    run_dir = _find_run_dir(session_dir)
    if run_dir is not None:
        tests_dir = run_dir / _safe_rel_path(directories.get("tests", ""), default=_DEFAULT_DIRECTORIES["tests"])
        if run_dir.parent.resolve() != tmp_dir.resolve():
            issues.append(Issue("P0", f"run directory is not under configured tmp directory: {run_dir}"))
        try:
            session_dir.resolve().relative_to(tests_dir.resolve())
        except ValueError:
            issues.append(Issue("P0", f"session directory is not inside run tests directory: {session_dir}"))
    else:
        tests_dir = code_root / _safe_rel_path(directories.get("tests", ""), default=_DEFAULT_DIRECTORIES["tests"])
        issues.append(Issue("P1", f"session directory is not under isolated tmp/run_* workspace: {session_dir}"))

    if tests_dir.exists() and tests_dir.is_symlink():
        issues.append(Issue("P1", f"tests directory is a symlink (discouraged): {tests_dir}"))

    kind_info = _classify_session(session_dir)
    if kind_info is None:
        issues.append(Issue("P1", f"unexpected session directory name (expected vYYYYMMDDHHMM or b-vYYYYMMDDHHMM): {session_dir.name}"))
        kind = "unknown"
        test_id = ""
    else:
        kind, test_id = kind_info

    # 检查必需的文件和目录
    required_paths = [
        (session_dir / "REVIEW.md", "REVIEW.md"),
        (session_dir / "TEST_PLAN.md", "TEST_PLAN.md"),
        (session_dir / "TEST_RUN.md", "TEST_RUN.md"),
        (session_dir / "TEST_REPORT.md", "TEST_REPORT.md"),
        (session_dir / "_artifacts", "_artifacts/"),
        (session_dir / "_scripts", "_scripts/"),
    ]
    for p, label in required_paths:
        if not p.exists():
            issues.append(Issue("P0", f"missing required {label}: {p}"))
        elif label.endswith("/") and not p.is_dir():
            issues.append(Issue("P0", f"{label} is not a directory: {p}"))

    review_text = ""
    report_text = ""
    test_plan_text = ""
    test_run_text = ""

    review_path: Path | None = session_dir / "REVIEW.md"
    if require_review:
        if review_path is None or not review_path.exists():
            issues.append(Issue("P0", f"missing REVIEW.md: {session_dir / 'REVIEW.md'}"))
        else:
            review_text = review_path.read_text(encoding="utf-8", errors="replace")

    test_plan_path = session_dir / "TEST_PLAN.md"
    if test_plan_path.exists():
        test_plan_text = test_plan_path.read_text(encoding="utf-8", errors="replace")
        if strict:
            placeholders = _scan_placeholders(test_plan_text)
            if placeholders:
                uniq = sorted(set(placeholders))
                shown = uniq[:8]
                suffix = " (and more)" if len(uniq) > len(shown) else ""
                issues.append(Issue("P0", f"TEST_PLAN.md contains unresolved placeholders: {shown}{suffix}"))

    test_run_path = session_dir / "TEST_RUN.md"
    if test_run_path.exists():
        test_run_text = test_run_path.read_text(encoding="utf-8", errors="replace")
        if strict:
            placeholders = _scan_placeholders(test_run_text)
            if placeholders:
                uniq = sorted(set(placeholders))
                shown = uniq[:8]
                suffix = " (and more)" if len(uniq) > len(shown) else ""
                issues.append(Issue("P0", f"TEST_RUN.md contains unresolved placeholders: {shown}{suffix}"))

    report_path = session_dir / "TEST_REPORT.md"
    if report_path.exists():
        report_text = report_path.read_text(encoding="utf-8", errors="replace")
        if strict:
            placeholders = _scan_placeholders(report_text)
            if placeholders:
                uniq = sorted(set(placeholders))
                shown = uniq[:8]
                suffix = " (and more)" if len(uniq) > len(shown) else ""
                issues.append(Issue("P0", f"TEST_REPORT.md contains unresolved placeholders: {shown}{suffix}"))
            ok, found = _check_report_status(report_text)
            if not found:
                issues.append(Issue("P1", "TEST_REPORT.md is missing a status line ('状态：...')."))
            elif not ok:
                issues.append(Issue("P1", "TEST_REPORT.md status line looks like the template placeholder; set it to a single status."))

    if require_review and review_path is not None and review_text and strict:
        placeholders = _scan_placeholders(review_text)
        if placeholders:
            uniq = sorted(set(placeholders))
            shown = uniq[:8]
            suffix = " (and more)" if len(uniq) > len(shown) else ""
            issues.append(Issue("P0", f"REVIEW.md contains unresolved placeholders: {shown}{suffix}"))

    if require_review:
        # 验证 TEST_PLAN/TEST_REPORT 是否引用了正确的审查文档
        expected_review_resolved = review_path.resolve() if (review_path is not None and review_path.exists()) else None
        for label, text in [("TEST_PLAN.md", test_plan_text), ("TEST_RUN.md", test_run_text), ("TEST_REPORT.md", report_text)]:
            if not text:
                continue
            ref = _extract_markdown_field(text, "对应审查") or _extract_markdown_field(text, "对应A轮审查")
            if ref is None:
                issues.append(Issue("P1", f"{label} missing '**对应审查**: ...' field"))
                continue
            ref_path = Path(ref)
            if ref_path.is_absolute() or ".." in ref_path.parts:
                issues.append(Issue("P0", f"{label} has unsafe review path: {ref}"))
                continue
            abs_ref = (code_root / ref_path).resolve()
            try:
                abs_ref.relative_to(code_root)
            except ValueError:
                issues.append(Issue("P0", f"{label} review path resolves outside code_root: {ref} -> {abs_ref}"))
                continue
            if not abs_ref.exists():
                issues.append(Issue("P0", f"{label} references missing review doc: {ref}"))
                continue
            if expected_review_resolved is not None and abs_ref != expected_review_resolved:
                issues.append(Issue("P1", f"{label} references a different review doc than expected by session id: {ref}"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an auto-test-code session directory for completeness.")
    parser.add_argument(
        "session_dir",
        help="Session directory path (e.g. tmp/run_YYYYMMDDHHMMSS/tests/vYYYYMMDDHHMM).",
    )
    parser.add_argument(
        "--code-root",
        default="",
        help="Explicit code root. If omitted, auto-detect by walking up from session_dir.",
    )
    parser.add_argument(
        "--require-review",
        action="store_true",
        help="Require REVIEW.md to exist and be consistent with TEST_PLAN/TEST_RUN/TEST_REPORT.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any unresolved {{PLACEHOLDER}} remains in session documents (recommended only after you finish writing).",
    )
    args = parser.parse_args()

    session_dir = Path(args.session_dir).expanduser()
    if args.code_root.strip():
        code_root = Path(args.code_root).expanduser().resolve()
    else:
        resolved_session = session_dir.resolve()
        code_root = _find_code_root(resolved_session) or _fail(f"could not locate code root from: {resolved_session}")

    issues = verify_session(
        session_dir=session_dir.resolve(),
        code_root=code_root,
        require_review=args.require_review,
        strict=args.strict,
    )

    if issues:
        order = {"P0": 0, "P1": 1, "P2": 2}
        issues_sorted = sorted(issues, key=lambda i: order.get(i.severity, 99))
        for it in issues_sorted:
            print(f"{it.severity}: {it.message}", file=sys.stderr)
        return 2

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
