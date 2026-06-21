#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import typing
from dataclasses import dataclass
from pathlib import Path

_TEST_ID_RE = re.compile(r"^v\d{12}$")
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


@dataclass(frozen=True)
class Issue:
    severity: str  # P0/P1/P2
    message: str


def _fail(message: str) -> typing.NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def _find_skill_root(start: Path) -> Path | None:
    p = start
    for _ in range(20):
        if (p / "SKILL.md").exists():
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


def _load_directories(config_path: Path) -> dict[str, str]:
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    data = _parse_simple_yaml_sections(text, wanted_sections={"directories"})
    out = data.get("directories") or {}
    return {str(k): str(v) for k, v in out.items()}


def _load_effective_directories(skill_root: Path) -> dict[str, str]:
    target_dirs = _load_directories(skill_root / "config.yaml")
    if target_dirs:
        return target_dirs
    bundled_root = Path(__file__).resolve().parent.parent
    return _load_directories(bundled_root / "config.yaml")


def _safe_rel_path(value: str, *, default: str) -> str:
    if not value:
        return default
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        return default
    return value


def _extract_markdown_field(text: str, field_label: str) -> str | None:
    # Example: **关联规划文档**: .bensz-api/skills/auto-test-skill/output/plans/v202601162330.md
    pat = re.compile(rf"^\*\*{re.escape(field_label)}\*\*:\s*(.+?)\s*$", re.MULTILINE)
    m = pat.search(text)
    if not m:
        return None
    return m.group(1).strip()


def _scan_placeholders(text: str) -> list[str]:
    return [m.group(0) for m in _PLACEHOLDER_RE.finditer(text)]


def _check_report_status(text: str) -> tuple[bool, bool]:
    """
    Returns (is_ok, found).
    Template placeholder looks like: "- 状态：✅ 通过 / ❌ 失败 / ⚠️ 部分通过"
    """
    for line in text.splitlines():
        if "状态：" in line:
            return ("/" not in line, True)
    return (False, False)


def _classify_session(session_dir: Path) -> tuple[str, str] | None:
    name = session_dir.name
    if name.startswith("B轮-"):
        test_id = name.removeprefix("B轮-")
        if _TEST_ID_RE.fullmatch(test_id):
            return ("b", test_id)
        return None
    if _TEST_ID_RE.fullmatch(name):
        return ("a", name)
    return None


