from __future__ import annotations

import fnmatch
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "缺少 PyYAML 依赖，无法读取 compact-bensz-skills/config.yaml。请先安装 pyyaml。"
    ) from exc


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
WORD_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")
HEADING_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)
FENCE_RE = re.compile(r"^```", re.MULTILINE)
LOCAL_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict[str, Any]:
    config_path = skill_dir() / "config.yaml"
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def resolve_skill_root(skill_root: str) -> Path:
    path = Path(skill_root).expanduser().resolve()
    if not path.is_dir():
        raise SystemExit(f"skill_root 不存在或不是目录: {path}")
    if not (path / "SKILL.md").exists():
        raise SystemExit(f"目标目录缺少 SKILL.md: {path}")
    return path


def resolve_workspace_root(
    target_skill_root: Path,
    config: dict[str, Any],
    workspace_dir: str | None = None,
    run_id: str | None = None,
    create: bool = False,
) -> Path:
    workspace_base, explicit_run_id = resolve_workspace_base(target_skill_root, config, workspace_dir)
    effective_run_id = run_id or explicit_run_id
    if effective_run_id is None:
        if create:
            effective_run_id = allocate_unique_run_id(workspace_base, config, generate_run_id(config))
        else:
            effective_run_id = read_latest_run_id(workspace_base, config)
            if effective_run_id is None:
                raise SystemExit(
                    "未找到可复用的 run 目录。请先运行 init_workspace.py，或显式传入 --run-id。"
                )
    return workspace_base / effective_run_id


def resolve_workspace_base(
    target_skill_root: Path,
    config: dict[str, Any],
    workspace_dir: str | None = None,
) -> tuple[Path, str | None]:
    if workspace_dir:
        candidate = Path(workspace_dir).expanduser().resolve()
        if is_run_dir_name(candidate.name, config):
            return candidate.parent, candidate.name
        return candidate, None
    return target_skill_root / config["workspace"]["hidden_dir"], None


def generate_run_id(config: dict[str, Any]) -> str:
    prefix = config["workspace"]["run_prefix"]
    timestamp_format = config["workspace"]["timestamp_format"]
    return f"{prefix}{datetime.now().strftime(timestamp_format)}"


def is_run_dir_name(name: str, config: dict[str, Any]) -> bool:
    prefix = config["workspace"]["run_prefix"]
    timestamp_format = config["workspace"]["timestamp_format"]
    sample = datetime(2000, 1, 2, 3, 4, 5).strftime(timestamp_format)
    digit_pattern = "".join(r"\d" if ch.isdigit() else re.escape(ch) for ch in sample)
    pattern = rf"^{re.escape(prefix)}{digit_pattern}(?:-\d{{2}})?$"
    return re.match(pattern, name) is not None


def allocate_unique_run_id(workspace_base: Path, config: dict[str, Any], base_run_id: str) -> str:
    if not (workspace_base / base_run_id).exists():
        return base_run_id
    for idx in range(2, 100):
        candidate = f"{base_run_id}-{idx:02d}"
        if not (workspace_base / candidate).exists():
            return candidate
    raise SystemExit(f"无法在 {workspace_base} 下分配唯一 run 目录: {base_run_id}")


def latest_run_pointer_path(workspace_base: Path, config: dict[str, Any]) -> Path:
    return workspace_base / config["workspace"]["latest_run_pointer"]


def write_latest_run_id(workspace_base: Path, config: dict[str, Any], run_id: str) -> None:
    pointer = latest_run_pointer_path(workspace_base, config)
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(run_id + "\n", encoding="utf-8")


def read_latest_run_id(workspace_base: Path, config: dict[str, Any]) -> str | None:
    pointer = latest_run_pointer_path(workspace_base, config)
    if not pointer.exists():
        return None
    run_id = pointer.read_text(encoding="utf-8").strip()
    return run_id or None


