"""Malaysia Prayer Time UVX Plugin."""

from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("malaysia-prayer-time")

# Constants
API_BASE = "https://api.pray.zone/v2/times"
USER_AGENT = "malaysia-prayer-time/1.0"


async def make_prayer_request(url: str, params: dict) -> dict[str, Any] | None:
    """Make a request to the Prayer API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url, headers=headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def format_prayer_times(data: dict) -> str:
    """Format prayer times data into a readable string."""
    if "error" in data:
        return f"Error fetching prayer times: {data['error']}"

    try:
        times = data["results"]["datetime"][0]["times"]
        return f"""Prayer Times:
Imsak: {times['Imsak']}
Fajr: {times['Fajr']}
Sunrise: {times['Sunrise']}
Dhuhr: {times['Dhuhr']}
Asr: {times['Asr']}
Sunset: {times['Sunset']}
Maghrib: {times['Maghrib']}
Isha: {times['Isha']}
Midnight: {times['Midnight']}"""
    except (KeyError, IndexError):
        return "Unable to parse prayer times data"


@mcp.tool()
async def get_prayer_times(
    city: str = "kuala lumpur", country: str = "malaysia", date: str = "today"
) -> str:
    """Get prayer times for a specific city in Malaysia.

    Args:
        city: Name of the city (default: kuala lumpur)
        country: Country name (default: malaysia)
        date: Date in YYYY-MM-DD format or 'today' (default: today)
    """
    params = {"city": city, "country": country, "date": date}

    data = await make_prayer_request(f"{API_BASE}/today.json", params)
    return format_prayer_times(data)


@mcp.tool()
async def get_prayer_times_by_coordinates(
    latitude: float, longitude: float, date: str = "today"
) -> str:
    """Get prayer times for a specific location using coordinates.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        date: Date in YYYY-MM-DD format or 'today' (default: today)
    """
    params = {"latitude": latitude, "longitude": longitude, "date": date}

    data = await make_prayer_request(f"{API_BASE}/today.json", params)
    return format_prayer_times(data)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
