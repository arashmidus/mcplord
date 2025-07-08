#!/usr/bin/env python3
"""
Mistral OCR HTTP Server for ChatGPT Integration

This server provides HTTP/SSE endpoints for the Mistral OCR functionality
so it can be accessed by ChatGPT's MCP client.
"""

import asyncio
import os
import json
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

# Import our core OCR server
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mistral_ocr_server import MistralOCRServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests
class DocumentAnnotationRequest(BaseModel):
    document_url: str
    pages: Optional[str] = None
    include_images: bool = False

class BBoxAnnotationRequest(BaseModel):
    document_url: str
    pages: Optional[str] = None
    include_images: bool = False

class FullAnnotationRequest(BaseModel):
    document_url: str
    pages: Optional[str] = None

class ResearchPaperRequest(BaseModel):
    document_url: str

class MCPToolCall(BaseModel):
    method: str = "tools/call"
    params: Dict[str, Any]

class MCPListTools(BaseModel):
    method: str = "tools/list"

# Global OCR server instance
ocr_server = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the OCR server."""
    global ocr_server
    ocr_server = MistralOCRServer()
    logger.info("Mistral OCR HTTP Server initialized")
    yield
    logger.info("Mistral OCR HTTP Server shutting down")

# Create FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Mistral OCR MCP Server",
        description="HTTP/SSE server for Mistral OCR annotation capabilities",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware for ChatGPT access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # ChatGPT needs this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """Root endpoint showing server info."""
        return {
            "name": "Mistral OCR MCP Server",
            "version": "1.0.0",
            "description": "PDF processing with structured data extraction",
            "tools": [
                "process_pdf_document_annotation",
                "process_pdf_bbox_annotation",
                "process_pdf_full_annotation",
                "analyze_research_paper"
            ]
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "mistral_available": MISTRAL_AVAILABLE}
    
    # MCP Protocol Endpoints
    @app.post("/mcp/tools/list")
    async def list_tools():
        """List available MCP tools."""
        return {
            "tools": [
                {
                    "name": "process_pdf_document_annotation",
                    "description": "Extract structured annotations from a PDF document using Mistral OCR",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "document_url": {"type": "string", "description": "URL to the PDF document"},
                            "pages": {"type": "string", "description": "Comma-separated page numbers or 'all'"},
                            "include_images": {"type": "boolean", "description": "Include base64 images"}
                        },
                        "required": ["document_url"]
                    }
                },
                {
                    "name": "process_pdf_bbox_annotation",
                    "description": "Extract BBOX annotations from a PDF document using Mistral OCR",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "document_url": {"type": "string", "description": "URL to the PDF document"},
                            "pages": {"type": "string", "description": "Comma-separated page numbers or 'all'"},
                            "include_images": {"type": "boolean", "description": "Include base64 images"}
                        },
                        "required": ["document_url"]
                    }
                },
                {
                    "name": "process_pdf_full_annotation",
                    "description": "Extract complete annotations from a PDF using Mistral OCR",
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
        }
    
    @app.post("/mcp/tools/call")
    async def call_tool(request: MCPToolCall):
        """Call an MCP tool."""
        global ocr_server
        
        if not ocr_server:
            raise HTTPException(status_code=500, detail="OCR server not initialized")
        
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        try:
            if tool_name == "process_pdf_document_annotation":
                result = await process_document_annotation_internal(
                    arguments.get("document_url"),
                    arguments.get("pages"),
                    arguments.get("include_images", False)
                )
            elif tool_name == "process_pdf_bbox_annotation":
                result = await process_bbox_annotation_internal(
                    arguments.get("document_url"),
                    arguments.get("pages"),
                    arguments.get("include_images", False)
                )
            elif tool_name == "process_pdf_full_annotation":
                result = await process_full_annotation_internal(
                    arguments.get("document_url"),
                    arguments.get("pages")
                )
            elif tool_name == "analyze_research_paper":
                result = await analyze_research_paper_internal(
                    arguments.get("document_url")
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Direct API endpoints for easier testing
    @app.post("/api/document-annotation")
    async def document_annotation_endpoint(request: DocumentAnnotationRequest):
        """Direct endpoint for document annotation."""
        result = await process_document_annotation_internal(
            request.document_url,
            request.pages,
            request.include_images
        )
        return {"result": json.loads(result)}
    
    @app.post("/api/bbox-annotation")
    async def bbox_annotation_endpoint(request: BBoxAnnotationRequest):
        """Direct endpoint for BBOX annotation."""
        result = await process_bbox_annotation_internal(
            request.document_url,
            request.pages,
            request.include_images
        )
        return {"result": json.loads(result)}
    
    @app.post("/api/full-annotation")
    async def full_annotation_endpoint(request: FullAnnotationRequest):
        """Direct endpoint for full annotation."""
        result = await process_full_annotation_internal(
            request.document_url,
            request.pages
        )
        return {"result": json.loads(result)}
    
    @app.post("/api/research-paper")
    async def research_paper_endpoint(request: ResearchPaperRequest):
        """Direct endpoint for research paper analysis."""
        result = await analyze_research_paper_internal(request.document_url)
        return {"result": json.loads(result)}
    
    # Internal helper functions
    async def process_document_annotation_internal(
        document_url: str,
        pages: Optional[str] = None,
        include_images: bool = False
    ) -> str:
        """Internal function for document annotation."""
        global ocr_server
        
        try:
            # Parse pages
            page_list = None
            if pages and pages.lower() != "all":
                page_list = [int(p.strip()) for p in pages.split(",")]
            
            result = await ocr_server.process_document_annotation(
                document_url=document_url,
                pages=page_list,
                include_image_base64=include_images
            )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e), "status": "failed"}, indent=2)
    
    async def process_bbox_annotation_internal(
        document_url: str,
        pages: Optional[str] = None,
        include_images: bool = False
    ) -> str:
        """Internal function for BBOX annotation."""
        global ocr_server
        
        try:
            # Parse pages
            page_list = None
            if pages and pages.lower() != "all":
                page_list = [int(p.strip()) for p in pages.split(",")]
            
            result = await ocr_server.process_bbox_annotation(
                document_url=document_url,
                pages=page_list,
                include_image_base64=include_images
            )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e), "status": "failed"}, indent=2)
    
    async def process_full_annotation_internal(
        document_url: str,
        pages: Optional[str] = None
    ) -> str:
        """Internal function for full annotation."""
        global ocr_server
        
        try:
            # Parse pages
            page_list = None
            if pages and pages.lower() != "all":
                page_list = [int(p.strip()) for p in pages.split(",")]
            
            result = await ocr_server.process_full_annotation(
                document_url=document_url,
                pages=page_list
            )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e), "status": "failed"}, indent=2)
    
    async def analyze_research_paper_internal(document_url: str) -> str:
        """Internal function for research paper analysis."""
        global ocr_server
        
        try:
            # Use research paper schema
            research_schema = ocr_server.create_research_paper_schema()
            
            result = await ocr_server.process_document_annotation(
                document_url=document_url,
                pages=list(range(10)),  # Process more pages for research papers
                custom_schema=research_schema
            )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e), "status": "failed"}, indent=2)

if __name__ == "__main__":
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
        exit(1)
    
    # Check if API key is available
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("⚠️  MISTRAL_API_KEY not found. Server will run in mock mode.")
        print("Set your API key: export MISTRAL_API_KEY='your_key_here'")
    
    print("🚀 Starting Mistral OCR HTTP Server...")
    print("📡 Server will be available at http://localhost:3005")
    print("📄 Available endpoints:")
    print("   • GET  /                     - Server info")
    print("   • GET  /health               - Health check")
    print("   • POST /mcp/tools/list       - List MCP tools")
    print("   • POST /mcp/tools/call       - Call MCP tool")
    print("   • POST /api/document-annotation - Direct document annotation")
    print("   • POST /api/bbox-annotation     - Direct BBOX annotation")
    print("   • POST /api/full-annotation     - Direct full annotation")
    print("   • POST /api/research-paper      - Direct research paper analysis")
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",  # Bind to all interfaces for tunnel access
        port=3005,
        log_level="info"
    )

else:
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not available for HTTP server mode")
        app = None 