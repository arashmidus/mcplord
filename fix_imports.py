#!/usr/bin/env python3
"""
Quick Fix for Import Issues
Run this script to test and fix common import problems.
"""

import os
import sys
from pathlib import Path

def main():
    print("🔧 Fixing MCP Agent Scaffolding imports...")
    
    # Add current directory to Python path
    current_dir = str(Path(__file__).parent.absolute())
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Set PYTHONPATH environment variable
    os.environ['PYTHONPATH'] = f"{current_dir}:{os.environ.get('PYTHONPATH', '')}"
    
    print(f"✅ Added to Python path: {current_dir}")
    
    # Test imports
    try:
        print("🧪 Testing imports...")
        
        from coordination.state.context_bundle import ContextBundle
        print("✅ ContextBundle import successful")
        
        from mcp.servers.context_server import ContextServer
        print("✅ ContextServer import successful")
        
        from agents.base.agent import BaseAgent
        print("✅ BaseAgent import successful")
        
        print("\n🎉 All imports working!")
        print(f"\nTo make this permanent, run:")
        print(f'export PYTHONPATH="{current_dir}:$PYTHONPATH"')
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all __init__.py files are present")
        
        # List missing __init__.py files
        dirs_needing_init = []
        for root, dirs, files in os.walk(current_dir):
            if '__pycache__' in root or '.git' in root:
                continue
            if any(f.endswith('.py') for f in files) and '__init__.py' not in files:
                dirs_needing_init.append(root)
        
        if dirs_needing_init:
            print("Missing __init__.py files in:")
            for d in dirs_needing_init:
                print(f"  {d}")
                # Create the missing __init__.py file
                init_file = Path(d) / "__init__.py"
                init_file.write_text('"""Package init file."""\n')
                print(f"  ✅ Created {init_file}")

if __name__ == "__main__":
    main() 