# Troubleshooting Guide for Mistral OCR MCP Server

## 🔍 Common Issues and Solutions

### 1. `spawn python ENOENT` Error

**Problem:** Claude Desktop can't find the Python executable.

**Solution:** Use the full path to your Python executable instead of just `python`.

```bash
# Find your Python path
which python

# Update your claude_desktop_config.json to use the full path
{
  "mcpServers": {
    "mistral-ocr": {
      "command": "/Users/astaneh/.pyenv/versions/3.11.9/bin/python",
      "args": ["/Users/astaneh/mcplord/mcp-agent-scaffolding/mistral_ocr_mcp_server.py"],
      "cwd": "/Users/astaneh/mcplord"
    }
  }
}
```

**Quick Fix:** Run the setup script:
```bash
cd mcp-agent-scaffolding
python setup_claude_config.py
```

### 2. `ModuleNotFoundError: No module named 'mcp.server'`

**Problem:** Import conflict with local `mcp` directory.

**Solution:** Make sure the `cwd` (current working directory) is set to the parent directory:

```json
{
  "mcpServers": {
    "mistral-ocr": {
      "command": "/path/to/python",
      "args": ["/path/to/mistral_ocr_mcp_server.py"],
      "cwd": "/Users/astaneh/mcplord"
    }
  }
}
```

### 3. Tools Not Showing Up in Claude Desktop

**Checklist:**
1. ✅ Restart Claude Desktop completely (quit and reopen)
2. ✅ Check configuration file syntax is valid JSON
3. ✅ Verify all paths are absolute (not relative)
4. ✅ Ensure MCP SDK is installed: `pip install mcp`
5. ✅ Test server manually: `python mistral_ocr_mcp_server.py`

### 4. Server Starts But Tools Don't Work

**Check Claude's logs:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Common causes:**
- Python dependencies missing
- Server crashes during tool execution
- API key issues (if using real Mistral API)

### 5. Mistral API Key Issues

**Mock Mode (No API Key):**
- Server runs with example data
- Good for testing setup
- No real OCR processing

**Real Mode (With API Key):**
```bash
export MISTRAL_API_KEY="your_key_here"
```

Or in configuration:
```json
{
  "mcpServers": {
    "mistral-ocr": {
      "command": "/path/to/python",
      "args": ["/path/to/mistral_ocr_mcp_server.py"],
      "cwd": "/Users/astaneh/mcplord",
      "env": {
        "MISTRAL_API_KEY": "your_key_here"
      }
    }
  }
}
```

## 🧪 Testing Your Setup

### 1. Test Server Manually
```bash
cd /Users/astaneh/mcplord
python mcp-agent-scaffolding/mistral_ocr_mcp_server.py
```

Should show:
```
🚀 Starting Mistral OCR MCP Server...
📄 Available tools:
   • process_pdf_document_annotation
   • process_pdf_bbox_annotation
   • analyze_research_paper
```

### 2. Test Configuration
```bash
# Check config file exists and is valid JSON
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
```

### 3. Test in Claude Desktop
1. Look for tools icon (⚙️) in chat interface
2. Should see 3 tools listed
3. Try: "Analyze this research paper: https://arxiv.org/pdf/2301.00001.pdf"

## 📋 Quick Diagnostic Commands

```bash
# Check Python path
which python

# Check MCP installation
pip show mcp

# Test server startup
cd /Users/astaneh/mcplord && python mcp-agent-scaffolding/mistral_ocr_mcp_server.py

# Check Claude logs
tail -f ~/Library/Logs/Claude/mcp*.log

# Validate config file
python -c "import json; print(json.load(open('/Users/astaneh/Library/Application Support/Claude/claude_desktop_config.json')))"
```

## 🔧 Reset Everything

If all else fails:

1. **Backup and reset config:**
   ```bash
   cd mcp-agent-scaffolding
   cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Desktop/claude_config_backup.json
   python setup_claude_config.py
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install --upgrade mcp mistralai
   ```

3. **Restart Claude Desktop completely**

## 🆘 Still Having Issues?

1. **Check the official MCP documentation:** https://modelcontextprotocol.io/docs/tools/debugging
2. **Verify your setup matches the working example in this repo**
3. **Check that your Python environment has all required packages**

## ✅ Working Configuration Example

Here's a known working configuration:

```json
{
  "mcpServers": {
    "mistral-ocr": {
      "command": "/Users/astaneh/.pyenv/versions/3.11.9/bin/python",
      "args": [
        "/Users/astaneh/mcplord/mcp-agent-scaffolding/mistral_ocr_mcp_server.py"
      ],
      "cwd": "/Users/astaneh/mcplord"
    }
  }
}
```

This configuration:
- ✅ Uses full Python path (no `python` command)
- ✅ Uses absolute paths for all files
- ✅ Sets correct working directory to avoid import conflicts
- ✅ Follows official MCP patterns 