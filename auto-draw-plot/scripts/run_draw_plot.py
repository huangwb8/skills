#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from common import (
    copy_file,
    ensure_dir,
    expand_path,
    join_lines,
    load_config,
    read_text,
    sha256_file,
    write_json,
    write_text,
)
from evaluate_image import evaluate_image, heuristic_evaluation
from generate_image import generate_image
from image_provider_client import ImageProviderConfig, health_check_image_provider
from init_workspace import init_workspace
from modes import DrawMode, mode_prompt_lines, resolve_mode
from build_parallel_plan import build_parallel_plan as create_parallel_plan


def build_round_prompt(
    *,
    request_text: str,
    round_index: int,
    max_rounds: int,
    prior_rounds: List[Dict[str, Any]],
    remote_env: Optional[Path],
    prompt_dir: Path,
    mode: DrawMode,
) -> Dict[str, Any]:
    cfg = load_config()
    gen_cfg = cfg.get("generation", {}) or {}
    guardrails = gen_cfg.get("prompt_guardrails", []) or []

    feedback_lines: List[str] = []
    if prior_rounds:
        prev_round = prior_rounds[-1]
        evaluation = prev_round.get("evaluation", {}) or {}
        feedback_lines.extend(
            [
                f"- 上一轮得分：{evaluation.get('score', 0)}",
                f"- 上一轮总结：{evaluation.get('summary', '')}",
            ]
        )
        for item in (evaluation.get("must_fix") or [])[:5]:
            feedback_lines.append(f"- 必须修复：{item}")
        for item in (evaluation.get("prompt_patch") or [])[:6]:
            feedback_lines.append(f"- Prompt 增量：{item}")

    planner_lines = [
        mode.planner_role,
        "请把用户需求转成可直接发送给图片生成模型的高质量 prompt。",
        "请输出原始 JSON，不要加 Markdown。",
        "JSON schema:",
        "{",
        '  "image_prompt": "可直接发送给图片模型的完整 prompt",',
        '  "negative_prompt": ["尽量避免的内容"],',
        '  "focus_points": ["本轮重点"],',
        '  "reasoning": "本轮为什么这样写 prompt"',
        "}",
        "",
        f"当前轮次：{round_index}/{max_rounds}",
        "",
        "用户需求：",
        request_text.strip(),
        "",
        *mode_prompt_lines(mode),
        "",
        "硬性护栏：",
        *[f"- {line}" for line in guardrails],
    ]
    if prior_rounds:
        planner_lines.extend(
            [
                "",
                "本轮生成方式：上一轮 output.png 会作为第一张参考图提供给图片模型；请基于它做 image-to-image 微调。",
                "请尽量保留上一轮已经正确的主体、布局、配色和文字，只针对反馈问题做局部优化；除非反馈明确要求重构，不要从零重画。",
            ]
        )
    if feedback_lines:
        planner_lines.extend(["", "上一轮反馈：", *feedback_lines])

    negative_prompt = ["watermark", "logo", "distorted text", "random extra objects"]
    if mode.name in {"roadmap", "schematic"}:
        negative_prompt.extend(
            [
                "condensed font",
                "narrow font",
                "compressed font",
                "horizontally squeezed text",
                "tall skinny Chinese characters",
            ]
        )

    payload: Dict[str, Any] = {
        "image_prompt": fallback_round_prompt(request_text=request_text, feedback_lines=feedback_lines, mode=mode),
        "negative_prompt": negative_prompt,
        "focus_points": ["忠实满足用户要求", "主体清晰", "结构稳定"],
        "reasoning": "使用本地模板拼装 prompt；脚本默认不调用 Gemini 文本规划，宿主 AI 可在运行前自行优化用户需求。",
    }
    normalized = normalize_prompt_payload(
        payload=payload,
        request_text=request_text,
        feedback_lines=feedback_lines,
        guardrails=[str(item) for item in guardrails] + mode.guardrails,
    )
    normalized["raw_text"] = ""
    normalized["planner_backend"] = "local_template"
    normalized["planner_context"] = join_lines(planner_lines)
    write_json(prompt_dir / "prompt-plan.json", normalized)
    write_text(prompt_dir / "prompt.txt", normalized["full_prompt"] + "\n")
    return normalized


