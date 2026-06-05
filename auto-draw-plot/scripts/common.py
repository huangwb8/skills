from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def info(message: str) -> None:
    print(f"[auto-draw-plot] {message}")


def warn(message: str) -> None:
    print(f"[auto-draw-plot][warn] {message}", file=sys.stderr)


def fatal(message: str, code: int = 2) -> "None":
    print(f"[auto-draw-plot][error] {message}", file=sys.stderr)
    raise SystemExit(code)


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:
        fatal(f"缺少 PyYAML，无法读取配置：{exc}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fatal(f"配置文件不存在：{path}")
    except Exception as exc:
        fatal(f"读取 YAML 失败：{path} ({exc})")
    return data or {}


def load_config() -> Dict[str, Any]:
    return load_yaml(skill_root() / "config.yaml")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def expand_path(value: str | Path, *, base: Optional[Path] = None) -> Path:
    p = Path(os.path.expanduser(str(value)))
    if p.is_absolute():
        return p
    if base is None:
        base = Path.cwd()
    return (base / p).resolve()


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def now_tag(fmt: str) -> str:
    return dt.datetime.now().strftime(fmt)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def slugify(text: str, *, max_len: int = 48) -> str:
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", text.strip())
    normalized = normalized.strip("-").lower()
    if not normalized:
        normalized = "draw-plot"
    return normalized[:max_len].rstrip("-") or "draw-plot"


def relative_display(path: Path, *, base: Optional[Path] = None) -> str:
    try:
        if base is None:
            base = Path.cwd()
        return str(path.resolve().relative_to(base.resolve()))
    except Exception:
        return str(path)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return None

    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    candidates = fenced + [raw]
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        candidate = _repair_json_candidate(candidate)
        try:
            data = json.loads(candidate)
        except Exception:
            data = _try_balanced_json(candidate)
        if isinstance(data, dict):
            return data
    return None


def _try_balanced_json(text: str) -> Optional[Dict[str, Any]]:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for idx in range(start, len(text)):
        ch = text[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                snippet = text[start : idx + 1]
                snippet = _repair_json_candidate(snippet)
                try:
                    data = json.loads(snippet)
                except Exception:
                    return None
                if isinstance(data, dict):
                    return data
                return None
    return None


def join_lines(lines: Iterable[str]) -> str:
    return "\n".join([line for line in lines if line is not None])


def _repair_json_candidate(text: str) -> str:
    repaired = text
    repaired = re.sub(r'"\s+([A-Za-z_][A-Za-z0-9_]*)"\s*:', r'"\1":', repaired)
    repaired = re.sub(r'"\n+([A-Za-z_][A-Za-z0-9_]*)"\s*:', r'"\1":', repaired)
    repaired = repaired.replace("\r\n", "\n")
    return repaired
