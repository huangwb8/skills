from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from common import load_config, now_iso, read_text, sanitize_user_list, sanitize_user_text, skill_root, write_text


CANONICAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
FINGERPRINT_PATTERN = re.compile(r"^resolution_fingerprint:\s*([a-f0-9]{64})\s*$", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为已有 Bensz bug 追加不可覆盖的 resolution 记录。")
    parser.add_argument("--bug-dir", required=True, help="包含 bug-context.json 与 BUG_REPORT.md 的 bug 目录")
    parser.add_argument("--status", required=True, choices=("fixed", "duplicate"))
    parser.add_argument("--canonical-root-cause", required=True, help="稳定的 canonical 根因 ID")
    parser.add_argument("--fixed-version-or-commit", required=True)
    parser.add_argument("--verification", action="append", default=[], help="可重复传入的验证证据")
    parser.add_argument("--duplicate-of", help="重复记录指向的 canonical bug hash 或公开路径")
    parser.add_argument("--resolved-at", help="ISO 8601 时间；默认使用当前 UTC 时间")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def validated_bug_dir(path_text: str, config: dict[str, Any]) -> Path:
    path = Path(path_text).expanduser()
    if path.is_symlink():
        raise SystemExit(f"拒绝使用符号链接 bug 目录：{path}")
    path = path.resolve()
    if not path.is_dir():
        raise SystemExit(f"bug 目录不存在：{path}")
    required = (config["storage"]["context_filename"], config["storage"]["report_filename"])
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        raise SystemExit(f"bug 目录缺少原始证据文件：{', '.join(missing)}")
    return path


def validate_resolved_at(value: str | None) -> str:
    if not value:
        return now_iso()
    candidate = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise SystemExit("--resolved-at 必须是 ISO 8601 时间") from exc
    return value


def build_payload(args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any]:
    canonical_id = sanitize_user_text(args.canonical_root_cause, config)
    if not CANONICAL_ID_PATTERN.fullmatch(canonical_id):
        raise SystemExit("--canonical-root-cause 仅允许 3-128 位字母、数字、点、下划线、冒号或连字符")
    version = sanitize_user_text(args.fixed_version_or_commit, config)
    verification = sanitize_user_list(args.verification, config)
    duplicate_of = sanitize_user_text(args.duplicate_of, config) or None
    if not version:
        raise SystemExit("标记 resolved 必须提供 --fixed-version-or-commit")
    if not verification:
        raise SystemExit("标记 resolved 必须至少提供一条 --verification")
    if args.status == "duplicate" and not duplicate_of:
        raise SystemExit("status=duplicate 必须提供 --duplicate-of")
    return {
        "status": args.status,
        "canonical_root_cause": canonical_id,
        "fixed_version_or_commit": version,
        "verification": verification,
        "duplicate_of": duplicate_of,
    }


def payload_fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def render_resolution(payload: dict[str, Any], resolved_at: str, config: dict[str, Any]) -> str:
    template = read_text(skill_root() / config["templates"]["resolution"])
    verification_block = "\n".join(f"- {item}" for item in payload["verification"])
    return template.format(
        status=payload["status"],
        canonical_root_cause=payload["canonical_root_cause"],
        fixed_version_or_commit=payload["fixed_version_or_commit"],
        resolved_at=resolved_at,
        duplicate_of=payload["duplicate_of"] or "null",
        resolution_fingerprint=payload_fingerprint(payload),
        verification_block=verification_block,
    )


def main() -> None:
    args = parse_args()
    config = load_config()
    bug_dir = validated_bug_dir(args.bug_dir, config)
    payload = build_payload(args, config)
    resolved_at = validate_resolved_at(args.resolved_at)
    fingerprint = payload_fingerprint(payload)
    resolution_path = bug_dir / config["storage"]["resolution_filename"]
    action = "create"

    if resolution_path.exists():
        existing = read_text(resolution_path)
        match = FINGERPRINT_PATTERN.search(existing)
        if match and match.group(1) == fingerprint:
            action = "unchanged"
        else:
            raise SystemExit(
                f"resolution 已存在且内容不同，追加式协议拒绝覆盖：{resolution_path}"
            )
    elif not args.dry_run:
        write_text(resolution_path, render_resolution(payload, resolved_at, config))

    result = {
        "action": action,
        "dry_run": bool(args.dry_run),
        "resolution_path": str(resolution_path),
        "status": payload["status"],
        "canonical_root_cause": payload["canonical_root_cause"],
        "duplicate_of": payload["duplicate_of"],
    }
    if args.print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        prefix = "预计创建" if args.dry_run and action == "create" else ("无需变更" if action == "unchanged" else "已创建")
        print(f"{prefix}: {resolution_path}")


if __name__ == "__main__":
    main()
