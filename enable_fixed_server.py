#!/usr/bin/env python3
"""
Enable the fixed enhanced server for Claude Desktop
"""

import json
import shutil
import sys
from pathlib import Path

def get_claude_config_path():
    """Get the Claude Desktop configuration path."""
    if sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":  # Windows
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"

def enable_fixed_server():
    """Enable the fixed enhanced server."""
    
    print("🔧 Enabling Fixed Enhanced Server")
    print("=" * 50)
    
    config_path = get_claude_config_path()
    current_dir = Path(__file__).parent
    working_dir = current_dir.parent
    
    # Backup existing config
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        shutil.copy2(config_path, backup_path)
        print(f"✅ Backed up config to: {backup_path}")
    
    # Load existing config
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            config = {}
    else:
        config = {}
    
    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Add the fixed enhanced server
    config["mcpServers"]["mistral-ocr-enhanced-fixed"] = {
        "command": sys.executable,
        "args": [str(current_dir / "mistral_ocr_enhanced_server_fixed.py")],
        "cwd": str(working_dir)
    }
    
    # Keep the original working server as backup
    config["mcpServers"]["mistral-ocr-backup"] = {
        "command": sys.executable,
        "args": [str(current_dir / "mistral_ocr_mcp_server.py")],
        "cwd": str(working_dir),
        "_note": "Original working server as backup"
    }
    
    # Save the updated config
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration updated successfully!")
    print("\n📋 Current servers:")
    print("   • mistral-ocr-enhanced-fixed: Fixed enhanced server (PDF uploads)")
    print("   • mistral-ocr-backup: Original working server (URLs only)")
    
    print("\n🔄 Next steps:")
    print("1. Restart Claude Desktop completely")
    print("2. Test with the fixed enhanced server")
    print("3. Upload a PDF and ask Claude to analyze it")
    
    return True

if __name__ == "__main__":
    print("🚀 Fixed Enhanced Server Enabler")
    
    if enable_fixed_server():
        print("\n🎉 Fixed enhanced server enabled!")
        print("\nYou can now upload PDFs directly to Claude Desktop!")
        print("The server will handle your legal_complaint.pdf properly.")
    else:
        print("\n❌ Failed to enable fixed server.")
        sys.exit(1) 