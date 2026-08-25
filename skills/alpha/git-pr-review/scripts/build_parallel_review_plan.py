#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import shutil
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

from common_config import get_skill_root, load_config


SCRIPT_PATH = Path(__file__)
SKILL_ROOT = get_skill_root(SCRIPT_PATH)
CONFIG = load_config(SKILL_ROOT)
DIRECTORIES_CFG = CONFIG["directories"]
PARALLEL_CFG = CONFIG["parallel_review"]
FILES_CFG = CONFIG["files"]
DEPENDENCIES_CFG = CONFIG.get("dependencies") or {}
REVIEW_POLICY = CONFIG.get("review_policy") or {}
SNAPSHOT_SOURCES = (
    ("raw_dir", str(DIRECTORIES_CFG["raw"])),
    ("notes_dir", str(DIRECTORIES_CFG["notes"])),
    ("evidence_dir", str(DIRECTORIES_CFG["evidence"])),
)


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        _ensure_dir(dst.parent)
        shutil.copy2(src, dst)


def _digest_tree(root: Path) -> str:
    digest = hashlib.md5()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _resolve_parallel_vibe_script() -> Path:
    configured = str(DEPENDENCIES_CFG.get("parallel_vibe_script") or "").strip()
    if not configured:
        raise ValueError("config.dependencies.parallel_vibe_script is required")
    candidate = Path(configured).expanduser()
    if not candidate.is_absolute():
        candidate = (SKILL_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.exists() or not candidate.is_file():
        raise ValueError(f"parallel-vibe runner script not found: {candidate}")
    return candidate


def _result_template_text() -> str:
    sections = [str(item) for item in (PARALLEL_CFG.get("required_result_sections") or [])]
    if not sections:
        sections = [
            "# Independent PR Review",
            "## Final Call",
            "## Problem Understanding",
            "## Strengths",
            "## Limitations",
            "## Security Review",
            "## License Review",
            "## Good PR Criteria Comparison",
            "## Key Evidence",
            "## Evidence Gaps",
            "## Suggested Disposition",
        ]
    recommendations = " / ".join(str(item) for item in (REVIEW_POLICY.get("final_recommendations") or []))
    risks = " / ".join(str(item) for item in (REVIEW_POLICY.get("risk_levels") or []))
    confidences = " / ".join(str(item) for item in (PARALLEL_CFG.get("confidence_levels") or ["High", "Medium", "Low"]))

    lines: list[str] = [sections[0], ""]
    for section in sections[1:]:
        lines.append(section)
        if section == "## Final Call":
            lines.extend(
                [
                    f"- Recommendation: {recommendations}",
                    f"- Risk Level: {risks}",
                    f"- Confidence: {confidences}",
                ]
            )
        else:
            lines.append("- ...")
        lines.append("")
    return "\n".join(lines).rstrip()


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    return payload


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"manifest missing object: {key}")
    return value


def _resolve_path(value: Any, *, field_name: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"manifest missing path: {field_name}")
    return Path(value).expanduser().resolve()


def _validate_manifest(manifest: dict[str, Any]) -> tuple[Path, dict[str, Path]]:
    repo = _require_mapping(manifest, "repo")
    pull_request = _require_mapping(manifest, "pull_request")
    if not str(repo.get("owner") or "").strip() or not str(repo.get("name") or "").strip():
        raise ValueError("manifest.repo must include owner and name")
    if not str(pull_request.get("input") or pull_request.get("pr_slug") or "").strip():
        raise ValueError("manifest.pull_request must include input or pr_slug")

    paths = _require_mapping(manifest, "paths")
    run_dir = _resolve_path(paths.get("run_dir"), field_name="paths.run_dir")
    if not run_dir.exists() or not run_dir.is_dir():
        raise ValueError(f"manifest paths.run_dir does not exist: {run_dir}")

    resolved: dict[str, Path] = {"run_dir": run_dir}
    for key, _ in SNAPSHOT_SOURCES:
        current = _resolve_path(paths.get(key), field_name=f"paths.{key}")
        if not current.exists() or not current.is_dir():
            raise ValueError(f"manifest {key} does not exist: {current}")
        try:
            current.relative_to(run_dir)
        except ValueError as exc:
            raise ValueError(f"manifest {key} must stay inside run_dir: {current}") from exc
        resolved[key] = current
    return run_dir, resolved


