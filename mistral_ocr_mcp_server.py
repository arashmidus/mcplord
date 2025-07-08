#!/usr/bin/env python3
"""
Mistral OCR MCP Server - Following Official MCP Pattern

This MCP server provides access to Mistral's OCR annotation capabilities,
following the official MCP pattern for Claude Desktop integration.
"""

import asyncio
import os
import json
import logging
import sys
from typing import Any, Dict, List, Optional

# Fix import path conflicts - remove current directory from sys.path
if '' in sys.path:
    sys.path.remove('')
if '.' in sys.path:
    sys.path.remove('.')

# Import MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolResult, TextContent, Tool
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Error: MCP SDK not available. Install with: pip install mcp", file=sys.stderr)
    print(f"Import error: {e}", file=sys.stderr)
    MCP_AVAILABLE = False
    sys.exit(1)

# Import Mistral AI (optional)
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

# Set up logging to stderr only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
def load_env_file():
    """Load environment variables from .env file."""
    from pathlib import Path
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"\'')
                        os.environ[key] = value
            logger.info("Loaded environment variables from .env file")
        except Exception as e:
            logger.warning(f"Error loading .env file: {e}")

# Load .env file first
load_env_file()

# Initialize Mistral client
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
mistral_client = None

if MISTRAL_API_KEY and MISTRAL_AVAILABLE:
    try:
        mistral_client = Mistral(api_key=MISTRAL_API_KEY)
        logger.info("Mistral client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Mistral client: {e}")
else:
    logger.warning("MISTRAL_API_KEY not found or Mistral not available. Server will run in mock mode.")

def create_document_annotation_schema() -> Dict[str, Any]:
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

# Tool implementations

async def process_pdf_document_annotation(
    document_url: str,
    pages: Optional[str] = None,
    include_images: bool = False
) -> str:
    """Extract structured annotations from a PDF document using Mistral OCR.

    Args:
        document_url: URL to the PDF document (e.g., https://arxiv.org/pdf/paper.pdf)
        pages: Comma-separated page numbers to process (e.g., "0,1,2,3" or "all" for first 8)
        include_images: Whether to include base64 encoded images in response
    """
    try:
        # Parse pages
        page_list = None
        if pages and pages.lower() != "all":
            page_list = [int(p.strip()) for p in pages.split(",")]
        else:
            page_list = list(range(8))  # Default to first 8 pages
        
        if mistral_client:
            # Real Mistral API call
            logger.info(f"Processing document annotation for {document_url}, pages: {page_list}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: mistral_client.ocr.process(
                    model="mistral-ocr-latest",
                    document={"document_url": document_url},
                    pages=page_list,
                    document_annotation_format=create_document_annotation_schema(),
                    include_image_base64=include_images
                )
            )
            
            result = response.dict() if hasattr(response, 'dict') else response
            logger.info("Document annotation completed successfully")
        else:
            # Mock response
            result = {
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
                "pages_processed": page_list,
                "status": "mock_success"
            }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Document annotation failed: {e}")
        return json.dumps({"error": str(e), "status": "failed"}, indent=2)

async def process_pdf_bbox_annotation(
    document_url: str,
    pages: Optional[str] = None,
    include_images: bool = False
) -> str:
    """Extract BBOX annotations from a PDF document using Mistral OCR.

    Args:
        document_url: URL to the PDF document
        pages: Comma-separated page numbers to process (e.g., "0,1,2,3" or "all" for first 8)
        include_images: Whether to include base64 encoded images in response
    """
    try:
        # Parse pages
        page_list = None
        if pages and pages.lower() != "all":
            page_list = [int(p.strip()) for p in pages.split(",")]
        else:
            page_list = list(range(8))  # Default to first 8 pages
        
        bbox_schema = {
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
        
        if mistral_client:
            # Real Mistral API call
            logger.info(f"Processing BBOX annotation for {document_url}, pages: {page_list}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: mistral_client.ocr.process(
                    model="mistral-ocr-latest",
                    document={"document_url": document_url},
                    pages=page_list,
                    bbox_annotation_format=bbox_schema,
                    include_image_base64=include_images
                )
            )
            
            result = response.dict() if hasattr(response, 'dict') else response
            logger.info("BBOX annotation completed successfully")
        else:
            # Mock response
            result = {
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
                "pages_processed": page_list,
                "status": "mock_success"
            }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"BBOX annotation failed: {e}")
        return json.dumps({"error": str(e), "status": "failed"}, indent=2)

async def analyze_research_paper(document_url: str) -> str:
    """Specialized tool for analyzing research papers with detailed extraction.

    Args:
        document_url: URL to the research paper PDF
    """
    try:
        research_schema = {
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
        
        if mistral_client:
            logger.info(f"Analyzing research paper: {document_url}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: mistral_client.ocr.process(
                    model="mistral-ocr-latest",
                    document={"document_url": document_url},
                    pages=list(range(10)),  # Process more pages for research papers
                    document_annotation_format=research_schema
                )
            )
            
            result = response.dict() if hasattr(response, 'dict') else response
            logger.info("Research paper analysis completed successfully")
        else:
            # Mock response
            result = {
                "research_paper_annotation": {
                    "title": f"Mock Analysis of {document_url}",
                    "authors": ["Author One", "Author Two"],
                    "abstract": "This is a mock abstract for testing purposes.",
                    "keywords": ["AI", "Machine Learning", "Research"],
                    "sections": ["Abstract", "Introduction", "Methodology", "Results", "Conclusion"],
                    "methodology": "Mock methodology description",
                    "key_findings": [
                        "Finding 1: Mock finding for testing",
                        "Finding 2: Another mock finding"
                    ],
                    "references": ["Reference 1", "Reference 2"],
                    "language": "English"
                },
                "status": "mock_success"
            }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Research paper analysis failed: {e}")
        return json.dumps({"error": str(e), "status": "failed"}, indent=2)

# Create the MCP server
server = Server("mistral-ocr")

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "process_pdf_document_annotation":
            result = await process_pdf_document_annotation(**arguments)
        elif name == "process_pdf_bbox_annotation":
            result = await process_pdf_bbox_annotation(**arguments)
        elif name == "analyze_research_paper":
            result = await analyze_research_paper(**arguments)
        else:
            result = json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
        
        return CallToolResult(content=[TextContent(type="text", text=result)])
        
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
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

# Main execution
async def main():
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Print server info to stderr (so it doesn't interfere with MCP protocol)
    print("🚀 Starting Mistral OCR MCP Server...", file=sys.stderr)
    if not MISTRAL_API_KEY:
        print("⚠️  MISTRAL_API_KEY not found. Server will run in mock mode.", file=sys.stderr)
        print("Set your API key: export MISTRAL_API_KEY='your_key_here'", file=sys.stderr)
    
    print("📄 Available tools:", file=sys.stderr)
    print("   • process_pdf_document_annotation", file=sys.stderr)
    print("   • process_pdf_bbox_annotation", file=sys.stderr)
    print("   • analyze_research_paper", file=sys.stderr)
    
    # Run the server
    asyncio.run(main()) 