def fallback_round_prompt(*, request_text: str, feedback_lines: List[str], mode: DrawMode) -> str:
    lines = [
        "Create one polished, publication-ready PNG image that directly satisfies the user requirement below.",
        f"Mode: {mode.name} - {mode.label}.",
        f"Purpose: {mode.purpose}",
        "",
        "User requirement:",
        request_text.strip(),
        "",
        "Render guidance:",
        *[f"- {item}" for item in mode.prompt_sections],
        *[f"- {item}" for item in mode.guardrails],
        "- Keep the main subject prominent and unambiguous.",
        "- Use a clean composition with readable labels only when necessary.",
        "- Prefer a white or light background unless the user explicitly asked otherwise.",
        "- Make colors intentional and high-contrast.",
    ]
    if mode.name in {"roadmap", "schematic"}:
        lines.extend(
            [
                "- Use normal-width Chinese label typography, like modern Heiti / Source Han Sans / Noto Sans CJK, with natural character proportions.",
                "- Prefer wrapping labels into short lines over squeezing or narrowing glyphs to fit boxes.",
                "- Do not use condensed, narrow, compressed, horizontally squeezed, or tall skinny text for Chinese labels.",
            ]
        )
    if feedback_lines:
        lines.extend(
            [
                "",
                "The previous round image is attached as the primary reference. Edit and improve that image instead of starting from scratch.",
                "Keep correct existing composition details stable; only change what the feedback requires.",
                "Fix these issues from the previous round:",
                *feedback_lines,
            ]
        )
    return join_lines(lines).strip()


def normalize_prompt_payload(
    *,
    payload: Dict[str, Any],
    request_text: str,
    feedback_lines: List[str],
    guardrails: List[str],
) -> Dict[str, Any]:
    image_prompt = str(payload.get("image_prompt") or "").strip()
    negative_prompt = _normalize_text_list(payload.get("negative_prompt"))
    focus_points = _normalize_text_list(payload.get("focus_points"))
    reasoning = str(payload.get("reasoning") or "").strip()
    if not image_prompt:
        sections = [
            "请生成一张高质量、结构清晰、主体明确的 PNG 图片。",
            "用户需求如下：",
            request_text.strip(),
        ]
        if feedback_lines:
            sections.extend(["", "请同时修复上一轮问题：", *feedback_lines])
        image_prompt = join_lines(sections)
        if not reasoning:
            reasoning = "模型未返回结构化 prompt，已回退到基于原始需求的护栏模板。"

    final_lines = [image_prompt.strip(), "", "必须遵守：", *[f"- {line}" for line in guardrails]]
    if negative_prompt:
        final_lines.extend(["", "尽量避免：", *[f"- {item}" for item in negative_prompt]])
    return {
        "image_prompt": image_prompt.strip(),
        "negative_prompt": negative_prompt,
        "focus_points": focus_points,
        "reasoning": reasoning,
        "full_prompt": join_lines(final_lines).strip(),
    }


def build_round_reference_images(
    *,
    user_reference_images: Optional[List[Path]],
    prior_rounds: List[Dict[str, Any]],
    max_reference_images: int,
) -> Dict[str, Any]:
    refs: List[Path] = []
    seen: set[str] = set()

    def add_ref(path: Path) -> None:
        if len(refs) >= max(1, max_reference_images):
            return
        key = _path_key(path)
        if key in seen:
            return
        refs.append(path)
        seen.add(key)

    prev_image = previous_round_image(prior_rounds)
    if prev_image is not None:
        add_ref(prev_image)
    for item in user_reference_images or []:
        add_ref(Path(item))

    prev_round = prior_rounds[-1] if prior_rounds else None
    return {
        "mode": "image-to-image" if prev_image is not None else "text-to-image",
        "source_round": prev_round.get("round") if prev_round else None,
        "source_image": str(prev_image) if prev_image is not None else None,
        "reference_images": [str(item) for item in refs],
        "user_reference_images": [str(item) for item in (user_reference_images or [])],
        "max_reference_images": max_reference_images,
    }


def previous_round_image(prior_rounds: List[Dict[str, Any]]) -> Optional[Path]:
    if not prior_rounds:
        return None
    image_meta = (prior_rounds[-1].get("image", {}) or {})
    output_png = str(image_meta.get("output_png") or "").strip()
    if not output_png:
        return None
    path = Path(output_png)
    if not path.exists():
        return None
    return path


def _path_key(path: Path) -> str:
    try:
        return str(path.resolve())
    except Exception:
        return str(path)


