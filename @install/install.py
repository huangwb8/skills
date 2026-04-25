#!/usr/bin/env python3
"""Cross-platform installer for bensz skills.

This script is intentionally self-contained and uses only the Python standard
library. It downloads skills from GitHub zip archives, installs changed skills
to user-level Codex and Claude Code directories, and records lightweight
manifests for traceability.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


MIN_PYTHON = (3, 8)
INSTALLATION_ROOT_PARTS = (".bensz-skills", "installation")

DEFAULT_SOURCES = [
    {
        "id": "general",
        "name": "General skills",
        "url": "https://github.com/huangwb8/skills",
        "branch": "main",
        "skills_path": ".",
    },
    {
        "id": "research",
        "name": "Research skills",
        "url": "https://github.com/huangwb8/ChineseResearchLaTeX",
        "branch": "main",
        "skills_path": "skills",
    },
    {
        "id": "anthropic-docs",
        "name": "Anthropic document skills",
        "url": "https://github.com/anthropics/skills",
        "branch": "main",
        "skills_path": "skills",
    },
]

LEGACY_SKILL_NAMES = [
    "make_latex_model",
    "transfer_old_latex_to_new",
    "write-paper-sci",
    "explain-figures",
    "complete_example",
]

IGNORE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "test",
    "tests",
    "plans",
}
IGNORE_FILE_NAMES = {".DS_Store"}
IGNORE_ROOT_FILE_NAMES = {"readme.md", "changelog.md"}
IGNORE_GLOBS = ("*.pyc", "*.pyo")

MESSAGES = {
    "en": {
        "python_too_old": "Python {current} is too old. Please use Python {required} or newer.",
        "start": "Starting bensz skills installation...",
        "sources": "Selected sources: {sources}",
        "target": "Installing to {label}: {root}",
        "download": "Downloading {name} from {url}",
        "download_done": "Downloaded {name}",
        "download_failed": "Failed to download {name}: {error}",
        "extract_failed": "Failed to extract {name}: {error}",
        "skills_missing": "No skills root found for {name} at path: {path}",
        "no_skills": "No installable skills found in: {root}",
        "removed_legacy": "Removed legacy skill: {path}",
        "skip_legacy_path": "Skipped legacy path that is not a symlink: {path}",
        "removed": "Removed existing skill: {path}",
        "installed": "Installed: {name}",
        "skipped": "Skipped unchanged: {name}",
        "ignored": "Ignored {count} non-production skill(s)",
        "manifest": "Manifest saved: {path}",
        "summary": "Summary: {installed} installed or updated, {skipped} unchanged, {ignored} ignored",
        "dry_run": "[dry-run] {message}",
        "unknown_source": "Unknown source id(s): {ids}",
        "cleanup": "Temporary files cleaned up.",
        "done": "Installation complete.",
    },
    "zh": {
        "python_too_old": "Python {current} 版本过低，请使用 Python {required} 或更新版本。",
        "start": "开始安装 bensz 技能...",
        "sources": "已选择源: {sources}",
        "target": "正在安装到 {label}: {root}",
        "download": "正在从 {url} 下载 {name}",
        "download_done": "下载完成: {name}",
        "download_failed": "下载失败: {name}: {error}",
        "extract_failed": "解压失败: {name}: {error}",
        "skills_missing": "未找到 {name} 的 skills 根目录: {path}",
        "no_skills": "未发现可安装技能: {root}",
        "removed_legacy": "已移除 legacy 技能: {path}",
        "skip_legacy_path": "跳过非软链接 legacy 路径: {path}",
        "removed": "已删除旧技能: {path}",
        "installed": "已安装: {name}",
        "skipped": "跳过未变化: {name}",
        "ignored": "已忽略 {count} 个非生产技能",
        "manifest": "安装清单已保存: {path}",
        "summary": "统计: 已安装或更新 {installed} 个，未变化 {skipped} 个，已忽略 {ignored} 个",
        "dry_run": "[dry-run] {message}",
        "unknown_source": "未知源 ID: {ids}",
        "cleanup": "临时文件已清理。",
        "done": "安装完成。",
    },
}


@dataclass(frozen=True)
class Target:
    label: str
    root: Path
    legacy_link: Path


@dataclass(frozen=True)
class Skill:
    name: str
    src: Path
    md5: str


@dataclass
class InstallResult:
    installed: int = 0
    skipped: int = 0
    ignored: int = 0
    messages: list[str] | None = None

    def __post_init__(self) -> None:
        if self.messages is None:
            self.messages = []


def tr(lang: str, key: str, **kwargs: object) -> str:
    return MESSAGES.get(lang, MESSAGES["en"])[key].format(**kwargs)


def ensure_python(lang: str) -> None:
    if sys.version_info < MIN_PYTHON:
        current = ".".join(str(part) for part in sys.version_info[:3])
        required = ".".join(str(part) for part in MIN_PYTHON)
        raise SystemExit(tr(lang, "python_too_old", current=current, required=required))


def stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def installation_root() -> Path:
    return Path.home().joinpath(*INSTALLATION_ROOT_PARTS)


def path_label(path: Path) -> str:
    try:
        return str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def print_msg(lang: str, key: str, dry_run: bool = False, **kwargs: object) -> None:
    message = tr(lang, key, **kwargs)
    if dry_run:
        message = tr(lang, "dry_run", message=message)
    print(message)


def should_ignore_rel_path(rel_path: Path) -> bool:
    if len(rel_path.parts) == 1 and rel_path.name.lower() in IGNORE_ROOT_FILE_NAMES:
        return True
    if any(part.startswith(".") for part in rel_path.parts):
        return True
    if any(part in IGNORE_DIR_NAMES for part in rel_path.parts):
        return True
    if rel_path.name in IGNORE_FILE_NAMES:
        return True
    if any(fnmatch.fnmatch(rel_path.name, pattern) for pattern in IGNORE_GLOBS):
        return True
    return False


def copytree_ignore(src_root: Path):
    def ignore(current_dir: str, names: list[str]) -> list[str]:
        current_path = Path(current_dir)
        ignored = []
        for name in names:
            try:
                rel_path = (current_path / name).relative_to(src_root)
            except ValueError:
                continue
            if should_ignore_rel_path(rel_path):
                ignored.append(name)
        return ignored

    return ignore


def calculate_md5(skill_dir: Path) -> str:
    hasher = hashlib.md5()
    for file_path in sorted(skill_dir.rglob("*")):
        if not file_path.is_file():
            continue
        rel_path = file_path.relative_to(skill_dir)
        if should_ignore_rel_path(rel_path):
            continue
        hasher.update(str(rel_path).encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(file_path.read_bytes())
    return hasher.hexdigest()


def installed_md5(dest_dir: Path, target: Target) -> str | None:
    manifest_file = dest_dir / f".skill-manifest.{target.label}.json"
    if manifest_file.exists():
        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            value = data.get("md5")
            return str(value) if value else None
        except (OSError, json.JSONDecodeError):
            pass
    if dest_dir.exists():
        try:
            return calculate_md5(dest_dir)
        except OSError:
            return None
    return None


def save_skill_manifest(dest_dir: Path, md5: str, source: str, target: Target) -> None:
    manifest_file = dest_dir / f".skill-manifest.{target.label}.json"
    data = {
        "md5": md5,
        "source": source,
        "installed_at": stamp(),
        "target": target.label,
    }
    manifest_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_category(skill_dir: Path) -> str | None:
    skill_md = skill_dir / "SKILL.md"
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        if line.startswith("category:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'").lower()
    return None


def skill_type(skill_dir: Path, skills_root: Path) -> str:
    category = parse_category(skill_dir)
    if category in {"auxiliary", "dev", "development"}:
        return "auxiliary"
    if category in {"test", "testing"}:
        return "test"
    if category in {"normal", "production"}:
        return "normal"

    rel_path = skill_dir.relative_to(skills_root)
    if any(part in {"test", "tests"} for part in rel_path.parts):
        return "test"
    name = skill_dir.name.lower()
    if re.match(r"^\d{8}_\d{6}$", name):
        return "test"
    if any(pattern in name for pattern in ("test-", "-test", "_test", "test_")):
        return "test"
    return "normal"


def looks_like_skills_root(root: Path) -> bool:
    try:
        if not root.exists() or not root.is_dir():
            return False
        return any(child.is_dir() and (child / "SKILL.md").is_file() for child in root.iterdir())
    except OSError:
        return False


def resolve_skills_root(repo_root: Path, skills_path: str) -> Path | None:
    raw_path = skills_path.strip()
    requested = repo_root if raw_path in {"", "."} else repo_root / raw_path
    if looks_like_skills_root(requested):
        return requested
    if requested != repo_root and looks_like_skills_root(repo_root):
        return repo_root
    return None


def discover_skills(skills_root: Path) -> tuple[list[Skill], int]:
    normal: list[Skill] = []
    ignored = 0
    for skill_dir in sorted(skills_root.iterdir()):
        if skill_dir.name.startswith(".") or not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").is_file():
            continue
        if skill_type(skill_dir, skills_root) != "normal":
            ignored += 1
            continue
        normal.append(Skill(name=skill_dir.name, src=skill_dir, md5=calculate_md5(skill_dir)))

    by_name: dict[str, list[Path]] = {}
    for skill in normal:
        by_name.setdefault(skill.name, []).append(skill.src)
    collisions = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    if collisions:
        details = "; ".join(f"{name}: {', '.join(str(p) for p in paths)}" for name, paths in collisions.items())
        raise RuntimeError(f"Duplicate skill directory names: {details}")
    return normal, ignored


def github_archive_url(repo_url: str, branch: str) -> str:
    parsed = urllib.parse.urlparse(repo_url)
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if parsed.netloc.lower() not in {"github.com", "www.github.com"} or len(parts) < 2:
        raise ValueError(f"Only GitHub repository URLs are supported: {repo_url}")
    owner = parts[0]
    repo = parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    branch_ref = urllib.parse.quote(branch, safe="/")
    return f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch_ref}.zip"


def download_file(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "bensz-skills-installer"})
    with urllib.request.urlopen(request, timeout=120) as response:
        with dest.open("wb") as out:
            shutil.copyfileobj(response, out)


def safe_extract_zip(zip_path: Path, dest_dir: Path) -> Path:
    dest_resolved = dest_dir.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        members = archive.infolist()
        for member in members:
            target = (dest_dir / member.filename).resolve()
            if target != dest_resolved and dest_resolved not in target.parents:
                raise RuntimeError(f"Unsafe zip path: {member.filename}")
        archive.extractall(dest_dir)

    top_dirs = [child for child in dest_dir.iterdir() if child.is_dir()]
    if len(top_dirs) == 1:
        return top_dirs[0]
    return dest_dir


def download_source(source: dict[str, str], temp_root: Path, lang: str) -> Path | None:
    name = source["name"]
    url = github_archive_url(source["url"], source["branch"])
    print_msg(lang, "download", name=name, url=url)
    source_dir = temp_root / source["id"]
    source_dir.mkdir(parents=True, exist_ok=True)
    zip_path = source_dir / "source.zip"
    try:
        download_file(url, zip_path)
        repo_root = safe_extract_zip(zip_path, source_dir / "extracted")
    except (OSError, urllib.error.URLError, zipfile.BadZipFile, RuntimeError) as exc:
        print_msg(lang, "download_failed", name=name, error=exc)
        return None
    print_msg(lang, "download_done", name=name)
    return resolve_skills_root(repo_root, source["skills_path"])


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def remove_existing(dest: Path, lang: str, dry_run: bool, result: InstallResult) -> None:
    if not dest.exists() and not dest.is_symlink():
        return
    print_msg(lang, "removed", dry_run=dry_run, path=dest)
    result.messages.append(f"remove existing: {dest}")
    if not dry_run:
        remove_path(dest)


def remove_legacy_skills(target: Target, active_names: set[str], lang: str, dry_run: bool, result: InstallResult) -> None:
    legacy_link = target.legacy_link
    if legacy_link.exists() or legacy_link.is_symlink():
        if legacy_link.is_symlink():
            print_msg(lang, "removed_legacy", dry_run=dry_run, path=legacy_link)
            result.messages.append(f"remove legacy symlink: {legacy_link}")
            if not dry_run:
                legacy_link.unlink()
        else:
            print_msg(lang, "skip_legacy_path", path=legacy_link)

    for name in LEGACY_SKILL_NAMES:
        if name in active_names:
            continue
        legacy_path = target.root / name
        if not legacy_path.exists() and not legacy_path.is_symlink():
            continue
        print_msg(lang, "removed_legacy", dry_run=dry_run, path=legacy_path)
        result.messages.append(f"remove legacy skill: {legacy_path}")
        if not dry_run:
            remove_path(legacy_path)


def install_skills(
    skills: list[Skill],
    ignored_count: int,
    target: Target,
    source_label: str,
    force: bool,
    dry_run: bool,
    lang: str,
) -> InstallResult:
    result = InstallResult(ignored=ignored_count)
    active_names = {skill.name for skill in skills}
    remove_legacy_skills(target, active_names, lang, dry_run, result)

    if not dry_run:
        target.root.mkdir(parents=True, exist_ok=True)

    for skill in skills:
        dest = target.root / skill.name
        current_md5 = None if force else installed_md5(dest, target)
        if current_md5 == skill.md5:
            result.skipped += 1
            print_msg(lang, "skipped", name=skill.name)
            continue

        remove_existing(dest, lang, dry_run, result)
        print_msg(lang, "installed", dry_run=dry_run, name=skill.name)
        result.messages.append(f"install: {skill.src} -> {dest}")
        if not dry_run:
            shutil.copytree(
                skill.src,
                dest,
                symlinks=False,
                dirs_exist_ok=False,
                ignore=copytree_ignore(skill.src),
            )
            save_skill_manifest(dest, skill.md5, source_label, target)
        result.installed += 1

    return result


def manifest_dir() -> Path:
    path = installation_root() / "manifests"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_run_manifest(records: list[dict[str, object]], dry_run: bool, lang: str) -> None:
    if dry_run:
        print(json.dumps({"runs": records}, ensure_ascii=False, indent=2))
        return
    path = manifest_dir() / f"install-manifest.{stamp()}.json"
    path.write_text(json.dumps({"runs": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print_msg(lang, "manifest", path=path_label(path))


def select_sources(source_ids: str | None) -> list[dict[str, str]]:
    if not source_ids:
        return DEFAULT_SOURCES
    wanted = {item.strip() for item in source_ids.split(",") if item.strip()}
    known = {source["id"] for source in DEFAULT_SOURCES}
    unknown = sorted(wanted - known)
    if unknown:
        raise ValueError(",".join(unknown))
    return [source for source in DEFAULT_SOURCES if source["id"] in wanted]


def build_targets(args: argparse.Namespace) -> list[Target]:
    install_codex = args.codex or (not args.codex and not args.claude)
    install_claude = args.claude or (not args.codex and not args.claude)
    home = Path.home()
    targets = []
    if install_codex:
        targets.append(Target("codex", home / ".codex" / "skills", home / ".codex" / "skills" / "pipeline-skills"))
    if install_claude:
        targets.append(Target("claude", home / ".claude" / "skills", home / ".claude" / "skills" / "pipeline-skills"))
    return targets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install bensz skills using only the Python standard library.",
    )
    parser.add_argument("--codex", action="store_true", help="Install to Codex only.")
    parser.add_argument("--claude", action="store_true", help="Install to Claude Code only.")
    parser.add_argument("--force", action="store_true", help="Reinstall even when MD5 is unchanged.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    parser.add_argument("--check", action="store_true", help="Alias for --dry-run.")
    parser.add_argument("--source", help="Comma-separated source ids. Available: general,research,anthropic-docs.")
    parser.add_argument("--lang", choices=["en", "zh"], default="en", help="Installer language. Default: en.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    lang = args.lang
    ensure_python(lang)
    dry_run = bool(args.dry_run or args.check)

    try:
        sources = select_sources(args.source)
    except ValueError as exc:
        print_msg(lang, "unknown_source", ids=exc)
        return 1

    targets = build_targets(args)
    print_msg(lang, "start")
    print_msg(lang, "sources", sources=", ".join(source["id"] for source in sources))

    total_installed = 0
    total_skipped = 0
    total_ignored = 0
    records: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="bensz-skills-install-") as tmp:
        temp_root = Path(tmp)
        for source in sources:
            try:
                skills_root = download_source(source, temp_root, lang)
            except ValueError as exc:
                print_msg(lang, "download_failed", name=source["name"], error=exc)
                continue

            if skills_root is None:
                print_msg(lang, "skills_missing", name=source["name"], path=source["skills_path"])
                continue

            skills, ignored = discover_skills(skills_root)
            if not skills:
                print_msg(lang, "no_skills", root=skills_root)
                continue

            total_ignored += ignored
            source_label = f"{source['id']} ({source['url']}@{source['branch']}:{source['skills_path']})"
            for target in targets:
                print()
                print_msg(lang, "target", label=target.label, root=target.root)
                result = install_skills(
                    skills=skills,
                    ignored_count=ignored,
                    target=target,
                    source_label=source_label,
                    force=args.force,
                    dry_run=dry_run,
                    lang=lang,
                )
                total_installed += result.installed
                total_skipped += result.skipped
                if result.ignored:
                    print_msg(lang, "ignored", count=result.ignored)
                records.append(
                    {
                        "source": source_label,
                        "target": target.label,
                        "target_root": str(target.root),
                        "installed_count": result.installed,
                        "skipped_count": result.skipped,
                        "ignored_count": result.ignored,
                        "messages": result.messages,
                    }
                )

    print()
    save_run_manifest(records, dry_run, lang)
    print_msg(lang, "cleanup")
    print_msg(lang, "summary", installed=total_installed, skipped=total_skipped, ignored=total_ignored)
    print_msg(lang, "done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
