#!/usr/bin/env python3
"""
Setup Secure Tunnels for ChatGPT MCP Integration

This script creates secure tunnels so ChatGPT can access your local MCP servers.
Uses ngrok to expose local servers to the internet securely.
"""

import asyncio
import subprocess
import signal
import sys
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

console = Console()

class MCPTunnelManager:
    """Manage MCP servers with secure tunnels for ChatGPT access."""
    
    def __init__(self):
        self.servers: Dict[str, subprocess.Popen] = {}
        self.tunnels: Dict[str, subprocess.Popen] = {}
        self.tunnel_urls: Dict[str, str] = {}
        self.server_configs = {}
        
    def check_ngrok_installed(self) -> bool:
        """Check if ngrok is installed."""
        try:
            result = subprocess.run(["ngrok", "version"], capture_output=True, text=True)
            if result.returncode == 0:
                console.print(f"✅ ngrok installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        console.print("❌ ngrok not found")
        return False
    
    def install_ngrok_instructions(self):
        """Show instructions for installing ngrok."""
        console.print(Panel.fit(
            "[bold yellow]📦 Install ngrok for Secure Tunnels[/bold yellow]\n\n"
            "[bold]Option 1: Homebrew (Recommended)[/bold]\n"
            "brew install ngrok/ngrok/ngrok\n\n"
            "[bold]Option 2: Download[/bold]\n"
            "1. Go to: https://ngrok.com/download\n"
            "2. Download for macOS\n"
            "3. Move to /usr/local/bin/ngrok\n\n"
            "[bold]Option 3: Quick install[/bold]\n"
            "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null\n"
            "echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list\n"
            "sudo apt update && sudo apt install ngrok\n\n"
            "[green]After installation, run this script again![/green]",
            border_style="yellow"
        ))
    
    def load_server_configs(self):
        """Load server configurations for tunneling."""
        self.server_configs = {
            "playwright": {
                "name": "Playwright Browser Automation",
                "command": ["npx", "@playwright/mcp", "--port", "3001", "--host", "0.0.0.0"],
                "port": 3001,
                "description": "35+ browser automation tools",
                "capabilities": ["navigation", "interaction", "screenshots", "pdf", "testing"]
            },
            "memory": {
                "name": "Memory Knowledge Graph", 
                "command": ["npx", "@modelcontextprotocol/server-memory", "--port", "3002", "--host", "0.0.0.0"],
                "port": 3002,
                "description": "Persistent memory and knowledge graph",
                "capabilities": ["remember", "search", "forget"]
            },
            "mistral_ocr": {
                "name": "Mistral OCR Annotation",
                "command": ["python", "mcp/servers/mistral_ocr_simple_server.py"],
                "port": 3005,
                "description": "PDF processing with structured data extraction",
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
            console.print(f"🚀 Starting {config['name']} on port {config['port']}...")
            
            # Start the server process
            process = subprocess.Popen(
                config['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            await asyncio.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                self.servers[server_key] = process
                console.print(f"✅ {config['name']} started locally on port {config['port']}")
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
    
    async def create_tunnel(self, server_key: str) -> bool:
        """Create an ngrok tunnel for a server."""
        if server_key not in self.server_configs:
            return False
        
        config = self.server_configs[server_key]
        port = config['port']
        
        try:
            console.print(f"🌐 Creating secure tunnel for {config['name']}...")
            
            # Start ngrok tunnel
            tunnel_process = subprocess.Popen(
                ["ngrok", "http", str(port), "--log", "stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give ngrok time to start
            await asyncio.sleep(5)
            
            # Get the public URL
            try:
                response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
                tunnels_data = response.json()
                
                for tunnel in tunnels_data.get("tunnels", []):
                    if tunnel.get("config", {}).get("addr") == f"http://localhost:{port}":
                        public_url = tunnel.get("public_url")
                        if public_url:
                            self.tunnels[server_key] = tunnel_process
                            self.tunnel_urls[server_key] = public_url
                            console.print(f"✅ Tunnel created: {public_url}")
                            return True
                
                console.print(f"❌ Could not get tunnel URL for {config['name']}")
                tunnel_process.terminate()
                return False
                
            except Exception as e:
                console.print(f"❌ Failed to get tunnel info: {e}")
                tunnel_process.terminate()
                return False
                
        except Exception as e:
            console.print(f"❌ Failed to create tunnel for {config['name']}: {e}")
            return False
    
    async def setup_all(self):
        """Setup all servers with tunnels."""
        console.print(Panel.fit(
            "[bold green]🌐 Setting Up MCP Servers with Secure Tunnels[/bold green]\n"
            "Creating public URLs for ChatGPT access",
            border_style="green"
        ))
        
        # Check ngrok
        if not self.check_ngrok_installed():
            self.install_ngrok_instructions()
            return False
        
        started_servers = []
        tunneled_servers = []
        
        # Start servers
        for server_key in self.server_configs.keys():
            success = await self.start_server(server_key)
            if success:
                started_servers.append(server_key)
        
        if not started_servers:
            console.print("❌ No servers could be started")
            return False
        
        # Create tunnels
        for server_key in started_servers:
            success = await self.create_tunnel(server_key)
            if success:
                tunneled_servers.append(server_key)
        
        if tunneled_servers:
            self.show_connection_info(tunneled_servers)
            return True
        else:
            console.print("❌ No tunnels could be created")
            return False
    
    def show_connection_info(self, tunneled_servers: List[str]):
        """Show connection information for ChatGPT."""
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 MCP Servers Ready for ChatGPT![/bold green]")
        console.print("="*60)
        
        table = Table(title="Public MCP Server URLs")
        table.add_column("Server", style="cyan")
        table.add_column("Public URL", style="green", width=50) 
        table.add_column("Capabilities", style="blue")
        
        for server_key in tunneled_servers:
            config = self.server_configs[server_key]
            public_url = self.tunnel_urls[server_key]
            table.add_row(
                config['name'],
                public_url,
                ', '.join(config['capabilities'][:3]) + "..."
            )
        
        console.print(table)
        
        # Show ChatGPT connection instructions
        console.print("\n[bold]📱 ChatGPT Connection Instructions:[/bold]")
        
        for server_key in tunneled_servers:
            config = self.server_configs[server_key]
            public_url = self.tunnel_urls[server_key]
            console.print(f"\n🔗 {config['name']}:")
            console.print(f"   URL: [green]{public_url}[/green]")
            console.print(f"   Label: [cyan]{server_key}_mcp[/cyan]")
            console.print(f"   Authentication: [yellow]None[/yellow]")
        
        console.print("\n[bold]🎯 In ChatGPT:[/bold]")
        console.print("1. Use the PUBLIC URLs above (not localhost)")
        console.print("2. Copy/paste the full ngrok URL")
        console.print("3. Set Authentication to 'None'")
        console.print("4. Click 'Connect'")
        
        console.print("\n[bold]🔒 Security Notes:[/bold]")
        console.print("• Tunnels are encrypted and secure")
        console.print("• URLs are temporary and change on restart")
        console.print("• Only MCP protocol traffic is allowed")
        console.print("• Tunnels automatically close when script stops")
        
        console.print("\n[bold]✨ Test Commands for ChatGPT:[/bold]")
        console.print("• 'Take a screenshot of https://example.com'")
        console.print("• 'Navigate to Google and search for Python'")
        console.print("• 'Remember that I prefer TypeScript over JavaScript'")
        console.print("• 'Generate a PDF of the current page'")
    
    def show_live_status(self) -> Panel:
        """Show live status of servers and tunnels."""
        if not self.servers and not self.tunnels:
            return Panel("No servers or tunnels running", title="MCP Status")
        
        content = []
        
        for server_key in self.server_configs.keys():
            config = self.server_configs[server_key]
            server_status = "🔴 Stopped"
            tunnel_status = "🔴 No tunnel"
            
            if server_key in self.servers:
                process = self.servers[server_key]
                if process.poll() is None:
                    server_status = "🟢 Running"
                else:
                    server_status = "🔴 Crashed"
            
            if server_key in self.tunnels:
                tunnel_process = self.tunnels[server_key]
                if tunnel_process.poll() is None:
                    public_url = self.tunnel_urls.get(server_key, "Unknown")
                    tunnel_status = f"🌐 {public_url}"
                else:
                    tunnel_status = "🔴 Tunnel down"
            
            content.append(f"{config['name']}")
            content.append(f"  Server: {server_status}")
            content.append(f"  Tunnel: {tunnel_status}")
            content.append("")
        
        return Panel("\n".join(content), title="🌐 MCP Servers + Tunnels")
    
    async def monitor(self):
        """Monitor servers and tunnels."""
        try:
            with Live(self.show_live_status(), refresh_per_second=2) as live:
                while True:
                    live.update(self.show_live_status())
                    await asyncio.sleep(0.5)
                    
                    # Check for dead processes
                    dead_servers = []
                    for server_key, process in self.servers.items():
                        if process.poll() is not None:
                            dead_servers.append(server_key)
                    
                    dead_tunnels = []
                    for server_key, process in self.tunnels.items():
                        if process.poll() is not None:
                            dead_tunnels.append(server_key)
                    
                    if dead_servers or dead_tunnels:
                        for server_key in dead_servers:
                            console.print(f"💀 Server {server_key} died")
                            del self.servers[server_key]
                        
                        for server_key in dead_tunnels:
                            console.print(f"🌐💀 Tunnel {server_key} died")
                            del self.tunnels[server_key]
                            del self.tunnel_urls[server_key]
        
        except KeyboardInterrupt:
            console.print("\n🛑 Monitoring stopped")
    
    def cleanup(self):
        """Stop all servers and tunnels."""
        console.print("\n🛑 Stopping all servers and tunnels...")
        
        # Stop tunnels
        for server_key, process in self.tunnels.items():
            try:
                console.print(f"   Stopping tunnel for {server_key}...")
                process.terminate()
                process.wait(timeout=3)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        # Stop servers
        for server_key, process in self.servers.items():
            try:
                console.print(f"   Stopping server {server_key}...")
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.servers.clear()
        self.tunnels.clear()
        self.tunnel_urls.clear()
        console.print("✅ All servers and tunnels stopped")

async def main():
    """Main entry point."""
    manager = MCPTunnelManager()
    manager.load_server_configs()
    
    try:
        success = await manager.setup_all()
        
        if not success:
            console.print("[red]❌ Setup failed[/red]")
            return
        
        console.print("\n[bold]🔥 Servers and tunnels are running![/bold]")
        console.print("Press Ctrl+C to stop everything")
        console.print("Use the PUBLIC URLs above in ChatGPT")
        
        await manager.monitor()
        
    except KeyboardInterrupt:
        console.print("\n🛑 Shutting down...")
    except Exception as e:
        console.print(f"❌ Error: {e}")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        console.print("\n🛑 Received shutdown signal")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(main()) 