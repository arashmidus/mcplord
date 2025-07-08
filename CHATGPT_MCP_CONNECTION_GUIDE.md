# ChatGPT MCP Connection Guide

## 🎯 Quick Setup Summary

**✅ Working Servers:**
- **Playwright Browser Automation** → `http://localhost:3001` 
- **Memory Knowledge Graph** → `http://localhost:3002`

## 🚀 Step 1: Start MCP Servers

```bash
# In your mcp-agent-scaffolding directory
python start_mcp_servers_for_chatgpt.py
```

This will start servers in HTTP/SSE mode on these ports:
- **Port 3001**: Playwright (browser automation)
- **Port 3002**: Memory (persistent knowledge)

## 📱 Step 2: Connect in ChatGPT

### For Playwright Browser Automation:
1. **URL**: `http://localhost:3001`
2. **Label**: `playwright_browser_automation` (or any descriptive name)
3. **Authentication**: `None` or leave empty
4. Click **Connect**

### For Memory Knowledge Graph:
1. **URL**: `http://localhost:3002` 
2. **Label**: `memory_knowledge_graph` (or any descriptive name)
3. **Authentication**: `None` or leave empty
4. Click **Connect**

## ✨ What You Can Do with ChatGPT + MCP

### 🎭 Playwright Browser Automation
Ask ChatGPT to:
- **"Take a screenshot of https://example.com"**
- **"Fill out the contact form on this website"**
- **"Navigate to Google and search for 'AI news'"**
- **"Generate a PDF of this documentation page"**
- **"Click the login button and enter my credentials"**
- **"Scroll down and take another screenshot"**
- **"Open multiple tabs and compare websites"**
- **"Monitor network requests on this page"**

### 🧠 Memory Knowledge Graph
Ask ChatGPT to:
- **"Remember that I prefer Python over JavaScript"**
- **"Store this project information for later"**
- **"What did we discuss about the API design?"**
- **"Search for all conversations about database optimization"**
- **"Forget the outdated information about the old system"**

## 🔧 Server Management

### Start Servers
```bash
python start_mcp_servers_for_chatgpt.py
```

### Check if Servers are Running
```bash
# Check if ports are in use
lsof -i :3001  # Playwright
lsof -i :3002  # Memory
```

### Stop Servers
Press `Ctrl+C` in the terminal running the servers, or:
```bash
# Kill processes by port
kill $(lsof -t -i:3001)  # Stop Playwright
kill $(lsof -t -i:3002)  # Stop Memory
```

### Custom Configuration
Edit `start_mcp_servers_for_chatgpt.py` to:
- Change ports
- Add/remove servers
- Modify server options (headless mode, etc.)

## 🌐 Browser Automation Examples

### Basic Navigation
> "Navigate to https://news.ycombinator.com and take a screenshot"

### Form Interaction
> "Go to https://httpbin.org/forms/post, fill in the customer name as 'John Doe', phone as '555-1234', select 'large' size, and take a screenshot"

### Multi-step Automation
> "Navigate to GitHub, search for 'playwright', click the first result, and generate a PDF of the repository page"

### Data Extraction
> "Go to a weather website, find the current temperature for San Francisco, and remember this information"

## 🧠 Memory Examples

### Storing Information
> "Remember that our main API endpoint is https://api.example.com/v1 and we use JWT tokens for authentication"

### Retrieving Information
> "What API information did we store earlier?"

### Contextual Memory
> "Remember that this browser automation session is for testing the checkout flow on our e-commerce site"

## 🛠️ Troubleshooting

### Connection Issues
1. **"Can't connect to server"**
   - Ensure servers are running: `python start_mcp_servers_for_chatgpt.py`
   - Check URLs are exactly: `http://localhost:3001` and `http://localhost:3002`
   - No authentication required

2. **"Server not responding"**
   - Restart servers with Ctrl+C then re-run
   - Check for port conflicts: `lsof -i :3001 :3002`

3. **"Tools not available"**
   - Verify connection status in ChatGPT
   - Check server logs for errors

### Server Startup Issues
1. **"npx command not found"**
   ```bash
   # Install Node.js
   brew install node
   ```

2. **"@playwright/mcp not found"**
   ```bash
   # Install Playwright MCP
   npm install -g @playwright/mcp
   npx playwright install
   ```

3. **"Port already in use"**
   ```bash
   # Kill existing processes
   kill $(lsof -t -i:3001 :3002)
   ```

## 🔐 Security Notes

- Servers run on localhost only (not accessible from internet)
- No authentication required for local development
- Browser runs in sandboxed mode
- Memory data stored locally

## ⚡ Performance Tips

1. **Headless Mode**: Servers run in headless mode by default for better performance
2. **Keep Servers Running**: Don't restart unless necessary
3. **Memory Management**: Memory server persists data between sessions

## 🎨 Advanced Configurations

### Custom Playwright Options
Edit the server config in `start_mcp_servers_for_chatgpt.py`:
```python
"command": ["npx", "@playwright/mcp", "--port", "3001", "--headless", "--browser", "firefox"]
```

### Different Browser
```python
"command": ["npx", "@playwright/mcp", "--port", "3001", "--browser", "webkit"]
```

### Device Emulation
```python
"command": ["npx", "@playwright/mcp", "--port", "3001", "--device", "iPhone 15"]
```

### Vision Mode (AI Visual Analysis)
```python
"command": ["npx", "@playwright/mcp", "--port", "3001", "--vision"]
```

## 📊 Monitoring

The server manager provides real-time monitoring:
- ✅ Green status = Server running
- ❌ Red status = Server stopped
- Process IDs for debugging
- URLs for connection

## 🎯 Example Workflows

### 1. Web Research + Memory
```
1. "Navigate to https://research-site.com and search for 'AI trends 2024'"
2. "Take a screenshot of the results"
3. "Remember the key findings from this research"
4. "What AI trends did we find?"
```

### 2. E-commerce Testing
```
1. "Go to our staging site at https://staging.shop.com"
2. "Add a product to cart"
3. "Fill out checkout form with test data"
4. "Take screenshots of each step"
5. "Remember any issues found during this test"
```

### 3. Documentation Generation
```
1. "Navigate to our API docs at https://docs.api.com"
2. "Generate a PDF of the authentication section"
3. "Remember the API key requirements"
4. "Take screenshots of the code examples"
```

## 🚀 Next Steps

1. **Start the servers**: `python start_mcp_servers_for_chatgpt.py`
2. **Connect ChatGPT** using the URLs above
3. **Test with simple commands** like taking a screenshot
4. **Build complex workflows** combining browser automation and memory
5. **Explore advanced features** like multi-tab operations and form automation

---

**🎉 You're now ready to use ChatGPT with powerful browser automation and memory capabilities!** 