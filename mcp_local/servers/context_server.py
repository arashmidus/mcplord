"""
MCP Context Server

A basic MCP server that provides context management and shared state
for multi-agent systems. This server implements the context bundle
pattern and coordinates between agents.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from coordination.state.context_bundle import ContextBundle


class ContextRequest(BaseModel):
    """Request for context information."""
    agent_id: str
    agent_name: str
    task: str
    timestamp: float
    additional_context: Optional[Dict[str, Any]] = None


class StateUpdate(BaseModel):
    """Update to shared state."""
    agent_id: str
    key: str
    value: Any
    timestamp: float


class ContextServer:
    """
    MCP Context Server that manages shared state and context for agents.
    
    This server provides:
    - Shared state management
    - Context bundle creation
    - Agent coordination information
    - Historical context tracking
    """
    
    def __init__(self):
        self.shared_state: Dict[str, Any] = {}
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        self.context_history: List[Dict[str, Any]] = []
        self.tools_registry: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.max_history_entries = 1000
        self.cleanup_interval = 300  # 5 minutes
        
        self.logger = logging.getLogger("mcp.context_server")
        
        # Initialize cleanup task reference (will be started when server runs)
        self._cleanup_task = None
    
    async def get_context(self, request: ContextRequest) -> Dict[str, Any]:
        """
        Get context bundle for an agent.
        
        Args:
            request: Context request from agent
            
        Returns:
            Context data for the agent
        """
        # Start cleanup task on first request if not already started
        self.start_cleanup_task()
        
        self.logger.info(f"Context request from {request.agent_name} ({request.agent_id})")
        
        # Update agent registry
        self.agent_registry[request.agent_id] = {
            "name": request.agent_name,
            "last_seen": request.timestamp,
            "current_task": request.task,
            "status": "active"
        }
        
        # Build context response
        context_data = {
            "shared_state": self._get_filtered_shared_state(request.agent_id),
            "tools": self._get_available_tools(request.agent_id),
            "history": self._get_relevant_history(request.agent_id, request.task),
            "coordination": self._get_coordination_info(request.agent_id),
            "environment": self._get_environment_info(),
            "constraints": self._get_constraints(request.agent_id)
        }
        
        # Record context request in history
        self.context_history.append({
            "type": "context_request",
            "agent_id": request.agent_id,
            "agent_name": request.agent_name,
            "task": request.task,
            "timestamp": request.timestamp,
            "response_size": len(json.dumps(context_data))
        })
        
        return context_data
    
    async def update_state(self, update: StateUpdate) -> Dict[str, Any]:
        """
        Update shared state.
        
        Args:
            update: State update from agent
            
        Returns:
            Update confirmation
        """
        self.logger.info(f"State update from {update.agent_id}: {update.key}")
        
        # Update shared state
        self.shared_state[update.key] = {
            "value": update.value,
            "updated_by": update.agent_id,
            "timestamp": update.timestamp
        }
        
        # Record in history
        self.context_history.append({
            "type": "state_update",
            "agent_id": update.agent_id,
            "key": update.key,
            "timestamp": update.timestamp
        })
        
        return {"success": True, "timestamp": time.time()}
    
    async def get_state(self, key: str) -> Optional[Any]:
        """
        Get a specific state value.
        
        Args:
            key: State key to retrieve
            
        Returns:
            State value or None if not found
        """
        state_entry = self.shared_state.get(key)
        if state_entry:
            return state_entry["value"]
        return None
    
    async def register_tool(self, tool_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a tool with the context server.
        
        Args:
            tool_definition: Tool definition
            
        Returns:
            Registration confirmation
        """
        tool_name = tool_definition.get("name")
        if not tool_name:
            raise ValueError("Tool definition must include 'name' field")
        
        self.tools_registry[tool_name] = tool_definition
        self.logger.info(f"Registered tool: {tool_name}")
        
        return {"success": True, "tool_name": tool_name}
    
    async def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of agents.
        
        Args:
            agent_id: Specific agent ID, or None for all agents
            
        Returns:
            Agent status information
        """
        if agent_id:
            return self.agent_registry.get(agent_id, {})
        else:
            return self.agent_registry
    
    def _get_filtered_shared_state(self, agent_id: str) -> Dict[str, Any]:
        """Get shared state filtered for the requesting agent."""
        # For now, return all shared state
        # In production, might filter based on permissions
        return {
            key: entry["value"] 
            for key, entry in self.shared_state.items()
        }
    
    def _get_available_tools(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get tools available to the requesting agent."""
        # For now, return all tools
        # In production, might filter based on agent capabilities
        return list(self.tools_registry.values())
    
    def _get_relevant_history(self, agent_id: str, task: str) -> List[Dict[str, Any]]:
        """Get relevant historical context for the agent."""
        relevant_history = []
        
        # Get recent entries from this agent
        agent_history = [
            entry for entry in self.context_history[-50:]  # Last 50 entries
            if entry.get("agent_id") == agent_id
        ]
        relevant_history.extend(agent_history[-10:])  # Last 10 from this agent
        
        # Get entries related to the current task
        task_keywords = task.lower().split()
        for entry in self.context_history[-100:]:  # Last 100 entries
            if entry.get("task"):
                entry_task = entry["task"].lower()
                if any(keyword in entry_task for keyword in task_keywords):
                    relevant_history.append(entry)
        
        # Remove duplicates and sort by timestamp
        seen_entries = set()
        unique_history = []
        for entry in relevant_history:
            entry_id = (entry.get("agent_id"), entry.get("timestamp"))
            if entry_id not in seen_entries:
                seen_entries.add(entry_id)
                unique_history.append(entry)
        
        unique_history.sort(key=lambda x: x.get("timestamp", 0))
        
        return unique_history[-20:]  # Return last 20 relevant entries
    
    def _get_coordination_info(self, agent_id: str) -> Dict[str, Any]:
        """Get coordination information for the agent."""
        # Get other active agents
        current_time = time.time()
        active_agents = []
        
        for aid, info in self.agent_registry.items():
            if aid != agent_id and info.get("last_seen", 0) > current_time - 300:  # Active in last 5 minutes
                active_agents.append({
                    "id": aid,
                    "name": info.get("name"),
                    "current_task": info.get("current_task"),
                    "status": info.get("status"),
                    "last_seen": info.get("last_seen")
                })
        
        # Get coordination requests
        coordination_requests = [
            entry for entry in self.context_history[-50:]
            if entry.get("type") == "coordination_request"
        ]
        
        return {
            "other_agents": active_agents,
            "coordination_requests": coordination_requests,
            "agent_count": len(active_agents) + 1  # +1 for requesting agent
        }
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information."""
        return {
            "server_time": time.time(),
            "server_uptime": time.time() - getattr(self, 'start_time', time.time()),
            "total_agents": len(self.agent_registry),
            "total_state_keys": len(self.shared_state),
            "total_tools": len(self.tools_registry),
            "history_entries": len(self.context_history)
        }
    
    def _get_constraints(self, agent_id: str) -> Dict[str, Any]:
        """Get constraints for the agent."""
        # Default constraints - could be customized per agent
        return {
            "cost_limit": 10.0,
            "time_limit": 300.0,  # 5 minutes
            "max_iterations": 20,
            "rate_limit": 60  # requests per minute
        }
    
    def start_cleanup_task(self):
        """Start the periodic cleanup task."""
        if self._cleanup_task is None:
            try:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            except RuntimeError:
                # No event loop running, will start later
                pass
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old data."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                current_time = time.time()
                
                # Clean up old agent entries
                inactive_agents = [
                    aid for aid, info in self.agent_registry.items()
                    if info.get("last_seen", 0) < current_time - 3600  # 1 hour
                ]
                
                for aid in inactive_agents:
                    del self.agent_registry[aid]
                    self.logger.info(f"Cleaned up inactive agent: {aid}")
                
                # Clean up old history entries
                if len(self.context_history) > self.max_history_entries:
                    old_count = len(self.context_history)
                    self.context_history = self.context_history[-self.max_history_entries:]
                    self.logger.info(f"Cleaned up {old_count - len(self.context_history)} old history entries")
                
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")


# FastAPI app
app = FastAPI(title="MCP Context Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize context server
context_server = ContextServer()
context_server.start_time = time.time()

# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/context")
async def get_context(request: ContextRequest):
    """Get context for an agent."""
    try:
        return await context_server.get_context(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/state")
async def update_state(update: StateUpdate):
    """Update shared state."""
    try:
        return await context_server.update_state(update)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state/{key}")
async def get_state(key: str):
    """Get a specific state value."""
    try:
        value = await context_server.get_state(key)
        if value is None:
            raise HTTPException(status_code=404, detail="State key not found")
        return {"key": key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools")
async def register_tool(tool_definition: Dict[str, Any]):
    """Register a tool."""
    try:
        return await context_server.register_tool(tool_definition)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def get_agents():
    """Get all agent statuses."""
    try:
        return await context_server.get_agent_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent status."""
    try:
        agent_info = await context_server.get_agent_status(agent_id)
        if not agent_info:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get server statistics."""
    try:
        return context_server._get_environment_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the context server."""
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main() 