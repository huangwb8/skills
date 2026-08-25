from __future__ import annotations

import argparse
import base64
import json
import subprocess
from typing import Any

from common import (
    bug_report_markdown,
    current_github_username,
    find_context_files,
    gh_auth_ok,
    load_config,
    now_iso,
    read_json,
    read_text,
    sanitized_local_context,
    sanitized_public_context,
    skill_root,
    skill_storage_root,
    slugify,
    validate_storage_root,
    write_json,
    write_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把本地收集的 bug 公开上报到 GitHub 仓库。")
    parser.add_argument("--bug-root")
    parser.add_argument("--skill-name")
    parser.add_argument("--repo-owner")
    parser.add_argument("--repo-name")
    parser.add_argument("--reporter-github")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def gh_api(
    endpoint: str,
    *,
    host: str,
    method: str = "GET",
    fields: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = ["gh", "api", endpoint]
    if host and host != "github.com":
        command.extend(["--hostname", host])
    if method != "GET":
        command.extend(["--method", method])
    for key, value in (fields or {}).items():
        command.extend(["-f", f"{key}={value}"])
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )


def remote_file_exists(owner: str, repo: str, path: str, host: str) -> bool:
    result = gh_api(f"repos/{owner}/{repo}/contents/{path}", host=host)
    return result.returncode == 0


def verify_remote_repo_access(owner: str, repo: str, host: str) -> None:
    result = gh_api(f"repos/{owner}/{repo}", host=host)
    if result.returncode != 0:
        raise SystemExit(
            f"无法访问远端仓库 {owner}/{repo}。\n"
            "请确认仓库存在、当前 `gh` 账号有权限，并且网络可用。"
        )


def upload_text_file(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    dry_run: bool,
    host: str,
) -> None:
    if dry_run:
        return
    payload = base64.b64encode(content.encode("utf-8")).decode("ascii")
    result = gh_api(
        f"repos/{owner}/{repo}/contents/{path}",
        host=host,
        method="PUT",
        fields={"message": message, "content": payload},
    )
    if result.returncode != 0:
        raise SystemExit(f"上传失败：{path}\n{result.stderr.strip()}")


def main() -> None:
    args = parse_args()
    config = load_config()
    if not gh_auth_ok():
        raise SystemExit("`gh` 未登录或不可用。请先执行 `gh auth login`，然后重试。")

    owner = args.repo_owner or config["github"]["owner"]
    repo = args.repo_name or config["github"]["repo"]
    host = config.get("github", {}).get("api_host") or "github.com"
    bug_root = skill_storage_root(config, args.bug_root)
    bug_root = validate_storage_root(bug_root)
    reporter_github = current_github_username(args.reporter_github)
    if not reporter_github:
        raise SystemExit("无法确定当前 GitHub 用户名。请先确认 `gh auth status` 可用。")
    verify_remote_repo_access(owner, repo, host)

    context_filename = config["storage"]["context_filename"]
    context_files = find_context_files(bug_root, context_filename)
    if args.skill_name:
        expected_skill = slugify(args.skill_name)
        context_files = [
            path
            for path in context_files
            if slugify(read_json(path)["skill"]["name"]) == expected_skill
        ]

    uploaded = 0
    would_upload = 0
    skipped = 0
    already_public = 0
    results: list[dict[str, Any]] = []
    template_path = skill_root() / config["templates"]["bug_report"]
    template_text = read_text(template_path)

    for context_path in context_files:
        context = sanitized_local_context(read_json(context_path), config)
        if not context.get("bug", {}).get("is_skill_design_defect", False):
            skipped += 1
            continue

        bug_hash = context["bug_hash"]
        skill_slug = slugify(context["skill"]["name"])
        remote_dir = f"{skill_slug}/{reporter_github}/{bug_hash}"
        remote_context_path = f"{remote_dir}/{config['storage']['context_filename']}"
        remote_report_path = f"{remote_dir}/{config['storage']['report_filename']}"

        tracking = context.setdefault("tracking", {})
        if not args.dry_run:
            tracking["public_reported"] = True
            tracking["public_repo"] = f"{owner}/{repo}"
            tracking["public_path"] = remote_dir
            tracking["reported_at"] = now_iso()
        context["reporter"]["github_username"] = reporter_github
        public_context = sanitized_public_context(
            context,
            config,
            placeholder=config["reporting"]["redacted_placeholder"],
        )
        markdown = bug_report_markdown(template_text, context, config)
        public_markdown = bug_report_markdown(template_text, public_context, config)
        report_path = context_path.parent / config["storage"]["report_filename"]
        if not args.dry_run:
            write_text(report_path, markdown)

        context_exists = remote_file_exists(owner, repo, remote_context_path, host)
        report_exists = remote_file_exists(owner, repo, remote_report_path, host)
        if context_exists and report_exists:
            already_public += 1
        else:
            would_upload += 1
            message = config["reporting"]["commit_message_template"].format(
                bug_hash=bug_hash,
                skill_name=context["skill"]["name"],
            )
            upload_text_file(
                owner,
                repo,
                remote_context_path,
                json.dumps(public_context, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                message,
                args.dry_run,
                host,
            )
            upload_text_file(
                owner,
                repo,
                remote_report_path,
                public_markdown,
                message,
                args.dry_run,
                host,
            )
            if not args.dry_run:
                uploaded += 1

        if not args.dry_run:
            write_json(context_path, context)
        results.append(
            {
                "bug_hash": bug_hash,
                "remote_dir": remote_dir,
                "uploaded": (not args.dry_run) and not (context_exists and report_exists),
                "would_upload": args.dry_run and not (context_exists and report_exists),
            }
        )

    summary = {
        "bug_root": str(bug_root),
        "repo": f"{owner}/{repo}",
        "reporter": reporter_github,
        "dry_run": args.dry_run,
        "uploaded": uploaded,
        "would_upload": would_upload,
        "already_public": already_public,
        "skipped": skipped,
        "total_scanned": len(context_files),
        "results": results,
    }
    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        if args.dry_run:
            print(
                f"扫描 {len(context_files)} 个本地 bug，预计新增公开 {would_upload} 个，"
                f"已存在 {already_public} 个，跳过 {skipped} 个。"
            )
        else:
            print(
                f"扫描 {len(context_files)} 个本地 bug，新增公开 {uploaded} 个，"
                f"已存在 {already_public} 个，跳过 {skipped} 个。"
            )
        print(f"远端仓库: https://{host}/{owner}/{repo}")


if __name__ == "__main__":
    main()
