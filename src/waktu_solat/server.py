#!/usr/bin/env python3

"""
Malaysia Prayer Time MCP Server
This server implements access to Malaysia Prayer Time data
using the API from github.com/mptwaktusolat/api-waktusolat.
"""

import sys
import json
import asyncio
import logging
from typing import Dict, Any, List
from . import config
from .client import client, APIError
from .models import PrayerTimes, Zone
from .cache import cached

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WaktuSolatServer:
    def __init__(self):
        self.server_info = {
            "name": "Malaysia Prayer Time MCP Server",
            "version": "0.2.0",
        }
        self.tools = {
            "get_prayer_times": self.handle_get_prayer_times,
            "list_zones": self.handle_list_zones,
            "get_current_prayer": self.handle_get_current_prayer,
        }

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

    async def handle_get_prayer_times(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_prayer_times tool request."""
        zone = args.get("zone")
        if not zone:
            return {"error": "Zone is required"}
        try:
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
        except APIError as e:
            logger.error(f"API Error in get_prayer_times: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in get_prayer_times")
            return {"error": f"Internal server error: {str(e)}"}

    async def handle_list_zones(self, _: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_zones tool request."""
        try:
            zones = await self.get_zones()
            formatted_zones = "\n".join(
                f"{zone.code}: {zone.name} ({zone.negeri})" for zone in zones
            )
            return {"content": [{"type": "text", "text": formatted_zones}]}
        except APIError as e:
            logger.error(f"API Error in list_zones: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in list_zones")
            return {"error": f"Internal server error: {str(e)}"}

    async def handle_get_current_prayer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_current_prayer tool request."""
        zone = args.get("zone")
        if not zone:
            return {"error": "Zone is required"}
        try:
            current_prayer = await self.get_current_prayer(zone)
            return {
                "content": [
                    {"type": "text", "text": json.dumps(current_prayer, indent=2)}
                ]
            }
        except APIError as e:
            logger.error(f"API Error in get_current_prayer: {e}")
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
        if method == "listTools":
            return self.get_tools_list()
        elif method == "callTool":
            tool_name = request.get("params", {}).get("name")
            tool_args = request.get("params", {}).get("arguments", {})
            if tool_name in self.tools:
                try:
                    return await self.tools[tool_name](tool_args)
                except Exception as e:
                    logger.exception(f"Error handling tool {tool_name}")
                    return {"error": f"Tool execution failed: {str(e)}"}
            return {"error": f"Unknown tool: {tool_name}"}
        return {"error": f"Unknown method: {method}"}

    async def run(self):
        """Start the server using stdio transport."""
        logger.info("Starting Waktu Solat MCP Server...")
        while True:
            try:
                request_line = await asyncio.get_event_loop().run_in_executor(
                    None, input
                )
                if not request_line:
                    continue
                request = json.loads(request_line)
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
            except EOFError:
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON request: {e}")
                print(json.dumps({"error": "Invalid JSON request"}), flush=True)
            except Exception as e:
                logger.exception("Unexpected server error")
                print(json.dumps({"error": f"Server error: {str(e)}"}), flush=True)


def main():
    """Main entry point."""
    server = WaktuSolatServer()
    try:
        asyncio.run(server.run())
    except Exception as e:
        logger.exception("Fatal server error")
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
