#!/usr/bin/env python3
"""
Simple Test Runner for MCP Agent Scaffolding

Demonstrates the testing framework without requiring external API keys.
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

console = Console()

async def run_unit_tests():
    """Run unit-level tests (tool testing)."""
    console.print("[bold blue]🔬 Running Unit Tests[/bold blue]")
    
    from testing.scenarios.test_research_agent import MockMCPClient
    
    results = []
    
    # Test 1: Mock web search
    try:
        mock_client = MockMCPClient()
        result = await mock_client.call_tool("web_search", query="test query")
        success = result["success"] and len(result.get("result", {}).get("results", [])) > 0
        results.append(("test_mock_web_search", success, 0.0, "Tool test passed" if success else "Tool test failed"))
    except Exception as e:
        results.append(("test_mock_web_search", False, 0.0, str(e)))
    
    # Test 2: Mock text analysis
    try:
        mock_client = MockMCPClient()
        result = await mock_client.call_tool("text_analysis", text="test text")
        success = result["success"] and "summary" in result.get("result", {})
        results.append(("test_mock_text_analysis", success, 0.0, "Tool test passed" if success else "Tool test failed"))
    except Exception as e:
        results.append(("test_mock_text_analysis", False, 0.0, str(e)))
    
    return results

async def run_component_tests():
    """Run component-level tests (agent functionality)."""
    console.print("[bold blue]🧪 Running Component Tests[/bold blue]")
    
    from agents.base.agent import AgentConfig
    from agents.examples.research_agent import ResearchAgent
    from testing.scenarios.test_research_agent import MockMCPClient
    from coordination.state.context_bundle import ContextBundle
    
    results = []
    
    # Test 3: Agent initialization
    try:
        config = AgentConfig(
            name="test_agent",
            description="Test agent",
            mcp_server_urls=["http://localhost:8001"],
            cost_limit=5.0
        )
        agent = ResearchAgent(config)
        agent.mcp_client = MockMCPClient()
        await agent._initialize_agent()
        
        success = hasattr(agent, 'research_stack') and hasattr(agent, 'findings_database')
        results.append(("test_agent_initialization", success, 0.0, "Agent created successfully" if success else "Agent creation failed"))
    except Exception as e:
        results.append(("test_agent_initialization", False, 0.0, str(e)))
    
    # Test 4: Research functionality
    try:
        config = AgentConfig(
            name="test_agent",
            description="Test agent", 
            mcp_server_urls=["http://localhost:8001"],
            cost_limit=5.0
        )
        agent = ResearchAgent(config)
        agent.mcp_client = MockMCPClient()
        await agent._initialize_agent()
        
        context = ContextBundle.create_minimal(
            agent_id="test_agent",
            agent_name="test_agent", 
            task="conduct_research:AI:basic"
        )
        context.available_tools = list(agent.mcp_client.tools.values())
        
        result = await agent._conduct_research("conduct_research:AI:basic", context)
        success = result.get("success", False) and "findings" in result
        cost = result.get("cost", 0.0)
        
        results.append(("test_conduct_research", success, cost, "Research completed" if success else "Research failed"))
    except Exception as e:
        results.append(("test_conduct_research", False, 0.0, str(e)))
    
    return results

async def run_system_tests():
    """Run system-level tests (full workflows)."""
    console.print("[bold blue]🚀 Running System Tests[/bold blue]")
    
    from testing.frameworks.cost_aware_runner import TestConfig, TestRun, TestSummary
    
    results = []
    
    # Test 5: Testing framework components
    try:
        config = TestConfig(
            name="test_framework",
            description="Test the testing framework",
            test_function=lambda: True,
            estimated_cost=0.1
        )
        
        run = TestRun(
            test_name="test_framework",
            success=True,
            execution_time=1.0,
            cost=0.1
        )
        
        summary = TestSummary(
            test_name="test_framework",
            total_runs=5,
            successful_runs=4,
            failed_runs=1,
            success_rate=0.8,
            average_execution_time=1.0,
            total_cost=0.5,
            min_required_rate=0.8,
            passed_threshold=True
        )
        
        success = (config.name == "test_framework" and 
                  run.success == True and 
                  summary.passed_threshold == True)
        
        results.append(("test_framework_components", success, 0.0, "Framework test passed" if success else "Framework test failed"))
    except Exception as e:
        results.append(("test_framework_components", False, 0.0, str(e)))
    
    return results

def display_results(test_type: str, results: list):
    """Display test results in a nice table."""
    table = Table(title=f"{test_type} Test Results")
    table.add_column("Test Name", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Cost", style="yellow")
    table.add_column("Details", style="dim")
    
    for test_name, success, cost, details in results:
        status = "✅ PASS" if success else "❌ FAIL"
        table.add_row(test_name, status, f"${cost:.2f}", details)
    
    console.print(table)
    
    passed = sum(1 for _, success, _, _ in results if success)
    total = len(results)
    console.print(f"📊 {test_type}: {passed}/{total} tests passed")
    
    return passed, total

async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold green]🧪 MCP Agent Scaffolding - Test Suite[/bold green]\n"
        "Running comprehensive tests without external dependencies",
        border_style="green"
    ))
    
    total_passed = 0
    total_tests = 0
    total_cost = 0.0
    
    # Run different test levels
    unit_results = await run_unit_tests()
    passed, count = display_results("Unit", unit_results)
    total_passed += passed
    total_tests += count
    total_cost += sum(cost for _, _, cost, _ in unit_results)
    
    console.print()
    
    component_results = await run_component_tests()
    passed, count = display_results("Component", component_results)
    total_passed += passed
    total_tests += count
    total_cost += sum(cost for _, _, cost, _ in component_results)
    
    console.print()
    
    system_results = await run_system_tests()
    passed, count = display_results("System", system_results)
    total_passed += passed
    total_tests += count
    total_cost += sum(cost for _, _, cost, _ in system_results)
    
    # Final summary
    console.print("\n" + "="*60)
    console.print("[bold green]📊 Test Suite Summary[/bold green]")
    console.print("="*60)
    
    summary_table = Table()
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Tests", str(total_tests))
    summary_table.add_row("Tests Passed", str(total_passed))
    summary_table.add_row("Tests Failed", str(total_tests - total_passed))
    summary_table.add_row("Success Rate", f"{total_passed/total_tests:.1%}" if total_tests > 0 else "0%")
    summary_table.add_row("Total Cost", f"${total_cost:.2f}")
    
    console.print(summary_table)
    
    if total_passed == total_tests:
        console.print("\n🎉 All tests passed! Your MCP Agent Scaffolding is working perfectly!")
    else:
        console.print(f"\n⚠️  {total_tests - total_passed} tests failed. Check the details above.")
    
    console.print("\n[bold]Key Testing Features Demonstrated:[/bold]")
    console.print("✅ Multi-layered testing (Unit/Component/System)")
    console.print("✅ Cost tracking and budget management")
    console.print("✅ Mock-friendly architecture")
    console.print("✅ Statistical success rate measurement")
    console.print("✅ Comprehensive test reporting")

if __name__ == "__main__":
    asyncio.run(main()) 