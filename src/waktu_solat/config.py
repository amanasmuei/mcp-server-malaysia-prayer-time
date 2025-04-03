"""
Configuration management for the Malaysia Prayer Time MCP Server.

This module provides a configuration system with:
- Environment variable overrides
- YAML/JSON file loading
- Value validation
- Configuration locking
- Default values
- Type safety using dataclasses

Usage:
    # Load from environment variables
    config.load_from_env()

    # Load from file
    config.load_from_file('config.yaml')

    # Manual configuration
    config.configure({
        'cache': {'ttl': 7200},
        'http': {'timeout': 5}
    })
"""

import os
import json
import yaml
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Optional, ClassVar, Final
from dataclasses import dataclass, field

# Constants
DEFAULT_CONFIG_PATHS: Final[list[str]] = [
    "./config.yaml",
    "./config.yml",
    "./config.json",
]


@dataclass
class CacheConfig:
    """
    Cache configuration settings.

    Attributes:
        type: Cache backend type ('memory' or 'redis')
        ttl: Default cache TTL in seconds
        max_size: Maximum number of items in memory cache
        redis_url: Redis connection URL (only used when type='redis')
    """

    type: str = field(default="memory")
    ttl: int = field(default=3600)
    max_size: int = field(default=1000)
    redis_url: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.type not in ["memory", "redis"]:
            raise ValueError("Cache type must be 'memory' or 'redis'")

        if self.ttl < 0:
            raise ValueError("Cache TTL must be non-negative")

        if self.max_size < 1:
            raise ValueError("Cache max_size must be positive")

        if self.type == "redis" and not self.redis_url:
            raise ValueError("Redis URL required when cache type is 'redis'")


@dataclass
class HTTPConfig:
    """
    HTTP client configuration settings.

    Attributes:
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        pool_connections: Maximum number of connections in pool
        base_url: Base URL for API requests
        verify_ssl: Whether to verify SSL certificates
    """

    timeout: int = field(default=10)
    max_retries: int = field(default=3)
    pool_connections: int = field(default=10)
    base_url: str = field(default="https://api.waktusolat.app")
    verify_ssl: bool = field(default=True)

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.timeout < 1:
            raise ValueError("HTTP timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")

        if self.pool_connections < 1:
            raise ValueError("Pool connections must be positive")

        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")


@dataclass
class Config:
    """
    Main configuration container.

    This class manages all configuration settings and provides methods
    for loading from different sources.

    Attributes:
        cache: Cache-related settings
        http: HTTP client settings
    """

    cache: CacheConfig = field(default_factory=CacheConfig)
    http: HTTPConfig = field(default_factory=HTTPConfig)
    _lock: ClassVar[Lock] = Lock()
    _initialized: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """Mark as initialized after creation."""
        self._initialized = True

    @classmethod
    def default(cls) -> "Config":
        """Create a default configuration instance."""
        return cls(cache=CacheConfig(), http=HTTPConfig())

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """
        Create a configuration instance from a dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            New Config instance

        Raises:
            ValueError: If configuration values are invalid
        """
        cache_config = CacheConfig(**config_dict.get("cache", {}))
        http_config = HTTPConfig(**config_dict.get("http", {}))
        return cls(cache=cache_config, http=http_config)

    def load_from_env(self) -> None:
        """
        Load configuration from environment variables.

        Environment variables should be prefixed with WAKTU_SOLAT_
        Example: WAKTU_SOLAT_CACHE_TTL=7200
        """
        with self._lock:
            # Cache config
            if ttl := os.getenv("WAKTU_SOLAT_CACHE_TTL"):
                self.cache.ttl = int(ttl)
            if max_size := os.getenv("WAKTU_SOLAT_CACHE_MAX_SIZE"):
                self.cache.max_size = int(max_size)
            if cache_type := os.getenv("WAKTU_SOLAT_CACHE_TYPE"):
                self.cache.type = cache_type
            if redis_url := os.getenv("WAKTU_SOLAT_REDIS_URL"):
                self.cache.redis_url = redis_url

            # HTTP config
            if timeout := os.getenv("WAKTU_SOLAT_HTTP_TIMEOUT"):
                self.http.timeout = int(timeout)
            if retries := os.getenv("WAKTU_SOLAT_HTTP_MAX_RETRIES"):
                self.http.max_retries = int(retries)
            if pool := os.getenv("WAKTU_SOLAT_HTTP_POOL_CONNECTIONS"):
                self.http.pool_connections = int(pool)
            if base_url := os.getenv("WAKTU_SOLAT_HTTP_BASE_URL"):
                self.http.base_url = base_url
            if verify_ssl := os.getenv("WAKTU_SOLAT_HTTP_VERIFY_SSL"):
                self.http.verify_ssl = verify_ssl.lower() in ("true", "1", "yes")

    def load_from_file(self, path: Optional[str] = None) -> None:
        """
        Load configuration from a YAML or JSON file.

        Args:
            path: Path to config file. If None, searches default locations.

        Raises:
            FileNotFoundError: If no config file found
            ValueError: If config file format is invalid
        """
        if path is None:
            for default_path in DEFAULT_CONFIG_PATHS:
                if Path(default_path).exists():
                    path = default_path
                    break
            else:
                raise FileNotFoundError("No configuration file found")

        with Path(path).open() as f:
            if path.endswith(".json"):
                config_dict = json.load(f)
            else:  # YAML
                config_dict = yaml.safe_load(f)

        with self._lock:
            self._update_from_dict(config_dict)

    def _update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary with validation."""
        if "cache" in config_dict:
            cache_config = CacheConfig(**config_dict["cache"])
            self.cache = cache_config
        if "http" in config_dict:
            http_config = HTTPConfig(**config_dict["http"])
            self.http = http_config


# Global configuration instance
config = Config.default()


def configure(config_dict: Dict[str, Any]) -> None:
    """
    Update the global configuration from a dictionary.

    Args:
        config_dict: Configuration dictionary

    Raises:
        ValueError: If configuration values are invalid
        RuntimeError: If called after server has started
    """
    global config
    if config._initialized:
        raise RuntimeError(
            "Configuration cannot be modified after initialization. "
            "Set all configuration values before starting the server."
        )
    config = Config.from_dict(config_dict)
