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

        if not isinstance(data, list):
            raise ResponseError("Invalid prayer times data format in response")

        # Transform waktusolat.app v2 format to our model format
        prayer_times = []
        for item in data:
            transformed = {
                "date": item.get("date"),
                "day": datetime.strptime(item.get("date", ""), "%Y-%m-%d").strftime(
                    "%A"
                ),
                "imsak": item.get("imsak"),
                "fajr": item.get("fajr"),
                "syuruk": item.get("syuruk"),
                "dhuhr": item.get("dhuhr"),
                "asr": item.get("asr"),
                "maghrib": item.get("maghrib"),
                "isha": item.get("isha"),
            }
            try:
                prayer_times.append(PrayerTimes.model_validate(transformed))
            except ValueError:
                logger.warning(f"Skipping invalid prayer time data: {item}")
                continue

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

        if not isinstance(data, list):
            raise ResponseError("Invalid prayer times data format in response")

        # Find today's prayer times
        today = datetime.now().strftime("%Y-%m-%d")
        today_data = next((item for item in data if item.get("date") == today), None)

        if not today_data:
            raise ResponseError("No prayer times available for today")

        times = {
            "fajr": today_data.get("fajr"),
            "syuruk": today_data.get("syuruk"),
            "dhuhr": today_data.get("dhuhr"),
            "asr": today_data.get("asr"),
            "maghrib": today_data.get("maghrib"),
            "isha": today_data.get("isha"),
        }

        now = datetime.now().time()
        prayers = ["fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha"]
        current_prayer = None
        next_prayer = None

        for i, prayer in enumerate(prayers):
            if prayer not in times:
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
