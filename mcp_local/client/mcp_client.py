"""
MCP Client implementation for agent communication with MCP servers.

This module provides a comprehensive MCP client that enables agents to:
- Connect to multiple MCP servers
- Fetch context and shared state
- Call tools across servers
- Handle connection management and error recovery
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import httpx
import websockets
from pydantic import BaseModel

# Try to import MCP if available, otherwise use mocks
try:
    from mcp import StdioServerParameters, create_stdio_client
    from mcp.client.session import ClientSession
    MCP_AVAILABLE = True
except ImportError:
    # Mock classes for when MCP is not available
    class StdioServerParameters:
        def __init__(self, command, args=None):
            self.command = command
            self.args = args or []
    
    class ClientSession:
        async def list_tools(self):
            return None
        
        async def list_resources(self):
            return None
        
        async def read_resource(self, uri):
            return None
        
        async def call_tool(self, name, params):
            return None
    
    async def create_stdio_client(params):
        class MockClient:
            async def __aenter__(self):
                return ClientSession()
            
            async def __aexit__(self, *args):
                pass
        
        return MockClient()
    
    MCP_AVAILABLE = False

from monitoring.metrics.mcp_metrics import MCPMetrics


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server connection."""
    
    url: str
    transport_type: str = "http"  # http, websocket, stdio
    auth_token: Optional[str] = None
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    

