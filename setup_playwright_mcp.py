#!/usr/bin/env python3
"""
Playwright MCP Server Setup Script

This script sets up Microsoft's official Playwright MCP server with all necessary
dependencies and provides a comprehensive demonstration of its capabilities.
"""

import asyncio
import subprocess
import sys
import shutil
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.prompt import Confirm, Prompt

# Add current directory to path for imports
current_dir = str(Path(__file__).parent.absolute())
sys.path.insert(0, current_dir)

from mcp.client.real_mcp_client import RealMCPClient, MCPServerConfigs

console = Console()

class PlaywrightMCPSetup:
    """Complete setup and demo for Playwright MCP server."""
    
    def __init__(self):
        self.client = RealMCPClient()
        self.setup_complete = False
        
    def check_dependency(self, command: str, install_command: str = None) -> bool:
        """Check if a dependency is installed."""
        try:
            result = subprocess.run([command, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                console.print(f"✅ {command}: {version}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        console.print(f"❌ {command}: Not found")
        if install_command:
            console.print(f"   Install with: {install_command}")
        return False
    
    def check_dependencies(self) -> bool:
        """Check all required dependencies."""
        console.print("\n🔍 Checking dependencies...")
        
        # Check Node.js
        node_ok = self.check_dependency("node", "brew install node")
        
        # Check npm
        npm_ok = self.check_dependency("npm", "comes with Node.js")
        
        # Check if playwright browsers are installed
        playwright_ok = False
        try:
            result = subprocess.run(["npx", "playwright", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                console.print(f"✅ playwright: {result.stdout.strip()}")
                playwright_ok = True
            else:
                console.print("❌ playwright: Not found")
        except:
            console.print("❌ playwright: Not found")
        
        return node_ok and npm_ok
    
    async def install_playwright_mcp(self) -> bool:
        """Install the Playwright MCP server."""
        console.print("\n📦 Installing Playwright MCP server...")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Install Playwright MCP
                task1 = progress.add_task("Installing @playwright/mcp...", total=None)
                result = subprocess.run(
                    ["npm", "install", "-g", "@playwright/mcp"],
                    capture_output=True, text=True, timeout=120
                )
                
                if result.returncode != 0:
                    console.print(f"❌ Failed to install @playwright/mcp: {result.stderr}")
                    return False
                
                progress.update(task1, description="@playwright/mcp installed!")
                
                # Install Playwright browsers
                task2 = progress.add_task("Installing Playwright browsers...", total=None)
                result = subprocess.run(
                    ["npx", "playwright", "install"],
                    capture_output=True, text=True, timeout=300
                )
                
                if result.returncode != 0:
                    console.print(f"❌ Failed to install browsers: {result.stderr}")
                    return False
                
                progress.update(task2, description="Playwright browsers installed!")
            
            console.print("✅ Playwright MCP server installation complete!")
            return True
            
        except Exception as e:
            console.print(f"❌ Installation failed: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to Playwright MCP server."""
        console.print("\n🔌 Testing Playwright MCP server connection...")
        
        try:
            success = await self.client.connect_to_server(
                "playwright",
                *MCPServerConfigs.playwright()
            )
            
            if success:
                console.print("✅ Successfully connected to Playwright MCP server!")
                
                # Show available tools
                tools = await self.client.list_tools("playwright")
                if tools.get("playwright"):
                    tool_count = len(tools["playwright"])
                    console.print(f"📚 Available tools: {tool_count}")
                    
                    # Show key capabilities
                    table = Table(title="Playwright MCP Capabilities")
                    table.add_column("Category", style="cyan")
                    table.add_column("Tools", style="green")
                    
                    capabilities = {
                        "Navigation": "browser_navigate, browser_back, browser_forward, browser_reload",
                        "Interaction": "browser_click, browser_type, browser_fill, browser_select",
                        "Visual": "browser_take_screenshot, browser_snapshot, browser_pdf_save",
                        "Waiting": "browser_wait_for, browser_wait_for_navigation",
                        "Forms": "browser_fill, browser_select, browser_file_upload",
                        "Tabs": "browser_tab_new, browser_tab_select, browser_tab_close",
                        "Monitoring": "browser_network_requests, browser_console_messages",
                        "Testing": "browser_generate_playwright_test"
                    }
                    
                    for category, tool_list in capabilities.items():
                        table.add_row(category, tool_list)
                    
                    console.print(table)
                
                return True
            else:
                console.print("❌ Failed to connect to Playwright MCP server")
                return False
                
        except Exception as e:
            console.print(f"❌ Connection test failed: {e}")
            return False
    
    async def run_interactive_demo(self):
        """Run an interactive demonstration of Playwright capabilities."""
        console.print(Panel.fit(
            "[bold blue]🎭 Interactive Playwright MCP Demo[/bold blue]\n"
            "Choose demonstrations to run",
            border_style="blue"
        ))
        
        demos = {
            "1": ("Basic Navigation & Screenshots", self.demo_navigation),
            "2": ("Form Interaction", self.demo_forms),
            "3": ("Web Scraping & Data Extraction", self.demo_scraping),
            "4": ("PDF Generation", self.demo_pdf),
            "5": ("Network Monitoring", self.demo_network),
            "6": ("Multi-tab Operations", self.demo_tabs),
            "7": ("Visual Testing", self.demo_visual),
            "8": ("Test Generation", self.demo_test_generation),
            "9": ("Run All Demos", self.run_all_demos)
        }
        
        while True:
            console.print("\n[bold]Available Demos:[/bold]")
            for key, (name, _) in demos.items():
                console.print(f"  {key}. {name}")
            console.print("  0. Exit")
            
            choice = Prompt.ask("\nSelect a demo", choices=list(demos.keys()) + ["0"])
            
            if choice == "0":
                break
            elif choice in demos:
                name, demo_func = demos[choice]
                console.print(f"\n🚀 Running: {name}")
                await demo_func()
                console.print(f"✅ {name} completed!\n")
            
            if not Confirm.ask("Continue with more demos?", default=True):
                break
    
    async def demo_navigation(self):
        """Demo basic navigation and screenshots."""
        try:
            # Navigate to example.com
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://example.com"
            })
            console.print("   🔗 Navigated to example.com")
            
            # Take screenshot
            await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "example_page.png"
            })
            console.print("   📸 Screenshot saved as example_page.png")
            
            # Navigate to another page
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://httpbin.org"
            })
            console.print("   🔗 Navigated to httpbin.org")
            
            # Take another screenshot
            await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "httpbin_page.png"
            })
            console.print("   📸 Screenshot saved as httpbin_page.png")
            
        except Exception as e:
            console.print(f"   ❌ Navigation demo error: {e}")
    
    async def demo_forms(self):
        """Demo form interaction."""
        try:
            # Navigate to a form
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://httpbin.org/forms/post"
            })
            console.print("   🔗 Navigated to form page")
            
            # Fill form fields
            await self.client.call_tool("playwright", "browser_fill", {
                "selector": "input[name='custname']",
                "value": "Playwright Demo User"
            })
            console.print("   ✏️  Filled customer name")
            
            await self.client.call_tool("playwright", "browser_fill", {
                "selector": "input[name='custtel']",
                "value": "555-PLAYWRIGHT"
            })
            console.print("   📞 Filled phone number")
            
            # Select dropdown
            await self.client.call_tool("playwright", "browser_select", {
                "selector": "select[name='size']",
                "value": "large"
            })
            console.print("   📋 Selected size")
            
            # Take screenshot of filled form
            await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "filled_form_demo.png"
            })
            console.print("   📸 Screenshot of filled form saved")
            
        except Exception as e:
            console.print(f"   ❌ Form demo error: {e}")
    
    async def demo_scraping(self):
        """Demo web scraping capabilities."""
        try:
            # Navigate to a content-rich page
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://news.ycombinator.com"
            })
            console.print("   🔗 Navigated to Hacker News")
            
            # Wait for content to load
            await self.client.call_tool("playwright", "browser_wait_for", {
                "selector": ".storylink",
                "timeout": 10000
            })
            console.print("   ⏳ Waited for stories to load")
            
            # Take visual snapshot for analysis
            result = await self.client.call_tool("playwright", "browser_snapshot", {
                "name": "hacker_news_content"
            })
            console.print("   📊 Visual content snapshot taken")
            
            # Take screenshot
            await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "hacker_news_demo.png"
            })
            console.print("   📸 Screenshot saved")
            
        except Exception as e:
            console.print(f"   ❌ Scraping demo error: {e}")
    
    async def demo_pdf(self):
        """Demo PDF generation."""
        try:
            # Navigate to documentation
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://playwright.dev/docs/intro"
            })
            console.print("   🔗 Navigated to Playwright documentation")
            
            # Generate PDF
            await self.client.call_tool("playwright", "browser_pdf_save", {
                "path": "playwright_docs_demo.pdf"
            })
            console.print("   📄 PDF saved as playwright_docs_demo.pdf")
            
        except Exception as e:
            console.print(f"   ❌ PDF demo error: {e}")
    
    async def demo_network(self):
        """Demo network monitoring."""
        try:
            # Navigate to a page with network activity
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://httpbin.org/json"
            })
            console.print("   🔗 Navigated to JSON endpoint")
            
            # Monitor network requests
            network_result = await self.client.call_tool("playwright", "browser_network_requests", {})
            console.print("   🌐 Network requests captured")
            
            # Check console messages
            console_result = await self.client.call_tool("playwright", "browser_console_messages", {})
            console.print("   💻 Console messages captured")
            
        except Exception as e:
            console.print(f"   ❌ Network demo error: {e}")
    
    async def demo_tabs(self):
        """Demo multi-tab operations."""
        try:
            # Open new tab
            await self.client.call_tool("playwright", "browser_tab_new", {})
            console.print("   🆕 Opened new tab")
            
            # Navigate in new tab
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://example.com"
            })
            console.print("   🔗 Navigated in new tab")
            
            # Take screenshot
            await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "new_tab_demo.png"
            })
            console.print("   📸 Screenshot of new tab saved")
            
        except Exception as e:
            console.print(f"   ❌ Tabs demo error: {e}")
    
    async def demo_visual(self):
        """Demo visual testing capabilities."""
        try:
            # Navigate to a visually interesting page
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://playwright.dev"
            })
            console.print("   🔗 Navigated to Playwright homepage")
            
            # Take visual snapshot with analysis
            await self.client.call_tool("playwright", "browser_snapshot", {
                "name": "playwright_homepage_visual"
            })
            console.print("   👁️  Visual analysis snapshot taken")
            
            # Take regular screenshot for comparison
            await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "playwright_homepage.png"
            })
            console.print("   📸 Screenshot saved for comparison")
            
        except Exception as e:
            console.print(f"   ❌ Visual demo error: {e}")
    
    async def demo_test_generation(self):
        """Demo test generation capabilities."""
        try:
            # Generate a test script
            result = await self.client.call_tool("playwright", "browser_generate_playwright_test", {
                "actions": [
                    {"action": "navigate", "url": "https://example.com"},
                    {"action": "click", "selector": "h1"},
                    {"action": "screenshot", "path": "test_screenshot.png"}
                ]
            })
            console.print("   🧪 Playwright test code generated")
            
        except Exception as e:
            console.print(f"   ❌ Test generation demo error: {e}")
    
    async def run_all_demos(self):
        """Run all demos in sequence."""
        demos = [
            ("Navigation & Screenshots", self.demo_navigation),
            ("Form Interaction", self.demo_forms),
            ("Web Scraping", self.demo_scraping),
            ("PDF Generation", self.demo_pdf),
            ("Network Monitoring", self.demo_network),
            ("Multi-tab Operations", self.demo_tabs),
            ("Visual Testing", self.demo_visual),
            ("Test Generation", self.demo_test_generation),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Running all demos...", total=len(demos))
            
            for demo_name, demo_func in demos:
                progress.update(task, description=f"Running {demo_name}...")
                await demo_func()
                progress.advance(task)
                await asyncio.sleep(0.5)  # Brief pause between demos
    
    async def setup_and_run(self):
        """Complete setup and demonstration process."""
        console.print(Panel.fit(
            "[bold green]🎭 Playwright MCP Server Setup & Demo[/bold green]\n"
            "Microsoft's official browser automation MCP server",
            border_style="green"
        ))
        
        # Check dependencies
        if not self.check_dependencies():
            console.print("\n[red]❌ Missing dependencies. Please install Node.js first.[/red]")
            console.print("[yellow]Install Node.js with: brew install node[/yellow]")
            return
        
        # Ask about installation
        if Confirm.ask("\nInstall/update Playwright MCP server?", default=True):
            if not await self.install_playwright_mcp():
                console.print("[red]❌ Installation failed. Exiting.[/red]")
                return
        
        # Test connection
        if not await self.test_connection():
            console.print("[red]❌ Connection test failed. Exiting.[/red]")
            return
        
        # Run demonstrations
        if Confirm.ask("\nRun interactive demonstrations?", default=True):
            await self.run_interactive_demo()
        
        # Show summary
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 Playwright MCP Setup Complete![/bold green]")
        console.print("="*60)
        
        console.print("\n[bold]What you can do now:[/bold]")
        console.print("✅ Use 35+ browser automation tools")
        console.print("✅ Navigate websites and take screenshots")
        console.print("✅ Fill forms and interact with elements")
        console.print("✅ Generate PDFs from web pages")
        console.print("✅ Monitor network requests and console logs")
        console.print("✅ Perform visual testing and analysis")
        console.print("✅ Generate Playwright test code")
        console.print("✅ Build web automation agents")
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Integrate Playwright tools into your agents")
        console.print("2. Build web scraping and automation workflows")
        console.print("3. Create testing and monitoring agents")
        console.print("4. Explore all available tools and capabilities")
        
        console.print(f"\n[bold]Configuration:[/bold]")
        console.print(f"   Server config: config/real_mcp_servers.yml")
        console.print(f"   Demo script: examples/playwright_demo.py")
        console.print(f"   Client code: mcp/client/real_mcp_client.py")
    
    async def cleanup(self):
        """Clean up connections and resources."""
        await self.client.disconnect_all()

async def main():
    """Main entry point."""
    setup = PlaywrightMCPSetup()
    
    try:
        await setup.setup_and_run()
    except KeyboardInterrupt:
        console.print("\n🛑 Setup interrupted")
    except Exception as e:
        console.print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await setup.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 