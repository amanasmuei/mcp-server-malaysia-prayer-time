"""
Malaysia Prayer Time UVX Plugin

This module serves as the entry point for the UVX plugin integration
with Claude Desktop and other UVX-compatible applications.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List

from waktu_solat.client import client, APIError, ValidationError
from waktu_solat.models import PrayerTimes, Zone
from waktu_solat.cache import cached

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MalaysiaPrayerTimePlugin:
    """UVX Plugin implementation for Malaysia prayer times."""

    def __init__(self):
        """Initialize the plugin with necessary resources."""
        logger.info("Initializing Malaysia Prayer Time UVX Plugin...")

    @cached(ttl=3600)  # Cache prayer times for 1 hour
    async def get_prayer_times(self, zone: str) -> List[PrayerTimes]:
        """Fetch prayer times for a specific zone with caching."""
        async with client as http:
            return await http.get_prayer_times(zone)

    @cached(ttl=86400)  # Cache zones for 24 hours
    async def get_zones(self) -> List[Zone]:
        """Fetch all available zones with caching."""
        async with client as http:
            return await http.get_zones()

    @cached(ttl=60)  # Cache current prayer for 1 minute
    async def get_current_prayer(self, zone: str) -> Dict:
        """Get the current prayer time status for a zone with caching."""
        async with client as http:
            return await http.get_current_prayer(zone)

    async def handle_get_prayer_times(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_prayer_times tool request.

        Args:
            params: Dictionary containing tool parameters including 'zone'

        Returns:
            Dictionary containing prayer times data
        """
        try:
            zone = params.get("zone")
            if not zone:
                return {"error": "Zone is required"}

            prayer_times = await self.get_prayer_times(zone)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            [pt.model_dump() for pt in prayer_times], indent=2
                        ),
                    }
                ]
            }
        except ValidationError as e:
            logger.warning(f"Validation error in get_prayer_times: {e}")
            return {"error": str(e)}
        except APIError as e:
            logger.error(f"API error in get_prayer_times: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in get_prayer_times")
            return {"error": f"Internal server error: {str(e)}"}

    async def handle_list_zones(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle list_zones tool request.

        Returns:
            Dictionary containing formatted list of zones
        """
        try:
            zones = await self.get_zones()
            formatted_zones = "\n".join(
                f"{zone.code}: {zone.name} ({zone.negeri})"
                for zone in sorted(zones, key=lambda z: (z.negeri, z.code))
            )
            return {"content": [{"type": "text", "text": formatted_zones}]}
        except APIError as e:
            logger.error(f"API error in list_zones: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in list_zones")
            return {"error": f"Internal server error: {str(e)}"}

    async def handle_get_current_prayer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_current_prayer tool request.

        Args:
            params: Dictionary containing tool parameters including 'zone'

        Returns:
            Dictionary containing current prayer data
        """
        try:
            zone = params.get("zone")
            if not zone:
                return {"error": "Zone is required"}

            current_prayer = await self.get_current_prayer(zone)

            return {
                "content": [
                    {"type": "text", "text": json.dumps(current_prayer, indent=2)}
                ]
            }
        except ValidationError as e:
            logger.warning(f"Validation error in get_current_prayer: {e}")
            return {"error": str(e)}
        except APIError as e:
            logger.error(f"API error in get_current_prayer: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in get_current_prayer")
            return {"error": f"Internal server error: {str(e)}"}


# UVX Plugin instance
plugin = MalaysiaPrayerTimePlugin()


# UVX entry points - these functions will be called by the UVX runtime
async def get_prayer_times(params: Dict[str, Any]) -> Dict[str, Any]:
    """UVX entry point for get_prayer_times tool."""
    return await plugin.handle_get_prayer_times(params)


async def list_zones(params: Dict[str, Any]) -> Dict[str, Any]:
    """UVX entry point for list_zones tool."""
    return await plugin.handle_list_zones(params)


async def get_current_prayer(params: Dict[str, Any]) -> Dict[str, Any]:
    """UVX entry point for get_current_prayer tool."""
    return await plugin.handle_get_current_prayer(params)
