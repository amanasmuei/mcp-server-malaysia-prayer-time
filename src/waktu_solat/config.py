"""
Configuration management for the Malaysia Prayer Time MCP Server.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class CacheConfig:
    type: str = "memory"  # or "redis"
    ttl: int = 3600  # Cache TTL in seconds
    max_size: int = 1000  # Maximum number of items in cache


@dataclass
class HTTPConfig:
    timeout: int = 10  # Timeout in seconds
    max_retries: int = 3
    pool_connections: int = 10
    base_url: str = "https://api.waktusolat.app/api/v2"


@dataclass
class Config:
    cache: CacheConfig
    http: HTTPConfig

    @classmethod
    def default(cls) -> "Config":
        """Create a default configuration instance."""
        return cls(cache=CacheConfig(), http=HTTPConfig())

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create a configuration instance from a dictionary."""
        cache_config = CacheConfig(**config_dict.get("cache", {}))
        http_config = HTTPConfig(**config_dict.get("http", {}))
        return cls(cache=cache_config, http=http_config)


# Global configuration instance
config = Config.default()


def configure(config_dict: Dict[str, Any]) -> None:
    """Update the global configuration from a dictionary."""
    global config
    config = Config.from_dict(config_dict)
