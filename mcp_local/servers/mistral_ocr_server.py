#!/usr/bin/env python3
"""
Mistral OCR Annotation MCP Server

This MCP server provides access to Mistral's OCR annotation capabilities,
allowing clients to process PDFs and extract structured data including:
- Document annotations (language, chapter titles, URLs)
- BBOX annotations (document type, descriptions, summaries)
- Base64 image extraction
"""

import asyncio
import os
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union

# Fix import path conflicts - remove current directory from sys.path
if '' in sys.path:
    sys.path.remove('')
if '.' in sys.path:
    sys.path.remove('.')

try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    try:
        # Alternative import for different MCP versions
        from mcp import create_server, Server
        from mcp.server.stdio import stdio_server
        from mcp.types import CallToolResult, TextContent, Tool
        MCP_AVAILABLE = True
    except ImportError:
        MCP_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MistralOCRServer:
    """MCP Server for Mistral OCR annotation capabilities."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found. Server will run in mock mode.")
            self.client = None
        else:
            if MISTRAL_AVAILABLE:
                try:
                    self.client = Mistral(api_key=self.api_key)
                    logger.info("Mistral client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Mistral client: {e}")
                    self.client = None
            else:
                logger.warning("Mistral AI library not available. Install with: pip install mistralai")
                self.client = None
    
    def create_document_annotation_schema(self) -> Dict[str, Any]:
        """Create the document annotation JSON schema."""
        return {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "properties": {
                        "language": {
                            "title": "Language",
                            "description": "The primary language of the document",
                            "type": "string"
                        },
                        "chapter_titles": {
                            "title": "Chapter_Titles",
                            "description": "List of chapter titles, headings, and section names found in the document",
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "urls": {
                            "title": "URLs",
                            "description": "List of URLs found in the document",
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "summary": {
                            "title": "Summary",
                            "description": "Brief summary of the document content",
                            "type": "string"
                        },
                        "document_type": {
                            "title": "Document_Type",
                            "description": "Type of document (research paper, manual, report, etc.)",
                            "type": "string"
                        }
                    },
                    "required": ["language", "chapter_titles", "urls"],
                    "title": "DocumentAnnotation",
                    "type": "object",
                    "additionalProperties": False
                },
                "name": "document_annotation",
                "strict": True
            }
        }
    
    def create_bbox_annotation_schema(self) -> Dict[str, Any]:
        """Create the BBOX annotation JSON schema."""
        return {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "properties": {
                        "document_type": {
                            "title": "Document_Type",
                            "description": "The type of content in this region (chart, table, text, image, etc.)",
                            "type": "string"
                        },
                        "short_description": {
                            "title": "Short_Description",
                            "description": "A brief description of the content in this region",
                            "type": "string"
                        },
                        "summary": {
                            "title": "Summary",
                            "description": "Detailed summary of the content in this region",
                            "type": "string"
                        }
                    },
                    "required": ["document_type", "short_description", "summary"],
                    "title": "BBOXAnnotation",
                    "type": "object",
                    "additionalProperties": False
                },
                "name": "bbox_annotation",
                "strict": True
            }
        }
    
    def create_research_paper_schema(self) -> Dict[str, Any]:
        """Create a specialized schema for research papers."""
        return {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "properties": {
                        "title": {"title": "Title", "description": "The title of the paper", "type": "string"},
                        "authors": {"title": "Authors", "description": "List of authors", "type": "array", "items": {"type": "string"}},
                        "abstract": {"title": "Abstract", "description": "The abstract of the paper", "type": "string"},
                        "keywords": {"title": "Keywords", "description": "Keywords or key terms", "type": "array", "items": {"type": "string"}},
                        "sections": {"title": "Sections", "description": "Main sections of the paper", "type": "array", "items": {"type": "string"}},
                        "methodology": {"title": "Methodology", "description": "Description of the methodology used", "type": "string"},
                        "key_findings": {"title": "Key_Findings", "description": "Main findings or results", "type": "array", "items": {"type": "string"}},
                        "references": {"title": "References", "description": "Key references cited", "type": "array", "items": {"type": "string"}},
                        "language": {"title": "Language", "description": "Language of the document", "type": "string"}
                    },
                    "required": ["title", "language", "sections"],
                    "title": "ResearchPaperAnnotation",
                    "type": "object",
                    "additionalProperties": False
                },
                "name": "research_paper_annotation",
                "strict": True
            }
        }
    
    async def process_document_annotation(
        self,
        document_url: str,
        pages: Optional[List[int]] = None,
        include_image_base64: bool = False,
        custom_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process document with annotation extraction."""
        if not self.client:
            return await self._mock_document_annotation(document_url, pages)
        
        try:
            # Use custom schema or default
            annotation_schema = custom_schema or self.create_document_annotation_schema()
            
            # Set default pages if not specified
            if pages is None:
                pages = list(range(8))  # Default to first 8 pages
            
            logger.info(f"Processing document annotation for {document_url}, pages: {pages}")
            
            # Make API call
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.ocr.process(
                    model="mistral-ocr-latest",
                    document={"document_url": document_url},
                    pages=pages,
                    document_annotation_format=annotation_schema,
                    include_image_base64=include_image_base64
                )
            )
            
            logger.info("Document annotation completed successfully")
            return response.dict() if hasattr(response, 'dict') else response
            
        except Exception as e:
            logger.error(f"Document annotation failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def process_bbox_annotation(
        self,
        document_url: str,
        pages: Optional[List[int]] = None,
        include_image_base64: bool = False,
        custom_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process document with BBOX annotation extraction."""
        if not self.client:
            return await self._mock_bbox_annotation(document_url, pages)
        
        try:
            # Use custom schema or default
            bbox_schema = custom_schema or self.create_bbox_annotation_schema()
            
            # Set default pages if not specified
            if pages is None:
                pages = list(range(8))  # Default to first 8 pages
            
            logger.info(f"Processing BBOX annotation for {document_url}, pages: {pages}")
            
            # Make API call
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.ocr.process(
                    model="mistral-ocr-latest",
                    document={"document_url": document_url},
                    pages=pages,
                    bbox_annotation_format=bbox_schema,
                    include_image_base64=include_image_base64
                )
            )
            
            logger.info("BBOX annotation completed successfully")
            return response.dict() if hasattr(response, 'dict') else response
            
        except Exception as e:
            logger.error(f"BBOX annotation failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def process_full_annotation(
        self,
        document_url: str,
        pages: Optional[List[int]] = None,
        include_image_base64: bool = True
    ) -> Dict[str, Any]:
        """Process document with both document and BBOX annotations."""
        if not self.client:
            return await self._mock_full_annotation(document_url, pages)
        
        try:
            # Set default pages if not specified
            if pages is None:
                pages = list(range(8))  # Default to first 8 pages
            
            logger.info(f"Processing full annotation for {document_url}, pages: {pages}")
            
            # Make API call with both annotation types
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.ocr.process(
                    model="mistral-ocr-latest",
                    document={"document_url": document_url},
                    pages=pages,
                    document_annotation_format=self.create_document_annotation_schema(),
                    bbox_annotation_format=self.create_bbox_annotation_schema(),
                    include_image_base64=include_image_base64
                )
            )
            
            logger.info("Full annotation completed successfully")
            return response.dict() if hasattr(response, 'dict') else response
            
        except Exception as e:
            logger.error(f"Full annotation failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    # Mock implementations for when Mistral API is not available
    async def _mock_document_annotation(self, document_url: str, pages: Optional[List[int]]) -> Dict[str, Any]:
        """Mock document annotation for testing."""
        return {
            "document_annotation": {
                "language": "English",
                "chapter_titles": [
                    "Abstract",
                    "1 Introduction", 
                    "2 Methodology",
                    "3 Results",
                    "4 Conclusion"
                ],
                "urls": [
                    "https://example.com/reference1",
                    "https://example.com/reference2"
                ],
                "summary": f"Mock analysis of document: {document_url}",
                "document_type": "Research Paper"
            },
            "pages_processed": pages or list(range(8)),
            "status": "mock_success"
        }
    
    async def _mock_bbox_annotation(self, document_url: str, pages: Optional[List[int]]) -> Dict[str, Any]:
        """Mock BBOX annotation for testing."""
        return {
            "bbox_annotations": [
                {
                    "document_type": "chart",
                    "short_description": "Performance comparison chart",
                    "summary": "A chart showing performance metrics across different models"
                },
                {
                    "document_type": "table",
                    "short_description": "Results table",
                    "summary": "Table containing numerical results and statistics"
                }
            ],
            "pages_processed": pages or list(range(8)),
            "status": "mock_success"
        }
    
    async def _mock_full_annotation(self, document_url: str, pages: Optional[List[int]]) -> Dict[str, Any]:
        """Mock full annotation for testing."""
        doc_annotation = await self._mock_document_annotation(document_url, pages)
        bbox_annotation = await self._mock_bbox_annotation(document_url, pages)
        
        return {
            **doc_annotation,
            **bbox_annotation,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGB...",
            "status": "mock_success"
        }

# Initialize the OCR server
ocr_server = MistralOCRServer()

async def process_pdf_document_annotation(
    document_url: str,
    pages: Optional[str] = None,
    include_images: bool = False
) -> str:
    """
    Extract structured annotations from a PDF document using Mistral OCR.
    
    Args:
        document_url: URL to the PDF document (e.g., https://arxiv.org/pdf/paper.pdf)
        pages: Comma-separated page numbers to process (e.g., "0,1,2,3" or "all" for first 8)
        include_images: Whether to include base64 encoded images in response
    
    Returns:
        JSON string containing document annotations (language, chapters, URLs, summary)
    """
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

async def process_pdf_bbox_annotation(
    document_url: str,
    pages: Optional[str] = None,
    include_images: bool = False
) -> str:
    """
    Extract BBOX annotations from a PDF document using Mistral OCR.
    
    Args:
        document_url: URL to the PDF document
        pages: Comma-separated page numbers to process (e.g., "0,1,2,3" or "all" for first 8)
        include_images: Whether to include base64 encoded images in response
    
    Returns:
        JSON string containing BBOX annotations (content type, descriptions, summaries for each region)
    """
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

async def process_pdf_full_annotation(
    document_url: str,
    pages: Optional[str] = None
) -> str:
    """
    Extract complete annotations (both document and BBOX) from a PDF using Mistral OCR.
    
    Args:
        document_url: URL to the PDF document
        pages: Comma-separated page numbers to process (e.g., "0,1,2,3" or "all" for first 8)
    
    Returns:
        JSON string containing both document and BBOX annotations plus base64 images
    """
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

async def analyze_research_paper(document_url: str) -> str:
    """
    Specialized tool for analyzing research papers with custom annotation schema.
    
    Args:
        document_url: URL to the research paper PDF
    
    Returns:
        JSON string with detailed research paper analysis
    """
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

# Simple server for stdio mode
if __name__ == "__main__":
    import sys
    
    # Check if API key is available
    if not os.getenv("MISTRAL_API_KEY"):
        print("⚠️  MISTRAL_API_KEY not found. Server will run in mock mode.", file=sys.stderr)
        print("Set your API key: export MISTRAL_API_KEY='your_key_here'", file=sys.stderr)
    
    print("🚀 Starting Mistral OCR Annotation MCP Server...", file=sys.stderr)
    print("📄 Available tools:", file=sys.stderr)
    print("   • process_pdf_document_annotation", file=sys.stderr)
    print("   • process_pdf_bbox_annotation", file=sys.stderr)
    print("   • process_pdf_full_annotation", file=sys.stderr)
    print("   • analyze_research_paper", file=sys.stderr)
    
    # Create basic server for stdio mode
    if MCP_AVAILABLE:
        try:
            from mcp.server import Server
            from mcp.server.stdio import stdio_server
            from mcp.types import CallToolResult, TextContent, Tool
            
            server = Server("mistral-ocr-server")
            
            @server.call_tool()
            async def call_tool(name: str, arguments: dict) -> CallToolResult:
                """Handle tool calls."""
                try:
                    if name == "process_pdf_document_annotation":
                        result = await process_pdf_document_annotation(**arguments)
                    elif name == "process_pdf_bbox_annotation":
                        result = await process_pdf_bbox_annotation(**arguments)
                    elif name == "process_pdf_full_annotation":
                        result = await process_pdf_full_annotation(**arguments)
                    elif name == "analyze_research_paper":
                        result = await analyze_research_paper(**arguments)
                    else:
                        result = json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
                    
                    return CallToolResult(content=[TextContent(type="text", text=result)])
                    
                except Exception as e:
                    error_result = json.dumps({"error": str(e), "status": "failed"}, indent=2)
                    return CallToolResult(content=[TextContent(type="text", text=error_result)])
            
            @server.list_tools()
            async def list_tools() -> list[Tool]:
                """List available tools."""
                return [
                    Tool(
                        name="process_pdf_document_annotation",
                        description="Extract structured annotations from a PDF document using Mistral OCR",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_url": {"type": "string", "description": "URL to the PDF document"},
                                "pages": {"type": "string", "description": "Comma-separated page numbers or 'all'"},
                                "include_images": {"type": "boolean", "description": "Include base64 images"}
                            },
                            "required": ["document_url"]
                        }
                    ),
                    Tool(
                        name="process_pdf_bbox_annotation",
                        description="Extract BBOX annotations from a PDF document using Mistral OCR",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_url": {"type": "string", "description": "URL to the PDF document"},
                                "pages": {"type": "string", "description": "Comma-separated page numbers or 'all'"},
                                "include_images": {"type": "boolean", "description": "Include base64 images"}
                            },
                            "required": ["document_url"]
                        }
                    ),
                    Tool(
                        name="process_pdf_full_annotation",
                        description="Extract complete annotations from a PDF using Mistral OCR",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_url": {"type": "string", "description": "URL to the PDF document"},
                                "pages": {"type": "string", "description": "Comma-separated page numbers or 'all'"}
                            },
                            "required": ["document_url"]
                        }
                    ),
                    Tool(
                        name="analyze_research_paper",
                        description="Specialized analysis for research papers",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_url": {"type": "string", "description": "URL to the research paper PDF"}
                            },
                            "required": ["document_url"]
                        }
                    )
                ]
            
            async def main():
                async with stdio_server() as (read_stream, write_stream):
                    await server.run(read_stream, write_stream, server.create_initialization_options())
            
            asyncio.run(main())
            
        except Exception as e:
            print(f"❌ Error starting server: {e}", file=sys.stderr)
            print("Running in basic mode...", file=sys.stderr)
    else:
        print("❌ MCP library not available. Install with: pip install mcp", file=sys.stderr) 