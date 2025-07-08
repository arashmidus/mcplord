#!/bin/bash

# MCP Agent Scaffolding Setup Script
echo "🚀 Setting up MCP Agent Scaffolding..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install the package in development mode
echo "🛠️  Installing package in development mode..."
pip install -e .

# Set PYTHONPATH
export PYTHONPATH="${PWD}:${PYTHONPATH}"
echo "✅ PYTHONPATH set to: ${PYTHONPATH}"

# Initialize configuration
echo "⚙️  Initializing configuration..."
python scripts/init_config.py --minimal

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Set PYTHONPATH: export PYTHONPATH=\"\$(pwd):\$PYTHONPATH\""
echo "3. Start the context server: python mcp/servers/context_server.py"
echo "4. Run the demo: python scripts/run_demo.py"
echo ""
echo "For testing:"
echo "   python testing/scenarios/test_research_agent.py"
echo "" 