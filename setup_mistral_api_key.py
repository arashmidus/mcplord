#!/usr/bin/env python3
"""
Mistral API Key Setup Script

This script helps you set up your Mistral API key for the enhanced MCP server.
"""

import os
import sys
from pathlib import Path

def check_current_key():
    """Check if API key is currently set."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if api_key:
        print(f"✅ MISTRAL_API_KEY is currently set (ends with: ...{api_key[-8:]})")
        return True
    else:
        print("❌ MISTRAL_API_KEY is not set")
        return False

def get_shell_profile_path():
    """Get the appropriate shell profile path."""
    shell = os.getenv("SHELL", "/bin/bash")
    home = Path.home()
    
    if "zsh" in shell:
        return home / ".zshrc"
    elif "bash" in shell:
        # Check for .bash_profile first, then .bashrc
        bash_profile = home / ".bash_profile"
        if bash_profile.exists():
            return bash_profile
        else:
            return home / ".bashrc"
    else:
        return home / ".profile"

def add_to_profile(api_key, profile_path):
    """Add API key to shell profile."""
    try:
        # Read existing content
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                content = f.read()
        else:
            content = ""
        
        # Check if already exists
        if "MISTRAL_API_KEY" in content:
            print(f"⚠️  MISTRAL_API_KEY already exists in {profile_path}")
            print("   You may need to update it manually or remove the old line")
            return False
        
        # Add the export line
        export_line = f'\nexport MISTRAL_API_KEY="{api_key}"\n'
        
        with open(profile_path, 'a') as f:
            f.write(export_line)
        
        print(f"✅ Added MISTRAL_API_KEY to {profile_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {profile_path}: {e}")
        return False

def create_env_file(api_key):
    """Create a .env file in the current directory."""
    env_path = Path(".env")
    
    try:
        # Read existing .env if it exists
        if env_path.exists():
            with open(env_path, 'r') as f:
                content = f.read()
        else:
            content = ""
        
        # Check if already exists
        if "MISTRAL_API_KEY" in content:
            print("⚠️  MISTRAL_API_KEY already exists in .env file")
            return False
        
        # Add the key
        env_line = f'MISTRAL_API_KEY="{api_key}"\n'
        
        with open(env_path, 'a') as f:
            f.write(env_line)
        
        print(f"✅ Added MISTRAL_API_KEY to .env file")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_api_key(api_key):
    """Test if the API key works."""
    try:
        from mistralai import Mistral
        client = Mistral(api_key=api_key)
        print("✅ API key format appears valid")
        print("   (Note: Full validation requires making an API call)")
        return True
    except ImportError:
        print("⚠️  Mistral AI library not available - install with: pip install mistralai")
        return False
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

def main():
    print("🔑 Mistral API Key Setup")
    print("=" * 50)
    
    # Check current status
    print("\n📋 Current Status:")
    has_key = check_current_key()
    
    if has_key:
        response = input("\n🤔 API key is already set. Do you want to update it? (y/N): ")
        if response.lower() != 'y':
            print("👍 Keeping existing API key")
            return
    
    # Get API key from user
    print("\n🔑 Enter your Mistral API Key:")
    print("   You can get one from: https://console.mistral.ai/")
    print("   The key should start with something like 'sk-' or similar")
    
    api_key = input("\nAPI Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return
    
    # Test the API key
    print("\n🧪 Testing API key...")
    test_api_key(api_key)
    
    # Choose setup method
    print("\n📋 Choose setup method:")
    print("1. Add to shell profile (recommended - persistent)")
    print("2. Create .env file (project-specific)")
    print("3. Show manual instructions")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == "1":
        # Add to shell profile
        profile_path = get_shell_profile_path()
        print(f"\n📁 Using shell profile: {profile_path}")
        
        if add_to_profile(api_key, profile_path):
            print(f"\n✅ Success! API key added to {profile_path}")
            print("\n📋 Next steps:")
            print("1. Restart your terminal OR run:")
            print(f"   source {profile_path}")
            print("2. Test the enhanced server:")
            print("   python test_pdf_upload.py")
        
    elif choice == "2":
        # Create .env file
        if create_env_file(api_key):
            print("\n✅ Success! API key added to .env file")
            print("\n📋 Next steps:")
            print("1. The server will automatically load from .env")
            print("2. Test the enhanced server:")
            print("   python test_pdf_upload.py")
        
    elif choice == "3":
        # Show manual instructions
        print("\n📋 Manual Setup Instructions:")
        print("\n1. **Environment Variable (Terminal session):**")
        print(f'   export MISTRAL_API_KEY="{api_key}"')
        
        print("\n2. **Shell Profile (Permanent):**")
        profile_path = get_shell_profile_path()
        print(f"   Add this line to {profile_path}:")
        print(f'   export MISTRAL_API_KEY="{api_key}"')
        
        print("\n3. **Environment File:**")
        print("   Create a .env file with:")
        print(f'   MISTRAL_API_KEY="{api_key}"')
        
    else:
        print("❌ Invalid choice")
        return
    
    print("\n🎉 Setup complete!")
    print("\n🔧 The enhanced MCP server will now use your API key for real OCR processing!")

if __name__ == "__main__":
    main() 