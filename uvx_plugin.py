"""
Malaysia Prayer Time UVX Plugin

This module serves as the entry point for the UVX plugin integration
with Claude Desktop and other UVX-compatible applications.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Mock data for testing
MOCK_PRAYER_TIMES = [
    {
        "date": "2024-04-04",
        "day": "Thursday",
        "hijri": "1445-09-24",
        "imsak": "05:48",
        "fajr": "05:58",
        "syuruk": "07:12",
        "dhuhr": "13:19",
        "asr": "16:25",
        "maghrib": "19:21",
        "isha": "20:30",
    }
]

MOCK_ZONES = [
    {"code": "SGR01", "name": "Gombak", "negeri": "Selangor"},
    {"code": "KUL01", "name": "Kuala Lumpur", "negeri": "W.P. Kuala Lumpur"},
    {"code": "JHR01", "name": "Pulau Aur", "negeri": "Johor"},
]

MOCK_CURRENT_PRAYER = {
    "prayer": "Asr",
    "time": "16:25",
    "next_prayer": "Maghrib",
    "next_prayer_time": "19:21",
    "remaining_time": "2:56",
}


# UVX tool implementation functions
def get_prayer_times(zone: str) -> Dict[str, Any]:
    """
    Get prayer times for a specific zone in Malaysia.

    Args:
        zone: The zone code (e.g., 'SGR01', 'KUL01')

    Returns:
        Dictionary containing prayer times data
    """
    logger.info(f"Getting prayer times for zone: {zone}")

    # For now, return mock data
    return {
        "content": [{"type": "text", "text": json.dumps(MOCK_PRAYER_TIMES, indent=2)}]
    }


def list_zones() -> Dict[str, Any]:
    """
    List all available prayer time zones in Malaysia.

    Returns:
        Dictionary containing formatted list of zones
    """
    logger.info("Listing all zones")

    # For now, return mock data
    formatted_zones = "\n".join(
        f"{zone['code']}: {zone['name']} ({zone['negeri']})"
        for zone in sorted(MOCK_ZONES, key=lambda z: (z["negeri"], z["code"]))
    )

    return {"content": [{"type": "text", "text": formatted_zones}]}


def get_current_prayer(zone: str) -> Dict[str, Any]:
    """
    Get the current prayer time status for a zone.

    Args:
        zone: The zone code (e.g., 'SGR01', 'KUL01')

    Returns:
        Dictionary containing current prayer data
    """
    logger.info(f"Getting current prayer for zone: {zone}")

    # For now, return mock data
    return {
        "content": [{"type": "text", "text": json.dumps(MOCK_CURRENT_PRAYER, indent=2)}]
    }
