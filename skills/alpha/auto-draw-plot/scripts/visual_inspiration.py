#!/usr/bin/env python3
"""List curated exemplars, read one case, or validate a host-authored blueprint."""

from __future__ import annotations

import argparse
import json
import sys
from http.client import HTTPException
from pathlib import Path
from typing import Any
from urllib.request import HTTPRedirectHandler, build_opener

INDEX = Path(__file__).resolve().parents[1] / "references" / "visual-exemplars.json"
VISUAL_TASKS = (
    "scientific_medical_illustration", "scientific_mechanism_diagram",
    "technical_roadmap", "flowchart_architecture", "infographic_data_storytelling",
    "editorial_poster_design", "photography_photorealism", "product_visualization",
    "3d_isometric_illustration", "character_artistic_illustration", "other",
)
DESIGN_DIMENSIONS = (
    "composition", "visual_hierarchy", "color", "typography", "lighting",
    "material_texture", "spatial_geometry", "information_density", "consistency",
    "rendering_style",
)
MAX_CASES = 5
MAX_SOURCE_BYTES = 96 * 1024
MAX_BLUEPRINT_BYTES = 8 * 1024


def load_cases() -> dict:
    cases = json.loads(INDEX.read_text(encoding="utf-8"))
    return {case["id"]: case for case in cases}


def case_metadata(case: dict) -> dict:
    source = f'https://github.com/{case["repository"]}/blob/{case["revision"]}/{case["path"]}'
    if "lines" in case:
        first, last = case["lines"]
        source += f"#L{first}" if first == last else f"#L{first}-L{last}"
    return {
        "id": case["id"],
        "repository": case["repository"],
        "url": source,
        "categories": case["categories"],
        "description": case["description"],
        "keywords": case["keywords"],
        "use_for": case["use_for"],
        "design_dimensions": case.get("design_dimensions", []),
        "access": "local_note" if "design_note" in case else "github_excerpt",
        "prompt_available": case["prompt_available"],
    }


def shortlist(
    visual_tasks: list[str],
    *,
    level: int,
    keywords: tuple[str, ...] = (),
    dimensions: tuple[str, ...] = (),
) -> list[dict]:
    """Return relevant local candidates, grouped in review order."""
    if level not in (1, 2) or not visual_tasks:
        return []
    terms = {word.strip().casefold() for word in keywords if word.strip()}
    design_targets = set(dimensions)
    ranked = []
    for case in load_cases().values():
        for priority, task in enumerate(visual_tasks):
            if task in case["categories"]:
                matches = len(terms.intersection(tag.casefold() for tag in case["keywords"]))
                matched_dimensions = len(design_targets.intersection(case.get("design_dimensions", ())))
                rank = (priority, -matches, -matched_dimensions, case["categories"].index(task))
                ranked.append((rank, case))
                break
    ranked.sort(key=lambda item: item[0])
    repositories: dict[str, list[dict]] = {}
    for _, case in ranked:
        repositories.setdefault(case["repository"], []).append(case_metadata(case))
    groups = list(repositories.values())[:level]
    if not groups:
        return []
    primary = groups[0][:3]
    secondary = groups[1][: MAX_CASES - len(primary)] if len(groups) == 2 else []
    return primary + secondary


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_case(case_id: str) -> dict:
    """Fetch only the pinned source for one indexed case and expose only its section."""
    case = load_cases().get(case_id)
    if case is None:
        raise ValueError("未知视觉案例 ID。")
    metadata = case_metadata(case)
    if "design_note" in case:
        return {**metadata, "design_note": case["design_note"], "untrusted_excerpt": "", "preview_url": None}
    root = f'https://raw.githubusercontent.com/{case["repository"]}/{case["revision"]}/'
    line_range = case.get("lines")
    with build_opener(NoRedirect).open(root + case["path"], timeout=5) as response:
        if line_range is None:
            raw = response.read(MAX_SOURCE_BYTES + 1)
            if len(raw) > MAX_SOURCE_BYTES:
                raise ValueError("视觉案例来源超出读取上限。")
        else:
            first, last = line_range
            remaining = MAX_SOURCE_BYTES
            selected = []
            for number in range(1, last + 1):
                line = response.readline(remaining + 1)
                remaining -= len(line)
                if remaining < 0:
                    raise ValueError("视觉案例来源超出读取上限。")
                if not line:
                    raise ValueError("视觉案例定位无效。")
                if number >= first:
                    selected.append(line)
            raw = b"".join(selected)
    lines = raw.decode("utf-8").splitlines()
    if not lines or ("heading" in case and lines[0] != case["heading"]):
        raise ValueError("视觉案例定位无效。")
    return {
        **metadata,
        "untrusted_excerpt": "\n".join(lines)[:4000],
        "preview_url": root + case["preview_path"] if case.get("preview_path") else None,
    }


