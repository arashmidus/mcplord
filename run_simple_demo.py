#!/usr/bin/env python3
"""
Simple MCP Agent Scaffolding Demo

This demo runs without external servers, using mock clients to show the functionality.
"""

import asyncio
import sys
import os
from pathlib import Path

# Setup path
current_dir = str(Path(__file__).parent.absolute())
sys.path.insert(0, current_dir)
os.environ['PYTHONPATH'] = f"{current_dir}:{os.environ.get('PYTHONPATH', '')}"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def demo_context_bundle():
    """Demo the context bundle system."""
    console.print("[bold blue]📦 Context Bundle Demo[/bold blue]")
    
    from coordination.state.context_bundle import ContextBundle
    
    # Create a context bundle
    bundle = ContextBundle.create_minimal(
        agent_id="demo_agent",
        agent_name="demo_research_agent", 
        task="Research artificial intelligence applications"
    )
    
    # Add some mock data
    bundle.shared_state["current_research_topic"] = "AI in healthcare"
    bundle.available_tools = [
        {"name": "web_search", "description": "Search the web"},
        {"name": "text_analysis", "description": "Analyze text content"}
    ]
    bundle.coordination_info["other_agents"] = [
        {"id": "agent_2", "name": "analysis_agent", "status": "idle"}
    ]
    
    # Show the bundle
    table = Table(title="Context Bundle Contents")
    table.add_column("Component", style="cyan")
    table.add_column("Content", style="green")
    
    table.add_row("Agent ID", bundle.get_agent_id())
    table.add_row("Task", bundle.get_task())
    table.add_row("Available Tools", f"{len(bundle.available_tools)} tools")
    table.add_row("Shared State Keys", f"{len(bundle.shared_state)} items")
    table.add_row("Other Agents", f"{len(bundle.get_other_agents())} agents")
    
    console.print(table)
    console.print("✅ Context bundle created and populated!")

async def demo_agent_with_mock():
    """Demo agent functionality with mock MCP client."""
    console.print("\n[bold blue]🤖 Agent with Mock Client Demo[/bold blue]")
    
    from agents.base.agent import AgentConfig
    from agents.examples.research_agent import ResearchAgent
    from testing.scenarios.test_research_agent import MockMCPClient
    from coordination.state.context_bundle import ContextBundle
    
    # Create agent
    config = AgentConfig(
        name="demo_research_agent",
        description="Demo research agent",
        mcp_server_urls=["http://localhost:8001"],
        cost_limit=5.0,
        max_iterations=3
    )
    
    agent = ResearchAgent(config)
    
    # Replace with mock client (no real connections needed)
    agent.mcp_client = MockMCPClient()
    
    # Initialize agent
    await agent._initialize_agent()
    
    # Create context
    context = ContextBundle.create_minimal(
        agent_id=agent.agent_id,
        agent_name=agent.config.name,
        task="Research AI applications in education"
    )
    context.available_tools = list(agent.mcp_client.tools.values())
    
    # Execute a research task
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Executing research task...", total=None)
        
        result = await agent._conduct_research("conduct_research:AI applications:basic", context)
        
        progress.update(task, description="Research completed!")
    
    # Show results
    table = Table(title="Research Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Success", "✅ Yes" if result.get("success") else "❌ No")
    table.add_row("Topic", result.get("topic", "Unknown"))
    table.add_row("Cost", f"${result.get('cost', 0.0):.2f}")
    table.add_row("Sources Found", str(result.get("sources_count", 0)))
    table.add_row("Cached Result", "Yes" if result.get("cached") else "No")
    
    console.print(table)
    
    # Show agent status
    status = agent.get_status()
    console.print(f"\n📊 Agent Status: {status['status']}")
    console.print(f"💰 Total Cost: ${status['total_cost']:.2f}")

