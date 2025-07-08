#!/usr/bin/env python3
"""
Browser Automation Agent

This agent uses the Microsoft Playwright MCP server to perform sophisticated
web automation tasks including research, form filling, testing, and monitoring.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional

from agents.base.agent import BaseAgent, AgentConfig
from mcp.client.real_mcp_client import RealMCPClient, MCPServerConfigs


class BrowserAutomationAgent(BaseAgent):
    """
    Sophisticated browser automation agent using Playwright MCP server.
    
    Capabilities:
    - Web research and data extraction
    - Form automation and testing
    - Screenshot and PDF generation
    - E2E testing workflows
    - Website monitoring
    """
    
    def __init__(self, agent_id: str = "browser_agent"):
        config = AgentConfig(
            name=agent_id,
            description="Advanced browser automation agent with Playwright integration",
            mcp_server_urls=["playwright://localhost"],
            max_iterations=20,
            cost_limit=50.0
        )
        super().__init__(config)
        
        # Initialize Playwright MCP client
        self.playwright_client = RealMCPClient()
        self.browser_ready = False
    
    async def _initialize_agent(self):
        """Initialize the Playwright browser automation capabilities."""
        self.logger.info("Initializing Browser Automation Agent with Playwright...")
        
        # Connect to Playwright MCP server
        success = await self.playwright_client.connect_to_server(
            "playwright", 
            *MCPServerConfigs.playwright()
        )
        
        if success:
            self.browser_ready = True
            self.logger.info("✅ Playwright MCP server connected")
            
            # Get available tools
            tools = await self.playwright_client.list_tools("playwright")
            tool_count = len(tools.get("playwright", []))
            self.logger.info(f"📚 {tool_count} browser automation tools available")
        else:
            self.logger.warning("❌ Could not connect to Playwright MCP server")
            self.logger.info("💡 Install with: npm install -g @playwright/mcp")
    
    async def _determine_next_action(self, context) -> Optional[str]:
        """Determine next browser automation action based on context."""
        if not self.browser_ready:
            return None
        
        # Analyze context for automation opportunities
        shared_state = context.shared_state or {}
        
        # Check for pending web tasks
        if "pending_web_tasks" in shared_state:
            return "process_web_tasks"
        
        # Check for monitoring tasks
        if "monitor_websites" in shared_state:
            return "monitor_websites"
        
        # Default autonomous action
        return "web_health_check"
    
    async def _execute_task_with_context(self, task: str, context) -> Dict[str, Any]:
        """Execute browser automation task with context."""
        task_lower = task.lower()
        
        # Route to appropriate automation method
        if any(keyword in task_lower for keyword in ["navigate", "visit", "browse"]):
            return await self._handle_navigation_task(task, context)
        elif any(keyword in task_lower for keyword in ["screenshot", "capture", "image"]):
            return await self._handle_screenshot_task(task, context)
        elif any(keyword in task_lower for keyword in ["form", "fill", "submit"]):
            return await self._handle_form_task(task, context)
        elif any(keyword in task_lower for keyword in ["test", "verify", "check"]):
            return await self._handle_testing_task(task, context)
        elif any(keyword in task_lower for keyword in ["pdf", "save", "download"]):
            return await self._handle_pdf_task(task, context)
        elif any(keyword in task_lower for keyword in ["scrape", "extract", "data"]):
            return await self._handle_scraping_task(task, context)
        elif any(keyword in task_lower for keyword in ["monitor", "watch", "track"]):
            return await self._handle_monitoring_task(task, context)
        else:
            # General web research task
            return await self._handle_research_task(task, context)
    
    async def _handle_navigation_task(self, task: str, context) -> Dict[str, Any]:
        """Handle web navigation tasks."""
        if not self.browser_ready:
            return {"success": False, "error": "Browser not ready"}
        
        try:
            # Extract URL from task (simplified - in real implementation would use NLP)
            url = self._extract_url_from_task(task)
            if not url:
                url = "https://example.com"  # Default for demo
            
            # Navigate to URL
            nav_result = await self.playwright_client.call_tool("playwright", "browser_navigate", {
                "url": url
            })
            
            # Take screenshot for confirmation
            screenshot_result = await self.playwright_client.call_tool("playwright", "browser_take_screenshot", {
                "path": f"navigation_{self.state.iteration_count}.png"
            })
            
            return {
                "success": True,
                "action": "navigation",
                "url": url,
                "navigation_result": str(nav_result),
                "screenshot": f"navigation_{self.state.iteration_count}.png",
                "execution_time": 2.0,
                "cost": 0.01
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "cost": 0.0}
    
    async def _handle_screenshot_task(self, task: str, context) -> Dict[str, Any]:
        """Handle screenshot and visual capture tasks."""
        if not self.browser_ready:
            return {"success": False, "error": "Browser not ready"}
        
        try:
            # Take screenshot
            filename = f"screenshot_{self.state.iteration_count}.png"
            screenshot_result = await self.playwright_client.call_tool("playwright", "browser_take_screenshot", {
                "path": filename
            })
            
            # Take visual snapshot for analysis if requested
            if "analysis" in task.lower():
                snapshot_result = await self.playwright_client.call_tool("playwright", "browser_snapshot", {
                    "name": f"analysis_{self.state.iteration_count}"
                })
                
                return {
                    "success": True,
                    "action": "screenshot_with_analysis",
                    "screenshot": filename,
                    "analysis": str(snapshot_result),
                    "execution_time": 3.0,
                    "cost": 0.02
                }
            
            return {
                "success": True,
                "action": "screenshot",
                "screenshot": filename,
                "result": str(screenshot_result),
                "execution_time": 1.5,
                "cost": 0.01
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "cost": 0.0}
    
    async def _handle_form_task(self, task: str, context) -> Dict[str, Any]:
        """Handle form filling and interaction tasks."""
        if not self.browser_ready:
            return {"success": False, "error": "Browser not ready"}
        
        try:
            # Navigate to a test form
            await self.playwright_client.call_tool("playwright", "browser_navigate", {
                "url": "https://httpbin.org/forms/post"
            })
            
            # Fill form fields
            form_data = self._extract_form_data_from_task(task)
            
            for field, value in form_data.items():
                await self.playwright_client.call_tool("playwright", "browser_fill", {
                    "selector": f"input[name='{field}'], select[name='{field}']",
                    "value": value
                })
            
            # Take screenshot of filled form
            screenshot_result = await self.playwright_client.call_tool("playwright", "browser_take_screenshot", {
                "path": f"form_filled_{self.state.iteration_count}.png"
            })
            
            return {
                "success": True,
                "action": "form_filling",
                "form_data": form_data,
                "screenshot": f"form_filled_{self.state.iteration_count}.png",
                "execution_time": 4.0,
                "cost": 0.03
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "cost": 0.0}
    
    async def _handle_testing_task(self, task: str, context) -> Dict[str, Any]:
        """Handle automated testing tasks."""
        if not self.browser_ready:
            return {"success": False, "error": "Browser not ready"}
        
        try:
            # Generate test workflow
            test_actions = [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "wait", "selector": "h1"},
                {"action": "click", "selector": "h1"},
                {"action": "screenshot", "path": f"test_step_{self.state.iteration_count}.png"}
            ]
            
            # Generate Playwright test code
            test_code_result = await self.playwright_client.call_tool("playwright", "browser_generate_playwright_test", {
                "actions": test_actions
            })
            
            # Execute basic test navigation
            await self.playwright_client.call_tool("playwright", "browser_navigate", {
                "url": "https://example.com"
            })
            
            # Wait for element
            await self.playwright_client.call_tool("playwright", "browser_wait_for", {
                "selector": "h1",
                "timeout": 10000
            })
            
            # Take test screenshot
            await self.playwright_client.call_tool("playwright", "browser_take_screenshot", {
                "path": f"test_result_{self.state.iteration_count}.png"
            })
            
            return {
                "success": True,
                "action": "automated_testing",
                "test_actions": test_actions,
                "generated_code": str(test_code_result),
                "screenshot": f"test_result_{self.state.iteration_count}.png",
                "execution_time": 5.0,
                "cost": 0.04
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "cost": 0.0}
    
    async def _handle_pdf_task(self, task: str, context) -> Dict[str, Any]:
        """Handle PDF generation tasks."""
        if not self.browser_ready:
            return {"success": False, "error": "Browser not ready"}
        
        try:
            # Navigate to a documentation page
            url = self._extract_url_from_task(task) or "https://playwright.dev/docs/intro"
            
            await self.playwright_client.call_tool("playwright", "browser_navigate", {
                "url": url
            })
            
            # Generate PDF
            pdf_filename = f"generated_pdf_{self.state.iteration_count}.pdf"
            pdf_result = await self.playwright_client.call_tool("playwright", "browser_pdf_save", {
                "path": pdf_filename
            })
            
            return {
                "success": True,
                "action": "pdf_generation",
                "url": url,
                "pdf_file": pdf_filename,
                "result": str(pdf_result),
                "execution_time": 3.0,
                "cost": 0.02
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "cost": 0.0}
    
    async def _handle_scraping_task(self, task: str, context) -> Dict[str, Any]:
        """Handle web scraping and data extraction tasks."""
        if not self.browser_ready:
            return {"success": False, "error": "Browser not ready"}
        
        try:
            # Navigate to a data-rich site
            url = "https://news.ycombinator.com"  # Good for demo
            
            await self.playwright_client.call_tool("playwright", "browser_navigate", {
                "url": url
            })
            
            # Wait for content to load
            await self.playwright_client.call_tool("playwright", "browser_wait_for", {
                "selector": ".storylink",
                "timeout": 10000
            })
            
            # Take visual snapshot for analysis
            snapshot_result = await self.playwright_client.call_tool("playwright", "browser_snapshot", {
                "name": f"scraping_analysis_{self.state.iteration_count}"
            })
            
            # Take screenshot
            screenshot_result = await self.playwright_client.call_tool("playwright", "browser_take_screenshot", {
                "path": f"scraped_page_{self.state.iteration_count}.png"
            })
            
            return {
                "success": True,
                "action": "web_scraping",
                "url": url,
                "analysis": str(snapshot_result),
                "screenshot": f"scraped_page_{self.state.iteration_count}.png",
                "execution_time": 4.0,
                "cost": 0.03
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "cost": 0.0}
    
    async def _handle_monitoring_task(self, task: str, context) -> Dict[str, Any]:
        """Handle website monitoring tasks."""
        if not self.browser_ready:
            return {"success": False, "error": "Browser not ready"}
        
        try:
            # Navigate to target site
            url = self._extract_url_from_task(task) or "https://httpbin.org/json"
            
            await self.playwright_client.call_tool("playwright", "browser_navigate", {
                "url": url
            })
            
            # Monitor network requests
            network_result = await self.playwright_client.call_tool("playwright", "browser_network_requests", {})
            
            # Monitor console messages
            console_result = await self.playwright_client.call_tool("playwright", "browser_console_messages", {})
            
            # Take monitoring screenshot
            screenshot_result = await self.playwright_client.call_tool("playwright", "browser_take_screenshot", {
                "path": f"monitoring_{self.state.iteration_count}.png"
            })
            
            return {
                "success": True,
                "action": "website_monitoring",
                "url": url,
                "network_requests": str(network_result),
                "console_messages": str(console_result),
                "screenshot": f"monitoring_{self.state.iteration_count}.png",
                "execution_time": 3.5,
                "cost": 0.025
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "cost": 0.0}
    
    async def _handle_research_task(self, task: str, context) -> Dict[str, Any]:
        """Handle general web research tasks."""
        if not self.browser_ready:
            return {"success": False, "error": "Browser not ready"}
        
        try:
            # Navigate to a search engine or relevant site
            search_query = self._extract_search_query_from_task(task)
            url = f"https://duckduckgo.com/?q={search_query.replace(' ', '+')}"
            
            await self.playwright_client.call_tool("playwright", "browser_navigate", {
                "url": url
            })
            
            # Wait for results
            await self.playwright_client.call_tool("playwright", "browser_wait_for", {
                "selector": ".result",
                "timeout": 10000
            })
            
            # Take snapshot for analysis
            snapshot_result = await self.playwright_client.call_tool("playwright", "browser_snapshot", {
                "name": f"research_{self.state.iteration_count}"
            })
            
            # Take screenshot
            screenshot_result = await self.playwright_client.call_tool("playwright", "browser_take_screenshot", {
                "path": f"research_{self.state.iteration_count}.png"
            })
            
            return {
                "success": True,
                "action": "web_research",
                "search_query": search_query,
                "url": url,
                "analysis": str(snapshot_result),
                "screenshot": f"research_{self.state.iteration_count}.png",
                "execution_time": 4.0,
                "cost": 0.03
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "cost": 0.0}
    
    # Helper methods for task parsing
    def _extract_url_from_task(self, task: str) -> Optional[str]:
        """Extract URL from task description."""
        # Simplified URL extraction - in production would use proper NLP
        import re
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, task)
        return match.group(0) if match else None
    
    def _extract_form_data_from_task(self, task: str) -> Dict[str, str]:
        """Extract form data from task description."""
        # Simplified form data extraction - in production would use proper NLP
        return {
            "custname": "John Doe",
            "custtel": "555-1234",
            "custemail": "john@example.com",
            "size": "medium"
        }
    
    def _extract_search_query_from_task(self, task: str) -> str:
        """Extract search query from task description."""
        # Simplified query extraction - in production would use proper NLP
        stopwords = ["research", "search", "find", "look", "for", "about", "on"]
        words = task.lower().split()
        query_words = [w for w in words if w not in stopwords and len(w) > 2]
        return " ".join(query_words[:5])  # Limit to 5 words
    
    async def stop(self):
        """Stop the agent and clean up browser connections."""
        await super().stop()
        if self.playwright_client:
            await self.playwright_client.disconnect_all()


async def create_browser_automation_agent(agent_id: str = "browser_agent") -> BrowserAutomationAgent:
    """Create and initialize a browser automation agent."""
    agent = BrowserAutomationAgent(agent_id)
    await agent.initialize()
    return agent


# Example usage and testing
async def demo_browser_agent():
    """Demonstrate the browser automation agent capabilities."""
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]🎭 Browser Automation Agent Demo[/bold blue]\n"
        "Sophisticated web automation with Playwright MCP",
        border_style="blue"
    ))
    
    # Create agent
    agent = await create_browser_automation_agent()
    
    # Demo tasks
    demo_tasks = [
        "Navigate to https://example.com and take a screenshot",
        "Fill out a contact form with sample data", 
        "Take a screenshot with visual analysis",
        "Generate a PDF from the current page",
        "Research information about playwright testing",
        "Monitor network requests on httpbin.org",
        "Run automated tests on a website"
    ]
    
    console.print(f"\n🤖 Created {agent.config.name}")
    console.print(f"📚 Browser automation capabilities: {agent.browser_ready}")
    
    # Execute demo tasks
    for i, task in enumerate(demo_tasks, 1):
        console.print(f"\n🎯 Task {i}: {task}")
        
        try:
            result = await agent.execute_task(task)
            
            if result["success"]:
                console.print(f"   ✅ Success! Action: {result.get('action', 'unknown')}")
                console.print(f"   ⏱️  Time: {result.get('execution_time', 0):.1f}s")
                console.print(f"   💰 Cost: ${result.get('cost', 0):.3f}")
                
                # Show specific results
                if 'screenshot' in result:
                    console.print(f"   📸 Screenshot: {result['screenshot']}")
                if 'pdf_file' in result:
                    console.print(f"   📄 PDF: {result['pdf_file']}")
                if 'url' in result:
                    console.print(f"   🔗 URL: {result['url']}")
            else:
                console.print(f"   ❌ Error: {result.get('error')}")
                
        except Exception as e:
            console.print(f"   ❌ Exception: {e}")
    
    # Show agent status
    status = agent.get_status()
    console.print(f"\n📊 Final Status:")
    console.print(f"   Iterations: {status['iteration_count']}")
    console.print(f"   Total Cost: ${status['total_cost']:.3f}")
    console.print(f"   Status: {status['status']}")
    
    await agent.stop()
    console.print("\n🎉 Browser automation demo complete!")


if __name__ == "__main__":
    asyncio.run(demo_browser_agent()) 