def _short_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 350 or not value.isprintable():
        raise ValueError(f"视觉蓝图 {field} 必须是 1–350 字符的单行文字。")
    return value.strip()


def normalize_blueprint(value: object) -> dict:
    if not isinstance(value, dict) or value.get("visual_task") not in VISUAL_TASKS:
        raise ValueError("视觉蓝图需要有效的 visual_task。")
    inspiration = value.get("inspiration")
    if not isinstance(inspiration, list) or not 1 <= len(inspiration) <= MAX_CASES:
        raise ValueError(f"视觉蓝图需要 1–{MAX_CASES} 个实际采用的案例。")
    cases = load_cases()
    sources = []
    seen = set()
    for item in inspiration:
        case_id = item.get("id") if isinstance(item, dict) else None
        if not isinstance(case_id, str) or case_id not in cases or case_id in seen:
            raise ValueError("视觉蓝图的案例 ID 必须来自索引且不得重复。")
        seen.add(case_id)
        case = cases[case_id]
        metadata = case_metadata(case)
        sources.append({
            "id": case_id,
            "repository": metadata["repository"],
            "url": metadata["url"],
            "categories": metadata["categories"],
            "reason": _short_text(item.get("reason"), "inspiration.reason"),
        })
    if len({source["repository"] for source in sources}) > 2:
        raise ValueError("视觉蓝图最多记录两个来源仓库。")

    principles = value.get("design_principles")
    if not isinstance(principles, dict) or not principles or any(key not in DESIGN_DIMENSIONS for key in principles):
        raise ValueError("视觉蓝图需要至少一项受支持的 design_principles。")
    blueprint = {
        "visual_task": value["visual_task"],
        "inspiration": sources,
        "design_principles": {key: _short_text(text, key) for key, text in principles.items()},
        "adaptation": _short_text(value.get("adaptation"), "adaptation"),
    }
    if "excluded_elements" in value:
        blueprint["excluded_elements"] = _short_text(value["excluded_elements"], "excluded_elements")
    return blueprint


def read_blueprint(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        raw = handle.read(MAX_BLUEPRINT_BYTES + 1)
    if len(raw) > MAX_BLUEPRINT_BYTES:
        raise ValueError("视觉蓝图文件超出 8 KiB。")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("视觉蓝图需要 JSON 对象。")
    return value


def design_prompt_lines(blueprint: dict) -> list[str]:
    return [
        "", "Optional visual direction, only where compatible with the user requirement, mode, "
        "reference-image preservation and round feedback:",
        *[f"- {dimension}: {text}" for dimension, text in blueprint["design_principles"].items()],
        f'- Apply to this task: {blueprint["adaptation"]}',
        "Preserve the user-specified content, data, labels, relationships, arrow directions, geometry and format. "
        "Apply these directions only to the requested scope of change.",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--task", choices=VISUAL_TASKS, action="append", help="主类别在先，可追加次类别")
    group.add_argument("--case", help="仅深入读取一个已选案例")
    parser.add_argument("--level", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--keyword", action="append", default=[], help="用于本地排序的索引关键词，可重复")
    parser.add_argument("--dimension", choices=DESIGN_DIMENSIONS, action="append", default=[], help="待解决的设计维度，可重复")
    args = parser.parse_args()
    try:
        result = read_case(args.case) if args.case else shortlist(
            args.task, level=args.level, keywords=tuple(args.keyword), dimensions=tuple(args.dimension),
        )
    except (OSError, ValueError, HTTPException) as exc:
        parser.exit(1, f"视觉案例不可用，可继续使用内置绘图规范：{type(exc).__name__}\n")
    json.dump(result, sys.stdout, ensure_ascii=True, indent=2)
    print()


if __name__ == "__main__":
    main()
