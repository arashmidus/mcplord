#!/usr/bin/env python3
"""
Simple Mistral OCR HTTP Server for ChatGPT

A simplified HTTP server that exposes Mistral OCR functionality via HTTP endpoints
compatible with ChatGPT's MCP client.
"""

import asyncio
import os
import json
import logging
from typing import Any, Dict, List, Optional

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    print("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
    exit(1)

# Mistral AI imports
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request/Response models
class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolListResponse(BaseModel):
    tools: List[Dict[str, Any]]

class ToolCallResponse(BaseModel):
    content: List[Dict[str, Any]]

# Simple OCR server class
class SimpleMistralOCR:
    """Simplified Mistral OCR implementation."""
    
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if self.api_key and MISTRAL_AVAILABLE:
            try:
                self.client = Mistral(api_key=self.api_key)
                logger.info("Mistral client initialized with API key")
            except Exception as e:
                logger.error(f"Failed to initialize Mistral client: {e}")
                self.client = None
        else:
            self.client = None
            if not self.api_key:
                logger.info("No API key - running in mock mode")
            if not MISTRAL_AVAILABLE:
                logger.warning("Mistral AI library not available")
    
    def get_document_schema(self) -> Dict[str, Any]:
        """Get document annotation schema."""
        return {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "properties": {
                        "language": {"type": "string", "description": "Document language"},
                        "chapter_titles": {"type": "array", "items": {"type": "string"}, "description": "Chapter titles and headings"},
                        "urls": {"type": "array", "items": {"type": "string"}, "description": "URLs found in document"},
                        "summary": {"type": "string", "description": "Document summary"},
                        "document_type": {"type": "string", "description": "Type of document"}
                    },
                    "required": ["language", "chapter_titles", "urls"],
                    "title": "DocumentAnnotation",
                    "type": "object"
                },
                "name": "document_annotation",
                "strict": True
            }
        }
    
    async def process_document(self, document_url: str, pages: Optional[str] = None) -> Dict[str, Any]:
        """Process document with Mistral OCR."""
        if not self.client:
            # Return mock data
            return {
                "document_annotation": {
                    "language": "English",
                    "chapter_titles": ["Abstract", "Introduction", "Methodology", "Results", "Conclusion"],
                    "urls": ["https://example.com/ref1", "https://example.com/ref2"],
                    "summary": f"Mock analysis of document: {document_url}",
                    "document_type": "Research Paper"
                },
                "status": "mock_success",
                "pages_processed": pages or "0,1,2,3"
            }
        
        try:
            # Parse pages
            page_list = list(range(8))  # Default
            if pages and pages.lower() != "all":
                page_list = [int(p.strip()) for p in pages.split(",")]
            
            # Call Mistral OCR API
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.ocr.process(
                    model="mistral-ocr-latest",
                    document={"document_url": document_url},
                    pages=page_list,
                    document_annotation_format=self.get_document_schema()
                )
            )
            
            # Convert response to dict
            if hasattr(response, 'dict'):
                return response.dict()
            else:
                return dict(response)
                
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return {"error": str(e), "status": "failed"}

# Create FastAPI app
app = FastAPI(
    title="Mistral OCR MCP Server",
    description="Simple HTTP server for Mistral OCR capabilities",
    version="1.0.0"
)

# Add CORS for ChatGPT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global OCR instance
ocr = SimpleMistralOCR()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Mistral OCR MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools": 4,
        "mistral_available": MISTRAL_AVAILABLE,
        "api_key_set": bool(os.getenv("MISTRAL_API_KEY"))
    }

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}

@app.get("/mcp/tools/list")
async def list_tools():
    """List available MCP tools."""
    tools = [
        {
            "name": "process_pdf_document_annotation",
            "description": "Extract structured annotations from a PDF document using Mistral OCR",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "document_url": {"type": "string", "description": "URL to the PDF document"},
                    "pages": {"type": "string", "description": "Comma-separated page numbers or 'all'"}
                },
                "required": ["document_url"]
            }
        },
        {
            "name": "process_pdf_bbox_annotation", 
            "description": "Extract BBOX annotations from a PDF document",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "document_url": {"type": "string", "description": "URL to the PDF document"},
                    "pages": {"type": "string", "description": "Comma-separated page numbers or 'all'"}
                },
                "required": ["document_url"]
            }
        },
        {
            "name": "process_pdf_full_annotation",
            "description": "Extract complete annotations from a PDF",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "document_url": {"type": "string", "description": "URL to the PDF document"},
                    "pages": {"type": "string", "description": "Comma-separated page numbers or 'all'"}
                },
                "required": ["document_url"]
            }
        },
        {
            "name": "analyze_research_paper",
            "description": "Specialized analysis for research papers",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "document_url": {"type": "string", "description": "URL to the research paper PDF"}
                },
                "required": ["document_url"]
            }
        }
    ]
    
    return {"tools": tools}

@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call an MCP tool."""
    tool_name = request.name
    args = request.arguments
    
    try:
        if tool_name == "process_pdf_document_annotation":
            result = await ocr.process_document(
                document_url=args.get("document_url"),
                pages=args.get("pages")
            )
        elif tool_name in ["process_pdf_bbox_annotation", "process_pdf_full_annotation", "analyze_research_paper"]:
            # For now, all tools use the same document processing
            result = await ocr.process_document(
                document_url=args.get("document_url"),
                pages=args.get("pages")
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Direct API endpoints for testing
@app.post("/api/process")
async def process_document_api(
    document_url: str,
    pages: Optional[str] = None
):
    """Direct API endpoint for document processing."""
    try:
        result = await ocr.process_document(document_url, pages)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Server startup info
    api_key = os.getenv("MISTRAL_API_KEY")
    print("🚀 Starting Mistral OCR Simple HTTP Server...")
    print(f"📡 Server will be available at http://localhost:3005")
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Not set (mock mode)'}")
    print(f"📦 Mistral AI: {'✅ Available' if MISTRAL_AVAILABLE else '❌ Not available'}")
    print("\n📄 Available endpoints:")
    print("   • GET  /                   - Server info") 
    print("   • GET  /health             - Health check")
    print("   • POST /mcp/tools/list     - List MCP tools")
    print("   • POST /mcp/tools/call     - Call MCP tool")
    print("   • POST /api/process        - Direct processing")
    print("\n🎯 For ChatGPT: Use the /mcp/ endpoints")
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3005,
        log_level="info",
        access_log=False
    ) 