# MCP Multi-Agent Scaffolding

A production-ready framework for building, testing, and maintaining MCP-powered multi-agent systems.

## 🏗️ Architecture Overview

This scaffolding implements the recommended patterns for MCP multi-agent systems:

- **Stateless Agents**: Agents request context via MCP rather than storing state
- **Context Bundles**: Rich, structured context delivery
- **Autonomous Loops**: Self-directed agent operation
- **Runtime Modularity**: Plugin-style architecture for extensibility
- **Cost-Aware Testing**: Monitor and control testing expenses

## 📁 Project Structure

```
mcp-agent-scaffolding/
├── agents/                    # Agent implementations
│   ├── base/                 # Base agent classes and interfaces
│   ├── examples/             # Example agent implementations
│   └── registry/             # Agent registry and discovery
├── mcp/                      # MCP server implementations
│   ├── servers/              # Individual MCP servers
│   ├── client/               # MCP client utilities
│   └── protocols/            # Protocol definitions
├── testing/                  # Testing framework
│   ├── frameworks/           # Testing utilities and frameworks
│   ├── scenarios/            # Test scenario definitions
│   └── validators/           # Semantic validation tools
├── coordination/             # Agent coordination patterns
│   ├── orchestrators/        # Orchestration strategies
│   ├── protocols/            # Coordination protocols
│   └── state/                # Shared state management
├── monitoring/               # Observability and monitoring
│   ├── metrics/              # Performance metrics
│   ├── tracing/              # Distributed tracing
│   └── dashboards/           # Monitoring dashboards
├── config/                   # Configuration management
├── deploy/                   # Deployment configurations
├── docs/                     # Documentation
└── scripts/                  # Development and deployment scripts
```

## 🚀 Quick Start

### 1. Setup Environment

#### Option A: Automatic Setup (Recommended)
```bash
# Make setup script executable and run it
chmod +x run_setup.sh
./run_setup.sh
```

#### Option B: Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Set PYTHONPATH (important!)
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Initialize configuration
python scripts/init_config.py --minimal
```

### 2. Start MCP Servers

```bash
# Start the context management server
python mcp/servers/context_server.py &

# Start the coordination server
python mcp/servers/coordination_server.py &

# Start the monitoring server
python mcp/servers/monitoring_server.py &
```

### 3. Run Example Agents

```bash
# Start a simple example agent
python agents/examples/hello_world_agent.py

# Start a multi-agent workflow
python scripts/run_workflow.py --workflow examples/research_workflow
```

### 4. Run Tests

```bash
# Run unit tests
python -m pytest testing/unit/

# Run integration tests with cost monitoring
python testing/frameworks/cost_aware_runner.py --budget 50

# Run semantic validation tests
python testing/frameworks/semantic_validator.py --scenario testing/scenarios/basic_workflow.yaml
```

## 🧪 Testing Strategy

This framework implements a multi-layered testing approach specifically designed for MCP systems:

### Unit Level: Tool Testing
- Direct tool invocation bypassing LLM
- Traditional integration testing patterns
- Fast, deterministic, low-cost

### Component Level: Toolbox Testing  
- LLM + tool combinations
- Statistical success rate measurement
- Semantic validation with LLMs

### System Level: Workflow Testing
- End-to-end multi-agent scenarios
- Coordination and handoff validation
- Cost and performance monitoring

## 📊 Monitoring & Observability

- **Real-time Metrics**: Agent performance, MCP server health, coordination efficiency
- **Distributed Tracing**: Complete request flow across agents and MCP servers
- **Cost Tracking**: Token usage, API calls, and expenses per agent/workflow
- **Success Rate Analytics**: Statistical analysis of agent success patterns

## 🛠️ Development Workflow

1. **Agent Development**: Use base classes and patterns
2. **MCP Integration**: Leverage provided server templates
3. **Testing**: Multi-layered validation with cost awareness
4. **Monitoring**: Built-in observability and metrics
5. **Deployment**: Container-ready with scaling support

## 📚 Documentation

- [Agent Development Guide](docs/agent_development.md)
- [MCP Server Setup](docs/mcp_setup.md)
- [Testing Best Practices](docs/testing_guide.md)
- [Deployment Guide](docs/deployment.md)
- [API Reference](docs/api_reference.md)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and contribution process.

## 🔧 Troubleshooting

### Common Issues

**1. Module not found errors:**
```bash
# Make sure PYTHONPATH is set correctly
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Or install in development mode
pip install -e .
```

**2. sqlite3 installation error:**
- `sqlite3` is built into Python, remove it from requirements.txt if present

**3. MCP package not found:**
- The MCP package may not be available on PyPI yet
- Comment out the mcp line in requirements.txt for now
- The scaffolding provides mock implementations for testing

**4. Permission errors on setup script:**
```bash
chmod +x run_setup.sh
```

**5. Context server startup issues:**
```bash
# Make sure you're in the project root and PYTHONPATH is set
cd mcp-agent-scaffolding
export PYTHONPATH="$(pwd):$PYTHONPATH"
python mcp/servers/context_server.py
```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details. 