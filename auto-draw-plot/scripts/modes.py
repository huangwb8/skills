from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class DrawMode:
    name: str
    label: str
    canvas_width: int
    canvas_height: int
    accept_score: float
    planner_role: str
    purpose: str
    prompt_sections: List[str]
    guardrails: List[str]
    evaluation_criteria: List[str]


def resolve_mode(config: Dict[str, Any], requested: str | None = None) -> DrawMode:
    modes_cfg = config.get("modes", {}) if isinstance(config.get("modes"), dict) else {}
    default_name = str(modes_cfg.get("default", "general") or "general").strip().lower()
    explicit = requested is not None and str(requested).strip() != ""
    mode_name = _canonical_mode_name(modes_cfg, requested or default_name)
    presets = modes_cfg.get("presets") if isinstance(modes_cfg.get("presets"), dict) else {}
    preset = presets.get(mode_name)
    if not isinstance(preset, dict) and explicit:
        valid = sorted(str(key) for key in presets.keys()) or [default_name]
        raise ValueError(f"不支持的绘图模式：{requested!r}。可用模式：{', '.join(valid)}")
    if not isinstance(preset, dict):
        preset = presets.get(default_name) if isinstance(presets.get(default_name), dict) else {}
        mode_name = default_name if isinstance(presets.get(default_name), dict) else "general"

    gen_cfg = config.get("generation", {}) if isinstance(config.get("generation"), dict) else {}
    eval_cfg = config.get("evaluation", {}) if isinstance(config.get("evaluation"), dict) else {}
    return DrawMode(
        name=mode_name,
        label=str(preset.get("label") or mode_name),
        canvas_width=int(preset.get("canvas_width") or gen_cfg.get("default_canvas_width", 1600) or 1600),
        canvas_height=int(preset.get("canvas_height") or gen_cfg.get("default_canvas_height", 900) or 900),
        accept_score=float(preset.get("accept_score") or eval_cfg.get("accept_score", 8.5) or 8.5),
        planner_role=str(preset.get("planner_role") or "你是一位高质量图片生成 prompt 设计师。"),
        purpose=str(preset.get("purpose") or "生成一张高质量 PNG 图片。"),
        prompt_sections=_as_text_list(preset.get("prompt_sections")),
        guardrails=_as_text_list(preset.get("guardrails")),
        evaluation_criteria=_as_text_list(preset.get("evaluation_criteria")),
    )


def mode_prompt_lines(mode: DrawMode) -> List[str]:
    lines = [
        f"绘图模式：{mode.name}（{mode.label}）",
        f"模式目标：{mode.purpose}",
    ]
    if mode.prompt_sections:
        lines.append("模式构图要求：")
        lines.extend([f"- {item}" for item in mode.prompt_sections])
    if mode.guardrails:
        lines.append("模式硬性约束：")
        lines.extend([f"- {item}" for item in mode.guardrails])
    return lines


def mode_evaluation_lines(mode: DrawMode) -> List[str]:
    if not mode.evaluation_criteria:
        return []
    return ["模式专属评估项：", *[f"- {item}" for item in mode.evaluation_criteria]]


def _canonical_mode_name(modes_cfg: Dict[str, Any], requested: str) -> str:
    raw = str(requested or "").strip().lower()
    if not raw:
        return "general"
    presets = modes_cfg.get("presets") if isinstance(modes_cfg.get("presets"), dict) else {}
    if raw in presets:
        return raw
    aliases = modes_cfg.get("aliases") if isinstance(modes_cfg.get("aliases"), dict) else {}
    for name, values in aliases.items():
        candidates = [str(name).strip().lower()]
        if isinstance(values, list):
            candidates.extend(str(item).strip().lower() for item in values)
        if raw in candidates:
            return str(name).strip().lower()
    return raw


def _as_text_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