def _review_prompt(*, thread_id: str, idx: int, total: int, repo: str, pr_ref: str, focus: str, extra: str) -> str:
    extra_block = f"\n补充指示：\n{extra.strip()}\n" if extra.strip() else ""
    result_template = _result_template_text()
    return dedent(
        f"""
        你正在执行一次 GitHub Pull Request 的独立评审。

        这是第 {idx}/{total} 个独立评审 thread，thread_id={thread_id}。
        你的任务不是参考其他 thread，而是基于当前 workspace 中提供的材料，独立完成一次完整 PR 审查。

        目标仓库：{repo}
        目标 PR：{pr_ref}
        本 thread 的次级关注焦点：{focus}
        {extra_block}
        你必须遵守以下要求：
        - 只能基于当前 workspace 中已有的 `manifest.json`、`raw/`、`notes/`、`evidence/` 材料进行判断。
        - 不要假设你能看到其他 thread 的结果。
        - 不要修改原始证据文件；只在当前工作区根目录写出 `RESULT.md`。
        - 如果材料不足，要明确写出“证据不足”与它对结论的影响。
        - 如果 PR 涉及依赖、复制的第三方代码、字体、图标、模板、数据或许可证文件，必须显式给出 license / 合规判断。
        - 优先使用 workspace 中 `notes/community_good_pr.md` 的内置“好 PR”标准。
        - 只有用户明确要求最新口径、指定特殊社区规范，或你判断当前内置标准不足时，才额外联网补充来源；如补充了，必须在 RESULT.md 里说明。

        `RESULT.md` 必须使用以下结构：

        {result_template}
        """
    ).strip() + "\n"


