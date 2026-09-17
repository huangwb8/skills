#!/usr/bin/env python3
"""Check numbered R/Rmd units, dependencies, directory boundaries and checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - reported when a plan or metadata needs parsing
    yaml = None


UNIT_ID_RE = re.compile(r"^(?P<a>\d{2})\.(?P<b>\d{2})\.(?P<c>\d{2})$")
UNIT_STEM_RE = re.compile(r"^(?P<id>\d{2}\.\d{2}\.\d{2})\. (?P<name>[^/\\]+)$")
UNIT_FILE_RE = re.compile(
    r"^(?P<stem>\d{2}\.\d{2}\.\d{2}\. [^/\\]+?)(?P<functions>_functions)?(?P<suffix>\.R|\.Rmd|\.html)$"
)
WRITE_RAW_RE = re.compile(
    r"(?:write(?:Lines|\.table|\.csv|_csv|_tsv)?|saveRDS|save|ggsave|file\.copy|dir\.create)\s*\([^\n]{0,240}(?:file\.path\s*\(\s*['\"]raw['\"]|['\"]raw[/\\])",
    re.IGNORECASE,
)
ABSOLUTE_PATH_RE = re.compile(r"^(?:/|[A-Za-z]:[/\\]|\\\\)")
LEGACY_TMP_RE = re.compile(r"(?:file\.path\s*\(\s*['\"]tmp['\"]|['\"]tmp[/\\])")
WINDOWS_RESERVED_RE = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def unit_key(unit_id: str) -> tuple[int, int, int]:
    match = UNIT_ID_RE.fullmatch(unit_id)
    if not match:
        raise ValueError(unit_id)
    return tuple(int(match.group(name)) for name in ("a", "b", "c"))


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return f"<outside-project>/{path.name}"


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML is required to read YAML plans and checkpoint metadata")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def md5_file(path: Path) -> str:
    digest = hashlib.md5()  # nosec: integrity/cache identity, not authentication
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unsafe_plan_path(value: str) -> bool:
    return bool(ABSOLUTE_PATH_RE.match(value)) or ".." in re.split(r"[/\\]+", value)


def unsafe_portable_name(value: str) -> bool:
    return bool(re.search(r'[<>:"/\\|?*\x00-\x1f]', value)) or value.endswith((".", " ")) or bool(
        WINDOWS_RESERVED_RE.match(value)
    )


def detect_legacy_project(root: Path) -> bool:
    if not (root / "tmp").is_dir():
        return False
    for path in list(root.glob("*.R")) + list(root.glob("*.Rmd")):
        if UNIT_FILE_RE.fullmatch(path.name) or path.name == "00.Environment.R":
            continue
        if LEGACY_TMP_RE.search(path.read_text(encoding="utf-8", errors="replace")):
            return True
    return False


def check_root_files(root: Path, findings: list[Finding], *, legacy: bool) -> dict[str, set[str]]:
    stems: dict[str, set[str]] = {}
    environment_path = root / "00.Environment.R"

    for path in sorted(root.iterdir()):
        if not path.is_file() or path.suffix not in {".R", ".Rmd", ".html"}:
            continue
        if path.name == "00.Environment.R":
            continue
        match = UNIT_FILE_RE.fullmatch(path.name)
        if not match:
            severity = "warning" if legacy else "error"
            code = "legacy-unnumbered-file" if legacy else "unnumbered-root-file"
            findings.append(
                Finding(severity, code, path.name, "root R/Rmd/HTML file does not use 'AA.BB.CC. name'")
            )
            continue
        stem = match.group("stem")
        stem_match = UNIT_STEM_RE.fullmatch(stem)
        if stem_match and unsafe_portable_name(stem_match.group("name")):
            findings.append(
                Finding("error", "unsafe-unit-name", path.name, "unit name is not portable to Windows filesystems")
            )
        kind = "functions.R" if match.group("functions") else match.group("suffix").lstrip(".")
        stems.setdefault(stem, set()).add(kind)
    if stems and not legacy:
        if environment_path.is_symlink():
            findings.append(
                Finding("error", "environment-symlink", "00.Environment.R", "environment entry cannot be a symlink")
            )
        elif not environment_path.is_file():
            findings.append(
                Finding("error", "missing-environment", "00.Environment.R", "numbered projects need 00.Environment.R")
            )
    return stems


def check_plan(root: Path, plan_path: Path, stems: dict[str, set[str]], findings: list[Finding]) -> None:
    if not plan_path.exists():
        findings.append(Finding("error", "missing-plan", relative(plan_path, root), "analysis plan does not exist"))
        return
    try:
        data = load_yaml(plan_path)
    except Exception as exc:
        findings.append(Finding("error", "invalid-plan", relative(plan_path, root), str(exc)))
        return
    if not isinstance(data, dict) or not isinstance(data.get("units"), list):
        findings.append(Finding("error", "invalid-plan-shape", relative(plan_path, root), "plan must contain a units list"))
        return

    workflow = str(data.get("workflow", ""))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", workflow):
        findings.append(
            Finding(
                "error",
                "invalid-workflow",
                relative(plan_path, root),
                "workflow must start with a letter or digit and be a safe path segment",
            )
        )

    units: dict[str, dict[str, Any]] = {}
    required_fields = ("purpose", "depends_on", "inputs", "code", "products", "cache", "reports", "completion")
    for index, raw in enumerate(data["units"]):
        location = f"{relative(plan_path, root)}:units[{index}]"
        if not isinstance(raw, dict):
            findings.append(Finding("error", "invalid-unit", location, "unit must be a mapping"))
            continue
        unit_id = str(raw.get("id", ""))
        name = str(raw.get("name", "")).strip()
        if not UNIT_ID_RE.fullmatch(unit_id) or not name:
            findings.append(Finding("error", "invalid-unit-identity", location, "unit needs a valid id and non-empty name"))
            continue
        if not UNIT_STEM_RE.fullmatch(f"{unit_id}. {name}") or unsafe_portable_name(name):
            findings.append(Finding("error", "unsafe-unit-name", location, "unit name is not a portable file name"))
            continue
        if unit_id in units:
            findings.append(Finding("error", "duplicate-unit", location, f"duplicate unit id {unit_id}"))
            continue
        units[unit_id] = raw
        stem = f"{unit_id}. {name}"
        for field in required_fields:
            if field not in raw:
                findings.append(Finding("error", "missing-unit-field", location, f"missing {field}"))
        if stem not in stems and not raw.get("legacy", False):
            findings.append(Finding("error", "missing-unit-file", location, f"no numbered root file matches {stem!r}"))

        cache_enabled = raw.get("cache")
        if not isinstance(cache_enabled, bool):
            findings.append(Finding("error", "invalid-cache", location, "cache must be true or false"))

        code = raw.get("code", [])
        if not isinstance(code, list):
            findings.append(Finding("error", "invalid-code-list", location, "code must be a list"))
            continue
        seen_code: set[str] = set()
        allowed_code_names = {f"{stem}.R", f"{stem}_functions.R", f"{stem}.Rmd"}
        for item in code:
            item_text = str(item)
            if unsafe_plan_path(item_text):
                findings.append(Finding("error", "unsafe-code-path", location, f"unsafe code path: {item}"))
                continue
            candidate = (root / item_text).resolve()
            try:
                rel = candidate.relative_to(root)
            except ValueError:
                findings.append(Finding("error", "path-outside-root", location, f"code path escapes project: {item}"))
                continue
            if not candidate.is_file():
                findings.append(Finding("error", "missing-code", rel.as_posix(), "planned code file does not exist"))
            if candidate.parent != root:
                findings.append(Finding("error", "code-not-in-root", rel.as_posix(), "numbered R/Rmd code must be in project root"))
            if Path(item_text).name not in allowed_code_names:
                findings.append(Finding("error", "code-unit-mismatch", location, f"code does not match unit stem: {item}"))
            if item_text in seen_code:
                findings.append(Finding("error", "duplicate-code", location, f"duplicate code entry: {item}"))
            seen_code.add(item_text)
        if cache_enabled is True and sum(str(item) == f"{stem}.R" for item in code) != 1:
            findings.append(
                Finding(
                    "error",
                    "cached-unit-main-script",
                    location,
                    f"cached unit must declare exactly one root computation script: {stem}.R",
                )
            )

        for field in ("inputs", "products", "reports"):
            values = raw.get(field, [])
            if not isinstance(values, list):
                findings.append(Finding("error", f"invalid-{field}", location, f"{field} must be a list"))
                continue
            for item in values:
                item_text = str(item)
                if unsafe_plan_path(item_text):
                    findings.append(Finding("error", "parent-path-segment", location, f"unsafe {field} path: {item}"))
                    continue
                candidate = (root / item_text).resolve()
                try:
                    rel = candidate.relative_to(root)
                except ValueError:
                    findings.append(Finding("error", "path-outside-root", location, f"{field} path escapes project: {item}"))
                    continue
                if field == "inputs" and rel.parts and rel.parts[0] == "raw" and not candidate.exists():
                    findings.append(Finding("error", "missing-raw-input", rel.as_posix(), "planned raw input does not exist"))
                if field == "inputs" and (not rel.parts or rel.parts[0] not in {"raw", "products"}):
                    findings.append(Finding("error", "input-boundary", rel.as_posix(), "inputs must come from raw/ or products/"))
                if field == "reports":
                    root_html = rel.parent == Path(".") and rel.name == f"{stem}.html"
                    formal_report = (
                        len(rel.parts) >= 3
                        and rel.parts[0] == "reports"
                        and rel.parts[1] in {"figures", "tables", "supplementary"}
                        and rel.name.startswith(f"{unit_id}.")
                    )
                    if not (root_html or formal_report):
                        findings.append(Finding("error", "report-boundary", rel.as_posix(), "report path does not match the unit/root/report boundary"))

        products = raw.get("products", [])
        expected_prefix = f"products/{workflow}/{stem}/"
        expected_dir = (root / "products" / workflow / stem).resolve()
        product_locations_valid = True
        if isinstance(products, list):
            for item in products:
                candidate = (root / str(item)).resolve()
                try:
                    candidate.relative_to(expected_dir)
                except ValueError:
                    product_locations_valid = False
                    findings.append(Finding("error", "product-boundary", location, f"product must stay under {expected_prefix}: {item}"))
        if cache_enabled is True:
            if not isinstance(products, list) or not products or not product_locations_valid:
                findings.append(Finding("error", "cache-product-mismatch", location, f"cached unit needs a product under {expected_prefix}"))

    requirements = data.get("requirements", [])
    if not isinstance(requirements, list):
        findings.append(Finding("error", "invalid-requirements", relative(plan_path, root), "requirements must be a list"))
    elif not requirements:
        findings.append(Finding("error", "missing-requirements", relative(plan_path, root), "requirements must not be empty"))
    else:
        seen_requirements: set[str] = set()
        for index, requirement in enumerate(requirements):
            location = f"{relative(plan_path, root)}:requirements[{index}]"
            if not isinstance(requirement, dict):
                findings.append(Finding("error", "invalid-requirement", location, "requirement must be a mapping"))
                continue
            requirement_id = str(requirement.get("id", ""))
            mapped_units = requirement.get("units", [])
            if not requirement_id or requirement_id in seen_requirements:
                findings.append(Finding("error", "invalid-requirement-id", location, "requirement id is empty or duplicated"))
            seen_requirements.add(requirement_id)
            if not requirement.get("description"):
                findings.append(Finding("error", "missing-requirement-description", location, "requirement needs a description"))
            if not isinstance(mapped_units, list) or not mapped_units:
                findings.append(Finding("error", "unmapped-requirement", location, "requirement must map to at least one unit"))
            else:
                for unit_id in mapped_units:
                    if str(unit_id) not in units:
                        findings.append(Finding("error", "unknown-requirement-unit", location, f"unknown unit {unit_id}"))

    graph: dict[str, list[str]] = {}
    for unit_id, raw in units.items():
        depends = raw.get("depends_on", [])
        location = f"{relative(plan_path, root)}:{unit_id}"
        if not isinstance(depends, list):
            findings.append(Finding("error", "invalid-dependencies", location, "depends_on must be a list"))
            graph[unit_id] = []
            continue
        graph[unit_id] = [str(item) for item in depends]
        for upstream in graph[unit_id]:
            if upstream not in units:
                findings.append(Finding("error", "missing-upstream", location, f"unknown upstream {upstream}"))
            elif unit_key(upstream) >= unit_key(unit_id):
                findings.append(Finding("error", "forward-dependency", location, f"upstream {upstream} is not earlier"))

    unit_stems = {f"{unit_id}. {str(raw.get('name', '')).strip()}": unit_id for unit_id, raw in units.items()}
    for unit_id, raw in units.items():
        location = f"{relative(plan_path, root)}:{unit_id}"
        inputs = raw.get("inputs", [])
        if not isinstance(inputs, list):
            continue
        for item in inputs:
            parts = str(item).replace("\\", "/").split("/")
            if not parts or parts[0] != "products":
                continue
            if len(parts) < 4 or parts[1] != workflow:
                findings.append(
                    Finding(
                        "error",
                        "invalid-product-input",
                        location,
                        f"product input must use products/{workflow}/<unit-stem>/<file>: {item}",
                    )
                )
                continue
            upstream = unit_stems.get(parts[2])
            if upstream is None:
                findings.append(
                    Finding("error", "unknown-product-input", location, f"product input has no planned unit: {item}")
                )
            elif unit_key(upstream) >= unit_key(unit_id):
                findings.append(
                    Finding("error", "product-input-order", location, f"product input must come from an earlier unit: {item}")
                )
            elif upstream not in graph.get(unit_id, []):
                findings.append(
                    Finding(
                        "error",
                        "product-input-dependency",
                        location,
                        f"product input requires depends_on entry {upstream}: {item}",
                    )
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            findings.append(Finding("error", "dependency-cycle", relative(plan_path, root), f"cycle contains {node}"))
            return
        visiting.add(node)
        for upstream in graph.get(node, []):
            if upstream in graph:
                visit(upstream)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)

    if any(unit.get("cache") is True for unit in units.values()):
        helper = root / "templates" / "checkpoint_helpers.R"
        templates = root / "templates"
        helper_is_safe = helper.is_file() and not helper.is_symlink() and not templates.is_symlink()
        if helper_is_safe:
            try:
                helper.resolve().relative_to(root)
            except ValueError:
                helper_is_safe = False
        if not helper_is_safe:
            findings.append(
                Finding(
                    "error",
                    "unsafe-checkpoint-helper",
                    "templates/checkpoint_helpers.R",
                    "cached workflows need a regular in-project copy of the Skill checkpoint helper",
                )
            )


def walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)


def check_checkpoint(path: Path, root: Path, findings: list[Finding], *, stale_severity: str) -> None:
    required = ("metadata.yaml", "summary.md", "SUCCESS")
    if path.is_symlink():
        findings.append(Finding("error", "checkpoint-symlink", relative(path, root), "checkpoint directory cannot be a symlink"))
        return
    for name in required:
        required_path = path / name
        if required_path.is_symlink():
            findings.append(Finding("error", "checkpoint-symlink", relative(required_path, root), f"{name} cannot be a symlink"))
        elif not required_path.is_file():
            findings.append(Finding(stale_severity, "incomplete-checkpoint", relative(path, root), f"missing {name}"))
    metadata_path = path / "metadata.yaml"
    if metadata_path.is_symlink() or (path / "SUCCESS").is_symlink():
        return
    if not metadata_path.is_file():
        return
    try:
        metadata = load_yaml(metadata_path)
    except Exception as exc:
        findings.append(Finding(stale_severity, "invalid-metadata", relative(metadata_path, root), str(exc)))
        return
    if not isinstance(metadata, dict):
        findings.append(Finding(stale_severity, "invalid-metadata-shape", relative(metadata_path, root), "metadata must be a mapping"))
        return
    for key in (
        "unit_id",
        "cache_identity",
        "product_identity",
        "output_contract_version",
        "output_structure",
        "outputs",
    ):
        if key not in metadata:
            findings.append(Finding(stale_severity, "missing-metadata-field", relative(metadata_path, root), f"missing {key}"))
    for value in walk_strings(metadata):
        if ABSOLUTE_PATH_RE.match(value):
            findings.append(Finding("error", "absolute-private-path", relative(metadata_path, root), "metadata contains an absolute path"))
            break
    outputs = metadata.get("outputs", [])
    if not isinstance(outputs, list) or not outputs:
        findings.append(Finding(stale_severity, "empty-checkpoint-outputs", relative(metadata_path, root), "outputs must be a non-empty list"))
    else:
        for item in outputs:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("path"), str)
                or not isinstance(item.get("md5"), str)
                or not re.fullmatch(r"[0-9a-fA-F]{32}", item.get("md5", ""))
            ):
                findings.append(Finding(stale_severity, "invalid-checkpoint-output", relative(metadata_path, root), "each output needs path and MD5"))
                continue
            candidate = (path / item["path"]).resolve()
            try:
                candidate.relative_to(path.resolve())
            except ValueError:
                findings.append(Finding("error", "output-path-escape", relative(metadata_path, root), str(item["path"])))
                continue
            logical_candidate = path / item["path"]
            if logical_candidate.is_symlink():
                findings.append(Finding("error", "checkpoint-symlink", relative(logical_candidate, root), "checkpoint output cannot be a symlink"))
                continue
            if not candidate.is_file():
                findings.append(Finding(stale_severity, "missing-checkpoint-output", relative(path, root), str(item["path"])))
                continue
            expected_md5 = item.get("md5")
            if isinstance(expected_md5, str):
                actual_md5 = md5_file(candidate)
                if actual_md5 != expected_md5:
                    findings.append(Finding(stale_severity, "damaged-checkpoint-output", relative(candidate, root), "MD5 does not match metadata"))

    success_path = path / "SUCCESS"
    if success_path.is_file() and isinstance(metadata.get("cache_identity"), str):
        marker = success_path.read_text(encoding="utf-8", errors="replace").strip()
        if marker != metadata["cache_identity"]:
            findings.append(Finding(stale_severity, "success-identity-mismatch", relative(success_path, root), "SUCCESS does not match cache_identity"))


def check_boundaries(root: Path, findings: list[Finding], *, allow_stale_checkpoints: bool) -> None:
    reports = root / "reports"
    if reports.is_dir():
        for path in reports.rglob("*"):
            if path.is_file() and path.suffix in {".R", ".Rmd"}:
                findings.append(Finding("error", "source-in-reports", relative(path, root), "reports contains source code"))
            if path.is_file() and path.suffix == ".html" and path.parent.name != "supplementary":
                findings.append(Finding("error", "report-html-location", relative(path, root), "rendered Rmd HTML belongs in project root"))

    products = root / "products"
    if products.is_dir():
        for path in products.rglob("*"):
            if path.is_file() and path.suffix in {".R", ".Rmd", ".html"}:
                findings.append(Finding("error", "source-in-products", relative(path, root), "products contains source/report files"))
        for directory in sorted(path for path in products.rglob("*") if path.is_dir()):
            if len(directory.relative_to(products).parts) != 2:
                continue
            files = [item for item in directory.iterdir() if item.is_file()]
            if files:
                check_checkpoint(
                    directory,
                    root,
                    findings,
                    stale_severity="warning" if allow_stale_checkpoints else "error",
                )

    for script in list(root.glob("*.R")) + list(root.glob("*.Rmd")):
        text = script.read_text(encoding="utf-8", errors="replace")
        if WRITE_RAW_RE.search(text):
            findings.append(Finding("error", "write-to-raw", script.name, "script appears to write into raw/"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", help="R analysis project root")
    parser.add_argument("--plan", default=None, help="plan path relative to project root")
    parser.add_argument("--strict", action="store_true", help="exit non-zero when findings exist")
    parser.add_argument("--legacy", action="store_true", help="explicitly validate an existing unnumbered tmp-based project")
    parser.add_argument(
        "--allow-stale-checkpoints",
        action="store_true",
        help="downgrade recoverable checkpoint integrity findings to warnings",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        print("[FAIL] project root is not a directory", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    legacy = args.legacy or detect_legacy_project(root)
    stems = check_root_files(root, findings, legacy=legacy)
    if args.plan:
        plan_path = (root / args.plan).resolve()
        try:
            plan_path.relative_to(root)
        except ValueError:
            print("[FAIL] --plan must stay inside project root", file=sys.stderr)
            return 2
        check_plan(root, plan_path, stems, findings)
    check_boundaries(root, findings, allow_stale_checkpoints=args.allow_stale_checkpoints)

    payload = {
        "project_root": ".",
        "mode": "strict" if args.strict else "report",
        "numbered_units": sorted(stems),
        "legacy_mode": legacy,
        "findings": [asdict(item) for item in findings],
        "status": "pass" if not findings else "findings",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(f"[{item.severity.upper()}] {item.code}: {item.path}: {item.message}")
        print(f"[{payload['status'].upper()}] units={len(stems)} findings={len(findings)} mode={payload['mode']}")
    blocking = any(item.severity == "error" for item in findings)
    return 1 if args.strict and blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
