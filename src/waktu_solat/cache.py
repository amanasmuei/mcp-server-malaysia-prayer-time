"""
Simple in-memory cache implementation with TTL support.
"""

from typing import Dict, Any, Optional, TypeVar, Generic, Callable
import time
from dataclasses import dataclass
from functools import wraps
from .config import config

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A cache entry with TTL tracking."""

    value: T
    expires_at: float


class Cache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self):
        self._store: Dict[str, CacheEntry] = {}
        self._max_size = config.cache.max_size
        self._ttl = config.cache.ttl

    def _clean_expired(self) -> None:
        """Remove expired entries from cache."""
        now = time.time()
        expired_keys = [
            key for key, entry in self._store.items() if entry.expires_at <= now
        ]
        for key in expired_keys:
            del self._store[key]

    def _ensure_capacity(self) -> None:
        """Ensure cache doesn't exceed max size by removing oldest entries."""
        if len(self._store) >= self._max_size:
            # Remove 10% of oldest entries
            num_to_remove = max(1, self._max_size // 10)
            sorted_items = sorted(self._store.items(), key=lambda x: x[1].expires_at)
            for key, _ in sorted_items[:num_to_remove]:
                del self._store[key]

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        Returns None if key doesn't exist or entry has expired.
        """
        self._clean_expired()

        entry = self._store.get(key)
        if entry is None:
            return None

        if entry.expires_at <= time.time():
            del self._store[key]
            return None

        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache with optional TTL override.
        """
        self._clean_expired()
        self._ensure_capacity()

        expires_at = time.time() + (ttl if ttl is not None else self._ttl)
        self._store[key] = CacheEntry(value, expires_at)

    def delete(self, key: str) -> None:
        """Remove a key from cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all entries from cache."""
        self._store.clear()


# Global cache instance
cache = Cache()


def cache_key(*args: Any, **kwargs: Any) -> str:
    """Generate a cache key from args and kwargs."""
    args_str = "_".join(str(arg) for arg in args)
    kwargs_str = "_".join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return f"{args_str}_{kwargs_str}".strip("_")


def cached(ttl: Optional[int] = None):
    """
    Decorator for caching function results.

    Args:
        ttl: Optional TTL override in seconds

    Example:
        @cached(ttl=300)
        async def get_zones():
            return await fetch_zones()
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__module__}.{func.__name__}_{cache_key(*args, **kwargs)}"

            # Check cache first
            result = cache.get(key)
            if result is not None:
                return result

            # Call original function
            result = await func(*args, **kwargs)

            # Cache the result
            cache.set(key, result, ttl)

            return result

        return wrapper

    return decorator
