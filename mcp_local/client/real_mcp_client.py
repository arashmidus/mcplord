#!/usr/bin/env python3
"""
Real MCP Client

This client integrates with actual MCP servers using the official MCP SDK.
It supports connecting to servers via stdio, SSE, and WebSocket transports.
"""

import asyncio
import json
import logging
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Callable, Tuple
from pathlib import Path
import shlex

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import Resource, Tool, Prompt, GetResourceResult, CallToolResult
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Mock classes for graceful fallback
    class ClientSession:
        pass
    class StdioServerParameters:
        pass
    class Resource:
        pass
    class Tool:
        pass
    class Prompt:
        pass
    class GetResourceResult:
        pass
    class CallToolResult:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
logger = logging.getLogger(__name__)

class RealMCPClient:
    """
    Real MCP client that connects to actual MCP servers.
    
    Supports multiple server connections, tool discovery, and execution.
    """
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.server_processes: Dict[str, subprocess.Popen] = {}
        self.tools_cache: Dict[str, List[Tool]] = {}
        self.resources_cache: Dict[str, List[Resource]] = {}
        self.prompts_cache: Dict[str, List[Prompt]] = {}
        
    async def connect_to_server(
        self, 
        server_name: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        cwd: Optional[str] = None
    ) -> bool:
        """Connect to an MCP server via stdio transport."""
        if not MCP_AVAILABLE:
            console.print("[red]MCP SDK not available. Using mock implementation.[/red]")
            return await self._mock_connect(server_name, command, args)
        
        try:
            args = args or []
            env = env or {}
            
            console.print(f"🔌 Connecting to MCP server: {server_name}")
            console.print(f"   Command: {command} {' '.join(args)}")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env
            )
            
            # Connect to the server
            stdio_transport = await stdio_client(server_params)
            
            # Create session
            session = ClientSession(stdio_transport[0], stdio_transport[1])
            
            # Initialize the session
            await session.initialize()
            
            # Store the session
            self.sessions[server_name] = session
            
            # Cache available tools, resources, and prompts
            await self._refresh_server_capabilities(server_name)
            
            console.print(f"✅ Connected to {server_name}")
            return True
            
        except Exception as e:
            console.print(f"❌ Failed to connect to {server_name}: {e}")
            logger.exception(f"Failed to connect to server {server_name}")
            return False
    
    async def _refresh_server_capabilities(self, server_name: str):
        """Refresh cached capabilities for a server."""
        if server_name not in self.sessions:
            return
        
        session = self.sessions[server_name]
        
        try:
            # Get tools
            tools_result = await session.list_tools()
            self.tools_cache[server_name] = tools_result.tools if tools_result else []
            
            # Get resources
            resources_result = await session.list_resources()
            self.resources_cache[server_name] = resources_result.resources if resources_result else []
            
            # Get prompts
            prompts_result = await session.list_prompts()
            self.prompts_cache[server_name] = prompts_result.prompts if prompts_result else []
            
        except Exception as e:
            logger.warning(f"Failed to refresh capabilities for {server_name}: {e}")
    
    async def list_servers(self) -> List[str]:
        """List connected server names."""
        return list(self.sessions.keys())
    
    async def list_tools(self, server_name: Optional[str] = None) -> Dict[str, List[Tool]]:
        """List available tools from servers."""
        if server_name:
            if server_name in self.tools_cache:
                return {server_name: self.tools_cache[server_name]}
            return {server_name: []}
        
        return self.tools_cache.copy()
    
    async def list_resources(self, server_name: Optional[str] = None) -> Dict[str, List[Resource]]:
        """List available resources from servers."""
        if server_name:
            if server_name in self.resources_cache:
                return {server_name: self.resources_cache[server_name]}
            return {server_name: []}
        
        return self.resources_cache.copy()
    
    async def list_prompts(self, server_name: Optional[str] = None) -> Dict[str, List[Prompt]]:
        """List available prompts from servers."""
        if server_name:
            if server_name in self.prompts_cache:
                return {server_name: self.prompts_cache[server_name]}
            return {server_name: []}
        
        return self.prompts_cache.copy()
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any] = None
    ) -> CallToolResult:
        """Call a tool on a specific server."""
        if not MCP_AVAILABLE:
            return await self._mock_call_tool(server_name, tool_name, arguments)
        
        if server_name not in self.sessions:
            raise ValueError(f"Not connected to server: {server_name}")
        
        session = self.sessions[server_name]
        arguments = arguments or {}
        
        try:
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.exception(f"Failed to call tool {tool_name} on {server_name}")
            raise
    
    async def get_resource(
        self,
        server_name: str,
        resource_uri: str
    ) -> GetResourceResult:
        """Get a resource from a specific server."""
        if not MCP_AVAILABLE:
            return await self._mock_get_resource(server_name, resource_uri)
        
        if server_name not in self.sessions:
            raise ValueError(f"Not connected to server: {server_name}")
        
        session = self.sessions[server_name]
        
        try:
            result = await session.read_resource(resource_uri)
            return result
        except Exception as e:
            logger.exception(f"Failed to get resource {resource_uri} from {server_name}")
            raise
    
    async def get_prompt(
        self,
        server_name: str,
        prompt_name: str,
        arguments: Dict[str, Any] = None
    ):
        """Get a prompt from a specific server."""
        if not MCP_AVAILABLE:
            return await self._mock_get_prompt(server_name, prompt_name, arguments)
        
        if server_name not in self.sessions:
            raise ValueError(f"Not connected to server: {server_name}")
        
        session = self.sessions[server_name]
        arguments = arguments or {}
        
        try:
            result = await session.get_prompt(prompt_name, arguments)
            return result
        except Exception as e:
            logger.exception(f"Failed to get prompt {prompt_name} from {server_name}")
            raise
    
    async def disconnect_server(self, server_name: str):
        """Disconnect from a server."""
        if server_name in self.sessions:
            session = self.sessions[server_name]
            try:
                # Close the session
                await session.__aexit__(None, None, None)
            except:
                pass
            
            del self.sessions[server_name]
        
        # Clean up cached data
        self.tools_cache.pop(server_name, None)
        self.resources_cache.pop(server_name, None)
        self.prompts_cache.pop(server_name, None)
        
        # Clean up process if we have one
        if server_name in self.server_processes:
            process = self.server_processes[server_name]
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
            del self.server_processes[server_name]
        
        console.print(f"🔌 Disconnected from {server_name}")
    
    async def disconnect_all(self):
        """Disconnect from all servers."""
        server_names = list(self.sessions.keys())
        for server_name in server_names:
            await self.disconnect_server(server_name)
    
    def print_servers_status(self):
        """Print status of all connected servers."""
        if not self.sessions:
            console.print("[yellow]No servers connected[/yellow]")
            return
        
        table = Table(title="Connected MCP Servers")
        table.add_column("Server", style="cyan")
        table.add_column("Tools", style="green")
        table.add_column("Resources", style="blue")
        table.add_column("Prompts", style="magenta")
        
        for server_name in self.sessions:
            tools_count = len(self.tools_cache.get(server_name, []))
            resources_count = len(self.resources_cache.get(server_name, []))
            prompts_count = len(self.prompts_cache.get(server_name, []))
            
            table.add_row(
                server_name,
                str(tools_count),
                str(resources_count),
                str(prompts_count)
            )
        
        console.print(table)
    
    def print_tools(self, server_name: Optional[str] = None):
        """Print available tools."""
        tools_data = self.tools_cache
        
        if server_name:
            if server_name not in tools_data:
                console.print(f"[red]Server {server_name} not found[/red]")
                return
            tools_data = {server_name: tools_data[server_name]}
        
        for server, tools in tools_data.items():
            if not tools:
                continue
                
            table = Table(title=f"Tools from {server}")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="green")
            
            for tool in tools:
                table.add_row(
                    tool.name,
                    tool.description or "No description"
                )
            
            console.print(table)
    
    # Mock implementations for when MCP SDK is not available
    async def _mock_connect(self, server_name: str, command: str, args: List[str] = None) -> bool:
        """Mock connection for when MCP SDK is not available."""
        console.print(f"[yellow]Mock connection to {server_name}[/yellow]")
        
        # Add mock tools
        self.tools_cache[server_name] = [
            type('Tool', (), {
                'name': 'echo',
                'description': 'Echo back the input message'
            })(),
            type('Tool', (), {
                'name': 'add',
                'description': 'Add two numbers together'
            })()
        ]
        
        # Add mock resources
        self.resources_cache[server_name] = [
            type('Resource', (), {
                'uri': f'{server_name}://status',
                'name': 'Server Status',
                'description': 'Current server status'
            })()
        ]
        
        # Mock session
        self.sessions[server_name] = type('MockSession', (), {})()
        
        return True
    
    async def _mock_call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]):
        """Mock tool call."""
        if tool_name == "echo":
            message = arguments.get("message", "Hello from mock!")
            return type('CallToolResult', (), {
                'content': [type('Content', (), {'text': f"Echo: {message}"})()]
            })()
        elif tool_name == "add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            result = a + b
            return type('CallToolResult', (), {
                'content': [type('Content', (), {'text': f"Result: {result}"})()]
            })()
        else:
            return type('CallToolResult', (), {
                'content': [type('Content', (), {'text': f"Mock result for {tool_name}"})()]
            })()
    
    async def _mock_get_resource(self, server_name: str, resource_uri: str):
        """Mock resource retrieval."""
        return type('GetResourceResult', (), {
            'contents': [type('Content', (), {
                'uri': resource_uri,
                'text': f"Mock content for {resource_uri}"
            })()]
        })()
    
    async def _mock_get_prompt(self, server_name: str, prompt_name: str, arguments: Dict[str, Any]):
        """Mock prompt retrieval."""
        return type('GetPromptResult', (), {
            'description': f"Mock prompt: {prompt_name}",
            'messages': [type('Message', (), {
                'role': 'user',
                'content': type('Content', (), {
                    'text': f"Mock prompt content for {prompt_name}"
                })()
            })()]
        })()

