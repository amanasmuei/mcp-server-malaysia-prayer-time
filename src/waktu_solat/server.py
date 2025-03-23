#!/usr/bin/env python3

"""
Malaysia Prayer Time MCP Server
This server implements access to Malaysia Prayer Time data
using the API from github.com/mptwaktusolat/api-waktusolat.
"""

import sys
import json
import asyncio
from typing import List, Dict, Any
import requests
from .models import PrayerTimes, Zone

API_BASE_URL = "https://api.waktusolat.app/api/v2"

class WaktuSolatServer:
    def __init__(self):
        self.server_info = {
            "name": "Malaysia Prayer Time MCP Server",
            "version": "0.1.0"
        }
        self.tools = {
            "get_prayer_times": self.handle_get_prayer_times,
            "list_zones": self.handle_list_zones,
            "get_current_prayer": self.handle_get_current_prayer
        }

    async def get_prayer_times(self, zone: str) -> List[PrayerTimes]:
        """Helper function to fetch prayer times for a specific zone"""
        try:
            response = requests.get(f"{API_BASE_URL}/solat/{zone}")
            response.raise_for_status()
            data = response.json()
            if data and data.get("data"):
                return [PrayerTimes.model_validate(item) for item in data["data"]]
            raise ValueError("Failed to fetch prayer times data")
        except Exception as e:
            raise Exception(f"Failed to fetch prayer times: {str(e)}")

    async def get_zones(self) -> List[Zone]:
        """Helper function to fetch all available zones"""
        try:
            response = requests.get(f"{API_BASE_URL}/zones")
            response.raise_for_status()
            data = response.json()
            if data and data.get("data"):
                return [Zone.model_validate(item) for item in data["data"]]
            raise ValueError("Failed to fetch zones data")
        except Exception as e:
            raise Exception(f"Failed to fetch zones: {str(e)}")

    async def get_current_prayer(self, zone: str) -> Dict:
        """Helper function to get the current prayer time status for a zone"""
        try:
            response = requests.get(f"{API_BASE_URL}/current-time/{zone}")
            response.raise_for_status()
            data = response.json()
            if data:
                return data
            raise ValueError("Failed to fetch current prayer time data")
        except Exception as e:
            raise Exception(f"Failed to fetch current prayer time: {str(e)}")

    async def handle_get_prayer_times(self, args: Dict[str, Any]):
        zone = args.get("zone")
        if not zone:
            return {"error": "Zone is required"}
        try:
            prayer_times = await self.get_prayer_times(zone)
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps([pt.model_dump() for pt in prayer_times], indent=2)
                }]
            }
        except Exception as e:
            return {"error": str(e)}

    async def handle_list_zones(self, _: Dict[str, Any]):
        try:
            zones = await self.get_zones()
            formatted_zones = "\n".join(
                f"{zone.code}: {zone.name} ({zone.negeri})"
                for zone in zones
            )
            return {
                "content": [{
                    "type": "text",
                    "text": formatted_zones
                }]
            }
        except Exception as e:
            return {"error": str(e)}

    async def handle_get_current_prayer(self, args: Dict[str, Any]):
        zone = args.get("zone")
        if not zone:
            return {"error": "Zone is required"}
        try:
            current_prayer = await self.get_current_prayer(zone)
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(current_prayer, indent=2)
                }]
            }
        except Exception as e:
            return {"error": str(e)}

    def get_tools_list(self):
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
                                "description": "The zone code (e.g., 'SGR01', 'KUL01', etc.)"
                            }
                        },
                        "required": ["zone"]
                    }
                },
                {
                    "name": "list_zones",
                    "description": "List all available prayer time zones in Malaysia",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "get_current_prayer",
                    "description": "Get the current prayer time status for a specific zone",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "zone": {
                                "type": "string",
                                "description": "The zone code (e.g., 'SGR01', 'KUL01', etc.)"
                            }
                        },
                        "required": ["zone"]
                    }
                }
            ]
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        if method == "listTools":
            return self.get_tools_list()
        elif method == "callTool":
            tool_name = request.get("params", {}).get("name")
            tool_args = request.get("params", {}).get("arguments", {})
            if tool_name in self.tools:
                return await self.tools[tool_name](tool_args)
            return {"error": f"Unknown tool: {tool_name}"}
        return {"error": f"Unknown method: {method}"}

    async def run(self):
        """Start the server using stdio transport"""
        while True:
            try:
                request_line = await asyncio.get_event_loop().run_in_executor(None, input)
                if not request_line:
                    continue
                request = json.loads(request_line)
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
            except EOFError:
                break
            except Exception as e:
                print(json.dumps({"error": str(e)}), flush=True)

def main():
    server = WaktuSolatServer()
    try:
        asyncio.run(server.run())
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
