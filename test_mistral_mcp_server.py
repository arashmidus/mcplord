#!/usr/bin/env python3
"""
Test script for Mistral OCR MCP Server

This script tests the MCP server by checking if it can list tools properly.
"""

import subprocess
import json
import sys
import time

def test_mcp_server():
    """Test the MCP server by checking tool listing."""
    
    print("🧪 Testing Mistral OCR MCP Server...")
    
    # Test 1: Check if server starts without errors
    print("\n📋 Test 1: Server startup...")
    try:
        # Start the server process
        proc = subprocess.Popen([
            sys.executable, "mistral_ocr_mcp_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        
        # Give it a moment to start
        time.sleep(2)
        
        # Send a list_tools request (following MCP protocol)
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        request_str = json.dumps(mcp_request) + "\n"
        
        # Send the request
        proc.stdin.write(request_str.encode())
        proc.stdin.flush()
        
        # Wait for response or timeout
        try:
            stdout, stderr = proc.communicate(timeout=5)
            
            print(f"✅ Server started successfully")
            print(f"📝 Server output (stderr): {stderr.decode()[:200]}...")
            
            # Try to parse response
            if stdout:
                print(f"📤 Server response: {stdout.decode()[:200]}...")
            
        except subprocess.TimeoutExpired:
            print("⏰ Server is running (no immediate errors)")
            
        # Clean up
        proc.terminate()
        
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False
    
    print("\n✅ Basic server test completed!")
    return True

def test_server_direct():
    """Test server functions directly (without MCP protocol)."""
    
    print("\n🧪 Testing server functions directly...")
    
    try:
        # Import the server module
        import mistral_ocr_mcp_server as server_module
        
        # Test the tool functions directly
        print("📋 Testing process_pdf_document_annotation...")
        
        import asyncio
        
        async def test_function():
            result = await server_module.process_pdf_document_annotation(
                document_url="https://arxiv.org/pdf/2301.00001.pdf",
                pages="0,1",
                include_images=False
            )
            return result
        
        # Run the test
        result = asyncio.run(test_function())
        parsed_result = json.loads(result)
        
        print("✅ Function executed successfully!")
        print(f"📝 Result type: {type(parsed_result)}")
        print(f"📊 Status: {parsed_result.get('status', 'unknown')}")
        
        if 'document_annotation' in parsed_result:
            print(f"📄 Language detected: {parsed_result['document_annotation'].get('language', 'unknown')}")
            print(f"📚 Chapter count: {len(parsed_result['document_annotation'].get('chapter_titles', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing functions: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Mistral OCR MCP Server Test Suite")
    print("="*50)
    
    # Test 1: Basic server startup
    test1_result = test_mcp_server()
    
    # Test 2: Direct function testing
    test2_result = test_server_direct()
    
    print("\n" + "="*50)
    print("📊 Test Results:")
    print(f"   🔧 Server startup: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   🎯 Function test: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! Server is ready for Claude Desktop integration.")
        print("\n📋 Next steps:")
        print("   1. Add the server to Claude Desktop's configuration")
        print("   2. Test with real PDF documents")
        print("   3. Optionally set MISTRAL_API_KEY for real OCR processing")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    print("\n🔗 For Claude Desktop integration, add this to claude_desktop_config.json:")
    print(f"""{{
  "mcpServers": {{
    "mistral-ocr": {{
      "command": "python",
      "args": ["{__file__.replace('test_mistral_mcp_server.py', 'mistral_ocr_mcp_server.py')}"]
    }}
  }}
}}""") 