def _build_plan(
    *,
    manifest: dict[str, Any],
    review_count: int,
    extra_instructions: str,
    review_runner_type: str,
    review_runner_profile: str,
) -> dict[str, Any]:
    thread_width = int(PARALLEL_CFG["thread_id_width"])
    repo = manifest["repo"]
    pr = manifest["pull_request"]
    repo_ref = f"{repo['owner']}/{repo['name']}"
    pr_ref = str(pr.get("input") or pr.get("pr_slug") or pr.get("number") or "")
    focuses = list(PARALLEL_CFG.get("review_focuses") or [])
    threads: list[dict[str, Any]] = []

    for idx in range(1, review_count + 1):
        thread_id = str(idx).zfill(thread_width)
        focus = focuses[(idx - 1) % len(focuses)] if focuses else "完整独立评审"
        threads.append(
            {
                "thread_id": thread_id,
                "title": f"Independent Review {idx}",
                "runner": {
                    "type": review_runner_type,
                    "profile": review_runner_profile,
                    "model": "",
                    "args": [],
                },
                "prompt": _review_prompt(
                    thread_id=thread_id,
                    idx=idx,
                    total=review_count,
                    repo=repo_ref,
                    pr_ref=pr_ref,
                    focus=focus,
                    extra=extra_instructions,
                ),
            }
        )

    synthesis_cfg = PARALLEL_CFG.get("synthesis") or {}
    synthesis_runner = synthesis_cfg.get("runner") or {"type": "claude", "profile": "deep"}
    return {
        "plan_version": 1,
        "prompt": f"Independent PR review for {repo_ref} {pr_ref}",
        "threads": threads,
        "synthesis": {
            "enabled": bool(synthesis_cfg.get("enabled", False)),
            "runner": {
                "type": str(synthesis_runner.get("type") or "claude"),
                "profile": str(synthesis_runner.get("profile") or "deep"),
                "model": "",
                "args": [],
            },
            "prompt": "请综合多份独立 PR 审查结果，生成一份最终决策建议。",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a parallel-vibe plan for independent git-pr-review runs.")
    parser.add_argument("--manifest", required=True, help="Path to git-pr-review manifest.json")
    parser.add_argument("--n", type=int, default=int(PARALLEL_CFG["default_review_count"]), help="Independent review count")
    parser.add_argument("--extra-instructions", default="", help="Extra instructions passed to all independent reviewers")
    parser.add_argument(
        "--review-runner-type",
        default=str(PARALLEL_CFG["review_runner"]["type"]),
        help="Runner type for independent reviewers (default from config.yaml)",
    )
    parser.add_argument(
        "--review-runner-profile",
        default=str(PARALLEL_CFG["review_runner"]["profile"]),
        help="Runner profile for independent reviewers (default from config.yaml)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        return fail(f"manifest not found: {manifest_path}")

    review_count = int(args.n)
    if review_count < int(PARALLEL_CFG["min_review_count"]) or review_count > int(PARALLEL_CFG["max_review_count"]):
        return fail(
            f"--n must be within [{PARALLEL_CFG['min_review_count']}, {PARALLEL_CFG['max_review_count']}]: {review_count}"
        )

    try:
        manifest = _load_manifest(manifest_path)
        run_dir, manifest_paths = _validate_manifest(manifest)
    except ValueError as exc:
        return fail(str(exc))

    parallel_root = run_dir / str(PARALLEL_CFG["workspace_dir"])
    input_snapshot = parallel_root / str(PARALLEL_CFG["input_snapshot_dir"])
    parallel_out_dir = parallel_root / str(PARALLEL_CFG["parallel_out_dir"])
    plan_path = parallel_root / str(PARALLEL_CFG["plan_filename"])
    plan_md_path = parallel_root / str(PARALLEL_CFG["plan_markdown"])
    job_path = parallel_root / str(PARALLEL_CFG["job_manifest_name"])
    aggregate_md_path = parallel_root / str(PARALLEL_CFG["aggregate_markdown"])
    aggregate_json_path = parallel_root / str(PARALLEL_CFG["aggregate_json"])

    _ensure_dir(parallel_root)
    _ensure_dir(parallel_out_dir)
    if input_snapshot.exists():
        shutil.rmtree(input_snapshot)
    _ensure_dir(input_snapshot)

    _copy_if_exists(manifest_path, input_snapshot / str(FILES_CFG["manifest_name"]))
    for path_key, dest_dirname in SNAPSHOT_SOURCES:
        _copy_if_exists(manifest_paths[path_key], input_snapshot / dest_dirname)

    snapshot_fingerprint = _digest_tree(input_snapshot)
    plan = _build_plan(
        manifest=manifest,
        review_count=review_count,
        extra_instructions=str(args.extra_instructions or ""),
        review_runner_type=str(args.review_runner_type or PARALLEL_CFG["review_runner"]["type"]),
        review_runner_profile=str(args.review_runner_profile or PARALLEL_CFG["review_runner"]["profile"]),
    )
    plan_bytes = json.dumps(plan, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    plan_path.write_bytes(plan_bytes)
    project_id = hashlib.md5(plan_bytes + snapshot_fingerprint.encode("utf-8")).hexdigest()
    project_root = parallel_out_dir / ".bensz-api" / "skills" / "parallel-vibe" / project_id
    try:
        parallel_vibe_script = _resolve_parallel_vibe_script()
    except ValueError as exc:
        return fail(str(exc))

    command = " ".join(
        [
            "python3",
            shlex.quote(str(parallel_vibe_script)),
            "--plan-file",
            shlex.quote(str(plan_path)),
            "--src-dir",
            shlex.quote(str(input_snapshot)),
            "--out-dir",
            shlex.quote(str(parallel_out_dir)),
            "--project-id",
            shlex.quote(project_id),
        ]
    )
    plan_md_path.write_text(
        dedent(
            f"""
            # Parallel Independent Review Plan

            - Review count: {review_count}
            - Manifest: `{manifest_path}`
            - Input snapshot: `{input_snapshot}`
            - Input snapshot fingerprint: `{snapshot_fingerprint}`
            - Parallel out dir: `{parallel_out_dir}`
            - Parallel runner script: `{parallel_vibe_script}`
            - Expected project root: `{project_root}`
            - Aggregate markdown: `{aggregate_md_path}`
            - Aggregate json: `{aggregate_json_path}`
            - Recommended command: `{command}`
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    job = {
        "review_count": review_count,
        "manifest": str(manifest_path),
        "run_dir": str(run_dir),
        "parallel_root": str(parallel_root),
        "input_snapshot": str(input_snapshot),
        "input_snapshot_fingerprint": snapshot_fingerprint,
        "parallel_out_dir": str(parallel_out_dir),
        "parallel_vibe_script": str(parallel_vibe_script),
        "plan_file": str(plan_path),
        "plan_markdown": str(plan_md_path),
        "project_id": project_id,
        "project_root": str(project_root),
        "aggregate_markdown": str(aggregate_md_path),
        "aggregate_json": str(aggregate_json_path),
        "recommended_command": command,
    }
    job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(job, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
