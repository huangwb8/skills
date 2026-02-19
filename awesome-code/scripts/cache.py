#!/usr/bin/env python3
"""
Awesome Code - 缓存机制模块

提供 LRU 缓存、文件缓存等缓存机制，减少重复计算和 I/O 操作。
"""

from __future__ import annotations

import functools
import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class LRUCache:
    """简单的 LRU (Least Recently Used) 缓存实现"""

    def __init__(self, capacity: int = 128):
        """
        初始化 LRU 缓存

        Args:
            capacity: 缓存容量（最大条目数）
        """
        self.capacity: int = capacity
        self.cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        if key in self.cache:
            value, _ = self.cache[key]
            # 更新访问时间
            self.cache[key] = (value, time.time())
            return value
        return None

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果缓存已满，删除最旧的条目
        if len(self.cache) >= self.capacity and key not in self.cache:
            # 找到最旧的条目（访问时间最早）
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[key] = (value, time.time())

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()

    def remove(self, key: str) -> bool:
        """
        删除指定缓存条目

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def size(self) -> int:
        """获取当前缓存大小"""
        return len(self.cache)

    def keys(self) -> list[str]:
        """获取所有缓存键"""
        return list(self.cache.keys())


def lru_cache(
    maxsize: int = 128,
    key_func: Optional[Callable[..., str]] = None,
) -> Callable[[F], F]:
    """
    LRU 缓存装饰器

    Args:
        maxsize: 最大缓存大小
        key_func: 自定义键生成函数，接收函数参数返回缓存键

    Returns:
        装饰器函数

    示例:
        @lru_cache(maxsize=256)
        def expensive_function(x: int, y: int) -> int:
            return x * y

        # 使用自定义键生成函数
        @lru_cache(key_func=lambda self, x: f"user_{self.user_id}_{x}")
        def get_user_data(self, x: int) -> dict:
            ...
    """

    def decorator(func: F) -> F:
        cache: Dict[str, Tuple[Any, float]] = {}
        access_times: Dict[str, float] = {}

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 生成缓存键
            if key_func is not None:
                cache_key = key_func(*args, **kwargs)
            else:
                # 使用参数的哈希值作为键
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_str = ":".join(key_parts)
                cache_key = hashlib.md5(key_str.encode()).hexdigest()

            # 检查缓存
            if cache_key in cache:
                access_times[cache_key] = time.time()
                return cache[cache_key][0]

            # 执行函数
            result = func(*args, **kwargs)

            # 存储结果
            cache[cache_key] = (result, time.time())
            access_times[cache_key] = time.time()

            # 如果超过最大大小，删除最旧的条目
            if len(cache) > maxsize:
                oldest_key = min(access_times.keys(), key=lambda k: access_times[k])
                del cache[oldest_key]
                del access_times[oldest_key]

            return result

        # 添加缓存控制方法
        wrapper.cache_clear = lambda: (cache.clear(), access_times.clear())  # type: ignore[attr-defined]
        wrapper.cache_info = lambda: {  # type: ignore[attr-defined]
            "size": len(cache),
            "maxsize": maxsize,
        }

        return wrapper  # type: ignore[return-value]

    return decorator


class FileCache:
    """文件缓存系统"""

    def __init__(
        self,
        cache_dir: str | Path = ".awesome-code/cache",
        ttl_seconds: int = 3600,
    ):
        """
        初始化文件缓存

        Args:
            cache_dir: 缓存目录路径
            ttl_seconds: 缓存过期时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds: int = ttl_seconds

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用哈希值避免文件名冲突和特殊字符问题
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            # 读取缓存数据
            with open(cache_path, "rb") as f:
                data = pickle.load(f)

            # 检查是否过期
            cached_time = data.get("timestamp", 0)
            if time.time() - cached_time > self.ttl_seconds:
                cache_path.unlink()
                return None

            return data.get("value")
        except Exception:
            # 缓存文件损坏，删除并返回 None
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        cache_path = self._get_cache_path(key)

        try:
            data = {
                "value": value,
                "timestamp": time.time(),
            }
            with open(cache_path, "wb") as f:
                pickle.dump(data, f)
        except Exception:
            # 写入失败，忽略
            pass

    def clear(self) -> None:
        """清空所有缓存"""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink(missing_ok=True)

    def remove(self, key: str) -> bool:
        """
        删除指定缓存条目

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def cleanup_expired(self) -> int:
        """
        清理过期的缓存文件

        Returns:
            清理的文件数量
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)

                cached_time = data.get("timestamp", 0)
                if time.time() - cached_time > self.ttl_seconds:
                    cache_file.unlink()
                    count += 1
            except Exception:
                # 文件损坏，删除
                cache_file.unlink(missing_ok=True)
                count += 1
        return count


def file_cache(
    cache_dir: str | Path = ".awesome-code/cache",
    ttl_seconds: int = 3600,
    key_func: Optional[Callable[..., str]] = None,
) -> Callable[[F], F]:
    """
    文件缓存装饰器

    Args:
        cache_dir: 缓存目录路径
        ttl_seconds: 缓存过期时间（秒）
        key_func: 自定义键生成函数

    Returns:
        装饰器函数

    示例:
        @file_cache(ttl_seconds=7200)
        def load_config(path: str) -> dict:
            ...
    """

    def decorator(func: F) -> F:
        file_cache_instance = FileCache(cache_dir=cache_dir, ttl_seconds=ttl_seconds)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 生成缓存键
            if key_func is not None:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # 尝试从缓存获取
            cached_value = file_cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 存储到缓存
            file_cache_instance.set(cache_key, result)

            return result

        # 添加缓存控制方法
        wrapper.cache_clear = file_cache_instance.clear  # type: ignore[attr-defined]
        wrapper.cache_cleanup = file_cache_instance.cleanup_expired  # type: ignore[attr-defined]

        return wrapper  # type: ignore[return-value]

    return decorator


# 全局缓存实例（用于内存缓存）
_global_lru_cache = LRUCache(capacity=256)


def get_global_cache() -> LRUCache:
    """获取全局 LRU 缓存实例"""
    return _global_lru_cache


if __name__ == "__main__":
    # 示例用法

    # LRU 缓存装饰器
    @lru_cache(maxsize=128)
    def fibonacci(n: int) -> int:
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    print("fibonacci(100) =", fibonacci(100))
    print("缓存信息:", fibonacci.cache_info())

    # 文件缓存装饰器
    @file_cache(ttl_seconds=60)
    def load_json_data(url: str) -> dict:
        # 模拟加载远程数据
        return {"data": "sample", "url": url}

    print("\n首次加载:", load_json_data("https://example.com/data"))
    print("从缓存加载:", load_json_data("https://example.com/data"))
