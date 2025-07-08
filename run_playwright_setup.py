#!/usr/bin/env python3
"""
Simple runner for Playwright MCP Server setup.

This script handles environment setup and runs the comprehensive
Playwright MCP configuration and demonstration.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Set environment variables
os.environ['PYTHONPATH'] = f"{current_dir}:{os.environ.get('PYTHONPATH', '')}"

# Import and run the setup
if __name__ == "__main__":
    try:
        from setup_playwright_mcp import main
        import asyncio
        asyncio.run(main())
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're in the mcp-agent-scaffolding directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1) 