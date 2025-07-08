# Playwright MCP Server Guide

Microsoft's official Playwright MCP server provides advanced browser automation capabilities with 35+ tools for web interaction, testing, and automation.

## Quick Start

### 1. Install and Setup
```bash
# Run the automated setup
python run_playwright_setup.py

# Or run manually
python setup_playwright_mcp.py
```

### 2. Manual Installation (if needed)
```bash
# Install Node.js (if not already installed)
brew install node

# Install Playwright MCP server
npm install -g @playwright/mcp

# Install browser binaries
npx playwright install
```

## Available Capabilities

### Navigation & Page Control
- `browser_navigate` - Navigate to URLs
- `browser_back` - Go back in history
- `browser_forward` - Go forward in history
- `browser_reload` - Reload current page
- `browser_wait_for` - Wait for elements or conditions
- `browser_wait_for_navigation` - Wait for page navigation

### Element Interaction
- `browser_click` - Click on elements
- `browser_type` - Type text into elements
- `browser_fill` - Fill form fields
- `browser_select` - Select dropdown options
- `browser_scroll` - Scroll page or elements
- `browser_file_upload` - Upload files

### Visual Capture
- `browser_take_screenshot` - Take page screenshots
- `browser_snapshot` - Take visual snapshots with AI analysis
- `browser_pdf_save` - Generate PDFs from pages

### Tab Management
- `browser_tab_new` - Open new tabs
- `browser_tab_select` - Switch between tabs
- `browser_tab_close` - Close tabs

### Monitoring & Debugging
- `browser_network_requests` - Monitor network activity
- `browser_console_messages` - Capture console logs
- `browser_handle_dialog` - Handle alert/confirm dialogs

### Testing & Automation
- `browser_generate_playwright_test` - Generate test code
- Advanced element waiting and timing controls

## Configuration Options

The Playwright MCP server supports many configuration options:

```bash
# Headless mode (default is headed)
npx @playwright/mcp --headless

# Different browsers
npx @playwright/mcp --browser firefox
npx @playwright/mcp --browser webkit
npx @playwright/mcp --browser msedge

# Device emulation
npx @playwright/mcp --device "iPhone 15"

# Custom viewport
npx @playwright/mcp --viewport-size "1920,1080"

# With proxy
npx @playwright/mcp --proxy-server "http://proxy:8080"

# Save traces for debugging
npx @playwright/mcp --save-trace

# Vision mode (uses screenshots for AI analysis)
npx @playwright/mcp --vision
```

## Integration with MCP Agent Framework

### 1. Enable in Configuration
In `config/real_mcp_servers.yml`, the Playwright server is already configured:

```yaml
playwright:
  enabled: true
  description: "Advanced browser automation with 35+ tools"
  command: "npx"
  args: ["-y", "@playwright/mcp"]
  env: {}
  capabilities: ["tools", "resources"]
```

### 2. Connect in Agent Code
```python
from mcp.client.real_mcp_client import RealMCPClient, MCPServerConfigs

client = RealMCPClient()

# Connect to Playwright server
await client.connect_to_server(
    "playwright",
    *MCPServerConfigs.playwright()
)

# Take a screenshot
result = await client.call_tool("playwright", "browser_take_screenshot", {
    "path": "screenshot.png"
})
```

### 3. Example Agent Integration
```python
class WebAutomationAgent(BaseAgent):
    async def navigate_and_capture(self, url: str) -> str:
        """Navigate to a URL and take a screenshot."""
        
        # Navigate to URL
        await self.call_tool("playwright", "browser_navigate", {"url": url})
        
        # Wait for page to load
        await self.call_tool("playwright", "browser_wait_for", {
            "selector": "body",
            "timeout": 10000
        })
        
        # Take screenshot
        result = await self.call_tool("playwright", "browser_take_screenshot", {
            "path": f"capture_{int(time.time())}.png"
        })
        
        return f"Captured screenshot of {url}"
    
    async def fill_form(self, form_data: dict) -> str:
        """Fill out a web form."""
        for selector, value in form_data.items():
            await self.call_tool("playwright", "browser_fill", {
                "selector": selector,
                "value": value
            })
        
        return "Form filled successfully"
```

## Common Use Cases

### 1. Web Scraping
```python
# Navigate to page
await client.call_tool("playwright", "browser_navigate", {
    "url": "https://example.com/data"
})

# Wait for content
await client.call_tool("playwright", "browser_wait_for", {
    "selector": ".data-table",
    "timeout": 10000
})

# Take visual snapshot for AI analysis
await client.call_tool("playwright", "browser_snapshot", {
    "name": "data_extraction"
})
```

