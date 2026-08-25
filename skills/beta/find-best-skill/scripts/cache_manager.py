#!/usr/bin/env python3
"""
Find Best Skill - 缓存管理器

功能：
- 缓存技能元数据到 .bensz-api/skills/find-best-skill/cache/
- 基于关键词和标签进行相似度匹配
- 自动清理过期缓存（默认半年）
- 支持本地/联网数据混合推荐
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import argparse

# `cache_manager.py` needs to work in both modes:
# - `python scripts/cache_manager.py ...` (scripts/ on sys.path)
# - `from scripts.cache_manager import CacheManager` (scripts as namespace package)
try:
    from .config_loader import get_cache_config, load_config  # type: ignore
except ImportError:  # pragma: no cover
    from config_loader import get_cache_config, load_config

class CacheManager:
    """技能缓存管理器"""

    def __init__(self, cache_dir: Optional[str] = None, config: Optional[Dict] = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径，默认 .bensz-api/skills/find-best-skill/cache
            config: 配置字典，包含 TTL 等参数
        """
        self.cache_dir = Path(os.path.expanduser(cache_dir or ".bensz-api/skills/find-best-skill/cache"))
        self.cache_file = self.cache_dir / "cache" / "metadata.json"
        self.keywords_index = self.cache_dir / "cache" / "index" / "keywords.json"
        self.tags_index = self.cache_dir / "cache" / "index" / "tags.json"

        self.config = self._normalize_config(config)

        self._ensure_structure()

    @staticmethod
    def _normalize_config(config: Optional[Dict]) -> Dict:
        """Normalize config keys to keep backward compatibility."""
        defaults = {
            "ttl_days": 180,
            "max_size": 1000,
            "similarity_threshold": 0.3,
        }
        if not config:
            return defaults

        # Accept both the new keys (ttl_days/max_size) and legacy keys
        # (cache_ttl_days/max_cache_size) from early versions.
        normalized = dict(defaults)
        if "ttl_days" in config:
            normalized["ttl_days"] = int(config["ttl_days"])
        if "cache_ttl_days" in config:
            normalized["ttl_days"] = int(config["cache_ttl_days"])
        if "max_size" in config:
            normalized["max_size"] = int(config["max_size"])
        if "max_cache_size" in config:
            normalized["max_size"] = int(config["max_cache_size"])
        if "similarity_threshold" in config:
            normalized["similarity_threshold"] = float(config["similarity_threshold"])
        return normalized

    def _ensure_structure(self):
        """确保缓存目录结构存在"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.keywords_index.parent.mkdir(parents=True, exist_ok=True)  # also covers tags_index.parent

        # 初始化缓存文件（如果不存在）
        if not self.cache_file.exists():
            self._write_cache({"skills": {}, "version": "0.1.0"})

    def _read_cache(self) -> Dict:
        """读取缓存数据"""
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"skills": {}, "version": "0.1.0"}
        except json.JSONDecodeError:
            self._backup_corrupt_file(self.cache_file)
            # Self-heal to a clean cache file to keep the tool usable.
            fresh = {"skills": {}, "version": "0.1.0"}
            self._write_cache(fresh)
            return fresh

    def _write_cache(self, data: Dict):
        """写入缓存数据"""
        self._atomic_write_json(self.cache_file, data)

    def _read_index(self, index_file: Path) -> Dict:
        """读取索引文件"""
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_index(self, index_file: Path, data: Dict):
        """写入索引文件"""
        index_file.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write_json(index_file, data)

    @staticmethod
    def _atomic_write_json(path: Path, data: Dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = Path(f"{path}.tmp.{os.getpid()}")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        finally:
            # Best-effort cleanup (if replace failed).
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass

    @staticmethod
    def _backup_corrupt_file(path: Path) -> None:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        backup = Path(f"{path}.corrupt.{ts}")
        try:
            os.replace(path, backup)
        except OSError:
            # If we can't move it, we still fall back to a fresh cache.
            pass

    @staticmethod
    def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _update_access_time(self, skill_name: str):
        """更新技能的访问时间"""
        cache = self._read_cache()
        if skill_name in cache["skills"]:
            cache["skills"][skill_name]["meta"]["last_accessed"] = datetime.now().isoformat()
            self._write_cache(cache)

    def add_skill(self, skill_name: str, meta: Dict, keywords: List[str], tags: List[str]) -> bool:
        """
        添加技能到缓存

        Args:
            skill_name: 技能名称
            meta: 元数据（url, description, stars, last_updated 等）
            keywords: 关键词列表
            tags: 标签列表

        Returns:
            是否成功添加
        """
        cache = self._read_cache()

        # 检查缓存大小限制
        if len(cache["skills"]) >= self.config["max_size"]:
            self._cleanup_old_entries()

        now = datetime.now().isoformat()

        cache["skills"][skill_name] = {
            "meta": {
                "name": skill_name,
                "cached_at": now,
                "last_accessed": now,
                "source": meta.get("source", "online"),
                **meta
            },
            "keywords": [k.lower() for k in keywords],
            "tags": [t.lower() for t in tags],
            "quality": meta.get("quality", {})
        }

        self._write_cache(cache)
        self._rebuild_indexes()
        return True

    def get_skill(self, skill_name: str) -> Optional[Dict]:
        """
        获取技能详情

        Args:
            skill_name: 技能名称

        Returns:
            技能数据，不存在返回 None
        """
        cache = self._read_cache()
        skill = cache["skills"].get(skill_name)

        if skill:
            self._update_access_time(skill_name)

        return skill

    def search_by_keywords(self, query_keywords: List[str], limit: int = 10) -> List[Tuple[str, float, Dict]]:
        """
        基于关键词搜索技能

        Args:
            query_keywords: 查询关键词列表
            limit: 返回结果上限

        Returns:
            [(skill_name, score, skill_data), ...] 按分数降序
        """
        cache = self._read_cache()
        results = []

        query_keywords = [k.lower() for k in query_keywords]

        for skill_name, skill_data in cache["skills"].items():
            skill_keywords = skill_data.get("keywords", [])
            skill_tags = skill_data.get("tags", [])

            # 计算关键词相似度
            keyword_scores = []
            for qk in query_keywords:
                for sk in skill_keywords:
                    ratio = SequenceMatcher(None, qk, sk).ratio()
                    if ratio >= self.config["similarity_threshold"]:
                        keyword_scores.append(ratio)

            # 标签完全匹配加分
            tag_bonus = sum(1 for tag in skill_tags if tag in query_keywords)

            # 计算综合分数
            if keyword_scores:
                avg_keyword_score = sum(keyword_scores) / len(keyword_scores)
                final_score = avg_keyword_score + (tag_bonus * 0.1)
                results.append((skill_name, final_score, skill_data))

        # 按分数降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _cleanup_old_entries(self):
        """清理过期缓存"""
        cache = self._read_cache()
        now = datetime.now()
        ttl = timedelta(days=self.config["ttl_days"])

        to_remove = []

        for skill_name, skill_data in cache["skills"].items():
            cached_at = self._parse_iso_datetime(skill_data.get("meta", {}).get("cached_at"))
            if not cached_at or now - cached_at > ttl:
                to_remove.append(skill_name)

        for skill_name in to_remove:
            del cache["skills"][skill_name]

        self._write_cache(cache)

    def _rebuild_indexes(self):
        """重建索引文件"""
        cache = self._read_cache()

        # 构建关键词索引
        keywords_index = {}
        for skill_name, skill_data in cache["skills"].items():
            for keyword in skill_data.get("keywords", []):
                if keyword not in keywords_index:
                    keywords_index[keyword] = []
                keywords_index[keyword].append(skill_name)

        self._write_index(self.keywords_index, keywords_index)

        # 构建标签索引
        tags_index = {}
        for skill_name, skill_data in cache["skills"].items():
            for tag in skill_data.get("tags", []):
                if tag not in tags_index:
                    tags_index[tag] = []
                tags_index[tag].append(skill_name)

        self._write_index(self.tags_index, tags_index)

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        cache = self._read_cache()
        now = datetime.now()
        ttl = timedelta(days=self.config["ttl_days"])

        expiring_soon = 0
        expired = 0

        for skill_data in cache["skills"].values():
            cached_at = self._parse_iso_datetime(skill_data.get("meta", {}).get("cached_at"))
            if not cached_at:
                expired += 1
                continue
            age = now - cached_at

            if age > ttl:
                expired += 1
            elif age > ttl * 0.8:  # 超过 80% TTL
                expiring_soon += 1

        return {
            "total_skills": len(cache["skills"]),
            "expired": expired,
            "expiring_soon": expiring_soon,
            "cache_dir": str(self.cache_dir),
            "ttl_days": self.config["ttl_days"]
        }

    def clear_cache(self, skill_name: Optional[str] = None):
        """
        清理缓存

        Args:
            skill_name: 指定技能名，None 表示清理所有
        """
        cache = self._read_cache()

        if skill_name:
            if skill_name in cache["skills"]:
                del cache["skills"][skill_name]
                print(f"✓ 已清理技能: {skill_name}")
            else:
                print(f"✗ 技能不存在: {skill_name}")
        else:
            cache["skills"] = {}
            print("✓ 已清理所有缓存")

        self._write_cache(cache)
        self._rebuild_indexes()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="Find Best Skill 缓存管理器")
    parser.add_argument(
        "--config",
        default=None,
        help="config.yaml 路径（默认：使用 find-best-skill/config.yaml）",
    )
    parser.add_argument("--cache-dir", default=None, help="缓存目录路径（CLI 覆盖 config.yaml）")
    parser.add_argument("--stats", action="store_true", help="显示缓存统计信息")
    parser.add_argument("--clear", nargs="?", const="__ALL__", help="清理缓存（可指定技能名）")
    parser.add_argument("--search", nargs="+", help="搜索关键词")
    parser.add_argument("--limit", type=int, default=10, help="搜索结果上限")

    args = parser.parse_args()

    try:
        cfg = load_config(args.config) if args.config else load_config()
    except Exception as e:
        print(f"✗ 读取配置失败：{e}", file=sys.stderr)
        sys.exit(1)
    cache_cfg = get_cache_config(cfg)

    if not cache_cfg.enabled:
        print("✗ 缓存已在 config.yaml:cache.enabled 中禁用")
        return

    cache_dir = args.cache_dir or cache_cfg.dir
    manager = CacheManager(
        cache_dir=cache_dir,
        config={
            "ttl_days": cache_cfg.ttl_days,
            "max_size": cache_cfg.max_size,
            "similarity_threshold": cache_cfg.similarity_threshold,
        },
    )

    if args.stats:
        stats = manager.get_stats()
        print("\n📊 缓存统计:")
        print(f"  总技能数: {stats['total_skills']}")
        print(f"  已过期: {stats['expired']}")
        print(f"  即将过期: {stats['expiring_soon']}")
        print(f"  缓存目录: {stats['cache_dir']}")
        print(f"  过期时间: {stats['ttl_days']} 天\n")

    elif args.clear:
        skill_name = None if args.clear == "__ALL__" else args.clear
        manager.clear_cache(skill_name)

    elif args.search:
        results = manager.search_by_keywords(args.search, limit=args.limit)

        print(f"\n🔍 搜索结果: {' + '.join(args.search)}\n")
        if results:
            for i, (skill_name, score, skill_data) in enumerate(results, 1):
                meta = skill_data["meta"]
                print(f"{i}. {skill_name} (相关度: {score:.2f})")
                print(f"   {meta.get('description', 'N/A')}")
                print(f"   ⭐ {meta.get('stars', 'N/A')} | 📅 {meta.get('last_updated', 'N/A')}")
                print(f"   🔗 {meta.get('url', 'N/A')}\n")
        else:
            print("未找到相关技能\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
