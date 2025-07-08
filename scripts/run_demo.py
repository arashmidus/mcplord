"""
MCP Agent Scaffolding Demo

This script demonstrates the complete workflow of the MCP agent scaffolding:
1. Initialize configuration
2. Start MCP servers
3. Create and run agents
4. Execute tests with cost tracking
5. Monitor performance
"""

import asyncio
import logging
import time
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.layout import Layout

from agents.examples.research_agent import create_research_agent
from testing.frameworks.cost_aware_runner import CostAwareTestRunner
from testing.scenarios.test_research_agent import run_research_agent_tests
from mcp.servers.context_server import ContextServer
from coordination.state.context_bundle import ContextBundle

console = Console()


async def start_demo_mcp_server():
    """Start a demo MCP server for testing."""
    server = ContextServer()
    
    # Register some demo tools
    await server.register_tool({
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Maximum results", "default": 5}
        }
    })
    
    await server.register_tool({
        "name": "text_analysis",
        "description": "Analyze text content",
        "parameters": {
            "text": {"type": "string", "description": "Text to analyze"},
            "analysis_type": {"type": "string", "description": "Type of analysis"}
        }
    })
    
    return server


async def demo_agent_lifecycle():
    """Demonstrate agent lifecycle and basic functionality."""
    console.print("\n[bold blue]🤖 Agent Lifecycle Demo[/bold blue]")
    
    # Create a research agent
    agent = await create_research_agent([
        "http://localhost:8001"  # Demo server URL
    ])
    
    try:
        # Execute a research task
        console.print("📋 Executing research task...")
        result = await agent.execute_task(
            "Research the benefits of artificial intelligence in education",
            context={"priority": "medium", "depth": "basic"}
        )
        
        # Display results
        console.print("✅ Task completed!")
        console.print(f"Success: {result.get('success', False)}")
        console.print(f"Cost: ${result.get('cost', 0.0):.2f}")
        
        if result.get('success'):
            console.print("📊 Research findings summary available")
        
        # Get agent status
        status = agent.get_status()
        console.print(f"Agent status: {status['status']}")
        console.print(f"Total iterations: {status['iteration_count']}")
        console.print(f"Total cost: ${status['total_cost']:.2f}")
        
    finally:
        await agent.stop()
    
    return True


async def demo_testing_framework():
    """Demonstrate cost-aware testing framework."""
    console.print("\n[bold blue]🧪 Testing Framework Demo[/bold blue]")
    
    # Run a subset of tests with cost tracking
    runner = CostAwareTestRunner(
        budget_limit=5.0,
        default_sample_size=3,
        enable_semantic_validation=False,  # Disable for demo
        results_dir="demo_test_results"
    )
    
    # Import and register test module
    import testing.scenarios.test_research_agent as test_module
    runner.register_tests_from_module(test_module)
    
    # Run unit tests
    console.print("🔬 Running unit tests...")
    unit_results = await runner.run_all_tests(
        categories=["unit"],
        stop_on_budget=True
    )
    
    # Display results
    console.print("\n📊 Test Results Summary:")
    for test_name, summary in unit_results.items():
        status = "✅ PASS" if summary.passed_threshold else "❌ FAIL"
        console.print(f"{status} {test_name}: {summary.success_rate:.1%} success rate")
    
    # Show budget usage
    budget_status = runner.get_budget_status()
    console.print(f"\n💰 Budget Usage: ${budget_status['current_spend']:.2f} / ${budget_status['budget_limit']:.2f}")
    
    return unit_results


