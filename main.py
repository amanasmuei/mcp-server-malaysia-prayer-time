"""Malaysia Prayer Time UVX Plugin."""

from typing import Any, List, Dict
import asyncio
import sys
import os
import re

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.append(src_path)

from mcp.server import FastMCP
from waktu_solat.client import client as waktu_client
from waktu_solat.models import PrayerTimes, Zone

# Initialize FastMCP server
mcp_server = FastMCP("malaysia-prayer-time")


async def format_prayer_times(prayer_times: List[PrayerTimes]) -> str:
    """Format prayer times data into a readable string."""
    if not prayer_times:
        return "No prayer times available"

    # Get the first prayer time available (most likely today or closest available date)
    prayer_time = prayer_times[0]

    # Format the prayer times in a readable form
    formatted_times = []
    for field in ["imsak", "fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha"]:
        value = getattr(prayer_time, field, None)
        if value:
            # Capitalize the field name for display
            field_name = field.capitalize()
            if field == "syuruk":
                field_name = "Sunrise"
            formatted_times.append(f"{field_name}: {value}")

    time_str = "\n".join(formatted_times)

    return f"""Prayer Times for {prayer_time.date} ({prayer_time.day}):\n{time_str}"""


@mcp_server.tool()
async def debug_api_response(zone_code: str = "SGR03") -> str:
    """Debug the raw API response for a specific zone.

    Args:
        zone_code: Zone code (e.g., 'SGR03') (default: SGR03)
    """
    try:
        # Get raw API response
        async with waktu_client as client:
            data = await client._request("GET", f"/v2/solat/{zone_code}")

        # Format as a string with basic information
        if isinstance(data, dict) and "prayers" in data:
            prayers_count = len(data["prayers"])
            first_prayer = data["prayers"][0] if prayers_count > 0 else "No prayers"

            return f"""API Response for zone {zone_code}:
Zone: {data.get('zone')}
Year: {data.get('year')}
Month: {data.get('month')}
Last Updated: {data.get('last_updated')}
Number of prayers: {prayers_count}
First prayer: {first_prayer}
"""
        else:
            return f"Raw API response: {data}"

    except Exception as e:
        return f"Error debugging API: {str(e)}\nType: {type(e).__name__}\n{str(e.__traceback__)}"


@mcp_server.tool()
async def get_prayer_times(
    city: str = "kuala lumpur", country: str = "malaysia", date: str = "today"
) -> str:
    """Get prayer times for a specific city in Malaysia.

    Args:
        city: Name of the city or zone code (e.g., 'SGR03') (default: kuala lumpur)
        country: Country name (default: malaysia)
        date: Date in YYYY-MM-DD format or 'today' (default: today)
    """
    try:
        # Check if input is a zone code (e.g., PRK02)
        is_zone_code = bool(re.match(r"^[A-Z]{3}\d{2}$", city))

        if is_zone_code:
            # Use the provided zone code directly
            zone_code = city
        else:
            # Convert city to lowercase for matching
            city = city.lower().strip()

            # Get all available zones
            async with waktu_client as client:
                zones = await client.get_zones()

            # Find a matching zone for the city
            zone_match = None
            for zone in zones:
                if city in zone.name.lower():
                    zone_match = zone
                    break

            if not zone_match:
                # Default to Kuala Lumpur if no match
                zone_match = next(
                    (z for z in zones if "kuala lumpur" in z.name.lower()), None
                )
                if not zone_match:
                    return f"Error: Could not find prayer times for {city}. Try using a major city in Malaysia."

            zone_code = zone_match.code

        # Get prayer times for the zone
        async with waktu_client as client:
            prayer_times = await client.get_prayer_times(zone_code)

        if not prayer_times:
            # If no prayer times are available, debug the API response
            debug_info = await debug_api_response(zone_code)
            return f"No prayer times available for {zone_code}.\n\nDebug info:\n{debug_info}"

        return await format_prayer_times(prayer_times)

    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        return f"Error fetching prayer times: {str(e)}\nType: {type(e).__name__}\n{tb}"


@mcp_server.tool()
async def get_prayer_times_by_coordinates(
    latitude: float, longitude: float, date: str = "today"
) -> str:
    """Get prayer times for a specific location using coordinates.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        date: Date in YYYY-MM-DD format or 'today' (default: today)
    """
    try:
        # Define a simplified mapping of major zone codes to coordinates
        # This is a basic implementation - a more complete solution would include all zones
        zone_coordinates = {
            "SGR01": (3.0738, 101.5183),  # Petaling
            "SGR02": (3.3333, 101.5000),  # Gombak
            "SGR03": (3.1570, 101.7123),  # Kuala Lumpur
            "SGR04": (3.0000, 101.7500),  # Sepang
            "PRK01": (4.5943, 101.0901),  # Ipoh
            "PRK02": (4.7500, 100.9167),  # Kuala Kangsar
            "PRK03": (4.0167, 101.0333),  # Teluk Intan
            "PRK04": (5.3333, 100.7333),  # Taiping
            "PNG01": (5.4145, 100.3292),  # George Town
            "JHR01": (1.4927, 103.7414),  # Johor Bahru
            "KDH01": (6.1167, 100.3667),  # Alor Setar
            "TRG01": (5.3333, 103.1500),  # Kuala Terengganu
            "KTN01": (6.1333, 102.2500),  # Kota Bharu
            "MLK01": (2.1889, 102.2511),  # Melaka
        }

        # Calculate distance to each zone
        closest_zone = None
        min_distance = float("inf")

        for zone_code, (zone_lat, zone_lon) in zone_coordinates.items():
            # Simple Euclidean distance calculation
            # In a production system, you might use the Haversine formula for more accuracy
            distance = ((latitude - zone_lat) ** 2 + (longitude - zone_lon) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                closest_zone = zone_code

        # Default to Kuala Lumpur if no close match found
        zone_code = closest_zone or "SGR03"  # Kuala Lumpur

        # Get prayer times for the zone
        async with waktu_client as client:
            prayer_times = await client.get_prayer_times(zone_code)

        if not prayer_times:
            # If no prayer times are available, debug the API response
            debug_info = await debug_api_response(zone_code)
            return f"No prayer times available for coordinates ({latitude}, {longitude}) using zone {zone_code}.\n\nDebug info:\n{debug_info}"

        return await format_prayer_times(prayer_times)

    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        return f"Error fetching prayer times by coordinates: {str(e)}\nType: {type(e).__name__}\n{tb}"


@mcp_server.tool()
async def list_zones() -> str:
    """List all available prayer time zones in Malaysia."""
    try:
        async with waktu_client as client:
            zones = await client.get_zones()

        # Format the zone list
        formatted_zones = []
        for zone in sorted(zones, key=lambda z: (z.negeri, z.code)):
            formatted_zones.append(f"{zone.code}: {zone.name} ({zone.negeri})")

        return "\n".join(formatted_zones)

    except Exception as e:
        return f"Error fetching zones: {str(e)}"


if __name__ == "__main__":
    # Initialize and run the server
    mcp_server.run(transport="stdio")
