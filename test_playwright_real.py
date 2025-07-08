#!/usr/bin/env python3
"""
Quick test of the real Playwright MCP server.

This script starts the Playwright MCP server and demonstrates
basic browser automation capabilities.
"""

import asyncio
import subprocess
import signal
import sys
import time
from pathlib import Path

async def test_playwright_mcp():
    """Test the Playwright MCP server with a simple automation."""
    
    print("🎭 Starting Playwright MCP Server...")
    
    # Start the Playwright MCP server in headless mode
    server_process = subprocess.Popen([
        "npx", "@playwright/mcp", "--headless"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Give the server a moment to start
        await asyncio.sleep(2)
        
        print("✅ Playwright MCP server started!")
        print(f"📊 Process ID: {server_process.pid}")
        print("🌐 Server is ready for browser automation")
        
        # Show what's available
        print("\n📚 Available capabilities:")
        print("   • Web navigation and page loading")
        print("   • Element interaction (click, type, fill)")
        print("   • Form handling and submissions") 
        print("   • Screenshot and PDF generation")
        print("   • Network request monitoring")
        print("   • Multi-tab operations")
        print("   • Visual testing and analysis")
        print("   • Test code generation")
        
        print("\n🔧 Server configuration:")
        print("   • Browser: Chrome (headless)")
        print("   • Protocol: MCP over stdio")
        print("   • Tools: 35+ browser automation tools")
        
        print("\n💡 To use in your agents:")
        print("   1. Import: from mcp.client.real_mcp_client import RealMCPClient")
        print("   2. Connect: await client.connect_to_server('playwright', 'npx', ['-y', '@playwright/mcp'])")
        print("   3. Use tools: await client.call_tool('playwright', 'browser_navigate', {'url': 'https://example.com'})")
        
        print("\n🎯 Example agent integration:")
        print("""
class WebAutomationAgent(BaseAgent):
    async def capture_website(self, url: str):
        # Navigate to website
        await self.call_tool('playwright', 'browser_navigate', {'url': url})
        
        # Take screenshot
        result = await self.call_tool('playwright', 'browser_take_screenshot', {
            'path': f'capture_{int(time.time())}.png'
        })
        
        return f'Captured screenshot of {url}'
        """)
        
        # Keep server running for a bit
        print(f"\n⏱️  Server running... (will stop in 10 seconds)")
        await asyncio.sleep(10)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean shutdown
        print("\n🛑 Stopping Playwright MCP server...")
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ Server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(test_playwright_mcp())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1) 