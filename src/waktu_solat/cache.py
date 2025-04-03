"""
Thread-safe in-memory cache implementation with TTL support.

This module provides a simple but robust caching mechanism with the following features:
- Thread-safe operations
- TTL (Time To Live) support
- Automatic cleanup of expired entries
- Capacity management to prevent memory leaks
- Decorator support for easy function result caching
"""

from __future__ import annotations
import logging
import threading
import time
from dataclasses import dataclass
from functools import wraps
from typing import Dict, Any, Optional, TypeVar, Generic, Callable

from .config import config

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A cache entry with TTL tracking."""

    value: T
    expires_at: float


class Cache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self) -> None:
        """Initialize a new cache instance."""
        self._store: Dict[str, CacheEntry[Any]] = {}
        self._max_size: int = config.cache.max_size
        self._ttl: int = config.cache.ttl
        self._lock: threading.RLock = threading.RLock()

    def _clean_expired(self) -> None:
        """Remove expired entries from cache."""
        now = time.time()
        expired_keys = [
            key for key, entry in self._store.items() if entry.expires_at <= now
        ]
        if expired_keys:
            for key in expired_keys:
                del self._store[key]
            logger.debug(f"Cleaned {len(expired_keys)} expired entries from cache")

    def _ensure_capacity(self) -> None:
        """Ensure cache doesn't exceed max size by removing oldest entries."""
        if len(self._store) >= self._max_size:
            # Remove 10% of oldest entries
            num_to_remove = max(1, self._max_size // 10)
            sorted_items = sorted(self._store.items(), key=lambda x: x[1].expires_at)
            for key, _ in sorted_items[:num_to_remove]:
                del self._store[key]
            logger.debug(f"Removed {num_to_remove} entries to ensure cache capacity")

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: The key to look up

        Returns:
            The cached value if it exists and hasn't expired, None otherwise
        """
        with self._lock:
            self._clean_expired()

            entry = self._store.get(key)
            if entry is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            if entry.expires_at <= time.time():
                del self._store[key]
                logger.debug(f"Cache entry expired for key: {key}")
                return None

            logger.debug(f"Cache hit for key: {key}")
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache with optional TTL override.

        Args:
            key: The key to store the value under
            value: The value to cache
            ttl: Optional TTL override in seconds. Must be positive if provided.

        Raises:
            ValueError: If TTL is not a positive integer
        """
        if ttl is not None and ttl <= 0:
            raise ValueError("TTL must be a positive integer")

        with self._lock:
            self._clean_expired()
            self._ensure_capacity()

            effective_ttl = ttl if ttl is not None else self._ttl
            expires_at = time.time() + effective_ttl
            self._store[key] = CacheEntry(value, expires_at)
            logger.debug(f"Cache set for key: {key} with TTL: {effective_ttl}s")

    def delete(self, key: str) -> None:
        """
        Remove a key from cache.

        Args:
            key: The key to remove
        """
        with self._lock:
            if self._store.pop(key, None) is not None:
                logger.debug(f"Deleted cache entry for key: {key}")

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._store.clear()
            logger.debug("Cache cleared")


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
