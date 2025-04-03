<div align="center">
  <img src="public/images/banner.svg" alt="Malaysia Prayer Time MCP Server" width="800">
</div>

# Malaysia Prayer Time MCP Server

A Model Context Protocol (MCP) server that provides prayer times for locations in Malaysia. This server integrates with Claude Desktop to provide real-time prayer time information using the pray.zone API.

## Features

- Get prayer times for any city in Malaysia
- Get prayer times using latitude and longitude coordinates
- Supports date-specific queries
- Real-time data from pray.zone API

## Prerequisites

- Python 3.10 or higher
- Claude Desktop (latest version)
- `uv` package manager (recommended)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/mcp-server-malaysia-prayer-time.git
cd mcp-server-malaysia-prayer-time
```

2. Create and activate a virtual environment using `uv`:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package in editable mode:
```bash
uv pip install -e .
```

## Configuration with Claude Desktop

1. Create or edit the Claude Desktop configuration file:
```bash
# On macOS
mkdir -p ~/Library/Application\ Support/Claude/
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. Add the following configuration (adjust paths according to your setup):
```json
{
    "mcpServers": {
        "malaysia-prayer-time": {
            "command": "/absolute/path/to/your/.venv/bin/python",
            "args": [
                "-m",
                "malaysia_prayer_time"
            ],
            "cwd": "/absolute/path/to/mcp-server-malaysia-prayer-time"
        }
    }
}
```

3. Restart Claude Desktop completely

## Usage

Once configured, you can use the following tools in Claude Desktop:

### get_prayer_times
Get prayer times for any city in Malaysia.

Example queries:
- "What are the prayer times for Kuala Lumpur today?"
- "Show me prayer times for Penang, Malaysia"
- "Get prayer schedule for Johor Bahru for tomorrow"

### get_prayer_times_by_coordinates
Get prayer times using latitude and longitude coordinates.

Example queries:
- "What are the prayer times at coordinates 3.1390, 101.6869?"
- "Show prayer schedule for location 5.4141, 100.3288"

## Prayer Times Information

The server provides the following prayer times:
- Imsak
- Fajr
- Sunrise
- Dhuhr
- Asr
- Sunset
- Maghrib
- Isha
- Midnight

## Troubleshooting

If you encounter any issues:

1. Check Claude Desktop logs:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

2. Verify the server runs manually:
```bash
python -m malaysia_prayer_time
```

3. Common issues:
   - Make sure all paths in `claude_desktop_config.json` are absolute
   - Ensure Python 3.10+ is used in the virtual environment
   - Verify Claude Desktop is updated to the latest version

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) - For the MCP framework
- [pray.zone API](https://pray.zone/) - For providing prayer time data
- Claude Desktop - For the MCP integration platform
