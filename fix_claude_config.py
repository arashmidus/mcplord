#!/usr/bin/env python3
"""
Fix Claude Desktop configuration and test servers
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

def backup_config(config_path):
    """Backup the existing configuration."""
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        shutil.copy2(config_path, backup_path)
        print(f"✅ Backed up config to: {backup_path}")
        return True
    return False

def load_config(config_path):
    """Load existing configuration."""
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️  Invalid JSON in config file")
            return {}
    return {}

def save_config(config_path, config):
    """Save configuration."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def fix_claude_config():
    """Fix the Claude Desktop configuration."""
    
    print("🔧 Fixing Claude Desktop Configuration")
    print("=" * 50)
    
    config_path = get_claude_config_path()
    current_dir = Path(__file__).parent
    working_dir = current_dir.parent
    
    print(f"📍 Config path: {config_path}")
    print(f"📍 Working dir: {working_dir}")
    
    # Backup existing config
    backup_config(config_path)
    
    # Load existing config
    config = load_config(config_path)
    
    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Add the original working server
    config["mcpServers"]["mistral-ocr"] = {
        "command": sys.executable,
        "args": [str(current_dir / "mistral_ocr_mcp_server.py")],
        "cwd": str(working_dir)
    }
    
    # Add the enhanced server (commented out for now)
    config["mcpServers"]["mistral-ocr-enhanced-disabled"] = {
        "command": sys.executable,
        "args": [str(current_dir / "mistral_ocr_enhanced_server.py")],
        "cwd": str(working_dir),
        "_note": "Enhanced server - currently disabled due to validation errors"
    }
    
    # Save the updated config
    save_config(config_path, config)
    
    print("✅ Configuration updated successfully!")
    print("\n📋 Current servers:")
    print("   • mistral-ocr: Original working server")
    print("   • mistral-ocr-enhanced-disabled: Enhanced server (disabled)")
    
    print("\n🔄 Next steps:")
    print("1. Restart Claude Desktop completely")
    print("2. Test with the original server first")
    print("3. Once confirmed working, we can debug the enhanced server")
    
    return True

def show_debug_info():
    """Show debugging information."""
    print("\n🔍 Debug Information:")
    print("=" * 50)
    
    current_dir = Path(__file__).parent
    
    # Check if files exist
    files_to_check = [
        "mistral_ocr_mcp_server.py",
        "mistral_ocr_enhanced_server.py",
        ".env"
    ]
    
    for file in files_to_check:
        file_path = current_dir / file
        status = "✅ EXISTS" if file_path.exists() else "❌ MISSING"
        print(f"   {file}: {status}")
    
    # Check MCP version
    try:
        import mcp
        print(f"   MCP library: ✅ Available")
    except ImportError:
        print(f"   MCP library: ❌ Missing")
    
    # Check Mistral library
    try:
        import mistralai
        print(f"   Mistral library: ✅ Available")
    except ImportError:
        print(f"   Mistral library: ❌ Missing")
    
    # Check API key
    import os
    api_key = os.getenv("MISTRAL_API_KEY")
    if api_key:
        print(f"   API key: ✅ Set (ends with: ...{api_key[-8:]})")
    else:
        print(f"   API key: ❌ Not set")

if __name__ == "__main__":
    print("🔧 Claude Desktop Configuration Fixer")
    
    show_debug_info()
    
    if fix_claude_config():
        print("\n🎉 Configuration fixed successfully!")
        print("\nℹ️  The enhanced server has been temporarily disabled.")
        print("   Use the original server first to confirm everything works.")
        print("   Then we can debug the enhanced server separately.")
    else:
        print("\n❌ Configuration fix failed.")
        sys.exit(1) 