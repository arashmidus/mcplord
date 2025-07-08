#!/usr/bin/env python3
"""
Test script for Claude Desktop integration

This script helps verify that the MCP server is working correctly with Claude Desktop.
"""

import subprocess
import json
import sys
import time
import os
from pathlib import Path

def check_claude_config():
    """Check if Claude Desktop configuration is correct."""
    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    
    if not config_path.exists():
        print("❌ Claude Desktop config file not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if "mcpServers" not in config:
            print("❌ No mcpServers in config")
            return False
        
        if "mistral-ocr" not in config["mcpServers"]:
            print("❌ mistral-ocr server not found in config")
            return False
        
        server_config = config["mcpServers"]["mistral-ocr"]
        print("✅ Claude Desktop configuration found:")
        print(f"   Command: {server_config['command']}")
        print(f"   Args: {server_config['args']}")
        print(f"   Working dir: {server_config.get('cwd', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def test_server_startup():
    """Test if the server starts correctly."""
    print("\n🧪 Testing server startup...")
    
    server_path = Path(__file__).parent / "mistral_ocr_mcp_server.py"
    if not server_path.exists():
        print(f"❌ Server file not found: {server_path}")
        return False
    
    try:
        # Change to parent directory to avoid import conflicts
        os.chdir(Path(__file__).parent.parent)
        
        # Start server process
        proc = subprocess.Popen([
            sys.executable, str(server_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give it time to start
        time.sleep(2)
        
        # Check if process is still running
        if proc.poll() is None:
            print("✅ Server started successfully and is running")
            proc.terminate()
            proc.wait()
            return True
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ Server failed to start")
            print(f"   stdout: {stdout[:200]}...")
            print(f"   stderr: {stderr[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def check_python_path():
    """Check if Python path is correct."""
    print("\n🐍 Checking Python environment...")
    
    python_path = sys.executable
    print(f"   Python executable: {python_path}")
    
    # Check MCP installation
    try:
        import mcp
        print("✅ MCP SDK is available")
        return True
    except ImportError as e:
        print(f"❌ MCP SDK not available: {e}")
        return False

def restart_claude_desktop():
    """Provide instructions for restarting Claude Desktop."""
    print("\n🔄 To restart Claude Desktop:")
    print("   1. Quit Claude Desktop completely (Cmd+Q)")
    print("   2. Wait 2-3 seconds")
    print("   3. Reopen Claude Desktop")
    print("   4. Look for the tools icon (⚙️) in the chat interface")
    print("   5. You should see 3 tools listed")

def main():
    """Main test function."""
    print("🚀 Claude Desktop Integration Test")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Python Environment", check_python_path),
        ("Server Startup", test_server_startup),
        ("Claude Config", check_claude_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Your MCP server should work with Claude Desktop.")
        restart_claude_desktop()
        print("\n🧪 Test commands in Claude Desktop:")
        print('   "Analyze this research paper: https://arxiv.org/pdf/2301.00001.pdf"')
        print('   "Extract sections from: https://arxiv.org/pdf/2301.00001.pdf"')
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Run: cd mcp-agent-scaffolding && python setup_claude_config.py")
        print("   2. Check: tail -f ~/Library/Logs/Claude/mcp*.log")
        print("   3. Restart Claude Desktop completely")

if __name__ == "__main__":
    main() 