# Mistral OCR MCP Server Guide

This guide shows you how to set up and use the Mistral OCR MCP server with Claude Desktop, following the [official MCP quickstart pattern](https://modelcontextprotocol.io/quickstart/server).

## 🎯 What This Server Does

The Mistral OCR MCP server provides three powerful tools for analyzing PDF documents:

- **`process_pdf_document_annotation`**: Extract structured metadata (language, chapters, URLs, summary)
- **`process_pdf_bbox_annotation`**: Extract content descriptions for specific regions (charts, tables, etc.)
- **`analyze_research_paper`**: Specialized analysis for research papers with detailed extraction

## 📋 Prerequisites

1. **Python 3.10 or higher**
2. **Claude Desktop** (latest version)
3. **MCP SDK**: `pip install mcp`
4. **Optional**: Mistral API key for real OCR processing

## 🚀 Quick Setup

### Step 1: Install Dependencies

```bash
cd mcp-agent-scaffolding
pip install mcp mistralai
```

### Step 2: Test the Server

Test that the server works properly:

```bash
# Run from parent directory to avoid import conflicts
cd ..
python mcp-agent-scaffolding/mistral_ocr_mcp_server.py
```

You should see:
```
🚀 Starting Mistral OCR MCP Server...
⚠️  MISTRAL_API_KEY not found. Server will run in mock mode.
📄 Available tools:
   • process_pdf_document_annotation
   • process_pdf_bbox_annotation
   • analyze_research_paper
```

Press `Ctrl+C` to stop the server.

### Step 3: Configure Claude Desktop

Open your Claude Desktop configuration file:

**macOS/Linux:**
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
code %APPDATA%\Claude\claude_desktop_config.json
```

Add this configuration:

```json
{
  "mcpServers": {
    "mistral-ocr": {
      "command": "python",
      "args": [
        "/ABSOLUTE/PATH/TO/YOUR/mcplord/mcp-agent-scaffolding/mistral_ocr_mcp_server.py"
      ],
      "cwd": "/ABSOLUTE/PATH/TO/YOUR/mcplord"
    }
  }
}
```

**⚠️ Important:** 
- Replace `/ABSOLUTE/PATH/TO/YOUR/` with your actual path
- Use absolute paths, not relative paths
- The `cwd` setting ensures we run from the correct directory to avoid import conflicts

### Step 4: Restart Claude Desktop

After saving the configuration, **completely restart Claude Desktop**.

### Step 5: Test in Claude Desktop

1. Open Claude Desktop
2. Look for the "Search and tools" icon (⚙️) in the chat interface
3. You should see three tools listed:
   - process_pdf_document_annotation
   - process_pdf_bbox_annotation  
   - analyze_research_paper

Try asking Claude:
- "Analyze this research paper: https://arxiv.org/pdf/2301.00001.pdf"
- "What are the main sections in this document: [PDF URL]"

## 🔑 Using with Real Mistral API

To use real Mistral OCR processing instead of mock data:

1. Get a Mistral API key from [https://console.mistral.ai/](https://console.mistral.ai/)

2. Set the environment variable:
   ```bash
   export MISTRAL_API_KEY="your_key_here"
   ```

3. Or add it to your Claude Desktop config:
   ```json
   {
     "mcpServers": {
       "mistral-ocr": {
         "command": "python",
         "args": ["/ABSOLUTE/PATH/TO/mistral_ocr_mcp_server.py"],
         "cwd": "/ABSOLUTE/PATH/TO/mcplord",
         "env": {
           "MISTRAL_API_KEY": "your_key_here"
         }
       }
     }
   }
   ```

## 🧪 Testing the Tools

### Document Annotation Example

```
Ask Claude: "Extract the main structure from this paper: https://arxiv.org/pdf/2301.00001.pdf"
```

This will use `process_pdf_document_annotation` and return:
- Document language
- Chapter titles and sections
- URLs found in the document
- Brief summary
- Document type

### BBOX Annotation Example

```
Ask Claude: "Analyze the charts and tables in pages 1-3 of: https://arxiv.org/pdf/2301.00001.pdf"
```

This will use `process_pdf_bbox_annotation` and return:
- Content type for each region (chart, table, text, etc.)
- Short descriptions
- Detailed summaries of each region

### Research Paper Analysis Example

```
Ask Claude: "Give me a detailed analysis of this research paper: https://arxiv.org/pdf/2301.00001.pdf"
```

This will use `analyze_research_paper` and return:
- Paper title and authors
- Abstract
- Keywords
- Methodology
- Key findings
- References

## 🛠️ Troubleshooting

### Tools Not Showing Up

1. Check that MCP is installed: `pip install mcp`
2. Verify your configuration file path and syntax
3. Ensure you're using absolute paths
4. Restart Claude Desktop completely
5. Check Claude's logs:
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

### Import Errors

If you see `ModuleNotFoundError: No module named 'mcp.server'`:

1. Make sure you're running from the correct directory (with `cwd` setting)
2. The local `mcp/` folder might be conflicting with the installed package
3. Try running from the parent directory as shown in the setup

### Server Fails to Start

1. Check that Python can find all dependencies
2. Verify the file path in your configuration
3. Look at Claude's error logs for specific error messages

### Mock vs Real Mode

- **Mock mode**: Server runs without MISTRAL_API_KEY, returns example data
- **Real mode**: Requires valid API key, processes actual documents

The server will automatically detect which mode to use based on the API key.

## 📚 Example Usage Patterns

### Basic Document Analysis
```
"What's in this document: https://arxiv.org/pdf/paper.pdf"
```

### Targeted Page Analysis
```
"Analyze just the first 3 pages of: https://arxiv.org/pdf/paper.pdf"
```

### Chart and Table Extraction
```
"Extract all charts and tables from: https://arxiv.org/pdf/paper.pdf"
```

### Research Paper Deep Dive
```
"Give me a complete analysis of the methodology and findings in: https://arxiv.org/pdf/paper.pdf"
```

## 🔗 References

- [MCP Official Quickstart](https://modelcontextprotocol.io/quickstart/server)
- [Claude Desktop MCP Integration](https://modelcontextprotocol.io/quickstart/server#testing-your-server-with-claude-for-desktop)
- [Mistral OCR API Documentation](https://docs.mistral.ai/)

---

## 🎉 Success!

If everything is working, you should see the tools available in Claude Desktop and be able to analyze PDF documents using Mistral's OCR capabilities. The server supports both mock mode (for testing) and real API mode (with your Mistral API key). 