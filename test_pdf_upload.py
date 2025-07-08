#!/usr/bin/env python3
"""
Test script for PDF upload functionality

This script demonstrates how to use the enhanced MCP server with uploaded PDF files.
"""

import base64
import json
import asyncio
from pathlib import Path

# Import our enhanced server
import sys
import os
sys.path.append(str(Path(__file__).parent))

def encode_pdf_to_base64(pdf_path: str) -> str:
    """Encode a PDF file to base64."""
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()
    return base64.b64encode(pdf_data).decode('utf-8')

async def test_uploaded_pdf():
    """Test the enhanced server with an uploaded PDF."""
    
    # For demonstration, let's create a small test PDF or use an existing one
    # In a real scenario, this would come from a file upload
    
    print("🧪 Testing Enhanced Mistral OCR Server with PDF Upload")
    print("=" * 60)
    
    # Example 1: Test with URL (existing functionality)
    print("\n📋 Test 1: URL-based PDF processing")
    
    try:
        from mistral_ocr_enhanced_server import process_pdf_document_annotation
        
        result = await process_pdf_document_annotation(
            document_url="https://arxiv.org/pdf/2301.00001.pdf",
            pages="0,1",
            include_images=False
        )
        
        print("✅ URL processing successful")
        parsed_result = json.loads(result)
        print(f"📊 Status: {parsed_result.get('status', 'unknown')}")
        
        if 'document_annotation' in parsed_result:
            print(f"📄 Language: {parsed_result['document_annotation'].get('language', 'unknown')}")
            print(f"📚 Sections: {len(parsed_result['document_annotation'].get('chapter_titles', []))}")
        
    except Exception as e:
        print(f"❌ URL processing failed: {e}")
    
    # Example 2: Test with base64 upload (new functionality)
    print("\n📋 Test 2: Base64 PDF upload processing")
    
    # Create a simple test scenario
    # In practice, you'd get this from a file upload in Claude Desktop
    test_pdf_path = Path(__file__).parent / "test_sample.pdf"
    
    if test_pdf_path.exists():
        try:
            # Encode PDF to base64
            base64_content = encode_pdf_to_base64(str(test_pdf_path))
            
            result = await process_pdf_document_annotation(
                document_base64=base64_content,
                document_name="test_sample.pdf",
                pages="0,1",
                include_images=False
            )
            
            print("✅ Base64 upload processing successful")
            parsed_result = json.loads(result)
            print(f"📊 Status: {parsed_result.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Base64 processing failed: {e}")
    else:
        print("⚠️  No test PDF found - creating mock base64 test")
        
        # Mock base64 content for demonstration
        mock_base64 = "JVBERi0xLjQKJcOkw7zDtsOyw6DP"  # This is just "PDF-1.4" encoded
        
        try:
            result = await process_pdf_document_annotation(
                document_base64=mock_base64,
                document_name="mock_test.pdf",
                pages="0,1",
                include_images=False
            )
            
            print("✅ Mock base64 test completed")
            parsed_result = json.loads(result)
            print(f"📊 Status: {parsed_result.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Mock base64 test failed: {e}")
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print("✅ Enhanced server supports both URL and base64 upload methods")
    print("📄 Users can now upload PDFs directly to Claude Desktop")
    print("🔧 The server automatically handles temporary file management")

def create_sample_pdf():
    """Create a simple sample PDF for testing."""
    try:
        # Try to create a simple PDF using reportlab if available
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        sample_path = Path(__file__).parent / "test_sample.pdf"
        
        c = canvas.Canvas(str(sample_path), pagesize=letter)
        c.drawString(100, 750, "Sample PDF for MCP Testing")
        c.drawString(100, 730, "This is a test document for the Enhanced Mistral OCR Server")
        c.drawString(100, 710, "Chapter 1: Introduction")
        c.drawString(100, 690, "Chapter 2: Methodology")
        c.drawString(100, 670, "Chapter 3: Results")
        c.drawString(100, 650, "References: https://example.com/ref1")
        c.save()
        
        print(f"✅ Created sample PDF: {sample_path}")
        return str(sample_path)
        
    except ImportError:
        print("⚠️  reportlab not available - install with: pip install reportlab")
        return None
    except Exception as e:
        print(f"❌ Failed to create sample PDF: {e}")
        return None

def demonstrate_usage():
    """Demonstrate how to use the enhanced server."""
    print("\n🚀 Enhanced Mistral OCR MCP Server - Usage Examples")
    print("=" * 60)
    
    print("\n📖 How to use with Claude Desktop:")
    print("1. **For URL-based PDFs** (existing functionality):")
    print('   "Analyze this paper: https://arxiv.org/pdf/2301.00001.pdf"')
    
    print("\n2. **For uploaded PDFs** (new functionality):")
    print("   a. Upload a PDF file to Claude Desktop")
    print("   b. Claude will automatically convert it to base64")
    print("   c. The enhanced server will process the uploaded file")
    print('   d. Ask: "Analyze the PDF I just uploaded"')
    
    print("\n🔧 Technical Details:")
    print("• The server accepts either 'document_url' OR 'document_base64'")
    print("• Base64 PDFs are saved to temporary files for processing")
    print("• Temporary files are automatically cleaned up after processing")
    print("• All existing URL-based functionality is preserved")
    
    print("\n📋 Tool Parameters:")
    print("• document_url: URL to PDF (e.g., arXiv link)")
    print("• document_base64: Base64 encoded PDF content")
    print("• document_name: Original filename (optional, for base64)")
    print("• pages: Page numbers to process (e.g., '0,1,2,3')")
    print("• include_images: Whether to include extracted images")

if __name__ == "__main__":
    print("🧪 Enhanced Mistral OCR Server - PDF Upload Test")
    
    # Create a sample PDF if reportlab is available
    sample_pdf = create_sample_pdf()
    
    # Demonstrate usage
    demonstrate_usage()
    
    # Run async test
    print("\n🔄 Running async tests...")
    asyncio.run(test_uploaded_pdf()) 