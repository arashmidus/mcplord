"""
Initialization script for MCP Agent Scaffolding

This script sets up the necessary configuration files, directories,
and environment for developing and testing MCP-powered multi-agent systems.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()


def create_directory_structure():
    """Create the required directory structure."""
    directories = [
        "config",
        "logs",
        "test_results",
        "data",
        "monitoring/dashboards",
        "monitoring/metrics", 
        "monitoring/tracing",
        "deploy/docker",
        "deploy/kubernetes"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        console.print(f"✓ Created directory: {directory}")


def create_agent_config() -> Dict[str, Any]:
    """Create agent configuration."""
    console.print("\n[bold]Agent Configuration[/bold]")
    
    config = {
        "agents": {
            "research_agent": {
                "name": "research_agent",
                "description": "Autonomous research agent for information gathering and analysis",
                "class": "agents.examples.research_agent.ResearchAgent",
                "config": {
                    "max_iterations": 20,
                    "sleep_interval": 2.0,
                    "cost_limit": 25.0,
                    "log_level": "INFO"
                }
            }
        },
        "default_config": {
            "max_iterations": 10,
            "sleep_interval": 1.0,
            "cost_limit": 10.0,
            "enable_tracing": True,
            "log_level": "INFO"
        }
    }
    
    return config


def create_mcp_server_config() -> Dict[str, Any]:
    """Create MCP server configuration."""
    console.print("\n[bold]MCP Server Configuration[/bold]")
    
    config = {
        "servers": {
            "context_server": {
                "url": "http://localhost:8001",
                "transport_type": "http",
                "enabled": True,
                "description": "Context management and shared state server"
            },
            "tools_server": {
                "url": "http://localhost:8002", 
                "transport_type": "http",
                "enabled": True,
                "description": "Tool execution server"
            },
            "coordination_server": {
                "url": "http://localhost:8003",
                "transport_type": "http", 
                "enabled": True,
                "description": "Agent coordination server"
            }
        },
        "client_config": {
            "timeout": 30.0,
            "retry_attempts": 3,
            "retry_delay": 1.0
        }
    }
    
    return config


def create_testing_config() -> Dict[str, Any]:
    """Create testing configuration."""
    console.print("\n[bold]Testing Configuration[/bold]")
    
    config = {
        "cost_aware_testing": {
            "budget_limit": 100.0,
            "default_sample_size": 10,
            "enable_semantic_validation": True,
            "results_dir": "test_results"
        },
        "semantic_validation": {
            "model_provider": "openai",
            "model_name": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 1000,
            "cost_per_token": 0.00003
        },
        "test_categories": {
            "unit": {
                "priority": 1,
                "budget_allocation": 0.1
            },
            "component": {
                "priority": 2,
                "budget_allocation": 0.4
            },
            "system": {
                "priority": 3,
                "budget_allocation": 0.5
            }
        }
    }
    
    return config


def create_monitoring_config() -> Dict[str, Any]:
    """Create monitoring configuration."""
    console.print("\n[bold]Monitoring Configuration[/bold]")
    
    config = {
        "metrics": {
            "enabled": True,
            "collection_interval": 30,
            "export_format": "prometheus",
            "export_endpoint": "http://localhost:9090"
        },
        "tracing": {
            "enabled": True,
            "service_name": "mcp-agent-system",
            "jaeger_endpoint": "http://localhost:14268/api/traces"
        },
        "logging": {
            "level": "INFO",
            "format": "structured",
            "output": "file",
            "log_file": "logs/mcp-agents.log",
            "rotate": True,
            "max_size": "10MB"
        },
        "alerts": {
            "cost_threshold": 50.0,
            "error_rate_threshold": 0.1,
            "response_time_threshold": 5.0
        }
    }
    
    return config


def create_environment_config() -> Dict[str, Any]:
    """Create environment configuration."""
    console.print("\n[bold]Environment Configuration[/bold]")
    
    # Ask for API keys
    openai_key = Prompt.ask("OpenAI API Key (optional, press Enter to skip)", default="")
    anthropic_key = Prompt.ask("Anthropic API Key (optional, press Enter to skip)", default="")
    
    config = {
        "development": {
            "mcp_servers": [
                "http://localhost:8001",
                "http://localhost:8002", 
                "http://localhost:8003"
            ],
            "database_url": "sqlite:///data/mcp_agents_dev.db",
            "redis_url": "redis://localhost:6379/0",
            "log_level": "DEBUG"
        },
        "testing": {
            "mcp_servers": [
                "http://localhost:18001",
                "http://localhost:18002",
                "http://localhost:18003"
            ],
            "database_url": "sqlite:///data/mcp_agents_test.db",
            "redis_url": "redis://localhost:6379/1",
            "log_level": "INFO"
        },
        "production": {
            "mcp_servers": [
                "http://mcp-context:8001",
                "http://mcp-tools:8002",
                "http://mcp-coordination:8003"
            ],
            "database_url": "postgresql://user:pass@db:5432/mcp_agents",
            "redis_url": "redis://redis:6379/0",
            "log_level": "WARNING"
        },
        "api_keys": {
            "openai_api_key": openai_key,
            "anthropic_api_key": anthropic_key
        }
    }
    
    return config


def create_docker_compose():
    """Create Docker Compose configuration."""
    docker_compose = {
        "version": "3.8",
        "services": {
            "context-server": {
                "build": ".",
                "command": "python mcp/servers/context_server.py",
                "ports": ["8001:8001"],
                "environment": [
                    "PYTHONPATH=/app"
                ],
                "volumes": [
                    "./logs:/app/logs",
                    "./data:/app/data"
                ]
            },
            "redis": {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"]
            },
            "prometheus": {
                "image": "prom/prometheus:latest",
                "ports": ["9090:9090"],
                "volumes": [
                    "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"
                ]
            },
            "jaeger": {
                "image": "jaegertracing/all-in-one:latest",
                "ports": [
                    "14268:14268",
                    "16686:16686"
                ]
            }
        }
    }
    
    return docker_compose


def create_dockerfile():
    """Create Dockerfile."""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs data test_results

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8001 8002 8003

# Default command
CMD ["python", "mcp/servers/context_server.py"]
"""
    
    return dockerfile_content


