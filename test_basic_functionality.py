#!/usr/bin/env python3
"""
Basic Functionality Test

This script tests that all the core components of the MCP scaffolding work correctly
without needing to start full servers or make external API calls.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = str(Path(__file__).parent.absolute())
sys.path.insert(0, current_dir)
os.environ['PYTHONPATH'] = f"{current_dir}:{os.environ.get('PYTHONPATH', '')}"

async def test_context_bundle():
    """Test the ContextBundle functionality."""
    print("🧪 Testing ContextBundle...")
    
    from coordination.state.context_bundle import ContextBundle
    
    # Test creating a minimal context bundle
    bundle = ContextBundle.create_minimal(
        agent_id="test_agent",
        agent_name="test_agent",
        task="test task"
    )
    
    assert bundle.get_agent_id() == "test_agent"
    assert bundle.get_task() == "test task"
    
    # Test adding and getting values
    bundle.shared_state["test_key"] = "test_value"
    assert bundle.get_shared_value("test_key") == "test_value"
    
    print("✅ ContextBundle working correctly")
    return True

async def test_agent_creation():
    """Test creating an agent instance."""
    print("🧪 Testing Agent Creation...")
    
    from agents.base.agent import AgentConfig
    from agents.examples.research_agent import ResearchAgent
    
    # Create agent config
    config = AgentConfig(
        name="test_agent",
        description="Test agent",
        mcp_server_urls=["http://localhost:8001"],
        cost_limit=5.0
    )
    
    # Create agent (don't initialize to avoid MCP connections)
    agent = ResearchAgent(config)
    
    assert agent.config.name == "test_agent"
    assert agent.state.status == "idle"
    
    print("✅ Agent creation working correctly")
    return True

def test_testing_framework():
    """Test the testing framework components."""
    print("🧪 Testing Framework Components...")
    
    from testing.frameworks.cost_aware_runner import TestConfig, TestRun, TestSummary
    from testing.frameworks.semantic_validator import SemanticCheck
    
    # Test TestConfig
    config = TestConfig(
        name="test",
        description="test",
        test_function=lambda: True,
        estimated_cost=0.1
    )
    
    assert config.name == "test"
    assert config.estimated_cost == 0.1
    
    # Test TestRun
    run = TestRun(
        test_name="test",
        success=True,
        execution_time=1.0,
        cost=0.1
    )
    
    assert run.success == True
    assert run.cost == 0.1
    
    # Test SemanticCheck
    check = SemanticCheck(
        name="test_check",
        description="test",
        criteria="test criteria"
    )
    
    assert check.name == "test_check"
    
    print("✅ Testing framework components working correctly")
    return True

def test_context_server_creation():
    """Test creating a context server instance."""
    print("🧪 Testing Context Server Creation...")
    
    from mcp.servers.context_server import ContextServer
    
    # Create server instance (don't start async tasks)
    server = ContextServer()
    
    assert hasattr(server, 'shared_state')
    assert hasattr(server, 'agent_registry')
    assert isinstance(server.shared_state, dict)
    
    print("✅ Context server creation working correctly")
    return True

def test_mcp_client_creation():
    """Test creating an MCP client."""
    print("🧪 Testing MCP Client Creation...")
    
    from mcp.client.mcp_client import MCPClient, MCPServerConfig
    
    # Create client with mock servers
    client = MCPClient(["http://localhost:8001"])
    
    assert len(client.server_configs) == 1
    assert client.server_configs[0].url == "http://localhost:8001"
    
    print("✅ MCP client creation working correctly")
    return True

async def main():
    """Run all tests."""
    print("🚀 Testing MCP Agent Scaffolding Core Functionality")
    print("=" * 60)
    
    tests = [
        test_context_bundle,
        test_agent_creation,
        test_testing_framework,
        test_context_server_creation,
        test_mcp_client_creation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All core functionality working correctly!")
        print("\n✅ Your MCP Agent Scaffolding is ready to use!")
        print("\nNext steps:")
        print("1. Install missing dependencies if needed: pip install -r requirements.txt")
        print("2. Run the demo: python scripts/run_demo.py")
        print("3. Start building your own agents!")
        
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 