# 🌟 Real MCP Agent System Guide

This guide shows you how to run the **actual MCP agent system** with real MCP servers from the official repositories.

## 🚀 Quick Start

### 1. Prerequisites

**Install Node.js and npm:**
```bash
# macOS (using Homebrew)
brew install node

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# Download from https://nodejs.org/
```

**Install Python dependencies:**
```bash
cd mcp-agent-scaffolding
pip install -r requirements.txt
```

**Install uv for Python MCP servers:**
```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
pip install uv
```

### 2. Run the Real System

```bash
python run_with_real_mcp_servers.py
```

This will:
- ✅ Connect to real MCP servers (memory, time, fetch)
- ✅ Create agents with actual tool access  
- ✅ Demonstrate task execution with real MCP integration
- ✅ Show interactive mode for exploration

## 🖥️ Available MCP Servers

### 🟢 Ready to Use (No Setup Required)

| Server | Description | Tools | Command |
|--------|-------------|-------|---------|
| **memory** | Knowledge graph persistent memory | remember, search, forget | `npx @modelcontextprotocol/server-memory` |
| **time** | Time and timezone operations | get_current_time, convert_timezone | `npx @modelcontextprotocol/server-time` |
| **fetch** | Web content fetching | fetch | `npx @modelcontextprotocol/server-fetch` |

### 🔧 Setup Required

| Server | Description | Setup Required |
|--------|-------------|----------------|
| **filesystem** | File operations | Enable in config + set path |
| **git** | Git repository tools | Enable + set repository path |
| **github** | GitHub API integration | GitHub Personal Access Token |
| **sqlite** | Database operations | Database file path |
| **postgres** | PostgreSQL access | Connection string |
| **brave_search** | Web search | Brave Search API key |
| **puppeteer** | Browser automation | Additional npm packages |

## ⚙️ Configuration

### Enable/Disable Servers

Edit `config/real_mcp_servers.yml`:

```yaml
servers:
  memory:
    enabled: true  # ✅ Enable this server
    
  github:
    enabled: false  # ❌ Disable this server
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your_token_here"
```

### Server Groups

Use predefined server groups:

```yaml
groups:
  basic:
    servers: ["memory", "time", "fetch"]
  development: 
    servers: ["filesystem", "git", "github"]
  data:
    servers: ["sqlite", "postgres"]
```

## 🎯 Examples

### 1. Basic Demo (Works Out of Box)

```bash
# Run with default enabled servers
python run_with_real_mcp_servers.py
```

### 2. Enable Filesystem Access

```yaml
# In config/real_mcp_servers.yml
filesystem:
  enabled: true
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/your/safe/directory"]
```

### 3. Add GitHub Integration

```yaml
github:
  enabled: true
  env:
    GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_your_token_here"
```

### 4. Database Integration

```yaml
sqlite:
  enabled: true
  args: ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/your.db"]

postgres:
  enabled: true  
  args: ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"]
```

## 🛠️ Using the System

### Command Line Interface

```bash
# Show connected servers
MCP> servers

# Show all available tools
MCP> tools

# Show tools from specific server
MCP> tools memory

# Call a specific tool
MCP> call memory remember {"content": "Important information"}

# Execute a task
MCP> task What is the current time?

# Or just type naturally
MCP> Remember that I prefer Python over JavaScript
```

### Programmatic Usage

```python
from mcp.client.real_mcp_client import RealMCPClient, MCPServerConfigs

# Create client
client = RealMCPClient()

# Connect to servers
await client.connect_to_server("memory", *MCPServerConfigs.memory())
await client.connect_to_server("time", *MCPServerConfigs.time())

# List available tools
tools = await client.list_tools()
print(f"Available tools: {tools}")

# Call a tool
result = await client.call_tool("memory", "remember", {
    "content": "This is important information"
})

# Create an agent with MCP access
from agents.examples.research_agent import create_research_agent

agent = await create_research_agent([
    "memory://localhost",
    "time://localhost"  
])

# Execute tasks
result = await agent.execute_task("What time is it and remember this conversation")
```