def verify_test_session(
    *,
    session_dir: Path,
    skill_root: Path,
    require_plan: bool,
) -> list[Issue]:
    issues: list[Issue] = []

    if not session_dir.exists() or not session_dir.is_dir():
        return [Issue("P0", f"session_dir is not a directory: {session_dir}")]

    directories = _load_effective_directories(skill_root)
    tests_dir = skill_root / _safe_rel_path(directories.get("tests", ""), default="tests")
    if tests_dir.exists():
        if tests_dir.is_symlink():
            issues.append(Issue("P1", f"tests directory is a symlink (discouraged): {tests_dir}"))
        try:
            session_dir.resolve().relative_to(tests_dir.resolve())
        except Exception:
            issues.append(Issue("P1", f"session_dir is not under configured tests directory: {tests_dir}"))

    kind_info = _classify_session(session_dir)
    if kind_info is None:
        issues.append(Issue("P1", f"unexpected session directory name (expected vYYYYMMDDHHMM or B轮-vYYYYMMDDHHMM): {session_dir.name}"))
        kind = "unknown"
        test_id = ""
    else:
        kind, test_id = kind_info

    required_paths = [
        (session_dir / "TEST_PLAN.md", "TEST_PLAN.md"),
        (session_dir / "TEST_REPORT.md", "TEST_REPORT.md"),
        (session_dir / "_artifacts", "_artifacts/"),
        (session_dir / "_scripts", "_scripts/"),
    ]
    for p, label in required_paths:
        if not p.exists():
            issues.append(Issue("P0", f"missing required {label}: {p}"))
        elif label.endswith("/") and not p.is_dir():
            issues.append(Issue("P0", f"{label} is not a directory: {p}"))

    plan_text = ""
    report_text = ""
    test_plan_text = ""

    plan_path: Path | None = None
    if require_plan and kind in {"a", "b"} and test_id:
        plans_dir = skill_root / _safe_rel_path(directories.get("plans", ""), default="plans")
        if kind == "a":
            plan_path = plans_dir / f"{test_id}.md"
        else:
            plan_path = plans_dir / f"B轮-{test_id}.md"

        if not plan_path.exists():
            issues.append(Issue("P0", f"missing plan doc (expected by session id): {plan_path}"))
        else:
            plan_text = plan_path.read_text(encoding="utf-8", errors="replace")

    test_plan_path = session_dir / "TEST_PLAN.md"
    if test_plan_path.exists():
        test_plan_text = test_plan_path.read_text(encoding="utf-8", errors="replace")
        placeholders = _scan_placeholders(test_plan_text)
        if placeholders:
            uniq = sorted(set(placeholders))
            shown = uniq[:8]
            suffix = " (and more)" if len(uniq) > len(shown) else ""
            issues.append(Issue("P0", f"TEST_PLAN.md contains unresolved placeholders: {shown}{suffix}"))

    report_path = session_dir / "TEST_REPORT.md"
    if report_path.exists():
        report_text = report_path.read_text(encoding="utf-8", errors="replace")
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
            issues.append(Issue("P1", "TEST_REPORT.md status line looks like the template placeholder; set it to a single status (e.g. ✅ 通过)."))

    if require_plan and plan_path is not None and plan_text:
        if kind == "a":
            placeholders = _scan_placeholders(plan_text)
            if placeholders:
                uniq = sorted(set(placeholders))
                shown = uniq[:8]
                suffix = " (and more)" if len(uniq) > len(shown) else ""
                issues.append(Issue("P0", f"A-round plan doc contains unresolved placeholders (should be fully rendered): {shown}{suffix}"))
        elif kind == "b":
            # B-round plan templates are intentionally verbose; only enforce that auto-filled header fields are not left as placeholders.
            for ph in ["{{TEST_ID}}", "{{CHECK_TIME}}", "{{A_TEST_ID}}", "{{TARGET_SKILL_NAME}}", "{{TARGET_SKILL_ROOT}}"]:
                if ph in plan_text:
                    issues.append(Issue("P0", f"B-round plan doc still contains required auto-filled placeholder: {ph}"))

    if require_plan:
        # Validate that TEST_PLAN/TEST_REPORT reference an existing plan file.
        expected_plan_resolved = plan_path.resolve() if (plan_path is not None and plan_path.exists()) else None
        for label, text in [("TEST_PLAN.md", test_plan_text), ("TEST_REPORT.md", report_text)]:
            if not text:
                continue
            ref = _extract_markdown_field(text, "关联规划文档")
            if ref is None:
                issues.append(Issue("P1", f"{label} missing '**关联规划文档**: ...' field"))
                continue
            ref_path = Path(ref)
            if ref_path.is_absolute() or ".." in ref_path.parts:
                issues.append(Issue("P0", f"{label} has unsafe plan path: {ref}"))
                continue
            abs_ref = (skill_root / ref_path).resolve()
            try:
                abs_ref.relative_to(skill_root)
            except ValueError:
                issues.append(Issue("P0", f"{label} plan path resolves outside skill_root: {ref} -> {abs_ref}"))
                continue
            if not abs_ref.exists():
                issues.append(Issue("P0", f"{label} references missing plan doc: {ref}"))
                continue
            if expected_plan_resolved is not None and abs_ref != expected_plan_resolved:
                issues.append(Issue("P1", f"{label} references a different plan doc than expected by session id: {ref}"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an auto-test-skill test session directory for completeness.")
    parser.add_argument(
        "session_dir",
        help="Session directory path (e.g. .bensz-api/skills/auto-test-skill/output/tests/vYYYYMMDDHHMM or .bensz-api/skills/auto-test-skill/output/tests/B轮-vYYYYMMDDHHMM).",
    )
    parser.add_argument(
        "--skill-root",
        default="",
        help="Explicit skill root (must contain SKILL.md). If omitted, auto-detect by walking up from session_dir.",
    )
    parser.add_argument(
        "--require-plan",
        action="store_true",
        help="Require the corresponding plan doc to exist and be consistent with TEST_PLAN/TEST_REPORT.",
    )
    args = parser.parse_args()

    session_dir = Path(args.session_dir).expanduser()
    if args.skill_root.strip():
        skill_root = Path(args.skill_root).expanduser().resolve()
        if not (skill_root / "SKILL.md").exists():
            _fail(f"--skill-root is not a Skill directory (missing SKILL.md): {skill_root}")
    else:
        resolved_session = session_dir.resolve()
        skill_root = _find_skill_root(resolved_session) or _fail(f"could not locate skill root from: {resolved_session}")

    issues = verify_test_session(
        session_dir=session_dir.resolve(),
        skill_root=skill_root,
        require_plan=args.require_plan,
    )

    if issues:
        # Print in severity order.
        order = {"P0": 0, "P1": 1, "P2": 2}
        issues_sorted = sorted(issues, key=lambda i: order.get(i.severity, 99))
        for it in issues_sorted:
            print(f"{it.severity}: {it.message}", file=sys.stderr)
        return 2

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
