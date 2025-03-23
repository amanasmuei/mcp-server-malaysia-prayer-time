#!/usr/bin/env node

/**
 * Malaysia Prayer Time MCP Server
 * This server implements access to Malaysia Prayer Time data
 * using the API from github.com/mptwaktusolat/api-waktusolat.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

/**
 * Types for the prayer time data
 */
type PrayerTimes = {
  date: string;
  day: string;
  imsak: string;
  fajr: string;
  syuruk: string;
  dhuhr: string;
  asr: string;
  maghrib: string;
  isha: string;
};

type Zone = {
  name: string;
  code: string;
  negeri: string;
};

/**
 * API endpoint base URL
 */
const API_BASE_URL = "https://api.waktusolat.app/api/v2";

/**
 * Create an MCP server with capabilities for resources and tools
 */
const server = new Server(
  {
    name: "Malaysia Prayer Time MCP Server",
    version: "0.1.0",
  },
  {
    capabilities: {
      resources: {},
      tools: {},
      prompts: {},
    },
  }
);

/**
 * Helper function to fetch prayer times for a specific zone
 */
async function getPrayerTimes(zone: string): Promise<PrayerTimes[]> {
  try {
    const response = await axios.get(`${API_BASE_URL}/solat/${zone}`);
    if (response.data && response.data.data) {
      return response.data.data;
    }
    throw new Error("Failed to fetch prayer times data");
  } catch (error) {
    console.error("Error fetching prayer times:", error);
    throw new Error(`Failed to fetch prayer times: ${error}`);
  }
}

/**
 * Helper function to fetch all available zones
 */
async function getZones(): Promise<Zone[]> {
  try {
    const response = await axios.get(`${API_BASE_URL}/zones`);
    if (response.data && response.data.data) {
      return response.data.data;
    }
    throw new Error("Failed to fetch zones data");
  } catch (error) {
    console.error("Error fetching zones:", error);
    throw new Error(`Failed to fetch zones: ${error}`);
  }
}

/**
 * Helper function to get the current prayer time status for a zone
 */
async function getCurrentPrayerTime(zone: string): Promise<any> {
  try {
    const response = await axios.get(`${API_BASE_URL}/current-time/${zone}`);
    if (response.data) {
      return response.data;
    }
    throw new Error("Failed to fetch current prayer time data");
  } catch (error) {
    console.error("Error fetching current prayer time:", error);
    throw new Error(`Failed to fetch current prayer time: ${error}`);
  }
}

/**
 * Handler for listing available resources
 * We don't expose any resources in this implementation
 */
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: []
  };
});

/**
 * Handler for reading a resource
 * Not used in this implementation
 */
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  throw new Error(`Resource ${request.params.uri} not found`);
});

/**
 * Handler that lists available tools
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_prayer_times",
        description: "Get prayer times for a specific zone in Malaysia",
        inputSchema: {
          type: "object",
          properties: {
            zone: {
              type: "string",
              description: "The zone code (e.g., 'SGR01', 'KUL01', etc.)"
            }
          },
          required: ["zone"]
        }
      },
      {
        name: "list_zones",
        description: "List all available prayer time zones in Malaysia",
        inputSchema: {
          type: "object",
          properties: {}
        }
      },
      {
        name: "get_current_prayer",
        description: "Get the current prayer time status for a specific zone",
        inputSchema: {
          type: "object",
          properties: {
            zone: {
              type: "string",
              description: "The zone code (e.g., 'SGR01', 'KUL01', etc.)"
            }
          },
          required: ["zone"]
        }
      }
    ]
  };
});

/**
 * Handler for tool calls
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  switch (request.params.name) {
    case "get_prayer_times": {
      const zone = String(request.params.arguments?.zone);
      if (!zone) {
        throw new Error("Zone is required");
      }

      const prayerTimes = await getPrayerTimes(zone);
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(prayerTimes, null, 2)
        }]
      };
    }

    case "list_zones": {
      const zones = await getZones();
      
      // Format the zones in a more readable way
      const formattedZones = zones.map(zone => 
        `${zone.code}: ${zone.name} (${zone.negeri})`
      ).join('\n');
      
      return {
        content: [{
          type: "text",
          text: formattedZones
        }]
      };
    }

    case "get_current_prayer": {
      const zone = String(request.params.arguments?.zone);
      if (!zone) {
        throw new Error("Zone is required");
      }

      const currentPrayer = await getCurrentPrayerTime(zone);
      
      return {
        content: [{
          type: "text",
          text: JSON.stringify(currentPrayer, null, 2)
        }]
      };
    }

    default:
      throw new Error("Unknown tool");
  }
});

/**
 * Handler that lists available prompts
 * We don't expose any prompts in this implementation
 */
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: []
  };
});

/**
 * Handler for getting a prompt
 * Not used in this implementation
 */
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  throw new Error(`Prompt ${request.params.name} not found`);
});

/**
 * Start the server using stdio transport
 */
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