class MCPClient:
    """
    MCP Client for agent communication with multiple MCP servers.
    
    Handles connection management, request routing, error recovery,
    and provides a unified interface for agent-MCP interactions.
    """
    
    def __init__(self, server_configs: Union[List[str], List[MCPServerConfig]]):
        self.servers = {}
        self.sessions = {}
        self.metrics = MCPMetrics()
        self.logger = logging.getLogger("mcp.client")
        
        # Convert string URLs to server configs if needed
        self.server_configs = []
        for config in server_configs:
            if isinstance(config, str):
                self.server_configs.append(MCPServerConfig(url=config))
            else:
                self.server_configs.append(config)
    
    async def connect(self) -> None:
        """Establish connections to all configured MCP servers."""
        self.logger.info(f"Connecting to {len(self.server_configs)} MCP servers")
        
        connection_tasks = []
        for config in self.server_configs:
            task = asyncio.create_task(self._connect_to_server(config))
            connection_tasks.append(task)
        
        # Wait for all connections to complete
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        # Log connection results
        successful_connections = 0
        for i, result in enumerate(results):
            config = self.server_configs[i]
            if isinstance(result, Exception):
                self.logger.error(f"Failed to connect to {config.url}: {result}")
            else:
                successful_connections += 1
                self.logger.info(f"Successfully connected to {config.url}")
        
        if successful_connections == 0:
            raise RuntimeError("Failed to connect to any MCP servers")
        
        self.logger.info(f"Connected to {successful_connections}/{len(self.server_configs)} servers")
    
    async def disconnect(self) -> None:
        """Disconnect from all MCP servers."""
        self.logger.info("Disconnecting from MCP servers")
        
        disconnect_tasks = []
        for server_id, session in self.sessions.items():
            try:
                if hasattr(session, 'close'):
                    task = asyncio.create_task(session.close())
                    disconnect_tasks.append(task)
            except Exception as e:
                self.logger.warning(f"Error disconnecting from {server_id}: {e}")
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        self.sessions.clear()
        self.servers.clear()
    
    async def _connect_to_server(self, config: MCPServerConfig) -> None:
        """Connect to a single MCP server."""
        server_id = self._get_server_id(config.url)
        
        try:
            if config.transport_type == "stdio":
                session = await self._connect_stdio(config)
            elif config.transport_type == "websocket":
                session = await self._connect_websocket(config)
            else:  # Default to HTTP
                session = await self._connect_http(config)
            
            self.sessions[server_id] = session
            self.servers[server_id] = config
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {config.url}: {e}")
            raise
    
    async def _connect_http(self, config: MCPServerConfig) -> httpx.AsyncClient:
        """Connect to an HTTP MCP server."""
        headers = {}
        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
        
        client = httpx.AsyncClient(
            base_url=config.url,
            headers=headers,
            timeout=config.timeout
        )
        
        # Test connection with a ping
        try:
            response = await client.get("/health")
            if response.status_code != 200:
                raise RuntimeError(f"Server health check failed: {response.status_code}")
        except Exception as e:
            await client.aclose()
            raise RuntimeError(f"HTTP connection test failed: {e}")
        
        return client
    
    async def _connect_websocket(self, config: MCPServerConfig) -> Any:
        """Connect to a WebSocket MCP server."""
        # Convert HTTP URL to WebSocket URL
        ws_url = config.url.replace("http://", "ws://").replace("https://", "wss://")
        
        extra_headers = {}
        if config.auth_token:
            extra_headers["Authorization"] = f"Bearer {config.auth_token}"
        
        websocket = await websockets.connect(
            ws_url,
            extra_headers=extra_headers,
            ping_interval=20,
            ping_timeout=10
        )
        
        return websocket
    
    async def _connect_stdio(self, config: MCPServerConfig) -> ClientSession:
        """Connect to a stdio MCP server."""
        # Parse stdio command from URL
        # Format: stdio://command?args=arg1,arg2,arg3
        parsed = urlparse(config.url)
        command = parsed.netloc
        args = []
        
        if parsed.query:
            query_params = dict(x.split('=') for x in parsed.query.split('&'))
            if 'args' in query_params:
                args = query_params['args'].split(',')
        
        server_params = StdioServerParameters(
            command=command,
            args=args
        )
        
        stdio_client = await create_stdio_client(server_params)
        session = await stdio_client.__aenter__()
        
        return session
    
    def _get_server_id(self, url: str) -> str:
        """Generate a server ID from URL."""
        parsed = urlparse(url)
        return f"{parsed.netloc}{parsed.path}".replace("/", "_").replace(":", "_")
    
    async def fetch_context(self, context_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch context from MCP servers.
        
        Args:
            context_request: Request containing agent info and context requirements
            
        Returns:
            Aggregated context data from all servers
        """
        start_time = time.time()
        
        try:
            # Fetch context from all available servers
            context_tasks = []
            for server_id, session in self.sessions.items():
                task = asyncio.create_task(
                    self._fetch_context_from_server(server_id, session, context_request)
                )
                context_tasks.append(task)
            
            # Gather results from all servers
            results = await asyncio.gather(*context_tasks, return_exceptions=True)
            
            # Aggregate successful results
            aggregated_context = {
                "shared_state": {},
                "tools": [],
                "history": [],
                "coordination": {},
                "environment": {},
                "constraints": {}
            }
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    server_id = list(self.sessions.keys())[i]
                    self.logger.warning(f"Failed to fetch context from {server_id}: {result}")
                    continue
                
                # Merge context data
                if isinstance(result, dict):
                    for key in aggregated_context:
                        if key in result:
                            if isinstance(aggregated_context[key], dict):
                                aggregated_context[key].update(result[key])
                            elif isinstance(aggregated_context[key], list):
                                aggregated_context[key].extend(result[key])
            
            # Record metrics
            fetch_time = time.time() - start_time
            self.metrics.record_context_fetch(fetch_time, len(results))
            
            return aggregated_context
            
        except Exception as e:
            self.logger.error(f"Context fetch failed: {e}")
            raise
    
    async def _fetch_context_from_server(
        self,
        server_id: str,
        session: Any,
        context_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch context from a single MCP server."""
        config = self.servers[server_id]
        
        try:
            if isinstance(session, httpx.AsyncClient):
                return await self._fetch_context_http(session, context_request)
            elif isinstance(session, ClientSession):
                return await self._fetch_context_stdio(session, context_request)
            else:
                return await self._fetch_context_websocket(session, context_request)
                
        except Exception as e:
            self.logger.warning(f"Failed to fetch context from {server_id}: {e}")
            # Return empty context instead of failing
            return {}
    
    async def _fetch_context_http(
        self,
        client: httpx.AsyncClient,
        context_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch context via HTTP."""
        response = await client.post("/context", json=context_request)
        response.raise_for_status()
        return response.json()
    
    async def _fetch_context_stdio(
        self,
        session: ClientSession,
        context_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch context via stdio."""
        # Use MCP protocol to request resources and tools
        context_data = {
            "shared_state": {},
            "tools": [],
            "history": [],
            "coordination": {},
            "environment": {},
            "constraints": {}
        }
        
        try:
            # List available tools
            tools_result = await session.list_tools()
            context_data["tools"] = tools_result.tools if hasattr(tools_result, 'tools') else []
            
            # List available resources
            resources_result = await session.list_resources()
            if hasattr(resources_result, 'resources'):
                for resource in resources_result.resources:
                    if resource.name == "shared_state":
                        state_result = await session.read_resource(resource.uri)
                        if hasattr(state_result, 'contents'):
                            context_data["shared_state"] = json.loads(state_result.contents[0].text)
                    elif resource.name == "coordination":
                        coord_result = await session.read_resource(resource.uri)
                        if hasattr(coord_result, 'contents'):
                            context_data["coordination"] = json.loads(coord_result.contents[0].text)
            
        except Exception as e:
            self.logger.warning(f"Error fetching stdio context: {e}")
        
        return context_data
    
    async def _fetch_context_websocket(
        self,
        websocket: Any,
        context_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch context via WebSocket."""
        # Send context request
        message = {
            "type": "context_request",
            "data": context_request
        }
        await websocket.send(json.dumps(message))
        
        # Receive response
        response = await websocket.recv()
        return json.loads(response)
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call a tool on any available MCP server.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        start_time = time.time()
        
        # Find servers that have this tool
        available_servers = []
        for server_id, session in self.sessions.items():
            if await self._server_has_tool(server_id, session, tool_name):
                available_servers.append((server_id, session))
        
        if not available_servers:
            raise ValueError(f"Tool '{tool_name}' not found on any connected servers")
        
        # Use the first available server (could implement load balancing here)
        server_id, session = available_servers[0]
        
        try:
            result = await self._call_tool_on_server(session, tool_name, **kwargs)
            
            # Record metrics
            execution_time = time.time() - start_time
            self.metrics.record_tool_call(tool_name, server_id, execution_time, True)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.metrics.record_tool_call(tool_name, server_id, execution_time, False)
            self.logger.error(f"Tool call failed: {tool_name} on {server_id}: {e}")
            raise
    
    async def _server_has_tool(self, server_id: str, session: Any, tool_name: str) -> bool:
        """Check if a server has a specific tool."""
        try:
            if isinstance(session, ClientSession):
                tools_result = await session.list_tools()
                if hasattr(tools_result, 'tools'):
                    return any(tool.name == tool_name for tool in tools_result.tools)
            # For HTTP and WebSocket, we'd need to implement tool discovery
            return True  # Assume available for now
        except Exception:
            return False
    
    async def _call_tool_on_server(self, session: Any, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool on a specific server."""
        if isinstance(session, ClientSession):
            result = await session.call_tool(tool_name, kwargs)
            return {
                "success": True,
                "result": result.content[0].text if hasattr(result, 'content') else str(result),
                "cost": 0.0  # Would need to implement cost tracking
            }
        elif isinstance(session, httpx.AsyncClient):
            response = await session.post(f"/tools/{tool_name}", json=kwargs)
            response.raise_for_status()
            return response.json()
        else:
            # WebSocket implementation
            message = {
                "type": "tool_call",
                "tool": tool_name,
                "params": kwargs
            }
            await session.send(json.dumps(message))
            response = await session.recv()
            return json.loads(response)
    
    async def update_state(self, agent_id: str, key: str, value: Any) -> None:
        """Update shared state via MCP servers."""
        update_data = {
            "agent_id": agent_id,
            "key": key,
            "value": value,
            "timestamp": time.time()
        }
        
        # Update state on all servers (eventual consistency)
        update_tasks = []
        for server_id, session in self.sessions.items():
            task = asyncio.create_task(
                self._update_state_on_server(session, update_data)
            )
            update_tasks.append(task)
        
        await asyncio.gather(*update_tasks, return_exceptions=True)
    
    async def _update_state_on_server(self, session: Any, update_data: Dict[str, Any]) -> None:
        """Update state on a single server."""
        try:
            if isinstance(session, httpx.AsyncClient):
                await session.post("/state", json=update_data)
            elif isinstance(session, ClientSession):
                # For stdio, we'd need to implement state management
                pass
            else:
                # WebSocket
                message = {
                    "type": "state_update",
                    "data": update_data
                }
                await session.send(json.dumps(message))
        except Exception as e:
            self.logger.warning(f"Failed to update state: {e}")
    
    async def get_state(self, key: str) -> Any:
        """Get shared state from MCP servers."""
        # Try to get state from any available server
        for server_id, session in self.sessions.items():
            try:
                if isinstance(session, httpx.AsyncClient):
                    response = await session.get(f"/state/{key}")
                    if response.status_code == 200:
                        return response.json().get("value")
                elif isinstance(session, ClientSession):
                    # Implement stdio state retrieval
                    pass
                else:
                    # WebSocket
                    message = {
                        "type": "state_get",
                        "key": key
                    }
                    await session.send(json.dumps(message))
                    response = await session.recv()
                    data = json.loads(response)
                    if data.get("success"):
                        return data.get("value")
            except Exception:
                continue
        
        return None
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected server IDs."""
        return list(self.sessions.keys())
    
    def is_connected(self) -> bool:
        """Check if any servers are connected."""
        return len(self.sessions) > 0 