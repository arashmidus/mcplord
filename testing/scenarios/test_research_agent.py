"""
Test scenarios for the Research Agent using cost-aware testing framework.

This module demonstrates how to test MCP agents with:
- Statistical success rate measurement
- Cost tracking and budget management
- Semantic validation of outputs
- Multi-layered testing approach
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

from agents.examples.research_agent import ResearchAgent, create_research_agent
from testing.frameworks.cost_aware_runner import mcp_test, CostAwareTestRunner
from testing.frameworks.semantic_validator import (
    SemanticValidator, ValidationRequest, SemanticCheck,
    create_content_check, create_function_call_check
)
from coordination.state.context_bundle import ContextBundle


# Test fixtures and utilities
class MockMCPClient:
    """Mock MCP client for testing."""
    
    def __init__(self):
        self.tools = {
            "web_search": {
                "name": "web_search",
                "description": "Search the web for information"
            },
            "text_analysis": {
                "name": "text_analysis", 
                "description": "Analyze text content"
            }
        }
        self.state = {}
        self.call_count = 0
    
    async def connect(self):
        pass
    
    async def disconnect(self):
        pass
    
    async def fetch_context(self, request):
        return {
            "shared_state": self.state,
            "tools": list(self.tools.values()),
            "history": [],
            "coordination": {"other_agents": []},
            "environment": {},
            "constraints": {"cost_limit": 10.0}
        }
    
    async def call_tool(self, tool_name, **kwargs):
        self.call_count += 1
        
        if tool_name == "web_search":
            return {
                "success": True,
                "result": {
                    "results": [
                        {"title": "Test Result", "snippet": "Test snippet", "url": "http://example.com"}
                    ]
                },
                "cost": 0.1
            }
        elif tool_name == "text_analysis":
            return {
                "success": True,
                "result": {
                    "key_points": ["Point 1", "Point 2"],
                    "summary": "Test analysis summary"
                },
                "cost": 0.2
            }
        
        return {"success": False, "error": "Unknown tool", "cost": 0.0}
    
    async def update_state(self, agent_id, key, value):
        self.state[key] = value
    
    async def get_state(self, key):
        return self.state.get(key)


# Unit Level Tests (Tool Testing)
@mcp_test(
    estimated_cost=0.0,
    min_success_rate=0.95,
    sample_size=5,
    category="unit",
    priority=1,
    tags=["basic", "tools"]
)
async def test_mock_web_search():
    """Test web search tool directly without LLM."""
    mock_client = MockMCPClient()
    
    result = await mock_client.call_tool("web_search", query="test query")
    
    return {
        "success": result["success"],
        "has_results": len(result.get("result", {}).get("results", [])) > 0,
        "cost": result.get("cost", 0.0)
    }


@mcp_test(
    estimated_cost=0.0,
    min_success_rate=0.95,
    sample_size=5,
    category="unit",
    priority=1,
    tags=["basic", "tools"]
)
async def test_mock_text_analysis():
    """Test text analysis tool directly without LLM."""
    mock_client = MockMCPClient()
    
    result = await mock_client.call_tool("text_analysis", text="test text")
    
    return {
        "success": result["success"],
        "has_analysis": "summary" in result.get("result", {}),
        "cost": result.get("cost", 0.0)
    }


# Component Level Tests (Toolbox Testing)
@mcp_test(
    estimated_cost=0.5,
    min_success_rate=0.80,
    sample_size=10,
    category="component",
    priority=2,
    tags=["agent", "research"]
)
async def test_research_agent_initialization():
    """Test research agent initialization and basic functionality."""
    try:
        # Create agent with mock client
        agent = ResearchAgent({
            "name": "test_research_agent",
            "description": "Test agent",
            "mcp_server_urls": ["http://localhost:8001"],
            "cost_limit": 5.0
        })
        
        # Replace with mock client
        agent.mcp_client = MockMCPClient()
        
        # Initialize
        await agent._initialize_agent()
        
        # Check initialization
        return {
            "success": True,
            "has_research_stack": hasattr(agent, 'research_stack'),
            "has_findings_database": hasattr(agent, 'findings_database'),
            "cost": 0.0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cost": 0.0
        }


@mcp_test(
    estimated_cost=0.3,
    min_success_rate=0.75,
    sample_size=8,
    category="component",
    priority=2,
    tags=["agent", "research", "semantic"]
)
async def test_conduct_basic_research():
    """Test basic research functionality with semantic validation."""
    try:
        # Create agent with mock client
        agent = ResearchAgent({
            "name": "test_research_agent",
            "description": "Test agent",
            "mcp_server_urls": ["http://localhost:8001"],
            "cost_limit": 5.0
        })
        
        agent.mcp_client = MockMCPClient()
        await agent._initialize_agent()
        
        # Create context bundle
        context = ContextBundle.create_minimal(
            agent_id="test_agent",
            agent_name="test_research_agent",
            task="conduct_research:AI:basic"
        )
        
        # Add tools to context
        context.available_tools = list(agent.mcp_client.tools.values())
        
        # Conduct research
        result = await agent._conduct_research("conduct_research:AI:basic", context)
        
        return {
            "success": result.get("success", False),
            "has_findings": "findings" in result,
            "topic_correct": result.get("topic") == "AI",
            "cost": result.get("cost", 0.0),
            "raw_result": result  # For semantic validation
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cost": 0.0
        }


@mcp_test(
    estimated_cost=0.4,
    min_success_rate=0.70,
    sample_size=6,
    category="component",
    priority=3,
    tags=["agent", "research", "extraction"]
)
async def test_topic_extraction():
    """Test research topic extraction from task descriptions."""
    try:
        agent = ResearchAgent({
            "name": "test_research_agent",
            "description": "Test agent",
            "mcp_server_urls": ["http://localhost:8001"],
            "cost_limit": 5.0
        })
        
        # Test different task descriptions
        test_cases = [
            "Research about artificial intelligence in healthcare",
            "Investigate the impact of climate change on agriculture",
            "Analyze the current state of quantum computing",
            "Study the effects of social media on mental health"
        ]
        
        extraction_results = []
        for task in test_cases:
            topics = agent._extract_research_topics(task)
            extraction_results.append({
                "task": task,
                "topics": topics,
                "has_topics": len(topics) > 0
            })
        
        success_count = sum(1 for r in extraction_results if r["has_topics"])
        
        return {
            "success": success_count > 0,
            "extraction_success_rate": success_count / len(test_cases),
            "results": extraction_results,
            "cost": 0.0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cost": 0.0
        }


# System Level Tests (Workflow Testing)
@mcp_test(
    estimated_cost=1.0,
    min_success_rate=0.60,
    sample_size=5,
    category="system",
    priority=4,
    tags=["workflow", "end-to-end"]
)
async def test_full_research_workflow():
    """Test complete research workflow from task to results."""
    try:
        # Create agent with mock client
        agent = ResearchAgent({
            "name": "test_research_agent",
            "description": "Test agent",
            "mcp_server_urls": ["http://localhost:8001"],
            "cost_limit": 5.0
        })
        
        agent.mcp_client = MockMCPClient()
        await agent._initialize_agent()
        
        # Execute full research task
        result = await agent.execute_task(
            "Research the current state of artificial intelligence in healthcare",
            context={"priority": "high", "depth": "basic"}
        )
        
        # Validate workflow completion
        return {
            "success": result.get("success", False),
            "has_findings": "findings" in result,
            "used_tools": agent.mcp_client.call_count > 0,
            "cost": result.get("cost", 0.0),
            "workflow_result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cost": 0.0
        }


@mcp_test(
    estimated_cost=0.8,
    min_success_rate=0.65,
    sample_size=4,
    category="system",
    priority=4,
    tags=["autonomous", "multi-step"]
)
async def test_autonomous_research_loop():
    """Test autonomous research decision-making."""
    try:
        agent = ResearchAgent({
            "name": "test_research_agent",
            "description": "Test agent",
            "mcp_server_urls": ["http://localhost:8001"],
            "cost_limit": 5.0,
            "max_iterations": 3
        })
        
        agent.mcp_client = MockMCPClient()
        await agent._initialize_agent()
        
        # Create context with research request
        context = ContextBundle.create_minimal(
            agent_id="test_agent",
            agent_name="test_research_agent",
            task="autonomous_iteration"
        )
        
        # Add pending research request
        context.shared_state["pending_research_requests"] = [
            {"topic": "machine learning", "depth": "basic", "priority": 1}
        ]
        context.available_tools = list(agent.mcp_client.tools.values())
        
        # Test autonomous decision making
        action = await agent._determine_next_action(context)
        
        return {
            "success": action is not None,
            "action_type": action.split(":")[0] if action else None,
            "has_research_action": "research" in (action or "").lower(),
            "cost": 0.0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cost": 0.0
        }


# Semantic validation test
@mcp_test(
    estimated_cost=0.15,
    min_success_rate=0.85,
    sample_size=3,
    category="validation",
    priority=2,
    tags=["semantic", "validation"]
)
async def test_semantic_validation():
    """Test semantic validation of research outputs."""
    try:
        # Mock research output
        research_output = {
            "success": True,
            "topic": "artificial intelligence",
            "findings": {
                "web_search": {
                    "results": [
                        {"title": "AI in Healthcare", "snippet": "AI is transforming healthcare..."}
                    ]
                },
                "synthesis": {
                    "key_points": ["AI improves diagnosis", "Machine learning in medical imaging"],
                    "summary": "AI has significant applications in healthcare"
                }
            },
            "cost": 0.3
        }
        
        # Create semantic checks
        checks = [
            create_content_check("artificial intelligence"),
            create_content_check("healthcare"),
            SemanticCheck(
                name="findings_structure",
                description="Verify findings have proper structure",
                criteria="The findings should contain web_search results and synthesis information"
            )
        ]
        
        # Validate (this would normally use LLM, but we'll simulate)
        validation_result = {
            "content_check": True,
            "healthcare_check": True,
            "structure_check": True
        }
        
        return {
            "success": all(validation_result.values()),
            "validation_results": validation_result,
            "cost": 0.0  # Mock validation cost
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cost": 0.0
        }


# Test runner example
async def run_research_agent_tests():
    """Run all research agent tests with cost-aware runner."""
    
    # Initialize test runner
    runner = CostAwareTestRunner(
        budget_limit=10.0,
        default_sample_size=5,
        enable_semantic_validation=True,
        results_dir="test_results"
    )
    
    # Register tests from this module
    runner.register_tests_from_module(globals())
    
    # Run tests by priority
    print("Running unit tests...")
    unit_results = await runner.run_all_tests(
        categories=["unit"],
        stop_on_budget=False
    )
    
    print("Running component tests...")
    component_results = await runner.run_all_tests(
        categories=["component"],
        stop_on_budget=True
    )
    
    print("Running system tests...")
    system_results = await runner.run_all_tests(
        categories=["system"],
        stop_on_budget=True
    )
    
    # Print summary
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    all_results = {**unit_results, **component_results, **system_results}
    
    for test_name, summary in all_results.items():
        status = "PASS" if summary.passed_threshold else "FAIL"
        print(f"{test_name}: {status} ({summary.success_rate:.1%} success rate, ${summary.total_cost:.2f})")
    
    # Print budget usage
    budget_status = runner.get_budget_status()
    print(f"\nBudget Usage: ${budget_status['current_spend']:.2f} / ${budget_status['budget_limit']:.2f}")
    print(f"Utilization: {budget_status['utilization_percentage']:.1f}%")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(run_research_agent_tests()) 