# Convenience functions for common MCP servers
class MCPServerConfigs:
    """Pre-configured settings for popular MCP servers."""
    
    @staticmethod
    def filesystem(root_path: str) -> Tuple[str, List[str]]:
        """Filesystem server configuration."""
        return "npx", ["-y", "@modelcontextprotocol/server-filesystem", root_path]
    
    @staticmethod
    def memory() -> Tuple[str, List[str]]:
        """Memory server configuration."""
        return "npx", ["-y", "@modelcontextprotocol/server-memory"]
    
    @staticmethod
    def time() -> Tuple[str, List[str]]:
        """Time server configuration."""
        return "npx", ["-y", "@modelcontextprotocol/server-time"]
    
    @staticmethod
    def git(repository_path: str) -> Tuple[str, List[str]]:
        """Git server configuration."""
        return "uvx", ["mcp-server-git", "--repository", repository_path]
    
    @staticmethod
    def github(token: str) -> Tuple[str, List[str], Dict[str, str]]:
        """GitHub server configuration."""
        return (
            "npx", 
            ["-y", "@modelcontextprotocol/server-github"],
            {"GITHUB_PERSONAL_ACCESS_TOKEN": token}
        )
    
    @staticmethod
    def sqlite(db_path: str) -> Tuple[str, List[str]]:
        """SQLite server configuration."""
        return "npx", ["-y", "@modelcontextprotocol/server-sqlite", db_path]
    
    @staticmethod
    def postgres(connection_string: str) -> Tuple[str, List[str]]:
        """PostgreSQL server configuration."""
        return "npx", ["-y", "@modelcontextprotocol/server-postgres", connection_string]
    
    @staticmethod
    def brave_search(api_key: str) -> Tuple[str, List[str], Dict[str, str]]:
        """Brave Search server configuration."""
        return (
            "npx",
            ["-y", "@modelcontextprotocol/server-brave-search"],
            {"BRAVE_API_KEY": api_key}
        )
    
    @staticmethod
    def fetch() -> Tuple[str, List[str]]:
        """Fetch server configuration."""
        return "npx", ["-y", "@modelcontextprotocol/server-fetch"]
    
    @staticmethod
    def puppeteer() -> Tuple[str, List[str]]:
        """Puppeteer server configuration."""
        return "npx", ["-y", "@modelcontextprotocol/server-puppeteer"]
    
    @staticmethod
    def playwright() -> Tuple[str, List[str]]:
        """Microsoft Playwright MCP server configuration."""
        return "npx", ["-y", "@playwright/mcp"]

