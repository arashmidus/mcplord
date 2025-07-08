#!/bin/bash

# Run MCP Servers for ChatGPT Integration
# This script starts the necessary MCP servers in HTTP/SSE mode

echo "🎭 Starting MCP Servers for ChatGPT..."
echo "Press Ctrl+C to stop all servers"
echo ""

# Set up environment
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Start the server manager
python start_mcp_servers_for_chatgpt.py 