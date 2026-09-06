#!/usr/bin/env python3
"""Fast remote skill version checker and updater.

Only remote installation is affected. Local-source installation remains owned by
install.py and keeps its existing MD5-based behavior.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_ROOT / "config.yaml"
DEFAULT_SOURCE_FILTER = "huangwb8"
TARGETS = {"codex": Path.home() / ".codex" / "skills", "claude": Path.home() / ".claude" / "skills"}


@dataclass(frozen=True)
class RemoteSkill:
    source: dict[str, str]
    name: str
    version: tuple[int, ...]
    remote_path: str


def parse_version(value: str | None) -> tuple[int, ...] | None:
    """Parse numeric dotted versions without adding a runtime dependency."""
    if not value:
        return None
    match = re.fullmatch(r"\s*v?(\d+(?:\.\d+)*)\s*", value)
    return tuple(int(part) for part in match.group(1).split(".")) if match else None


def version_is_newer(remote: tuple[int, ...], local: tuple[int, ...] | None) -> bool:
    if local is None:
        return True
    width = max(len(remote), len(local))
    return (remote + (0,) * (width - len(remote))) > (local + (0,) * (width - len(local)))


def _config_value(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}:\s*[\"']?([^\"'\n#]+?)[\"']?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def load_sources(config_path: Path = CONFIG_PATH) -> list[dict[str, str]]:
    """Read the small remote_sources contract without requiring PyYAML."""
    text = config_path.read_text(encoding="utf-8")
    sources: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_sources = False
    for line in text.splitlines():
        if line.strip() == "remote_sources:":
            in_sources = True
            continue
        if not in_sources:
            continue
        if line and not line[0].isspace() and line.strip().endswith(":"):
            break
        item = re.match(r"^\s*-\s+id:\s*[\"']?([^\"'\n]+?)[\"']?\s*$", line)
        if item:
            if current and current.get("url"):
                sources.append(current)
            current = {"id": item.group(1).strip()}
            continue
        if current:
            field = re.match(r"^\s+(url|branch|skills_path|name):\s*[\"']?([^\"'\n]+?)[\"']?\s*$", line)
            if field:
                current[field.group(1)] = field.group(2).strip()
    if current and current.get("url"):
        sources.append(current)
    return sources


def github_tree(source: dict[str, str]) -> list[str]:
    parsed = urllib.parse.urlparse(source["url"])
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.lower() != "github.com" or len(parts) < 2:
        raise ValueError(f"unsupported remote source: {source['url']}")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    branch = urllib.parse.quote(source.get("branch", "main"), safe="")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    request = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json", "User-Agent": "bensz-skill-updater"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
        return [item["path"] for item in payload.get("tree", []) if item.get("type") == "blob"]
    except urllib.error.HTTPError:
        # GitHub's unauthenticated API is rate-limited. Git's protocol is the
        # authoritative fallback and avoids a second API dependency.
        with tempfile.TemporaryDirectory(prefix="bensz-skill-tree-") as temp:
            repo = Path(temp) / "repo"
            subprocess.run(
                ["git", "clone", "--depth", "1", "--filter=blob:none", "--no-checkout",
                 "--branch", source.get("branch", "main"), source["url"], str(repo)],
                check=True, capture_output=True, text=True, timeout=120,
            )
            result = subprocess.run(
                ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", "HEAD"],
                check=True, capture_output=True, text=True, timeout=30,
            )
            return result.stdout.splitlines()


def raw_url(source: dict[str, str], path: str) -> str:
    parsed = urllib.parse.urlparse(source["url"])
    parts = [part for part in parsed.path.split("/") if part]
    owner, repo = parts[0], parts[1].removesuffix(".git")
    branch = urllib.parse.quote(source.get("branch", "main"), safe="")
    quoted_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{quoted_path}"


def mirror_raw_url(source: dict[str, str], path: str) -> str | None:
    mirror = source.get("mirror_url", "").rstrip("/")
    if not mirror:
        return None
    return f"{mirror}/raw/{source.get('branch', 'main')}/{path}"


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "bensz-skill-updater"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def fetch_preferred_text(source: dict[str, str], path: str) -> str:
    """Use a configured mirror first; fall back to GitHub on any mirror error."""
    mirror = mirror_raw_url(source, path)
    if mirror:
        try:
            return fetch_text(mirror)
        except Exception:
            pass
    return fetch_text(raw_url(source, path))


def _fetch_version(source: dict[str, str], path: str) -> tuple[str, tuple[int, ...] | None]:
    text = fetch_preferred_text(source, path)
    return path, parse_version(_config_value(text, "version"))


def discover_remote_skills(source: dict[str, str], tree: list[str] | None = None) -> list[RemoteSkill]:
    root = source.get("skills_path", "skills").strip("/")
    prefix = f"{root}/" if root and root != "." else ""
    paths = tree if tree is not None else github_tree(source)
    result: list[RemoteSkill] = []
    for path in paths:
        if not path.startswith(prefix) or not path.endswith("/config.yaml"):
            continue
        relative = path[len(prefix):]
        parts = relative.split("/")
        if len(parts) != 2 or parts[1] != "config.yaml":
            continue
        name = parts[0]
        version = None
        try:
            version = parse_version(_config_value(fetch_preferred_text(source, path), "version"))
        except Exception:
            continue
        if version is not None:
            result.append(RemoteSkill(source, name, version, path))
    return result


def local_version(name: str, target_roots: list[Path]) -> tuple[int, ...] | None:
    versions: list[tuple[int, ...]] = []
    for root in target_roots:
        config = root / name / "config.yaml"
        if config.is_file():
            version = parse_version(_config_value(config.read_text(encoding="utf-8"), "version"))
            if version is not None:
                versions.append(version)
    return min(versions) if versions else None


def installer_path() -> Path:
    candidates = [root / "install-bensz-skills" / "scripts" / "install.py" for root in TARGETS.values()]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return SCRIPT_DIR / "install.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check and update newer versions from selected remote skill sources.")
    parser.add_argument("--source-contains", action="append", default=None, help="Only sources whose id/name/url contains this string; repeatable.")
    parser.add_argument("--all-sources", action="store_true", help="Disable the default source substring filter.")
    parser.add_argument("--skill", action="append", default=[], help="Only check these skill names; repeatable or comma-separated.")
    parser.add_argument("--check-only", action="store_true", help="Report newer skills without installing them.")
    parser.add_argument("--codex", action="store_true", help="Compare Codex installation only.")
    parser.add_argument("--claude", action="store_true", help="Compare Claude Code installation only.")
    args = parser.parse_args(argv)
    targets = [TARGETS[label] for label, selected in (("codex", args.codex), ("claude", args.claude)) if selected] or list(TARGETS.values())
    filters = [item.lower() for item in (args.source_contains or [DEFAULT_SOURCE_FILTER])]
    requested = {name.strip() for value in args.skill for name in value.split(",") if name.strip()}
    newer: dict[str, list[str]] = {}
    for source in load_sources():
        haystack = " ".join(source.get(key, "") for key in ("id", "name", "url")).lower()
        if not args.all_sources and not any(value in haystack for value in filters):
            continue
        try:
            tree = github_tree(source)
            # Fetch all version manifests concurrently: network latency, not CPU,
            # dominates this check. The tree itself remains sourced from GitHub.
            root = source.get("skills_path", "skills").strip("/")
            prefix = f"{root}/" if root and root != "." else ""
            candidates = []
            for path in tree:
                if path.startswith(prefix) and path.endswith("/config.yaml"):
                    relative = path[len(prefix):].split("/")
                    if len(relative) == 2 and relative[1] == "config.yaml":
                        candidates.append(path)
            skills = []
            with ThreadPoolExecutor(max_workers=min(16, max(1, len(candidates)))) as pool:
                for path, version in pool.map(lambda item: _fetch_version(source, item), candidates):
                    if version is not None:
                        skills.append(RemoteSkill(source, path[len(prefix):].split("/")[0], version, path))
        except Exception as exc:
            print(f"[WARN] {source.get('id', 'unknown')}: {exc}", file=sys.stderr)
            continue
        for skill in skills:
            if requested and skill.name not in requested:
                continue
            current = local_version(skill.name, targets)
            if version_is_newer(skill.version, current):
                newer.setdefault(skill.source["id"], []).append(skill.name)
                print(f"[UPDATE] {skill.name}: local {current or 'missing'} -> remote {'.'.join(map(str, skill.version))}")
    if not newer or args.check_only:
        return 0
    command = [sys.executable, str(installer_path()), "--remote", "--auto"]
    for source_id, names in newer.items():
        command.append(f"--{source_id}")
        for name in sorted(set(names)):
            command.extend(["--skill", name])
    if args.codex:
        command.append("--codex")
    elif args.claude:
        command.append("--claude")
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
