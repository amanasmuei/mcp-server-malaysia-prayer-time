"""
Async HTTP client for interacting with the waktusolat.app API.

This module provides a high-level interface to the waktusolat.app API with:
- Automatic connection pooling and timeouts
- Retry logic for transient failures
- Type-safe responses using Pydantic models
- Comprehensive error handling
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, TypeVar, Type
import httpx
from pydantic import BaseModel

from .config import config
from .models import PrayerTimes, Zone

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for more detailed logging

# Add stream handler if no handlers are configured
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

T = TypeVar("T", bound=BaseModel)


class APIError(Exception):
    """Base exception for API errors."""

    pass


class ValidationError(APIError):
    """Raised when input validation fails."""

    pass


class ResponseError(APIError):
    """Raised when the API response is invalid."""

    pass


class ConnectionError(APIError):
    """Raised when connection to the API fails."""

    pass


class HTTPClient:
    """Async HTTP client for the waktusolat.app API."""

    def __init__(self) -> None:
        """Initialize a new HTTP client instance."""
        self._client: Optional[httpx.AsyncClient] = httpx.AsyncClient(
            timeout=httpx.Timeout(config.http.timeout),
            limits=httpx.Limits(
                max_connections=config.http.pool_connections,
                max_keepalive_connections=config.http.pool_connections,
            ),
        )
        self._base_url: str = config.http.base_url.rstrip("/")
        self._retry_count: int = 3

        # Validate base URL
        if not re.match(r"^https?://", self._base_url):
            raise ValidationError("Base URL must start with http:// or https://")

    async def __aenter__(self) -> "HTTPClient":
        """Setup the async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup the async context."""
        if self._client:
            try:
                logger.debug("Closing HTTP client connection")
                await self._client.aclose()
            except Exception as e:
                logger.error(f"Error closing HTTP client: {e}")
            finally:
                logger.debug("HTTP client connection closed")
                self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get the httpx client instance, creating it if needed.

        Returns:
            The httpx AsyncClient instance

        Raises:
            RuntimeError: If the client cannot be initialized
        """
        if not self._client:
            logger.debug("Creating new HTTP client instance")
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(config.http.timeout),
                limits=httpx.Limits(
                    max_connections=config.http.pool_connections,
                    max_keepalive_connections=config.http.pool_connections,
                ),
            )
        return self._client

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            **kwargs: Additional arguments to pass to httpx

        Returns:
            API response data as dictionary

        Raises:
            RuntimeError: If client is not initialized
            APIError: If the request fails after retries
        """
        if not path.startswith("/"):
            path = f"/{path}"

        url = f"{self._base_url}{path}"
        client = await self._get_client()
        logger.debug(f"Making {method} request to {url}")

        # Add standard headers
        headers = {
            "User-Agent": "MalaysiaPrayerTimeMCP/0.2.0",
            "Accept": "application/json",
            **kwargs.get("headers", {}),
        }
        kwargs["headers"] = headers

        for attempt in range(self._retry_count):
            try:
                response = await self._client.request(method, url, **kwargs)
                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError as e:
                    # Log the actual response content for debugging
                    logger.error(f"Invalid JSON response content: {response.text}")
                    raise ResponseError(f"Invalid JSON response: {str(e)}")

                if not data:
                    raise ResponseError("Empty response from API")

                # Log successful response data for debugging
                logger.debug(f"Successfully received response from {url}: {data}")
                return data

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                if attempt == self._retry_count - 1:
                    logger.error(error_msg)
                    raise APIError(error_msg)
                logger.warning(f"Request failed (attempt {attempt + 1}): {error_msg}")

            except httpx.RequestError as e:
                error_msg = f"Request failed: {str(e)}"
                if attempt == self._retry_count - 1:
                    logger.error(error_msg)
                    raise ConnectionError(error_msg)
                logger.warning(f"Request failed (attempt {attempt + 1}): {error_msg}")

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(error_msg)
                raise APIError(error_msg)

    async def get_prayer_times(self, zone: str) -> List[PrayerTimes]:
        """
        Fetch prayer times for a specific zone.

        Args:
            zone: Zone code (e.g., 'SGR01')

        Returns:
            List of prayer times for the zone

        Raises:
            ValidationError: If zone format is invalid
            APIError: If the request fails
        """
        if not re.match(r"^[A-Z]{3}\d{2}$", zone):
            raise ValidationError("Invalid zone format. Expected format: 'ABC12'")

        logger.info(f"Fetching prayer times for zone: {zone}")
        data = await self._request("GET", f"/v2/solat/{zone}")

        # Check if the response is the new format (object with prayers array)
        if (
            isinstance(data, dict)
            and "prayers" in data
            and isinstance(data["prayers"], list)
        ):
            prayers_data = data["prayers"]
        elif isinstance(data, list):
            # Fallback to old format (direct array)
            prayers_data = data
        else:
            logger.error(f"Invalid data format received: {type(data)}. Data: {data}")
            raise ResponseError(
                f"Invalid prayer times data format in response. Received: {type(data).__name__}, data: {data}"
            )

        # If there are no prayer times, return an empty list
        if not prayers_data:
            logger.warning(f"No prayer times found for zone {zone}")
            return []

        # Transform waktusolat.app v2 format to our model format
        prayer_times = []
        for item in prayers_data:
            # Check if we have all the required fields
            if not all(
                key in item
                for key in ["day", "fajr", "dhuhr", "asr", "maghrib", "isha", "syuruk"]
            ):
                logger.warning(f"Skipping incomplete prayer time data: {item}")
                continue

            # Handle different date formats in the new API
            date_str = None
            if "date" in item:
                date_str = item.get("date")
            else:
                # Reconstruct date from the current API response
                # Extract year and month from the parent object if available
                year = (
                    data.get("year", datetime.now().year)
                    if isinstance(data, dict)
                    else datetime.now().year
                )
                month = (
                    data.get("month", datetime.now().strftime("%b").upper())
                    if isinstance(data, dict)
                    else datetime.now().strftime("%b").upper()
                )
                day = item.get("day", 1)

                # Try to parse the month if it's a string
                if isinstance(month, str):
                    try:
                        month_num = datetime.strptime(month, "%b").month
                    except ValueError:
                        try:
                            month_num = datetime.strptime(month, "%B").month
                        except ValueError:
                            # Default to current month if parsing fails
                            month_num = datetime.now().month
                else:
                    month_num = month

                date_str = f"{year}-{month_num:02d}-{day:02d}"

            # Convert Unix timestamps to time strings if needed
            time_fields = ["fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha"]
            times = {}

            for field in time_fields:
                time_value = item.get(field)
                if time_value is None:
                    times[field] = None
                    continue

                # Try to convert timestamp to time string
                if isinstance(time_value, int):
                    try:
                        # Convert to HH:MM format - API returns Unix timestamp in seconds
                        dt = datetime.fromtimestamp(time_value)
                        times[field] = dt.strftime("%H:%M")
                    except (ValueError, OSError, OverflowError) as e:
                        logger.warning(
                            f"Error converting timestamp {time_value} for {field}: {e}"
                        )
                        times[field] = None
                else:
                    # Already a string, validate format or None
                    times[field] = time_value if isinstance(time_value, str) else None

            transformed = {
                "date": date_str,
                "day": (
                    datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
                    if date_str
                    else ""
                ),
                "imsak": item.get("imsak"),  # Might be None in new API
                "fajr": times["fajr"],
                "syuruk": times["syuruk"],
                "dhuhr": times["dhuhr"],
                "asr": times["asr"],
                "maghrib": times["maghrib"],
                "isha": times["isha"],
            }

            try:
                prayer_times.append(PrayerTimes.model_validate(transformed))
            except ValueError as e:
                logger.warning(f"Skipping invalid prayer time data: {item}. Error: {e}")
                continue

        # If we couldn't parse any prayer times, return empty
        if not prayer_times:
            logger.warning(f"Could not parse any valid prayer times for zone {zone}")
            return []

        return prayer_times

    async def get_zones(self) -> List[Zone]:
        """
        Fetch all available zones.

        Returns:
            List of available prayer time zones

        Raises:
            APIError: If the request fails
        """
        logger.info("Fetching available zones")
        data = await self._request("GET", "/zones")

        logger.debug(f"Raw zones response: {data}")

        if not isinstance(data, list):
            raise ResponseError("Invalid zones data format in response")

        # Transform waktusolat.app format to our model format
        zones = []
        for item in data:
            if not all(k in item for k in ["daerah", "jakimCode", "negeri"]):
                logger.warning(
                    f"Skipping zone data with missing required fields: {item}"
                )
                continue

            # Skip empty or invalid values
            if not item["daerah"] or not item["jakimCode"] or not item["negeri"]:
                logger.warning(f"Skipping zone data with empty required fields: {item}")
                continue

            transformed = {
                "name": item["daerah"].strip(),
                "code": item["jakimCode"].strip(),
                "negeri": item["negeri"].strip(),
            }

            # Extra validation before attempting model validation
            if not all(transformed.values()):
                logger.warning(
                    f"Skipping zone with empty values after stripping: {transformed}"
                )
                continue

            try:
                logger.debug(f"Attempting to validate zone data: {transformed}")
                validated_zone = Zone.model_validate(transformed)
                logger.debug(f"Successfully validated zone: {validated_zone}")
                zones.append(validated_zone)
            except ValueError as e:
                logger.warning(
                    f"Validation failed for zone {item['jakimCode']}: {str(e)}. "
                    f"Transformed data: {transformed}"
                )
                continue

        if not zones:
            logger.error("No valid zones found in API response")
            raise ResponseError("Failed to parse any valid zones from API response")

        return zones

    async def get_current_prayer(self, zone: str) -> Dict[str, Any]:
        """
        Get the current prayer time status for a zone.

        Args:
            zone: Zone code (e.g., 'SGR01')

        Returns:
            Dictionary containing current prayer time information

        Raises:
            ValidationError: If zone format is invalid
            APIError: If the request fails
        """
        if not re.match(r"^[A-Z]{3}\d{2}$", zone):
            raise ValidationError("Invalid zone format. Expected format: 'ABC12'")

        logger.info(f"Fetching current prayer time for zone: {zone}")
        # Get today's prayer times and calculate current prayer
        data = await self._request("GET", f"/v2/solat/{zone}")

        # Check if the response is the new format (object with prayers array)
        if (
            isinstance(data, dict)
            and "prayers" in data
            and isinstance(data["prayers"], list)
        ):
            prayers_data = data["prayers"]
        elif isinstance(data, list):
            # Fallback to old format (direct array)
            prayers_data = data
        else:
            logger.error(f"Invalid data format received: {type(data)}. Data: {data}")
            raise ResponseError(
                f"Invalid prayer times data format in response. Received: {type(data).__name__}, data: {data}"
            )

        # Find today's prayer times
        today = datetime.now().strftime("%Y-%m-%d")
        today_data = None

        # First try to find an exact date match
        for item in prayers_data:
            if "date" in item and item.get("date") == today:
                today_data = item
                break

        # If not found, try to match by day number for the current month
        if not today_data:
            current_day = datetime.now().day
            for item in prayers_data:
                if item.get("day") == current_day:
                    today_data = item
                    break

        # If still not found, use the first available day
        if not today_data and prayers_data:
            logger.warning(
                f"No exact date match found for {today}. Using first available day."
            )
            today_data = prayers_data[0]

        if not today_data:
            raise ResponseError("No prayer times available for today")

        # Convert Unix timestamps to time strings if needed
        time_fields = ["fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha"]
        times = {}

        for field in time_fields:
            time_value = today_data.get(field)
            if time_value is None:
                times[field] = None
                continue

            # Try to convert timestamp to time string
            if isinstance(time_value, int):
                try:
                    # Convert to HH:MM format - API returns Unix timestamp in seconds
                    dt = datetime.fromtimestamp(time_value)
                    times[field] = dt.strftime("%H:%M")
                except (ValueError, OSError, OverflowError) as e:
                    logger.warning(
                        f"Error converting timestamp {time_value} for {field}: {e}"
                    )
                    times[field] = None
            else:
                # Already a string, validate format or None
                times[field] = time_value if isinstance(time_value, str) else None

        now = datetime.now().time()
        prayers = ["fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha"]
        current_prayer = None
        next_prayer = None

        for i, prayer in enumerate(prayers):
            if prayer not in times or times[prayer] is None:
                continue
            try:
                prayer_time = datetime.strptime(times[prayer], "%H:%M").time()
                if now < prayer_time:
                    if i > 0:
                        current_prayer = prayers[i - 1]
                    next_prayer = prayer
                    break
            except ValueError:
                logger.warning(f"Invalid time format for {prayer}: {times[prayer]}")

        # If we've passed all prayers, current is isha and next is tomorrow's fajr
        if not current_prayer and not next_prayer:
            current_prayer = "isha"
            next_prayer = "fajr"

        return {
            "current_prayer": current_prayer,
            "next_prayer": next_prayer,
            "prayer_times": times,
        }


# Global client instance
client = HTTPClient()
