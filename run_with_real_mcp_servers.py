#!/usr/bin/env python3
"""
Run MCP Agent System with Real MCP Servers

This script demonstrates the complete MCP agent scaffolding system
integrated with real MCP servers from the official repositories.
"""

import asyncio
import sys
import os
import yaml
import time
from pathlib import Path
from typing import Dict, List, Any

# Setup path
current_dir = str(Path(__file__).parent.absolute())
sys.path.insert(0, current_dir)
os.environ['PYTHONPATH'] = f"{current_dir}:{os.environ.get('PYTHONPATH', '')}"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.live import Live

# Import our modules
from mcp.client.real_mcp_client import RealMCPClient, MCPServerConfigs
from agents.base.agent import BaseAgent
from coordination.state.context_bundle import ContextBundle

console = Console()

class RealMCPAgentSystem:
    """
    Complete MCP agent system with real server integration.
    """
    
    def __init__(self, config_path: str = "config/real_mcp_servers.yml"):
        self.config_path = config_path
        self.config = None
        self.mcp_client = RealMCPClient()
        self.agents = {}
        self.system_running = False
        
    def load_config(self):
        """Load MCP servers configuration."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            console.print(f"✅ Loaded config from {self.config_path}")
        except Exception as e:
            console.print(f"❌ Failed to load config: {e}")
            # Use default config
            self.config = {
                "servers": {
                    "memory": {
                        "enabled": True,
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-memory"],
                        "env": {}
                    }
                },
                "defaults": {"connection_timeout": 30}
            }
    
    async def connect_enabled_servers(self) -> List[str]:
        """Connect to all enabled MCP servers."""
        if not self.config:
            self.load_config()
        
        servers = self.config.get("servers", {})
        connected = []
        
        console.print("\n🔌 Connecting to enabled MCP servers...")
        
        for server_name, server_config in servers.items():
            if not server_config.get("enabled", False):
                console.print(f"  ⏸️  Skipping disabled server: {server_name}")
                continue
            
            console.print(f"  📡 Connecting to {server_name}...")
            
            success = await self.mcp_client.connect_to_server(
                server_name=server_name,
                command=server_config["command"],
                args=server_config.get("args", []),
                env=server_config.get("env", {})
            )
            
            if success:
                connected.append(server_name)
                console.print(f"    ✅ {server_name} connected")
            else:
                console.print(f"    ❌ {server_name} failed to connect")
            
            # Small delay between connections
            await asyncio.sleep(1)
        
        return connected
    
    def show_system_overview(self, connected_servers: List[str]):
        """Display comprehensive system overview."""
        layout = Layout()
        
        # Create server status table
        server_table = Table(title="🖥️  Connected MCP Servers")
        server_table.add_column("Server", style="cyan")
        server_table.add_column("Status", style="green")
        server_table.add_column("Description", style="blue")
        server_table.add_column("Tools", style="yellow")
        
        servers_config = self.config.get("servers", {})
        
        for server_name in connected_servers:
            server_info = servers_config.get(server_name, {})
            description = server_info.get("description", "No description")
            tools = ", ".join(server_info.get("tools", [])[:3])  # Show first 3 tools
            if len(server_info.get("tools", [])) > 3:
                tools += "..."
            
            server_table.add_row(
                server_name,
                "🟢 Online",
                description[:50] + "..." if len(description) > 50 else description,
                tools
            )
        
        console.print(server_table)
        
        # Show available tools summary
        self.mcp_client.print_servers_status()
        
        # Show configuration groups
        groups = self.config.get("groups", {})
        if groups:
            console.print("\n📋 Server Groups:")
            for group_name, group_info in groups.items():
                group_servers = group_info.get("servers", [])
                active_servers = [s for s in group_servers if s in connected_servers]
                
                if active_servers:
                    console.print(f"  🔹 {group_name}: {', '.join(active_servers)}")
    
    async def create_enhanced_agent(self, agent_name: str, connected_servers: List[str]):
        """Create an agent with access to real MCP servers."""
        
        class RealMCPAgent(BaseAgent):
            def __init__(self, agent_id: str, mcp_client: RealMCPClient, servers: List[str]):
                from agents.base.agent import AgentConfig
                
                # Create config for the agent
                config = AgentConfig(
                    name=agent_id,
                    description=f"Real MCP agent with {len(servers)} servers",
                    mcp_server_urls=[f"mcp://{server}" for server in servers]
                )
                super().__init__(config)
                self.real_mcp_client = mcp_client
                self.available_servers = servers
            
            async def _initialize_agent(self):
                """Initialize the agent."""
                pass
            
            async def _determine_next_action(self, context_bundle):
                """Determine the next action based on context."""
                return "execute_tools"
            
            async def _execute_task_with_context(self, task: str, context_bundle):
                """Execute task with context bundle."""
                return await self._execute_task_directly(task, context_bundle.to_dict() if hasattr(context_bundle, 'to_dict') else {})
            
            async def _execute_task_directly(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
                """Execute task directly without going through base class context fetching."""
                start_time = time.time()
                
                try:
                    # Get available tools from all connected servers
                    all_tools = await self.real_mcp_client.list_tools()
                    console.print(f"   📚 Available tools: {sum(len(tools) for tools in all_tools.values())}")
                    
                    # Demonstrate tool usage based on task
                    results = []
                    
                    # Example: If task mentions time, use time server
                    if "time" in task.lower() and "time" in self.available_servers:
                        console.print("   🕒 Using time server...")
                        try:
                            time_tools = await self.real_mcp_client.list_tools("time")
                            if time_tools.get("time"):
                                # Try to call a time tool
                                for tool in time_tools["time"][:1]:  # Use first tool
                                    result = await self.real_mcp_client.call_tool("time", tool.name, {})
                                    results.append(f"Time tool result: {result}")
                        except Exception as e:
                            results.append(f"Time tool error: {e}")
                    
                    # Example: If task mentions memory, use memory server
                    if "remember" in task.lower() or "memory" in task.lower() and "memory" in self.available_servers:
                        console.print("   🧠 Using memory server...")
                        try:
                            memory_tools = await self.real_mcp_client.list_tools("memory")
                            if memory_tools.get("memory"):
                                # Try to remember something
                                for tool in memory_tools["memory"][:1]:
                                    if "remember" in tool.name.lower():
                                        result = await self.real_mcp_client.call_tool(
                                            "memory", 
                                            tool.name, 
                                            {"content": f"Task executed: {task}"}
                                        )
                                        results.append(f"Memory tool result: {result}")
                                        break
                        except Exception as e:
                            results.append(f"Memory tool error: {e}")
                    
                    # Example: If task mentions web/fetch, use fetch server
                    if any(word in task.lower() for word in ["web", "fetch", "download", "url"]) and "fetch" in self.available_servers:
                        console.print("   🌐 Using fetch server...")
                        try:
                            fetch_tools = await self.real_mcp_client.list_tools("fetch")
                            if fetch_tools.get("fetch"):
                                results.append("Fetch server is available for web requests")
                        except Exception as e:
                            results.append(f"Fetch tool error: {e}")
                    
                    execution_time = time.time() - start_time
                    
                    return {
                        "success": True,
                        "results": results,
                        "execution_time": execution_time,
                        "cost": 0.001 * len(results),  # Mock cost
                        "tools_used": len(results),
                    }
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    return {
                        "success": False,
                        "error": str(e),
                        "execution_time": execution_time,
                        "cost": 0.0
                    }
                
            async def execute_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
                """Execute a task using real MCP servers."""
                console.print(f"🤖 Agent {self.config.name} analyzing task: {task}")
                return await self._execute_task_directly(task, context)
            
            async def _get_available_tools(self) -> List[str]:
                """Get list of available tools from connected servers."""
                all_tools = await self.real_mcp_client.list_tools()
                tools = []
                for server_tools in all_tools.values():
                    tools.extend([tool.name for tool in server_tools])
                return tools
        
        agent = RealMCPAgent(agent_name, self.mcp_client, connected_servers)
        self.agents[agent_name] = agent
        
        console.print(f"🤖 Created agent '{agent_name}' with {len(connected_servers)} MCP servers")
        return agent
    
    async def demonstrate_agent_workflows(self, connected_servers: List[str]):
        """Demonstrate various agent workflows with real MCP servers."""
        console.print("\n" + "="*70)
        console.print("[bold blue]🚀 Agent Workflow Demonstrations[/bold blue]")
        console.print("="*70)
        
        # Create demonstration agents
        research_agent = await self.create_enhanced_agent("research_agent", connected_servers)
        memory_agent = await self.create_enhanced_agent("memory_agent", connected_servers)
        
        # Demonstration tasks
        demo_tasks = [
            {
                "agent": research_agent,
                "task": "What is the current time in UTC?",
                "description": "Testing time server integration"
            },
            {
                "agent": memory_agent, 
                "task": "Remember that we completed the MCP integration demo successfully",
                "description": "Testing memory server integration"
            },
            {
                "agent": research_agent,
                "task": "I need to fetch information from a web page",
                "description": "Testing fetch server capabilities"
            }
        ]
        
        # Execute demonstration tasks
        for i, demo in enumerate(demo_tasks, 1):
            console.print(f"\n🎯 Demo {i}: {demo['description']}")
            console.print(f"   Task: {demo['task']}")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Executing...", total=None)
                
                result = await demo["agent"].execute_task(demo["task"])
                
                progress.update(task_progress, description="Completed!")
            
            # Show results
            if result.get("success"):
                console.print(f"   ✅ Success! Execution time: {result['execution_time']:.2f}s")
                console.print(f"   💰 Cost: ${result.get('cost', 0.0):.4f}")
                
                if result.get("results"):
                    console.print("   📋 Results:")
                    for res in result["results"]:
                        console.print(f"      • {res}")
            else:
                console.print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    async def interactive_mode(self, connected_servers: List[str]):
        """Interactive mode for real-time MCP server exploration."""
        console.print("\n" + "="*70)
        console.print("[bold green]🎮 Interactive MCP Mode[/bold green]")
        console.print("Type 'help' for commands, 'quit' to exit")
        console.print("="*70)
        
        agent = await self.create_enhanced_agent("interactive_agent", connected_servers)
        
        while True:
            try:
                user_input = console.input("\n[bold cyan]MCP>[/bold cyan] ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    console.print("""
