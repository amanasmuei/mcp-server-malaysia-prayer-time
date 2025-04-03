<div align="center">
  <img src="public/images/banner.svg" alt="Malaysia Prayer Time MCP Server" width="800">
</div>

# Malaysia Prayer Time MCP Server

An MCP (Model Context Protocol) server that provides access to Malaysia Prayer Time data using the API from [github.com/mptwaktusolat/api-waktusolat](https://github.com/mptwaktusolat/api-waktusolat).

## Features

- Get prayer times for specific zones in Malaysia
- List all available prayer time zones
- Get current prayer time status for a zone

## Prerequisites

1. Install Python 3.8 or higher
2. Install UVX CLI tool:
   ```bash
   pip install uvx-cli
   ```
3. Verify UVX installation:
   ```bash
   uvx --version
   ```
   If you get a "command not found" error, make sure your Python scripts directory is in your PATH:
   ```bash
   # For macOS/Linux, add to ~/.zshrc or ~/.bashrc:
   export PATH="$PATH:$(python3 -m site --user-base)/bin"
   
   # Then reload your shell:
   source ~/.zshrc  # or source ~/.bashrc
   ```

## Installation

### Option 1: Install as UVX Plugin (Recommended for Claude Desktop)

1. Install the plugin directly from the repository:
```bash
pip install git+https://github.com/amanasmuei/mcp-server-malaysia-prayer-time.git
```

2. Configure Claude Desktop to use the plugin:
   - Create or edit the Claude Desktop configuration file:
   ```bash
   mkdir -p ~/Library/Application\ Support/Claude
   touch ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
   
   - Add the following configuration to `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "waktu-solat": {
         "command": "uvx",
         "args": ["run", "malaysia-prayer-time"],
         "env": {}
       }
     }
   }
   ```

3. Restart Claude Desktop to load the plugin.

Note: While the plugin is automatically registered with UVX after installation, Claude Desktop currently requires manual configuration to use UVX plugins.

If you don't see the process running:
1. Check Claude Desktop logs for any errors
2. Verify that the configuration in `~/Library/Application Support/Claude/claude_desktop_config.json` is correct and properly formatted
3. Try restarting Claude Desktop
4. Ensure the plugin is properly installed by running the verification commands above
5. If you see "spawn uvx ENOENT" error:
   - Make sure UVX is installed: `pip install uvx-cli`
   - Verify UVX is in your PATH: `which uvx`
   - If not found, add Python scripts to PATH as described in Prerequisites
   - Restart your terminal and Claude Desktop

### Option 2: Install as MCP Server

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

### Verifying Installation

To check if the plugin is properly installed:

1. Check if the plugin is installed in your Python environment:
   ```bash
   pip list | grep malaysia-prayer-time
   ```

2. Check if the UVX plugin is registered:
   ```bash
   uvx list-plugins
   ```

3. Check if the server process is running:
   ```bash
   # For UVX Plugin
   ps aux | grep waktu_solat.mcp_server
   ```
   You should see a process running with `python -m waktu_solat.mcp_server`

4. For MCP Server:
   ```bash
   ps aux | grep mcp-server-waktu-solat
   ```
   You should see a process running with the server script path

If you don't see the process running:
1. Check Claude Desktop logs for any errors
2. Verify that the configuration in `~/Library/Application Support/Claude/claude_desktop_config.json` is correct and properly formatted
3. Try restarting Claude Desktop
4. Ensure the plugin is properly installed by running the verification commands above

### Stopping the Server

To stop the server process:

1. Find the process ID (PID):
   ```bash
   # For UVX Plugin
   ps aux | grep waktu_solat.mcp_server | grep -v grep | awk '{print $2}'
   
   # For MCP Server
   ps aux | grep mcp-server-waktu-solat | grep -v grep | awk '{print $2}'
   ```

2. Stop the process:
   ```bash
   # Replace <PID> with the process ID from step 1
   kill <PID>
   ```

Alternatively, you can use a single command:
```bash
# For UVX Plugin
pkill -f waktu_solat.mcp_server

# For MCP Server
pkill -f mcp-server-waktu-solat
```

Note: The server will automatically restart when you open Claude Desktop again unless you remove the configuration from `claude_desktop_config.json`.

## Usage

### Running with Claude Desktop as UVX Plugin

After installing the plugin and configuring Claude Desktop as described in the installation section, you can access the tools directly through Claude.

Example prompts:
- "What are the prayer times for KUL01 zone in Malaysia?"
- "List all available prayer time zones in Malaysia"
- "What is the current prayer time for SGR01 zone?"

### Running in Claude Desktop as MCP Server

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

### Available Tools

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

4. To test the UVX plugin during development:
```bash
# The plugin is located in src/uvx_plugin.py
uvx run src/uvx_plugin.py
```

Note: The UVX plugin implementation is in `src/uvx_plugin.py`. This is the main implementation with full API integration, caching, and proper error handling.

## License

See [LICENSE](LICENSE) file.
