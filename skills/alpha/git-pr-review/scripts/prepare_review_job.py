#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from common_config import get_skill_root, load_config


SCRIPT_PATH = Path(__file__)
SKILL_ROOT = get_skill_root(SCRIPT_PATH)
CONFIG = load_config(SKILL_ROOT)
DIRECTORIES = CONFIG["directories"]
FILES = CONFIG["files"]
OUTPUT = CONFIG["output"]
GOOD_PR_REFERENCE = SKILL_ROOT / "references" / "good-pr-standards.md"
PR_NUMBER_RE = re.compile(r"^(?:#|pr[-\s]?)?(\d+)$", re.IGNORECASE)


def sanitize(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text.strip())
    text = re.sub(r"_+", "_", text).strip("._-")
    return text or "unknown"


def validate_timestamp(timestamp: str) -> str:
    fmt = str(OUTPUT["timestamp_format"])
    try:
        datetime.strptime(timestamp, fmt)
    except ValueError as exc:
        raise ValueError(f"timestamp must match {fmt!r}: {timestamp}") from exc
    return timestamp


def parse_repo(repo: str) -> tuple[str, str, str]:
    repo = repo.strip()
    if repo.startswith(("http://", "https://")):
        parsed = urlparse(repo)
        if parsed.netloc not in {"github.com", "www.github.com"}:
            raise ValueError(f"Only github.com repositories are supported: {repo}")
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) != 2:
            raise ValueError(f"Repository URL must point to the repo root: {repo}")
        owner, name = parts[0], parts[1]
    else:
        parts = [p for p in repo.split("/") if p]
        if len(parts) != 2:
            raise ValueError("Repository must be a GitHub URL or owner/repo slug.")
        owner, name = parts[0], parts[1]
    repo_name = name.removesuffix(".git")
    if not owner or not repo_name:
        raise ValueError("Repository must include both owner and repo name.")
    repo_slug = sanitize(f"{owner}_{repo_name}")
    return owner, repo_name, repo_slug


def parse_pr(pr: str) -> tuple[str, int, tuple[str, str] | None]:
    pr = pr.strip()
    if pr.startswith(("http://", "https://")):
        parsed = urlparse(pr)
        if parsed.netloc not in {"github.com", "www.github.com"}:
            raise ValueError(f"Only github.com PR URLs are supported: {pr}")
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 4 and parts[2] == "pull" and parts[3].isdigit():
            number = int(parts[3])
            return f"pr-{number}", number, (parts[0], parts[1])
        raise ValueError(f"Could not parse PR number from URL: {pr}")

    match = PR_NUMBER_RE.fullmatch(pr)
    if not match:
        raise ValueError("PR must be a PR URL, '#123', '123', or 'pr-123'.")
    number = int(match.group(1))
    return f"pr-{number}", number, None


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def allocate_run_dir(workspace_root: Path, timestamp: str) -> tuple[Path, str]:
    candidate = workspace_root / timestamp
    if not candidate.exists():
        return candidate, timestamp
    for idx in range(2, 100):
        run_id = f"{timestamp}-{idx:02d}"
        candidate = workspace_root / run_id
        if not candidate.exists():
            return candidate, run_id
    raise RuntimeError(f"failed to allocate unique run directory under {workspace_root}")


