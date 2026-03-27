from __future__ import annotations

import argparse

from common import (
    add_common_collection_arguments,
    bug_report_markdown,
    build_bug_directory,
    compute_bug_hash,
    current_github_username,
    deduplication_payload,
    detect_device,
    detect_os_details,
    detect_runtime,
    detect_software_versions,
    load_config,
    merge_unique,
    now_iso,
    parse_software_pairs,
    read_json,
    read_text,
    reporter_folder_name,
    sanitize_user_list,
    sanitize_user_text,
    sanitized_local_context,
    skill_root,
    skill_storage_root,
    validate_storage_root,
    write_json,
    write_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="记录 Bensz skills 的设计缺陷 bug。")
    add_common_collection_arguments(parser)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()
    root = skill_storage_root(config, args.bug_root)
    root = validate_storage_root(root)
    github_username = current_github_username(args.reporter_github)
    reporter_display = github_username or config["defaults"]["anonymous_reporter"]
    reporter_folder = reporter_folder_name(config, github_username)

    skill_name = sanitize_user_text(args.skill_name, config)
    skill_author = sanitize_user_text(args.skill_author, config)
    bug_summary = sanitize_user_text(args.bug_summary, config)
    expected_behavior = sanitize_user_text(args.expected_behavior, config)
    actual_behavior = sanitize_user_text(args.actual_behavior, config)
    reproduction_steps = sanitize_user_list(args.reproduction_step, config)
    evidence = sanitize_user_list(args.evidence, config)
    workaround = sanitize_user_text(args.workaround, config) or None
    additional_note = sanitize_user_text(args.additional_note, config) or None
    severity = sanitize_user_text(args.severity, config) or config["defaults"]["severity"]
    skill_source_path = sanitize_user_text(args.skill_source_path, config) or None
    skill_source_repo = sanitize_user_text(args.skill_source_repo, config) or None

    software_overrides = parse_software_pairs(args.software)
    environment = {
        "device": detect_device(config, args.device_type or config["defaults"]["device_type"]),
        "os": detect_os_details(),
        "runtime": detect_runtime(config, args.agent_runtime or config["defaults"]["agent_runtime"]),
        "software_versions": detect_software_versions(config, software_overrides),
    }

    fingerprint_payload = deduplication_payload(
        config=config,
        skill_name=skill_name,
        skill_author=skill_author,
        summary=bug_summary,
        expected_behavior=expected_behavior,
        actual_behavior=actual_behavior,
        environment=environment,
    )
    bug_hash = compute_bug_hash(fingerprint_payload, config["hashing"]["algorithm"])
    bug_dir = build_bug_directory(config, root, skill_name, reporter_folder, bug_hash)
    context_path = bug_dir / config["storage"]["context_filename"]
    report_path = bug_dir / config["storage"]["report_filename"]

    now = now_iso()
    if context_path.exists():
        context = sanitized_local_context(read_json(context_path), config)
        tracking = context.setdefault("tracking", {})
        tracking["occurrence_count"] = int(tracking.get("occurrence_count", 1)) + 1
        tracking["last_seen_at"] = now
        context["bug"]["evidence"] = merge_unique(context["bug"].get("evidence", []), evidence)
        context["bug"]["reproduction_steps"] = merge_unique(
            context["bug"].get("reproduction_steps", []),
            reproduction_steps,
        )
        if workaround:
            context["bug"]["workaround"] = workaround
        if additional_note:
            context["bug"]["additional_notes"] = additional_note
        if github_username:
            context["reporter"]["github_username"] = github_username
    else:
        context = {
            "schema_version": config["defaults"]["schema_version"],
            "bug_hash": bug_hash,
            "skill": {
                "name": skill_name,
                "author": skill_author,
                "source_path": skill_source_path,
                "source_repo": skill_source_repo,
            },
            "reporter": {
                "display_name": reporter_display,
                "github_username": github_username,
                "local_username": None,
            },
            "bug": {
                "summary": bug_summary,
                "severity": severity,
                "expected_behavior": expected_behavior,
                "actual_behavior": actual_behavior,
                "reproduction_steps": reproduction_steps,
                "evidence": evidence,
                "workaround": workaround,
                "impact": config["defaults"]["impact_text"],
                "additional_notes": additional_note,
                "is_skill_design_defect": True,
            },
            "environment": environment,
            "tracking": {
                "collected_at": now,
                "first_seen_at": now,
                "last_seen_at": now,
                "occurrence_count": 1,
                "public_reported": False,
                "public_repo": None,
                "public_path": None,
                "reported_at": None,
                "local_path": None,
            },
            "deduplication": {
                "hash_algorithm": config["hashing"]["algorithm"],
                "hash_version": config["hashing"]["version"],
                "fingerprint_payload": fingerprint_payload,
            },
        }

    context = sanitized_local_context(context, config)
    template_path = skill_root() / config["templates"]["bug_report"]
    markdown = bug_report_markdown(read_text(template_path), context, config)
    write_json(context_path, context)
    write_text(report_path, markdown)

    result = {
        "bug_hash": bug_hash,
        "bug_dir": str(bug_dir),
        "context_path": str(context_path),
        "report_path": str(report_path),
        "occurrence_count": context["tracking"]["occurrence_count"],
        "public_reported": context["tracking"]["public_reported"],
    }
    if args.print_json:
        import json

        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"已记录 bug: {bug_hash}")
        print(f"目录: {bug_dir}")


if __name__ == "__main__":
    main()