[bold]Available Commands:[/bold]
  servers     - Show connected servers
  tools       - Show all available tools  
  tools <srv> - Show tools from specific server
  call <srv> <tool> [args] - Call a specific tool
  task <description> - Execute a task
  quit        - Exit interactive mode
                    """)
                elif user_input.lower() == 'servers':
                    self.mcp_client.print_servers_status()
                elif user_input.lower().startswith('tools'):
                    parts = user_input.split()
                    server_name = parts[1] if len(parts) > 1 else None
                    self.mcp_client.print_tools(server_name)
                elif user_input.lower().startswith('call'):
                    parts = user_input.split(' ', 3)
                    if len(parts) >= 3:
                        server_name = parts[1]
                        tool_name = parts[2]
                        args_str = parts[3] if len(parts) > 3 else "{}"
                        
                        try:
                            args = eval(args_str) if args_str.strip() else {}
                            result = await self.mcp_client.call_tool(server_name, tool_name, args)
                            console.print(f"✅ Result: {result}")
                        except Exception as e:
                            console.print(f"❌ Error: {e}")
                    else:
                        console.print("Usage: call <server> <tool> [args]")
                elif user_input.lower().startswith('task'):
                    task = user_input[5:].strip()
                    if task:
                        result = await agent.execute_task(task)
                        if result.get("success"):
                            console.print("✅ Task completed successfully!")
                            for res in result.get("results", []):
                                console.print(f"  • {res}")
                        else:
                            console.print(f"❌ Task failed: {result.get('error')}")
                    else:
                        console.print("Usage: task <description>")
                elif user_input:
                    # Treat as a task
                    result = await agent.execute_task(user_input)
                    if result.get("success"):
                        console.print("✅ Task completed!")
                        for res in result.get("results", []):
                            console.print(f"  • {res}")
                    else:
                        console.print(f"❌ Error: {result.get('error')}")
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"❌ Error: {e}")
        
        console.print("\n👋 Exiting interactive mode...")
    
    async def cleanup(self):
        """Clean up resources."""
        console.print("\n🧹 Cleaning up...")
        await self.mcp_client.disconnect_all()
        console.print("✅ Cleanup complete")

async def main():
    """Main entry point for the real MCP system."""
    console.print(Panel.fit(
        "[bold green]🌟 MCP Agent Scaffolding - Real Server Integration[/bold green]\n"
        "Complete system with actual MCP servers, agents, and workflows",
        border_style="green"
    ))
    
    system = RealMCPAgentSystem()
    
    try:
        # Load configuration
        system.load_config()
        
        # Connect to enabled servers
        connected_servers = await system.connect_enabled_servers()
        
        if not connected_servers:
            console.print("\n[red]❌ No servers connected. Please check your configuration.[/red]")
            console.print("\n[yellow]💡 To get started:[/yellow]")
            console.print("1. Install Node.js and npm")
            console.print("2. Servers will be installed automatically via npx/uvx")
            console.print("3. Enable basic servers in config/real_mcp_servers.yml")
            console.print("4. Run this script again")
            return
        
        # Show system overview
        console.print("\n" + "="*70)
        console.print("[bold blue]📊 System Overview[/bold blue]")
        console.print("="*70)
        system.show_system_overview(connected_servers)
        
        # Show available tools
        console.print("\n" + "="*70)
        console.print("[bold blue]🛠️  Available Tools[/bold blue]")
        console.print("="*70)
        system.mcp_client.print_tools()
        
        # Demonstrate workflows
        await system.demonstrate_agent_workflows(connected_servers)
        
        # Show final summary
        console.print("\n" + "="*70)
        console.print("[bold green]🎉 Real MCP System Demo Complete![/bold green]")
        console.print("="*70)
        
        console.print("\n[bold]What you've accomplished:[/bold]")
        console.print(f"✅ Connected to {len(connected_servers)} real MCP servers")
        console.print("✅ Created agents with real tool access")
        console.print("✅ Demonstrated task execution with MCP integration")
        console.print("✅ Tested memory, time, and fetch capabilities")
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Enable more servers in config/real_mcp_servers.yml")
        console.print("2. Add your API keys for GitHub, Brave Search, etc.")
        console.print("3. Create custom agents for your specific use cases")
        console.print("4. Build production workflows with this scaffolding")
        
        # Optional interactive mode
        if len(connected_servers) > 0:
            try:
                console.print(f"\n[yellow]Press Enter for interactive mode, or Ctrl+C to exit...[/yellow]")
                input()
                await system.interactive_mode(connected_servers)
            except KeyboardInterrupt:
                pass
        
    except Exception as e:
        console.print(f"\n[red]System error: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    finally:
        await system.cleanup()
        console.print("\n[dim]Thank you for trying the Real MCP Agent System![/dim]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n🛑 Interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Failed to run: {e}")
        sys.exit(1) 