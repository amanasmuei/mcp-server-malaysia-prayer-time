"""
Malaysia Prayer Time MCP Server package.

This package provides a Model Context Protocol (MCP) server for accessing
Malaysia prayer time data from waktusolat.app API.

Features:
- Prayer times for all zones in Malaysia
- Current prayer status
- Zone listing and lookup
- Request caching
- Rate limiting
- Input validation
- Graceful shutdown
- Health checks

Example:
    >>> from waktu_solat import WaktuSolatServer
    >>> server = WaktuSolatServer()
    >>> asyncio.run(server.run())
"""

from typing import Final

from .models import PrayerTimes, Zone
from .server import WaktuSolatServer
from .config import config, configure, CacheConfig, HTTPConfig
from .client import APIError, ValidationError, ConnectionError

# Package version - update this when making releases
__version__: Final[str] = "0.2.0"

# Package metadata
__title__: Final[str] = "mcp-server-malaysia-prayer-time"
__description__: Final[str] = "MCP Server for Malaysia Prayer Times"
__author__: Final[str] = "Your Name"
__license__: Final[str] = "MIT"

__all__ = [
    # Main classes
    "WaktuSolatServer",
    "PrayerTimes",
    "Zone",
    # Configuration
    "config",
    "configure",
    "CacheConfig",
    "HTTPConfig",
    # Exceptions
    "APIError",
    "ValidationError",
    "ConnectionError",
    # Version
    "__version__",
]
