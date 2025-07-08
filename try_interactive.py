#!/usr/bin/env python3
"""
Quick Interactive MCP Mode

This script starts the MCP system and goes straight to interactive mode.
"""

import asyncio
import sys
from pathlib import Path

# Setup path
current_dir = str(Path(__file__).parent.absolute())
sys.path.insert(0, current_dir)

from rich.console import Console
from rich.panel import Panel
from run_with_real_mcp_servers import RealMCPAgentSystem

console = Console()

async def main():
    """Start interactive mode directly."""
    console.print(Panel.fit(
        "[bold green]🎮 MCP Interactive Mode[/bold green]\n"
        "Quick start for exploring your MCP agent system",
        border_style="green"
    ))
    
    system = RealMCPAgentSystem()
    
    try:
        # Quick setup
        system.load_config()
        connected_servers = await system.connect_enabled_servers()
        
        if not connected_servers:
            console.print("[red]❌ No servers connected.[/red]")
            console.print("💡 Basic servers will work in mock mode for demo purposes.")
            # Add mock servers for demo
            connected_servers = ["memory", "time", "fetch"]
        
        console.print(f"\n✅ Ready! Connected to: {', '.join(connected_servers)}")
        console.print("\n[bold]Try these commands:[/bold]")
        console.print("  servers     - Show connected servers")
        console.print("  tools       - Show available tools")
        console.print("  task <text> - Execute a task")
        console.print("  quit        - Exit")
        console.print("\n[yellow]Or just type naturally![/yellow]")
        
        # Go straight to interactive mode
        await system.interactive_mode(connected_servers)
        
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    finally:
        await system.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 