def create_gitignore():
    """Create .gitignore file."""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Test results
test_results/
.pytest_cache/
.coverage

# Data
data/
*.db
*.sqlite

# API Keys
.env
config/secrets.yml

# OS
.DS_Store
Thumbs.db

# Monitoring
monitoring/data/
"""
    
    return gitignore_content


def save_config_file(filename: str, config: Dict[str, Any], format_type: str = "yaml"):
    """Save configuration to file."""
    filepath = Path("config") / filename
    
    if format_type == "yaml":
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    elif format_type == "json":
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
    
    console.print(f"✓ Created config file: {filepath}")


@click.command()
@click.option("--interactive", "-i", is_flag=True, help="Interactive configuration setup")
@click.option("--minimal", "-m", is_flag=True, help="Create minimal configuration")
def init_config(interactive: bool, minimal: bool):
    """Initialize MCP Agent Scaffolding configuration."""
    
    console.print(Panel.fit(
        "[bold blue]MCP Agent Scaffolding Initialization[/bold blue]\n"
        "Setting up configuration for multi-agent development",
        border_style="blue"
    ))
    
    # Create directory structure
    console.print("\n[bold]Creating directory structure...[/bold]")
    create_directory_structure()
    
    # Create configuration files
    console.print("\n[bold]Creating configuration files...[/bold]")
    
    # Agent configuration
    agent_config = create_agent_config()
    save_config_file("agents.yml", agent_config)
    
    # MCP server configuration
    mcp_config = create_mcp_server_config()
    save_config_file("mcp_servers.yml", mcp_config)
    
    # Testing configuration
    if not minimal:
        testing_config = create_testing_config()
        save_config_file("testing.yml", testing_config)
        
        # Monitoring configuration
        monitoring_config = create_monitoring_config()
        save_config_file("monitoring.yml", monitoring_config)
    
    # Environment configuration
    if interactive:
        env_config = create_environment_config()
        save_config_file("environment.yml", env_config)
    
    # Docker configuration
    if not minimal:
        console.print("\n[bold]Creating Docker configuration...[/bold]")
        docker_compose = create_docker_compose()
        save_config_file("docker-compose.yml", docker_compose, "yaml")
        
        dockerfile_content = create_dockerfile()
        with open("Dockerfile", 'w') as f:
            f.write(dockerfile_content)
        console.print("✓ Created Dockerfile")
    
    # Git configuration
    gitignore_content = create_gitignore()
    with open(".gitignore", 'w') as f:
        f.write(gitignore_content)
    console.print("✓ Created .gitignore")
    
    # Summary
    console.print("\n" + "="*50)
    console.print("[bold green]Initialization Complete![/bold green]")
    console.print("="*50)
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Review and customize configuration files in config/")
    console.print("2. Set up environment variables (copy from config/environment.yml)")
    console.print("3. Install dependencies: pip install -r requirements.txt")
    console.print("4. Start MCP servers: python mcp/servers/context_server.py")
    console.print("5. Run tests: python testing/scenarios/test_research_agent.py")
    
    if not minimal:
        console.print("6. Start monitoring stack: docker-compose up -d prometheus jaeger")
        console.print("7. Access dashboards:")
        console.print("   - Prometheus: http://localhost:9090")
        console.print("   - Jaeger: http://localhost:16686")


if __name__ == "__main__":
    init_config() 