async def demo_testing_framework():
    """Demo the cost-aware testing framework."""
    console.print("\n[bold blue]🧪 Testing Framework Demo[/bold blue]")
    
    from testing.frameworks.cost_aware_runner import TestConfig, TestRun, TestSummary
    
    # Simulate running tests
    test_results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        tests = [
            "test_mock_web_search",
            "test_mock_text_analysis", 
            "test_research_agent_initialization",
            "test_conduct_basic_research"
        ]
        
        for test_name in tests:
            task = progress.add_task(f"Running {test_name}...", total=None)
            await asyncio.sleep(0.5)  # Simulate test execution
            
            # Simulate test results
            import random
            success_rate = random.uniform(0.7, 1.0)
            cost = random.uniform(0.05, 0.25)
            
            summary = TestSummary(
                test_name=test_name,
                total_runs=5,
                successful_runs=int(5 * success_rate),
                failed_runs=5 - int(5 * success_rate),
                success_rate=success_rate,
                average_execution_time=random.uniform(0.5, 2.0),
                total_cost=cost,
                min_required_rate=0.8,
                passed_threshold=success_rate >= 0.8
            )
            
            test_results.append(summary)
            progress.update(task, description=f"✅ {test_name} completed")
    
    # Show test results
    table = Table(title="Test Results Summary")
    table.add_column("Test Name", style="cyan")
    table.add_column("Success Rate", style="green")
    table.add_column("Status", style="bold")
    table.add_column("Cost", style="yellow")
    
    total_cost = 0.0
    passed_tests = 0
    
    for summary in test_results:
        status = "✅ PASS" if summary.passed_threshold else "❌ FAIL"
        table.add_row(
            summary.test_name,
            f"{summary.success_rate:.1%}",
            status,
            f"${summary.total_cost:.2f}"
        )
        total_cost += summary.total_cost
        if summary.passed_threshold:
            passed_tests += 1
    
    console.print(table)
    console.print(f"\n📊 Summary: {passed_tests}/{len(test_results)} tests passed")
    console.print(f"💰 Total cost: ${total_cost:.2f}")

async def demo_monitoring():
    """Demo monitoring capabilities."""
    console.print("\n[bold blue]📊 Monitoring Demo[/bold blue]")
    
    from monitoring.metrics.agent_metrics import AgentMetrics
    from monitoring.metrics.testing_metrics import TestingMetrics
    
    # Create metrics instances
    agent_metrics = AgentMetrics("demo_agent", "research_agent")
    test_metrics = TestingMetrics()
    
    # Simulate some activity
    agent_metrics.record_task_execution("research_task_1", 2.3, True)
    agent_metrics.record_task_execution("research_task_2", 1.8, True)
    agent_metrics.record_task_execution("research_task_3", 3.1, False)
    agent_metrics.record_tool_call("web_search", 0.5)
    agent_metrics.record_tool_call("text_analysis", 1.2)
    
    # Get metrics
    metrics = agent_metrics.get_metrics()
    
    # Display metrics
    table = Table(title="Agent Performance Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Tasks", str(metrics["task_count"]))
    table.add_row("Success Rate", f"{metrics['success_rate']:.1%}")
    table.add_row("Avg Execution Time", f"{metrics['average_execution_time']:.2f}s")
    table.add_row("Tool Calls", str(len(metrics["tool_calls"])))
    
    console.print(table)

async def main():
    """Run the simple demo."""
    console.print(Panel.fit(
        "[bold green]🚀 MCP Agent Scaffolding - Simple Demo[/bold green]\n"
        "Demonstrating core functionality without external dependencies",
        border_style="green"
    ))
    
    try:
        await demo_context_bundle()
        await demo_agent_with_mock()
        await demo_testing_framework()
        await demo_monitoring()
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 Demo Complete![/bold green]")
        console.print("="*60)
        
        console.print("\n[bold]What you've seen:[/bold]")
        console.print("✅ Context Bundle system for rich agent context")
        console.print("✅ Stateless agent architecture with MCP integration")
        console.print("✅ Cost-aware testing with statistical validation")
        console.print("✅ Real-time performance monitoring")
        console.print("✅ Mock-friendly design for testing")
        
        console.print("\n[bold]Ready for production use:[/bold]")
        console.print("• Add real MCP servers for live data")
        console.print("• Connect to external APIs and databases")
        console.print("• Deploy with Docker and Kubernetes")
        console.print("• Scale to multiple agent workflows")
        
    except Exception as e:
        console.print(f"\n[red]Demo error: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    console.print("\n[dim]Thank you for trying MCP Agent Scaffolding![/dim]")

if __name__ == "__main__":
    asyncio.run(main()) 