async def demo_real_mcp_servers():
    """Demonstrate connecting to and using real MCP servers."""
    client = RealMCPClient()
    
    try:
        console.print(Panel.fit(
            "[bold green]🔌 Real MCP Servers Demo[/bold green]\n"
            "Connecting to actual MCP servers and using their tools",
            border_style="green"
        ))
        
        # Connect to multiple servers
        servers_to_test = [
            ("memory", *MCPServerConfigs.memory()),
            ("time", *MCPServerConfigs.time()),
            ("fetch", *MCPServerConfigs.fetch()),
        ]
        
        connected_servers = []
        
        for server_name, command, args in servers_to_test:
            console.print(f"\n📡 Attempting to connect to {server_name}...")
            
            success = await client.connect_to_server(
                server_name=server_name,
                command=command,
                args=args
            )
            
            if success:
                connected_servers.append(server_name)
            
            # Small delay between connections
            await asyncio.sleep(1)
        
        if not connected_servers:
            console.print("[red]❌ Could not connect to any servers. Using mock mode.[/red]")
            # Add a mock server for demo
            await client._mock_connect("mock_server", "echo", ["hello"])
            connected_servers = ["mock_server"]
        
        # Show server status
        console.print("\n" + "="*60)
        client.print_servers_status()
        
        # Show available tools
        console.print("\n" + "="*60)
        console.print("[bold]📚 Available Tools:[/bold]")
        client.print_tools()
        
        # Demonstrate tool usage
        for server_name in connected_servers[:2]:  # Test first 2 servers
            console.print(f"\n🔧 Testing tools from {server_name}:")
            
            tools = await client.list_tools(server_name)
            server_tools = tools.get(server_name, [])
            
            for tool in server_tools[:2]:  # Test first 2 tools
                try:
                    console.print(f"  🛠️  Calling {tool.name}...")
                    
                    # Prepare sample arguments based on tool name
                    args = {}
                    if hasattr(tool, 'name'):
                        if "echo" in tool.name.lower():
                            args = {"message": "Hello from MCP agent!"}
                        elif "add" in tool.name.lower():
                            args = {"a": 15, "b": 27}
                        elif "time" in tool.name.lower():
                            args = {"timezone": "UTC"}
                        elif "remember" in tool.name.lower():
                            args = {"content": "This is a test memory"}
                    
                    result = await client.call_tool(server_name, tool.name, args)
                    
                    if hasattr(result, 'content') and result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                console.print(f"     ✅ {content.text}")
                            else:
                                console.print(f"     ✅ {content}")
                    else:
                        console.print(f"     ✅ Tool executed successfully")
                        
                except Exception as e:
                    console.print(f"     ❌ Error: {e}")
        
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 Real MCP Demo Complete![/bold green]")
        
        return client
        
    except Exception as e:
        console.print(f"[red]Demo failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return client

if __name__ == "__main__":
    asyncio.run(demo_real_mcp_servers()) 