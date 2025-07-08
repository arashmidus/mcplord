#!/usr/bin/env python3
"""
Test server startup and basic functionality
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

async def test_server_startup():
    """Test that the server can start without errors."""
    
    print("🧪 Testing Enhanced Server Startup")
    print("=" * 40)
    
    try:
        # Import the server components
        from mcp.server import Server
        from mcp.types import CallToolResult, TextContent, Tool
        
        print("✅ MCP imports successful")
        
        # Test TextContent creation
        text_content = TextContent(type="text", text="Test message")
        print(f"✅ TextContent created: {type(text_content)}")
        
        # Test CallToolResult creation
        result = CallToolResult(content=[text_content])
        print(f"✅ CallToolResult created: {type(result)}")
        
        # Test server creation
        server = Server("test-server")
        print(f"✅ Server created: {type(server)}")
        
        # Test tool creation
        tool = Tool(
            name="test_tool",
            description="Test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_param": {"type": "string", "description": "Test parameter"}
                },
                "required": ["test_param"]
            }
        )
        print(f"✅ Tool created: {type(tool)}")
        
        print("\n✅ All MCP components working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_server_import():
    """Test that the enhanced server can be imported."""
    
    print("\n🧪 Testing Enhanced Server Import")
    print("=" * 40)
    
    try:
        # Import enhanced server functions
        from mistral_ocr_enhanced_server import (
            process_pdf_document_annotation,
            process_pdf_bbox_annotation,
            analyze_research_paper
        )
        
        print("✅ Enhanced server functions imported successfully")
        
        # Test a simple call with error handling
        result = await process_pdf_document_annotation()
        print(f"✅ Function call successful (expected error): {result[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing enhanced server: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    
    print("🔧 Enhanced Mistral OCR Server - Startup Test")
    print("=" * 50)
    
    # Test 1: Basic MCP components
    test1_passed = await test_server_startup()
    
    # Test 2: Enhanced server import
    test2_passed = await test_enhanced_server_import()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   MCP Components: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Enhanced Server: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Server should work correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 