def create_monitoring_dashboard(agent_metrics, test_metrics):
    """Create a live monitoring dashboard."""
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="agents", ratio=1),
        Layout(name="tests", ratio=1)
    )
    
    # Header
    layout["header"].update(
        Panel("🚀 MCP Agent Scaffolding - Live Dashboard", style="bold blue")
    )
    
    # Agent metrics table
    agent_table = Table(title="Agent Metrics")
    agent_table.add_column("Metric", style="cyan")
    agent_table.add_column("Value", style="green")
    
    if agent_metrics:
        agent_table.add_row("Total Tasks", str(agent_metrics.get("task_count", 0)))
        agent_table.add_row("Success Rate", f"{agent_metrics.get('success_rate', 0):.1%}")
        agent_table.add_row("Avg Execution Time", f"{agent_metrics.get('average_execution_time', 0):.2f}s")
    
    layout["agents"].update(Panel(agent_table))
    
    # Test metrics table
    test_table = Table(title="Test Metrics")
    test_table.add_column("Metric", style="cyan")
    test_table.add_column("Value", style="green")
    
    if test_metrics:
        test_table.add_row("Total Tests", str(test_metrics.get("total_tests", 0)))
        test_table.add_row("Pass Rate", f"{test_metrics.get('pass_rate', 0):.1%}")
        test_table.add_row("Total Cost", f"${test_metrics.get('total_cost', 0):.2f}")
    
    layout["tests"].update(Panel(test_table))
    
    # Footer
    layout["footer"].update(
        Panel("Press Ctrl+C to exit", style="dim")
    )
    
    return layout


async def demo_monitoring():
    """Demonstrate monitoring and observability."""
    console.print("\n[bold blue]📊 Monitoring Demo[/bold blue]")
    
    # Simulate some metrics
    agent_metrics = {
        "task_count": 5,
        "success_rate": 0.8,
        "average_execution_time": 2.3
    }
    
    test_metrics = {
        "total_tests": 8,
        "pass_rate": 0.875,
        "total_cost": 1.25
    }
    
    # Show dashboard for a few seconds
    dashboard = create_monitoring_dashboard(agent_metrics, test_metrics)
    
    with Live(dashboard, refresh_per_second=1) as live:
        for i in range(5):
            await asyncio.sleep(1)
            # Update some metrics to show live updates
            agent_metrics["task_count"] += 1
            test_metrics["total_cost"] += 0.1
            
            dashboard = create_monitoring_dashboard(agent_metrics, test_metrics)
            live.update(dashboard)
    
    console.print("📈 Monitoring dashboard demo completed")


async def main():
    """Run the complete demo."""
    console.print(Panel.fit(
        "[bold green]🚀 MCP Agent Scaffolding Demo[/bold green]\n"
        "Demonstrating multi-agent development, testing, and monitoring",
        border_style="green"
    ))
    
    try:
        # Step 1: Start demo MCP server
        console.print("\n[bold]Step 1: Starting MCP Server[/bold]")
        server = await start_demo_mcp_server()
        console.print("✅ Demo MCP server started")
        
        # Step 2: Demo agent lifecycle
        console.print("\n[bold]Step 2: Agent Lifecycle[/bold]")
        await demo_agent_lifecycle()
        
        # Step 3: Demo testing framework
        console.print("\n[bold]Step 3: Testing Framework[/bold]")
        test_results = await demo_testing_framework()
        
        # Step 4: Demo monitoring
        console.print("\n[bold]Step 4: Monitoring Dashboard[/bold]")
        await demo_monitoring()
        
        # Summary
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 Demo Complete![/bold green]")
        console.print("="*60)
        
        console.print("\n[bold]What you've seen:[/bold]")
        console.print("✅ Stateless agent architecture with MCP integration")
        console.print("✅ Context bundle pattern for rich agent context")
        console.print("✅ Cost-aware testing with statistical validation")
        console.print("✅ Real-time monitoring and observability")
        console.print("✅ Production-ready scaffolding structure")
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print("• Customize agents for your specific use cases")
        console.print("• Add more MCP servers and tools")
        console.print("• Expand test coverage with semantic validation")
        console.print("• Deploy with Docker and monitoring stack")
        console.print("• Scale with Kubernetes for production")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Demo error: {e}[/red]")
        logging.exception("Demo failed")
    
    console.print("\n[dim]Thank you for trying MCP Agent Scaffolding![/dim]")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demo
    asyncio.run(main()) 