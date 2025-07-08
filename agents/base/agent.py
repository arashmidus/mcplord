"""
Base Agent class implementing stateless agent patterns with MCP integration.

This module provides the foundational architecture for MCP-powered agents that:
- Request context via MCP rather than storing state
- Support autonomous loops and self-directed operation
- Enable runtime modularity and plugin-style architecture
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from mcp.client.mcp_client import MCPClient
from monitoring.metrics.agent_metrics import AgentMetrics
from coordination.state.context_bundle import ContextBundle


class AgentConfig(BaseModel):
    """Configuration for an agent instance."""
    
    name: str = Field(..., description="Unique agent name")
    description: str = Field(..., description="Agent purpose and capabilities")
    mcp_server_urls: List[str] = Field(default_factory=list, description="MCP servers to connect to")
    max_iterations: int = Field(default=10, description="Maximum autonomous loop iterations")
    sleep_interval: float = Field(default=1.0, description="Sleep between autonomous loop iterations")
    cost_limit: float = Field(default=10.0, description="Maximum cost per operation in USD")
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")
    log_level: str = Field(default="INFO", description="Logging level")


class AgentState(BaseModel):
    """Current state of an agent (minimal, mostly for coordination)."""
    
    agent_id: str
    status: str = "idle"  # idle, working, error, stopped
    current_task: Optional[str] = None
    last_activity: float = Field(default_factory=time.time)
    iteration_count: int = 0
    total_cost: float = 0.0


class BaseAgent(ABC):
    """
    Base class for MCP-powered stateless agents.
    
    This class implements the core patterns for MCP multi-agent systems:
    - Stateless operation with context fetching via MCP
    - Autonomous loops with self-directed operation
    - Runtime modularity through plugin architecture
    - Cost tracking and monitoring
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = str(uuid4())
        self.state = AgentState(agent_id=self.agent_id)
        
        # Setup logging
        self.logger = logging.getLogger(f"agent.{config.name}")
        self.logger.setLevel(getattr(logging, config.log_level))
        
        # Initialize components
        self.mcp_client = MCPClient(config.mcp_server_urls)
        self.metrics = AgentMetrics(self.agent_id, config.name)
        
        # Runtime flags
        self._running = False
        self._should_stop = False
        
    async def initialize(self) -> None:
        """Initialize the agent and establish MCP connections."""
        self.logger.info(f"Initializing agent {self.config.name} ({self.agent_id})")
        
        try:
            # Connect to MCP servers
            await self.mcp_client.connect()
            
            # Perform agent-specific initialization
            await self._initialize_agent()
            
            self.logger.info("Agent initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def start_autonomous_loop(self) -> None:
        """Start the autonomous agent loop."""
        if self._running:
            self.logger.warning("Agent is already running")
            return
            
        self.logger.info("Starting autonomous agent loop")
        self._running = True
        self.state.status = "working"
        
        try:
            while self._running and not self._should_stop:
                # Check cost limits
                if self.state.total_cost >= self.config.cost_limit:
                    self.logger.warning(f"Cost limit reached: ${self.state.total_cost:.2f}")
                    break
                
                # Check iteration limits
                if self.state.iteration_count >= self.config.max_iterations:
                    self.logger.info(f"Maximum iterations reached: {self.state.iteration_count}")
                    break
                
                # Execute one iteration
                await self._execute_iteration()
                
                # Update state
                self.state.iteration_count += 1
                self.state.last_activity = time.time()
                
                # Sleep between iterations
                await asyncio.sleep(self.config.sleep_interval)
                
        except Exception as e:
            self.logger.error(f"Error in autonomous loop: {e}")
            self.state.status = "error"
            raise
        finally:
            self._running = False
            if self.state.status != "error":
                self.state.status = "idle"
    
    async def stop(self) -> None:
        """Stop the agent gracefully."""
        self.logger.info("Stopping agent")
        self._should_stop = True
        
        # Wait for current iteration to complete
        while self._running:
            await asyncio.sleep(0.1)
        
        self.state.status = "stopped"
        await self.mcp_client.disconnect()
    
    async def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a single task with optional context.
        
        Args:
            task: Description of the task to execute
            context: Optional context data for the task
            
        Returns:
            Task execution result
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Executing task: {task}")
            self.state.current_task = task
            
            # Fetch context bundle from MCP
            context_bundle = await self._fetch_context_bundle(task, context)
            
            # Execute the task with context
            result = await self._execute_task_with_context(task, context_bundle)
            
            # Track metrics
            execution_time = time.time() - start_time
            self.metrics.record_task_execution(task, execution_time, result.get("success", False))
            
            # Update cost tracking
            cost = result.get("cost", 0.0)
            self.state.total_cost += cost
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            execution_time = time.time() - start_time
            self.metrics.record_task_execution(task, execution_time, False)
            raise
        finally:
            self.state.current_task = None
    
    async def _execute_iteration(self) -> None:
        """Execute one iteration of the autonomous loop."""
        # Fetch current context to determine what to do
        context_bundle = await self._fetch_context_bundle("autonomous_iteration")
        
        # Determine next action based on context
        action = await self._determine_next_action(context_bundle)
        
        if action:
            await self.execute_task(action, context_bundle.to_dict())
    
    async def _fetch_context_bundle(
        self, 
        task: str, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ContextBundle:
        """
        Fetch comprehensive context bundle from MCP servers.
        
        Args:
            task: The task requiring context
            additional_context: Additional context to include
            
        Returns:
            Rich context bundle with all relevant information
        """
        # Build context request
        context_request = {
            "agent_id": self.agent_id,
            "agent_name": self.config.name,
            "task": task,
            "timestamp": time.time(),
            "additional_context": additional_context or {}
        }
        
        # Fetch context from MCP servers
        context_data = await self.mcp_client.fetch_context(context_request)
        
        # Create context bundle
        return ContextBundle(
            agent_info={
                "id": self.agent_id,
                "name": self.config.name,
                "description": self.config.description
            },
            task_context={
                "task": task,
                "additional_context": additional_context or {}
            },
            shared_state=context_data.get("shared_state", {}),
            available_tools=context_data.get("tools", []),
            historical_context=context_data.get("history", []),
            coordination_info=context_data.get("coordination", {})
        )
    
    # Abstract methods that subclasses must implement
    
    @abstractmethod
    async def _initialize_agent(self) -> None:
        """Perform agent-specific initialization."""
        pass
    
    @abstractmethod
    async def _determine_next_action(self, context: ContextBundle) -> Optional[str]:
        """
        Determine the next action to take based on context.
        
        Args:
            context: Current context bundle
            
        Returns:
            Next action to execute, or None if no action needed
        """
        pass
    
    @abstractmethod
    async def _execute_task_with_context(
        self, 
        task: str, 
        context: ContextBundle
    ) -> Dict[str, Any]:
        """
        Execute a task with the provided context.
        
        Args:
            task: Task description
            context: Context bundle with all relevant information
            
        Returns:
            Task execution result including success status and any outputs
        """
        pass
    
    # Utility methods for subclasses
    
    async def _call_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call an MCP tool and track costs."""
        start_time = time.time()
        
        try:
            result = await self.mcp_client.call_tool(tool_name, **kwargs)
            
            # Track cost if provided
            if "cost" in result:
                self.state.total_cost += result["cost"]
                
            return result
            
        finally:
            execution_time = time.time() - start_time
            self.metrics.record_tool_call(tool_name, execution_time)
    
    async def _update_shared_state(self, key: str, value: Any) -> None:
        """Update shared state via MCP."""
        await self.mcp_client.update_state(self.agent_id, key, value)
    
    async def _get_shared_state(self, key: str) -> Any:
        """Get shared state via MCP."""
        return await self.mcp_client.get_state(key)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "status": self.state.status,
            "current_task": self.state.current_task,
            "iteration_count": self.state.iteration_count,
            "total_cost": self.state.total_cost,
            "last_activity": self.state.last_activity,
            "uptime": time.time() - self.state.last_activity if self._running else 0
        } 