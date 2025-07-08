#!/usr/bin/env python3
"""
Microsoft Playwright MCP Server Demo

This script demonstrates how to use the Microsoft Playwright MCP server
for advanced browser automation including navigation, screenshots, form filling,
and web scraping.
"""

import asyncio
import sys
import json
from pathlib import Path

# Setup path
current_dir = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, current_dir)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp.client.real_mcp_client import RealMCPClient, MCPServerConfigs

console = Console()

class PlaywrightMCPDemo:
    """Demo class for Microsoft Playwright MCP server."""
    
    def __init__(self):
        self.client = RealMCPClient()
        self.connected = False
    
    async def connect(self):
        """Connect to the Playwright MCP server."""
        console.print("🎭 Connecting to Microsoft Playwright MCP server...")
        
        success = await self.client.connect_to_server(
            "playwright", 
            *MCPServerConfigs.playwright()
        )
        
        if success:
            self.connected = True
            console.print("✅ Connected to Playwright MCP server!")
            
            # Show available tools
            tools = await self.client.list_tools("playwright")
            if tools.get("playwright"):
                console.print(f"📚 Available tools: {len(tools['playwright'])}")
                
                # Show some key tools
                table = Table(title="Key Playwright Tools")
                table.add_column("Tool", style="cyan")
                table.add_column("Description", style="green")
                
                key_tools = [
                    ("browser_navigate", "Navigate to a URL"),
                    ("browser_take_screenshot", "Take a screenshot of the page"),
                    ("browser_click", "Click on an element"),
                    ("browser_type", "Type text into an element"),
                    ("browser_fill", "Fill a form field"),
                    ("browser_wait_for", "Wait for an element or condition"),
                    ("browser_pdf_save", "Save page as PDF"),
                    ("browser_snapshot", "Take visual snapshot with analysis"),
                ]
                
                for tool, desc in key_tools:
                    table.add_row(tool, desc)
                
                console.print(table)
        else:
            console.print("❌ Failed to connect to Playwright server")
            console.print("💡 Make sure Node.js is installed and run: npm install -g @playwright/mcp")
        
        return success
    
    async def demo_basic_navigation(self):
        """Demo basic web navigation."""
        if not self.connected:
            return
        
        console.print("\n🌐 Demo 1: Basic Web Navigation")
        
        try:
            # Navigate to a website
            result = await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://example.com"
            })
            console.print(f"   ✅ Navigated to example.com: {result}")
            
            # Take a screenshot
            screenshot_result = await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "example_screenshot.png"
            })
            console.print(f"   📸 Screenshot saved: {screenshot_result}")
            
        except Exception as e:
            console.print(f"   ❌ Navigation error: {e}")
    
    async def demo_form_interaction(self):
        """Demo form filling and interaction."""
        if not self.connected:
            return
        
        console.print("\n📝 Demo 2: Form Interaction")
        
        try:
            # Navigate to a form page
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://httpbin.org/forms/post"
            })
            console.print("   🔗 Navigated to form page")
            
            # Fill out form fields
            await self.client.call_tool("playwright", "browser_fill", {
                "selector": "input[name='custname']",
                "value": "John Doe"
            })
            console.print("   ✏️  Filled customer name")
            
            await self.client.call_tool("playwright", "browser_fill", {
                "selector": "input[name='custtel']", 
                "value": "555-1234"
            })
            console.print("   📞 Filled phone number")
            
            # Select from dropdown
            await self.client.call_tool("playwright", "browser_select", {
                "selector": "select[name='size']",
                "value": "medium"
            })
            console.print("   📋 Selected size")
            
            # Take screenshot of filled form
            await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "filled_form.png"
            })
            console.print("   📸 Screenshot of filled form saved")
            
        except Exception as e:
            console.print(f"   ❌ Form interaction error: {e}")
    
    async def demo_web_scraping(self):
        """Demo web scraping and data extraction."""
        if not self.connected:
            return
        
        console.print("\n🕷️  Demo 3: Web Scraping")
        
        try:
            # Navigate to a news site
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
            
            # Take a snapshot for analysis
            snapshot_result = await self.client.call_tool("playwright", "browser_snapshot", {
                "name": "hacker_news_analysis"
            })
            console.print(f"   📊 Visual analysis snapshot: {snapshot_result}")
            
            # Take screenshot
            await self.client.call_tool("playwright", "browser_take_screenshot", {
                "path": "hacker_news.png"
            })
            console.print("   📸 Screenshot saved")
            
        except Exception as e:
            console.print(f"   ❌ Scraping error: {e}")
    
    async def demo_pdf_generation(self):
        """Demo PDF generation from web pages."""
        if not self.connected:
            return
        
        console.print("\n📄 Demo 4: PDF Generation")
        
        try:
            # Navigate to a documentation page
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://playwright.dev/docs/intro"
            })
            console.print("   🔗 Navigated to Playwright docs")
            
            # Generate PDF
            pdf_result = await self.client.call_tool("playwright", "browser_pdf_save", {
                "path": "playwright_docs.pdf"
            })
            console.print(f"   📄 PDF saved: {pdf_result}")
            
        except Exception as e:
            console.print(f"   ❌ PDF generation error: {e}")
    
    async def demo_network_monitoring(self):
        """Demo network request monitoring."""
        if not self.connected:
            return
        
        console.print("\n🌐 Demo 5: Network Monitoring")
        
        try:
            # Navigate and monitor network requests
            await self.client.call_tool("playwright", "browser_navigate", {
                "url": "https://httpbin.org/json"
            })
            console.print("   🔗 Navigated to JSON endpoint")
            
            # Get network requests
            network_result = await self.client.call_tool("playwright", "browser_network_requests", {})
            console.print(f"   🌐 Network requests: {network_result}")
            
            # Get console messages
            console_result = await self.client.call_tool("playwright", "browser_console_messages", {})
            console.print(f"   💻 Console messages: {console_result}")
            
        except Exception as e:
            console.print(f"   ❌ Network monitoring error: {e}")
    
    async def demo_test_generation(self):
        """Demo Playwright test generation."""
        if not self.connected:
            return
        
        console.print("\n🧪 Demo 6: Test Generation")
        
        try:
            # Generate Playwright test code
            test_result = await self.client.call_tool("playwright", "browser_generate_playwright_test", {
                "actions": [
                    {"action": "navigate", "url": "https://example.com"},
                    {"action": "click", "selector": "h1"},
                    {"action": "screenshot", "path": "test.png"}
                ]
            })
            console.print(f"   🧪 Generated test code: {test_result}")
            
        except Exception as e:
            console.print(f"   ❌ Test generation error: {e}")
    
    async def run_all_demos(self):
        """Run all Playwright demos."""
        console.print(Panel.fit(
            "[bold blue]🎭 Microsoft Playwright MCP Server Demo[/bold blue]\n"
            "Advanced browser automation with 35+ tools",
            border_style="blue"
        ))
        
        # Connect to server
        connected = await self.connect()
        
        if not connected:
            console.print("\n[red]❌ Could not connect to Playwright server[/red]")
            console.print("\n[yellow]💡 Setup instructions:[/yellow]")
            console.print("1. Install Node.js: brew install node")
            console.print("2. Install Playwright MCP: npm install -g @playwright/mcp")
            console.print("3. Install browsers: npx playwright install")
            console.print("4. Run this demo again")
            return
        
        # Run demos
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            demos = [
                ("Basic Navigation", self.demo_basic_navigation),
                ("Form Interaction", self.demo_form_interaction),
                ("Web Scraping", self.demo_web_scraping),
                ("PDF Generation", self.demo_pdf_generation),
                ("Network Monitoring", self.demo_network_monitoring),
                ("Test Generation", self.demo_test_generation),
            ]
            
            for demo_name, demo_func in demos:
                task = progress.add_task(f"Running {demo_name}...", total=None)
                await demo_func()
                progress.update(task, description=f"{demo_name} completed!")
                await asyncio.sleep(1)  # Brief pause between demos
        
        # Summary
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 Playwright MCP Demo Complete![/bold green]")
        console.print("="*60)
        
        console.print("\n[bold]Files generated:[/bold]")
        console.print("📸 example_screenshot.png")
        console.print("📸 filled_form.png") 
        console.print("📸 hacker_news.png")
        console.print("📄 playwright_docs.pdf")
        
        console.print("\n[bold]Playwright MCP capabilities demonstrated:[/bold]")
        console.print("✅ Web navigation and page loading")
        console.print("✅ Form filling and element interaction")
        console.print("✅ Screenshot and visual capture")
        console.print("✅ PDF generation from web pages")
        console.print("✅ Network request monitoring")
        console.print("✅ Console message capture")
        console.print("✅ Test code generation")
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Use Playwright tools in your agents")
        console.print("2. Build web automation workflows")
        console.print("3. Create testing and monitoring agents")
        console.print("4. Explore all 35+ available tools")
        
    async def cleanup(self):
        """Clean up connections."""
        await self.client.disconnect_all()

async def main():
    """Run the Playwright MCP demo."""
    demo = PlaywrightMCPDemo()
    
    try:
        await demo.run_all_demos()
    except KeyboardInterrupt:
        console.print("\n🛑 Demo interrupted")
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await demo.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 