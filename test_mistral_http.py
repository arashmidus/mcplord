#!/usr/bin/env python3
"""
Quick test script to debug the Mistral OCR HTTP server
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

try:
    print("🧪 Testing Mistral OCR HTTP server imports...")
    
    # Test FastAPI import
    try:
        from fastapi import FastAPI
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
    
    # Test Mistral import
    try:
        from mistralai import Mistral
        print("✅ Mistral AI imported successfully") 
    except ImportError as e:
        print(f"⚠️  Mistral AI import failed (will use mock): {e}")
    
    # Test our OCR server import
    try:
        from mcp.servers.mistral_ocr_server import MistralOCRServer
        print("✅ MistralOCRServer imported successfully")
        
        # Test server creation
        server = MistralOCRServer()
        print("✅ MistralOCRServer created successfully")
        
    except Exception as e:
        print(f"❌ MistralOCRServer failed: {e}")
        traceback.print_exc()
    
    # Test HTTP server import
    try:
        from mcp.servers.mistral_ocr_http_server import app
        if app:
            print("✅ HTTP server app created successfully")
        else:
            print("❌ HTTP server app is None")
    except Exception as e:
        print(f"❌ HTTP server import failed: {e}")
        traceback.print_exc()
    
    print("\n🎯 All tests completed!")
    
except Exception as e:
    print(f"❌ Test script failed: {e}")
    traceback.print_exc() 