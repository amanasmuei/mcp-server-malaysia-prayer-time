<div align="center">
  <img src="public/images/banner.svg" alt="Malaysia Prayer Time MCP Server" width="800">
</div>

# Malaysia Prayer Time MCP Server

An MCP (Model Context Protocol) server that provides access to Malaysia Prayer Time data using the API from [github.com/mptwaktusolat/api-waktusolat](https://github.com/mptwaktusolat/api-waktusolat).

## Features

- Get prayer times for specific zones in Malaysia
- List all available prayer time zones
- Get current prayer time status for a zone

## Installation

1. Create a virtual environment and install dependencies using uv:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

2. Make the server executable:
```bash
chmod +x bin/mcp-server-waktu-solat
```

## Usage

### Running in Claude Desktop

1. Add the following configuration to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "waktu-solat": {
      "command": "uvx",
      "args": ["run", "/absolute/path/to/bin/mcp-server-waktu-solat"],
      "env": {}
    }
  }
}
```
Replace `/absolute/path/to/` with the actual path where you cloned this repository.

2. Restart Claude Desktop to load the new MCP server.

### Available MCP Tools

The server implements the following tools:

### get_prayer_times
Get prayer times for a specific zone in Malaysia
- Input: `zone` (string) - The zone code (e.g., 'SGR01', 'KUL01')

### list_zones
List all available prayer time zones in Malaysia
- No input required

### get_current_prayer
Get the current prayer time status for a specific zone
- Input: `zone` (string) - The zone code (e.g., 'SGR01', 'KUL01')

## Development

1. Clone the repository
2. Install development dependencies:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

3. Run the server:
```bash
./bin/mcp-server-waktu-solat
```

## License

See [LICENSE](LICENSE) file.