def write_placeholder(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def build_good_pr_note() -> str:
    if not GOOD_PR_REFERENCE.exists():
        return "# Community Good PR Notes\n\n- 未找到内置参考 `references/good-pr-standards.md`，请手动补充。\n"
    source = GOOD_PR_REFERENCE.read_text(encoding="utf-8").strip()
    return (
        "# Community Good PR Notes\n\n"
        "以下内容由 skill 内置参考 `references/good-pr-standards.md` 预填充；"
        "默认优先使用这些标准，不必每次实时联网。\n\n"
        + source
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare an isolated workspace for git-pr-review.")
    parser.add_argument("--repo", required=True, help="GitHub repo URL or owner/repo")
    parser.add_argument("--pr", required=True, help="PR URL or PR number")
    parser.add_argument("--workspace-dir", default=str(DIRECTORIES["default_workspace"]), help="Workspace root")
    parser.add_argument("--report-dir", default=str(OUTPUT["default_report_dir"]), help="Final report directory")
    parser.add_argument("--timestamp", default="", help="Override timestamp")
    args = parser.parse_args()

    try:
        owner, repo_name, repo_slug = parse_repo(args.repo)
        pr_slug, pr_number, pr_repo = parse_pr(args.pr)
        if pr_repo is not None and tuple(pr_repo) != (owner, repo_name):
            raise ValueError(
                f"PR URL points to {pr_repo[0]}/{pr_repo[1]}, but --repo points to {owner}/{repo_name}."
            )
        fmt = str(OUTPUT["timestamp_format"])
        timestamp = validate_timestamp(args.timestamp) if args.timestamp else datetime.now().strftime(fmt)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    workspace_root = Path(args.workspace_dir).expanduser()
    report_root = Path(args.report_dir).expanduser()
    if not workspace_root.is_absolute():
        workspace_root = (Path.cwd() / workspace_root).resolve()
    else:
        workspace_root = workspace_root.resolve()
    if not report_root.is_absolute():
        report_root = (Path.cwd() / report_root).resolve()
    else:
        report_root = report_root.resolve()

    try:
        run_dir, run_id = allocate_run_dir(workspace_root, f"{DIRECTORIES['run_prefix']}{timestamp}")
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    raw_dir = run_dir / str(DIRECTORIES["raw"])
    notes_dir = run_dir / str(DIRECTORIES["notes"])
    evidence_dir = run_dir / str(DIRECTORIES["evidence"])
    logs_dir = run_dir / str(DIRECTORIES["logs"])

    for path in (workspace_root, run_dir, raw_dir, notes_dir, evidence_dir, logs_dir, report_root):
        ensure_dir(path)

    write_placeholder(
        raw_dir / str(FILES["raw_readme"]),
        "# Raw Inputs\n\n把 PR 元数据、diff、评论、CI 状态与关联 issue 保存到这个目录。\n",
    )
    write_placeholder(
        notes_dir / str(FILES["user_context_note"]),
        "# User Context\n\n- 用户已有判断：\n- 关注点：\n- 禁区或限制：\n",
    )
    write_placeholder(
        notes_dir / str(FILES["community_note"]),
        build_good_pr_note(),
    )
    write_placeholder(
        notes_dir / str(FILES["license_review_note"]),
        "# License Review\n\n- 是否涉及新依赖、复制代码、字体、图标、模板、数据或模型资源：\n- 发现的 license / notice：\n- 是否存在兼容性风险：\n- 建议动作：\n",
    )
    write_placeholder(
        evidence_dir / str(FILES["key_findings_note"]),
        "# Key Findings\n\n- 关键发现 1：\n- 关键发现 2：\n",
    )
    write_placeholder(
        evidence_dir / str(FILES["missing_items_note"]),
        "# Missing Items\n\n- 未获取材料：\n- 原因：\n- 对结论的影响：\n",
    )

    report_name = f"{OUTPUT['report_prefix']}_{repo_slug}_{pr_slug}_{run_id}{OUTPUT['report_extension']}"
    manifest_path = run_dir / str(FILES["manifest_name"])
    manifest = {
        "generated_at": timestamp,
        "run_id": run_id,
        "repo": {
            "input": args.repo,
            "owner": owner,
            "name": repo_name,
            "repo_slug": repo_slug,
            "skill_version": str(CONFIG["skill_info"]["version"]),
        },
        "pull_request": {
            "input": args.pr,
            "pr_slug": pr_slug,
            "number": pr_number,
            "url_repo": list(pr_repo) if pr_repo is not None else None,
        },
        "paths": {
            "workspace_root": str(workspace_root),
            "run_dir": str(run_dir),
            "raw_dir": str(raw_dir),
            "notes_dir": str(notes_dir),
            "evidence_dir": str(evidence_dir),
            "logs_dir": str(logs_dir),
            "report_dir": str(report_root),
            "report_path": str(report_root / report_name),
        },
        "files": {
            "manifest_name": str(FILES["manifest_name"]),
            "manifest_path": str(manifest_path),
            "raw_readme": str(raw_dir / str(FILES["raw_readme"])),
            "user_context_note": str(notes_dir / str(FILES["user_context_note"])),
            "community_note": str(notes_dir / str(FILES["community_note"])),
            "license_review_note": str(notes_dir / str(FILES["license_review_note"])),
            "key_findings_note": str(evidence_dir / str(FILES["key_findings_note"])),
            "missing_items_note": str(evidence_dir / str(FILES["missing_items_note"])),
        },
        "policy": {
            "read_only": True,
            "default_hidden_workspace": args.workspace_dir == str(DIRECTORIES["default_workspace"]),
            "must_keep_intermediate_inside_workspace": True,
            "required_report_sections": list(OUTPUT["required_sections"]),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "manifest": str(manifest_path),
        "run_dir": str(run_dir),
        "report_path": str(report_root / report_name),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
