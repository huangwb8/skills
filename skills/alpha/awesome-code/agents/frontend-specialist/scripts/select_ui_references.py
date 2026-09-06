#!/usr/bin/env python3
"""Select a small, deterministic set of UI reference categories and sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


def load_index() -> dict:
    root = Path(__file__).resolve().parents[1]
    index_path = root / "references" / "ui-reference-index.yaml"
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("需要 PyYAML 才能读取 UI 参考索引") from exc
    with index_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def tokens(value: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[\w-]+", value, re.UNICODE) if len(token) > 1}


def select(task: str, product_type: str, stack: str, index: dict) -> dict:
    query = tokens(f"{task} {product_type} {stack}")
    ranked = []
    for category, data in index["categories"].items():
        category_tokens = tokens(" ".join(data.get("keywords", [])))
        score = len(query & category_tokens)
        if product_type.lower() in {"dashboard", "admin", "crm", "api", "form"} and category == "product-components":
            score += 2
        if product_type.lower() in {"landing", "marketing", "saas", "brand"} and category in {"visual-inspiration", "page-structure"}:
            score += 2
        if product_type.lower() in {"form", "dialog", "interaction"} and category == "interaction-primitives":
            score += 2
        if score:
            ranked.append((score, category, data))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    selected = ranked[:3]
    sources = []
    for score, category, data in selected:
        for source in data.get("sources", []):
            if stack.lower() in {"vue", "nuxt"} and source["name"] in {"React Bits", "Magic UI", "Tremor"}:
                continue
            sources.append({"category": category, "match_score": score, **source})
    return {
        "query": {"task": task, "product_type": product_type, "stack": stack},
        "limits": {"max_categories": 3, "max_sources": 3, "max_patterns": 5},
        "categories": [{"name": category, "score": score} for score, category, _ in selected],
        "sources": sources[:3],
        "instructions": [
            "只读取与当前任务相关的具体组件或页面",
            "提取设计模式，不复制整页或大段源码",
            "许可证、版本、性能和无障碍未核实前仅作灵感参考",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--product-type", default="unknown")
    parser.add_argument("--stack", default="unknown")
    args = parser.parse_args()
    print(json.dumps(select(args.task, args.product_type, args.stack, load_index()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
