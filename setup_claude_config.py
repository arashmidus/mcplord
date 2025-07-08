#!/usr/bin/env python3
"""
Setup script for Claude Desktop MCP configuration

This script automatically configures Claude Desktop to use the Mistral OCR MCP server
with the correct Python path and working directory.
"""

import json
import os
import shutil
import sys
from pathlib import Path

def get_claude_config_path():
    """Get the path to Claude Desktop configuration file."""
    if sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":  # Windows
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"

def get_python_path():
    """Get the current Python executable path."""
    return sys.executable

def get_server_path():
    """Get the absolute path to the MCP server."""
    current_dir = Path(__file__).parent
    return str(current_dir / "mistral_ocr_mcp_server.py")

def get_working_directory():
    """Get the working directory (parent of mcp-agent-scaffolding)."""
    current_dir = Path(__file__).parent
    return str(current_dir.parent)

def create_mcp_config():
    """Create the MCP server configuration."""
    return {
        "mcpServers": {
            "mistral-ocr": {
                "command": get_python_path(),
                "args": [get_server_path()],
                "cwd": get_working_directory()
            }
        }
    }

def backup_existing_config(config_path):
    """Backup existing configuration if it exists."""
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        shutil.copy2(config_path, backup_path)
        print(f"📋 Backed up existing config to: {backup_path}")
        return True
    return False

def merge_configs(existing_config, new_config):
    """Merge new MCP server config with existing configuration."""
    if "mcpServers" not in existing_config:
        existing_config["mcpServers"] = {}
    
    # Add or update the mistral-ocr server
    existing_config["mcpServers"]["mistral-ocr"] = new_config["mcpServers"]["mistral-ocr"]
    
    return existing_config

def main():
    """Main setup function."""
    print("🚀 Setting up Claude Desktop MCP configuration...")
    print("=" * 60)
    
    # Get paths
    config_path = get_claude_config_path()
    python_path = get_python_path()
    server_path = get_server_path()
    working_dir = get_working_directory()
    
    print(f"📍 Configuration details:")
    print(f"   Claude config: {config_path}")
    print(f"   Python path: {python_path}")
    print(f"   Server path: {server_path}")
    print(f"   Working dir: {working_dir}")
    print()
    
    # Check if server file exists
    if not Path(server_path).exists():
        print(f"❌ Error: Server file not found at {server_path}")
        print("   Make sure you're running this script from the mcp-agent-scaffolding directory")
        sys.exit(1)
    
    # Create config directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new one
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
            print("📄 Found existing Claude Desktop configuration")
        except json.JSONDecodeError:
            print("⚠️  Existing config file is invalid JSON, creating new one")
            backup_existing_config(config_path)
    
    # Create new MCP configuration
    new_config = create_mcp_config()
    
    # Merge configurations
    final_config = merge_configs(existing_config, new_config)
    
    # Backup existing config
    if config_path.exists():
        backup_existing_config(config_path)
    
    # Write the configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(final_config, f, indent=2)
        
        print("✅ Successfully updated Claude Desktop configuration!")
        print()
        print("📋 Next steps:")
        print("   1. Restart Claude Desktop completely")
        print("   2. Look for the tools icon (⚙️) in the chat interface")
        print("   3. You should see 3 tools: process_pdf_document_annotation, process_pdf_bbox_annotation, analyze_research_paper")
        print()
        print("🧪 Test with:")
        print('   "Analyze this research paper: https://arxiv.org/pdf/2301.00001.pdf"')
        print()
        print("🔧 If you have issues, check Claude's logs:")
        print("   tail -f ~/Library/Logs/Claude/mcp*.log")
        
    except Exception as e:
        print(f"❌ Error writing configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 