def path_within(base_dir: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False


def workspace_subpaths(config: dict[str, Any], workspace_root: Path) -> dict[str, Path]:
    subpaths = {name: workspace_root / name for name in config["workspace"]["subdirs"]}
    subpaths["workspace_root"] = workspace_root
    subpaths["workspace_base"] = workspace_root.parent
    subpaths["before_snapshot_dir"] = workspace_root / config["workspace"]["before_snapshot_dir"]
    for key, relative_path in config["reports"].items():
        subpaths[key] = workspace_root / relative_path
    return subpaths


def ensure_workspace(config: dict[str, Any], workspace_root: Path) -> dict[str, Path]:
    paths = workspace_subpaths(config, workspace_root)
    for path in paths.values():
        if path == paths["workspace_base"]:
            path.mkdir(parents=True, exist_ok=True)
            continue
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
    return paths


def should_ignore_path(relative_path: Path, config: dict[str, Any]) -> bool:
    ignore_dirs = set(config["source_files"]["ignore_dirs"])
    if any(part in ignore_dirs for part in relative_path.parts[:-1]):
        return True
    ignore_file_names = set(config["source_files"].get("ignore_file_names", []))
    if relative_path.name in ignore_file_names:
        return True
    ignore_globs = config["source_files"]["ignore_globs"]
    return any(fnmatch.fnmatch(relative_path.name, pattern) for pattern in ignore_globs)


def iter_markdown_files(
    target_skill_root: Path,
    config: dict[str, Any],
    workspace_root: Path,
) -> list[Path]:
    markdown_exts = set(config["source_files"]["markdown_extensions"])
    files: list[Path] = []
    for path in sorted(target_skill_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in markdown_exts:
            continue
        try:
            relative_path = path.relative_to(target_skill_root)
        except ValueError:
            continue
        if workspace_root in path.parents or path == workspace_root:
            continue
        if should_ignore_path(relative_path, config):
            continue
        files.append(path)
    return files


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compute_text_stats(text: str) -> dict[str, int]:
    return {
        "chars": len(text),
        "words": len(WORD_RE.findall(text)),
        "lines": text.count("\n") + (0 if not text else 1),
        "headings": len(HEADING_RE.findall(text)),
        "fence_markers": len(FENCE_RE.findall(text)),
    }


def compute_file_record(target_skill_root: Path, path: Path) -> dict[str, Any]:
    text = read_text(path)
    record = {"path": str(path.relative_to(target_skill_root))}
    record.update(compute_text_stats(text))
    return record


def build_totals(records: list[dict[str, Any]], phase: str) -> dict[str, Any]:
    return {
        "phase": phase,
        "file_count": len(records),
        "total_chars": sum(int(record["chars"]) for record in records),
        "total_words": sum(int(record["words"]) for record in records),
        "total_lines": sum(int(record["lines"]) for record in records),
        "total_headings": sum(int(record["headings"]) for record in records),
        "total_fence_markers": sum(int(record["fence_markers"]) for record in records),
        "files": records,
    }


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def snapshot_files(target_skill_root: Path, files: list[Path], snapshot_root: Path) -> None:
    if snapshot_root.exists():
        shutil.rmtree(snapshot_root)
    for file_path in files:
        relative_path = file_path.relative_to(target_skill_root)
        destination = snapshot_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, destination)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    body = text[match.end() :]
    return data, body


def nested_get(data: dict[str, Any], dotted_key: str) -> Any:
    value: Any = data
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def normalize_link_target(target: str) -> str | None:
    cleaned = target.strip()
    if not cleaned or cleaned.startswith("#"):
        return None
    if "://" in cleaned or cleaned.startswith("mailto:"):
        return None
    return cleaned.split("#", 1)[0]


def find_local_link_issues(
    base_file: Path,
    text: str,
    target_skill_root: Path,
) -> list[str]:
    issues: list[str] = []
    for raw_target in LOCAL_LINK_RE.findall(text):
        normalized = normalize_link_target(raw_target)
        if not normalized:
            continue
        resolved = (base_file.parent / normalized).resolve()
        if not path_within(target_skill_root, resolved):
            issues.append(f"本地链接越出 skill 根目录 -> {raw_target}")
            continue
        if not resolved.exists():
            issues.append(f"本地链接不存在 -> {raw_target}")
    return issues
