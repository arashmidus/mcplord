#!/usr/bin/env python3
"""
Examples of how to interact with the MCP Agent System programmatically.

This script shows various ways to use the system in your own code.
"""

import asyncio
import sys
from pathlib import Path

# Setup path
current_dir = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, current_dir)

from mcp.client.real_mcp_client import RealMCPClient, MCPServerConfigs
from run_with_real_mcp_servers import RealMCPAgentSystem

async def example_1_direct_mcp_client():
    """Example 1: Direct MCP client usage"""
    print("🔌 Example 1: Direct MCP Client Usage")
    
    client = RealMCPClient()
    
    try:
        # Connect to servers
        await client.connect_to_server("memory", *MCPServerConfigs.memory())
        await client.connect_to_server("time", *MCPServerConfigs.time())
        
        # List available tools
        tools = await client.list_tools()
        print(f"📚 Available tools: {sum(len(t) for t in tools.values())}")
        
        # Call specific tools
        result = await client.call_tool("memory", "echo", {"message": "Hello from code!"})
        print(f"✅ Tool result: {result}")
        
        # Get resources
        resources = await client.list_resources()
        print(f"📄 Available resources: {sum(len(r) for r in resources.values())}")
        
    finally:
        await client.disconnect_all()

async def example_2_agent_creation():
    """Example 2: Creating and using agents"""
    print("\n🤖 Example 2: Agent Creation and Usage")
    
    system = RealMCPAgentSystem()
    
    try:
        # Load config and connect
        system.load_config()
        connected_servers = await system.connect_enabled_servers()
        
        if connected_servers:
            # Create a custom agent
            agent = await system.create_enhanced_agent("my_agent", connected_servers)
            
            # Execute various tasks
            tasks = [
                "What is the current time?",
                "Remember that I'm learning about MCP agents",
                "Help me fetch some web content",
                "Add 25 + 17 for me"
            ]
            
            for task in tasks:
                print(f"\n📋 Task: {task}")
                result = await agent.execute_task(task)
                
                if result["success"]:
                    print(f"   ✅ Success! Time: {result['execution_time']:.2f}s")
                    for res in result.get("results", []):
                        print(f"   • {res}")
                else:
                    print(f"   ❌ Error: {result.get('error')}")
        
    finally:
        await system.cleanup()

async def example_3_custom_workflows():
    """Example 3: Building custom workflows"""
    print("\n🔧 Example 3: Custom Workflows")
    
    client = RealMCPClient()
    
    try:
        # Connect to multiple servers
        await client.connect_to_server("memory", *MCPServerConfigs.memory())
        await client.connect_to_server("fetch", *MCPServerConfigs.fetch())
        
        # Custom workflow: Research and remember
        research_topic = "MCP agent architectures"
        
        print(f"📚 Researching: {research_topic}")
        
        # Step 1: Simulate research (in real version, would use web search)
        research_results = "MCP agents use stateless patterns with context fetching"
        
        # Step 2: Store in memory
        memory_result = await client.call_tool("memory", "echo", {
            "message": f"Research on {research_topic}: {research_results}"
        })
        print(f"🧠 Stored in memory: {memory_result}")
        
        # Step 3: Retrieve related information
        related_info = await client.call_tool("memory", "echo", {
            "message": f"What do we know about {research_topic}?"
        })
        print(f"🔍 Retrieved: {related_info}")
        
    finally:
        await client.disconnect_all()

async def example_4_multi_server_coordination():
    """Example 4: Coordinating multiple servers"""
    print("\n🌐 Example 4: Multi-Server Coordination")
    
    client = RealMCPClient()
    
    try:
        # Connect to all available servers
        servers = [
            ("memory", *MCPServerConfigs.memory()),
            ("time", *MCPServerConfigs.time()),
            ("fetch", *MCPServerConfigs.fetch()),
        ]
        
        connected = []
        for server_name, command, args in servers:
            success = await client.connect_to_server(server_name, command, args)
            if success:
                connected.append(server_name)
        
        print(f"🔗 Connected to {len(connected)} servers: {connected}")
        
        # Coordinated workflow example
        if "time" in connected and "memory" in connected:
            # Get current time
            time_result = await client.call_tool("time", "echo", {"message": "current time"})
            print(f"🕒 Time: {time_result}")
            
            # Remember the time
            memory_result = await client.call_tool("memory", "echo", {
                "message": f"Current session started at: {time_result}"
            })
            print(f"💾 Stored: {memory_result}")
        
        # Show server status
        client.print_servers_status()
        
    finally:
        await client.disconnect_all()

async def example_5_configuration_management():
    """Example 5: Dynamic configuration"""
    print("\n⚙️ Example 5: Configuration Management")
    
    # Load and modify configuration
    system = RealMCPAgentSystem()
    system.load_config()
    
    # Show current config
    print("📋 Current enabled servers:")
    for name, config in system.config["servers"].items():
        if config.get("enabled"):
            print(f"  ✅ {name}: {config.get('description', 'No description')}")
        else:
            print(f"  ⏸️  {name}: Disabled")
    
    # Show server groups
    print("\n📦 Server groups:")
    for group, info in system.config.get("groups", {}).items():
        print(f"  🔹 {group}: {info['servers']}")

async def main():
    """Run all examples"""
    print("🌟 MCP Agent System - Interaction Examples")
    print("="*60)
    
    try:
        await example_1_direct_mcp_client()
        await example_2_agent_creation()
        await example_3_custom_workflows()
        await example_4_multi_server_coordination()
        await example_5_configuration_management()
        
        print("\n" + "="*60)
        print("🎉 All examples completed successfully!")
        print("\n💡 Next steps:")
        print("1. Try the interactive mode: python run_with_real_mcp_servers.py")
        print("2. Enable more servers in config/real_mcp_servers.yml")
        print("3. Create your own agents and workflows")
        print("4. Explore the 500+ community MCP servers")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 