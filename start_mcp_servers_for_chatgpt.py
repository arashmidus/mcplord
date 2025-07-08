#!/usr/bin/env python3
"""
Start MCP Servers for ChatGPT Client Integration

This script starts MCP servers in HTTP/SSE mode so they can be
connected to ChatGPT's MCP client interface.
"""

import asyncio
import subprocess
import signal
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text

console = Console()

class MCPServerManager:
    """Manage multiple MCP servers for ChatGPT integration."""
    
    def __init__(self):
        self.servers: Dict[str, subprocess.Popen] = {}
        self.server_configs = {}
        
    def load_server_configs(self):
        """Load server configurations that support HTTP/SSE."""
        self.server_configs = {
            "playwright": {
                "name": "Playwright Browser Automation",
                "command": ["npx", "@playwright/mcp", "--port", "3001", "--host", "localhost"],
                "port": 3001,
                "description": "35+ browser automation tools",
                "url": "http://localhost:3001",
                "capabilities": ["navigation", "interaction", "screenshots", "pdf", "testing"]
            },
            "memory": {
                "name": "Memory Knowledge Graph", 
                "command": ["npx", "@modelcontextprotocol/server-memory", "--port", "3002"],
                "port": 3002,
                "description": "Persistent memory and knowledge graph",
                "url": "http://localhost:3002",
                "capabilities": ["remember", "search", "forget"]
            },
            "fetch": {
                "name": "Web Content Fetcher",
                "command": ["npx", "@modelcontextprotocol/server-fetch", "--port", "3003"],
                "port": 3003, 
                "description": "Fetch and process web content",
                "url": "http://localhost:3003",
                "capabilities": ["fetch", "web_scraping"]
            },
            "time": {
                "name": "Time & Timezone",
                "command": ["npx", "@modelcontextprotocol/server-time", "--port", "3004"],
                "port": 3004,
                "description": "Time operations and timezone conversion",
                "url": "http://localhost:3004", 
                "capabilities": ["current_time", "timezone_conversion"]
            },
            "mistral_ocr": {
                "name": "Mistral OCR Annotation",
                "command": ["python", "mcp/servers/mistral_ocr_server.py"],
                "port": 3005,
                "description": "PDF processing with structured data extraction",
                "url": "http://localhost:3005",
                "capabilities": ["document_annotation", "bbox_annotation", "research_analysis"]
            }
        }
    
    async def start_server(self, server_key: str) -> bool:
        """Start a single MCP server."""
        if server_key not in self.server_configs:
            console.print(f"❌ Unknown server: {server_key}")
            return False
        
        config = self.server_configs[server_key]
        
        try:
            console.print(f"🚀 Starting {config['name']}...")
            console.print(f"   Command: {' '.join(config['command'])}")
            
            # Start the server process
            process = subprocess.Popen(
                config['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                self.servers[server_key] = process
                console.print(f"✅ {config['name']} started on port {config['port']}")
                console.print(f"   URL: {config['url']}")
                return True
            else:
                # Process died, check why
                stdout, stderr = process.communicate()
                console.print(f"❌ {config['name']} failed to start")
                if stderr:
                    console.print(f"   Error: {stderr}")
                return False
                
        except Exception as e:
            console.print(f"❌ Failed to start {config['name']}: {e}")
            return False
    
    async def start_all_servers(self):
        """Start all configured servers."""
        console.print(Panel.fit(
            "[bold green]🌐 Starting MCP Servers for ChatGPT[/bold green]\n"
            "Servers will be available via HTTP/SSE transport",
            border_style="green"
        ))
        
        started_servers = []
        failed_servers = []
        
        for server_key in self.server_configs.keys():
            success = await self.start_server(server_key)
            if success:
                started_servers.append(server_key)
            else:
                failed_servers.append(server_key)
        
        # Show results
        if started_servers:
            self.show_connection_info(started_servers)
        
        if failed_servers:
            console.print(f"\n❌ Failed to start: {', '.join(failed_servers)}")
            console.print("💡 Some servers may not support HTTP/SSE mode yet")
        
        return len(started_servers) > 0
    
    def show_connection_info(self, started_servers: List[str]):
        """Show connection information for ChatGPT client."""
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 MCP Servers Ready for ChatGPT![/bold green]")
        console.print("="*60)
        
        table = Table(title="Available MCP Servers")
        table.add_column("Server", style="cyan")
        table.add_column("URL", style="green") 
        table.add_column("Port", style="yellow")
        table.add_column("Capabilities", style="blue")
        
        for server_key in started_servers:
            config = self.server_configs[server_key]
            table.add_row(
                config['name'],
                config['url'],
                str(config['port']),
                ', '.join(config['capabilities'][:3]) + "..."
            )
        
        console.print(table)
        
        # Show ChatGPT connection instructions
        console.print("\n[bold]📱 ChatGPT Connection Instructions:[/bold]")
        
        for server_key in started_servers:
            config = self.server_configs[server_key]
            console.print(f"\n🔗 {config['name']}:")
            console.print(f"   URL: [green]{config['url']}[/green]")
            console.print(f"   Label: [cyan]{server_key}_mcp[/cyan]")
            console.print(f"   Authentication: [yellow]No authentication needed[/yellow]")
        
        console.print("\n[bold]🎯 In ChatGPT:[/bold]")
        console.print("1. Open the MCP connection dialog")
        console.print("2. Enter the URL from above")
        console.print("3. Give it a descriptive label")  
        console.print("4. Set Authentication to 'None' or leave empty")
        console.print("5. Click 'Connect'")
        
        console.print("\n[bold]✨ What you can do:[/bold]")
        console.print("• Ask ChatGPT to take screenshots of websites")
        console.print("• Request form filling and web automation")
        console.print("• Generate PDFs from web pages")
        console.print("• Store and retrieve information with memory")
        console.print("• Fetch and analyze web content")
        console.print("• Get current time and convert timezones")
    
    def show_server_status(self):
        """Show current status of all servers."""
        if not self.servers:
            console.print("[yellow]No servers running[/yellow]")
            return
        
        table = Table(title="Server Status")
        table.add_column("Server", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("PID", style="yellow")
        table.add_column("URL", style="blue")
        
        for server_key, process in self.servers.items():
            config = self.server_configs[server_key]
            
            if process.poll() is None:
                status = "🟢 Running"
                pid = str(process.pid)
            else:
                status = "🔴 Stopped"
                pid = "N/A"
            
            table.add_row(
                config['name'],
                status,
                pid,
                config['url']
            )
        
        console.print(table)
    
    async def monitor_servers(self):
        """Monitor server health and show live status."""
        try:
            with Live(self.get_status_display(), refresh_per_second=1) as live:
                while True:
                    live.update(self.get_status_display())
                    await asyncio.sleep(1)
                    
                    # Check if any servers have died
                    dead_servers = []
                    for server_key, process in self.servers.items():
                        if process.poll() is not None:
                            dead_servers.append(server_key)
                    
                    if dead_servers:
                        for server_key in dead_servers:
                            console.print(f"💀 {self.server_configs[server_key]['name']} has stopped")
                            del self.servers[server_key]
        
        except KeyboardInterrupt:
            console.print("\n🛑 Monitoring stopped")
    
    def get_status_display(self) -> Panel:
        """Get current status as a Rich panel."""
        if not self.servers:
            return Panel("No servers running", title="MCP Server Status")
        
        content = []
        for server_key, process in self.servers.items():
            config = self.server_configs[server_key]
            if process.poll() is None:
                status = "🟢 Running"
                content.append(f"{config['name']}: {status} on {config['url']}")
            else:
                content.append(f"{config['name']}: 🔴 Stopped")
        
        return Panel("\n".join(content), title="🌐 MCP Servers for ChatGPT")
    
    def stop_all_servers(self):
        """Stop all running servers."""
        console.print("\n🛑 Stopping all MCP servers...")
        
        for server_key, process in self.servers.items():
            config = self.server_configs[server_key]
            try:
                console.print(f"   Stopping {config['name']}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                console.print(f"   Force killing {config['name']}...")
                process.kill()
            except:
                pass
        
        self.servers.clear()
        console.print("✅ All servers stopped")

async def main():
    """Main entry point."""
    manager = MCPServerManager()
    manager.load_server_configs()
    
    try:
        # Start servers
        success = await manager.start_all_servers()
        
        if not success:
            console.print("[red]❌ No servers could be started[/red]")
            return
        
        # Show instructions
        console.print("\n[bold]🔥 Servers are running![/bold]")
        console.print("Press Ctrl+C to stop all servers")
        console.print("Use the URLs above to connect from ChatGPT")
        
        # Monitor servers
        await manager.monitor_servers()
        
    except KeyboardInterrupt:
        console.print("\n🛑 Shutting down...")
    except Exception as e:
        console.print(f"❌ Error: {e}")
    finally:
        manager.stop_all_servers()

if __name__ == "__main__":
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        console.print("\n🛑 Received shutdown signal")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(main()) 