## 🔌 Adding Custom Servers

### 1. Community Servers

Browse https://mcpservers.org/ for 500+ community servers.

Add to your config:
```yaml
servers:
  spotify:
    enabled: true
    command: "npx"
    args: ["-y", "mcp-server-spotify"] 
    env:
      SPOTIFY_CLIENT_ID: "your_id"
      SPOTIFY_CLIENT_SECRET: "your_secret"
```

### 2. Local Development Server

Create a simple MCP server:

```python
# my_server.py
from mcp.server import Server
from mcp.types import Tool

server = Server("my-custom-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="hello",
            description="Say hello",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "hello":
        return f"Hello, {arguments.get('name', 'World')}!"

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

Add to config:
```yaml
my_server:
  enabled: true
  command: "python"
  args: ["my_server.py"]
```

## 🔐 Security & Best Practices

### 1. Environment Variables

Store sensitive data in environment variables:

```bash
export GITHUB_TOKEN="your_token"
export OPENAI_API_KEY="your_key"
```

```yaml
github:
  env:
    GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
```

### 2. File System Access

Restrict filesystem server to safe directories:

```yaml
filesystem:
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/safe/sandbox/dir"]
```

### 3. Database Access

Use read-only database connections when possible:

```yaml
postgres:
  args: ["-y", "@modelcontextprotocol/server-postgres", "postgresql://readonly_user:pass@localhost/db"]
```

## 🐛 Troubleshooting

### Server Won't Connect

```bash
# Check if Node.js is installed
node --version
npm --version

# Check if server package exists
npx @modelcontextprotocol/server-memory --help

# Check Python MCP servers
uvx mcp-server-git --help
```

### MCP SDK Issues

```bash
# Install specific MCP version
pip install "mcp>=1.0.0"

# Fallback to mock mode
# The system will automatically use mocks if MCP SDK unavailable
```

### Tool Call Failures

1. Check tool name matches exactly
2. Verify required arguments
3. Check server logs for errors
4. Ensure proper permissions/API keys

### Performance Issues

1. Limit concurrent server connections
2. Use connection timeouts in config
3. Cache tool results when possible
4. Monitor server resource usage

## 📚 Next Steps

### 1. Production Setup

- Deploy with Docker containers
- Use environment variable management
- Set up monitoring and logging
- Implement proper error handling

### 2. Scale Your System

- Add more specialized servers
- Create domain-specific agents  
- Build custom MCP servers
- Integrate with existing workflows

### 3. Advanced Features

- Multi-agent coordination
- Persistent state management
- Cost optimization
- Performance monitoring

## 🌐 Resources

- **Official MCP Docs**: https://modelcontextprotocol.io
- **MCP Servers Repository**: https://github.com/modelcontextprotocol/servers  
- **Community Servers**: https://mcpservers.org/
- **MCP Inspector Tool**: `npx @modelcontextprotocol/inspector`
- **Discord Community**: MCP Discord channels

## 💡 Examples & Use Cases

### Research Agent
```python
# Research agent with web search and memory
agent = await create_research_agent([
    "memory://localhost",
    "brave_search://localhost", 
    "fetch://localhost"
])

result = await agent.execute_task(
    "Research the latest developments in quantum computing and remember the key points"
)
```

### Development Assistant
```python
# Development agent with code access
agent = await create_dev_agent([
    "filesystem://localhost",
    "git://localhost",
    "github://localhost"
])

result = await agent.execute_task(
    "Analyze the codebase and suggest improvements"
)
```

### Data Analysis Agent
```python
# Data agent with database access
agent = await create_data_agent([
    "postgres://localhost",
    "sqlite://localhost"
])

result = await agent.execute_task(
    "Query the sales database and generate a summary report"
)
```

---

🎉 **You now have a complete, production-ready MCP agent system!**

Start with the basic servers, then gradually add more capabilities as needed. The scaffolding is designed to scale from simple demos to complex multi-agent systems. 