#!/usr/bin/env python3
"""
Run Real MCP Agent System

This script demonstrates how to run the actual MCP agent system with real servers.
"""

import asyncio
import sys
import os
import time
import subprocess
import signal
from pathlib import Path

# Setup path
current_dir = str(Path(__file__).parent.absolute())
sys.path.insert(0, current_dir)
os.environ['PYTHONPATH'] = f"{current_dir}:{os.environ.get('PYTHONPATH', '')}"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import httpx

console = Console()

class MCPSystemRunner:
    """Manages the MCP system components."""
    
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:8001"
    
    async def start_context_server(self):
        """Start the MCP context server."""
        console.print("🚀 Starting MCP Context Server...")
        
        # Start server as subprocess
        env = os.environ.copy()
        env['PYTHONPATH'] = current_dir
        
        self.server_process = subprocess.Popen(
            [sys.executable, "mcp/servers/context_server.py"],
            cwd=current_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        for i in range(10):  # Try for 10 seconds
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/health", timeout=1.0)
                    if response.status_code == 200:
                        console.print("✅ Context server started successfully!")
                        return True
            except:
                pass
            
            await asyncio.sleep(1)
        
        console.print("❌ Failed to start context server")
        return False
    
    async def stop_context_server(self):
        """Stop the MCP context server."""
        if self.server_process:
            console.print("🛑 Stopping context server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
    
    async def check_server_status(self):
        """Check if the server is running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=2.0)
                return response.status_code == 200
        except:
            return False
    
    async def get_server_stats(self):
        """Get server statistics."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/stats", timeout=2.0)
                if response.status_code == 200:
                    return response.json()
        except:
            pass
        return {}

async def demo_real_agent_workflow():
    """Demonstrate a real agent workflow with the running server."""
    console.print("\n[bold blue]🤖 Real Agent Workflow Demo[/bold blue]")
    
    from agents.examples.research_agent import create_research_agent
    
    try:
        # Create a research agent that connects to real server
        agent = await create_research_agent([
            "http://localhost:8001"
        ])
        
        console.print("✅ Agent created and connected to MCP server")
        
        # Execute a research task
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Executing real research task...", total=None)
            
            result = await agent.execute_task(
                "Research the applications of large language models in software development",
                context={"priority": "high", "depth": "comprehensive"}
            )
            
            progress.update(task, description="Research task completed!")
        
        # Show results
        table = Table(title="Real Agent Execution Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Success", "✅ Yes" if result.get("success") else "❌ No")
        table.add_row("Cost", f"${result.get('cost', 0.0):.2f}")
        table.add_row("Execution Time", f"{result.get('execution_time', 0.0):.2f}s")
        table.add_row("Error", result.get('error', 'None'))
        
        console.print(table)
        
        # Show agent status
        status = agent.get_status()
        console.print(f"\n📊 Agent Status: {status['status']}")
        console.print(f"💰 Total Cost: ${status['total_cost']:.2f}")
        console.print(f"🔄 Iterations: {status['iteration_count']}")
        
        await agent.stop()
        return True
        
    except Exception as e:
        console.print(f"❌ Agent workflow failed: {e}")
        return False

async def demo_server_interaction():
    """Demonstrate direct server interaction."""
    console.print("\n[bold blue]🌐 Server Interaction Demo[/bold blue]")
    
    try:
        async with httpx.AsyncClient() as client:
            # Get server stats
            response = await client.get("http://localhost:8001/stats")
            if response.status_code == 200:
                stats = response.json()
                
                table = Table(title="Server Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Server Time", str(stats.get("server_time", "Unknown")))
                table.add_row("Total Agents", str(stats.get("total_agents", 0)))
                table.add_row("State Keys", str(stats.get("total_state_keys", 0)))
                table.add_row("Available Tools", str(stats.get("total_tools", 0)))
                table.add_row("History Entries", str(stats.get("history_entries", 0)))
                
                console.print(table)
            
            # Test state operations
            console.print("\n🔧 Testing state operations...")
            
            # Set some state
            state_data = {
                "agent_id": "demo_agent",
                "key": "demo_research_topic",
                "value": "AI applications in education",
                "timestamp": time.time()
            }
            
            response = await client.post("http://localhost:8001/state", json=state_data)
            if response.status_code == 200:
                console.print("✅ State set successfully")
            
            # Get the state back
            response = await client.get("http://localhost:8001/state/demo_research_topic")
            if response.status_code == 200:
                data = response.json()
                console.print(f"✅ State retrieved: {data['value']}")
            
            return True
            
    except Exception as e:
        console.print(f"❌ Server interaction failed: {e}")
        return False

async def main():
    """Run the real MCP system demonstration."""
    console.print(Panel.fit(
        "[bold green]🚀 MCP Agent Scaffolding - Real System[/bold green]\n"
        "Running the actual MCP infrastructure with real servers and agents",
        border_style="green"
    ))
    
    runner = MCPSystemRunner()
    
    try:
        # Start the context server
        server_started = await runner.start_context_server()
        
        if not server_started:
            console.print("❌ Could not start context server. Please check logs.")
            return
        
        # Wait a moment for full startup
        await asyncio.sleep(2)
        
        # Check server status
        status = await runner.check_server_status()
        if status:
            console.print("✅ Server is healthy and responding")
        else:
            console.print("⚠️  Server might not be fully ready")
        
        # Demo server interaction
        await demo_server_interaction()
        
        # Demo real agent workflow
        await demo_real_agent_workflow()
        
        # Show final status
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 Real System Demo Complete![/bold green]")
        console.print("="*60)
        
        console.print("\n[bold]You've successfully run:[/bold]")
        console.print("✅ Real MCP Context Server (HTTP API)")
        console.print("✅ Agent connecting to live server")
        console.print("✅ Context fetching and state management")
        console.print("✅ Task execution with real MCP integration")
        
        console.print("\n[bold]The server is still running at:[/bold]")
        console.print(f"🌐 Health: http://localhost:8001/health")
        console.print(f"📊 Stats: http://localhost:8001/stats")
        console.print(f"👥 Agents: http://localhost:8001/agents")
        
        console.print("\n[bold]To build your own system:[/bold]")
        console.print("1. Keep the context server running")
        console.print("2. Create your own agent classes extending BaseAgent")
        console.print("3. Add your own MCP tools and servers")
        console.print("4. Scale with multiple agent instances")
        
        # Ask if user wants to keep server running
        console.print("\n[yellow]Press Ctrl+C to stop the server when you're done exploring[/yellow]")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(5)
                # Check if server is still alive
                if not await runner.check_server_status():
                    console.print("⚠️  Server appears to have stopped")
                    break
        except KeyboardInterrupt:
            console.print("\n\n🛑 Shutting down...")
        
    except Exception as e:
        console.print(f"\n[red]System error: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean shutdown
        await runner.stop_context_server()
        console.print("✅ Server stopped cleanly")
        console.print("\n[dim]Thank you for trying the real MCP Agent System![/dim]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n🛑 Interrupted")
    except Exception as e:
        console.print(f"\n❌ Failed to run: {e}")
        sys.exit(1) 