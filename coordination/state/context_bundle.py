"""
Context Bundle implementation for structured context delivery to MCP agents.

This module defines the ContextBundle class which packages rich, structured context
information for agents to consume, implementing the "context bundles" pattern.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextBundle(BaseModel):
    """
    Rich context bundle containing all relevant information for agent decision-making.
    
    This class implements the "context bundles" pattern where agents receive
    comprehensive, structured context rather than raw data.
    """
    
    # Agent information
    agent_info: Dict[str, Any] = Field(
        description="Information about the requesting agent"
    )
    
    # Task-specific context
    task_context: Dict[str, Any] = Field(
        description="Context specific to the current task"
    )
    
    # Shared state across agents
    shared_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Shared state accessible by all agents"
    )
    
    # Available tools and capabilities
    available_tools: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tools available for the agent to use"
    )
    
    # Historical context
    historical_context: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Relevant historical interactions and outcomes"
    )
    
    # Coordination information
    coordination_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Information about other agents and coordination state"
    )
    
    # Environmental context
    environment: Dict[str, Any] = Field(
        default_factory=dict,
        description="Environmental variables and system state"
    )
    
    # Constraints and policies
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Constraints, policies, and limits"
    )
    
    # Metadata
    timestamp: float = Field(default_factory=time.time)
    version: str = Field(default="1.0")
    
    def get_agent_id(self) -> str:
        """Get the requesting agent's ID."""
        return self.agent_info.get("id", "unknown")
    
    def get_agent_name(self) -> str:
        """Get the requesting agent's name."""
        return self.agent_info.get("name", "unknown")
    
    def get_task(self) -> str:
        """Get the current task description."""
        return self.task_context.get("task", "")
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool by name.
        
        Args:
            tool_name: Name of the tool to find
            
        Returns:
            Tool definition if found, None otherwise
        """
        for tool in self.available_tools:
            if tool.get("name") == tool_name:
                return tool
        return None
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if a specific tool is available."""
        return self.get_tool_by_name(tool_name) is not None
    
    def get_shared_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from shared state.
        
        Args:
            key: Key to look up
            default: Default value if key not found
            
        Returns:
            Value from shared state or default
        """
        return self.shared_state.get(key, default)
    
    def get_coordination_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from coordination info.
        
        Args:
            key: Key to look up
            default: Default value if key not found
            
        Returns:
            Value from coordination info or default
        """
        return self.coordination_info.get(key, default)
    
    def get_other_agents(self) -> List[Dict[str, Any]]:
        """Get information about other agents in the system."""
        return self.coordination_info.get("other_agents", [])
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get information about currently active agents."""
        return [
            agent for agent in self.get_other_agents()
            if agent.get("status") in ["working", "idle"]
        ]
    
    def get_constraint(self, constraint_type: str, default: Any = None) -> Any:
        """
        Get a specific constraint value.
        
        Args:
            constraint_type: Type of constraint to get
            default: Default value if constraint not found
            
        Returns:
            Constraint value or default
        """
        return self.constraints.get(constraint_type, default)
    
    def get_cost_limit(self) -> float:
        """Get the cost limit constraint."""
        return self.get_constraint("cost_limit", 10.0)
    
    def get_time_limit(self) -> Optional[float]:
        """Get the time limit constraint."""
        return self.get_constraint("time_limit")
    
    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent historical context entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent history entries
        """
        return self.historical_context[-limit:] if self.historical_context else []
    
    def get_history_by_type(self, entry_type: str) -> List[Dict[str, Any]]:
        """
        Get historical context entries of a specific type.
        
        Args:
            entry_type: Type of history entries to filter for
            
        Returns:
            Filtered history entries
        """
        return [
            entry for entry in self.historical_context
            if entry.get("type") == entry_type
        ]
    
    def add_context_annotation(self, key: str, value: Any) -> None:
        """
        Add an annotation to the task context.
        
        Args:
            key: Annotation key
            value: Annotation value
        """
        if "annotations" not in self.task_context:
            self.task_context["annotations"] = {}
        self.task_context["annotations"][key] = value
    
    def get_context_annotation(self, key: str, default: Any = None) -> Any:
        """
        Get a context annotation value.
        
        Args:
            key: Annotation key
            default: Default value if key not found
            
        Returns:
            Annotation value or default
        """
        annotations = self.task_context.get("annotations", {})
        return annotations.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the context bundle to a dictionary."""
        return self.model_dump()
    
    def to_summary(self) -> Dict[str, Any]:
        """
        Create a summary of the context bundle for logging or debugging.
        
        Returns:
            Summarized context information
        """
        return {
            "agent_id": self.get_agent_id(),
            "agent_name": self.get_agent_name(),
            "task": self.get_task(),
            "available_tools": [tool.get("name") for tool in self.available_tools],
            "shared_state_keys": list(self.shared_state.keys()),
            "coordination_agents": len(self.get_other_agents()),
            "history_entries": len(self.historical_context),
            "constraints": list(self.constraints.keys()),
            "timestamp": self.timestamp
        }
    
    @classmethod
    def create_minimal(
        cls,
        agent_id: str,
        agent_name: str,
        task: str,
        **kwargs
    ) -> "ContextBundle":
        """
        Create a minimal context bundle with basic information.
        
        Args:
            agent_id: ID of the requesting agent
            agent_name: Name of the requesting agent
            task: Task description
            **kwargs: Additional context data
            
        Returns:
            Minimal context bundle
        """
        return cls(
            agent_info={
                "id": agent_id,
                "name": agent_name
            },
            task_context={
                "task": task,
                **kwargs
            }
        )
    
    @classmethod
    def merge_bundles(
        cls,
        primary: "ContextBundle",
        secondary: "ContextBundle"
    ) -> "ContextBundle":
        """
        Merge two context bundles, with primary bundle taking precedence.
        
        Args:
            primary: Primary context bundle
            secondary: Secondary context bundle to merge from
            
        Returns:
            Merged context bundle
        """
        merged_data = secondary.model_dump()
        primary_data = primary.model_dump()
        
        # Merge dictionaries
        for key in ["shared_state", "coordination_info", "environment", "constraints"]:
            if key in merged_data and key in primary_data:
                merged_data[key].update(primary_data[key])
            elif key in primary_data:
                merged_data[key] = primary_data[key]
        
        # Merge lists
        for key in ["available_tools", "historical_context"]:
            if key in merged_data and key in primary_data:
                merged_data[key].extend(primary_data[key])
            elif key in primary_data:
                merged_data[key] = primary_data[key]
        
        # Override scalar values
        for key in ["agent_info", "task_context", "timestamp", "version"]:
            if key in primary_data:
                merged_data[key] = primary_data[key]
        
        return cls(**merged_data) 