#!/usr/bin/env python3
"""
Simple test to check Mistral API response structure
"""

import asyncio
import json
import os
from pathlib import Path

# Load .env file
def load_env_file():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env_file()

async def test_mistral_api():
    """Test the Mistral API with a simple URL."""
    
    try:
        from mistralai import Mistral
        
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            print("❌ MISTRAL_API_KEY not found")
            return
            
        client = Mistral(api_key=api_key)
        
        # Simple document annotation schema
        schema = {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "properties": {
                        "language": {"type": "string", "description": "Document language"},
                        "title": {"type": "string", "description": "Document title"},
                        "summary": {"type": "string", "description": "Brief summary"}
                    },
                    "required": ["language"],
                    "title": "SimpleAnnotation",
                    "type": "object",
                    "additionalProperties": False
                },
                "name": "simple_annotation",
                "strict": True
            }
        }
        
        print("🧪 Testing Mistral OCR API...")
        print("📄 Processing: https://arxiv.org/pdf/2301.00001.pdf")
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.ocr.process(
                model="mistral-ocr-latest",
                document={"document_url": "https://arxiv.org/pdf/2301.00001.pdf"},
                pages=[0],
                document_annotation_format=schema
            )
        )
        
        print("\n✅ API call successful!")
        print(f"📊 Response type: {type(response)}")
        print(f"📊 Response attributes: {dir(response)}")
        
        # Try different ways to convert to dict
        if hasattr(response, 'dict'):
            result = response.dict()
            print("📋 Using .dict() method")
        elif hasattr(response, 'model_dump'):
            result = response.model_dump()
            print("📋 Using .model_dump() method")
        elif hasattr(response, '__dict__'):
            result = response.__dict__
            print("📋 Using .__dict__ attribute")
        else:
            result = {"raw": str(response)}
            print("📋 Using string conversion")
        
        print(f"\n📄 Result structure:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mistral_api()) 