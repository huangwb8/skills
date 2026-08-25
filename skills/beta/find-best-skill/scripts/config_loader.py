#!/usr/bin/env python3
"""
find-best-skill 配置加载器

目标：
- 让 scripts/ 下的工具都以 skill 根目录的 config.yaml 为单一真相来源
- 允许通过 CLI 参数覆盖（CLI > config.yaml > 默认值）
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


def find_skill_root() -> Path:
    """Return the find-best-skill root (parent of scripts/)."""
    return Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    return find_skill_root() / "config.yaml"


def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    path = Path(config_path) if config_path else default_config_path()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"config.yaml 格式不正确（期望 dict）：{path}")
    return data


def _get_nested(d: Dict[str, Any], keys: List[str], default: Any) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


@dataclass(frozen=True)
class CacheConfig:
    enabled: bool = True
    dir: str = ".bensz-api/skills/find-best-skill/cache"
    ttl_days: int = 180
    max_size: int = 1000
    similarity_threshold: float = 0.3


def get_cache_config(cfg: Dict[str, Any]) -> CacheConfig:
    cache = _get_nested(cfg, ["cache"], {}) or {}
    return CacheConfig(
        enabled=bool(cache.get("enabled", True)),
        dir=str(cache.get("dir", ".bensz-api/skills/find-best-skill/cache")),
        ttl_days=int(cache.get("ttl_days", 180)),
        max_size=int(cache.get("max_size", 1000)),
        similarity_threshold=float(cache.get("similarity_threshold", 0.3)),
    )


def get_min_stars(cfg: Dict[str, Any], default: int = 10) -> int:
    return int(_get_nested(cfg, ["recommendation_criteria", "min_stars"], default))
