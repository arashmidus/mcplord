#!/usr/bin/env python3
"""
Minimal MCP server to test basic functionality
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Load environment variables
def load_env_file():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        import os
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env_file()

# Import MCP components
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolResult, TextContent, Tool
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Error: MCP SDK not available: {e}", file=sys.stderr)
    MCP_AVAILABLE = False
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Create the server
server = Server("test-minimal")

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls."""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        if name == "test_tool":
            message = arguments.get("message", "Hello from minimal server!")
            result = {
                "response": f"Received: {message}",
                "status": "success"
            }
            result_text = json.dumps(result, indent=2)
            
            # Create TextContent properly
            text_content = TextContent(type="text", text=result_text)
            logger.info(f"Created TextContent: {type(text_content)}")
            
            # Create CallToolResult properly
            call_result = CallToolResult(content=[text_content])
            logger.info(f"Created CallToolResult: {type(call_result)}")
            
            return call_result
            
        else:
            error_result = json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            return CallToolResult(content=[TextContent(type="text", text=error_result)])
        
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        import traceback
        traceback.print_exc()
        error_result = json.dumps({"error": str(e), "status": "failed"}, indent=2)
        return CallToolResult(content=[TextContent(type="text", text=error_result)])

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    try:
        tools = [
            Tool(
                name="test_tool",
                description="Simple test tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Test message"}
                    },
                    "required": []
                }
            )
        ]
        logger.info(f"Listed {len(tools)} tools")
        return tools
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        import traceback
        traceback.print_exc()
        return []

async def main():
    """Main server function."""
    try:
        logger.info("Starting minimal MCP server...")
        
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server streams established")
            await server.run(read_stream, write_stream, server.create_initialization_options())
            
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Minimal MCP Server...", file=sys.stderr)
    print("📄 Available tools: test_tool", file=sys.stderr)
    
    asyncio.run(main()) 