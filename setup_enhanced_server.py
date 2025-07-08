#!/usr/bin/env python3
"""
Setup script for Enhanced Mistral OCR MCP Server

This script configures Claude Desktop to use the enhanced server that supports
both PDF URLs and uploaded PDF files.
"""

import json
import shutil
import sys
from pathlib import Path

def setup_enhanced_server():
    """Set up the enhanced MCP server for Claude Desktop."""
    
    print("🚀 Setting up Enhanced Mistral OCR MCP Server...")
    print("=" * 60)
    
    # Get paths
    current_dir = Path(__file__).parent
    enhanced_server_path = current_dir / "mistral_ocr_enhanced_server.py"
    working_dir = current_dir.parent
    
    # Check if enhanced server exists
    if not enhanced_server_path.exists():
        print(f"❌ Enhanced server not found: {enhanced_server_path}")
        print("   Make sure mistral_ocr_enhanced_server.py exists")
        return False
    
    # Get Claude config path
    if sys.platform == "darwin":  # macOS
        config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":  # Windows
        config_path = Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        config_path = Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    
    print(f"📍 Configuration details:")
    print(f"   Claude config: {config_path}")
    print(f"   Python path: {sys.executable}")
    print(f"   Enhanced server: {enhanced_server_path}")
    print(f"   Working dir: {working_dir}")
    print()
    
    # Create config directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
            print("📄 Found existing Claude Desktop configuration")
        except json.JSONDecodeError:
            print("⚠️  Existing config file is invalid JSON, creating new one")
            # Backup the broken config
            backup_path = config_path.with_suffix('.json.backup')
            shutil.copy2(config_path, backup_path)
            print(f"📋 Backed up broken config to: {backup_path}")
    
    # Create enhanced server configuration
    enhanced_config = {
        "mcpServers": {
            "mistral-ocr-enhanced": {
                "command": sys.executable,
                "args": [str(enhanced_server_path)],
                "cwd": str(working_dir)
            }
        }
    }
    
    # Merge configurations
    if "mcpServers" not in existing_config:
        existing_config["mcpServers"] = {}
    
    # Add the enhanced server (replace existing mistral-ocr if present)
    existing_config["mcpServers"]["mistral-ocr-enhanced"] = enhanced_config["mcpServers"]["mistral-ocr-enhanced"]
    
    # Optionally remove the old server
    if "mistral-ocr" in existing_config["mcpServers"]:
        print("🔄 Found existing mistral-ocr server - will keep both")
        print("   • mistral-ocr: Original server (URLs only)")
        print("   • mistral-ocr-enhanced: New server (URLs + uploads)")
    
    # Backup existing config
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        shutil.copy2(config_path, backup_path)
        print(f"📋 Backed up existing config to: {backup_path}")
    
    # Write the updated configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        print("✅ Successfully updated Claude Desktop configuration!")
        print()
        print("📋 Enhanced Features:")
        print("   ✅ Process PDFs from URLs (existing functionality)")
        print("   ✅ Process uploaded PDF files (NEW!)")
        print("   ✅ Automatic temporary file management")
        print("   ✅ Base64 encoding/decoding handling")
        print()
        print("🔧 Available Tools:")
        print("   • process_pdf_document_annotation (URLs + uploads)")
        print("   • process_pdf_bbox_annotation (URLs + uploads)")
        print("   • analyze_research_paper (URLs + uploads)")
        print()
        print("📋 Next steps:")
        print("   1. Restart Claude Desktop completely")
        print("   2. Look for the tools icon (⚙️) in the chat interface")
        print("   3. You should see the enhanced tools listed")
        print()
        print("🧪 Test with URLs:")
        print('   "Analyze this research paper: https://arxiv.org/pdf/2301.00001.pdf"')
        print()
        print("🧪 Test with uploads:")
        print("   1. Upload a PDF file to Claude Desktop")
        print('   2. Ask: "Analyze the PDF I just uploaded"')
        print("   3. Claude will automatically use the enhanced server")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing configuration: {e}")
        return False

def test_enhanced_server():
    """Test that the enhanced server can start properly."""
    print("\n🧪 Testing enhanced server startup...")
    
    import subprocess
    import time
    
    server_path = Path(__file__).parent / "mistral_ocr_enhanced_server.py"
    working_dir = Path(__file__).parent.parent
    
    try:
        # Change to working directory
        original_dir = Path.cwd()
        
        # Start server process
        proc = subprocess.Popen([
            sys.executable, str(server_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(working_dir))
        
        # Give it time to start
        time.sleep(3)
        
        # Check if process is still running
        if proc.poll() is None:
            print("✅ Enhanced server started successfully and is running")
            proc.terminate()
            proc.wait()
            return True
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ Enhanced server failed to start")
            if stderr:
                print(f"   Error: {stderr[:300]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing enhanced server: {e}")
        return False

def show_comparison():
    """Show comparison between original and enhanced server."""
    print("\n📊 Server Comparison:")
    print("=" * 60)
    
    print("🔹 Original Server (mistral-ocr):")
    print("   ✅ Process PDFs from URLs")
    print("   ❌ Cannot handle uploaded files")
    print("   ✅ Simple, stable")
    
    print("\n🔹 Enhanced Server (mistral-ocr-enhanced):")
    print("   ✅ Process PDFs from URLs")
    print("   ✅ Process uploaded PDF files")
    print("   ✅ Automatic base64 handling")
    print("   ✅ Temporary file management")
    print("   ✅ Backward compatible")
    
    print("\n💡 Recommendation:")
    print("   Use the enhanced server for full functionality!")

if __name__ == "__main__":
    print("🚀 Enhanced Mistral OCR MCP Server Setup")
    
    # Show comparison
    show_comparison()
    
    # Test the enhanced server
    if test_enhanced_server():
        print("\n✅ Enhanced server test passed!")
        
        # Set up the configuration
        if setup_enhanced_server():
            print("\n🎉 Setup completed successfully!")
            print("\n📱 Ready to use with Claude Desktop!")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
    else:
        print("\n❌ Enhanced server test failed. Please check the server file.") 