def run_draw_plot(
    *,
    request_text: str,
    project_root: Path,
    output_png: Optional[str],
    workspace_base: Optional[str],
    max_rounds: Optional[int],
    canvas_w: Optional[int],
    canvas_h: Optional[int],
    remote_env: Optional[Path],
    reference_images: Optional[List[Path]],
    mode_name: Optional[str] = None,
    provider_name: Optional[str] = None,
    allow_provider_fallback: bool = False,
    allow_outside_project: bool = False,
    postprocess_resize: Optional[bool] = None,
    postprocess_w: Optional[int] = None,
    postprocess_h: Optional[int] = None,
) -> Dict[str, Any]:
    cfg = load_config()
    gen_cfg = cfg.get("generation", {}) or {}
    eval_cfg = cfg.get("evaluation", {}) or {}
    reports_cfg = cfg.get("reports", {}) or {}
    parallel_cfg = cfg.get("parallel_vibe", {}) or {}
    mode = resolve_mode(cfg, mode_name)

    max_rounds = int(max_rounds or gen_cfg.get("default_max_rounds", 3))
    canvas_w = int(canvas_w or mode.canvas_width or gen_cfg.get("default_canvas_width", 1600))
    canvas_h = int(canvas_h or mode.canvas_height or gen_cfg.get("default_canvas_height", 900))
    effective_postprocess_resize = (
        bool(gen_cfg.get("postprocess_resize_default", False))
        if postprocess_resize is None
        else bool(postprocess_resize)
    )

    manifest = init_workspace(
        project_root=project_root,
        workspace_base=workspace_base,
        output_png=output_png,
        run_id=None,
        allow_outside_project=allow_outside_project,
    )
    run_dir = Path(manifest["run_dir"])
    request_file = Path(manifest["request_file"])
    analysis_json = Path(manifest["analysis_json"])
    result_json = Path(manifest["result_json"])

    write_text(request_file, request_text.strip() + "\n")
    provider_cfg = health_check_image_provider(
        remote_env_path=remote_env,
        provider_name=provider_name,
        timeout_s=int((cfg.get("api", {}) or {}).get("healthcheck_timeout_s", 30)),
    )
    api_cfg = cfg.get("api", {}) if isinstance(cfg.get("api"), dict) else {}
    async_job_cfg = api_cfg.get("async_image_job", {}) if isinstance(api_cfg.get("async_image_job"), dict) else {}
    current_provider_cfg = provider_cfg
    manifest["mode"] = {
        "name": mode.name,
        "label": mode.label,
        "canvas": {"width": canvas_w, "height": canvas_h},
        "accept_score": mode.accept_score,
    }
    manifest["image_provider"] = {
        "provider": provider_cfg.provider,
        "model": provider_cfg.model,
        "base_url": provider_cfg.base_url,
        "source": provider_cfg.source,
        "preflight_status": provider_cfg.preflight_status,
        "preflight_scope": provider_cfg.preflight_scope,
        "generation_eligibility": provider_cfg.generation_eligibility,
        "selection": str(provider_name or "auto"),
        "allow_provider_fallback": bool(allow_provider_fallback),
        "async_image_job_enabled": bool(async_job_cfg.get("enabled", True)),
        "async_image_job_submit_mode": str(async_job_cfg.get("submit_mode") or "sub2api_job_endpoint"),
        "async_image_job_fallback_to_sync_on_unsupported": bool(
            async_job_cfg.get("fallback_to_sync_on_unsupported", True)
        ),
    }
    manifest["generation"] = {
        "postprocess_resize": effective_postprocess_resize,
        "postprocess_width": int(postprocess_w) if postprocess_w else None,
        "postprocess_height": int(postprocess_h) if postprocess_h else None,
    }
    write_json(run_dir / str(reports_cfg.get("run_manifest", "run-manifest.json")), manifest)

    rounds_dir = Path(manifest["rounds_dir"])
    exports_dir = Path(manifest["exports_dir"])
    parallel_dir = ensure_dir(Path(manifest["parallel_vibe_dir"]))
    history: List[Dict[str, Any]] = []
    best_round: Optional[Dict[str, Any]] = None
    plateau_hits = 0
    repeated_hash_hits = 0
    last_hash: Optional[str] = None
    stop_reason = "max_rounds"

    for round_index in range(1, max_rounds + 1):
        round_dir = ensure_dir(rounds_dir / f"{gen_cfg.get('round_dir_prefix', 'round-')}{round_index:02d}")
        parallel_plan_path = prepare_parallel_plan(
            run_dir=run_dir,
            request_file=request_file,
            parallel_dir=parallel_dir,
            parallel_cfg=parallel_cfg,
            round_index=round_index,
            round_dir=round_dir,
        )
        prompt_data = build_round_prompt(
            request_text=request_text,
            round_index=round_index,
            max_rounds=max_rounds,
            prior_rounds=history,
            remote_env=remote_env,
            prompt_dir=round_dir,
            mode=mode,
        )
        reference_meta = build_round_reference_images(
            user_reference_images=reference_images,
            prior_rounds=history,
            max_reference_images=int(gen_cfg.get("max_reference_images", 4)),
        )
        round_reference_images = [Path(item) for item in reference_meta["reference_images"]]
        image_output = round_dir / "output.png"
        image_meta = generate_image(
            prompt=prompt_data["full_prompt"],
            output_png=image_output,
            remote_env=remote_env,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            debug_dir=round_dir / "image-debug",
            reference_images=round_reference_images,
            provider_cfg=current_provider_cfg,
            provider_name=provider_name,
            allow_provider_fallback=allow_provider_fallback,
            require_reference_images=bool(reference_meta["source_image"]),
            postprocess_resize=effective_postprocess_resize,
            postprocess_w=postprocess_w,
            postprocess_h=postprocess_h,
        )
        if image_meta.get("provider") and image_meta.get("provider") != current_provider_cfg.provider:
            current_provider_cfg = ImageProviderConfig(
                provider=str(image_meta.get("provider")),
                base_url=str(image_meta.get("base_url") or ""),
                api_key="",
                model=str(image_meta.get("model") or ""),
                env_path=remote_env,
                source=str(image_meta.get("provider_source") or "fallback"),
            )
        try:
            evaluation = evaluate_image(
                image_path=image_output,
                request_text=request_text,
                image_prompt=prompt_data["full_prompt"],
                remote_env=remote_env,
                output_json=round_dir / "evaluation.json",
                debug_dir=round_dir / "evaluation-debug",
                mode=mode,
            )
        except Exception:
            evaluation = heuristic_evaluation(image_output)
            write_json(round_dir / "evaluation.json", evaluation)
        evaluation["mode"] = mode.name
        evaluation["mode_accept_score"] = mode.accept_score
        evaluation["passed"] = bool(float(evaluation.get("score", 0.0)) >= float(mode.accept_score))

        image_hash = sha256_file(image_output)
        round_record = {
            "round": round_index,
            "round_dir": str(round_dir),
            "parallel_plan": str(parallel_plan_path),
            "prompt": prompt_data,
            "reference_strategy": reference_meta,
            "image": image_meta,
            "evaluation": evaluation,
            "image_sha256": image_hash,
        }
        history.append(round_record)
        write_json(analysis_json, {"run": manifest, "rounds": history})

        if best_round is None or float(evaluation.get("score", 0.0)) > float(
            (best_round.get("evaluation", {}) or {}).get("score", 0.0)
        ):
            best_round = round_record
            plateau_hits = 0
        else:
            delta = abs(
                float(evaluation.get("score", 0.0))
                - float((best_round.get("evaluation", {}) or {}).get("score", 0.0))
            )
            if delta <= float(eval_cfg.get("plateau_delta", 0.3)):
                plateau_hits += 1
            else:
                plateau_hits = 0

        if last_hash == image_hash:
            repeated_hash_hits += 1
        else:
            repeated_hash_hits = 0
        last_hash = image_hash

        if bool(evaluation.get("passed")):
            stop_reason = "accepted"
            break
        if repeated_hash_hits >= int(eval_cfg.get("repeated_hash_rounds", 2)) - 1:
            stop_reason = "repeated_hash"
            break
        if plateau_hits >= int(eval_cfg.get("plateau_rounds", 2)):
            stop_reason = "plateau"
            break

    if best_round is None:
        raise RuntimeError("未生成任何可用图片。")

    final_png = Path(manifest["public_output_png"])
    copy_file(Path(best_round["image"]["output_png"]), final_png)
    copy_file(Path(best_round["image"]["output_png"]), exports_dir / "best.png")

    summary = {
        "run": manifest,
        "best_round": best_round["round"],
        "best_round_dir": best_round["round_dir"],
        "final_output_png": str(final_png),
        "stop_reason": stop_reason,
        "round_count": len(history),
        "best_score": float((best_round.get("evaluation", {}) or {}).get("score", 0.0)),
        "mode": manifest["mode"],
        "image_provider": manifest["image_provider"],
        "providers_used": [
            {
                "round": item["round"],
                "provider": (item.get("image", {}) or {}).get("provider"),
                "model": (item.get("image", {}) or {}).get("model"),
                "base_url": (item.get("image", {}) or {}).get("base_url"),
                "source": (item.get("image", {}) or {}).get("provider_source"),
                "reference_mode": (item.get("reference_strategy", {}) or {}).get("mode"),
                "source_round": (item.get("reference_strategy", {}) or {}).get("source_round"),
            }
            for item in history
        ],
    }
    write_json(result_json, summary)
    write_json(analysis_json, {"run": manifest, "rounds": history, "summary": summary})
    return summary


