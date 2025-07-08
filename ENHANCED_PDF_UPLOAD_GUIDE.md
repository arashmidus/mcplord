# Enhanced Mistral OCR MCP Server - PDF Upload Guide

## 🎯 Overview

The **Enhanced Mistral OCR MCP Server** extends the original functionality to support both PDF URLs and **uploaded PDF files**. This means you can now upload PDFs directly to Claude Desktop and have them analyzed with Mistral's OCR capabilities!

## 🚀 New Features

### ✅ What's New
- **📤 PDF Upload Support**: Upload PDFs directly to Claude Desktop
- **🔄 Base64 Handling**: Automatic conversion and processing of uploaded files
- **🗂️ Temporary File Management**: Secure handling of uploaded files
- **⚡ Backward Compatible**: All existing URL functionality preserved

### 🔧 Enhanced Tools
All tools now support both `document_url` AND `document_base64` parameters:

1. **`process_pdf_document_annotation`** - Extract structured metadata
2. **`process_pdf_bbox_annotation`** - Extract content region descriptions  
3. **`analyze_research_paper`** - Specialized research paper analysis

## 📋 Setup Instructions

### 1. Install the Enhanced Server

```bash
cd mcp-agent-scaffolding
python setup_enhanced_server.py
```

This will:
- ✅ Test the enhanced server
- ✅ Update your Claude Desktop configuration
- ✅ Backup your existing config
- ✅ Add the new `mistral-ocr-enhanced` server

### 2. Restart Claude Desktop

**Important**: Completely restart Claude Desktop after setup!

### 3. Verify Installation

Look for the tools icon (⚙️) in Claude Desktop. You should see:
- `process_pdf_document_annotation` (enhanced)
- `process_pdf_bbox_annotation` (enhanced)
- `analyze_research_paper` (enhanced)

## 🎮 Usage Examples

### 📖 Method 1: URL-based PDFs (Existing)

```
"Analyze this research paper: https://arxiv.org/pdf/2301.00001.pdf"
```

### 📤 Method 2: Uploaded PDFs (NEW!)

1. **Upload a PDF file** to Claude Desktop using the attachment feature
2. **Ask Claude to analyze it**:
   ```
   "Analyze the PDF I just uploaded"
   "Extract the main sections from this document"
   "What are the key findings in this research paper?"
   ```

Claude will automatically:
- Convert the uploaded PDF to base64
- Pass it to the enhanced MCP server
- Process it with Mistral OCR
- Return structured annotations

## 🔧 Technical Details

### Input Parameters

**For URLs:**
```json
{
  "document_url": "https://arxiv.org/pdf/paper.pdf",
  "pages": "0,1,2,3",
  "include_images": false
}
```

**For Uploads:**
```json
{
  "document_base64": "JVBERi0xLjQK...",
  "document_name": "research_paper.pdf",
  "pages": "0,1,2,3",
  "include_images": false
}
```

### Processing Flow

1. **Upload Detection**: Server detects if input is URL or base64
2. **File Handling**: Base64 content is decoded and saved to temporary file
3. **Mistral Processing**: Document is processed with Mistral OCR API
4. **Cleanup**: Temporary files are automatically removed
5. **Response**: Structured annotations returned to Claude

### Security Features

- ✅ Temporary files are created in system temp directory
- ✅ Files are automatically cleaned up after processing
- ✅ Base64 validation prevents malformed uploads
- ✅ File size limits prevent abuse

## 📊 Output Examples

### Document Annotation
```json
{
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
    "summary": "This paper presents...",
    "document_type": "Research Paper"
  }
}
```

### BBOX Annotation
```json
{
  "bbox_annotations": [
    {
      "document_type": "chart",
      "short_description": "Performance comparison chart",
      "summary": "Chart showing model performance metrics"
    },
    {
      "document_type": "table",
      "short_description": "Results table",
      "summary": "Table containing numerical results"
    }
  ]
}
```

### Research Paper Analysis
```json
{
  "research_paper_annotation": {
    "title": "Advanced Machine Learning Techniques",
    "authors": ["Dr. Smith", "Dr. Johnson"],
    "abstract": "This paper explores...",
    "keywords": ["AI", "Machine Learning", "Deep Learning"],
    "sections": ["Abstract", "Introduction", "Methodology"],
    "methodology": "We used a novel approach...",
    "key_findings": [
      "Finding 1: Improved accuracy by 15%",
      "Finding 2: Reduced processing time"
    ],
    "references": ["Smith et al. 2023", "Johnson 2022"]
  }
}
```

## 🧪 Testing

### Test the Enhanced Server
```bash
python test_pdf_upload.py
```

### Test with Claude Desktop

1. **URL Test**:
   ```
   "Analyze this paper: https://arxiv.org/pdf/2301.00001.pdf"
   ```

2. **Upload Test**:
   - Upload a PDF file to Claude Desktop
   - Ask: "What are the main sections in this document?"

## 🔍 Troubleshooting

### Common Issues

**1. Tools not appearing in Claude Desktop**
- ✅ Restart Claude Desktop completely
- ✅ Check configuration file location
- ✅ Verify server path in config

**2. Upload processing fails**
- ✅ Check file size (keep under 10MB)
- ✅ Ensure PDF is valid format
- ✅ Check temporary directory permissions

**3. Mistral API errors**
- ✅ Set `MISTRAL_API_KEY` environment variable
- ✅ Server runs in mock mode without API key
- ✅ Check API quota and limits

### Debug Mode

Run the server directly to see detailed logs:
```bash
cd /path/to/mcplord
python mcp-agent-scaffolding/mistral_ocr_enhanced_server.py
```

## 📝 Configuration

### Claude Desktop Config

The enhanced server is configured in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mistral-ocr-enhanced": {
      "command": "python",
      "args": ["/path/to/mistral_ocr_enhanced_server.py"],
      "cwd": "/path/to/mcplord"
    }
  }
}
```

### Environment Variables

```bash
# Optional: Set your Mistral API key
export MISTRAL_API_KEY="your_api_key_here"

# Server runs in mock mode without API key
```

## 🎯 Best Practices

### For URLs
- ✅ Use direct PDF links (not HTML pages)
- ✅ Verify URLs are publicly accessible
- ✅ ArXiv links work great: `https://arxiv.org/pdf/XXXX.XXXX.pdf`

### For Uploads
- ✅ Keep files under 10MB for best performance
- ✅ Use descriptive filenames
- ✅ Ensure PDFs are text-based (not scanned images)

### Page Selection
- ✅ Use `"0,1,2,3"` for specific pages
- ✅ Use `"all"` for first 8 pages (default)
- ✅ Limit pages for faster processing

## 🔮 Future Enhancements

Potential improvements:
- 📷 Image OCR for scanned PDFs
- 🗂️ Multi-file batch processing
- 🎨 Enhanced annotation schemas
- 📊 Export to different formats

## 📞 Support

- 📖 Check the main [README.md](README.md) for general setup
- 🔧 Run `python setup_enhanced_server.py` to reconfigure
- 🧪 Use `python test_pdf_upload.py` to test functionality

---

**Ready to analyze your PDFs with both URLs and uploads!** 🚀 