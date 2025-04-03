#!/usr/bin/env python3

"""
Malaysia Prayer Time MCP Server

This server implements access to Malaysia Prayer Time data using the API
from github.com/mptwaktusolat/api-waktusolat. It provides three main tools:
- get_prayer_times: Fetch prayer times for a specific zone
- list_zones: List all available prayer time zones
- get_current_prayer: Get current prayer time status for a zone

Features:
- Input validation
- Response caching
- Rate limiting
- Graceful shutdown
- Health checks
"""

import asyncio
import logging
import json
import re
import signal
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Awaitable, Set

from . import config
from .client import client, APIError, ValidationError
from .models import PrayerTimes, Zone
from .cache import cached

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Simple rate limiter implementation."""

    requests_per_minute: int
    window_size: int = 60  # seconds
    _requests: Dict[str, List[float]] = field(default_factory=dict)

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        if client_id not in self._requests:
            self._requests[client_id] = []

        # Remove old requests
        self._requests[client_id] = [
            t for t in self._requests[client_id] if now - t < self.window_size
        ]

        # Check rate limit
        if len(self._requests[client_id]) >= self.requests_per_minute:
            return False

        # Add new request
        self._requests[client_id].append(now)
        return True


class WaktuSolatServer:
    """MCP server implementation for Malaysia prayer times."""

    def __init__(self):
        """Initialize the server with configuration and tools."""
        self.server_info: Dict[str, str] = {
            "name": "Malaysia Prayer Time MCP Server",
            "version": "0.2.0",
        }
        self.tools: Dict[str, Callable] = {
            "get_prayer_times": self.handle_get_prayer_times,
            "list_zones": self.handle_list_zones,
            "get_current_prayer": self.handle_get_current_prayer,
        }
        self.rate_limiter = RateLimiter(requests_per_minute=60)
        self.active_requests: Set[asyncio.Task] = set()
        self.shutdown_event: asyncio.Event = asyncio.Event()

        # Setup signal handlers for graceful shutdown
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_shutdown_signal)

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

    def _handle_shutdown_signal(self, signum: int, _) -> None:
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        self.shutdown_event.set()

    def _validate_zone(self, zone: Optional[str]) -> None:
        """Validate zone code format."""
        if not zone:
            raise ValidationError("Zone is required")
        if not re.match(r"^[A-Z]{3}\d{2}$", zone):
            raise ValidationError("Invalid zone format. Expected format: ABC12")

    async def handle_get_prayer_times(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_prayer_times tool request.

        Args:
            args: Dictionary containing tool arguments including 'zone'

        Returns:
            Dictionary containing prayer times data or error message

        Example:
            Input: {"zone": "SGR01"}
            Output: {
                "content": [{
                    "type": "text",
                    "text": "[{\"date\": \"2024-04-04\", ...}]"
                }]
            }
        """
        try:
            self._validate_zone(args.get("zone"))
            prayer_times = await self.get_prayer_times(args["zone"])

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

    async def handle_list_zones(self, _: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle list_zones tool request.

        Returns:
            Dictionary containing formatted list of zones or error message

        Example:
            Output: {
                "content": [{
                    "type": "text",
                    "text": "SGR01: Gombak (Selangor)\nKUL01: Kuala Lumpur..."
                }]
            }
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

    async def handle_get_current_prayer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_current_prayer tool request.

        Args:
            args: Dictionary containing tool arguments including 'zone'

        Returns:
            Dictionary containing current prayer data or error message

        Example:
            Input: {"zone": "SGR01"}
            Output: {
                "content": [{
                    "type": "text",
                    "text": "{\"prayer\": \"Asr\", \"time\": \"16:27\"...}"
                }]
            }
        """
        try:
            self._validate_zone(args.get("zone"))
            current_prayer = await self.get_current_prayer(args["zone"])

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

    def get_tools_list(self) -> Dict[str, Any]:
        """Get list of available tools."""
        return {
            "tools": [
                {
                    "name": "get_prayer_times",
                    "description": "Get prayer times for a specific zone in Malaysia",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "zone": {
                                "type": "string",
                                "description": "The zone code (e.g., 'SGR01', 'KUL01', etc.)",
                            }
                        },
                        "required": ["zone"],
                    },
                },
                {
                    "name": "list_zones",
                    "description": "List all available prayer time zones in Malaysia",
                    "inputSchema": {"type": "object", "properties": {}},
                },
                {
                    "name": "get_current_prayer",
                    "description": "Get the current prayer time status for a specific zone",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "zone": {
                                "type": "string",
                                "description": "The zone code (e.g., 'SGR01', 'KUL01', etc.)",
                            }
                        },
                        "required": ["zone"],
                    },
                },
            ]
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        request_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "name": self.server_info["name"],
                    "version": self.server_info["version"],
                    "capabilities": {},
                },
            }
        elif method == "listTools":
            return {"jsonrpc": "2.0", "id": request_id, "result": self.get_tools_list()}
        elif method == "callTool":
            tool_name = request.get("params", {}).get("name")
            tool_args = request.get("params", {}).get("arguments", {})
            if tool_name in self.tools:
                try:
                    result = await self.tools[tool_name](tool_args)
                    return {"jsonrpc": "2.0", "id": request_id, "result": result}
                except Exception as e:
                    logger.exception(f"Error handling tool {tool_name}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution failed: {str(e)}",
                        },
                    }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }

    async def health_check(self) -> None:
        """Perform periodic health checks."""
        # Disable health check for now to prevent duplicate requests
        while not self.shutdown_event.is_set():
            await asyncio.sleep(300)  # Just sleep without making requests

    async def run(self) -> None:
        """Start the server using stdio transport."""
        logger.info(
            f"Starting {self.server_info['name']} v{self.server_info['version']}..."
        )

        # Start health check task
        health_check_task = asyncio.create_task(self.health_check())
        self.active_requests.add(health_check_task)
        health_check_task.add_done_callback(self.active_requests.discard)

        while not self.shutdown_event.is_set():
            try:
                request_line = await asyncio.get_event_loop().run_in_executor(
                    None, input
                )
                if not request_line:
                    continue

                # Parse and validate request
                try:
                    request = json.loads(request_line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON request: {e}")
                    print(json.dumps({"error": "Invalid JSON request"}), flush=True)
                    continue

                # Apply rate limiting
                client_id = request.get("params", {}).get("client_id", "default")
                if not self.rate_limiter.is_allowed(client_id):
                    logger.warning(f"Rate limit exceeded for client: {client_id}")
                    print(json.dumps({"error": "Rate limit exceeded"}), flush=True)
                    continue

                # Handle request
                request_task = asyncio.create_task(self.handle_request(request))
                self.active_requests.add(request_task)
                request_task.add_done_callback(self.active_requests.discard)

                response = await request_task
                print(json.dumps(response), flush=True)

            except EOFError:
                logger.info("Received EOF, initiating shutdown...")
                self.shutdown_event.set()
                break
            except Exception as e:
                logger.exception("Unexpected server error")
                print(json.dumps({"error": f"Server error: {str(e)}"}), flush=True)

        # Graceful shutdown
        logger.info("Shutting down server...")
        await self._cleanup()
        logger.info("Server shutdown complete")

    async def _cleanup(self) -> None:
        """Clean up resources during shutdown."""
        try:
            if self.active_requests:
                logger.info(
                    f"Waiting for {len(self.active_requests)} active requests..."
                )
                await asyncio.gather(*self.active_requests, return_exceptions=True)

            # Ensure client is properly closed
            if hasattr(client, "_client") and client._client:
                await client._client.aclose()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main() -> None:
    """
    Main entry point.

    Sets up the server and handles the main event loop and error cases.
    """
    server = WaktuSolatServer()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.run())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.exception("Fatal server error")
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