### 2. Form Automation
```python
# Fill multiple form fields
form_fields = {
    "input[name='username']": "user@example.com",
    "input[name='password']": "secure_password",
    "select[name='country']": "US"
}

for selector, value in form_fields.items():
    if selector.startswith("select"):
        await client.call_tool("playwright", "browser_select", {
            "selector": selector,
            "value": value
        })
    else:
        await client.call_tool("playwright", "browser_fill", {
            "selector": selector,
            "value": value
        })

# Submit form
await client.call_tool("playwright", "browser_click", {
    "selector": "button[type='submit']"
})
```

### 3. Testing Workflows
```python
# Generate test code
test_result = await client.call_tool("playwright", "browser_generate_playwright_test", {
    "actions": [
        {"action": "navigate", "url": "https://app.example.com"},
        {"action": "fill", "selector": "#username", "value": "testuser"},
        {"action": "click", "selector": "#login-button"},
        {"action": "wait", "selector": ".dashboard", "timeout": 5000},
        {"action": "screenshot", "path": "dashboard.png"}
    ]
})
```

### 4. PDF Generation
```python
# Navigate to content
await client.call_tool("playwright", "browser_navigate", {
    "url": "https://docs.example.com/report"
})

# Generate PDF
await client.call_tool("playwright", "browser_pdf_save", {
    "path": "report.pdf",
    "format": "A4",
    "printBackground": True
})
```

### 5. Multi-tab Workflows
```python
# Open new tab for comparison
await client.call_tool("playwright", "browser_tab_new", {})

# Navigate in new tab
await client.call_tool("playwright", "browser_navigate", {
    "url": "https://comparison.example.com"
})

# Switch back to original tab
await client.call_tool("playwright", "browser_tab_select", {"index": 0})
```

## Advanced Features

### Vision Mode
Enable vision mode for AI-powered visual analysis:
```bash
npx @playwright/mcp --vision
```

This allows the `browser_snapshot` tool to provide detailed visual analysis of page content.

### Network Monitoring
```python
# Monitor network requests
network_data = await client.call_tool("playwright", "browser_network_requests", {})

# Check for specific API calls
console_logs = await client.call_tool("playwright", "browser_console_messages", {})
```

### Device Emulation
```python
# Configure for mobile testing
# (This would be set in server startup, not via tools)
```

### Error Handling
```python
try:
    await client.call_tool("playwright", "browser_click", {
        "selector": "#missing-element"
    })
except Exception as e:
    # Handle element not found, timeout, etc.
    print(f"Click failed: {e}")
```

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Ensure Node.js is installed: `node --version`
   - Install Playwright MCP: `npm install -g @playwright/mcp`
   - Install browsers: `npx playwright install`

2. **Connection timeout**
   - Check if server is running: `npx @playwright/mcp --help`
   - Verify firewall settings
   - Try increasing timeout values

3. **Element not found**
   - Use `browser_wait_for` before interacting with elements
   - Check selectors with developer tools
   - Increase timeout values

4. **Screenshots are blank**
   - Ensure page is fully loaded
   - Use `browser_wait_for` with appropriate selectors
   - Check viewport size settings

### Debug Mode
Run the server with additional logging:
```bash
DEBUG=* npx @playwright/mcp
```

### Browser Developer Tools
When running in headed mode, you can use browser developer tools to inspect elements and test selectors.

## Performance Tips

1. **Use headless mode** for faster execution
2. **Reuse browser instances** when possible
3. **Use efficient selectors** (ID > class > complex selectors)
4. **Set appropriate timeouts** to avoid unnecessary waiting
5. **Batch operations** when interacting with multiple elements

## Security Considerations

1. **Allowed origins** - Configure allowed/blocked origins
2. **File uploads** - Be careful with file upload capabilities
3. **Network access** - Monitor and restrict network requests
4. **User data** - Use isolated browser profiles for sensitive operations

## Example: Complete Web Automation Agent

See `examples/playwright_demo.py` for a comprehensive example that demonstrates all major Playwright MCP capabilities.

## Next Steps

1. Run the setup script: `python run_playwright_setup.py`
2. Explore the interactive demos
3. Integrate Playwright tools into your agents
4. Build custom web automation workflows
5. Create testing and monitoring agents

For more advanced usage, refer to the official Playwright documentation and MCP specification. 