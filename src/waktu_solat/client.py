"""
Async HTTP client for interacting with the waktusolat.app API.
"""

from typing import List, Dict, Any, Optional
import httpx
from .config import config
from .models import PrayerTimes, Zone


class APIError(Exception):
    """Base exception for API errors."""

    pass


class HTTPClient:
    """Async HTTP client for the waktusolat.app API."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._base_url = config.http.base_url
        self._timeout = httpx.Timeout(config.http.timeout)

    async def __aenter__(self) -> "HTTPClient":
        """Setup the async context."""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=config.http.pool_connections,
                    max_keepalive_connections=config.http.pool_connections,
                ),
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup the async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        url = f"{self._base_url}{path}"

        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status()
            data = response.json()

            if not data:
                raise APIError("Empty response from API")

            return data

        except httpx.HTTPStatusError as e:
            raise APIError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}")
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}")

    async def get_prayer_times(self, zone: str) -> List[PrayerTimes]:
        """Fetch prayer times for a specific zone."""
        data = await self._request("GET", f"/solat/{zone}")

        if not data.get("data"):
            raise APIError("No prayer times data in response")

        return [PrayerTimes.model_validate(item) for item in data["data"]]

    async def get_zones(self) -> List[Zone]:
        """Fetch all available zones."""
        data = await self._request("GET", "/zones")

        if not data.get("data"):
            raise APIError("No zones data in response")

        return [Zone.model_validate(item) for item in data["data"]]

    async def get_current_prayer(self, zone: str) -> Dict[str, Any]:
        """Get the current prayer time status for a zone."""
        data = await self._request("GET", f"/current-time/{zone}")

        if not data:
            raise APIError("No current prayer data in response")

        return data


# Global client instance
client = HTTPClient()