def prepare_parallel_plan(
    *,
    run_dir: Path,
    request_file: Path,
    parallel_dir: Path,
    parallel_cfg: Dict[str, Any],
    round_index: int,
    round_dir: Path,
) -> Path:
    round_plan_prefix = str(parallel_cfg.get("round_plan_prefix", "parallel-plan.round-"))
    round_plan_path = parallel_dir / f"{round_plan_prefix}{round_index:02d}.json"
    plan = create_parallel_plan(
        run_dir=run_dir,
        request_file=request_file,
        round_index=round_index,
        output_plan=round_plan_path,
    )
    latest_plan_path = parallel_dir / str(parallel_cfg.get("plan_filename", "parallel-plan.json"))
    if latest_plan_path != round_plan_path:
        write_json(latest_plan_path, plan)
    write_json(round_dir / "parallel-plan.json", plan)
    return round_plan_path


def _normalize_text_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="auto-draw-plot 多轮图片生成主入口。")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--request-file", help="用户需求 Markdown/TXT")
    group.add_argument("--request-text", help="用户需求文本")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--workspace-base", default="", help="自定义隐藏工作区根目录")
    parser.add_argument("--output-png", default="", help="最终输出 PNG 路径")
    parser.add_argument("--max-rounds", type=int, default=0)
    parser.add_argument("--canvas-width", type=int, default=0, help="期望布局宽度/宽高比参考，不承诺最终 PNG 像素")
    parser.add_argument("--canvas-height", type=int, default=0, help="期望布局高度/宽高比参考，不承诺最终 PNG 像素")
    parser.add_argument("--postprocess-resize", action="store_true", default=None, help="显式启用后处理尺寸对齐；默认保留 provider 原生输出")
    parser.add_argument("--postprocess-width", type=int, default=0, help="后处理目标宽度；需配合 --postprocess-resize")
    parser.add_argument("--postprocess-height", type=int, default=0, help="后处理目标高度；需配合 --postprocess-resize")
    parser.add_argument("--api-env", default="", help="remote.env 路径")
    parser.add_argument("--mode", default="", help="绘图模式：general（默认）/ roadmap / schematic")
    parser.add_argument("--provider", default="auto", help="图片 provider：auto（默认）/ gpt-image-2 / nano_banana")
    parser.add_argument(
        "--allow-provider-fallback",
        action="store_true",
        help="provider 故障时允许从 gpt-image-2 切到 Nano Banana/Gemini；计费、权限与客户端策略错误仍不回退",
    )
    parser.add_argument("--allow-outside-project", action="store_true", help="允许 workspace/output 写到 project_root 外部")
    parser.add_argument("--reference-image", action="append", default=[], help="可重复传入参考图")
    args = parser.parse_args()

    request_text = read_text(Path(args.request_file)) if args.request_file else str(args.request_text or "")
    summary = run_draw_plot(
        request_text=request_text,
        project_root=expand_path(args.project_root, base=Path.cwd()),
        output_png=args.output_png or None,
        workspace_base=args.workspace_base or None,
        max_rounds=(args.max_rounds or None),
        canvas_w=(args.canvas_width or None),
        canvas_h=(args.canvas_height or None),
        remote_env=expand_path(args.api_env, base=Path.cwd()) if args.api_env else None,
        reference_images=[expand_path(item, base=Path.cwd()) for item in (args.reference_image or [])],
        mode_name=args.mode or None,
        provider_name=str(args.provider or "auto"),
        allow_provider_fallback=bool(args.allow_provider_fallback),
        allow_outside_project=bool(args.allow_outside_project),
        postprocess_resize=args.postprocess_resize,
        postprocess_w=int(args.postprocess_width) or None,
        postprocess_h=int(args.postprocess_height) or None,
    )
    print(summary["final_output_png"])


if __name__ == "__main__":
    main()
